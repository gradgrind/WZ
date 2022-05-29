"""
ui/modules/course_lessons.py

Last updated:  2022-05-29

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

#TODO: Rework using Dialogs for the form editors, with the lesson forms
# in the main page

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
    db_read_unique_field,
    NoRecord,
    db_update_field,
    db_new_row,
    db_delete_rows,
    db_values
)

from ui.ui_base import (
    GuiError,
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
    QTableWidget,
    QTableWidgetItem,
    QTableView,
#?
    QDialog,
    QWidget,
#    QGroupBox,
    QLayout,
    QComboBox,
    QCheckBox,
    QValidator,
    QStackedLayout,
    QGridLayout,
    QSizePolicy,
    QSize,

    QScrollArea,

#    QTableView,
    QAbstractItemView,
    ### QtGui:
    QRegularExpressionValidator,
    ### QtCore:
    Qt,
    ### QtSql:
    QSqlTableModel,
)

from ui.dialogs import (
    dialogs_init,
    SHARED_DATA,
    DurationSelector,
    DayPeriodSelector,
    PartnersSelector,
    PayrollSelector,
    RoomSelector,
    partners,
    sublessons,
    TAG_FORMAT,
    DurationDelegate,
    DayPeriodDelegate,

    #RoomDialog,
    DayPeriodDialog,
    PartnersDialog,
    PayrollDialog,
    parse_time_field,
    get_time_entry,
    TimeSlotError,
    TableWidget
)

# Course table fields
COURSE_COLS = [(f, T[f]) for f in (
        "course",
        "CLASS",
        "GRP",
        "SUBJECT",
        "TEACHER",
        "REPORT",
        "GRADE",
        "COMPOSITE"
    )
]
# SUBJECT, CLASS and TEACHER are foreign keys with:
#  on delete cascade + on update cascade
FOREIGN_FIELDS = ("CLASS", "TEACHER", "SUBJECT")

FILTER_FIELDS = [cc for cc in COURSE_COLS if cc[0] in FOREIGN_FIELDS]

# Group of fields which determines a course (the tuple must be unique)
COURSE_KEY_FIELDS = ("CLASS", "GRP", "SUBJECT", "TEACHER")

LESSON_COLS = [(f, T[f]) for f in (
        "id",
        "course",
        "LENGTH",
        "PAYROLL",
#        "TAG",
        "ROOM",
        "TIME",
        "PLACE",
        "NOTES"
    )
]
#LESSONCOLS_SHOW = ("LENGTH", "PAYROLL", "TAG")
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
        dialogs_init()
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
        #self.lessontable.verticalHeader().hide()
        self.lessontable.set_callback(self.lesson_selected)
#        self.lessontable.activated.connect(self.lesson_activate)
        vbox2.addWidget(self.lessontable)

        self.field_lines = {}
        self.stack = QStackedLayout()
        vbox2.addLayout(self.stack)

        ### Page: No existing entries
#TODO
        empty_page = QLabel("EMPTY")
        self.stack.addWidget(empty_page)

        ### Page: Plain lesson entry
        self.stack.addWidget(PlainLesson(self))

        ### Page: Block member entry
        self.stack.addWidget(BlockLesson(self))
#TODO

        ### Page: "Extra" entry (no timetable, but payroll entry)
        extra_page = QWidget()
        self.stack.addWidget(extra_page)
        extra_form = QFormLayout(extra_page)
        f = "PAYROLL"
        editwidget = FormPayrollEdit(f, self.field_modified, no_length=True)
        self.field_lines[f + "__extra"] = editwidget
        extra_form.addRow(T[f], editwidget)

        vbox2.addWidget(QLabel(T["NOTES"] + ":"))
        self.note_editor = QLineEdit()
        self.note_editor.editingFinished.connect(self.notes_changed)
        vbox2.addWidget(self.note_editor)

        vbox2.addSpacing(20)
        vbox2.addStretch(1)
        vbox2.addWidget(HLine())
        self.lesson_delete_button = QPushButton(T['DELETE'])
        vbox2.addWidget(self.lesson_delete_button)
        self.lesson_delete_button.clicked.connect(self.lesson_delete)

        lesson_add_plain = QPushButton(T['NEW_PLAIN'])
        vbox2.addWidget(lesson_add_plain)
        lesson_add_plain.clicked.connect(self.lesson_add_plain)
        lesson_add_block = QPushButton(T['NEW_BLOCK'])
        vbox2.addWidget(lesson_add_block)
        lesson_add_block.clicked.connect(self.lesson_add_block)
        lesson_add_extra = QPushButton(T['NEW_EXTRA'])
        vbox2.addWidget(lesson_add_extra)
        lesson_add_extra.clicked.connect(self.lesson_add_extra)

        self.setStretchFactor(0, 1)  # stretch only left panel

    def course_activate(self, modelindex):
        self.edit_course()

    def edit_course(self):
        row = self.course_dialog.activate(
            self.current_row,
            (self.filter_field, self.filter_value)
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
                kv = db_key_value_list("CLASSES", "CLASS", "NAME", "CLASS")
                self.filter_list[f] = kv
                #delegate = ForeignKeyItemDelegate(kv, parent=self.coursemodel)
                #self.coursetable.setItemDelegateForColumn(i, delegate)
            if f == "SUBJECT":
                kv = db_key_value_list("SUBJECTS", "SID", "NAME", "NAME")
                SHARED_DATA["SUBJECTS"] = kv
                self.filter_list[f] = kv
                delegate = ForeignKeyItemDelegate(kv, parent=self.coursemodel)
                self.coursetable.setItemDelegateForColumn(i, delegate)
            elif f == "TEACHER":
                kv = db_key_value_list("TEACHERS", "TID", "NAME", "SORTNAME")
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
            #print("EXEC COURSE CHANGED:", row)
            record = self.coursemodel.record(row)
            self.set_course(record.value(0))
            self.course_delete_button.setEnabled(True)
            SHARED_DATA["COURSE"] = {
                f: record.value(f) for f in COURSE_KEY_FIELDS
            }
        else:
            # e.g. when entering an empty table
            #print("EMPTY TABLE")
            self.set_course(0)
            self.course_delete_button.setEnabled(False)
            SHARED_DATA["COURSE"] = {}

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
        print("SET COURSE:", course)
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
        self.lessontable.selectRow(self.current_row)

    def lesson_selected(self, row):
        self.current_row = row
        print("SELECT LESSON", row)
        self.note_editor.clear()
        if row >= 0:
            self.lesson_delete_button.setEnabled(True)
        else:
            self.stack.setCurrentIndex(0)
            self.lesson_delete_button.setEnabled(False)
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
            self.show_extra()

#        for f, t in LESSON_COLS:
#            if f not in LESSONCOLS_SHOW:
#                self.field_lines[f].setText(str(record.value(f)))

    def notes_changed(self):
        text = self.note_editor.text()
        #print("§§§ NOTES CHANGED:", text)
        db_update_field("LESSONS", "NOTES", text, id=self.lesson_id)


#TODO: -> class handler
    def show_extra(self):
        """Set up the "extra" item (payroll entry, no lesson) editor pane.
        The info is in <self.lesson_record> (a "QSqlRecord").
        """
#TODO
#        self.field_lines["PAYROLL__extra"].setText(
#            self.lesson_record.value("PAYROLL")
#            )




    def lesson_activate(self, index):
        if not index:
            index = self.lessontable.currentIndex()
#TODO
        print("ACTIVATE LESSON", index.row())
        #LessonEditorForm().exec()
#        self.lesson_dialog.activate(
#            self.this_course,
#            index.row()
#        )
# Need to call lesson_selected(row) afterwards?

#        return
#TODO
        row = index.row()
        if row < 0:
#???
            print("EMPTY LESSON TABLE:")#, repr(course))
# also need new block-lesson ...

        else:
            record = self.lessonmodel.record(row)
            tag = record.value("TIME")
            if tag.startswith(">"):
                self.block_lesson_dialog.activate(
                    self.this_course,
                    row
                )
            else:
                self.simple_lesson_dialog.activate(
                    self.this_course,
                    row
                )

    def field_modified(self, field, value):
        print(f"**MODIFIED** {field}: {value}")



    def lesson_add_plain(self):
#TODO: Did I rather want to do it like the courses? I.e. by popping up
# a dialog which has the option to modify the current one – if there
# is a current one – or create a new one.
        """Add a new "lesson", copying the current one if possible."""
        print("ADD PLAIN LESSON")
        return

        if self.this_course:    # If this is null (0), no lessons can be added
            model = self.lessonmodel
            index = self.lessontable.currentIndex()
            if index.isValid():
                row = index.row()
                #model.select()  # necessary to ensure current row is up to date
                record = model.record(row)
                # print("RECORD:", [record.value(i) for i in range(record.count())])
                length = record.value("LENGTH")
                try:
                    i = int(length)
                except ValueError:
                    record.setValue("LENGTH", "1")
                    record.setValue("PAYROLL", "*")
                    record.setValue("ROOM", "?")
                record.setValue(model.fieldIndex("id"), None)
#?
                record.setValue(model.fieldIndex("TAG"), None)
                n = model.rowCount()
            else:
                # Create a basic "normal" lesson
                record = model.record()
                record.setValue("course", self.this_course)
                record.setValue("LENGTH", "1")
                record.setValue("PAYROLL", "*")
                record.setValue("ROOM", "?")
                n = 0
            record.setValue("TIME", "?")
            record.setValue("PLACE", "?")
            if model.insertRecord(-1, record) and model.submitAll():
                #lid = model.query().lastInsertId()
                #print("INSERTED:", lid, model.rowCount())
                self.lessontable.selectRow(n)
            else:
                SHOW_ERROR(f"DB Error: {model.lastError().text()}")
                model.revertAll()

    def lesson_add_block(self):
        print("ADD BLOCK MEMBER", self.this_course)
# Don't allow repeated use of a tag already used for this course!

#TODO: pop up tag editor
#        widget = BlockLessonEditor()
#        widget.exec()

#?
        tag = BlockTagDialog()

        block_tags = []
        for i in range(self.lessonmodel.rowCount()):
            record = self.lessonmodel.record(i)
            t = record.value("TIME")
            if t.startswith(">"):
                block_tags.append(t)
            # ...

            # or ~
            if tag == record.value("TIME"):
                SHOW_ERROR(f"BLOCK tag already in use by this course: {tag}")


    def lesson_add_extra(self):
        print("ADD 'EXTRA' ENTRY", self.this_course)



    def lesson_delete(self):
        """Delete the current "lesson"."""
        model = self.lessonmodel
        index = self.lessontable.currentIndex()
        row = index.row()
        if model.removeRow(row) and model.submitAll():
            #model.select()
            n = model.rowCount()
            if row >= n:
                row = n - 1
                if row < 0:
                    self.lesson_selected(-1)
                    return
            self.lessontable.selectRow(row)
        else:
            SHOW_ERROR(f"DB Error: {model.lastError().text()}")
            model.revertAll()



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
        #self.course_id = record.value("course")
        ltime, tag = parse_time_field(record.value("TIME"))
        self.editors["Partners"].setText(tag)
        self.editors["Time"].setText(ltime)
        self.editors["LENGTH"].setText(record.value("LENGTH"))
        self.editors["PAYROLL"].setText(record.value("PAYROLL"))
        self.editors["ROOM"].setText(record.value("ROOM"))
        self.editors["PLACE"].setText(record.value("PLACE"))

    def length_changed(self, text):
        #print("$ UPDATE LENGTH:", text)
        db_update_field("LESSONS", "LENGTH", text, id=self.lesson_id)
        self.main_widget.redisplay()
        return False

    def room_changed(self, text):
        #print("$ UPDATE ROOM:", text)
        db_update_field("LESSONS", "ROOM", text, id=self.lesson_id)
        self.main_widget.redisplay()
        return False

    def time_changed(self, text):
        #print("$ UPDATE TIME:", text)
        # The action to take depends on whether there is a partner tag.
        ptag = self.editors["Partners"].text()
        if ptag:
            db_update_field("LESSONS", "TIME", "@"+text, PLACE=f"={ptag}")
        else:
            db_update_field("LESSONS", "TIME", "@"+text, id=self.lesson_id)
        self.main_widget.redisplay()
        return False

    def partners_changed(self, text):
        #print("$ UPDATE PARTNERS TAG:", text)
        oldtime = self.editors["Time"].text()
        oldpartners = self.editors["Partners"].text()

        if text:
            if text[0] == "+":
                # New partner tag, make lesson-time entry
                text = text[1:]
                newid = db_new_row("LESSONS",
                    PLACE=f"={text}",
                    TIME=f"@{oldtime}"
                )
                if not newid:
                    return False

            else:
                # Get time of new partners
                ltime = get_time_entry(text)
                self.editors["Time"].setText(ltime)

            if not db_update_field("LESSONS",
                "TIME",
                f"={text}",
                id=self.lesson_id
            ):
                return False

        else:
            # Remove the partner tag
            if not db_update_field("LESSONS",
                "TIME",
                f"@{oldtime}",
                id=self.lesson_id
            ):
                return False

        # If there are no other partners with the original tag, remove
        # its lesson-time entry.
        #print("§ ??? PARTNERS:", partners(oldpartners))
        if not partners(oldpartners):
            #print("§ EMPTY TAG:", oldpartners)
            db_delete_rows("LESSONS", PLACE=f"={oldpartners}")
        self.main_widget.redisplay()
        return False

    def payroll_changed(self, text):
        #print("$ UPDATE PAYROLL:", text)
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
        editwidget = KeySelector(changed_callback=self.sid_changed)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)
#?
        f = "Block_tag"
        editwidget = QComboBox(editable=True)
        editwidget.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        editwidget.currentTextChanged.connect(self.show_sublessons)
        self.editors[f] = editwidget

#?        editwidget.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        validator = QRegularExpressionValidator(TAG_FORMAT)
        editwidget.setValidator(validator)
        form.addRow(T[f], editwidget)

        self.lesson_table = TableWidget()
        self.lesson_table.setMinimumHeight(120)
        self.lesson_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.lesson_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.lesson_table.cellChanged.connect(self.sublesson_table_changed)

        self.lesson_table.setColumnCount(4)
        self.lesson_table.setHorizontalHeaderLabels((
            T["id"],
            T["LENGTH"],
            T["Time"],
            T["Partners"]
        ))
        self.lesson_table.hideColumn(0)
        Hhd = self.lesson_table.horizontalHeader()
        Hhd.setMinimumSectionSize(60)
        self.lesson_table.resizeColumnsToContents()
        Hhd.setStretchLastSection(True)

        # Set column editors
        delegate = DurationDelegate(self.lesson_table)
        self.lesson_table.setItemDelegateForColumn(1, delegate)
#TODO: Time and Partners
        delegate = DayPeriodDelegate(self.lesson_table)
        self.lesson_table.setItemDelegateForColumn(2, delegate)

        form.addRow(self.lesson_table)

        bb0 = QDialogButtonBox()
        bt_new = bb0.addButton("+", QDialogButtonBox.ButtonRole.ActionRole)
        bt_new.setFixedWidth(30)
        bt_del = bb0.addButton("–", QDialogButtonBox.ButtonRole.ActionRole)
        bt_del.setFixedWidth(30)
        bt_new.clicked.connect(self.lesson_add)
        bt_del.clicked.connect(self.lesson_del)
        form.addRow(bb0)

        f = "PAYROLL"
        editwidget = PayrollSelector(modified=self.payroll_changed)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)

    def lesson_activated(self, row, col):
#TODO
        print("§ ACTIVATED", row, col)
        self.lesson_table.editItem(self.lesson_table.item(row, col))

    def set_data(self, record):
        self.lesson_id = record.value("id")
        #self.course_id = record.value("course")
        fulltag = record.value("TIME")
        try:
            sid, tag = fulltag[1:].split("#")
        except ValueError:
            SHOW_ERROR(f"{T['INVALID_BLOCK_TAG']}: {fulltag}")
            sid, tag = "", ""
        self.editors["PAYROLL"].setText(record.value("PAYROLL"))
        self.editors["ROOM"].setText(record.value("ROOM"))
        subject_choice = self.editors["Block_subject"]
        subject_choice.set_items(SHARED_DATA["SUBJECTS"])
        try:
            subject_choice.reset(sid)
        except GuiError:
            if sid:
                SHOW_ERROR(f"{T['UNKNOWN_SUBJECT_TAG']}: {sid}")
        tagid = self.editors["Block_tag"]
        tagid.setCurrentText("#")
        tagid.setCurrentText(tag)

    def show_sublessons(self, text):
        if text == "#":
            return
        tag = f'>{self.editors["Block_subject"].selected()}#{text}'
        #print("§§ FULL TAG:", tag)
        slist = sublessons(tag)
        print(" ...", slist)
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
        self.__ltable_ready = True

    def sid_changed(self, sid):
        taglist = db_values(
            "LESSONS",
            "TIME",
            f"TIME LIKE '>{sid}#%'",
            distinct=True,
            sort_field="TIME"
        )
        print("sid_changed:", sid, taglist)
        tagid = self.editors["Block_tag"]
        tagid.clear()
        tagid.addItems([t.split("#", 1)[1] for t in taglist])
        tagid.setCurrentText("#")
        tagid.setCurrentIndex(-1)
        return True # accept

    def room_changed(self, text):
        #print("$ UPDATE ROOM:", text)
        db_update_field("LESSONS", "ROOM", text, id=self.lesson_id)
        self.main_widget.redisplay()
        return False

    def payroll_changed(self, text):
        #print("$ UPDATE PAYROLL:", text)
        db_update_field("LESSONS", "PAYROLL", text, id=self.lesson_id)
        self.main_widget.redisplay()
        return False

    def sublesson_table_changed(self, row, col):
#TODO
        if self.__ltable_ready:
            val = self.lesson_table.item(row, col).text()
            print("§ SUBLESSON table changed:", row, col, val)
            lesson_id = int(self.lesson_table.item(row, 0).text())
            if col == 1:
                # length
                db_update_field("LESSONS", "LENGTH", val, id=lesson_id)
            elif col == 2:
                # time
                print("!!! TODO")
            elif col == 3:
                # partners
                print("!!! TODO")
            else:
                raise Bug(f"Invalid sublesson table column: {col}")

    def lesson_add(self):
#TODO
        pass

    def lesson_del(self):
#TODO
        pass


# see version in dialogs.py
class EditableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent=parent, editable=True)

    def focusOutEvent(self, e):
        """Close the editor when focus leaves it. This reverts any
        partially entered text.
        """
        self.clearEditText()
        self.setCurrentIndex(self.currentIndex())


#Testing!
class LessonScrollArea(QScrollArea):
    def sizeHint(self):
        sh = super().sizeHint()
        if sh.isValid():
            return QSize(sh.width(), 120)
        return sh


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
        """Prevent dialog closure if there are changes.
        """
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
            #print("EMPTY TABLE")
            self.table_empty = True
            for f, t in COURSE_COLS:
                self.editors[f].setText("")
            if filter_field:
                self.editors[filter_field[0]].setText(filter_field[1])
        self.form_modified("", False)  # initialize form button states

        self.__value = -1   # Default return value => don't change row
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
                    self.return_value(r)            # Select this row
                    break
            else:
                SHOW_INFO(T["COURSE_ADDED"].format(klass=klass))
                self.return_value(self.current_row) # Reselect current row
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
                    self.return_value(r)    # Select this row
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


#TODO
class LessonEditorForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        vbox1 = QVBoxLayout(self)
        #vbox1.setContentsMargins(0, 0, 0, 0)
        self.coursedata = {}
        box0 = QFrame()
        box0.setLineWidth(1)
        box0.setMidLineWidth(1)
        box0.setFrameShape(QFrame.Shape.Box)
        box0.setFrameShadow(QFrame.Shadow.Sunken)

        # The course data
        vbox1.addWidget(box0)
        form0 = QFormLayout(box0)
        for f in COURSE_KEY_FIELDS:
            widget = QLineEdit()
            widget.setReadOnly(True)
            self.coursedata[f] = widget
            form0.addRow(T[f], widget)
        vbox1.addWidget(HLine())

        # Block member or simple lesson?
#        hbox1 = QHBoxLayout()
#        vbox1.addLayout(hbox1)
        self.blockmember = QCheckBox(T["BLOCK_MEMBER"])
#        self.blockmember = QGroupBox(T["BLOCK_MEMBER"])
#        self.blockmember.setCheckable(True)
        vbox1.addWidget(self.blockmember)

        self.blockmember.stateChanged.connect(self.toggle_block)
#        self.blockmember.toggled.connect(self.toggle_block)
#        hbox1.addWidget(self.blockmember)
#        hbox1.addStretch(1)
#???
#        hbox1.addWidget(QLabel(f'{T["TAG"]}:'))

        self.bframe = QFrame()
        vbox1.addWidget(self.bframe)
        bform = QFormLayout(self.bframe)

# It might be preferable to use a non-editable combobox with a separate
# button+popup (or whatever) to add a new identifier.
#        self.identifier = EditableComboBox()
        #self.identifier.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        #self.identifier.setInsertPolicy(QComboBox.InsertPolicy.InsertAtTop)
        # Alphabetical insertion doesn't apply to the items added programmatically
#        self.identifier.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
#        self.identifier.addItems(("10Gzwe", "Short", "Long_identifier"))
#        self.identifier.setItemData(0, "First item", Qt.ToolTipRole)
#        self.identifier.setItemData(1, "A rather longer tooltip,\n very rambly actually ...", Qt.ToolTipRole)
#        bn_validator = BlocknameValidator()
#        self.identifier.setValidator(bn_validator)
##        self.identifier.textActivated.connect(self.text_activated)
#        hbox1.addWidget(self.identifier)

#        self.stack = QStackedLayout(vbox1)

        # Fields for "simple lesson"
#        box1 = QFrame()
#        self.stack.addWidget(box1)

        self.block_s = KeySelector(changed_callback=self.block_subject_changed)
        bform.addRow("BLOCK SBJ", self.block_s)


        self.block_t = EditableComboBox()
        self.block_t.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
#--
        self.block_t.addItems(("", "block3", "block2"))

        self.block_t.currentIndexChanged.connect(self.block_changed)

        bform.addRow("BLOCK", self.block_t)

        form = QFormLayout()
        vbox1.addLayout(form)
        #vbox0.addLayout(form)
        self.editors = {}
        for f in "LENGTH", "PAYROLL", "ROOM", "TIME", "PLACE", "NOTES":
            if f == "ROOM":
                editwidget = FormRoomEdit(f, self.form_modified)
            else:
                editwidget = FormLineEdit(f, self.form_modified)
            self.editors[f] = editwidget
            form.addRow(T[f], editwidget)
#TODO: Now, what about TIME and PLACE???
# TIME is rather difficult, because it can be:
#   - ?: not yet placed
#   - @Mi:3  (an actual time ... + fixed flag? – "fixed", "held" or "movable"?))
#   - >block-tag (sid + identifier)
#   - =parallel-tag (identifier)
# (Block tags and parallel tags should probably be kept quite separate by
# making the prefix significant, i.e. ">Ma-id1" and "+Ma-id1" would be
# completely distince tags, though a "=" tag wouldn't normally have a
# subject part anyway.)
# There may also be entries with 0 length. These are then items that
# are present in the table for their payroll-relevance, although they
# don't appear in the timetable. For these TIME and PLACE play no role
# and should be null. Whether the 0 length or the empty time field is
# the primary flag for payroll-only, would need to be decided.

# There would also be special lesson table entries with null "course"
# field to specify the actual times of block members and parallel lessons.
# For these the tag would be in the PLACE field. Parallel lessons have
# just one such entry per tag, other fields – except TIME – being null.
# Block members can have several such entries (a block can consist of
# more than one lesson a week). These would also need to use the LENGTH
# field, to specify the duration of each component lesson.

# Note that these special entries also need to be visible, as part of
# the editor for the entries that reference them ...


#        # Fields for "block member"
#        box2 = QFrame()
#        self.stack.addWidget(box2)
##        form = QFormLayout(box2)

## Just testing ...
#        vbox2 = QVBoxLayout(box2)
#        vbox2.addWidget(QLabel("Header !"))
#        area = LessonScrollArea()
#        vbox2.addWidget(area)
#        scrolledarea = QWidget()
#        grid = QGridLayout()
#        scrolledarea.setLayout(grid)
#        area.setWidgetResizable(True)
#        area.setWidget(scrolledarea)
##--
#        self.__area = area

#        for i in range(8):
#            grid.addWidget(QLabel(f"Label {i}"), i, 0)
#            grid.addWidget(QLineEdit(), i, 1)
#            grid.addWidget(EditableComboBox(), i, 2)


#        vbox1.addStretch(1)
        vbox1.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        # The button-box
        hbox2 = QHBoxLayout()
        vbox1.addLayout(hbox2)
        hbox2.addSpacing(100)
        hbox2.addStretch(1)
        self.course_update_button = QPushButton(T["UPDATE"])
        self.course_update_button.clicked.connect(self.course_update)
        hbox2.addWidget(self.course_update_button)
        self.course_add_button = QPushButton(T["NEW"])
        self.course_add_button.clicked.connect(self.course_add)
        hbox2.addWidget(self.course_add_button)

    def init(self, model):#, keymaps):
        self.model = model
#TODO: table_empty probably not needed
#        self.table_empty = None
#        for f, kv in keymaps.items():
#            editwidget = self.editors[f]
#            editwidget.setup(kv)

#        self.block_s.set_items(
#            [kv for kv in SHARED_DATA["SUBJECTS"] if kv[0] != "--"]
#        )

#??? ...
    def block_subject_changed(self, text):
        print("-> BLOCK", text)
        return True

    def block_changed(self, i):
        # This can be called twice on a change because of sorting
        t = self.block_t.currentText()
        if t != self.block_tag:
            print("SWITCH BLOCK:", i, t)
            self.block_tag = t

    def toggle_block(self, state):
# How to avoid initial values being overwritten?

# Setting block needs to get list of block tags for time widget
# Setting "normal" needs to ...?

        print("BLOCK toggled", state)
        if state:
            self.bframe.show()
            e = self.editors["LENGTH"]
            e.setText("*")
            e.setReadOnly(True)
            e = self.editors["PLACE"]
            e.setText("")
            e.setReadOnly(True)
        else:
            self.bframe.hide()
            e = self.editors["LENGTH"]
            e.setText("LENGTH???")
            e.setReadOnly(False)
            e = self.editors["PLACE"]
            e.setText("PLACE???")
            e.setReadOnly(False)

        self.resize(0,0)
        return
#TODO
#        self.identifier.clear() # or clearEditText()

# Actually, it might be better to have two, completely distinct comboboxes,
# one for blocks and one for parallels, rather than reloading them each time.
# On the other hand, of course, the lists are dynamic, so they would need
# reloading anyway ...
# The parallels tags are from the TAG field. This must be empty for
# block components? Where do the block-tags go, then? I could use PLACE,
# but would that be any better than TAG? If it's all in TAG, I can use the
# same list, but differently filtered.
# I need a way to add and remove tags – maybe adding be entering new
# values and removing, when the last usage is removed. The removal could
# happen automatically – but entries for blocks in class "--" would
# also need to be removed. Perhaps for blocks, new entries should only
# be possible in class "--" (or via a special dialog)?
        if state:
            self.stack.setCurrentIndex(1)
        else:
            self.stack.setCurrentIndex(0)



### FROM CourseEditorForm ...

    def closeEvent(self, event):
        """Prevent dialog closure if there are changes.
        """
        if self.modified() and not LoseChangesDialog():
            event.ignore()
        else:
            event.accept()

    def modified(self):
#--
        return False
        #return self.form_change_set
        return bool(self.form_change_set)

    def clear_modified(self):
        self.form_change_set = set()

    def activate(self, course, row):
        """Initialize the dialog with values from the current "lesson"
        and then activate it.

        <course> is the course identifier ("course" field).
        <row> is the selected row (0 ...) in the lesson list.
        If row < 0 then there is no "lesson", so a new record must be
        set up.
        """
        self.clear_modified()
        self.current_row = row
        for f, v in SHARED_DATA["COURSE"].items():
            self.coursedata[f].setText(v)
        is_block_member = False
        self.block_tag = ""
        self.block_subject = "--"
        if row < 0:
            #print("EMPTY LESSON TABLE:", repr(course))
            # Initialize with a basic, "normal" lesson
#            "id" is <None>
#            "course" is parameter <course>
            self.editors["LENGTH"].setText("1")
            self.editors["PAYROLL"].setText("*")
            self.editors["ROOM"].setText("?")    # ?
            self.editors["TIME"].setText("?")
            self.editors["PLACE"].setText("?")
            self.editors["NOTES"].setText("")

        else:
            record = self.model.record(row)
            tag = record.value("TIME")
            if tag.startswith(">"):
                is_block_member = True
                try:
                    bs, btag = tag.split("#", 1)
                except ValueError:
                    SHOW_WARNING(f"Invalid block tag: {tag}")
                    bsid = self.block_s.selected()
                else:
                    try:
                        bsid = bs[1:]
                        self.block_s.reset(bsid)
                    except GuiError:
                        SHOW_WARNING(f"Unknown subject: {bsid}")
                        bsid = self.block_s.selected()

                print("§§§§§", bsid)

#                e = self.editors["LENGTH"]
#                e.setText("*")
#                e.hide()
#                e = self.editors["PLACE"]
#                e.setText("")
#                e.hide()
#            else:
#                e = self.editors["LENGTH"]
#                e.setText(record.value("LENGTH"))
#                e.show()
#                e = self.editors["PLACE"]
#                e.setText(record.value("PLACE"))
#                e.show()
            self.editors["PAYROLL"].setText(record.value("PAYROLL"))
            self.editors["ROOM"].setText(record.value("ROOM"))
            self.editors["TIME"].setText(tag)
# The time editor is probably handled differently if block member ...
            self.editors["NOTES"].setText("")

        if is_block_member:
            self.blockmember.setCheckState(Qt.CheckState.Checked)
#            self.blockmember.setChecked(True)

#LENGTH = "*"
#PAYROLL = payroll-entry
#ROOM = a single room or "" ... specifies a room to reserve for the block
#TIME = ""
#PLACE = ""

#        clear grid!!!
#        This is not easy! It may be better to replace the whole widget.
#        Or use a table with custom delegates/editors. As the items are
#        in the LESSONS table, it might even be sensible to use a
#        QSqlTableModel ...
#
#        for i in range(8):
#            w_length = QComboBox()
#            w_length.addItems([p[0] for p in self.periods])
#            grid.addWidget(w_length, i, 0)
#            grid.addWidget(QLineEdit(), i, 1)
#            grid.addWidget(EditableComboBox(), i, 2)

# There seems to be a memory leak here!
# Probably better to allw adding of rows, but excess rows should just be
# hidden, and reused when needed.
# But a table-view might be still better ...
#            for n in range(1000):
#                scrolledarea = QWidget()
#                grid = QGridLayout()
#                scrolledarea.setLayout(grid)
#                self.__area.setWidget(scrolledarea)
#                for i in range(3):
#                    w_length = QComboBox()
#                    w_length.addItems([str(p[0]) for p in self.periods])
#                    grid.addWidget(w_length, i, 0)
#                    grid.addWidget(QLineEdit(), i, 1)
#                    grid.addWidget(EditableComboBox(), i, 2)
        else:
            self.blockmember.setCheckState(Qt.CheckState.Unchecked)
#            self.blockmember.setChecked(False)
#LENGTH = "n"
#PAYROLL = payroll-entry
#ROOM = "r..." or "$" (or "?"?) ... list?
#TIME = "day:period" or "?" ("" if length = "0")
#PLACE = a single room or "?" ("" if length = "0")

#        for f, e in self.editors.items():
#            e.setText(str(record.value(f)))
        self.form_modified("", False)  # initialize form button states

        self.__value = -1   # Default return value => don't change row
        self.exec()
        return self.__value

# In addition there are special entries in the lesson table. These have
# 0 in the "course" field. Their tag field should match a parallel tag
# or a block tag. Their "TIME" field is used and, in the case of a block
# tag, also the "LENGTH" field, all others should be empty.
# Then it would not be possible to be parallel to a block lesson – which
# might be a good thing. If it should be possible to mark lessons as
# parallel to block lessons, the parallel tag could be in the "TIME"
# field. For the special lesson actually determining the time, the tag
# can be in the "PLACE" field because the "TIME" field is
# needed for the time.


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
                    self.return_value(r)            # Select this row
                    break
            else:
                SHOW_INFO(T["COURSE_ADDED"].format(klass=klass))
                self.return_value(self.current_row) # Reselect current row
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
                    self.return_value(r)    # Select this row
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
            self.form_change_set.add(field)
        else:
            self.form_change_set.discard(field)
            if self.form_change_set:
                if not self.form_change_set.intersection(COURSE_KEY_FIELDS):
                    self.course_add_button.setEnabled(False)
            else:
                self.course_update_button.setEnabled(False)
                self.course_add_button.setEnabled(False)
        # print("FORM CHANGED SET:", self.form_change_set)


class LessonEditorBase(QDialog):
    """Popup editor for a "normal" lesson.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.vbox1 = QVBoxLayout(self)
        #self.vbox1.setContentsMargins(0, 0, 0, 0)
        self.coursedata = {}
        box0 = QFrame()
        box0.setLineWidth(1)
        box0.setMidLineWidth(1)
        box0.setFrameShape(QFrame.Shape.Box)
        box0.setFrameShadow(QFrame.Shadow.Sunken)

        # The course data
        self.vbox1.addWidget(box0)
        form0 = QFormLayout(box0)
        for f in COURSE_KEY_FIELDS:
            widget = QLineEdit()
            widget.setReadOnly(True)
            self.coursedata[f] = widget
            form0.addRow(T[f], widget)
        self.vbox1.addWidget(HLine())

    def _add_dialog_buttons(self):
        buttonBox = QDialogButtonBox()
        self.vbox1.addWidget(buttonBox)
        self.bt_save = buttonBox.addButton(QDialogButtonBox.StandardButton.Save)
        buttonBox.addButton(QDialogButtonBox.StandardButton.Cancel)
        buttonBox.accepted.connect(self.lesson_update)
        buttonBox.rejected.connect(self.cancel)

    def init(self, model):
        self.model = model
