"""
ui/lesson_tag_dialog.py

Last updated:  2022-04-29

Handle lesson tags (course blocks and parallel lessons).


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

# TODO ....

########################################################################

if __name__ == "__main__":
    import sys, os, builtins

    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start
    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    #    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))

#T = TRANSLATIONS("ui.lesson_tag_dialog")
T = TRANSLATIONS("ui.modules.course_lessons")

### +++++

from core.db_management import open_database, db_read_full_table
from core.classes import get_class_list

from ui.ui_base import (
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QListWidget,
    QAbstractItemView,



    HLine,
    LoseChangesDialog,
    KeySelector,
    TableViewRowSelect,
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
    QTableView,
    ### QtCore:
    Qt,
    QSize,
    ### QtSql:
    QSqlTableModel,
)

# Course table fields
"""COURSE_COLS = [(f, T[f]) for f in (
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
"""
# SUBJECT, CLASS and TEACHER are foreign keys with:
#  on delete cascade + on update cascade
FOREIGN_FIELDS = ("CLASS", "TEACHER", "SUBJECT")

#FILTER_FIELDS = [cc for cc in COURSE_COLS if cc[0] in FOREIGN_FIELDS]

# Group of fields which determines a course (the tuple must be unique)
COURSE_KEY_FIELDS = ("CLASS", "GRP", "SUBJECT", "TEACHER")

"""LESSON_COLS = [(f, T[f]) for f in (
        "course",
        "LENGTH",
        "PAYROLL",
        "TAG",
        "ROOM",
        "NOTES"
    )
]
"""

LESSON_COLS = [
    "id",
    "course",
    "LENGTH",
    "PAYROLL",
    "TAG",
    "ROOM",
    "NOTES"
]

COMPONENT_COLS = [ #(f, T[f]) for f in (
        "id",           # hide
        "course",       # hide
        "LENGTH",       # ? hide?
        "PAYROLL",      # ?
        "TAG",          # ? hide?
        "ROOM",         # ?
        "NOTES",         # ?
# Then via "course":
        "CLASS",
        "GRP",
        "SUBJECT",
        "TEACHER",
    #)
]

COL_LIST = [
        "CLASS",
        "id",
        "course",
        "GRP",
        "SUBJECT",
        "TEACHER",
        "LENGTH",       # ? hide?
        "PAYROLL",      # ?
#        "TAG",          # ? hide?
        "ROOM",         # ?
        "PLACE",
        "NOTES",         # ?
]

### -----

class LessonTagDialog(QDialog):
    def __init__(self):
        super().__init__()
        vbox0 = QVBoxLayout(self)
        hbox1 = QHBoxLayout()
        vbox0.addLayout(hbox1)
        self.classlist = ListWidget()
        self.classlist.setMinimumWidth(30)
        self.classlist.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.classlist.currentTextChanged.connect(self.select_class)
        hbox1.addWidget(self.classlist)

        self.lessontable = QTableWidget()
        self.lessontable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lessontable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lessontable.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )  # non-editable
        self.lessontable.verticalHeader().hide()
        self.lessontable_cols = COL_LIST[1:]
        self.lessontable.setColumnCount(len(self.lessontable_cols))
        self.lessontable.setHorizontalHeaderLabels(self.lessontable_cols)
        hbox1.addWidget(self.lessontable)
        hbox1.setStretch(1, 1)

        #hbox1.addStretch(1)

        self.init_classes()

    def form(self):
        # Actually only (some of) the lesson fields should be editable,
        # and there may be special editors ...
        editor = QFormLayout()
        self.form_editors = {}
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

    def init_classes(self):
        self.classlist.clear()
        for klass, kname in get_class_list(skip_null=False):
            self.classlist.addItem(klass)
        self.classlist.setCurrentRow(0)


    def select_class(self, klass):
        print("SELECT CLASS:", klass)
        # Get the (timetable-relevant) "lessons" for the selected class
        cfields, cvalues = db_read_full_table("COURSES", CLASS=klass)
        cfmap = {cfields[i]: i for i in range(len(cfields))}
        print("Course fields:", cfmap)

        coursecol = cfmap["course"]
        coursemap = {row[coursecol]: row for row in cvalues}
        courses = list(coursemap)
        print("Course ids:", courses)

        lfields, lvalues = db_read_full_table("LESSONS", course=courses)
        lfmap = {lfields[i]: i for i in range(len(lfields))}
        print("Fields:", lfmap)
        self.lessontable.setRowCount(len(lvalues))
        self.lessontable.clearContents()
        lcoursecol = lfmap["course"]
        r = 0
        for row in lvalues:
            print("LESSONS:", row)
            c = 0
            course = row[lcoursecol]
            crow = coursemap[course]
            for f in self.lessontable_cols:
                try:
                    col = lfmap[f]
                    val = row[col]
                except KeyError:
                    try:
                        col = cfmap[f]
                        val = crow[col]
                    except KeyError:
                        raise Bug("Unexpected data structure")

                self.lessontable.setItem(r, c, QTableWidgetItem(str(val)))
                c += 1

            r += 1

        self.lessontable.resizeColumnsToContents()
        # Toggle the stretch on the last section here because of a
        # possible bug in Qt, where the stretch can be lost when
        # repopulating.
        hh = self.lessontable.horizontalHeader()
        hh.setStretchLastSection(False)
        hh.setStretchLastSection(True)


        print("Wanted fields:", self.lessontable_cols)


# Consider making this dialog the main/only editor for "lessons" – it
# could be activated by "entering" one of the now read-only entries in
# the base lesson table.

class ListWidget(QListWidget):
  def sizeHint(self):
    s = QSize()
    s.setHeight(super().sizeHint().height())
    s.setWidth(self.sizeHintForColumn(0))
    print("???", s)
    return s


class Courses:#(Page):
#    name = T["MODULE_NAME"]
#    title = T["MODULE_TITLE"]

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

class XTableView(QTableView):
    def keyPressEvent(self, e):
        key = e.key()
        i = self.currentIndex()
        if not self.isPersistentEditorOpen(i):
            if key == Qt.Key_Return:
                # start editing
                self.edit(i)
                return
            elif key == Qt.Key_Delete:
                # clear cell
                self.model().setData(i, "")
                return
        super().keyPressEvent(e)


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
        self.coursetable = TableViewRowSelect(self)
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
        self.course_delete_button = QPushButton(T["DELETE"])
        self.course_delete_button.clicked.connect(self.course_delete)
        hbox2.addWidget(self.course_delete_button)
        self.course_update_button = QPushButton(T["UPDATE"])
        self.course_update_button.clicked.connect(self.course_update)
        hbox2.addWidget(self.course_update_button)
        self.course_add_button = QPushButton(T["NEW"])
        self.course_add_button.clicked.connect(self.course_add)
        hbox2.addWidget(self.course_add_button)

        vbox2.addWidget(HLine())

        lessonbox = QFrame()
        vbox2.addWidget(lessonbox)
        vbox3 = QVBoxLayout(lessonbox)
        vbox3.setContentsMargins(0, 0, 0, 0)
        vbox3.addWidget(QLabel(f"<h4>{T['LESSONS']}</h4>"))

        # The lesson table
        self.lessontable = XTableView()
        self.lessontable.setStyleSheet(
            """QTableView {
               selection-background-color: #e0e0ff;
               selection-color: black;
            }
            QTableView::item:focus {
                selection-background-color: #d0ffff;
            }
            """
        )
        self.lessontable.setSelectionMode(QTableView.SingleSelection)
        self.lessontable.setSelectionBehavior(QTableView.SelectRows)
        self.lessontable.verticalHeader().hide()

        vbox3.addWidget(self.lessontable)
        hbox3 = QHBoxLayout()
        vbox2.addLayout(hbox3)
        hbox3.addStretch(1)
        self.lesson_delete_button = QPushButton(T['DELETE'])
        hbox3.addWidget(self.lesson_delete_button)
        self.lesson_delete_button.clicked.connect(self.lesson_delete)
        self.lesson_add_button = QPushButton(T['COPY_NEW'])
        hbox3.addWidget(self.lesson_add_button)
        self.lesson_add_button.clicked.connect(self.lesson_add)

        self.form_change_set = None
        self.setStretchFactor(0, 1)  # stretch only left panel

    def modified(self):
        return bool(self.form_change_set)

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
        self.lessontable.horizontalHeader().setStretchLastSection(True)

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
                SHOW_ERROR(T["COURSE_EXISTS"])
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
                SHOW_ERROR(T["COURSE_EXISTS"])
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
                SHOW_ERROR(T["COURSE_EXISTS"])
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

        # Toggle the stretch on the last section here because of a
        # possible bug in Qt, where the stretch can be lost when
        # repopulating.
        hh = self.lessontable.horizontalHeader()
        hh.setStretchLastSection(False)
        hh.setStretchLastSection(True)

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


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    open_database()

    from ui.ui_base import run

    widget = LessonTagDialog()
    widget.resize(1000, 550)
    widget.exec()
#    run(widget)
