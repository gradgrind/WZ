"""
ui/modules/course_editor.py

Last updated:  2023-02-21

Edit course and blocks+lessons data.


=+LICENCE=============================
Copyright 2023 Michael Towers

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

########################################################################

if __name__ == "__main__":
    import sys, os

    this = sys.path[0]
    appdir = os.path.dirname(os.path.dirname(this))
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start
    from ui.ui_base import StandalonePage as Page

    # start.setup(os.path.join(basedir, 'TESTDATA'))
    # start.setup(os.path.join(basedir, "DATA-2023"))
    start.setup(os.path.join(basedir, "DATA-2024"))
else:
    from ui.ui_base import StackPage as Page

T = TRANSLATIONS("ui.modules.course_editor")

### +++++

from typing import NamedTuple

from core.db_access import (
    open_database,
    db_read_full_table,
    db_update_field,
    db_new_row,
    db_delete_rows,
    db_values,
    NoRecord,
)
from core.teachers import Teachers
from core.classes import Classes
from core.basic_data import (
    clear_cache,
    get_payment_weights,
    get_subjects,
    sublessons,
    get_simultaneous_weighting,
)

from ui.ui_base import (
    HLine,
    LoseChangesDialog,
    KeySelector,
    RowSelectTable,
    FormLineEdit,
    FormComboBox,
    ForeignKeyItemDelegate,
    ### QtWidgets:
    QSplitter,
    QFrame,
    QFormLayout,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QDialogButtonBox,
    QTableWidgetItem,
    QTableView,
    QDialog,
    QWidget,
    QStackedLayout,
    QAbstractItemView,
    QCheckBox,
    QHeaderView,
    ### QtGui:
    QIcon,
    ### QtCore:
    Qt,
    Slot,
    ### QtSql:
    QSqlTableModel,
    ### uic
    uic,
)

from ui.course_dialogs import (
    set_coursedata,
    get_coursedata,
    GroupSelector,
    #    DurationSelector,
    #    DayPeriodSelector,
    #    PartnersSelector,
    PaymentSelector,
    RoomSelector,
    #    partners,
    DayPeriodDelegate,
    DurationDelegate,
    #    PartnersDelegate,
    BlockTagSelector,
    BlockTagDialog,
    #    parse_time_field,
    #    get_time_entry,
    TableWidget,
    courses_with_lessontag,
)

# Course table fields
#TODO: still needed?
COURSE_COLS = [
    (f, T[f])
    for f in (
        "course",
        "CLASS",
        "GRP",
        "SUBJECT",
        "TEACHER",
        "REPORT",
        "GRADES",
        "REPORT_SUBJECT",
        "AUTHORS",
        "NOTES",
    )
]
# SUBJECT, CLASS and TEACHER are foreign keys with:
#  on delete cascade + on update cascade
FOREIGN_FIELDS = ("CLASS", "TEACHER", "SUBJECT")

COURSE_TABLE_FIELDS = ( # the fields shown in the course table
# (db-field name, column-type, horizontal text alignment)
# column-type:
#   -1: checkbox
#    0: db-value
#    1: display-value (from column-dependent map)
# alignment:
#   -1: left
#    0: centre
#    1: right
    ("CLASS", 0, 0),
    ("GRP", 0, 0),
    ("SUBJECT", 1, -1),
    ("TEACHER", 1, -1),
    ("REPORT", -1, 0),
    ("GRADES", -1, 0),
    ("INFO", 0, -1),
)

#FILTER_FIELDS = [cc for cc in COURSE_COLS if cc[0] in FOREIGN_FIELDS]

# Group of fields which determines a course (the tuple must be unique)
class COURSE_KEY(NamedTuple):
    CLASS: str
    GRP: str
    SUBJECT: str
    TEACHER: str

    def __str__(self):
        return f"({self.CLASS}:{self.GRP}:{self.SUBJECT}:{self.TEACHER})"


# print("§§§§§§§§§§§", COURSE_KEY._fields, str(COURSE_KEY("10G", "*", "Ma", "EA")))

#TODO: deprecated?
BLOCK_COLS = [
    (f, T[f])
    for f in (
        "id",
        "course",
        "PAYMENT",
        "ROOM",
        "LESSON_TAG",
        "NOTES",
    )
]

#TODO: deprecated?
BLOCKCOLS_SHOW = ("LESSON_TAG", "PAYMENT", "NOTES")

### -----


def init():
    MAIN_WIDGET.add_tab(CourseEditorPage())


class CourseEditorPage(Page):
    name = T["MODULE_NAME"]
    title = T["MODULE_TITLE"]

    def __init__(self):
        super().__init__()

        uic.loadUi(APPDATAPATH("ui/course_editor.ui"), self)
#        self.course_editor = uic.loadUi(APPDATAPATH("ui/course_editor.ui"))

#        self.course_editor = CourseEditor()
#        hbox = QHBoxLayout(self)
#        hbox.setContentsMargins(0, 0, 0, 0)
#        hbox.addWidget(self.course_editor)

        self.icons = {
            "LESSON": self.lesson_new.icon(),
            "BLOCK": self.lesson_block.icon(),
            "PAY": self.lesson_pay.icon(),
        }


    def enter(self):
#TODO?
        open_database()
        clear_cache()

#        self.course_editor.init_data()

        self.init_data()
#TODO: Note that the course table is a QTableWidget and that it is at
# self.course_table. Don't use the special Qt data models, just work
# with basic db access methods.

        self.combo_filter.setCurrentIndex(-1)
        self.combo_filter.setCurrentIndex(0)

# ++++++++++++++ The widget implementation fine details ++++++++++++++

    def  init_data(self):
        print("§§§ init_data")

        teachers = Teachers()
        self.filter_list = {
            "CLASS": Classes().get_class_list(skip_null=False),
            "SUBJECT": get_subjects(),
            "TEACHER": [
                (tid, teachers.name(tid))
                for tid, tiddata in teachers.items()
            ]
        }


#TODO ...?
        self.course_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )


    @Slot(int)
    def on_combo_filter_currentIndexChanged(self, i):
        if i < 0:
            return
        # class, subject, teacher
        self.filter_field = FOREIGN_FIELDS[i]
        # print("§§§ on_combo_filter_currentIndexChanged", i, self.filter_field)
        self.select_list = self.filter_list[self.filter_field]
        self.combo_class.clear()
        for kv in self.select_list:
            self.combo_class.addItem(kv[1])

    @Slot(int)
    def on_combo_class_currentIndexChanged(self, i):
        """View selection changed, reload the course table.
        The method name is a bit of a misnomer, as the selector can be
        class, teacher or subject.
        """
        if i < 0:
            return
        key, val = self.select_list[i]
        # print("§§§ on_combo_class_currentIndexChanged", key, val)
        self.suppress_handlers = True
        fields, records = db_read_full_table(
            "COURSES", sort_field="SUBJECT", **{self.filter_field: key}
        )
        # Populate the course table
        self.course_table.setRowCount(len(records))
        self.courses = []
        for r, rec in enumerate(records):
            rdict = {fields[i]: val for i, val in enumerate(rec)}
            self.courses.append(rdict)
            # print("  --", rdict)
            c = 0
            for cid, ctype, align in COURSE_TABLE_FIELDS:
                cell_value = rdict[cid]
                if ctype == -1:
                    # Checkbox, needs special handling for alignment.
                    # Use a cell widget rather than cell item.
                    box = self.course_table.cellWidget(r, c)
                    if box:
                        cw = box.findChild(QCheckBox)
                    else:
                        cw = QCheckBox()
                        box = QWidget()
                        l = QHBoxLayout(box)
                        l.addWidget(cw)
                        if align == -1:
                            a = Qt.AlignmentFlag.AlignLeft
                        elif align == 1:
                            a = Qt.AlignmentFlag.AlignRight
                        else:
                            a = Qt.AlignmentFlag.AlignHCenter
                        l.setAlignment(a | Qt.AlignmentFlag.AlignVCenter)
                        l.setContentsMargins(0,0,0,0)
                        self.course_table.setCellWidget(r, c, box)
                        cw.toggled.connect(
                            self.on_report_toggle
                            if cid == "REPORT"
                            else self.on_grades_toggle
                        )
                    cw.setCheckState(
                        Qt.CheckState.Checked
                        if cell_value
                        else Qt.CheckState.Unchecked
                    )
                else:
                    item = self.course_table.item(r, c)
                    if not item:
                        item = QTableWidgetItem()
                        if align == -1:
                            a = Qt.AlignmentFlag.AlignLeft
                        elif align == 1:
                            a = Qt.AlignmentFlag.AlignRight
                        else:
                            a = Qt.AlignmentFlag.AlignHCenter
                        item.setTextAlignment(a | Qt.AlignmentFlag.AlignVCenter)
                        self.course_table.setItem(r, c, item)
                    if ctype == 0:
                        item.setText(cell_value)
                    elif ctype == 1:
#TODO: rather use a map?
                        for k, v in self.filter_list[cid]:
                            if k == cell_value:
                                item.setText(v)
                                break
                        else:
#TODO: T ...
                            REPORT(
                                "ERROR",
                                f"UNKNOWN VALUE IN FIELD '{cid}': '{cell_value}'"
                            )
                    else:
                        raise Bug(f"Invalid ctype ({ctype}) in COURSE_TABLE_FIELDS")
                c += 1
        self.suppress_handlers = False
        if len(records) > 0:
            self.course_table.setCurrentCell(0, 0)

    def on_report_toggle(self, on):
        if self.suppress_handlers:
            return
        row = self.course_table.currentRow()
        course_dict = self.courses[row]
        cnum = course_dict["course"]
        if not db_update_field(
            "COURSES",
            "REPORT",
            "X" if on else "",
            course=cnum,
        ):
            REPORT(
                "ERROR",
#TODO: T ...
                f"Couldn't update REPORT field of course {cnum}"
            )

    def on_grades_toggle(self, on):
        if self.suppress_handlers:
            return
        row = self.course_table.currentRow()
        course_dict = self.courses[row]
        cnum = course_dict["course"]
        if not db_update_field(
            "COURSES",
            "GRADES",
            "X" if on else "",
            course=cnum,
        ):
            REPORT(
                "ERROR",
#TODO: T ...
                f"Couldn't update GRADES field of course {cnum}"
            )

    def on_course_table_itemSelectionChanged(self):
        row = self.course_table.currentRow()
        print("§§§ on_course_table_itemSelectionChanged", row)

#TODO
#    def course_selected(self, row):
#?        self.current_row = row
        if row >= 0:
            self.pb_delete_course.setEnabled(True)
            self.course_dict = self.courses[row]
            self.set_course(self.course_dict["course"])
#?            set_coursedata(
#                COURSE_KEY(*[record.value(f) for f in COURSE_KEY._fields])
#            )
            self.frame_r.setEnabled(True)

        else:
            # e.g. when entering an empty table
            # print("EMPTY TABLE")
#?            self.set_course(0)
            self.pb_delete_course.setEnabled(False)
            self.course_dict = None
            # TODO: This could cause problems when an attempt is made to use the value?
#?            set_coursedata(None)
            # Actually, the right hand pane should probably be disabled.
            self.frame_r.setEnabled(False)

#TODO
    def set_course(self, course: int):
        print("SET COURSE:", repr(course))
#?        self.course_id = course

        fields, records = db_read_full_table(
            "COURSE_LESSONS", course=course
        )
        print("§§§ COURSE_LESSONS:", fields)

        self.lesson_table.setRowCount(0)
        self.course_lessons = []
        row = 0
        ### Build a list of entries
        ## First loop through entries in COURSE_LESSONS
#NOTE: There should be at most one COURSE_LESSONS entry for "lesson"
# types and "payment" types. For "block" types there can be more than
# one entry, but they should be connected with LESSON_GROUP entries
# with distinct (non-empty) BLOCK_NAME values.
# If violations are discovered, there should be an error report. It
# might be helpful to delete the offending entries, but as they are
# really not expected – and should not be possible – it is perhaps
# better to report the offending entries, but not to delete them, so
# that they are available for debugging purposes – the report could
# be via a bug exception?

#TODO: One thing I haven't considered is how to remove a course from a
# block. Perhaps the editor for block lessons should be separate?
# The copy function may not make sense – for payments it is not
# allowed; for lessons it is more or less superfluous (~same as add);
# for blocks it has no purpose if these are handled separately.
# Also note how the parameters are set in various tables. The room
# wish and pay details apply to all lesson components as they are set in
# COURSE_LESSONS. Only the time wish is set in the lesson component.
# This may be a bit restrictive, but is perhaps reasonable for most
# cases. If it is really essential to have a particular room for a
# particular lesson (and another one, or a choice, for another lesson),
# perhaps some additional constraint could be added ...

#?
        self.course_lesson_map = {}
        # key = block name; value = display row
        self.course_lesson_payment = 0 # for payment-only entries

        for rec in records:
            cldict = {fields[i]: val for i, val in enumerate(rec)}
            # <cldict> contains workload/payment and room-wish fields
            lg = cldict["lesson_group"]
            if lg:
                lgfields, lgrecord = db_read_unique_entry(
                    "LESSON_GROUP", lesson_group=lg
                )
                lgdata = {
                    lgfields[i]: val for i, val in enumerate(lgrecord)
                }
                # This contains the block-name, if any
                block_name = lgdata["BLOCK_NAME"]
                # Check uniqueness
                if block_name in self.course_lesson_map:
                    raise Bug("Multiple entries in COURSE_LESSONS"
                        f"for block '{block_name}', course {course}"
                    )
                    self.course_lesson_map[block_name] = row

                if block_name:
                    etype = 1
                    icon = self.icons["BLOCK"]
                else:
                    etype = 0
                    icon = self.icons["LESSON"]
                lfields, lrecords = db_read_full_table(
                    "LESSONS", lesson_group=lg
                )
                for lrec in lrecords:
                    self.lesson_table.insertRow(row)
                    ldata = {lfields[i]: val for i, val in enumerate(lrec)}
                    w = QTableWidgetItem(icon, "")
                    self.lesson_table.setItem(row, 0, w)
                    ln = ldata["LENGTH"]
                    w = QTableWidgetItem(ln)
                    self.lesson_table.setItem(row, 1, w)
                    if block_name:
                        w = QTableWidgetItem(block_name)
                        self.lesson_table.setItem(row, 2, w)
                    self.course_lessons.append((etype, cldict, lgdata, ldata))
                    row += 1
            else:
                # payment item
                if self.course_lesson_payment != 0:
                    raise Bug("Multiple entries in COURSE_LESSONS"
                        f"for payment-only item, course {course}"
                    )
#?
                self.course_lesson_payment = row

                self.lesson_table.insertRow(row)
                w = QTableWidgetItem(self.icons["PAY"], "")
                self.lesson_table.setItem(row, 0, w)
                w = QTableWidgetItem("–")
                self.lesson_table.setItem(row, 1, w)
                self.course_lessons.append((-1, cldict, lgdata, None))
                row += 1

#TODO: Is something like this needed?
# Toggle the stretch on the last section because of a possible bug in
# Qt, where the stretch can be lost when repopulating.
#        hh = table.horizontalHeader()
#        hh.setStretchLastSection(False)
#        hh.setStretchLastSection(True)

    def on_lesson_table_itemSelectionChanged(self):
        row = self.course_table.currentRow()
        print("§§§ on_lesson_table_itemSelectionChanged", row)
#TODO: populate the form fields
        etype, cldata, lgdata, ldata = self.course_lessons[row]
        if etype == -1:
            # payment entry
            self.lesson_length.clear()
            self.lesson_length.setEnabled(False)
            self.wish_room.clear()
            self.wish_room.setEnabled(False)
            self.block_name.clear()
            self.block_name.setEnabled(False)
            self.wish_time.clear()
            self.wish_time.setEnabled(False)
            self.parallel.clear()
            self.parallel.setEnabled(False)
            self.notes.clear()
            self.notes.setEnabled(False)
        else:
            self.lesson_length.setText(ldata["LENGTH"])
            self.lesson_length.setEnabled(True)
            self.wish_room.setText(cldata["ROOM"])
            self.wish_room.setEnabled(True)
            self.block_name.setText(lgdata["BLOCK_NAME"])
            self.block_name.setEnabled(True)
            self.wish_time.setText(ldata["TIME"])
            self.wish_time.setEnabled(True)
            records = db_read_table(
                "PARALLEL_LESSONS", ["TAG", "WEIGHTING"], lesson_id=ldata["id"]
            )
            if len(records) == 0:
                self.parallel.clear()
            elif len(records) == 1:
                t, w = records[0]
                self.parallel.setText(f'{t} @ {w}')
            else:
                raise Bug(
                    "Multiple PARALLEL_LESSONS entries for lesson"
                    f" with id {ldata['id']}"
                )
            self.parallel.setEnabled(True)
            self.notes.setPlainText(lgdata["NOTES"])
            self.notes.setEnabled(True)

        self.payment.setText(f'{cldata["WORKLOAD"]} * {cldata["PAY_FACTOR"]}')




#TODO
    def course_delete(self):
        """Delete the current course."""
        model = self.coursemodel
        if not SHOW_CONFIRM(T["REALLY_DELETE"]):
            return
        # course = self.editors["course"].text()
        index = self.coursetable.currentIndex()
        row = index.row()

        ## The BLOCKS table should have its "course" field (foreign
        ## key) defined as "ON DELETE CASCADE" to ensure that when
        ## a course is deleted also the associated activities are
        ## removed. Unfortunately this cannot propagate to the
        ## LESSONS table as the tags (LESSON_TAG) are not unique
        ## (so a foreign key constraint can't be used).
        ## This is handled by a "clean-up" function.
        # Get lesson tags:
        tags = set()
        for r in range(self.blockmodel.rowCount()):
            tag = self.blockmodel.record(r).value("LESSON_TAG")
            if tag:
                tags.add(tag)

        model.removeRow(row)
        if model.submitAll():
            # print("DELETED:", course)

            # Clean up LESSONS table
            for tag in tags:
                clean_lessons_table(tag)

            # Select a new row
            if row >= model.rowCount():
                row = model.rowCount() - 1
            self.coursetable.selectRow(row)
            if not self.coursetable.currentIndex().isValid():
                self.course_changed(-1)
        else:
            error = model.lastError()
            SHOW_ERROR(error.text())
            model.revertAll()


#### Below is old code! ####



class _CourseEditor(QSplitter):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setChildrenCollapsible(False)

        leftframe = QFrame()
        self.addWidget(leftframe)
        leftframe.setLineWidth(2)
        leftframe.setFrameShape(self.Box)
        vbox1 = QVBoxLayout(leftframe)

        # Course table title and filter settings
        hbox1 = QHBoxLayout()
        vbox1.addLayout(hbox1)
        hbox1.addWidget(QLabel(f"<h4>{T['COURSE_TITLE']}</h4>"))
        hbox1.addStretch(1)
        hbox1.addWidget(QLabel(f"<h5>{T['FILTER']}</h5>"))
        self.filter_field_select = KeySelector(
            value_mapping=FILTER_FIELDS, changed_callback=self.set_filter_field
        )
        hbox1.addWidget(self.filter_field_select)
        self.filter_value_select = KeySelector(changed_callback=self.set_filter)
        hbox1.addWidget(self.filter_value_select)

        # The course table itself
        self.coursetable = RowSelectTable(name="courses")
        self.coursetable.set_callback(self.course_changed)
        self.coursetable.activated.connect(self.course_activate)
        self.coursetable.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )  # non-editable
        self.coursetable.verticalHeader().hide()
        vbox1.addWidget(self.coursetable)

        # Course management buttons
        vbox1.addSpacing(10)
        bbox1 = QHBoxLayout()
        vbox1.addLayout(bbox1)
        bbox1.addStretch(1)
        self.course_delete_button = QPushButton(T["DELETE"])
        bbox1.addWidget(self.course_delete_button)
        self.course_delete_button.clicked.connect(self.course_delete)
        self.course_dialog = CourseEditorForm()
        edit_button = QPushButton(T["EDIT"])
        bbox1.addWidget(edit_button)
        edit_button.clicked.connect(self.edit_course)

        self.rightframe = QFrame()
        self.addWidget(self.rightframe)
        self.rightframe.setLineWidth(2)
        self.rightframe.setFrameShape(QFrame.Box)

        vbox2 = QVBoxLayout(self.rightframe)
        #        vbox2.addStretch(1)

        vbox2.addWidget(QLabel(f"<h4>{T['LESSONS']}</h4>"))

        # The blocks table
        self.blocktable = RowSelectTable(name="activities")
        self.blocktable.setMinimumHeight(80)
        self.blocktable.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )  # non-editable
        # self.blocktable.verticalHeader().hide()
        self.blocktable.set_callback(self.block_selected)
        vbox2.addWidget(self.blocktable)

        self.field_lines = {}
        self.stack = QStackedLayout()
        vbox2.addLayout(self.stack)

        ### Page: No existing entries
        empty_page = QLabel(T["NO_ENTRIES_FOR_COURSE"])
        self.stack.addWidget(empty_page)

        ### Page: Block/plain entry
        self.stack.addWidget(BlockLesson(self))

        ### Page: "Extra" entry (no timetable, but payment entry)
        self.stack.addWidget(NonLesson(self))

        vbox2.addWidget(QLabel(T["NOTES"] + ":"))
        self.note_editor = QLineEdit()
        self.note_editor.editingFinished.connect(self.notes_changed)
        vbox2.addWidget(self.note_editor)

        vbox2.addSpacing(20)
        vbox2.addStretch(1)
        vbox2.addWidget(HLine())
        self.block_delete_button = QPushButton(T["DELETE"])
        vbox2.addWidget(self.block_delete_button)
        self.block_delete_button.clicked.connect(self.block_delete)

        block_add_plain = QPushButton(T["NEW_PLAIN"])
        vbox2.addWidget(block_add_plain)
        block_add_plain.clicked.connect(self.block_add_plain)
        block_add_block = QPushButton(T["NEW_BLOCK"])
        vbox2.addWidget(block_add_block)
        block_add_block.clicked.connect(self.block_add_block)
        block_add_payment = QPushButton(T["NEW_EXTRA"])
        vbox2.addWidget(block_add_payment)
        block_add_payment.clicked.connect(self.block_add_payment)

        self.setStretchFactor(0, 1)  # stretch only left panel

    def course_activate(self, modelindex):
        self.edit_course()

    def edit_course(self):
        row = self.course_dialog.activate(
            self.current_row, (self.filter_field, self.filter_value)
        )
        if row >= 0:
            self.coursetable.selectRow(row)

    def set_filter_field(self, field):
        self.filter_value_select.set_items(self.filter_list[field])
        # print("FILTER FIELD:", field)
        self.filter_field = field
        self.filter_value_select.trigger()
        return True

    def set_filter(self, key):
        # print("FILTER KEY:", key)
        self.filter_value = key
        self.fill_course_table(key)
        return True

    def init_data(self):
        """Set up the course model, first clearing the "model-view"
        widgets (in case this is a reentry).
        """
        self.coursetable.setModel(None)
        self.blocktable.setModel(None)
        #        for f in FOREIGN_FIELDS:
        #            self.editors[f].clear()

        self.coursemodel = QSqlTableModel()
        self.coursemodel.setTable("COURSES")
        self.coursemodel.setEditStrategy(
            QSqlTableModel.EditStrategy.OnManualSubmit
        )
        # Set up the course view
        self.coursetable.setModel(self.coursemodel)
        self.coursetable.hideColumn(0)

        self.filter_list = {}
        for f, t in COURSE_COLS:
            i = self.coursemodel.fieldIndex(f)
            if f == "CLASS":
                kv = Classes().get_class_list(skip_null=False)
                self.filter_list[f] = kv
                # delegate = ForeignKeyItemDelegate(kv, parent=self.coursemodel)
                # self.coursetable.setItemDelegateForColumn(i, delegate)
            if f == "SUBJECT":
                kv = get_subjects()
                self.filter_list[f] = kv
                delegate = ForeignKeyItemDelegate(kv, parent=self.coursemodel)
                self.coursetable.setItemDelegateForColumn(i, delegate)
            elif f == "TEACHER":
                teachers = Teachers()
                kv = [
                    (tid, teachers.name(tid))
                    for tid, tiddata in teachers.items()
                ]
                self.filter_list[f] = kv
                delegate = ForeignKeyItemDelegate(kv, parent=self.coursemodel)
                self.coursetable.setItemDelegateForColumn(i, delegate)
            self.coursemodel.setHeaderData(i, Qt.Horizontal, t)
        self.course_dialog.init(self.coursemodel, self.filter_list)

        # Set up the blocks model
        self.blockmodel = QSqlTableModel()
        self.blockmodel.setTable("BLOCKS")
        self.blockmodel.setEditStrategy(
            QSqlTableModel.EditStrategy.OnManualSubmit
        )
        # Set up the blocks view
        self.blocktable.setModel(self.blockmodel)
        for f, t in BLOCK_COLS:
            i = self.blockmodel.fieldIndex(f)
            self.blockmodel.setHeaderData(i, Qt.Horizontal, t)
            if f not in BLOCKCOLS_SHOW:
                self.blocktable.hideColumn(i)
        #        self.simple_lesson_dialog.init(self.blockmodel)
        #        self.block_lesson_dialog.init(self.blockmodel)

        self.filter_field_select.trigger()

    def fill_course_table(self, filter_value):
        """Set filter and sort criteria, then populate table."""
        self.coursemodel.setFilter(f'{self.filter_field} = "{filter_value}"')
        self.coursemodel.setSort(
            self.coursemodel.fieldIndex(
                "SUBJECT" if self.filter_field == "CLASS" else "CLASS"
            ),
            Qt.AscendingOrder,
        )
        # print("SELECT:", self.coursemodel.selectStatement())
        self.coursemodel.select()
        self.coursetable.selectRow(0)
        if not self.coursetable.currentIndex().isValid():
            self.course_changed(-1)
        self.coursetable.resizeColumnsToContents()


    def redisplay(self):
        """Call this after updates to the current lesson data in the
        database. Redisplay the information.
        """
        self.blockmodel.select()
        self.blocktable.selectRow(self.current_lesson)

    def block_selected(self, row):
        self.current_lesson = row
        # print("SELECT LESSON", row)
        self.note_editor.clear()
        if row < 0:
            self.stack.setCurrentIndex(0)
            self.block_delete_button.setEnabled(False)
            self.note_editor.setEnabled(False)
            return
        self.block_delete_button.setEnabled(True)
        self.note_editor.setEnabled(True)
        record = self.blockmodel.record(row)
        block_tag = record.value("LESSON_TAG")
        if block_tag:
            self.stack.setCurrentIndex(1)
        else:
            self.stack.setCurrentIndex(2)
        self.block_id = record.value("id")
        self.note_editor.setText(record.value("NOTES"))
        self.stack.currentWidget().set_data(record)

    def notes_changed(self):
        text = self.note_editor.text()
        # print("§§§ NOTES CHANGED:", text)
        db_update_field("BLOCKS", "NOTES", text, id=self.block_id)
        self.redisplay()

    def block_add_plain(self):
        """Add a new "lesson", copying the current one if possible."""
        if not self.this_course:
            # No lessons can be added
            SHOW_WARNING(T["NO_COURSE_SO_NO_LESSONS"])
            return
        model = self.blockmodel
        index = self.blocktable.currentIndex()
        if index.isValid():
            row = index.row()
            # model.select()  # necessary to ensure current row is up to date
            record = model.record(row)
            record.setValue("id", None)
            n = model.rowCount()
        else:
            record = model.record()
            record.setValue("course", self.this_course)
            record.setValue("ROOM", "$")
            n = 0
        # Construct a block/lesson tag distinct from any existing ones
        tags = db_values("BLOCKS", "LESSON_TAG", course=self.this_course)
        tag0 = str(get_coursedata())
        tag = tag0
        i = 0
        while tag in tags:
            i += 1
            tag = f"{tag0}.{i}"
        record.setValue("PAYMENT", f"*{get_payment_weights()[0][0]}")
        record.setValue("LESSON_TAG", tag)
        record.setValue("NOTES", "")
        if model.insertRecord(-1, record) and model.submitAll():
            # lid = model.query().lastInsertId()
            # print("INSERTED:", lid, model.rowCount())
            self.blocktable.selectRow(n)
        else:
            SHOW_ERROR(f"DB Error: {model.lastError().text()}")
            model.revertAll()

    def block_add_block(self):
        """Add a new "block lesson", copying the current one if possible."""
        # print("ADD BLOCK MEMBER", self.this_course)
        if not self.this_course:
            # No lessons can be added
            SHOW_WARNING(T["NO_COURSE_SO_NO_LESSONS"])
            return
        model = self.blockmodel
        index = self.blocktable.currentIndex()
        if index.isValid():
            row = index.row()
            # model.select()  # necessary to ensure current row is up to date
            record = model.record(row)
            record.setValue("id", None)
            n = model.rowCount()
        else:
            record = model.record()
            record.setValue("course", self.this_course)
            record.setValue("ROOM", "$")
            n = 0
        bsid = BlockTagDialog.sidtag2value(get_coursedata().SUBJECT, "")
        tag = BlockTagDialog.popup(bsid, force_changed=True)
        # print("§ block tag:", tag)
        if not tag:
            if tag is not None:
                SHOW_ERROR(T["BLOCK_WITH_NO_TAG"])
            return
        # Don't allow repeated use of a tag already used for this
        # course
        if db_values("BLOCKS", "id", course=self.this_course, LESSON_TAG=tag):
            SHOW_ERROR(T["BLOCK_TAG_CLASH"].format(tag=tag))
            return
        record.setValue("PAYMENT", f"*{get_payment_weights()[0][0]}")
        record.setValue("LESSON_TAG", tag)
        record.setValue("NOTES", "")
        if model.insertRecord(-1, record) and model.submitAll():
            # lid = model.query().lastInsertId()
            # print("INSERTED:", lid, model.rowCount())
            self.blocktable.selectRow(n)
        else:
            SHOW_ERROR(f"DB Error: {model.lastError().text()}")
            model.revertAll()

    def block_add_payment(self):
        """Add a new "payment" entry."""
        # print("ADD 'EXTRA' ENTRY", self.this_course)
        if not self.this_course:
            # No lessons can be added
            SHOW_WARNING(T["NO_COURSE_SO_NO_LESSONS"])
            return
        model = self.blockmodel
        # Create a basic "payment" entry
        record = model.record()
        record.setValue("course", self.this_course)
        record.setValue("PAYMENT", f"1*{get_payment_weights()[0][0]}")
        #        record.setValue("NOTES", "")
        n = model.rowCount()
        if model.insertRecord(-1, record) and model.submitAll():
            # lid = model.query().lastInsertId()
            # print("INSERTED:", lid, model.rowCount())
            self.blocktable.selectRow(n)
        else:
            SHOW_ERROR(f"DB Error: {model.lastError().text()}")
            model.revertAll()

    def block_delete(self):
        """Delete the current "lesson block".
        Note that deletion of this record can leave "floating"
        sublessons, which should also be removed.
        """
        model = self.blockmodel
        index = self.blocktable.currentIndex()
        row = index.row()
        # model.select()  # necessary to ensure current row is up to date
        record = model.record(row)
        lesson_tag = record.value("LESSON_TAG")
        if model.removeRow(row) and model.submitAll():
            # model.select()
            n = model.rowCount()
            if n:
                if row and row >= n:
                    row = n - 1
                self.blocktable.selectRow(row)
            else:
                self.block_selected(-1)
        else:
            SHOW_ERROR(f"DB Error: {model.lastError().text()}")
            model.revertAll()
            return
        if lesson_tag:
            # If there are no other lesson-blocks sharing the lesson-tag,
            # remove any sublessons
            clean_lessons_table(lesson_tag)


def clean_lessons_table(tag=None):
    """Clean up LESSONS table by removing entries with tags which have
    no corresponding entries in the BLOCKS table.
    By passing in a tag, just this can be checked (and its entries deleted).
    """
    if tag:
        tags = [tag]
    else:
        tags = db_values("LESSONS", "TAG")
    for tag in tags:
        if not courses_with_lessontag(tag):
            db_delete_rows("LESSONS", TAG=tag)


class _BlockLesson(QWidget):
    def __init__(self, main_widget, parent=None):
        self.main_widget = main_widget
        super().__init__(parent=parent)
        form = QFormLayout(self)
        form.setContentsMargins(0, 0, 0, 0)
        self.editors = {}
        f = "ROOM"
        editwidget = RoomSelector(modified=self.room_changed)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)

        f = "Block_subject"
        editwidget = BlockTagSelector(modified=self.block_changed)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)

        # "Sublesson" table
        self.lesson_table = TableWidget()
        self.lesson_table.setMinimumHeight(150)
        self.lesson_table.setSelectionMode(
            QTableView.SelectionMode.SingleSelection
        )
        self.lesson_table.setSelectionBehavior(
            QTableView.SelectionBehavior.SelectRows
        )
        #        self.lesson_table.cellChanged.connect(self.sublesson_table_changed)

        self.lesson_table.setColumnCount(6)
        self.lesson_table.setHorizontalHeaderLabels(
#TODO: Do I really want to have PLACEMENT and ROOMS here?
            (T["id"], T["TAG"], T["LENGTH"], T["TIME"], T["PLACEMENT"], T["ROOMS"])
        )
        self.lesson_table.hideColumn(0)
        self.lesson_table.hideColumn(1)
        Hhd = self.lesson_table.horizontalHeader()
        Hhd.setMinimumSectionSize(60)
        self.lesson_table.resizeColumnsToContents()
        Hhd.setStretchLastSection(True)

        # Set column editors
        delegate = DurationDelegate(
            self.lesson_table, modified=self.length_changed
        )
        self.lesson_table.setItemDelegateForColumn(2, delegate)
        delegate = DayPeriodDelegate(
            self.lesson_table, modified=self.time_changed
        )
        self.lesson_table.setItemDelegateForColumn(3, delegate)
        form.addRow(self.lesson_table)

        bb0 = QDialogButtonBox()
        bt_new = bb0.addButton("+", QDialogButtonBox.ButtonRole.ActionRole)
        bt_new.setFixedWidth(30)
        bt_new.setToolTip(T["SELECT_TO_COPY_LENGTH"])
        bt_del = bb0.addButton("–", QDialogButtonBox.ButtonRole.ActionRole)
        bt_del.setFixedWidth(30)
        bt_del.setToolTip(T["DELETE_SELECTED"])
        bt_new.clicked.connect(self.block_add)
        bt_del.clicked.connect(self.block_del)
        self.bt_del = bt_del
        form.addRow(bb0)

        f = "PAYMENT"
        editwidget = PaymentSelector(modified=self.payment_changed)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)

    def set_data(self, record):
        self.block_id = record.value("id")
        self.course_id = record.value("course")
        block_tag = record.value("LESSON_TAG")
        self.editors["PAYMENT"].setText(record.value("PAYMENT"))
        self.editors["ROOM"].setText(record.value("ROOM"))
        edb = self.editors["Block_subject"]
        edb.set_block(block_tag)
        self.show_sublessons(edb.get_block())

    def show_sublessons(self, block_tag):
        slist = sublessons(block_tag, reset=True)
        # print(" ...", slist)
        ltable = self.lesson_table
        self.__ltable_ready = False
        ltable.clearContents()
        ltable.setRowCount(len(slist))
        r = 0
        for s in slist:
            ltable.setItem(r, 0, QTableWidgetItem(str(s.id)))
            ltable.setItem(r, 1, QTableWidgetItem(s.TAG))
            ltable.setItem(r, 2, QTableWidgetItem(str(s.LENGTH)))
            t = s.TIME
            if t and '.' not in t:
                # Show weighting of "simultaneous" tag
                t = f"{t}@{get_simultaneous_weighting(t)}"
            ltable.setItem(r, 3, QTableWidgetItem(t))
#TODO?
            ltable.setItem(r, 4, QTableWidgetItem(s.PLACEMENT))
            ltable.setItem(r, 5, QTableWidgetItem(s.ROOMS))
            r += 1
        self.bt_del.setEnabled(bool(slist))
        self.__ltable_ready = True

    def block_changed(self, tag):
        # print("§ block changed:", tag)
        __tags = db_values("BLOCKS", "LESSON_TAG", course=self.course_id)
        if tag in __tags:
            SHOW_ERROR(T["BLOCK_TAG_CLASH"].format(tag=tag))
            return False
        db_update_field("BLOCKS", "LESSON_TAG", tag, id=self.block_id)
        self.main_widget.redisplay()
        ### After a redisplay of the main widget it would be superfluous
        ### for a callback handler to update its cell, so <False> is
        ### returned to suppress this update.
        return False

    def room_changed(self, text):
        db_update_field("BLOCKS", "ROOM", text, id=self.block_id)
        self.main_widget.redisplay()
        return False

    def payment_changed(self, text):
        db_update_field("BLOCKS", "PAYMENT", text, id=self.block_id)
        self.main_widget.redisplay()
        return False

    def length_changed(self, row, new_value):
        sublesson_id = int(self.lesson_table.item(row, 0).text())
        return db_update_field("LESSONS", "LENGTH", new_value, id=sublesson_id)

    def time_changed(self, row, new_value):
        sublesson_id = int(self.lesson_table.item(row, 0).text())
        try:
            tag, _weighting = new_value.split("@", 1)
        except ValueError:
            tag = new_value
        else:
            weighting = int(_weighting)
            # A "simultaneous" tag
            try:
                w = get_simultaneous_weighting(tag, with_default=False)
            except NoRecord:
                # Add record
                db_new_row(
                    "PARALLEL_LESSONS", TAG=tag, WEIGHTING=weighting
                )
#TODO: There should be some cleaning of the table somewhere ...
            else:
                if w != int(weighting):
                    # Update record
                    db_update_field(
                        "PARALLEL_LESSONS",
                        "WEIGHTING",
                        weighting,
                        TAG=tag
                    )
        if db_update_field("LESSONS", "TIME", tag, id=sublesson_id):
            return new_value
        return None

    def block_add(self):
        row = self.lesson_table.currentRow()
        if row >= 0:
            length = self.lesson_table.item(row, 2).text()
        else:
            length = "1"
        editor = self.editors["Block_subject"]
        block_tag = editor.get_block()
        db_new_row("LESSONS", TAG=block_tag, LENGTH=length, TIME="")
        self.show_sublessons(block_tag)

    def block_del(self):
        row = self.lesson_table.currentRow()
        if row >= 0:
            sublesson_id = int(self.lesson_table.item(row, 0).text())
            db_delete_rows("LESSONS", id=sublesson_id)
            editor = self.editors["Block_subject"]
            block_tag = editor.get_block()
            self.show_sublessons(block_tag)
        else:
            SHOW_WARNING(T["DELETE_SELECTED"])


class _NonLesson(QWidget):
    def __init__(self, main_widget, parent=None):
        self.main_widget = main_widget
        super().__init__(parent=parent)
        form = QFormLayout(self)
        form.setContentsMargins(0, 0, 0, 0)
        self.editors = {}
        f = "PAYMENT"
        editwidget = PaymentSelector(modified=self.payment_changed)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)

    def set_data(self, record):
        self.block_id = record.value("id")
        self.course_id = record.value("course")
        self.editors["PAYMENT"].setText(record.value("PAYMENT"))

    def payment_changed(self, text):
        # print("$ UPDATE PAY_FACTOR:", text)
        db_update_field("BLOCKS", "PAYMENT", text, id=self.block_id)
        self.main_widget.redisplay()
        return False


class _CourseEditorForm(QDialog):
    def __init__(self):
        super().__init__()
        vbox0 = QVBoxLayout(self)
        form = QFormLayout()
        vbox0.addLayout(form)
        self.editors = {}
        for f, t in COURSE_COLS:
            if f == "course":
                editwidget = QLineEdit()
                editwidget.setReadOnly(True)
                editwidget.__real = False
            elif f in FOREIGN_FIELDS:
                editwidget = FormComboBox(f, self.form_modified)
                editwidget.__real = True
            elif f == "GRP":
                editwidget = GroupSelector(f, self.form_modified)
                editwidget.__real = True
            else:
                editwidget = FormLineEdit(f, self.form_modified)
                editwidget.__real = True
            self.editors[f] = editwidget
            if editwidget.__real:
                form.addRow(t, editwidget)
        vbox0.addWidget(HLine())
        buttonBox = QHBoxLayout()
        vbox0.addLayout(buttonBox)
        self.course_add_button = QPushButton(T["NEW"])
        self.course_add_button.setIcon(QIcon.fromTheme("icon_new"))
        buttonBox.addWidget(self.course_add_button)
        buttonBox.addStretch(1)
        self.course_update_button = QPushButton(T["APPLY"])
        self.course_update_button.setIcon(QIcon.fromTheme("icon_ok"))
        buttonBox.addWidget(self.course_update_button)
        bt_cancel = QPushButton(T["CANCEL"])
        bt_cancel.setIcon(QIcon.fromTheme("icon_cancel"))
        bt_cancel.setDefault(True)
        buttonBox.addWidget(bt_cancel)
        bt_cancel.clicked.connect(self.reject)
        self.course_update_button.clicked.connect(self.course_update)
        self.course_add_button.clicked.connect(self.course_add)

    def closeEvent(self, event):
        """Prevent dialog closure if there are changes."""
        if self.modified() and not LoseChangesDialog():
            event.ignore()
        else:
            event.accept()

    def modified(self):
        return bool(self.form_change_set)

    def clear_modified(self):
        self.form_change_set = set()

    def init(self, model, keymaps):
        self.model = model
        self.table_empty = None
        for f, kv in keymaps.items():
            editwidget = self.editors[f]
            editwidget.setup(kv)

    def activate(self, row, filter_field=None):
        """Initialize the dialog with values from the current course
        and show it.

        The idea behind the extra parameter is that, on empty tables, at
        least the filter field should be set. To do that here, this
        field and its value must be passed as a tuple: (field, value).
        """
        self.clear_modified()
        self.current_row = row
        if row >= 0:
            self.table_empty = False
            record = self.model.record(row)
            for f, t in COURSE_COLS:
                self.editors[f].setText(str(record.value(f)))
        else:
            # print("EMPTY TABLE")
            self.table_empty = True
            for f, t in COURSE_COLS:
                self.editors[f].setText("")
            if filter_field:
                self.editors[filter_field[0]].setText(filter_field[1])
        self.form_modified("", False)  # initialize form button states

        self.__value = -1  # Default return value => don't change row
        self.exec()
        return self.__value

    def return_value(self, row):
        """Quit the dialog, returning the given row number.
        Value -1 => don't change row, otherwise select the given row.
        """
        self.__value = row
        self.accept()

    def course_add(self):
        """Add the data in the form editor as a new course."""
        model = self.model
        row = 0
        model.insertRow(row)
        for f, t in COURSE_COLS[1:]:
            col = model.fieldIndex(f)
            val = self.editors[f].text()
            if f == "CLASS":
                klass = val
            model.setData(model.index(row, col), val)
        if model.submitAll():
            course = model.query().lastInsertId()
            # print("INSERTED:", course)
            for r in range(model.rowCount()):
                if model.data(model.index(r, 0)) == course:
                    self.return_value(r)  # Select this row
                    break
            else:
                SHOW_INFO(T["COURSE_ADDED"].format(klass=klass))
                self.return_value(self.current_row)  # Reselect current row
        else:
            error = model.lastError()
            if "UNIQUE" in error.databaseText():
                SHOW_ERROR(T["COURSE_EXISTS"])
            else:
                SHOW_ERROR(error.text())
            model.revertAll()

    def course_update(self):
        """Update the current course with the data in the form editor."""
        model = self.model
        row = self.current_row
        course = model.data(model.index(row, model.fieldIndex("course")))
        for f in self.form_change_set:
            col = model.fieldIndex(f)
            val = self.editors[f].text()
            model.setData(model.index(row, col), val)
        if model.submitAll():
            # The selection is lost – the changed row may even be in a
            # different place, perhaps not even displayed.
            # Try to stay with the same id, if it is displayed,
            # otherwise the same (or else the last) row.
            # print("UPDATED:", course)
            for r in range(model.rowCount()):
                if model.data(model.index(r, 0)) == course:
                    self.return_value(r)  # Select this row
                    break
            else:
                if row >= model.rowCount():
                    row = model.rowCount() - 1
                    self.return_value(row)  # Select this row
        else:
            error = model.lastError()
            if "UNIQUE" in error.databaseText():
                SHOW_ERROR(T["COURSE_EXISTS"])
            else:
                SHOW_ERROR(error.text())
            model.revertAll()

    def form_modified(self, field, changed):
        """Handle a change in a form editor field.
        Maintain the set of changed fields (<self.form_change_set>).
        Enable and disable the pushbuttons appropriately.
        """
        if self.table_empty:
            self.course_update_button.setEnabled(False)
            self.course_add_button.setEnabled(True)
        elif self.table_empty == None:
            # ignore – not yet set up
            return
        elif changed:
            self.course_update_button.setEnabled(True)
            self.form_change_set.add(field)
            if field in COURSE_KEY._fields:
                self.course_add_button.setEnabled(True)
        else:
            self.form_change_set.discard(field)
            if self.form_change_set:
                if not self.form_change_set.intersection(COURSE_KEY._fields):
                    self.course_add_button.setEnabled(False)
            else:
                self.course_update_button.setEnabled(False)
                self.course_add_button.setEnabled(False)
        # print("FORM CHANGED SET:", self.form_change_set)


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from ui.ui_base import run

    widget = CourseEditorPage()
    widget.enter()
    widget.resize(1000, 550)
    run(widget)