#        self.table_empty = None

    def form_modified(self, field, changed):
        """Handle a change in a form editor field.
        Maintain the set of changed fields (<self.form_change_set>).
        Enable and disable the pushbuttons appropriately.
        """
        print("LESSON MODIFIED", field, changed)
        if changed:
            self.bt_save.setEnabled(True)
            self.form_change_set.add(field)
        else:
            self.form_change_set.discard(field)
            if not self.form_change_set:
                self.bt_save.setEnabled(False)
        print("FORM CHANGED SET:", self.form_change_set)

    def cancel(self):
        print("$$CANCEL")
        if (not self.modified()) or LoseChangesDialog():
            self.reject()

    def closeEvent(self, event):
        """Prevent dialog closure if there are changes.
        """
        print("??? CLOSING", self.modified())
#        if self.modified() and not LoseChangesDialog():
#            event.ignore()
#        else:
#            event.accept()
        event.ignore()
        self.cancel()

    def modified(self):
        return bool(self.form_change_set)

    def clear_modified(self):
        self.form_change_set = set()

    def activate(self, course, row):
        """Initialize the dialog with values from the current "lesson"
        and then activate it.

        <course> is the course identifier ("course" field).
        <row> is the selected row (0 ...) in the lesson list.
        If row < 0 then there is no "lesson", so a new record must be
        set up.
        """
        self.clear_modified()
        self.current_row = row
        for f, v in SHARED_DATA["COURSE"].items():
            self.coursedata[f].setText(v)
        self.bt_save.setEnabled(False)
        return


        is_block_member = False
        self.block_tag = ""
        self.block_subject = "--"
        if row < 0:
            #print("EMPTY LESSON TABLE:", repr(course))
            # Initialize with a basic, "normal" lesson
