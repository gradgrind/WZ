"""
ui/modules/grades_manager.py

Last updated:  2022-09-17

Front-end for managing grade reports.


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

T = TRANSLATIONS("ui.modules.grades_manager")

### +++++

from core.db_access import open_database
from core.base import class_group_split
from core.basic_data import check_group
from core.pupils import pupils_in_group, pupil_name
from grades.gradetable import get_grade_entry_tables

#???
from ui.ui_base import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QListWidget,
    QAbstractItemView,
#    QPushButton,
    QComboBox,
    KeySelector,
    HLine,
    run,
)
from ui.editable import EdiTableWidget


#from ui.ui_extra import QWidget, QLabel, QVBoxLayout, \
#        QTreeWidget, QTreeWidgetItem, Qt

### -----

def init():
    MAIN_WIDGET.add_tab(ManageGrades())


class ManageGrades(Page):
    name = T["MODULE_NAME"]
    title = T["MODULE_TITLE"]

    def __init__(self):
        super().__init__()
        self.grade_manager = GradeManager()
        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.grade_manager)

    def enter(self):
        open_database()
        self.grade_manager.init_data()

    def is_modified(self):
        return self.grade_manager.modified()


# ++++++++++++++ The widget implementation ++++++++++++++


class GradeManager(QWidget):
    def __init__(self):
        super().__init__()
        hbox = QHBoxLayout(self)
        vboxl = QVBoxLayout()
        hbox.addLayout(vboxl)
        vboxr = QVBoxLayout()
        hbox.addLayout(vboxr)

        # Class info
        self.class_label = QLabel()
        vboxl.addWidget(self.class_label)
#TODO: Do I want this?
        self.modified_label = QLabel()
        vboxl.addWidget(self.modified_label)

        # The class data table
        self.pupil_data_table = EdiTableWidget()
        vboxl.addWidget(self.pupil_data_table)

        # Various "controls" in the panel on the right
        formbox = QFormLayout()
        vboxr.addLayout(formbox)
        self.occasion_selector = QComboBox()
        self.occasion_selector.currentTextChanged.connect(self.changed_occasion)
        formbox.addRow(T["Occasion"], self.occasion_selector)
        self.class_selector = QComboBox()
        self.class_selector.currentTextChanged.connect(self.changed_class)
        formbox.addRow(T["Class_Group"], self.class_selector)

        vboxr.addWidget(HLine())
        vboxr.addWidget(QLabel(T["Pupils"]))
        self.pupil_list = QListWidget()
        # self.pupil_list.setMinimumWidth(30)
        self.pupil_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        vboxr.addWidget(self.pupil_list)

    def init_data(self):
        self.__changes_enabled = False
        # Set up "occasions" here, from config
        self.occasion_selector.clear()
        entry_tables_info = get_grade_entry_tables()
        oinfo = entry_tables_info["OCCASIONS"]
        self.occasion2data = {}
        for o, odata in oinfo:
            self.occasion2data[o] = odata
            self.occasion_selector.addItem(o)
        # Enable callbacks
        self.__changes_enabled = True
        self.class_group = None
        self.changed_occasion(self.occasion_selector.currentText())

    def modified(self):
        """Return <True> if there are unsaved changes.
        """
#TODO: test whether there really are any changes?
        return True

    def changed_occasion(self, new_occasion: str):
        if not self.__changes_enabled:
            return
        print("NEW OCCASION:", new_occasion)
        # A change of occasion should preserve the class-group, if this
        # class-group is also available for the new occasion.
        self.occasion = new_occasion
        self.occasion_data = self.occasion2data[self.occasion]
        groups = []
        for g in self.occasion_data:
            if g[0] == '_':
                continue
            klass, group = class_group_split(g)
            if not check_group(klass, group):
                REPORT(
                    "ERROR",
                    T["BAD_GROUP_IN_CONFIG"].format(
                        group=g, occasion=new_occasion
                    )
                )
                continue
            groups.append(g)
        groups.sort(reverse=True)
        self.__changes_enabled = False
        self.class_selector.clear()
        self.class_selector.addItems(groups)
        self.class_selector.setCurrentText(self.class_group) # no exception
        # Enable callbacks
        self.__changes_enabled = True
        self.changed_class(self.class_selector.currentText())

    def changed_class(self, new_class_group):
        if not self.__changes_enabled:
            return
        print("NEW GROUP:", new_class_group)
#        grade_table = self.get_grade_table(occasion, class_group)

        self.class_group = new_class_group
        self.group_data = self.occasion_data[new_class_group]

        self.pupil_data_list = pupils_in_group(new_class_group, date=None)
        self.pupil_list.clear()
        self.pupil_list.addItems([pupil_name(p) for p in self.pupil_data_list])

#TODO: If I am working from an old grade table, the odd pupil may have
# changed class – I should probably get the pupil list from the grade
# table. If I want to update the pupil list, there could be an update
# button to do this?


# What about a configuration item which allow the INITIAL level value
# (Bewertungsmaßstab) to be set according to membership of particular
# groups?

# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from ui.ui_base import run

    widget = ManageGrades()
    widget.grade_manager.class_label.setText("<b>Klasse 02G</b>")
    widget.grade_manager.modified_label.setText("zuletzt geändert: 2021-10-05_20:14")
# Actually this can be in the main code, using the fixed (translated)
# column headers ... need to set up the data area.
    widget.grade_manager.pupil_data_table.setup(colheaders = ["PID", "Name"],
            undo_redo = True, paste = True,
            on_changed = None)

    widget.enter()

    widget.resize(600, 400)
    run(widget)


#new?
#    widget = ManagePupils()
#    widget.enter()
#    widget.resize(1000, 550)
#    run(widget)
