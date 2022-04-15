"""
ui/course_editor_widget.py

Last updated:  2022-04-15

A dual table widget with row editing capabilities.
It is intended for use with course/lesson data. The first table
includes basic course information and information for the pupil reports.
The second table handles information for teaching hours and the
timetable, the displayed rows being dependent on the row selected in
the first table.

=+LICENCE=================================
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

=-LICENCE=================================
"""

### Messages
_LOSE_CHANGES = "Die Änderungen werden verworfen. Weitermachen?"

### Labels
# Course field editor buttons
_DELETE = "Löschen"
_UPDATE = "Übernehmen"
_NEW = "Hinzufügen"

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
    ("COMPOSITE", "Sammelfach")
]

FILTER_FIELDS = [
    cc for cc in COURSE_COLS
    if cc[0] in ("CLASS", "TEACHER", "SUBJECT")
]

# Group of fields which determines a course (the tuple must be unique)
COURSE_KEY_FIELDS = ("CLASS", "GRP", "SUBJECT", "TEACHER")

# Lesson table
_LESSONS = "Unterrichts- bzw. Deputatsstunden"

########################################################################

import sys, os

if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication([])

    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    # TODO: Temporary redirection to use real data (there isn't any test data yet!)
    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    start.setup(os.path.join(basedir, 'DATA'))
    #start.setup(os.path.join(basedir, "DATA-2023"))

### +++++

from ui.ui_base import HLine, YesOrNoDialog, KeySelector

from qtpy.QtWidgets import (
    QSplitter,
    QFrame,
    QFormLayout,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,

    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,

    QTableView,
    QDataWidgetMapper,

#    QTableWidgetItem,
#    QMessageBox,
    QStyledItemDelegate,
#    QStyleOptionViewItem,
)
from qtpy.QtCore import Qt#, QPointF, QRectF, QSize
#from qtpy.QtGui import QKeySequence
#from qtpy.QtWidgets import QAction  # in Qt6 it is in QtGui
from qtpy.QtSql import (
    QSqlDatabase,
    QSqlQueryModel,
    QSqlQuery,
    QSqlTableModel,
#    QSqlRelationalTableModel,
#    QSqlRelation,
#    QSqlRelationalDelegate
)

### -----

class RowSelectTable(QTableWidget):
    """A table which is editable on a row basis. It has column headers,
    but no row headers.
#?
    The column headers can have display texts which
    differ from the internal data field names.
    """
    def __init__(self, headers, parent=None, readonly=False):
        super().__init__(parent=parent)
        self.setSelectionMode(self.SingleSelection)
        self.setSelectionBehavior(self.SelectRows)
        if readonly:
            self.setEditTriggers(self.NoEditTriggers)   # non-editable
        self.verticalHeader().hide()
        self.itemSelectionChanged.connect(self.selection_changed)
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

    def selection_changed(self):
        try:
            modelindex = self.selectedIndexes()[0]
            print("SELECT", modelindex.row())
        except IndexError:
            print("UNSELECT")


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
        if (index.isValid()
            and (
                (not self.main_widget.form_change_set)
                or YesOrNoDialog(_LOSE_CHANGES)
            )
        ):
            self.selectRow(index.row())

    def mouseMoveEvent(self, e):
        pass