#            "id" is <None>
#            "course" is parameter <course>
            self.editors["LENGTH"].setText("1")
            self.editors["PAYROLL"].setText("*")
            self.editors["ROOM"].setText("?")    # ?
            self.editors["TIME"].setText("?")
            self.editors["PLACE"].setText("?")
            self.editors["NOTES"].setText("")

        else:
            record = self.model.record(row)
            tag = record.value("TIME")
            if tag.startswith(">"):
                is_block_member = True
                try:
                    bs, btag = tag.split("#", 1)
                except ValueError:
                    SHOW_WARNING(f"Invalid block tag: {tag}")
                    bsid = self.block_s.selected()
                else:
                    try:
                        bsid = bs[1:]
                        self.block_s.reset(bsid)
                    except GuiError:
                        SHOW_WARNING(f"Unknown subject: {bsid}")
                        bsid = self.block_s.selected()

                print("§§§§§", bsid)

#                e = self.editors["LENGTH"]
#                e.setText("*")
#                e.hide()
#                e = self.editors["PLACE"]
#                e.setText("")
#                e.hide()
#            else:
#                e = self.editors["LENGTH"]
#                e.setText(record.value("LENGTH"))
#                e.show()
#                e = self.editors["PLACE"]
#                e.setText(record.value("PLACE"))
#                e.show()
            self.editors["PAYROLL"].setText(record.value("PAYROLL"))
            self.editors["ROOM"].setText(record.value("ROOM"))
            self.editors["TIME"].setText(tag)
