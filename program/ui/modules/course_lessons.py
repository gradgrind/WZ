"""
ui/modules/course_lessons.py

Last updated:  2022-04-17

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

# TODO: I have not yet worked out how to handle the blocks which
# share a "course tuple" (previously sids like ZwE+9u10). At the moment
# I have put the extra bit in the GRP field.

# TODO: add a status bar for short messages, etc.?

### Messages
_LOSE_CHANGES = "Die Änderungen werden verworfen. Weitermachen?"
_COURSE_EXISTS = "Der geänderte „Kurs“ existiert schon"

### Labels
_NAME = "Kurse/Stunden"
_TITLE = "Unterrichtskurse und -stunden verwalten"

# Course field editor buttons
_DELETE = "Löschen"
_UPDATE = "Übernehmen"
_NEW = "Hinzufügen"
_COPY_NEW = "Neu (Kopie)"

# Course table title line
_COURSE_TITLE = "Kurse"
_FILTER = "Filter:"

# Course table fields
COURSE_COLS = [
    ("course", "KursNr"),
    ("CLASS", "Klasse"),
    ("GRP", "Gruppe"),
    ("SUBJECT", "Fach"),
    ("TEACHER", "Lehrkraft"),
    ("REPORT", "Zeugnis"),
    ("GRADE", "Note"),
    ("COMPOSITE", "Sammelfach"),
]
# SUBJECT, CLASS and TEACHER are foreign keys with:
#  on delete cascade + on update cascade
FOREIGN_FIELDS = ("CLASS", "TEACHER", "SUBJECT")

FILTER_FIELDS = [
    cc for cc in COURSE_COLS if cc[0] in FOREIGN_FIELDS
]

# Group of fields which determines a course (the tuple must be unique)
COURSE_KEY_FIELDS = ("CLASS", "GRP", "SUBJECT", "TEACHER")

# Lesson table
_LESSONS = "Unterrichts- bzw. Deputatsstunden"

LESSON_COLS = [
    ("course", "KursNr"),
    ("LENGTH", "Länge"),
    ("PAYROLL", "Deputat"),
    ("TAG", "Kennung"),
    ("ROOM", "Raum"),
    ("NOTES", "Notizen"),
]

########################################################################

if __name__ == "__main__":
    import locale, sys, os, builtins

    print("LOCALE:", locale.setlocale(locale.LC_ALL, ""))
    this = sys.path[0]
    appdir = os.path.dirname(os.path.dirname(this))
    sys.path[0] = appdir
    try:
        builtins.PROGRAM_DATA = os.environ["PROGRAM_DATA"]
    except KeyError:
        basedir = os.path.dirname(appdir)
        builtins.PROGRAM_DATA = os.path.join(basedir, "wz-data")
    from ui.ui_base import StandalonePage as Page
    from core.base import start

    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    #    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))
else:
    from ui.ui_base import StackPage as Page

### +++++

from ui.ui_base import (
    open_database,
    HLine,
    LoseChangesDialog,
    KeySelector,
    # QtWidgets
    QSplitter,
    QFrame,
    QFormLayout,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTableView,
    QStyledItemDelegate,
    # QtCore
    Qt,
    # QtSql
    QSqlDatabase,
    QSqlQueryModel,
    QSqlQuery,
    QSqlTableModel,
)

### -----


def init():
    MAIN_WIDGET.add_tab(Courses())


class Courses(Page):
    name = _NAME
    title = _TITLE

    def __init__(self):
        super().__init__()
        self.course_editor = CourseEditor()
        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.course_editor)

    def enter(self):
        open_database()
        self.course_editor.init_data()

    def is_modified(self):
        return bool(self.course_editor.form_change_set)


# ++++++++++++++ The widget implementation ++++++++++++++


class CourseTableView(QTableView):
    """This avoids some very strange selection behaviour in QTableView,
    which I assume to be a bug:
    Programmatic switching of the selected row doesn't necessarily cause
    the visible selection (blue background) to move, although the
    current (selected) row does change. Clicking and moving (slightly
    dragging) the mouse produce different responses.
    """

    def __init__(self, main_widget):
        super().__init__()
        self.main_widget = main_widget

    def mousePressEvent(self, e):
        index = self.indexAt(e.pos())
        if index.isValid() and (
            (not self.main_widget.form_change_set) or LoseChangesDialog()
        ):
            self.selectRow(index.row())

    def mouseMoveEvent(self, e):
        pass


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
        hbox1.addWidget(QLabel(f"<h4>{_COURSE_TITLE}</h4>"))
        hbox1.addStretch(1)
        hbox1.addWidget(QLabel(f"<h5>{_FILTER}</h5>"))
        self.filter_field_select = KeySelector(
            value_mapping=FILTER_FIELDS, changed_callback=self.set_filter_field
        )
        hbox1.addWidget(self.filter_field_select)
        self.filter_value_select = KeySelector(changed_callback=self.set_filter)
        hbox1.addWidget(self.filter_value_select)

        # The course table itself
        self.coursetable = CourseTableView(self)
        self.coursetable.setSelectionMode(QTableView.SingleSelection)
        self.coursetable.setSelectionBehavior(QTableView.SelectRows)
        self.coursetable.setEditTriggers(
            QTableView.NoEditTriggers
        )  # non-editable
        self.coursetable.verticalHeader().hide()
        vbox1.addWidget(self.coursetable)

        self.rightframe = QFrame()
        self.addWidget(self.rightframe)
        self.rightframe.setLineWidth(2)
        self.rightframe.setFrameShape(QFrame.Box)

        vbox2 = QVBoxLayout(self.rightframe)
        editorbox = QFrame()
        self.courseeditor = QFormLayout(editorbox)
        vbox2.addWidget(editorbox)
        self.editors = {}
        for f, t in COURSE_COLS:
            if f == "course":
                editwidget = QLineEdit()
                editwidget.setReadOnly(True)
            elif f in FOREIGN_FIELDS:
                editwidget = FormComboBox(f, self.form_modified)
            else:
                editwidget = FormLineEdit(f, self.form_modified)
            self.editors[f] = editwidget
            self.courseeditor.addRow(t, editwidget)

        hbox2 = QHBoxLayout()
        vbox2.addLayout(hbox2)
        hbox2.addStretch(1)
        self.course_delete_button = QPushButton(_DELETE)
        self.course_delete_button.clicked.connect(self.course_delete)
        hbox2.addWidget(self.course_delete_button)
        self.course_update_button = QPushButton(_UPDATE)
        self.course_update_button.clicked.connect(self.course_update)
        hbox2.addWidget(self.course_update_button)
        self.course_add_button = QPushButton(_NEW)
        self.course_add_button.clicked.connect(self.course_add)
        hbox2.addWidget(self.course_add_button)

        vbox2.addWidget(HLine())

        lessonbox = QFrame()
        vbox2.addWidget(lessonbox)
        vbox3 = QVBoxLayout(lessonbox)
        vbox3.setContentsMargins(0, 0, 0, 0)
        vbox3.addWidget(QLabel(f"<h4>{_LESSONS}</h4>"))

        # The lesson table
        self.lessontable = QTableView()
        self.lessontable.setSelectionMode(QTableView.SingleSelection)
        self.lessontable.setSelectionBehavior(QTableView.SelectRows)
        self.lessontable.verticalHeader().hide()

        vbox3.addWidget(self.lessontable)
        hbox3 = QHBoxLayout()
        vbox2.addLayout(hbox3)
        hbox3.addStretch(1)
        self.lesson_delete_button = QPushButton(_DELETE)
        hbox3.addWidget(self.lesson_delete_button)
        self.lesson_delete_button.clicked.connect(self.lesson_delete)
        self.lesson_add_button = QPushButton(_COPY_NEW)
        hbox3.addWidget(self.lesson_add_button)
        self.lesson_add_button.clicked.connect(self.lesson_add)

        self.form_change_set = None
        self.setStretchFactor(0, 1)  # stretch only left panel

    def leave_ok(self):
        if self.form_change_set:
            return LoseChangesDialog()
        return True

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

    def form_modified(self, field, changed):
        """Handle a change in a form editor field.
        Maintain the set of changed fields (<self.form_change_set>).
        Enable and disable the pushbuttons appropriately.
        """
        if self.form_change_set == None:
            return
        if self.table_empty:
            self.course_update_button.setEnabled(False)
            self.course_add_button.setEnabled(True)
            self.course_delete_button.setEnabled(False)
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
                self.course_delete_button.setEnabled(True)
                self.course_update_button.setEnabled(False)
                self.course_add_button.setEnabled(False)
        # print("FORM CHANGED SET:", self.form_change_set)

    def init_data(self):
        # Set up the course model, first clearing the "model-view"
        # widgets (in case this is a reentry)
        self.coursetable.setModel(None)
        self.lessontable.setModel(None)
        for f in FOREIGN_FIELDS:
            self.editors[f].clear()

        self.coursemodel = QSqlTableModel()
        self.coursemodel.setTable("COURSES")
        self.coursemodel.setEditStrategy(QSqlTableModel.OnManualSubmit)
        # Set up the course view
        self.coursetable.setModel(self.coursemodel)
        selection_model = self.coursetable.selectionModel()
        selection_model.currentChanged.connect(self.course_changed)
        self.filter_list = {}
        for f, t in COURSE_COLS:
            i = self.coursemodel.fieldIndex(f)
            editwidget = self.editors[f]
            if f == "CLASS":
                kv = db_key_value_list("CLASSES", "CLASS", "NAME", "CLASS")
                self.filter_list[f] = kv
                editwidget.setup(kv)
                # delegate = ForeignKeyItemDelegate(editwidget,
                #        parent=self.coursemodel)
                # self.coursetable.setItemDelegateForColumn(i, delegate)
            if f == "SUBJECT":
                kv = db_key_value_list("SUBJECTS", "SID", "NAME", "NAME")
                self.filter_list[f] = kv
                editwidget.setup(kv)
                delegate = ForeignKeyItemDelegate(
                    editwidget, parent=self.coursemodel
                )
                self.coursetable.setItemDelegateForColumn(i, delegate)
            elif f == "TEACHER":
                kv = db_key_value_list("TEACHERS", "TID", "NAME", "SORTNAME")
                self.filter_list[f] = kv
                editwidget.setup(kv)
                delegate = ForeignKeyItemDelegate(
                    editwidget, parent=self.coursemodel
                )
                self.coursetable.setItemDelegateForColumn(i, delegate)
            self.coursemodel.setHeaderData(i, Qt.Horizontal, t)

        # Set up the lesson model
        self.lessonmodel = QSqlTableModel()
        self.lessonmodel.setTable("LESSONS")
        self.lessonmodel.setEditStrategy(QSqlTableModel.OnFieldChange)
        # Set up the lesson view
        self.lessontable.setModel(self.lessonmodel)
        for f, t in LESSON_COLS:
            i = self.lessonmodel.fieldIndex(f)
            self.lessonmodel.setHeaderData(i, Qt.Horizontal, t)
        self.lessontable.hideColumn(0)
        self.lessontable.hideColumn(1)

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
            self.course_changed(None, None)
        self.coursetable.resizeColumnsToContents()

    def course_changed(self, new, old):
        if new:
            self.table_empty = False
            row = new.row()
            # print("CURRENT", old.row(), "->", row)
            record = self.coursemodel.record(row)
            for f, t in COURSE_COLS:
                self.editors[f].setText(str(record.value(f)))
            self.set_course(record.value(0))
        else:
            # e.g. when entering an empty table
            self.table_empty = True
            # print("EMPTY TABLE")
            for f, t in COURSE_COLS:
                self.editors[f].setText("")
            self.editors[self.filter_field].setText(self.filter_value)
            self.set_course(0)
        self.form_change_set = set()
        self.form_modified("", False)  # initialize form button states

    def course_delete(self):
        """Delete the current course."""
        model = self.coursemodel
        if self.form_change_set:
            if not LoseChangesDialog():
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
                self.course_changed(None, None)
        else:
            error = model.lastError()
            if "UNIQUE" in error.databaseText():
                SHOW_ERROR(_COURSE_EXISTS)
            else:
                SHOW_ERROR(error.text())
            model.revertAll()

    def course_add(self):
        """Add the data in the form editor as a new course."""
        model = self.coursemodel
        index = self.coursetable.currentIndex()
        row0 = index.row()
        row = 0
        model.insertRow(row)
        for f, t in COURSE_COLS[1:]:
            col = model.fieldIndex(f)
            val = self.editors[f].text()
            model.setData(model.index(row, col), val)
        if model.submitAll():
            course = model.query().lastInsertId()
            # print("INSERTED:", course)
            for r in range(model.rowCount()):
                if model.data(model.index(r, 0)) == course:
                    self.coursetable.selectRow(r)
                    break
            else:
                self.coursetable.selectRow(row0)
        else:
            error = model.lastError()
            if "UNIQUE" in error.databaseText():
                SHOW_ERROR(_COURSE_EXISTS)
            else:
                SHOW_ERROR(error.text())
            model.revertAll()

    def course_update(self):
        """Update the current course with the data in the form editor."""
        model = self.coursemodel
        index = self.coursetable.currentIndex()
        course = model.data(index)
        row = index.row()
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
                    self.coursetable.selectRow(r)
                    break
            else:
                if row >= model.rowCount():
                    row = model.rowCount() - 1
                self.coursetable.selectRow(row)
        else:
            error = model.lastError()
            if "UNIQUE" in error.databaseText():
                SHOW_ERROR(_COURSE_EXISTS)
            else:
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
        # Enable or disable lesson butttons
        if self.lessonmodel.rowCount():
            self.lesson_delete_button.setEnabled(True)
        else:
            self.lesson_delete_button.setEnabled(False)
        self.lesson_add_button.setEnabled(course > 0)

    def lesson_delete(self):
        """Delete the current "lesson"."""
        model = self.lessonmodel
        index = self.lessontable.currentIndex()
        row = index.row()
        if model.removeRow(row):
            model.select()
            n = model.rowCount()
            if n == 0:
                self.lesson_delete_button.setEnabled(False)
            elif row >= n:
                self.lessontable.selectRow(n - 1)
            else:
                self.lessontable.selectRow(row)
        else:
            SHOW_ERROR(f"DB Error: {model.lastError().text()}")

    def lesson_add(self):
        """Add a new "lesson", copying the current one if possible."""
        if self.this_course:
            model = self.lessonmodel
            index = self.lessontable.currentIndex()
            if index.isValid():
                row = index.row()
                model.select()  # necessary to ensure current row is up to date
                record = model.record(row)
                # print("RECORD:", [record.value(i) for i in range(record.count())])
                record.setValue(0, None)
                n = model.rowCount()
            else:
                record = model.record()
                record.setValue(1, self.this_course)
                n = 0
            if model.insertRecord(-1, record):
                model.select()  # necessary to make new row immediately usable
                self.lessontable.selectRow(n)
                self.lesson_delete_button.setEnabled(True)
            else:
                SHOW_ERROR(f"DB Error: {model.lastError().text()}")


class ForeignKeyItemDelegate(QStyledItemDelegate):
    """An "item delegate" for displaying referenced values in
    foreign key fields.

    Specifically, these objects rely on separate field editor widgets
    (<FormComboBox> instances) to supply the key -> value mapping.
    """

    def __init__(self, editwidget, parent=None):
        super().__init__(parent)
        self.editwidget = editwidget

    def displayText(self, value, locale):
        return self.editwidget.itemText(self.editwidget.key2i[value])


class FormLineEdit(QLineEdit):
    """A specialized line editor for use in the course editor form."""

    def __init__(self, field, modified, parent=None):
        super().__init__(parent)
        self.__modified = modified
        self.__field = field
        self.text0 = None
        self.textEdited.connect(self.text_edited)

    def setText(self, text):
        super().setText(text)
        self.text0 = text

    def text_edited(self, text):
        self.__modified(self.__field, text != self.text0)


def db_key_value_list(table, key_field, value_field, sort_field):
    """Return a list of (key, value) pairs from the given database table."""
    model = QSqlQueryModel()
    model.setQuery(
        f"SELECT {key_field}, {value_field} FROM {table}"
        f" ORDER BY {sort_field}"
    )
    key_value_list = []
    for i in range(model.rowCount()):
        record = model.record(i)
        key_value_list.append((record.value(0), record.value(1)))
    return key_value_list


class FormComboBox(QComboBox):
    """A specialized combobox for use in the course editor form."""

    def __init__(self, field, modified, parent=None):
        super().__init__(parent)
        self.__modified = modified
        self.__field = field
        self.text0 = None
        self.currentIndexChanged.connect(self.change_index)

    def setup(self, key_value_list):
        """Set up the indexes required for the table's item delegate
        and the combobox (<editwidget>).
        """
        self.keylist = []
        self.key2i = {}
        self.clear()
        i = 0
        for k, v in key_value_list:
            self.key2i[k] = i
            self.keylist.append(k)
            self.addItem(v)
            i += 1

    def text(self):
        """Return the current "key"."""
        return self.keylist[self.currentIndex()]

    def setText(self, text):
        """<text> is the "key"."""
        if text:
            try:
                i = self.key2i[text]
            except KeyError:
                raise Bug(
                    f"Unknown key for editor field {self.__field}: '{text}'"
                )
            self.setCurrentIndex(i)
            self.text0 = text
        else:
            self.setCurrentIndex(0)
            self.text0 = self.keylist[0]

    def change_index(self, i):
        sid = self.keylist[i]
        self.__modified(self.__field, sid != self.text0)


# An example of code to create and populate the CLASSES table
def enter_classes():
    from qtpy.QtSql import QSqlQuery

    dbpath = DATAPATH("db1.sqlite")
    con = QSqlDatabase.addDatabase("QSQLITE")
    con.setDatabaseName(dbpath)
    if not con.open():
        raise Bug(f"Cannot open database at {dbpath}")
    print("TABLES:", con.tables())

    query = QSqlQuery()
    query.exec("drop table CLASSES")
    if not query.exec(
        "create table CLASSES(CLASS text primary key,"
        " NAME text unique not null, CLASSROOM text)"
    ):
        error = query.lastError()
        print("!!!", error.databaseText())
        # print("!!!2", error.text())

    classes = []
    names = []
    classrooms = []
    for i in range(1, 13):
        k = f"{i:02}G"
        classes.append(k)
        names.append(f"{i}. Großklasse")
        classrooms.append(f"r{k}")
        k = f"{i:02}K"
        classes.append(k)
        names.append(f"{i}. Kleinklasse")
        classrooms.append(f"r{k}")
    classes.append("13")
    names.append("13. Klasse")
    classrooms.append("r13")

    classes.append("--")
    names.append("keine Klasse")
    classrooms.append("")

    query.prepare("insert into CLASSES values (?, ?, ?)")
    query.addBindValue(classes)
    query.addBindValue(names)
    query.addBindValue(classrooms)
    if not query.execBatch():
        error = query.lastError()
        print("!!!", error.databaseText())
        # print("!!!2", error.text())


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    #    enter_classes()
    #    quit(0)

    from ui.ui_base import run

    widget = Courses()
    widget.enter()
    widget.resize(1000, 550)
    run(widget)