class CourseEditor(QSplitter):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setChildrenCollapsible(False)

        dbpath = DATAPATH("db1.sqlite")
        con = QSqlDatabase.addDatabase("QSQLITE")
        con.setDatabaseName(dbpath)
        if not con.open():
            raise Bug(f"Cannot open database at {dbpath}")
        #print("TABLES:", con.tables())

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
            value_mapping=FILTER_FIELDS,
            changed_callback=self.set_filter_field
        )
        hbox1.addWidget(self.filter_field_select)
        self.filter_value_select = KeySelector(
            changed_callback=self.set_filter
        )
        hbox1.addWidget(self.filter_value_select)

        # The course table itself
        self.coursetable = CourseTableView(self)
        self.coursetable.setSelectionMode(QTableView.SingleSelection)
        self.coursetable.setSelectionBehavior(QTableView.SelectRows)
        self.coursetable.setEditTriggers(QTableView.NoEditTriggers)   # non-editable
        #self.coursetable.setStyleSheet("QTableView::item:selected{"
        #           "background:rgb(135, 206, 255)}")
        self.coursetable.verticalHeader().hide()
        #self.coursetable.setLineWidth(2)
        #self.coursetable.setFrameShape(self.Box)
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
            elif f == "SUBJECT":
                editwidget = FormComboBox(f, self.form_modified)
            elif f == "TEACHER":
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
#TODO
        self.lessontable = RowSelectTable(["Länge", "Deputat", "Kennung",
                "Raum", "Notizen"])
        vbox3.addWidget(self.lessontable)
        hbox3 = QHBoxLayout()
        vbox2.addLayout(hbox3)
        hbox3.addStretch(1)
        del3 = QPushButton("Löschen")
        hbox3.addWidget(del3)
        new3 = QPushButton("Kopie Hinzufügen")
        hbox3.addWidget(new3)

#TODO
        self.lessontable.setRowCount(5)

        self.form_change_set = None
        self.init_data()

    def leave_ok(self):
        if self.form_change_set:
            return YesOrNoDialog(_LOSE_CHANGES)
#TODO: check for pending changes to lesson table
        return True

    def set_filter_field(self, field):
        self.filter_value_select.set_items(self.filter_list[field])
        #print("FILTER FIELD:", field)
        self.filter_field = field
        self.filter_value_select.trigger()
        return True

    def set_filter(self, key):
        #print("FILTER KEY:", key)
        self.fill_course_table(key)
        return True

    def form_modified(self, field, changed):
        """Handle a change in a form editor field.
        Maintain the set of changed fields (<self.form_change_set>).
        Enable and disable the pushbuttons appropriately.
        """
        if self.form_change_set == None:
            return
        if changed:
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
        #print("FORM CHANGED SET:", self.form_change_set)

    def init_data(self):
        #con = QSqlDatabase.database()
        # Set up the model
        self.coursemodel = QSqlTableModel()
        self.coursemodel.setTable("COURSES")
        self.coursemodel.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.filter_list = {}
        for f, t in COURSE_COLS:
            i = self.coursemodel.fieldIndex(f)
            editwidget = self.editors[f]
            if f == "SUBJECT":
                kv = db_key_value_list("SUBJECTS", "SID", "NAME", "NAME")
                self.filter_list[f] = kv
                editwidget.setup(kv)
                delegate = ForeignKeyItemDelegate(editwidget,
                        parent=self.coursemodel)
                self.coursetable.setItemDelegateForColumn(i, delegate)
            elif f == "TEACHER":
                kv = db_key_value_list("TEACHERS", "TID", "NAME", "SORTNAME")
                self.filter_list[f] = kv
                editwidget.setup(kv)
                delegate = ForeignKeyItemDelegate(editwidget,
                        parent=self.coursemodel)
                self.coursetable.setItemDelegateForColumn(i, delegate)
            self.coursemodel.setHeaderData(i, Qt.Horizontal, t)
        self.filter_list["CLASS"] = db_key_value_list(
            "CLASSES", "CLASS", "NAME", "CLASS"
        )
        self.filter_field_select.trigger()

    def fill_course_table(self, filter_value):
        """Set filter and sort criteria, then populate table.
        """
        self.coursemodel.setFilter(f'{self.filter_field} = "{filter_value}"')
        self.coursemodel.setSort(self.coursemodel.fieldIndex(
                "SUBJECT" if self.filter_field == "CLASS" else "CLASS"
            ),
            Qt.AscendingOrder
        )
        #print("SELECT:", self.coursemodel.selectStatement())
        self.coursemodel.select()

        # Set up the view
        self.coursetable.setModel(self.coursemodel)
        selection_model = self.coursetable.selectionModel()
        selection_model.currentChanged.connect(self.course_changed)
#?
#        selection_model.reset()
#?
        self.coursetable.selectRow(0)

        self.coursetable.resizeColumnsToContents()


    def course_changed(self, new, old):
        row = new.row()
        #print("CURRENT", old.row(), "->", row)
        record = self.coursemodel.record(row)
        for f, t in COURSE_COLS:
            self.editors[f].setText(str(record.value(f)))
        self.form_change_set = set()
        self.form_modified("", False)   # initialize form button states