# The time editor is probably handled differently if block member ...
            self.editors["NOTES"].setText("")

        if is_block_member:
            self.blockmember.setCheckState(Qt.CheckState.Checked)
#            self.blockmember.setChecked(True)

#LENGTH = "*"
#PAYROLL = payroll-entry
#ROOM = a single room or "" ... specifies a room to reserve for the block
#TIME = ""
#PLACE = ""

#        clear grid!!!
#        This is not easy! It may be better to replace the whole widget.
#        Or use a table with custom delegates/editors. As the items are
#        in the LESSONS table, it might even be sensible to use a
#        QSqlTableModel ...
#
#        for i in range(8):
#            w_length = QComboBox()
#            w_length.addItems([p[0] for p in self.periods])
#            grid.addWidget(w_length, i, 0)
#            grid.addWidget(QLineEdit(), i, 1)
#            grid.addWidget(EditableComboBox(), i, 2)

# There seems to be a memory leak here!
# Probably better to allw adding of rows, but excess rows should just be
# hidden, and reused when needed.
# But a table-view might be still better ...
#            for n in range(1000):
#                scrolledarea = QWidget()
#                grid = QGridLayout()
#                scrolledarea.setLayout(grid)
#                self.__area.setWidget(scrolledarea)
#                for i in range(3):
#                    w_length = QComboBox()
#                    w_length.addItems([str(p[0]) for p in self.periods])
#                    grid.addWidget(w_length, i, 0)
#                    grid.addWidget(QLineEdit(), i, 1)
#                    grid.addWidget(EditableComboBox(), i, 2)
        else:
            self.blockmember.setCheckState(Qt.CheckState.Unchecked)
