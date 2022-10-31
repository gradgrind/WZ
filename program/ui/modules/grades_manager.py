"""
ui/modules/grades_manager.py

Last updated:  2022-10-31

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

##### Configuration #####################
# Some sizes in points
GRADETABLE_TITLEHEIGHT = 25
GRADETABLE_ROWHEIGHT = 30
GRADETABLE_SUBJECTWIDTH = 25
GRADETABLE_EXTRAWIDTH = 40
GRADETABLE_HEADERHEIGHT = 100
GRADETABLE_PUPILWIDTH = 200
GRADETABLE_LEVELWIDTH = 50

GRID_COLOUR = "888800"  # rrggbb

#########################################

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

from core.db_access import open_database, db_values, db_read_table
from core.base import class_group_split, Dates
from core.basic_data import check_group
from core.pupils import pupils_in_group, pupil_name
from grades.gradetable import (
    get_grade_config,
    grade_table_info,
    read_stored_grades,
    make_grade_table,
)

#???
from ui.ui_base import (
    QWidget,
    QFormLayout,
    QDialog,
    QStyledItemDelegate,
    QLineEdit,
    QHBoxLayout,
    QVBoxLayout,

    QPushButton,
    QLayout,

    QLabel,
    QListWidget,
    QAbstractItemView,
    QComboBox,
    # QtCore
    Qt,

    KeySelector,
    HLine,
    run,
)
#from ui.editable import EdiTableWidget
#from ui.grid_base import GridViewAuto
from ui.grid_base import GridView

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


class InstanceSelector(QWidget):
    def __init__(self):
        super().__init__()
        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(0, 0, 0, 0)
        self.combobox = QComboBox()
        hbox.addWidget(self.combobox)
        label = "+"
        self.addnew = QPushButton(label)
        self.addnew.setToolTip("New Item")
        width = self.addnew.fontMetrics().boundingRect(label).width() + 16
        self.addnew.setMaximumWidth(width)
        hbox.addWidget(self.addnew)
        self.addnew.clicked.connect(self.do_addnew)

#TODO: According to the "occasion" and class-group there can be different
# sorts of "instance". The main report types don't cater for "instances",
# so the combobox and button could be disabled. Where a list is supplied
# in the configuration, no new values are possible, the current value
# would come from the database entry. Perhaps dates might be permitted.
# In that case a date-choice widget would be appropriate.
# Single report types, and maybe some other types, would take any string.
# In that case a line editor coulf be used.

    def do_addnew(self):
        result = InstanceDialog.popup(
            pos=self.mapToGlobal(self.rect().bottomLeft())
        )

    def set_list(self, value_list: list[str], mutable: int):
        self.value_list = value_list
        self.combobox.clear()
        self.combobox.addItems(value_list)
        self.setEnabled(mutable >= 0)
        self.addnew.setEnabled(mutable > 0)

    def text(self):
        return self.combobox.currentText()


#TODO
class InstanceDialog(QDialog):
    @classmethod
    def popup(cls, start_value="", parent=None, pos=None):
        d = cls(parent)
#        d.init()
        if pos:
            d.move(pos)
        return d.activate(start_value)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        #self.setWindowFlags(Qt.WindowType.Popup)
        vbox0 = QVBoxLayout(self)
        vbox0.setContentsMargins(0, 0, 0, 0)
        #vbox0.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.ledit = QLineEdit()
        vbox0.addWidget(self.ledit)

    def activate(self, start_value):
        self.result = None
        self.ledit.setText(start_value)
        self.exec()
        print("DONE", self.result)
        return self.result


class GradeManager(QWidget):
    def __init__(self):
        super().__init__()
        hbox = QHBoxLayout(self)
        vboxl = QVBoxLayout()
        hbox.addLayout(vboxl)
        vboxr = QVBoxLayout()
        hbox.addLayout(vboxr)
        hbox.setStretchFactor(vboxl, 1)

        # Class info
        self.class_label = QLabel()
        vboxl.addWidget(self.class_label)
#TODO: Do I want this?
        self.modified_label = QLabel()
        vboxl.addWidget(self.modified_label)

        # The class data table
        self.pupil_data_table = GradeTableView()
#        EdiTableWidget()
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
#        self.instance_selector = QComboBox()
        self.instance_selector = InstanceSelector()
#        delegate = InstanceDelegate(self)
#        self.instance_selector.setEditable(True)
#        self.instance_selector.setItemDelegate(delegate)
#        self.instance_selector.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
#TODO: ? Rather index changed signal?
#        self.instance_selector.currentTextChanged.connect(self.select_instance)
        formbox.addRow(T["Instance"], self.instance_selector)

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
        occasion_info = get_grade_config()["OCCASIONS"]
        self.occasion2data = {}
        for o, odata in occasion_info:
            self.occasion2data[o] = odata
            self.occasion_selector.addItem(o)
        # Enable callbacks
        self.__changes_enabled = True
        self.class_group = None
        self.changed_occasion(self.occasion_selector.currentText())

    def select_instance(self, instance=None):
#
        print(f"TODO: Instance '{instance}' // {self.instance_selector.text()}")

        __instance = self.instance_selector.text()
        if instance:
            if __instance != instance:
                raise Bug(f"Instance mismatch: '{instance}' vs. '{__instance}'")
        else:
            instance = __instance

        # Get info from database
        infolist = db_read_table(
            "GRADES_INFO",
            ["DATE_ISSUE", "DATE_GRADES"],
            CLASS_GROUP=self.class_group,
            OCCASION=self.occasion,
            INSTANCE=instance
        )[1]
        if infolist:
            if len(infolist) > 1:
                raise Bug(
                    f"Multiple entries in GRADES_INFO for {self.class_group}"
                    f" / {self.occasion} / {instance}"
                )
            DATE_ISSUE, DATE_GRADES = infolist[0]
        else:
            # No entry in database, use "today" for initial date values
            DATE_ISSUE = Dates.today()
            DATE_GRADES = DATE_ISSUE

        table_info = grade_table_info(self.occasion, self.class_group, instance)
        dbgrades = read_stored_grades(self.occasion, self.class_group, instance)

#TODO: If there are dbgrades, use these for the pupil rows, otherwise
# from table_info.
# Perhaps – if the date (of issue?) is not yet passed, the pupils should
# always come from table_info?
# Set up data structures?
# Perform all calculations.

        ## Headers
        self.pupil_data_table.setup(
            subjects=table_info["SUBJECTS"],
            extra_columns=table_info["EXTRAS"],
#TODO: This is from the general info, not from existing grade entries
            pupils=table_info["PUPILS"],
        )

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
                # Keys starting with '_' are for additional, non-group
                # related information.
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
            print("Class change handling disabled:", new_class_group)
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

        self.__changes_enabled = False
        try:
            instance_data = self.group_data["INSTANCE"]
        except KeyError:
            # No instances are allowed
            self.instance_selector.set_list([], -1)
        else:
            if isinstance(instance_data, list):
                self.instance_selector.set_list(instance_data, 0)
            else:
                # Get items from database
                instances = db_values(
                    "GRADES_INFO",
                    "INSTANCE",
                    sort_field="INSTANCE",
                    CLASS_GROUP=self.class_group,
                    OCCASION=self.occasion
                )
                self.instance_selector.set_list(instances, 1)
        self.__changes_enabled = True
        self.select_instance()


#class GradeTableView(GridViewAuto):
class GradeTableView(GridView):


    def setup(self, subjects, extra_columns, pupils):
        self.subject_list = subjects
        self.extras_list = extra_columns
        self.pupils_map = pupils
        rows = (GRADETABLE_HEADERHEIGHT,) \
            + (GRADETABLE_ROWHEIGHT,) * len(pupils)
        cols = (
           GRADETABLE_PUPILWIDTH,
            GRADETABLE_LEVELWIDTH,
        ) + (GRADETABLE_SUBJECTWIDTH,) * len(subjects) \
          + (GRADETABLE_EXTRAWIDTH,) * len(extra_columns)
        self.init(rows, cols, GRADETABLE_TITLEHEIGHT)

        row_list = []
        for rx in range(len(rows)):
            row = []

            for cx in range(len(cols)):

#            self.grid_tile(rx, cx, tag=f"({cx} | {rx})")
#            self.grid_tile(rx, cx, tag=f"({cx} | {rx})", border=None)
                rotate = False
                valign = None
                halign = None
                cell_selectable = True
                if len(row_list) == 0:
                    cell_selectable = False
                    if len(row) >= 2:
                        rotate = True
                        valign = 'b'
                elif len(row) == 0:
                    halign = 'l'
                row.append(
                    self.grid_tile(
                        rx, cx, tag=f"({cx} | {rx})",
                        border=GRID_COLOUR,
                        rotate=rotate,
                        cell_selectable=cell_selectable,
                        valign=valign,
                        halign=halign
                    )
                )
            row_list.append(row)

        self.grid_line_thick_v(2)
        self.grid_line_thick_h(1)

        hheaders = dict(get_grade_config()["HEADERS"])

        row_list[0][0].set_text(hheaders["PUPIL"])
        row_list[0][1].set_text(hheaders["LEVEL"])
        i = 2
        for s in subjects:
            row_list[0][i].set_text(s["NAME"])
            i += 1
        for s in extra_columns:
            row_list[0][i].set_text(s["NAME"])
            i += 1

        i = 1
        for pid, pinfo in pupils.items():
            pdata, p_grade_tids = pinfo
            row_list[i][0].set_text(pupil_name(pdata))
            row_list[i][1].set_text(pdata["LEVEL"])
            i += 1


#TODO


#?
        if GRADETABLE_TITLEHEIGHT > 0:
            title = self.add_title("Centre Title")
            title_l = self.add_title("Left Title", halign="l")
            title_r = self.add_title("Right Title", halign="r")

    def table2pdf(self, fpath):
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        self.to_pdf(fpath)
    #    self.to_pdf(fpath, can_rotate = False)


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from ui.ui_base import run

    widget = ManageGrades()
    widget.grade_manager.class_label.setText("<b>Klasse 02G</b>")
    widget.grade_manager.modified_label.setText("zuletzt geändert: 2021-10-05_20:14")
# Actually this can be in the main code, using the fixed (translated)
# column headers ... need to set up the data area.
#    widget.grade_manager.pupil_data_table.setup(colheaders = ["PID", "Name"],
#            undo_redo = True, paste = True,
#            on_changed = None)

    widget.enter()

    widget.resize(1000, 500)
    run(widget)


#new?
#    widget = ManagePupils()
#    widget.enter()
#    widget.resize(1000, 550)
#    run(widget)