#TODO ...
    def course_delete(self):
        """Delete the current course.
        """
        if self.form_change_set:
            if not YesOrNoDialog(_LOSE_CHANGES):
                return
        print("§§§ DELETE COURSE:", self.editors["course"].text())

#TODO ...
    def course_add(self):
        """Add the data in the form editor as a new course.
        """
        vals = {
            f: self.editors[f].text()
            for f, t in COURSE_COLS
        }
        vals["course"] = None
        print("§§§ ADD NEW COURSE:", vals)

#TODO ...
    def course_update(self):
        """Update the current course with the data in the form editor.
        """
        changes = {
            f: self.editors[f].text()
            for f in self.form_change_set
        }
        print("§§§ UPDATE COURSE:", changes)
        return

#TODO: Get data (to restore in case of failure)
# Would an "altered" indicator be possible? E.g. enable buttons only when
# relevant?
# What about a brake on selction changing if there are uncommitted changes?
# That would probably be easier if not using the mapper ...
        if not self.mapper.submit():
            if "UNIQUE" in QSqlQueryModel.lastError(self.coursemodel).databaseText():
                REPORT("ERROR", "Der geänderte „Kurs“ existiert schon")
            else:
                REPORT("ERROR", QSqlQueryModel.lastError(self.coursemodel).text())
            self.coursemodel.revertAll()


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
    """A specialized line editor for use in the course editor form.
    """
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
    """Return a list of (key, value) pairs from the given database table.
    """
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
    """A specialized combobox for use in the course editor form.
    """
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
        """Return the current "key".
        """
        return self.keylist[self.currentIndex()]

    def setText(self, text):
        """<text> is the "key".
        """
        try:
            i = self.key2i[text]
        except KeyError:
            raise Bug(f"Unknown key for editor field {self.field}: {key}")
        self.setCurrentIndex(i)
        self.text0 = text

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
        #print("!!!2", error.text())

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

    query.prepare("insert into CLASSES values (?, ?, ?)")
    query.addBindValue(classes)
    query.addBindValue(names)
    query.addBindValue(classrooms)
    if not query.execBatch():
        error = query.lastError()
        print("!!!", error.databaseText())
        #print("!!!2", error.text())


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
#    enter_classes()
#    quit(0)

    """
    from core.teachers import Teachers
    teachers = Teachers()
    lines = []
    for tid in teachers.list_teachers():
        lines.append(f"{tid}\t{teachers.name(tid)}\t{teachers[tid]['SORTNAME']}")
    print("\n ...", len(lines))

    outdir = DATAPATH("testing/tmp")
    tsvfile = os.path.join(outdir, f"teachers.tsv")
    with open(tsvfile, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    quit(0)
    """

    """
    from core.courses import Subjects

    data = {}
    def read_class_data(klass):
        lines = subjects.class_subjects(klass)
        if klass == "XX":
            klass = ""
        for line in lines:
            sid = line["SID"]
            try:
                sid0, x = sid.split("+")
                klass0 = f"{klass}+{x}"
            except:
                sid0 = sid
                klass0 = klass

            group = line["GROUP"]
            for tid in line["TIDS"].split():
                key = (klass0, group, sid0, tid)
#                print(key)
                try:
                    keydata = data[key]
                    print("REPEAT:", keydata)
                    if keydata["COMPOSITE"] or keydata["SGROUP"]:
                        if line["COMPOSITE"] or line["SGROUP"]:
                            print(" ... Conflict:", line)
                            continue
                except KeyError:
                    pass
                data[key] = line

    subjects = Subjects()
    __classes = []
    for k in subjects.classes():
        if k.startswith("XX"):
            read_class_data(k)
        else:
            __classes.append(k)
    for k in __classes:
        read_class_data(k)

    i = 0
    courses = []
    lessons = []
    for key, line in data.items():
        i += 1
        i_s = str(i)
        dbline = (i_s,) + key + (line["SGROUP"], "", line["COMPOSITE"])
        print("§:", dbline)
        courses.append("\t".join(dbline))
        for l in line["LENGTHS"].split():
            dbxline = (i_s, l, "", line["TAG"], line["ROOMS"])
            print("      --", dbxline)
            lessons.append("\t".join(dbxline))

    outdir = DATAPATH("testing/tmp")
    cfile = os.path.join(outdir, f"courses.tsv")
    with open(cfile, "w", encoding="utf-8") as fh:
        fh.write("\n".join(courses))

    lfile = os.path.join(outdir, f"lessons.tsv")
    with open(lfile, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lessons))
    """