#            self.blockmember.setChecked(False)
#LENGTH = "n"
#PAYROLL = payroll-entry
#ROOM = "r..." or "$" (or "?"?) ... list?
#TIME = "day:period" or "?" ("" if length = "0")
#PLACE = a single room or "?" ("" if length = "0")

#        for f, e in self.editors.items():
#            e.setText(str(record.value(f)))
        self.form_modified("", False)  # initialize form button states

        self.__value = -1   # Default return value => don't change row
        self.exec()
        return self.__value

# In addition there are special entries in the lesson table. These have
# 0 in the "course" field. Their tag field should match a parallel tag
# or a block tag. Their "TIME" field is used and, in the case of a block
# tag, also the "LENGTH" field, all others should be empty.
# Then it would not be possible to be parallel to a block lesson – which
# might be a good thing. If it should be possible to mark lessons as
# parallel to block lessons, the parallel tag could be in the "TIME"
# field. For the special lesson actually determining the time, the tag
# can be in the "PLACE" field because the "TIME" field is
# needed for the time.

#----------


class LessonEditor(LessonEditorBase):
    """Popup editor for a "normal" lesson.
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        form = QFormLayout()
        self.vbox1.addLayout(form)
        self.editors = {}
        f = "LENGTH"
        editwidget = FormComboBox(f, self.form_modified)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)
        f = "PAYROLL"
        editwidget = FormPayrollEdit(f, self.form_modified)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)
        f = "ROOM"
        editwidget = FormRoomEdit(f, self.form_modified)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)
        # TIME: embraces "partners" as well as the actual placement time
        ft = "Time"
        timefield = FormTimeEdit(ft, self.form_modified)
        f = "Partners"
        editwidget = FormPartnersEdit(f, self.form_modified, timefield)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)
        self.editors[ft] = timefield
        form.addRow(T[ft], timefield)
        f = "PLACE"
        editwidget = QLineEdit()
        editwidget.setReadOnly(True)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)
        f = "NOTES"
        editwidget = FormLineEdit(f, self.form_modified)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)

#TODO: Now, what about TIME and PLACE???
# TIME is rather difficult, because it can be:
#   - ?: not yet placed
#   - @Mi.3  (an actual time ... + fixed flag? – "fixed", "held" or "movable"?))
#   - >block-tag (sid + identifier)
#   - =parallel-tag (identifier)
# (Block tags and parallel tags should probably be kept quite separate by
# making the prefix significant, i.e. ">Ma-id1" and "=Ma-id1" would be
# completely distince tags, though a "=" tag wouldn't normally have a
# subject part anyway.)
# There may also be entries with 0 length. These are then items that
# are present in the table for their payroll-relevance, although they
# don't appear in the timetable. For these TIME and PLACE play no role
# and should be null. Whether the 0 length or the empty time field is
# the primary flag for payroll-only, would need to be decided.

# There would also be special lesson table entries with null "course"
# field to specify the actual times of block members and parallel lessons.
# For these the tag would be in the PLACE field. Parallel lessons have
# just one such entry per tag, other fields – except TIME – being null.
# Block members can have several such entries (a block can consist of
# more than one lesson a week). These would also need to use the LENGTH
# field, to specify the duration of each component lesson.

# Note that these special entries also need to be visible, as part of
# the editor for the entries that reference them ...


#        # Fields for "block member"
#        box2 = QFrame()
#        self.stack.addWidget(box2)
##        form = QFormLayout(box2)

## Just testing ...
#        vbox2 = QVBoxLayout(box2)
#        vbox2.addWidget(QLabel("Header !"))
#        area = LessonScrollArea()
#        vbox2.addWidget(area)
#        scrolledarea = QWidget()
#        grid = QGridLayout()
#        scrolledarea.setLayout(grid)
#        area.setWidgetResizable(True)
#        area.setWidget(scrolledarea)
##--
#        self.__area = area

#        for i in range(8):
#            grid.addWidget(QLabel(f"Label {i}"), i, 0)
#            grid.addWidget(QLineEdit(), i, 1)
#            grid.addWidget(EditableComboBox(), i, 2)


#        self.vbox1.addStretch(1)
        self.vbox1.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        # The button-box
        self._add_dialog_buttons()


#        hbox2 = QHBoxLayout()
#        self.vbox1.addLayout(hbox2)
#        hbox2.addSpacing(100)
#        hbox2.addStretch(1)
#        self.course_update_button = QPushButton(T["UPDATE"])
#        self.course_update_button.clicked.connect(self.lesson_update)
#        hbox2.addWidget(self.course_update_button)
#        self.course_add_button = QPushButton(T["NEW"])
#        self.course_add_button.clicked.connect(self.lesson_add)
#        hbox2.addWidget(self.course_add_button)

    def activate(self, course, row):
        super().activate(course, row)
        if self.current_row < 0:
            #print("EMPTY LESSON TABLE:", repr(course))
            # Initialize with a basic, "normal" lesson
#            "id" is <None>
#            "course" is parameter <course>
            self.editors["LENGTH"].setText("1")
            self.editors["PAYROLL"].setText("*")
            self.editors["ROOM"].setText("?")    # ?
            self.editors["Partners"].setText("")
            self.editors["Time"].setText("?")
            self.editors["PLACE"].setText("?")
            self.editors["NOTES"].setText("")

        else:
            record = self.model.record(self.current_row)
            ltime, tag = parse_time_field(record.value("TIME"))
            self.editors["Partners"].setText(tag)
            self.editors["Time"].setText(ltime)
            self.editors["LENGTH"].setText(record.value("LENGTH"))
            self.editors["PAYROLL"].setText(record.value("PAYROLL"))
            self.editors["ROOM"].setText(record.value("ROOM"))
            self.editors["NOTES"].setText(record.value("NOTES"))

        self.form_modified("", False)  # initialize form button states

        self.__value = -1   # Default return value => don't change row
        self.exec()
        return self.__value

#TODO: Move to main window, and implement! But perhaps retain some code
# here if it differs from that for the block members.
    def lesson_add(self):
        """Add the data in the form editor as a new course."""
        print("ADD LESSON")
        return

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
                    self.return_value(r)            # Select this row
                    break
            else:
                SHOW_INFO(T["COURSE_ADDED"].format(klass=klass))
                self.return_value(self.current_row) # Reselect current row
        else:
            error = model.lastError()
            if "UNIQUE" in error.databaseText():
                SHOW_ERROR(T["COURSE_EXISTS"])
            else:
                SHOW_ERROR(error.text())
            model.revertAll()

#TODO
    def lesson_update(self):
        """Update the current course with the data in the form editor."""
        print("UPDATE LESSON")
        return

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
                    self.return_value(r)    # Select this row
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


class FormPopupEdit(QLineEdit):
    """A field editor for a "form".
    The value is presented in a read-only QLineEdit. It can be edited by
    activating (mouse click) the cell. A custom pop-up dialog handles
    the actual editing. When this returns a changed value, the function
    supplied as parameter <modified> is called with arguments field-name
    and new-value. This callback function should return true if the
    change is accepted.
    """
    def __init__(self, field, modified, parent=None, **kargs):
        super().__init__(parent)
        self.setReadOnly(True)
        self.__modified = modified
        self.__field = field
        self.params = kargs

    def mousePressEvent(self, event):
        print("FormPopupEdit.mousePressEvent: Override Me!")

    def text_edited(self, text):
        if self.__modified(self.__field, text):
            self.setText(text)


class FormPayrollEdit(FormPopupEdit):
    def mousePressEvent(self, event):
        result = PayrollDialog(**self.params).activate(
            start_value=self.text()
        )
        if result:
            self.text_edited(result)


class FormTimeEdit(FormPopupEdit):
    def set_time(self, ltime):
        print("§ SET TIME:", ltime)
        self.text_edited(ltime)

    def mousePressEvent(self, event):
        result = SHARED_DATA["DayPeriodDialog"].activate(
            start_value=self.text()
        )
        if result:
            self.text_edited(result)


class FormPartnersEdit(FormPopupEdit):
    def __init__(self, field, modified, timefield, parent=None):
        super().__init__(field, modified, parent)
        self.timefield = timefield

    def mousePressEvent(self, event):
        result = SHARED_DATA["PartnersDialog"].activate(
            start_value=self.text()
        )
        if result:
            if result == "-":
                self.text_edited("")
                # Leave time field untouched, i.e. preserve previous time
            elif result[0] == "+":
                # New tag
                self.text_edited(result[1:])
                # Leave time field untouched, i.e. preserve previous time
            else:
                self.text_edited(result)
                # Get time from chosen tag
                self.timefield.set_time(get_time_entry(result))


#TODO
class BlockLessonEditor(LessonEditorBase):
    """Popup editor for a "block" lesson.
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        form = QFormLayout()
        self.vbox1.addLayout(form)
        self.editors = {}
        # LENGTH is always '*' or empty?
        f = "PAYROLL"
