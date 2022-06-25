"""
ui/modules/course_lessons.py

Last updated:  2022-06-25

Edit course and lesson data.


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

########################################################################

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

T = TRANSLATIONS("ui.modules.course_lessons")

### +++++

from core.db_management import (
    open_database,
    db_key_value_list,
    db_update_field,
    db_new_row,
    db_delete_rows,
    db_values,
)
from core.teachers import Teachers
from core.classes import Classes

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
    ### QtGui:
    ### QtCore:
    Qt,
    ### QtSql:
    QSqlTableModel,
)

from ui.course_dialogs import (
    get_payroll_weights,
    get_subjects,
    set_coursedata,
    get_coursedata,
    DurationSelector,
    DayPeriodSelector,
    PartnersSelector,
    PayrollSelector,
    RoomSelector,
    partners,
    sublessons,
    DayPeriodDelegate,
    DurationDelegate,
    PartnersDelegate,
    BlockTagSelector,
    BlockTagDialog,
    parse_time_field,
    get_time_entry,
    TableWidget,
    block_courses,
)

# Course table fields
COURSE_COLS = [
    (f, T[f])
    for f in (
        "course",
        "CLASS",
        "GRP",
        "SUBJECT",
        "TEACHER",
        "REPORT",
        "GRADE",
        "COMPOSITE",
    )
]
# SUBJECT, CLASS and TEACHER are foreign keys with:
#  on delete cascade + on update cascade
FOREIGN_FIELDS = ("CLASS", "TEACHER", "SUBJECT")

FILTER_FIELDS = [cc for cc in COURSE_COLS if cc[0] in FOREIGN_FIELDS]

# Group of fields which determines a course (the tuple must be unique)
COURSE_KEY_FIELDS = ("CLASS", "GRP", "SUBJECT", "TEACHER")

LESSON_COLS = [
    (f, T[f])
    for f in (
        "id",
        "course",
        "LENGTH",
        "PAYROLL",
        "ROOM",
        "TIME",
        "PLACE",
        "NOTES",
    )
]

LESSONCOLS_SHOW = ("LENGTH", "PAYROLL", "TIME")

### -----


def init():
    MAIN_WIDGET.add_tab(Courses())


class Courses(Page):
    name = T["MODULE_NAME"]
    title = T["MODULE_TITLE"]

    def __init__(self):
        super().__init__()
        self.course_editor = CourseEditor()
        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.course_editor)

    def enter(self):
        open_database()
        self.course_editor.init_data()


# ++++++++++++++ The widget implementation ++++++++++++++


class CourseEditor(QSplitter):
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

        # The lesson table
        self.lessontable = RowSelectTable(name="lessons")
        self.lessontable.setMinimumHeight(120)
        self.lessontable.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )  # non-editable
        # self.lessontable.verticalHeader().hide()
        self.lessontable.set_callback(self.lesson_selected)
        vbox2.addWidget(self.lessontable)

        self.field_lines = {}
        self.stack = QStackedLayout()
        vbox2.addLayout(self.stack)

        ### Page: No existing entries
        empty_page = QLabel(T["NO_LESSONS_FOR_COURSE"])
        self.stack.addWidget(empty_page)

        ### Page: Plain lesson entry
        self.stack.addWidget(PlainLesson(self))

        ### Page: Block member entry
        self.stack.addWidget(BlockLesson(self))

        ### Page: "Extra" entry (no timetable, but payroll entry)
        self.stack.addWidget(NonLesson(self))

        vbox2.addWidget(QLabel(T["NOTES"] + ":"))
        self.note_editor = QLineEdit()
        self.note_editor.editingFinished.connect(self.notes_changed)
        vbox2.addWidget(self.note_editor)

        vbox2.addSpacing(20)
        vbox2.addStretch(1)
        vbox2.addWidget(HLine())
        self.lesson_delete_button = QPushButton(T["DELETE"])
        vbox2.addWidget(self.lesson_delete_button)
        self.lesson_delete_button.clicked.connect(self.lesson_delete)

        lesson_add_plain = QPushButton(T["NEW_PLAIN"])
        vbox2.addWidget(lesson_add_plain)
        lesson_add_plain.clicked.connect(self.lesson_add_plain)
        lesson_add_block = QPushButton(T["NEW_BLOCK"])
        vbox2.addWidget(lesson_add_block)
        lesson_add_block.clicked.connect(self.lesson_add_block)
        lesson_add_payroll = QPushButton(T["NEW_EXTRA"])
        vbox2.addWidget(lesson_add_payroll)
        lesson_add_payroll.clicked.connect(self.lesson_add_payroll)

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
        self.lessontable.setModel(None)
        #        for f in FOREIGN_FIELDS:
        #            self.editors[f].clear()

        self.coursemodel = QSqlTableModel()
        self.coursemodel.setTable("COURSES")
        self.coursemodel.setEditStrategy(QSqlTableModel.OnManualSubmit)
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
                kv = [(tid, teachers.name(tid)) for tid, tiddata in teachers.items()]
                self.filter_list[f] = kv
                delegate = ForeignKeyItemDelegate(kv, parent=self.coursemodel)
                self.coursetable.setItemDelegateForColumn(i, delegate)
            self.coursemodel.setHeaderData(i, Qt.Horizontal, t)
        self.course_dialog.init(self.coursemodel, self.filter_list)

        # Set up the lesson model
        self.lessonmodel = QSqlTableModel()
        self.lessonmodel.setTable("LESSONS")
        self.lessonmodel.setEditStrategy(QSqlTableModel.OnManualSubmit)
        # Set up the lesson view
        self.lessontable.setModel(self.lessonmodel)
        for f, t in LESSON_COLS:
            i = self.lessonmodel.fieldIndex(f)
            self.lessonmodel.setHeaderData(i, Qt.Horizontal, t)
            if f not in LESSONCOLS_SHOW:
                self.lessontable.hideColumn(i)
        #        self.simple_lesson_dialog.init(self.lessonmodel)
        #        self.block_lesson_dialog.init(self.lessonmodel)

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

    def course_changed(self, row):
        self.current_row = row
        if row >= 0:
            # print("EXEC COURSE CHANGED:", row)
            record = self.coursemodel.record(row)
            self.set_course(record.value(0))
            self.course_delete_button.setEnabled(True)
            set_coursedata({f: record.value(f) for f in COURSE_KEY_FIELDS})
        else:
            # e.g. when entering an empty table
            # print("EMPTY TABLE")
            self.set_course(0)
            self.course_delete_button.setEnabled(False)
            set_coursedata({})

    def course_delete(self):
        """Delete the current course."""
        model = self.coursemodel
        if not SHOW_CONFIRM(T["REALLY_DELETE"]):
            return
        # course = self.editors["course"].text()
        index = self.coursetable.currentIndex()
        row = index.row()
        model.removeRow(row)
        if model.submitAll():
            # The LESSONS table should have its "course" field (foreign
            # key) defined as "ON DELETE CASCADE" to ensure that when
            # a course is deleted also the lessons are removed.
            # print("DELETED:", course)
            if row >= model.rowCount():
                row = model.rowCount() - 1
            self.coursetable.selectRow(row)
            if not self.coursetable.currentIndex().isValid():
                self.course_changed(-1)
        else:
            error = model.lastError()
            SHOW_ERROR(error.text())
            model.revertAll()

    def set_course(self, course):
        # print("SET COURSE:", course)
        self.this_course = course
        self.lessonmodel.setFilter(f"course = {course}")
        # print("SELECT:", self.lessonmodel.selectStatement())
        self.lessonmodel.select()
        self.lessontable.selectRow(0)
        self.lessontable.resizeColumnsToContents()
        if not self.lessonmodel.rowCount():
            # If there are no entries, method <lesson_selected> won't be
            # called automatically, so do it here.
            self.lesson_selected(-1)
        #        self.lesson_add_button.setEnabled(course > 0)

        # Toggle the stretch on the last section here because of a
        # possible bug in Qt, where the stretch can be lost when
        # repopulating.
        hh = self.lessontable.horizontalHeader()
        hh.setStretchLastSection(False)
        hh.setStretchLastSection(True)

    def redisplay(self):
        """Call this after updates to the current lesson data in the
        database. Redisplay the information.
        """
        self.lessonmodel.select()
        self.lessontable.selectRow(self.current_lesson)

    def lesson_selected(self, row):
        self.current_lesson = row
        # print("SELECT LESSON", row)
        self.note_editor.clear()
        if row >= 0:
            self.lesson_delete_button.setEnabled(True)
            self.note_editor.setEnabled(True)
        else:
            self.stack.setCurrentIndex(0)
            self.lesson_delete_button.setEnabled(False)
            self.note_editor.setEnabled(False)
            return
        record = self.lessonmodel.record(row)
        self.lesson_id = record.value("id")
        self.note_editor.setText(record.value("NOTES"))
        time_field = record.value("TIME")
        if time_field:
            if time_field.startswith(">"):
                # block member
                self.stack.setCurrentIndex(2)
                self.stack.currentWidget().set_data(record)
            else:
                # plain lesson
                self.stack.setCurrentIndex(1)
                self.stack.currentWidget().set_data(record)
        else:
            # "extra"
            self.stack.setCurrentIndex(3)
            self.stack.currentWidget().set_data(record)

    def notes_changed(self):
        text = self.note_editor.text()
        # print("§§§ NOTES CHANGED:", text)
        db_update_field("LESSONS", "NOTES", text, id=self.lesson_id)

    def lesson_add_plain(self):
        """Add a new "lesson", copying the current one if possible."""
        if not self.this_course:
            # No lessons can be added
            SHOW_WARNING(T["NO_COURSE_SO_NO_LESSONS"])
            return
        model = self.lessonmodel
        index = self.lessontable.currentIndex()
        if index.isValid():
            row = index.row()
            # model.select()  # necessary to ensure current row is up to date
            record = model.record(row)
            # print("RECORD:", [record.value(i) for i in range(record.count())])
            length = record.value("LENGTH")
            try:
                int(length)
            except ValueError:
                record.setValue("LENGTH", "1")
                record.setValue("PAYROLL", f"*{get_payroll_weights()[0][0]}")
                record.setValue("ROOM", "+")
            record.setValue("id", None)
            n = model.rowCount()
        else:
            # Create a basic "normal" lesson
            record = model.record()
            record.setValue("course", self.this_course)
            record.setValue("LENGTH", "1")
            record.setValue("PAYROLL", f"*{get_payroll_weights()[0][0]}")
            record.setValue("ROOM", "?")
            n = 0
        record.setValue("TIME", "@?")
        record.setValue("PLACE", "")
        record.setValue("NOTES", "")
        if model.insertRecord(-1, record) and model.submitAll():
            # lid = model.query().lastInsertId()
            # print("INSERTED:", lid, model.rowCount())
            self.lessontable.selectRow(n)
        else:
            SHOW_ERROR(f"DB Error: {model.lastError().text()}")
            model.revertAll()

    def lesson_add_block(self):
        """Add a new "block lesson", copying the current one if possible."""
        # print("ADD BLOCK MEMBER", self.this_course)
        if not self.this_course:
            # No lessons can be added
            SHOW_WARNING(T["NO_COURSE_SO_NO_LESSONS"])
            return
        model = self.lessonmodel
        index = self.lessontable.currentIndex()
        if index.isValid():
            row = index.row()
            # model.select()  # necessary to ensure current row is up to date
            record = model.record(row)
            t = record.value("TIME")
            if t.startswith(">"):
                bsid = BlockTagDialog.parse_block_tag(t)[0]
            else:
                bsid = get_coursedata()["SUBJECT"]
                record.setValue("PAYROLL", f"*{get_payroll_weights()[0][0]}")
            record.setValue("id", None)
            n = model.rowCount()
        else:
            record = model.record()
            record.setValue("course", self.this_course)
            record.setValue("ROOM", "+")
            record.setValue("PAYROLL", f"*{get_payroll_weights()[0][0]}")
            bsid = get_coursedata()["SUBJECT"]
            n = 0
        tag = BlockTagDialog.popup(bsid, "#")
        if not tag:
            return
        # print("§ block tag:", tag)
        if tag[0] == "+":
            # new tag
            tag = tag[1:]
        else:
            # Don't allow repeated use of a tag already used for this
            # course, or one which clashes in another way with an
            # existing lesson entry.
            if not check_new_time(self.this_course, tag):
                return
        record.setValue("LENGTH", "*")
        record.setValue("TIME", tag)
        record.setValue("PLACE", "")
        record.setValue("NOTES", "")
        if model.insertRecord(-1, record) and model.submitAll():
            # lid = model.query().lastInsertId()
            # print("INSERTED:", lid, model.rowCount())
            self.lessontable.selectRow(n)
        else:
            SHOW_ERROR(f"DB Error: {model.lastError().text()}")
            model.revertAll()

    def lesson_add_payroll(self):
        """Add a new "payroll" entry."""
        # print("ADD 'EXTRA' ENTRY", self.this_course)
        if not self.this_course:
            # No lessons can be added
            SHOW_WARNING(T["NO_COURSE_SO_NO_LESSONS"])
            return
        model = self.lessonmodel
        # Create a basic "payroll" entry
        record = model.record()
        record.setValue("course", self.this_course)
        record.setValue("LENGTH", "--")
        record.setValue("PAYROLL", f"1*{get_payroll_weights()[0][0]}")
        record.setValue("NOTES", "")
        n = model.rowCount()
        if model.insertRecord(-1, record) and model.submitAll():
            # lid = model.query().lastInsertId()
            # print("INSERTED:", lid, model.rowCount())
            self.lessontable.selectRow(n)
        else:
            SHOW_ERROR(f"DB Error: {model.lastError().text()}")
            model.revertAll()

    def lesson_delete(self):
        """Delete the current "lesson".
        Note that deletion of this record can leave "floating" sublessons
        and partner-time entries, which should also be removed.
        """
        model = self.lessonmodel
        index = self.lessontable.currentIndex()
        row = index.row()
        # model.select()  # necessary to ensure current row is up to date
        record = model.record(row)
        timefield = record.value("TIME")
        if model.removeRow(row) and model.submitAll():
            # model.select()
            n = model.rowCount()
            if n:
                if row and row >= n:
                    row = n - 1
                self.lessontable.selectRow(row)
            else:
                self.lesson_selected(-1)
        else:
            SHOW_ERROR(f"DB Error: {model.lastError().text()}")
            model.revertAll()
            return
        # print("§ timefield:", timefield)
        if timefield.startswith("="):
            # If there are no other partners with the original tag, remove
            # its lesson-time entry.
            # print("§ ...", partners(timefield[1:]))
            if not partners(timefield[1:]):
                # print("§ EMPTY TAG:", timefield)
                db_delete_rows("LESSONS", PLACE=timefield)
        elif timefield.startswith(">"):
            # A block entry, if there are none others sharing the block-tag,
            # remove any sublessons – and also any partner-times they
            # have as unique reference.
            if not block_courses(timefield):
                # Delete sublessons
                for sl in sublessons(timefield):
                    db_delete_rows("LESSONS", id=sl.id)
                    tag = sl.TIME
                    # print("§§ ...", tag)
                    if tag.startswith("="):
                        # print("§§$ ...", partners(tag[1:]))
                        if not partners(tag[1:]):
                            # print("§ EMPTY TAG:", tag)
                            db_delete_rows("LESSONS", PLACE=tag)


class PlainLesson(QWidget):
    def __init__(self, main_widget, parent=None):
        self.main_widget = main_widget
        super().__init__(parent=parent)
        form = QFormLayout(self)
        form.setContentsMargins(0, 0, 0, 0)
        self.editors = {}
        f = "LENGTH"
        editwidget = DurationSelector(modified=self.length_changed)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)
        f = "ROOM"
        editwidget = RoomSelector(modified=self.room_changed)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)
        # TIME: embraces "partners" as well as the actual placement time
        f = "Partners"
        editwidget = PartnersSelector(modified=self.partners_changed)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)
        f = "Time"
        timefield = DayPeriodSelector(modified=self.time_changed)
        self.editors[f] = timefield
        form.addRow(T[f], timefield)
        f = "PLACE"
        editwidget = QLineEdit()
        editwidget.setToolTip(T["PLACE_NOT_EDITABLE"])
        editwidget.setReadOnly(True)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)
        f = "PAYROLL"
        editwidget = PayrollSelector(modified=self.payroll_changed)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)

    def set_data(self, record):
        self.lesson_id = record.value("id")
        self.course_id = record.value("course")
        ltime, tag = parse_time_field(record.value("TIME"))
        self.editors["Partners"].setText(tag)
        self.editors["Time"].setText(ltime)
        self.editors["LENGTH"].setText(record.value("LENGTH"))
        self.editors["PAYROLL"].setText(record.value("PAYROLL"))
        self.editors["ROOM"].setText(record.value("ROOM"))
        self.editors["PLACE"].setText(record.value("PLACE"))

    ### After a redisplay of the main widget it would be inappropriate
    ### for a callback handler to update its cell, so <False> is returned
    ### to suppress this update.

    def length_changed(self, text):
        # print("$ UPDATE LENGTH:", text)
        db_update_field("LESSONS", "LENGTH", text, id=self.lesson_id)
        self.main_widget.redisplay()
        return False

    def room_changed(self, text):
        # print("$ UPDATE ROOM:", text)
        db_update_field("LESSONS", "ROOM", text, id=self.lesson_id)
        self.main_widget.redisplay()
        return False

    def time_changed(self, text):
        # print("$ UPDATE TIME:", text)
        # The action to take depends on whether there is a partner tag.
        ptag = self.editors["Partners"].text()
        if ptag:
            if not check_new_time(self.course_id, f"={ptag}"):
                return False
        elif not check_new_time(self.course_id, f"@{text}"):
            return False
        db_update_time(self.lesson_id, text, ptag, self.course_id)
        self.main_widget.redisplay()
        return False

    def partners_changed(self, text):
        # print("$ UPDATE PARTNERS TAG:", text)
        oldtime = self.editors["Time"].text()
        oldpartners = self.editors["Partners"].text()
        db_update_partners(
            self.lesson_id, text, oldpartners, oldtime, self.course_id
        )
        self.main_widget.redisplay()
        return False

    def payroll_changed(self, text):
        # print("$ UPDATE PAYROLL:", text)
        db_update_field("LESSONS", "PAYROLL", text, id=self.lesson_id)
        self.main_widget.redisplay()
        return False


class BlockLesson(QWidget):
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
        self.lesson_table.setMinimumHeight(120)
        self.lesson_table.setSelectionMode(
            QTableView.SelectionMode.SingleSelection
        )
        self.lesson_table.setSelectionBehavior(
            QTableView.SelectionBehavior.SelectRows
        )
        #        self.lesson_table.cellChanged.connect(self.sublesson_table_changed)

        self.lesson_table.setColumnCount(4)
        self.lesson_table.setHorizontalHeaderLabels(
            (T["id"], T["LENGTH"], T["Time"], T["Partners"])
        )
        self.lesson_table.hideColumn(0)
        Hhd = self.lesson_table.horizontalHeader()
        Hhd.setMinimumSectionSize(60)
        self.lesson_table.resizeColumnsToContents()
        Hhd.setStretchLastSection(True)

        # Set column editors
        delegate = DurationDelegate(
            self.lesson_table, modified=self.length_changed
        )
        self.lesson_table.setItemDelegateForColumn(1, delegate)
        delegate = DayPeriodDelegate(
            self.lesson_table, modified=self.time_changed
        )
        self.lesson_table.setItemDelegateForColumn(2, delegate)
        delegate = PartnersDelegate(
            self.lesson_table, modified=self.partners_changed
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
        bt_new.clicked.connect(self.lesson_add)
        bt_del.clicked.connect(self.lesson_del)
        self.bt_del = bt_del
        form.addRow(bb0)

        f = "PAYROLL"
        editwidget = PayrollSelector(modified=self.payroll_changed)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)

    def set_data(self, record):
        self.lesson_id = record.value("id")
        self.course_id = record.value("course")
        self.editors["PAYROLL"].setText(record.value("PAYROLL"))
        self.editors["ROOM"].setText(record.value("ROOM"))
        editor = self.editors["Block_subject"]
        editor.set_block(record.value("TIME"))
        self.show_sublessons(editor.get_block())

    def show_sublessons(self, block_tag):
        slist = sublessons(block_tag)
        # print(" ...", slist)
        ltable = self.lesson_table
        self.__ltable_ready = False
        ltable.clearContents()
        ltable.setRowCount(len(slist))
        r = 0
        for s in slist:
            t, p = parse_time_field(s.TIME)
            ltable.setItem(r, 0, QTableWidgetItem(str(s.id)))
            ltable.setItem(r, 1, QTableWidgetItem(s.LENGTH))
            ltable.setItem(r, 2, QTableWidgetItem(t))
            ltable.setItem(r, 3, QTableWidgetItem(p))
            r += 1
        self.bt_del.setEnabled(bool(slist))
        self.__ltable_ready = True

    def block_changed(self, block_tag):
        tag = block_tag.lstrip("+")
        # print("§ block changed:", tag)
        if not check_new_time(self.course_id, tag):
            return False
        db_update_field("LESSONS", "TIME", tag, id=self.lesson_id)
        self.main_widget.redisplay()
        ### After a redisplay of the main widget it would be superfluous
        ### for a callback handler to update its cell, so <False> is
        ### returned to suppress this update.
        return False

    def room_changed(self, text):
        # print("$ UPDATE ROOM:", text)
        db_update_field("LESSONS", "ROOM", text, id=self.lesson_id)
        self.main_widget.redisplay()
        return False

    def payroll_changed(self, text):
        # print("$ UPDATE PAYROLL:", text)
        db_update_field("LESSONS", "PAYROLL", text, id=self.lesson_id)
        self.main_widget.redisplay()
        return False

    def length_changed(self, row, new_value):
        sublesson_id = int(self.lesson_table.item(row, 0).text())
        return db_update_field("LESSONS", "LENGTH", new_value, id=sublesson_id)

    def time_changed(self, row, new_value):
        sublesson_id = int(self.lesson_table.item(row, 0).text())
        ptag = self.lesson_table.item(row, 3).text()
        return db_update_time(sublesson_id, new_value, ptag, self.course_id)

    def partners_changed(self, row, new_value):
        # Forbid duplication of other sublesson tags
        if not check_new_time(self.course_id, f"={new_value}"):
            return False
        sublesson_id = int(self.lesson_table.item(row, 0).text())
        old_partners = self.lesson_table.item(row, 3).text()
        old_time = self.lesson_table.item(row, 2).text()
        new_time = db_update_partners(
            sublesson_id, new_value, old_partners, old_time, self.course_id
        )
        if old_time != new_time:
            self.lesson_table.item(row, 2).setText(new_time)
        # If there are no other partners with the original tag, remove
        # its lesson-time entry.
        if new_time and not partners(old_partners):
            # print("§ EMPTY TAG:", oldpartners)
            db_delete_rows("LESSONS", PLACE=f"={old_partners}")
        return bool(new_time)

    def lesson_add(self):
        row = self.lesson_table.currentRow()
        if row >= 0:
            length = self.lesson_table.item(row, 1).text()
        else:
            length = "1"
        editor = self.editors["Block_subject"]
        block_tag = editor.get_block()
        db_new_row("LESSONS", LENGTH=length, TIME="@?", PLACE=block_tag)
        self.show_sublessons(block_tag)

    def lesson_del(self):
        row = self.lesson_table.currentRow()
        if row >= 0:
            sublesson_id = int(self.lesson_table.item(row, 0).text())
            db_delete_rows("LESSONS", id=sublesson_id)
            editor = self.editors["Block_subject"]
            block_tag = editor.get_block()
            self.show_sublessons(block_tag)
        else:
            SHOW_WARNING(T["DELETE_SELECTED"])


class NonLesson(QWidget):
    """Handle payroll-only items. These are not relevant for the timetable."""

    def __init__(self, main_widget, parent=None):
        self.main_widget = main_widget
        super().__init__(parent=parent)
        form = QFormLayout(self)
        form.setContentsMargins(0, 0, 0, 0)
        form.addRow(HLine())
        label = QLabel(T["PAYROLL_ENTRY"])
        label.setWordWrap(True)
        form.addRow(label)
        form.addRow(HLine())
        self.editor = PayrollSelector(
            modified=self.payroll_changed, no_length=True
        )
        form.addRow(T["PAYROLL"], self.editor)

    def set_data(self, record):
        self.lesson_id = record.value("id")
        # self.course_id = record.value("course")
        self.editor.setText(record.value("PAYROLL"))

    ### After a redisplay of the main widget it would be inappropriate
    ### for a callback handler to update its cell, so <False> is returned
    ### to suppress this update.

    def payroll_changed(self, text):
        # print("$ UPDATE PAYROLL:", text)
        db_update_field("LESSONS", "PAYROLL", text, id=self.lesson_id)
        self.main_widget.redisplay()
        return False


class CourseEditorForm(QDialog):
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
            else:
                editwidget = FormLineEdit(f, self.form_modified)
                editwidget.__real = True
            self.editors[f] = editwidget
            if editwidget.__real:
                form.addRow(t, editwidget)

        hbox1 = QHBoxLayout()
        vbox0.addLayout(hbox1)
        hbox1.addStretch(1)
        self.course_update_button = QPushButton(T["UPDATE"])
        self.course_update_button.clicked.connect(self.course_update)
        hbox1.addWidget(self.course_update_button)
        self.course_add_button = QPushButton(T["NEW"])
        self.course_add_button.clicked.connect(self.course_add)
        hbox1.addWidget(self.course_add_button)

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
        field and its value must be passed as a tuple: (field value).
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
            if field in COURSE_KEY_FIELDS:
                self.course_add_button.setEnabled(True)
        else:
            self.form_change_set.discard(field)
            if self.form_change_set:
                if not self.form_change_set.intersection(COURSE_KEY_FIELDS):
                    self.course_add_button.setEnabled(False)
            else:
                self.course_update_button.setEnabled(False)
                self.course_add_button.setEnabled(False)
        # print("FORM CHANGED SET:", self.form_change_set)


def check_new_time(course_id, tag):
    """Check that a new time-field doesn't clash with an existing one
    used by the current course. Only a basic comparison is done (a top
    level comparison).
    Return true if no conflict.
    """

    class TagMatchError(Exception):
        pass

    if tag != "@?":
        # get all lesson record with this course
        course_times = db_values("LESSONS", "TIME", course=course_id)
        # print("? course_times:", tag, course_times)
        try:
            for ctime in course_times:
                if ctime == "@?":
                    continue
                if ctime.startswith(">"):
                    # check sublessons
                    for sl in sublessons(ctime):
                        if sl.TIME == tag:
                            raise TagMatchError
                else:
                    if ctime == tag:
                        raise TagMatchError
        except TagMatchError:
            SHOW_ERROR(f'{T["BLOCK_TAG_TIME_CLASH"]}: {tag}')
            return False
    return True


def db_update_time(lesson_id, time, partners, course_id):
    # print("§ db_update_time:", lesson_id, time, partners, course_id)
    ttag = f"@{time}"
    if not check_new_time(course_id, ttag):
        return False
    if partners:
        ptag = f"={partners}"
        return db_update_field("LESSONS", "TIME", ttag, PLACE=ptag)
    else:
        return db_update_field("LESSONS", "TIME", ttag, id=lesson_id)
    return False


def db_update_partners(lesson_id, newpartners, oldpartners, oldtime, course_id):
    """Update the "Partners" field.
    Apart from the new field value it is also necessary to have the
    previous value of this field and the current value of the "Time"
    field. The latter is only necessary for transfer to newly created
    partners, which are indicated by a "+"-prefix.
    Return the new  "Time" field (which may be the same as the old one)
    if successful, else <None>.
    """
    new_time = oldtime
    if newpartners == "-":
        # Remove the partner tag
        if not db_update_field("LESSONS", "TIME", f"@{oldtime}", id=lesson_id):
            return None
    else:
        if newpartners[0] == "+":
            # New partner tag, make lesson-time entry
            newpartners = newpartners[1:]
            ptag = f"={newpartners}"
            if not db_new_row("LESSONS", PLACE=ptag, TIME=f"@{oldtime}"):
                return None
        else:
            ptag = f"={newpartners}"
            if not check_new_time(course_id, ptag):
                return None
        if db_update_field("LESSONS", "TIME", ptag, id=lesson_id):
            new_time = get_time_entry(newpartners)
        else:
            return None
    # If there are no other partners with the original tag, remove
    # its lesson-time entry.
    # print("§ ??? PARTNERS:", partners(oldpartners))
    if not partners(oldpartners):
        # print("§ EMPTY TAG:", oldpartners)
        db_delete_rows("LESSONS", PLACE=f"={oldpartners}")
    return new_time


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from ui.ui_base import run

    widget = Courses()
    widget.enter()
    widget.resize(1000, 550)
    run(widget)