#    dbc = _CourseEditor()

#    quit(0)

    window = CourseEditor()
    window.setWindowTitle("Edit Courses")

    window.show()

    theader1 = window.coursetable.horizontalHeader()
    theader2 = window.lessontable.horizontalHeader()
    print("§§§1", theader1.length(), theader2.length())
    window.coursetable.resizeColumnsToContents()
    window.lessontable.resizeColumnsToContents()
    l1 = theader1.length()
    l2 = theader2.length()
    theader2.setStretchLastSection(True)
    print("§§§2", l1, l2)
    window.setSizes((l1,l2+10))
    window.resize(l1+l2 + 60,550)
    app.exec()

    quit(0)



    # This seems to deactivate activate-on-single-click
    # (presumably elsewhere as well?)
    #    app.setStyleSheet("QAbstractItemView { activate-on-singleclick: 0; }")
    def is_modified1(mod):
        print("MODIFIED1:", mod)

    def is_modified2(mod):
        print("MODIFIED2:", mod)

    def validate(value):
        if value == "v":
            return "invalid value"
        return None

    window = QSplitter()
    window.setChildrenCollapsible(False)

    cols = ["id", "Klasse", "Fach", "Gruppe", "Lehrkräfte",
            "Sammelfach", "Zeugnis", "Noten"]
    cols2 = ["Länge", "Deputat", "Kennung", "Raum", "Bedingungen"]
    rows = ["Row %02d" % n for n in range(7)]
    tablewidget = RowEditTable(cols)

    tablewidget.setRowCount(25)

    tablewidget2 = RowEditTable(cols2)
    tablewidget2.setRowCount(5)

    window.addWidget(tablewidget)
    window.addWidget(tablewidget2)
    window.setWindowTitle("Edit Courses")

    window.show()
    theader1 = tablewidget.horizontalHeader()
    theader2 = tablewidget2.horizontalHeader()
    print("§§§1", theader1.length(), theader2.length())
    tablewidget.resizeColumnsToContents()
    tablewidget2.resizeColumnsToContents()
    l1 = theader1.length()
    l2 = theader2.length()
    print("§§§2", l1, l2)
    window.setSizes((l1,l2))
    window.resize(l1+l2 + 50,500)
    app.exec()

    quit(0)

    # setItemDelegate doesn't take ownership of the custom delegates,
    # so I retain references (otherwise there will be a segfault).
    idel1 = VerticalTextDelegate()
    #    idel2 = MyDelegate()
    tablewidget.setItemDelegateForRow(2, idel1)
    #    tablewidget.setItemDelegateForRow(1, idel2)

    sparse_data = []
    r, c = 2, 3
    sparse_data.append((r, c, "R%02d:C%02d" % (r, c)))
    r, c = 1, 4
    sparse_data.append((r, c, "R%02d:C%02d" % (r, c)))
    tablewidget.init_sparse_data(len(rows), len(cols), sparse_data)

    tablewidget.resizeRowToContents(1)
    tablewidget.resizeRowToContents(2)
    tablewidget.resizeColumnToContents(3)
    tablewidget.resize(600, 400)
    tablewidget.show()

    tw2 = EdiTableWidget()
    tw2.setup(
        undo_redo=True,
        cut=True,
        paste=True,
        row_add_del=True,
        column_add_del=True,
        on_changed=is_modified2,
    )
    tw2.init_data([["1", "2", "3", "4"], [""] * 4])
    tw2.item(1, 0).set_validator(validate)
    tw2.resize(400, 300)
    tw2.show()

    app.exec()