# Is the original form ok? 0 is probably invalid.
        editwidget = FormPayrollEdit(f, self.form_modified)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)
        f = "ROOM"
        editwidget = FormRoomEdit(f, self.form_modified)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)
        # TIME is the block code: >sid#tag
# ...
        # PLACE is empty
        f = "NOTES"
        editwidget = FormLineEdit(f, self.form_modified)
        self.editors[f] = editwidget
        form.addRow(T[f], editwidget)

        # Then some sort of table with entries for each "lesson unit"
        # of the block. Each would have LENGTH, Time and Partner fields,
        # though I wouldn't expect the Partner fields to be used.
        # A read-only qtablewidget with click-handlers on the fields is
        # probably fine here.

        frame1 = QFrame()
        frame1.setLineWidth(2)
        frame1.setFrameShape(QFrame.Shape.Box)
        self.vbox1.addWidget(frame1)
        fbox0 = QVBoxLayout(frame1)
        fbox0.setContentsMargins(0, 0, 0, 0)
        self.blocklessons = QTableWidget()
        fbox0.addWidget(self.blocklessons)
        self.blocklessons.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.blocklessons.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.blocklessons.setColumnCount(3)
        self.blocklessons.setHorizontalHeaderLabels((
            T["LENGTH"],
            T["Time"],
            T["Partners"]
        ))
        hh = self.blocklessons.horizontalHeader()
        hh.setMinimumSectionSize(60)
        hh.setStretchLastSection(True)
        self.blocklessons.resizeColumnsToContents()

