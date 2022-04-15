"""
ui/course_editor_widget.py

Last updated:  2022-04-12

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


### Labels
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

from ui.ui_base import HLine

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
    QSqlTableModel,
    QSqlRelationalTableModel,
    QSqlRelation,
    QSqlRelationalDelegate
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


class CourseEditor(QSplitter):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setChildrenCollapsible(False)
#TODO
        cols = ["Klasse", "Fach", "Gruppe", "Lehrkraft",
                "Zeugnis", "Noten", "Sammelfach"]
        cols2 = ["Länge", "Deputat", "Kennung", "Raum", "Notizen"]
        rows = ["Row %02d" % n for n in range(7)]

        self.coursetable = RowSelectTable(cols, readonly=True)
        self.coursetable = CourseTable()

        self.coursetable.setLineWidth(2)
        self.coursetable.setFrameShape(self.Box)
        self.addWidget(self.coursetable)
#TODO
#        self.coursetable.setRowCount(25)

        self.rightframe = QFrame()
        self.addWidget(self.rightframe)
        self.rightframe.setLineWidth(2)
        self.rightframe.setFrameShape(QFrame.Box)

        vbox2 = QVBoxLayout(self.rightframe)
        editorbox = QFrame()
        self.courseeditor = QFormLayout(editorbox)
        vbox2.addWidget(editorbox)
        self.editors = []
        for item in cols:
            editwidget = QComboBox()
            if item == "Lehrkraft":
                editwidget.addItems([f"{i:02d}" for i in range(1, 99)])
            else:
                editwidget.addItems(("First Item", "Second Item", "Third Item"))
            self.editors.append(editwidget)
            self.courseeditor.addRow(item, editwidget)

        hbox2 = QHBoxLayout()
        vbox2.addLayout(hbox2)
        hbox2.addStretch(1)
        del2 = QPushButton("Löschen")
        hbox2.addWidget(del2)
        upd2 = QPushButton("Übernehmen")
        hbox2.addWidget(upd2)
        new2 = QPushButton("Hinzufügen")
        hbox2.addWidget(new2)

        vbox2.addWidget(HLine())

        lessonbox = QFrame()
        vbox2.addWidget(lessonbox)
        vbox3 = QVBoxLayout(lessonbox)
        vbox3.setContentsMargins(0, 0, 0, 0)
        vbox3.addWidget(QLabel("<h4>Unterrichts- bzw. Deputatsstunden</h4>"))
        self.lessontable = RowSelectTable(cols2)
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


class CourseTable(QTableView):
    """A table which is editable on a row basis. It has column headers,
    but no row headers.
    The column headers can have display texts which
    differ from the internal data field names.
    """
    cols = [
        ("course", "KursNr"),
        ("CLASS", "Klasse"),
        ("GRP", "Gruppe"),
        ("SUBJECT", "Fach"),
        ("TEACHER", "Lehrkraft"),
        ("REPORT", "Zeugnis"),
        ("GRADE", "Note"),
        ("COMPOSITE", "Sammelfach")
    ]

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setSelectionMode(self.SingleSelection)
        self.setSelectionBehavior(self.SelectRows)
        self.setEditTriggers(self.NoEditTriggers)   # non-editable
        self.verticalHeader().hide()

# The following stuff should perhaps be in a separate method to allow
# a change of database.

        con = QSqlDatabase.database()
        # Set up the model
        self.model = QSqlRelationalTableModel()
        self.model.setTable("COURSES")
#?
#        self.model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.model.setEditStrategy(QSqlTableModel.OnFieldChange)

        for f, t in self.cols:
            i = self.model.fieldIndex(f)
            if f == "SUBJECT":
                self.model.setRelation(i, QSqlRelation("SUBJECTS", "SID", "NAME"))
            elif f == "TEACHER":
                self.model.setRelation(i, QSqlRelation("TEACHERS", "TID", "NAME"))
            self.model.setHeaderData(i, Qt.Horizontal, t)

#TODO: set filter and sort condition ...?
        self.model.select()

        # Set up the view
        self.setModel(self.model)
        selection_model = self.selectionModel()
        selection_model.currentChanged.connect(self.changed)
#?
#        selection_model.reset()
#?
#        self.selectRow(0)

        self.resizeColumnsToContents()

    def changed(self, new, old):
        print("CURRENT", old.row(), "->", new.row())
        record = self.model.record(new.row())
        vals = [str(record.value(f)) for f, t in self.cols]
        print("    ::", ", ".join(vals))
#


# see QDataWidgetMapper for record editing widget?


class _CourseEditor(QSplitter):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setChildrenCollapsible(False)

        dbpath = DATAPATH("db1.sqlite")
        con = QSqlDatabase.addDatabase("QSQLITE")
        con.setDatabaseName(dbpath)
        if not con.open():
            raise Bug(f"Cannot open database at {dbpath}")
        print("TABLES:", con.tables())
#        con.close()

        self.coursetable = QTableView()
        self.coursetable.setSelectionMode(QTableView.SingleSelection)
        self.coursetable.setSelectionBehavior(QTableView.SelectRows)
        self.coursetable.setEditTriggers(QTableView.NoEditTriggers)   # non-editable
        self.coursetable.verticalHeader().hide()
        self.coursetable.setLineWidth(2)
        self.coursetable.setFrameShape(self.Box)
        self.addWidget(self.coursetable)

        self.rightframe = QFrame()
        self.addWidget(self.rightframe)
        self.rightframe.setLineWidth(2)
        self.rightframe.setFrameShape(QFrame.Box)

        vbox2 = QVBoxLayout(self.rightframe)
        editorbox = QFrame()
        self.courseeditor = QFormLayout(editorbox)
        vbox2.addWidget(editorbox)
        self.editors = []
        for f, t in COURSE_COLS:
            if f == "course":
                editwidget = QLineEdit()
                editwidget.setReadOnly(True)
            elif f == "SUBJECT":
                editwidget = QComboBox()
                editwidget.currentIndexChanged.connect(self.change_subject)
            elif f == "TEACHER":
                editwidget = QComboBox()
                editwidget.currentIndexChanged.connect(self.change_teacher)
            else:
                editwidget = QLineEdit()
            self.editors.append(editwidget)
            self.courseeditor.addRow(t, editwidget)

        hbox2 = QHBoxLayout()
        vbox2.addLayout(hbox2)
        hbox2.addStretch(1)
        del2 = QPushButton("Löschen")
        hbox2.addWidget(del2)
        upd2 = QPushButton("Übernehmen")
        upd2.clicked.connect(self.course_update)
        hbox2.addWidget(upd2)
        new2 = QPushButton("Hinzufügen")
        hbox2.addWidget(new2)

        vbox2.addWidget(HLine())

        lessonbox = QFrame()
        vbox2.addWidget(lessonbox)
        vbox3 = QVBoxLayout(lessonbox)
        vbox3.setContentsMargins(0, 0, 0, 0)
        vbox3.addWidget(QLabel("<h4>Unterrichts- bzw. Deputatsstunden</h4>"))
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

        self.init_data()

    def change_subject(self, i):
        print("$$$s", self.subject_model.record(i).value("SID"))

    def change_teacher(self, i):
        print("$$$t", self.teacher_model.record(i).value("TID"))

    def init_data(self):
        con = QSqlDatabase.database()
        # Set up the model
        self.coursemodel = QSqlRelationalTableModel()
        self.coursemodel.setTable("COURSES")
#?
#        self.coursemodel.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.coursemodel.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.mapper = QDataWidgetMapper()
        self.mapper.setModel(self.coursemodel)
        self.mapper.setItemDelegate(QSqlRelationalDelegate())
        self.mapper.setSubmitPolicy(QDataWidgetMapper.ManualSubmit)
#        self.mapper.setSubmitPolicy(QDataWidgetMapper.AutoSubmit)
        n = 0
        for f, t in COURSE_COLS:
            i = self.coursemodel.fieldIndex(f)
            editwidget = self.editors[n]
            if f == "SUBJECT":
                relation = QSqlRelation("SUBJECTS", "SID", "NAME")
                self.coursemodel.setRelation(i, relation)
                self.subject_model = self.coursemodel.relationModel(i)
                editwidget.setModel(self.subject_model)
                editwidget.setModelColumn(self.subject_model.fieldIndex("NAME"))
            elif f == "TEACHER":
                relation = QSqlRelation("TEACHERS", "TID", "NAME")
                self.coursemodel.setRelation(i, relation)
                self.teacher_model = self.coursemodel.relationModel(i)
                editwidget.setModel(self.teacher_model)
                editwidget.setModelColumn(self.teacher_model.fieldIndex("NAME"))
            self.coursemodel.setHeaderData(i, Qt.Horizontal, t)
            n += 1
            self.mapper.addMapping(editwidget, i)

# A possible problem with the mapper is that if a submit fails, all the
# data will be reverted. It might be better to have a form that retains the
# erroneous values ... at least until the main selection changes.

#TODO: set filter and sort condition ...?
        self.coursemodel.select()

        # Set up the view
        self.coursetable.setModel(self.coursemodel)
        selection_model = self.coursetable.selectionModel()
        selection_model.currentChanged.connect(self.course_changed)
#?
#        selection_model.reset()
#?
#        self.coursetable.selectRow(0)

        self.coursetable.resizeColumnsToContents()

    def course_changed(self, new, old):
        row = new.row()
        print("CURRENT", old.row(), "->", row)
        record = self.coursemodel.record(row)
        vals = [str(record.value(i)) for i in range(record.count())]
#        vals = [str(record.value(f)) for f, t in COURSE_COLS]
        print("    ::", ", ".join(vals))
        for i in range(record.count()):
            print("  +", record.fieldName(i))
        self.mapper.setCurrentIndex(row)

    def course_update(self):
        """Clicked _COURSE_UPDATE button.
        """
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


# What about something like this?:
class CourseModel(QSqlTableModel):
    def data(self, index, role):
        val0 = super().data(index, role)
        if role == Qt.DisplayRole:
            return "Get from foreign key table with f(val0)"
        return val0
# But I guess there would still be the problem of getting the
# untransformed values. Would setting a (styled)itemdelegate on the
# affected columns be more appropriate?

class ForeignKeyItemDelegate(QStyledItemDelegate):
    def displayText(self, value, locale):
        val0 = super().displayText(value, locale)
        return f(val0) # would just using value.toString() be good enough?

# Then ...
# delegate = ForeignKeyItemDelegate()
# table_view.setItemDelegateForColumn(int_column1, delegate)
# table_view.setItemDelegateForColumn(int_column2, delegate)

# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":

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

    window = _CourseEditor()
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
