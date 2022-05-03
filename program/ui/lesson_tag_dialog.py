"""
ui/lesson_tag_dialog.py

Last updated:  2022-05-03

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
    QComboBox,
    QCheckBox,
    QValidator,



    HLine,
    LoseChangesDialog,
    KeySelector,
    #RowSelectTable,
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

class BlocknameValidator(QValidator):
    def validate(self, text, pos):
        print("VALIDATE:", pos, text)
        if text.startswith("+"):
            return (QValidator.State.Invalid, text, pos)
        if text.endswith("+"):
            return (QValidator.State.Intermediate, text, pos)
        return (QValidator.State.Acceptable, text, pos)


class EditableComboBox(QComboBox):
    def __init__(self):
        super().__init__(editable=True)

    def focusOutEvent(self, e):
        """Close the editor when focus leaves it. This reverts any
        partially entered text.
        """
        self.clearEditText()
        self.setCurrentIndex(self.currentIndex())


class LessonTagDialog(QDialog):
    def __init__(self):
        super().__init__()
        vbox0 = QVBoxLayout(self)

        hbox0 =QHBoxLayout()
        vbox0.addLayout(hbox0)
        self.blockmember = QCheckBox("Blockmitglied")
        hbox0.addWidget(self.blockmember)
        hbox0.addStretch(1)
        hbox0.addWidget(QLabel("Kennzeichen:"))
# It might be preferable to use a non-editable combobox with a separate
# button+popup (or whatever) to add a new identifier.
        self.identifier = EditableComboBox()
        self.identifier.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        #self.identifier.setInsertPolicy(QComboBox.InsertPolicy.InsertAtTop)
        # Alphabetical insertion doesn't apply to the items added programmatically
        self.identifier.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
        self.identifier.addItems(("10Gzwe", "Short", "Extremely_long_identifier"))
        self.identifier.setItemData(0, "First item", Qt.ToolTipRole)
        self.identifier.setItemData(1, "A rather longer tooltip,\n very rambly actually ...", Qt.ToolTipRole)
        bn_validator = BlocknameValidator()
        self.identifier.setValidator(bn_validator)
        self.identifier.currentIndexChanged.connect(self.index_changed)
        self.identifier.currentTextChanged.connect(self.text_changed)
        self.identifier.activated.connect(self.activated_index)
        self.identifier.textActivated.connect(self.text_activated)

        hbox0.addWidget(self.identifier)

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

    def index_changed(self, i):
        # called only after editing, but may be called twice then
        print("NEW INDEX:", i)

    def activated_index(self, i):
        # This seems the best for registering changes.
        # However, incomplete edits can still hang around ...
        print("ACTIVATED:", i)

    def text_changed(self, text):
        # called every time a character is edited ...
        print("NEW TEXT:", text)

    def text_activated(self, text):
        # Seems just like activated_index, but passes text
        print("ACTIVATED TEXT:", text)




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


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    open_database()

    from ui.ui_base import run

    widget = LessonTagDialog()
    widget.resize(1000, 550)
    widget.exec()
#    run(widget)