#TODO: Now, what about TIME and PLACE???
# TIME is rather difficult, because it can be:
#   - ?: not yet placed
#   - @Mi.3  (an actual time ... + fixed flag? – "fixed", "held" or "movable"?))
#   - >block-tag (sid + identifier)
#   - =parallel-tag (identifier)
# (Block tags and parallel tags should probably be kept quite separate by
# making the prefix significant, i.e. ">Ma-id1" and "=Ma-id1" would be
# completely distince tags, though a "=" tag wouldn't normally have a
# subject part anyway.)
# There may also be entries with 0 length. These are then items that
# are present in the table for their payroll-relevance, although they
# don't appear in the timetable. For these TIME and PLACE play no role
# and should be null. Whether the 0 length or the empty time field is
# the primary flag for payroll-only, would need to be decided.

# There would also be special lesson table entries with null "course"
# field to specify the actual times of block members and parallel lessons.
# For these the tag would be in the PLACE field. Parallel lessons have
# just one such entry per tag, other fields – except TIME – being null.
# Block members can have several such entries (a block can consist of
# more than one lesson a week). These would also need to use the LENGTH
# field, to specify the duration of each component lesson.

# Note that these special entries also need to be visible, as part of
# the editor for the entries that reference them ...


#        # Fields for "block member"
#        box2 = QFrame()
#        self.stack.addWidget(box2)
##        form = QFormLayout(box2)

