"""
ui/modules/pupils_manager.py

Last updated:  2022-12-04

Front-end for managing pupil data.


=+LICENCE=============================
Copyright 2022 Michael Towers

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

=-LICENCE========================================
"""

#####################################################

if __name__ == "__main__":
    import sys, os, builtins

    this = sys.path[0]
    appdir = os.path.dirname(os.path.dirname(this))
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start
    from ui.ui_base import StandalonePage as Page
    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    #    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))
else:
    from ui.ui_base import StackPage as Page

T = TRANSLATIONS("ui.modules.pupils_manager")

### +++++

from core.db_access import open_database, db_values
from core.basic_data import get_classes
from core.pupils import get_pupil_fields, get_pupils
from local.local_pupils import get_sortname
from ui.ui_base import (
    # QtWidgets
    QWidget,
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QFormLayout,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QLineEdit,
    # QtCore
    Qt, QPoint,
    # Others
    APP,
    KeySelector,
    run,
)
from ui.cell_editors import (
    CellEditorLine,
    CellEditorDate,
    CellEditorTable,
)

### -----

def init():
    MAIN_WIDGET.add_tab(ManagePupils())

# ++++++++++++++ The widget implementation ++++++++++++++

class ManagePupils(Page):
    name = T["MODULE_NAME"]
    title = T["MODULE_TITLE"]

    def __init__(self):
        super().__init__()
        self.pupil_manager = PupilManager()
        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.pupil_manager)

    def enter(self):
        open_database()
        self.pupil_manager.init_data()

    def is_modified(self):
        return self.pupil_manager.modified()


class PupilManager(QWidget):
    def __init__(self):
        super().__init__()
        hbox = QHBoxLayout(self)
        vboxl = QVBoxLayout()
        hbox.addLayout(vboxl)
        vboxr = QVBoxLayout()
        hbox.addLayout(vboxr)
        hbox.setStretchFactor(vboxl, 1)

        # The class data table, etc.
        self.data_view = QStackedWidget()
        #        EdiTableWidget()
        vboxl.addWidget(self.data_view)
#        self.pupil_data_table.signal_modified.connect(self.updated)

        # Various "controls" in the panel on the right
        formbox = QFormLayout()
        vboxr.addLayout(formbox)
        self.class_selector = KeySelector(changed_callback=self.changed_class)
        formbox.addRow(T["CLASS"], self.class_selector)

        self.pupil_table = TableWidget()
        self.data_view.addWidget(self.pupil_table)

    def modified(self):
        """Return <True> if there are unsaved changes.
        """
#TODO: test whether there really are any changes?
        return True

    def init_data(self):

        print("TODO: INIT")

        self.pupil_fields_map = get_pupil_fields()
        self.pupil_table.setColumnCount(len(self.pupil_fields_map))
        classes = get_classes()
        class_list = classes.get_class_list()
        self.field_editors = []
        headers = []
        for vec in self.pupil_fields_map.values():
            headers.append(vec[0])
            e = vec[1]
            if e == "CLASS_CHOICE":
                vlist = [[[v], text] for v, text in class_list]
                editor = CellEditorTable(vlist).activate
            elif e == "PID":
                editor = CellEditorPid().activate
            elif e == "SORT_NAME":
#TODO
                editor = CellEditorSortName().activate
            elif e == "GROUPS":
#TODO
                editor = CellEditorGroups(classes).activate
# use classes[klass].divisions
            elif e == "LINE":
                editor = CellEditorLine().activate
            elif e == "DATE_OR_EMPTY":
                editor = CellEditorDate(empty_ok = True)
            elif e == "DATE":
                editor = CellEditorDate(empty_ok = False)
            elif e == "CHOICE":
                vlist = [[[v], ""] for v in vec[2]]
                editor = CellEditorTable(vlist).activate
            elif e == "CHOICE_MAP":
                vlist = [[[v], text] for v, text in vec[2]]
                editor = CellEditorTable(vlist).activate
            else:
                #TODO?
                editor = None


            self.field_editors.append(editor)
        self.pupil_table.setHorizontalHeaderLabels(headers)

        self.class_selector.set_items(class_list)

        self.class_selector.trigger()

    def changed_class(self, klass):
        # print("TODO: Change to class", klass)
        pupils = get_pupils(klass)
        self.pupil_table.setRowCount(len(pupils))
        row = 0
        for pdata in pupils:
            col = 0
            for f in self.pupil_fields_map:
                self.pupil_table.setItem(row, col, CellItem(pdata[f]))
                col += 1
            row += 1
        # hHd = self.pupil_table.horizontalHeader()
        self.pupil_table.resizeColumnsToContents()
        # hHd.setStretchLastSection(True)
        return True # confirm acceptance to the <KeySelector>.

