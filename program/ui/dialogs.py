"""
ui/dialogs.py

Last updated:  2022-05-15

Dialogs for various editing purposes


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
    import sys, os

    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start
    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    #    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))

#T = TRANSLATIONS("ui.dialogs")
T = TRANSLATIONS("ui.modules.course_lessons")

### +++++

from typing import NamedTuple

from core.db_management import (
    open_database,
    db_read_table,
    db_read_full_table,
    db_key_value_list,
    db_values
)

#from core.classes import get_class_list

from ui.ui_base import (
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QListWidget,
    QAbstractItemView,
    QComboBox,
    QCheckBox,
    QValidator,
    QDialogButtonBox,
    QLayout,



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

#?
class BlocknameValidator(QValidator):
    def validate(self, text, pos):
        print("VALIDATE:", pos, text)
        if text.startswith("+"):
            return (QValidator.State.Invalid, text, pos)
        if text.endswith("+"):
            return (QValidator.State.Intermediate, text, pos)
        return (QValidator.State.Acceptable, text, pos)


class EditableComboBox(QComboBox):
    def __init__(self, parent=None, changed_callback=None, sort=True):
        """<changed_callback> takes a single parameter, the new text.
        <sort> selects alphabetical sorting (ascending) of manually
        added entries (not those added in the program).
        """
        self.__changed = changed_callback
        super().__init__(parent=parent, editable=True)
        self.__item = None
        if sort:
            self.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
        self.currentIndexChanged.connect(self.index_changed)

    def focusOutEvent(self, e):
        """Close the editor when focus leaves it. This reverts any
        partially entered text.
        """
        self.clearEditText()
        self.setCurrentIndex(self.currentIndex())

    def index_changed(self, i):
        # This can be called twice on a change because of sorting
        t = self.currentText()
        if t != self.__item:
            self.__item = t
            if self.__changed:
                self.__changed(t)


class DayPeriodDialog(QDialog):
    def timeslot2index(self, timeslot):
        """Convert a "timeslot" in the tag-form (e.g. "Mo.3") to a pair
        of 0-based indexes.
        """
        i, j = -1, -1
        if timeslot and timeslot != "?":
            e = False
            try:
                d, p = timeslot.split(".")
            except ValueError:
                e = True
            else:
                n = 0
                for day in self.DAYS:
                    if day[0] == d:
                        i = n
                        break
                    n += 1
                else:
                    e = True
                n = 0
                for period in self.PERIODS:
                    if period[0] == p:
                        j = n
                        break
                    n += 1
                else:
                    e = True
            if e:
                SHOW_ERROR(f"Bug: invalid day.period: {timeslot}")
                return -1, 0
        return i, j

    def index2timeslot(self, index):
        """Convert a pair of 0-based indexes to a "timeslot" in the
        tag-form (e.g. "Mo.3").
        """
        d = self.DAYS[index[0]][0]
        p = self.PERIODS[index[1]][0]
        return f"{d}.{p}"

    def __init__(self):
        super().__init__()
        vbox0 = QVBoxLayout(self)
        vbox0.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        hbox1 = QHBoxLayout()
        vbox0.addLayout(hbox1)
        self.daylist = ListWidget()
#        self.daylist.setMinimumWidth(30)
        self.daylist.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.daylist.currentRowChanged.connect(self.select_day)
        hbox1.addWidget(self.daylist)

        self.periodlist = ListWidget()
#        self.daylist.setMinimumWidth(30)
        self.periodlist.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.periodlist.currentRowChanged.connect(self.select_period)
        hbox1.addWidget(self.periodlist)


        """
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
        """



        buttonBox = QDialogButtonBox()
        vbox0.addWidget(buttonBox)
        bt_save = buttonBox.addButton(QDialogButtonBox.StandardButton.Save)
        bt_cancel = buttonBox.addButton(QDialogButtonBox.StandardButton.Cancel)
        bt_clear = buttonBox.addButton(QDialogButtonBox.StandardButton.Discard)
        #hbox1.addStretch(1)

        bt_save.clicked.connect(self.do_accept)
        bt_cancel.clicked.connect(self.reject)
        bt_clear.clicked.connect(self.do_clear)

    def do_accept(self):
        d = self.daylist.currentRow()
        p = self.periodlist.currentRow()
        self.result = self.index2timeslot((d, p))
        self.accept()

    def do_clear(self):
        self.result = "?"
        self.accept()

    def init(self):
        self.DAYS = db_key_value_list("TT_DAYS", "TAG", "NAME", "N")
        self.daylist.clear()
        self.daylist.addItems([d[1] for d in self.DAYS])
        self.PERIODS = db_key_value_list("TT_PERIODS", "TAG", "NAME", "N")
        self.periodlist.clear()
        self.periodlist.addItems([p[1] for p in self.PERIODS])

    def activate(self, start_value=None):
        d, p = self.timeslot2index(start_value)
        self.result = None
        if d < 0:
            if p == 0:
                # error
                self.result = "?"
            else:
                p = 0
            d = 0
        self.daylist.setCurrentRow(d)
        self.periodlist.setCurrentRow(p)
        self.exec()
        return self.result

    def select_day(self, day):
        print("SELECT DAY:", day)

    def select_period(self, period):
        print("SELECT CLASS:", period)

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


class CourseKeyFields(NamedTuple):
    CLASS: str
    GRP: str
    SUBJECT: str
    TEACHER: str
#+
def get_course_info(course):
    flist, clist = db_read_table(
        "COURSES",
        CourseKeyFields._fields,
        course=course
    )
    if len(clist) > 1:
        raise Bug(f"COURSE {course}: multiple entries")
# Perhaps not found is an error?
    return CourseKeyFields(*clist[0]) if clist else None

class Parallel(NamedTuple):
    id: int
    course: int  # When the field is null this gets set to an empy string
    TIME: str
    PLACE: str
#+
def parallels(tag):
    flist, plist = db_read_table(
        "LESSONS",
        Parallel._fields,
        TIME=tag
    )
    return [Parallel(*p) for p in plist]
#+
def placements(tag):
    flist, plist = db_read_table(
        "LESSONS",
        Parallel._fields,
        PLACE=tag
    )
    pl = []
    for p in plist:
        pp = Parallel(*p)
        if pp.course:
            SHOW_ERROR(f"Bug: invalid placement (course={pp.course})")
        else:
            pl.append(pp)
    return pl


#TODO
class ParallelsDialog(QDialog):
# Could enable the save button only when it is different from the initial value
# Could enable the clear/reset button only when there was an initial value
    def __init__(self):
        super().__init__()
        vbox0 = QVBoxLayout(self)

        hbox1 = QHBoxLayout()
        vbox0.addLayout(hbox1)

        vbox1 = QVBoxLayout()
        hbox1.addLayout(vbox1)
        self.identifier = EditableComboBox(changed_callback=self.tag_changed)
        vbox1.addWidget(self.identifier)

        self.identifier.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
#        bn_validator = BlocknameValidator()
#        self.identifier.setValidator(bn_validator)

        self.course_list = ListWidget()
        hbox1.addWidget(self.course_list)


        buttonBox = QDialogButtonBox()
        buttonBox.setOrientation(Qt.Orientation.Vertical)
        vbox1.addWidget(buttonBox)
        bt_save = buttonBox.addButton(QDialogButtonBox.StandardButton.Save)
        bt_cancel = buttonBox.addButton(QDialogButtonBox.StandardButton.Cancel)
        bt_clear = buttonBox.addButton(QDialogButtonBox.StandardButton.Discard)
        #hbox1.addStretch(1)

#        bt_save.clicked.connect(self.do_accept)
#        bt_cancel.clicked.connect(self.reject)
#        bt_clear.clicked.connect(self.do_clear)


    def tag_changed(self, text):
        tag = "=" + text
        print("NEW TEXT:", tag)
        # Populate the list widget with all courses sharing the new tag.
        # Including the currently selected one (which we can't identify here!)?
#        plist = parallels(tag)
        plist = parallels(text) # just for testing!
        self.course_list.clear()
        dlist = []
        for p in plist:
            if p.course:
                # Present info about the course
                dlist.append(str(get_course_info(p.course)))

            else:
                # This is a block lesson
                dlist.append(f"[BLOCK] {p.PLACE}")

#        self.course_list.addItems([str(p) for p in plist])
        self.course_list.addItems(dlist)

#TODO: Probably needs to be at start of activate, because of dynamic nature of items
    def init(self):
        self.identifier.clear()

        taglist = db_values(
            "LESSONS",
            "TIME",
#            "TIME LIKE '=_%'",   ... actually, this is what I need here
            "TIME NOT LIKE '>%'", # just testing ...
            distinct=True,
            sort_field="TIME"
        )

        self.identifier.addItems(taglist)

#TODO
    def activate(self, start_value=None):
#        d, p = self.timeslot2index(start_value)
        self.result = None
#        if d < 0:
#            if p == 0:
#                # error
#                self.result = "?"
#            else:
#                p = 0
#            d = 0
#        self.daylist.setCurrentRow(d)
#        self.periodlist.setCurrentRow(p)
        self.exec()
        return self.result

# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    open_database()

    for p in placements(">ZwE#09G10G"):
        print("!!!!", p)

    for p in parallels("sp03"):
        print("??????", p)

#    quit(0)

#    from ui.ui_base import run

    widget = ParallelsDialog()
    widget.init()
    print("----->", widget.activate())

    quit(0)

    widget = DayPeriodDialog()
    widget.init()
#    widget.resize(1000, 550)
#    widget.exec()

    print("----->", widget.activate("?"))
    print("----->", widget.activate("Di.4"))
    print("----->", widget.activate("Di.9"))

#    run(widget)
