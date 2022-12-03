"""
ui/modules/pupils_manager.py

Last updated:  2022-12-03

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
from core.classes import Classes
from core.basic_data import get_classes
from core.pupils import get_pupil_fields, get_pupils
from ui.ui_base import (
    # QtWidgets
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QFormLayout,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    # QtCore
    Qt,
    # Others
    APP,
    KeySelector,
    run
)
from ui.editable import EdiTableWidget



#from ui.ui_extra import QWidget, QLabel, QVBoxLayout, \
#        QTreeWidget, QTreeWidgetItem, Qt

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
        self.pupil_table.setHorizontalHeaderLabels(
            self.pupil_fields_map.values()
        )

        classes = get_classes()
        self.class_selector.set_items(classes.get_class_list())

        self.class_selector.trigger()


    def changed_class(self, klass):
        # print("TODO: Change to class", klass)
        pupils = get_pupils(klass)
        self.pupil_table.setRowCount(len(pupils))
        row = 0
        for pdata in pupils:
            col = 0
            for f in self.pupil_fields_map:
                self.pupil_table.setItem(row, col, QTableWidgetItem(pdata[f]))
                col += 1
            row += 1
        return True # confirm acceptance to the <KeySelector>.


class TableWidget(QTableWidget):
    def __init__(self, parent=None, changed_callback=None):
        self.changed_callback = changed_callback
        super().__init__(parent=parent)
        self.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.AnyKeyPressed
            | QAbstractItemView.EditTrigger.SelectedClicked  # this one has a delay!
        )
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

    def keyPressEvent(self, e):
        e.accept()
        key = e.key()
        if key == Qt.Key_Return:
            if self.state() != self.EditingState:
                self.editItem(self.currentItem())
        else:
            super().keyPressEvent(e)

    def clicked(self, r, c):
        print("CLICKED", r, c)

    def pressed(self, r, c):
        km = APP.queryKeyboardModifiers()
        if km & Qt.KeyboardModifier.ShiftModifier:
            return
        print("Pressed", r, c)
        self.clearSelection() # to avoid multiple selection ranges

    def entered(self, r, c):
        print("ENTERED", r, c)


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