########+++ field editors
# CLASS: an existing class. Note that if this is changed the pupil should
# disappear from the table!
# --- CHOICE or CHOICE_MAP ... from available classes
# PID: normally not editable. If I do allow editing there should perhaps
# be a warning, and a check that the result is valid, whatever that means.
# --- LINE ... but possibly with validator
# SORT_NAME: This can be a simple text-line editor.
# --- LINE
# LASTNAME, FIRSTNAMES, FIRSTNAME: also normal text-line editors
# --- LINE
# GROUPS: ideally a sort-of check list of available groups for the class.
# Actually, rather more complicated as groups within a division are
# mutually exclusive.
# DATE_EXIT: a date popup – probably without restrictions, but empty must
# be possible
# --- DATE_OR_EMPTY
# LEVEL: This could be a choice from the grades configuration?
# --- CHOICE or CHOICE_MAP ... from available levels (in GRADE_CONFIG)
# DATE_ENTRY: a date popup – probably without restrictions
# --- DATE
# DATE_BIRTH: a date popup – probably without restrictions
# --- DATE
# BIRTHPLACE: a simple text-line editor
# --- LINE
# SEX: a choice, from the base configuration
# --- CHOICE [m w]
# HOME: a simple text-line editor
# --- LINE
# DATE_QPHASE: a date popup – probably without restrictions, but empty
# must be possible
# --- DATE_OR_EMPTY

# At least the last one is specific to certain schools, not a general
# requirement. So surely the handler should be specified in a config
# file. Some handlers cannot easily be restricted to the config, so
# maybe there would need to be some sort of combination, special handlers
# for some fields in the code module.
# At least CLASS, PID, GROUPS and LEVEL would need special handlers.
########---

class TableWidget(QTableWidget):
    def __init__(self, parent=None, changed_callback=None):
        self.changed_callback = changed_callback
        super().__init__(parent=parent)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
#        self.setEditTriggers(
#            QAbstractItemView.EditTrigger.DoubleClicked
#            | QAbstractItemView.EditTrigger.AnyKeyPressed
#            | QAbstractItemView.EditTrigger.SelectedClicked  # this one has a delay!
#        )
        # Note that the <Return> key doesn't cause the editor to be opened,
        # so there is an event handling that ... see method <keyPressEvent>.

        # Change stylesheet to make the selected cell more visible
        self.setStyleSheet(
            """QTableView {
               selection-background-color: #f0e0ff;
               selection-color: black;
            }
            QTableView::item:focus {
                selection-background-color: #d0ffff;
            }
            """
        )
        self.cellClicked.connect(self.clicked)
        self.cellPressed.connect(self.pressed)
        self.cellEntered.connect(self.entered)
        self.click_pending = False

    def keyPressEvent(self, e):
        e.accept()
        key = e.key()
        if key == Qt.Key_Return:
            if self.state() != self.EditingState:
                self.editItem(self.currentItem())
        else:
            super().keyPressEvent(e)

    def clicked(self, r, c):
        if self.click_pending:
            x = self.columnViewportPosition(c)
            y = self.rowViewportPosition(r)
            pos = self.mapToGlobal(QPoint(x, y))
            print("CLICKED", r, c, pos)
#TODO
#            editor = self.field_editors[c]
#            if editor(pos, properties):
#                update db and display
# Where to store the properties? In the items, or in a separate store?
# Exactly what info is required?

    def pressed(self, r, c):
        km = APP.queryKeyboardModifiers()
        if km & Qt.KeyboardModifier.ShiftModifier:
            return
        print("Pressed", r, c)
        self.clearSelection() # to avoid multiple selection ranges
        self.click_pending = True

    def entered(self, r, c):
        print("ENTERED", r, c)
        self.click_pending = False

#???
class CellItem(QTableWidgetItem):
    def __init__(self, text):
        super().__init__(text)
        self.__properties = {"TEXT": text, "VALUE": text}

#TODO: How to get cell coordinates for popup?

####################################################
### Specialized cell editors for the pupil table ###
####################################################


class CellEditorPid(QDialog):
    """For correcting a pupil-id or creating a new one. This should
    normally be handled automatically, a manual change being generally
    undesirable.
    """
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        vbox = QVBoxLayout(self)
        label = QLabel(f'<p style="color:#a00000;">{T["PID_WARNING"]}</p>')
        vbox.addWidget(label)
        self.lineedit = QLineEdit(self)
        vbox.addWidget(self.lineedit)
        self.lineedit.returnPressed.connect(self.accept)

    def activate(self, pos, properties):
        text0 = properties["TEXT"]
        self.lineedit.setText(text0)
        self.move(pos)
        if self.exec():
            text = self.lineedit.text()
            if text != text0:
                if pupil_data(text):
                    properties["TEXT"] = text
                    return True
                SHOW_ERROR(T["PID_EXISTS"].format(pid=text))
        return False


#TODO
class CellEditorSortName(QDialog):
    def activate(self, pos, properties):
# use get_sortname(pdata) if no text
        pass

#TODO
class CellEditorGroups(QDialog):
    def __init__(self, classes):
        self.classes = classes

    def activate(self, pos, properties):
        pass


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from ui.ui_base import run

    widget = ManagePupils()
#    widget.pupil_manager.class_label.setText("<b>Klasse 02G</b>")
#    widget.pupil_manager.modified_label.setText("zuletzt geändert: 2021-10-05_20:14")
# Actually this can be in the main code, using the fixed (translated)
# column headers ... need to set up the data area.
#    widget.pupil_manager.pupil_data_table.setup(colheaders = ["PID", "Name"],
#            undo_redo = True, paste = True,
#            on_changed = None)
#    widget.resize(600, 400)
#    run(widget)


#new?
    widget.enter()
    widget.resize(1000, 550)
    run(widget)
