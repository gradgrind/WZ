"""
ui/modules/grades_manager.py

Last updated:  2022-11-27

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
GRADETABLE_TITLEHEIGHT = 40
GRADETABLE_ROWHEIGHT = 25
GRADETABLE_SUBJECTWIDTH = 25
GRADETABLE_EXTRAWIDTH = 40
GRADETABLE_HEADERHEIGHT = 100
GRADETABLE_PUPILWIDTH = 200
GRADETABLE_LEVELWIDTH = 50

GRID_COLOUR = "888800"  # rrggbb

COMPONENT_COLOUR = "ffeeff"
COMPOSITE_COLOUR = "eeffff"
CALCULATED_COLOUR = "ffffcc"

#########################################

if __name__ == "__main__":
    import sys, os

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

from core.db_access import open_database, db_values
from core.base import class_group_split
from core.basic_data import check_group
from core.pupils import pupils_in_group, pupil_name
from grades.gradetable_new import (
    get_grade_config,
    make_grade_table,
    full_grade_table,
    NO_GRADE,
    update_pupil_grades,
    update_table_info,
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
    QDateEdit,
    # QtCore
    Qt,
    QDate,

    KeySelector,
    HLine,
    run,
)
#from ui.editable import EdiTableWidget
from ui.grid_base import GridViewAuto, CellEditorTable, CellEditorText
#from ui.grid_base import GridView

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

        # The class data table
        self.pupil_data_table = GradeTableView()
#        EdiTableWidget()
        vboxl.addWidget(self.pupil_data_table)

        # Various "controls" in the panel on the right
        grade_config = get_grade_config()
        self.info_fields = dict(grade_config["INFO_FIELDS"])
        formbox = QFormLayout()
        vboxr.addLayout(formbox)
        self.occasion_selector = QComboBox()
        self.occasion_selector.currentTextChanged.connect(self.changed_occasion)
        formbox.addRow(self.info_fields["OCCASION"], self.occasion_selector)
        self.class_selector = QComboBox()
        self.class_selector.currentTextChanged.connect(self.changed_class)
        formbox.addRow(self.info_fields["CLASS_GROUP"], self.class_selector)
#        self.instance_selector = QComboBox()
        self.instance_selector = InstanceSelector()
#        delegate = InstanceDelegate(self)
#        self.instance_selector.setEditable(True)
#        self.instance_selector.setItemDelegate(delegate)
#        self.instance_selector.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
#TODO: ? Rather index changed signal?
#        self.instance_selector.currentTextChanged.connect(self.select_instance)
        formbox.addRow(self.info_fields["INSTANCE"], self.instance_selector)

        # Date fields
        firstday = QDate.fromString(CALENDAR["FIRST_DAY"], Qt.DateFormat.ISODate)
        lastday = QDate.fromString(CALENDAR["LAST_DAY"], Qt.DateFormat.ISODate)
        self.issue_date = QDateEdit()
        self.issue_date.setMinimumDate(firstday)
        self.issue_date.setMaximumDate(lastday)
        self.issue_date.setCalendarPopup(True)
        self.issue_date.setDisplayFormat(CONFIG["QT_DATEFORMAT"])
        formbox.addRow(self.info_fields["DATE_ISSUE"], self.issue_date)
        self.issue_date.dateChanged.connect(self.issue_date_changed)
        self.grade_date = QDateEdit()
        self.grade_date.setMinimumDate(firstday)
        self.grade_date.setMaximumDate(lastday)
        self.grade_date.setCalendarPopup(True)
        self.grade_date.setDisplayFormat(CONFIG["QT_DATEFORMAT"])
        formbox.addRow(self.info_fields["DATE_GRADES"], self.grade_date)
        self.grade_date.dateChanged.connect(self.grade_date_changed)

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

    def select_instance(self, instance=""):
#
        print(f"TODO: Instance '{instance}' // {self.instance_selector.text()}")

        __instance = self.instance_selector.text()
        if instance:
            if __instance != instance:
                raise Bug(f"Instance mismatch: '{instance}' vs. '{__instance}'")
        else:
            instance = __instance
        grade_table = full_grade_table(
            self.occasion, self.class_group, instance
        )
        self.instance = instance
        self.issue_date.setDate(
            QDate.fromString(
                grade_table["DATE_ISSUE"], Qt.DateFormat.ISODate
            )
        )
        self.grade_date.setDate(
            QDate.fromString(
                grade_table["DATE_GRADES"], Qt.DateFormat.ISODate
            )
        )
        self.pupil_data_table.setup(grade_table)

        self.pupil_data_table.set_title(
            f'{T["CLASS"]}: {self.class_group}'
        )
        ltitle = self.occasion
        if self.instance:
            ltitle = f'{ltitle} // {self.instance}'
        self.pupil_data_table.set_title(ltitle, "l")
        self.pupil_data_table.set_title(
            f'{grade_table["DATE_ISSUE"]} [{grade_table["DATE_GRADES"]}]',
            "r"
        )
#TODO? Maybe only for printing? The modification time can be presented
# in the right-hand panel ...
        self.pupil_data_table.set_title(
            f'{self.info_fields["MODIFIED"]}: {grade_table["MODIFIED"]}',
            "r2", True
        )

    def issue_date_changed(self, qdate):
        print("TODO: Issue date changed", qdate)
        update_table_info(
            "DATE_ISSUE",
            qdate.toString(Qt.DateFormat.ISODate),
            OCCASION=self.occasion,
            CLASS_GROUP=self.class_group,
            INSTANCE=self.instance
        )
        # Reload table
        self.select_instance()

    def grade_date_changed(self, qdate):
        print("TODO: Grade date changed", qdate)
        update_table_info(
            "DATE_GRADES",
            qdate.toString(Qt.DateFormat.ISODate),
            OCCASION=self.occasion,
            CLASS_GROUP=self.class_group,
            INSTANCE=self.instance
        )
        # Reload table
        self.select_instance()


class GradeTableView(GridViewAuto):
#class GradeTableView(GridView):

    def setup(self, grade_table):
        self.grade_table = grade_table
#? ... What data needs to be available later?
        subject_list = grade_table["SUBJECTS"]
        component_list = grade_table["COMPONENTS"]
        composite_list = grade_table["COMPOSITES"]
        extras_list = grade_table["EXTRAS"]
        all_sids = grade_table["ALL_SIDS"]
        pupils_list = grade_table["GRADE_TABLE_PUPILS"]
        pid2grades = grade_table["PUPIL_GRADES"]
        grade_config_table = grade_table["GRADES"]
        # grades_table["GRADE_ENTRY"] # partial path ("templates/...") to
        # grade entry template (without data-type ensing)
        # grades_table["PUPILS"] # current pupil list from database
#TODO: Do I need the latter entry?

        col2colour = []
        click_handler = []
        grade_click_handler = CellEditorTable(grade_config_table).activate
        for sdata in subject_list:
            col2colour.append(None)
            click_handler.append(grade_click_handler)
        for sdata in component_list:
            col2colour.append(COMPONENT_COLOUR)
            click_handler.append(grade_click_handler)
        for sdata in composite_list:
            col2colour.append(COMPOSITE_COLOUR)
            click_handler.append(None)
        nsubjects = len(col2colour)
        for sdata in extras_list:
            if "FUNCTION" in sdata:
                col2colour.append(CALCULATED_COLOUR)
                click_handler.append(None)
            else:
                col2colour.append(None)
                handler_type = sdata["TYPE"]
                if handler_type == "CHOICE":
                    values = [[[v], ""] for v in sdata["VALUES"]]
                    editor = CellEditorTable(values).activate
                elif handler_type == "CHOICE_MAP":
                    values = [[[v], text] for v, text in sdata["VALUES"]]
                    editor = CellEditorTable(values).activate
                elif handler_type == "TEXT":
                    editor = CellEditorText().activate
                else:
#TODO?
                    editor = None
                click_handler.append(editor)

        ### Set the basic grid parameters
        # Check for customized "extra-field" widths
        custom_widths = get_grade_config().get("EXTRA_FIELD_WIDTHS")
        extra_widths = []
        for sdata in extras_list:
            try:
                extra_widths.append(int(custom_widths[sdata["SID"]]))
            except:
                extra_widths.append(GRADETABLE_EXTRAWIDTH)
        __rows = (GRADETABLE_HEADERHEIGHT,) \
            + (GRADETABLE_ROWHEIGHT,) * len(pupils_list)
        __cols = (
           GRADETABLE_PUPILWIDTH,
            GRADETABLE_LEVELWIDTH,
        ) \
            + (GRADETABLE_SUBJECTWIDTH,) * nsubjects \
            + tuple(extra_widths)
        self.init(__rows, __cols, GRADETABLE_TITLEHEIGHT)

        self.grid_line_thick_v(2)
        self.grid_line_thick_h(1)

        # The column headers
        hheaders = dict(get_grade_config()["HEADERS"])
        self.get_cell((0, 0)).set_text(hheaders["PUPIL"])
        self.get_cell((0, 1)).set_text(hheaders["LEVEL"])
        colstart = 2
        self.col0 = colstart
        col = 0
        self.sid2col = {}
        for sid, sdata in all_sids.items():
            gridcol = col + colstart
            self.sid2col[sid] = gridcol
            cell = self.get_cell((0, gridcol))
            cell.set_verticaltext()
            cell.set_valign('b')
            cell.set_background(col2colour[col])
            cell.set_text(sdata["NAME"])
            col += 1

        # The rows
        rowstart = 1
        self.row0 = rowstart
        row = 0
        self.pid2row = {}
        for pdata in pupils_list:
            gridrow = row + rowstart
            pid = pdata["PID"]
            self.pid2row[pid] = gridrow
            cell = self.get_cell((gridrow, 0))
            cell.set_halign('l')
            cell.set_text(pupil_name(pdata))
            cell = self.get_cell((gridrow, 1))
            cell.set_text(pdata["LEVEL"])

            pgrades = pid2grades[pid]
            col = 0
            for sid in all_sids:
                cell = self.get_cell((gridrow, col + colstart))
                cell.set_background(col2colour[col])
#?
# This is not taking possible value delegates into account – which would
# allow the display of a text distinct from the actual value of the cell.
# At the moment it is not clear that I would need such a thing, but it
# might be useful to have it built in to the base functionality in base_grid.
# For editor types CHOICE_MAP it might come in handy, for instance.

# Actually, that is not quite the intended use of CHOICE_MAP – the "key"
# is displayed, but it is the "value" that is needed for further processing.
# For this it would be enough to set the "VALUE" property.

                cell.set_property("PID", pid)
                cell.set_property("SID", sid)
                cell.set_text(pgrades.get(sid, ""))
                handler = click_handler[col]
                if handler:
                    cell.set_property("EDITOR", handler)
                col += 1
            row += 1

#?
        if GRADETABLE_TITLEHEIGHT > 0:
            self.title = self.add_title()
            self.title_l = self.add_title("l")
            self.add_title("r")
            self.add_title("r2")

        self.rescale()

    def cell_modified(self, properties:dict):
        """Override base method in grid_base.GridView.
        """
        try:
            new_value = properties["VALUE"]
        except KeyError:
            new_value = properties["TEXT"]
        pid = properties["PID"]
        sid = properties["SID"]
        grades = self.grade_table["PUPIL_GRADES"][pid]
        grades[sid] = new_value
        # Update this pupil's grades (etc.) in the database
        changes = update_pupil_grades(self.grade_table, pid)
        if changes:
            # Update changed display cells
            row = self.pid2row[pid]
            for sid, oldval in changes:
                self.get_cell((row, self.sid2col[sid])).set_text(grades[sid])

    def table2pdf(self, fpath):
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        self.to_pdf(fpath)
    #    self.to_pdf(fpath, can_rotate = False)


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from ui.ui_base import run

    widget = ManageGrades()
    widget.enter()

    widget.resize(1000, 500)
    run(widget)


#new?
#    widget = ManagePupils()
#    widget.enter()
#    widget.resize(1000, 550)
#    run(widget)
