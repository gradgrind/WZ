"""
ui/dialogs.py

Last updated:  2022-05-17

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
    db_key_value_list,
    db_values
)

#from core.classes import get_class_list

from ui.ui_base import (
    HLine,

    ### QtWidgets:
    APP,
    QStyle,
    QDialog,
    QListWidget,
    QAbstractItemView,
    QComboBox,
    QDialogButtonBox,
    QLayout,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QToolButton,
    ### QtGui:
    QValidator,
    ### QtCore:
    Qt,
    QSize,
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

# This can still be useful as an example, even though I am not using it here!
class BlocknameValidator(QValidator):
    def validate(self, text, pos):
        print("VALIDATE:", pos, text)
        if text.startswith("+"):
            return (QValidator.State.Invalid, text, pos)
        if text.endswith("+"):
            return (QValidator.State.Intermediate, text, pos)
        return (QValidator.State.Acceptable, text, pos)


# This can still be useful, even though I am not using it here!
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


class ListWidget(QListWidget):
    def sizeHint(self):
        s = QSize()
        s.setHeight(super().sizeHint().height())
        scrollbarwidth = APP.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        # The scroll-bar width alone is not quite enough ...
        s.setWidth(self.sizeHintForColumn(0) + scrollbarwidth + 5)
        print("???", s, scrollbarwidth)
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


class ParallelsDialog(QDialog):
#TODO
# Could enable the save button only when it is different from the initial value
# Could enable the clear/reset button only when there was an initial value
    def __init__(self):
        super().__init__()
        hbox1 = QHBoxLayout(self)

        vbox1 = QVBoxLayout()
        hbox1.addLayout(vbox1)
        self.identifier = QComboBox(editable=True)
        self.identifier.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.identifier.currentTextChanged.connect(self.show_courses)
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
        #vbox1.addStretch(1)

        bt_save.clicked.connect(self.do_accept)
        bt_cancel.clicked.connect(self.reject)
        bt_clear.clicked.connect(self.do_clear)

    def do_accept(self):
        val = self.identifier.currentText()
#TODO
# Bear in mind that I still need to deal with the "=" prefixes ...
        if val != self.value0:
            self.result = val
        if self.identifier.findText(val) < 0:
             self.result = "+" + val
        self.accept()

    def do_clear(self):
        if self.value0:
            self.result = "-"
        self.accept()

    def show_courses(self, text):
        tag = "=" + text
        self.course_list.clear()
        #print("NEW TEXT:", tag)
        # Populate the list widget with all courses sharing the new tag.
        # Including the currently selected one (which we can't identify here!)?
#TODO
#        plist = parallels(tag)
        plist = parallels(text) # just for testing!

        dlist = []
        for p in plist:
            if p.course:
                # Present info about the course
                ci = get_course_info(p.course)
                #dlist.append(str(ci))
                dlist.append(f"{ci.CLASS}.{ci.GRP}: {ci.SUBJECT} ({ci.TEACHER})")

            else:
                # This is a block lesson
                dlist.append(f"[BLOCK] {p.PLACE}")
        self.course_list.addItems(dlist)

    def activate(self, start_value=None):
        self.value0 = start_value or ""
        self.result = None
        self.identifier.clear()
        taglist = db_values(
            "LESSONS",
            "TIME",
#TODO
#            "TIME LIKE '=_%'",   ... actually, this is what I need here
            "TIME NOT LIKE '>%'", # just testing ...
            distinct=True,
            sort_field="TIME"
        )
        self.identifier.addItems(taglist)
        if self.value0:
            self.identifier.setCurrentText(self.value0)
        else:
# Actually there shouldn't be any with no tag!
            self.show_courses(self.value0)
        self.exec()
        return self.result


# Possibly completely without display line? If I need to copy/paste
# an entry, I could suppl copy and paste buttons (or "actions").
class RoomDialog(QDialog):
    def __init__(self):
        super().__init__()
        vbox0 = QVBoxLayout(self)
        hbox1 = QHBoxLayout()
        vbox0.addLayout(hbox1)
        vboxl = QVBoxLayout()
        hbox1.addLayout(vboxl)

        self.roomchoice = QTableWidget()
        self.roomchoice.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.roomchoice.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.roomchoice.setSelectionBehavior(QAbstractItemView.SelectRows)
        vboxl.addWidget(self.roomchoice)

#TODO: Add buttons for: up, down, add, remove
        vboxm = QVBoxLayout()
        hbox1.addLayout(vboxm)

        bt_up = QToolButton()
        bt_up.setToolTip("Move up")
        vboxm.addWidget(bt_up)
        bt_up.setArrowType(Qt.ArrowType.UpArrow)
##        bt_up.setAutoRaise(True)
##        bt_up.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
#        bt_up.clicked.connect(???)
        bt_down = QToolButton()
        bt_down.setToolTip("Move down")
        vboxm.addWidget(bt_down)
        bt_down.setArrowType(Qt.ArrowType.DownArrow)
#        bt_down.clicked.connect(???)

        vboxm.addStretch(1)
        bt_left = QToolButton()
        vboxm.addWidget(bt_left)
        bt_left.setArrowType(Qt.ArrowType.LeftArrow)
#T
        bt_left.setToolTip("Add to choices")
        bt_left.clicked.connect(self.add2choices)
        bt_right = QToolButton()
        vboxm.addWidget(bt_right)
        bt_right.setIcon(self.style().standardIcon(
            QStyle.StandardPixmap.SP_DialogDiscardButton))
#        bt_right.setArrowType(Qt.ArrowType.RightArrow)
#T
        bt_right.setToolTip("Remove from choices")
        bt_right.clicked.connect(self.discard_choice)
        vboxm.addStretch(1)

        vboxr = QVBoxLayout()
        hbox1.addLayout(vboxr)

        self.roomlist = QTableWidget()
        self.roomlist.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.roomlist.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.roomlist.setSelectionBehavior(QAbstractItemView.SelectRows)
        #self.roomlist.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        vboxr.addWidget(self.roomlist)


        self.roomtext = QLineEdit()
        self.roomtext.textEdited.connect(self.text_changed)
        vboxl.addWidget(self.roomtext)

#        bn_validator = BlocknameValidator()
#        self.roomtext.setValidator(bn_validator)

        self.home = QCheckBox("CLASSROOM")
        vboxl.addWidget(self.home)
        self.extra = QCheckBox("OTHERS")
        vboxl.addWidget(self.extra)

        #vboxl.addSpacing(100)
        #vboxl.addStretch(1)

        #hbox2 = QHBoxLayout()
        #vboxl.addLayout(hbox2)
        #hbox2.addStretch(1)

        vbox0.addWidget(HLine())
        buttonBox = QDialogButtonBox()
        #buttonBox.setOrientation(Qt.Orientation.Vertical)
        vbox0.addWidget(buttonBox)
        bt_save = buttonBox.addButton(QDialogButtonBox.StandardButton.Save)
        bt_cancel = buttonBox.addButton(QDialogButtonBox.StandardButton.Cancel)
        bt_clear = buttonBox.addButton(QDialogButtonBox.StandardButton.Discard)

        bt_save.clicked.connect(self.do_accept)
        bt_cancel.clicked.connect(self.reject)
        bt_clear.clicked.connect(self.do_clear)

    def text_changed(self, text):
        rooms = text.split("/")
        print("§ -->", rooms)

    def add2choices(self):
        row = self.roomlist.currentRow()
        riditem = self.roomlist.item(row, 0)
        rid = riditem.text()
#?
        if rid == self.classroom:
            rid = '$'
        if rid not in self.choices:
            ri = len(self.choices)
            self.roomchoice.insertRow(ri)
            self.roomchoice.setItem(ri, 0, riditem.clone())
            self.roomchoice.setItem(ri, 1, self.roomlist.item(row, 1).clone())
            self.roomchoice.resizeColumnsToContents()
            self.roomchoice.selectRow(ri)
            self.choices.append(rid)
            self.write_choices()

    def discard_choice(self):
        row = self.roomchoice.currentRow()
        self.roomchoice.removeRow(row)
        del(self.choices[row])
        self.write_choices()

    def write_choices(self):
        self.roomtext.setText("/".join(self.choices))

    def do_accept(self):
        print("ACCEPT")
        return

        val = self.identifier.currentText()
#TODO
        if val != self.value0:
            self.result = val
        if self.identifier.findText(val) < 0:
             self.result = "+" + val
        self.accept()

    def do_clear(self):
        print("CLEAR")
        return
        if self.value0:
            self.result = "-"
        self.accept()

    def init(self):
        self.room2line = {}
        self.rooms = db_key_value_list(
            "TT_ROOMS",
            "RID",
            "NAME",
            sort_field="RID"
        )
        n = len(self.rooms)
        self.roomlist.setRowCount(n)
        self.roomlist.setColumnCount(2)
        for i in range(n):
            rid = self.rooms[i][0]
            self.room2line[rid] = i
            item = QTableWidgetItem(rid)
            self.roomlist.setItem(i, 0, item)
            item = QTableWidgetItem(self.rooms[i][1])
            self.roomlist.setItem(i, 1, item)
        self.roomlist.resizeColumnsToContents()
        Hhd = self.roomlist.horizontalHeader()
        Hhd.hide()
        #Hhd.setMinimumSectionSize(20)
        # A rather messy attempt to find an appropriate size for the table
        Vhd = self.roomlist.verticalHeader()
        Vhd.hide()
        Hw = Hhd.length()
        #Vw = Vhd.sizeHint().width()
        fixed_width = Hw + 20   # + Vw, if vertical headers in use
        self.roomlist.setFixedWidth(fixed_width)
        self.roomchoice.setFixedWidth(fixed_width)
        Hhd.setStretchLastSection(True)
        hh = self.roomchoice.horizontalHeader()
        hh.hide()
# Check that this doesn't need toggling after a clear() ...
        hh.setStretchLastSection(True)
        self.roomchoice.verticalHeader().hide()

    def activate(self, start_value="", classroom=None):
        self.classroom = classroom
#?
        if classroom:
            self.home.show()
        else:
            self.home.hide()
#?
        if start_value.endswith("+"):
            self.extra.setCheckState(Qt.CheckState.Checked)
            start_value = start_value[:-1]
        else:
            self.extra.setCheckState(Qt.CheckState.Unchecked)

        rids = start_value.split("/")
        self.choices = []
        self.roomchoice.clear()
        self.roomchoice.setColumnCount(2)
#?
        self.home.setCheckState(Qt.CheckState.Unchecked)
        for rid in rids:
            if rid == "$":
                if not self.classroom:
#T
                    SHOW_ERROR("No classroom defined")
                    continue
                rid = self.classroom
#?
                self.home.setCheckState(Qt.CheckState.Checked)
            try:
                row = self.room2line[rid]
            except KeyError:
#T
                SHOW_ERROR(f"Unknown room id: '{rid}'")
                continue

            # see method <add2choices>
            riditem = self.roomlist.item(row, 0)
#?
            if rid in self.choices:
                SHOW_WARNING("Repeated room id discarded: '{rid}'")
                continue
            ri = len(self.choices)
            self.roomchoice.insertRow(ri)
            self.roomchoice.setItem(ri, 0, riditem.clone())
            self.roomchoice.setItem(ri, 1, self.roomlist.item(row, 1).clone())
            self.roomchoice.resizeColumnsToContents()
            self.roomchoice.selectRow(ri)
            self.choices.append(rid)
        self.write_choices()

        self.roomchoice.selectRow(0)
        self.roomlist.selectRow(0)

# Focus line edit?
        self.exec()
        return


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    open_database()

    for p in placements(">ZwE#09G10G"):
        print("!!!!", p)

    for p in parallels("sp03"):
        print("??????", p)

#    quit(0)

    widget = RoomDialog()
    widget.init()
    print("----->", widget.activate(start_value="$/rPh+", classroom="r10G"))

#    quit(0)

    widget = ParallelsDialog()
    print("----->", widget.activate("huO"))

#    quit(0)

    widget = DayPeriodDialog()
    widget.init()
#    widget.resize(1000, 550)
#    widget.exec()

    print("----->", widget.activate("?"))
    print("----->", widget.activate("Di.4"))
    print("----->", widget.activate("Di.9"))

#    run(widget)