## Just testing ...
#        vbox2 = QVBoxLayout(box2)
#        vbox2.addWidget(QLabel("Header !"))
#        area = LessonScrollArea()
#        vbox2.addWidget(area)
#        scrolledarea = QWidget()
#        grid = QGridLayout()
#        scrolledarea.setLayout(grid)
#        area.setWidgetResizable(True)
#        area.setWidget(scrolledarea)
##--
#        self.__area = area

#        for i in range(8):
#            grid.addWidget(QLabel(f"Label {i}"), i, 0)
#            grid.addWidget(QLineEdit(), i, 1)
#            grid.addWidget(EditableComboBox(), i, 2)


#        self.vbox1.addStretch(1)
        self.vbox1.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        # The button-box
#        self._add_dialog_buttons()


#        hbox2 = QHBoxLayout()
#        self.vbox1.addLayout(hbox2)
#        hbox2.addSpacing(100)
#        hbox2.addStretch(1)
#        self.course_update_button = QPushButton(T["UPDATE"])
#        self.course_update_button.clicked.connect(self.lesson_update)
#        hbox2.addWidget(self.course_update_button)
#        self.course_add_button = QPushButton(T["NEW"])
#        self.course_add_button.clicked.connect(self.lesson_add)
#        hbox2.addWidget(self.course_add_button)

    def activate(self, course, row):
        super().activate(course, row)
        if self.current_row < 0:
            #print("EMPTY LESSON TABLE:", repr(course))
            # Initialize with a basic, "normal" lesson
#            "id" is <None>
#            "course" is parameter <course>
            self.editors["LENGTH"].setText("1")
            self.editors["PAYROLL"].setText("*")
            self.editors["ROOM"].setText("?")    # ?
            self.editors["Partners"].setText("")
            self.editors["Time"].setText("?")
            self.editors["PLACE"].setText("?")
            self.editors["NOTES"].setText("")

        else:
            record = self.model.record(self.current_row)
            ltime, tag = parse_time_field(record.value("TIME"))
            self.editors["Partners"].setText(tag)
            self.editors["Time"].setText(ltime)
            self.editors["LENGTH"].setText(record.value("LENGTH"))
            self.editors["PAYROLL"].setText(record.value("PAYROLL"))
            self.editors["ROOM"].setText(record.value("ROOM"))
            self.editors["NOTES"].setText(record.value("NOTES"))

        self.form_modified("", False)  # initialize form button states

        self.__value = -1   # Default return value => don't change row
        self.exec()
        return self.__value


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from ui.ui_base import run

    widget = Courses()
    widget.enter()
    widget.resize(1000, 550)
    run(widget)
