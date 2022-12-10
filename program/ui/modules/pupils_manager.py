"""
ui/modules/pupils_manager.py

Last updated:  2022-12-10

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
from core.classes import build_group_data, atomic_maps
from core.pupils import get_pupil_fields, get_pupils, pupil_data
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
    CellEditorCheckList,
)

### -----

def init():
    MAIN_WIDGET.add_tab(ManagePupils())


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

# ++++++++++++++ The widget implementation ++++++++++++++

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
#TODO: Perhaps without QStackedWidget ... maybe the plain table is enough.
        self.data_view = QStackedWidget()
        #        EdiTableWidget()
        vboxl.addWidget(self.data_view)
#        self.pupil_data_table.signal_modified.connect(self.updated)

        # Various "controls" in the panel on the right
        formbox = QFormLayout()
        vboxr.addLayout(formbox)
        self.class_selector = KeySelector(changed_callback=self.changed_class)
        formbox.addRow(T["CLASS"], self.class_selector)

#TODO: pass open_editor handler?
        self.pupil_table = TableWidget(edit_handler=self.edit_cell)
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
        self.field_list = []
        for f, vec in self.pupil_fields_map.items():
            self.field_list.append(f)
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
                self.group_editor = CellEditorGroups(classes)
                editor = self.group_editor.activate
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
        self.pupil_list = get_pupils(klass, use_cache=False)
        self.pupil_table.setRowCount(len(self.pupil_list))
        row = 0
        for pdata in self.pupil_list:
            col = 0
            for f in self.pupil_fields_map:
                self.pupil_table.setItem(row, col, CellItem(pdata[f]))
                col += 1
            row += 1
        # hHd = self.pupil_table.horizontalHeader()
        self.pupil_table.resizeColumnsToContents()
        # hHd.setStretchLastSection(True)
        self.group_editor.set_class(klass)
        return True # confirm acceptance to the <KeySelector>.

    def edit_cell(self, r, c, pos):
        pdata = self.pupil_list[r]
        properties = {
            "ROW_DATA": pdata,
            "VALUE": pdata[self.field_list[c]],
        }
        editor = self.field_editors[c]
        if editor(pos, properties):
            print("====>", properties)
#TODO
#                update db and display



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
    def __init__(self, parent=None, edit_handler=None):
        self.edit_handler = edit_handler
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
        if self.click_pending and self.edit_handler:
            x = self.columnViewportPosition(c)
            y = self.rowViewportPosition(r)
            pos = self.mapToGlobal(QPoint(x, y))
            print("CLICKED", r, c, pos)
            self.edit_handler(r, c, pos)

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
        text0 = properties["VALUE"]
        self.lineedit.setText(text0)
        self.move(pos)
        if self.exec():
            text = self.lineedit.text()
            # A new pupil-id may not be null ...
            if text:
                if text != text0:
                    # ... and may not be in use
                    if pupil_data(text, allow_none=True):
                        SHOW_ERROR(T["PID_EXISTS"].format(pid=text))
                    else:
                        properties["VALUE"] = text
                        return True
            else:
                SHOW_ERROR(T["NULL_PID"])
        return False


class CellEditorSortName(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        vbox = QVBoxLayout(self)
        self.lineedit = QLineEdit(self)
        vbox.addWidget(self.lineedit)
        self.lineedit.returnPressed.connect(self.accept)

    def activate(self, pos, properties):
        text0 = properties["VALUE"]
        if text0:
            self.lineedit.setText(text0)
        else:
            # Generate a default sorting name
            self.lineedit.setText(get_sortname(properties["ROW_DATA"]))
        self.move(pos)
        if self.exec():
            text = self.lineedit.text()
            if text != text0:
                # Check that it is unique
                if db_check_unique_entry("PUPILS", SORT_NAME=text):
                    SHOW_ERROR(T["SORT_NAME_EXISTS"])
                else:
                    properties["VALUE"] = text
                    return True
        return False


#TODO
class CellEditorGroups(CellEditorCheckList):
    """The groups field is a somewhat optional field – the program
    doesn't necessarily need any group information. However, membership
    of certain groups may be important, e.g. if it affects the grading.
    """
# I suppose ideally it would be some sort of check-box affair with
# illegal combinations being forbidden.
    def __init__(self, classes):
        self.__classes = classes
        super().__init__()

    def set_class(self, klass):
        divisions = self.__classes[klass].divisions
        gdata = build_group_data(divisions)
        self.__g2atoms = {
            g: set(atoms) for g, atoms in atomic_maps(
                gdata["MINIMAL_SUBGROUPS"], list(gdata["GROUP_MAP"])
            ).items() if g and '.' not in g
        }
#
        print("\n ... Atoms:", self.__g2atoms)
        self.set_list(self.__g2atoms)

    def item_changed(self, lwi):
#TODO: Check validity if adding a group

        if lwi.checkState() == Qt.CheckState.Checked:
            g = lwi.text()


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
