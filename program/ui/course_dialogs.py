"""
ui/course_dialogs.py

Last updated:  2022-06-27

Supporting "dialogs", etc., for various purposes within the course editor.


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
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    #    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))

# T = TRANSLATIONS("ui.dialogs")
T = TRANSLATIONS("ui.modules.course_lessons")

### +++++

from typing import NamedTuple

from core.db_management import (
    open_database,
    db_read_table,
    db_values,
    db_read_unique_field,
    NoRecord,
)
from core.basic_data import (
    get_days,
    get_periods,
    get_subjects,
    get_rooms,
    get_payroll_weights,
    SHARED_DATA,
    PAYROLL_FORMAT
)
from ui.ui_base import (
    GuiError,
    HLine,
    KeySelector,
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
    QCheckBox,
    QToolButton,
    QPushButton,
    QStyledItemDelegate,
    ### QtGui:
    QRegularExpressionValidator,
    ### QtCore:
    Qt,
    QSize,
    QRegularExpression,
    QTimer,
)

TAG_FORMAT = QRegularExpression("^[A-Za-z0-9_.]+$")


def set_coursedata(coursedata: dict):
    SHARED_DATA["COURSE"] = coursedata


def get_coursedata():
    return SHARED_DATA["COURSE"]


### -----


class TimeSlotError(Exception):
    pass


def timeslot2index(timeslot):
    """Convert a "timeslot" in the tag-form (e.g. "Mo.3") to a pair
    of 0-based indexes.
    """
    i, j = -1, -1
    if timeslot and timeslot != "?":
        if timeslot[0] == "?":
            # Remove "unfixed" flag
            timeslot = timeslot[1:]
        try:
            d, p = timeslot.split(".")
        except ValueError:
            raise TimeSlotError
        else:
            n = 0
            for day in get_days():
                if day[0] == d:
                    i = n
                    break
                n += 1
            else:
                raise TimeSlotError
            n = 0
            for period in get_periods():
                if period[0] == p:
                    j = n
                    break
                n += 1
            else:
                raise TimeSlotError
    return i, j


def index2timeslot(index):
    """Convert a pair of 0-based indexes to a "timeslot" in the
    tag-form (e.g. "Mo.3").
    """
    d = get_days()[index[0]][0]
    p = get_periods()[index[1]][0]
    return f"{d}.{p}"


class DayPeriodDialog(QDialog):
    @classmethod
    def popup(cls, start_value="", parent=None, pos=None):
        d = cls(parent)
        d.init()
        if pos:
            d.move(pos)
        return d.activate(start_value)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        vbox0 = QVBoxLayout(self)
        vbox0.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        hbox1 = QHBoxLayout()
        vbox0.addLayout(hbox1)
        self.daylist = ListWidget()
        #        self.daylist.setMinimumWidth(30)
        self.daylist.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        hbox1.addWidget(self.daylist)

        self.periodlist = ListWidget()
        #        self.daylist.setMinimumWidth(30)
        self.periodlist.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        hbox1.addWidget(self.periodlist)

        self.fixed_time = QCheckBox(T["TIME_FIXED"])
        vbox0.addWidget(self.fixed_time)

        buttonBox = QDialogButtonBox()
        vbox0.addWidget(buttonBox)
        bt_save = buttonBox.addButton(QDialogButtonBox.StandardButton.Save)
        bt_cancel = buttonBox.addButton(QDialogButtonBox.StandardButton.Cancel)
        bt_clear = buttonBox.addButton(QDialogButtonBox.StandardButton.Discard)

        bt_save.clicked.connect(self.do_accept)
        bt_cancel.clicked.connect(self.reject)
        bt_clear.clicked.connect(self.do_clear)

    def do_accept(self):
        d = self.daylist.currentRow()
        p = self.periodlist.currentRow()
        self.result = index2timeslot((d, p))
        if not self.fixed_time.isChecked():
            self.result = "?" + self.result
        self.accept()

    def do_clear(self):
        self.result = "?"
        self.accept()

    def init(self):
        self.daylist.clear()
        self.daylist.addItems([d[1] for d in get_days()])
        self.periodlist.clear()
        self.periodlist.addItems([p[1] for p in get_periods()])

    def activate(self, start_value=None):
        try:
            if start_value:
                fixed = start_value == "?" or start_value[0] != "?"
            d, p = timeslot2index(start_value)
            self.result = None
            if d < 0:
                d, p = 0, 0
        except TimeSlotError:
            SHOW_ERROR(f"Bug: invalid day.period: '{start_value}'")
            self.result = "?"
            d, p, fixed = 0, 0, True
        self.daylist.setCurrentRow(d)
        self.periodlist.setCurrentRow(p)
        self.fixed_time.setChecked(fixed)
        self.exec()
        return self.result


class ListWidget(QListWidget):
    def sizeHint(self):
        s = QSize()
        s.setHeight(super().sizeHint().height())
        scrollbarwidth = APP.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        # The scroll-bar width alone is not quite enough ...
        s.setWidth(self.sizeHintForColumn(0) + scrollbarwidth + 5)
        # print("???", s, scrollbarwidth)
        return s


class CourseKeyFields(NamedTuple):
    CLASS: str
    GRP: str
    SUBJECT: str
    TEACHER: str


def get_course_info(course):
    flist, clist = db_read_table(
        "COURSES", CourseKeyFields._fields, course=course
    )
    if len(clist) > 1:
        raise Bug(f"COURSE {course}: multiple entries")
    # Perhaps not found is an error?
    return CourseKeyFields(*clist[0]) if clist else None


class Partner(NamedTuple):
    id: int
    course: int  # When the field is null this gets set to an empy string
    TIME: str
    PLACE: str


def partners(tag):
    if tag.replace(" ", "") != tag:
        SHOW_ERROR(f"Bug: Spaces in partner tag: '{tag}'")
        return []
    if not tag:
        return []
    flist, plist = db_read_table("LESSONS", Partner._fields, TIME=f"={tag}")
    return [Partner(*p) for p in plist]


def block_courses(tag):
    return db_values("LESSONS", "course", TIME=tag)


class Sublesson(NamedTuple):
    id: int
    LENGTH: str
    TIME: str


def sublessons(tag):
    if tag.replace(" ", "") != tag:
        SHOW_ERROR(f"Bug: Spaces in partner tag: '{tag}'")
        return []
    if not tag:
        return []
    flist, plist = db_read_table("LESSONS", Sublesson._fields, PLACE=f"{tag}")
    return [Sublesson(*p) for p in plist]


def placements(xtag):
    """Return a list of <Partner> tuples with the given prefixed (full)
    tag in the PLACE field.
    """
    flist, plist = db_read_table("LESSONS", Partner._fields, PLACE=xtag)
    pl = []
    for p in plist:
        pp = Partner(*p)
        if pp.course:
            SHOW_ERROR(f"Bug: invalid placement (course={pp.course})")
        else:
            pl.append(pp)
    return pl


def parse_time_field(tag):
    """Convert a lesson time-field to a (Time, Tag) pair – assuming
    the given value is a valid time slot or "partners" tag.
    """
    if tag.startswith("="):
        tag = tag[1:]
        return get_time_entry(tag), tag
    else:
        # Check validity of time
        return check_start_time(tag), ""


def get_time_entry(tag):
    try:
        ltime = db_read_unique_field("LESSONS", "TIME", PLACE=f"={tag}")
    except NoRecord:
        SHOW_ERROR(f'{T["NO_TIME_FOR_PARTNERS"]}: {tag}')
        # TODO: add a time entry?
        # TIME="?", PLACE=f"={tag}", everything else empty
        return "?"
    # Check validity
    return check_start_time(ltime)


def check_start_time(tag):
    try:
        if tag.startswith("@"):
            ltime = tag[1:]
            timeslot2index(ltime)
            return ltime
    except TimeSlotError:
        pass
    SHOW_ERROR(f"{T['BAD_TIME']}: {tag}")
    return "?"


class PartnersDialog(QDialog):
    @classmethod
    def popup(cls, start_value="", pos=None):
        d = cls()
        if pos:
            d.move(pos)
        return d.activate(start_value)

    def __init__(self):
        super().__init__()
        hbox1 = QHBoxLayout(self)

        vbox1 = QVBoxLayout()
        hbox1.addLayout(vbox1)
        self.identifier = QComboBox(editable=True)
        self.identifier.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.identifier.currentTextChanged.connect(self.show_courses)
        validator = QRegularExpressionValidator(TAG_FORMAT)
        self.identifier.setValidator(validator)
        vbox1.addWidget(self.identifier)

        self.identifier.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        #        bn_validator = BlocknameValidator()
        #        self.identifier.setValidator(bn_validator)

        self.course_list = QListWidget()
        hbox1.addWidget(self.course_list)

        buttonBox = QDialogButtonBox()
        buttonBox.setOrientation(Qt.Orientation.Vertical)
        vbox1.addWidget(buttonBox)
        self.bt_save = buttonBox.addButton(QDialogButtonBox.StandardButton.Save)
        bt_cancel = buttonBox.addButton(QDialogButtonBox.StandardButton.Cancel)
        self.bt_clear = buttonBox.addButton(
            QDialogButtonBox.StandardButton.Discard
        )
        # vbox1.addStretch(1)

        self.bt_save.clicked.connect(self.do_accept)
        bt_cancel.clicked.connect(self.reject)
        self.bt_clear.clicked.connect(self.do_clear)

    def do_accept(self):
        val = self.identifier.currentText()
        if not val:
            SHOW_ERROR(T["EMPTY_PARTNER_TAG"])
            return
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
        """Populate the list widget with all courses sharing the given tag
        (i.e. "partners").
        """
        self.bt_save.setEnabled(text != self.value0)
        # Including the currently selected one (which we can't identify here!)?
        self.course_list.clear()
        plist = partners(text)
        dlist = []
        for p in plist:
            if p.course:
                # Present info about the course
                ci = get_course_info(p.course)
                # dlist.append(str(ci))
                dlist.append(
                    f"{ci.CLASS}.{ci.GRP}: {ci.SUBJECT} ({ci.TEACHER})"
                )

            else:
                # This is a block lesson
                dlist.append(f"[BLOCK] {p.PLACE}")
        self.course_list.addItems(dlist)

    def activate(self, start_value=""):
        self.bt_clear.setEnabled(bool(start_value))
        self.value0 = start_value
        self.result = None
        self.identifier.clear()
        taglist = db_values(
            "LESSONS",
            "PLACE",
            "PLACE LIKE '=_%'",  # "=" + at least one character
            # distinct=True,
            sort_field="PLACE",
        )
        self.identifier.addItems(
            [t[1:] for t in taglist if t.replace(" ", "") == t]
        )
        self.identifier.setCurrentText(self.value0)
        self.exec()
        return self.result


class DurationSelector(QComboBox):
    """A combobox for selecting lesson duration."""

    def __init__(self, modified=None, parent=None):
        super().__init__(parent)
        self.__callback = modified
        self.__report_changes = False
        self.currentTextChanged.connect(self.__changed)

    def setText(self, number):
        """Initialize the list of options and select the given one."""
        # print("(DurationSelector.setText)", number)
        self.__report_changes = False
        self.clear()
        self.addItems([str(i) for i in range(1, len(get_periods()) + 1)])
        self.setCurrentText(number)
        if self.__callback:
            self.__report_changes = True

    def __changed(self, text):
        # print("(DurationSelector.__changed)", text)
        if self.__report_changes and self.__callback:
            self.__callback(text)
        self.clearFocus()


class DayPeriodSelector(QLineEdit):
    def __init__(self, modified=None, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.__callback = modified

    def mousePressEvent(self, event):
        result = DayPeriodDialog.popup(start_value=self.text())
        if result:
            if result == "-":
                self.text_edited("")
            else:
                self.text_edited(result)

    def text_edited(self, text):
        if self.__callback and not self.__callback(text):
            return
        self.setText(text)


class PartnersSelector(QLineEdit):
    def __init__(self, modified=None, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.__callback = modified

    def mousePressEvent(self, event):
        result = PartnersDialog.popup(start_value=self.text())
        if result:
            if self.__callback and not self.__callback(result):
                return
            self.setText(result.lstrip("+-"))


class PayrollSelector(QLineEdit):
    def __init__(self, modified=None, no_length=False, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.__callback = modified
        self.__no_length = no_length

    def mousePressEvent(self, event):
        result = PayrollDialog.popup(
            start_value=self.text(), no_length=self.__no_length
        )
        if result:
            self.text_edited(result)

    def text_edited(self, text):
        if self.__callback and not self.__callback(text):
            return
        self.setText(text)


class RoomSelector(QLineEdit):
    def __init__(self, modified=None, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.__callback = modified

    def mousePressEvent(self, event):
        classroom = db_read_unique_field(
            "CLASSES", "CLASSROOM", CLASS=get_coursedata()["CLASS"]
        )
        result = RoomDialog.popup(start_value=self.text(), classroom=classroom)
        if result:
            if result == "-":
                self.text_edited("")
            else:
                self.text_edited(result)

    def text_edited(self, text):
        if self.__callback and not self.__callback(text):
            return
        self.setText(text)


class DurationDelegate(QStyledItemDelegate):
    def __init__(self, table, modified=None):
        super().__init__(parent=table)
        self.__table = table
        self.__modified = modified

    class Editor(DurationSelector):
        def showEvent(self, event):
            QTimer.singleShot(0, self.showPopup)

    def createEditor(self, parent, option, index):
        e = self.Editor(parent=parent)
        return e

    def setEditorData(self, editor, index):
        self.val0 = index.data()
        editor.setText(self.val0)

    def setModelData(self, editor, model, index):
        text = editor.currentText()
        #        self.__table.clearFocus()
        # print("?-------", text, text != self.val0)
        if text != self.val0:
            if (not self.__modified) or self.__modified(index.row(), text):
                model.setData(index, text)
        self.__table.setFocus()


class DayPeriodDelegate(QStyledItemDelegate):
    def __init__(self, table, modified=None):
        super().__init__(parent=table)
        self.__table = table
        self.__modified = modified

    class Editor(QLineEdit):
        # The line-edit is not used, but it has the necessary properties ...
        def showEvent(self, event):
            QTimer.singleShot(0, self.clearFocus)

    def createEditor(self, parent, option, index):
        return self.Editor(parent)

    def setModelData(self, editor, model, index):
        # This gets called on activation (thanks to the <showEvent>
        # method in <Editor>).
        old_value = model.data(index)  # or editor.text()
        # print("§§§ old:", old_value)
        rect = self.__table.visualRect(index)
        pos = self.__table.viewport().mapToGlobal(rect.bottomLeft())
        result = DayPeriodDialog.popup(old_value, pos=pos)
        if result:
            if (not self.__modified) or self.__modified(index.row(), result):
                model.setData(index, result)
        self.__table.setFocus()


class PartnersDelegate(QStyledItemDelegate):
    def __init__(self, table, modified=None):
        super().__init__(parent=table)
        self.__table = table
        self.__modified = modified

    class Editor(QLineEdit):
        # The line-edit is not used, but it has the necessary properties ...
        def showEvent(self, event):
            QTimer.singleShot(0, self.clearFocus)

    def createEditor(self, parent, option, index):
        return self.Editor(parent)

    def setModelData(self, editor, model, index):
        # This gets called on activation (thanks to the <showEvent>
        # method in <Editor>).
        old_value = model.data(index)  # or editor.text()
        # print("§§§ old:", old_value)

        rect = self.__table.visualRect(index)
        pos = self.__table.viewport().mapToGlobal(rect.bottomLeft())
        result = PartnersDialog.popup(old_value, pos=pos)
        # <result> can be empty -> no action,
        # it can be an existing "partners" entry,
        # it can have a +-prefix -> new entry,
        # it can be '-' -> clear it.
        if result:
            if (not self.__modified) or self.__modified(index.row(), result):
                model.setData(index, result.lstrip("+-"))
        self.__table.setFocus()
        # print("§§§ new", result)


class TableWidget(QTableWidget):
    def __init__(self, parent=None, changed_callback=None):
        self.changed_callback = changed_callback
        super().__init__(parent=parent)
        self.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.AnyKeyPressed
            | QAbstractItemView.EditTrigger.SelectedClicked  # this one has a delay!
        )
        # Note that the <Return> key doesn't cause the editor to be opened,
        # so there is an event handling that ... see method <keyPressEvent>.

        # Change stylesheet to make the selected cell more visible
        self.setStyleSheet(
            """QTableView {
               selection-background-color: #f0e0ff;
               selection-color: black;
            }
            QTableView::item:focus {
                selection-background-color: #d0ffff;
            }
            """
        )

    def keyPressEvent(self, e):
        e.accept()
        key = e.key()
        if key == Qt.Key_Return:
            if self.state() != self.EditingState:
                self.editItem(self.currentItem())
        else:
            super().keyPressEvent(e)


class BlockTagDialog(QDialog):
    """Select the block tag (subject + identifier) for a block. The
    identifier may be empty.

    A block tag is associated with multiple "course-lessons", though
    each tag should only occur once in any particular course.

    The "sublessons" belonging to the currently shown  block tag are
    displayed. In addition a list of associated courses is shown. These
    displays are only for informational purposes, they are not editable.
    """

    @classmethod
    def popup(cls, sid, tag):
        d = cls()
        return d.activate(sid, tag)

    @staticmethod
    def sidtag2value(sid, tag):
        """Encode a block tag, given the subject-id and identifier-tag."""
        return f">{sid}#{tag}"

    @staticmethod
    def parse_block_tag(block_tag):
        """Decode the given block tag. Return a triple:
        (subject-id, identifier-tag, subject name).
        """
        try:
            sid, tag = block_tag[1:].split("#", 1)
            subject = get_subjects().map(sid)
            if tag and not TAG_FORMAT.match(tag).hasMatch():
                raise ValueError
        except:
            SHOW_ERROR(f"{T['INVALID_BLOCK_TAG']}: {block_tag}")
            sid, subject = get_subjects()[0]
            tag = ""
        return sid, tag, subject

    def __init__(self):
        super().__init__()
        vbox0 = QVBoxLayout(self)
        hbox1 = QHBoxLayout()
        vbox0.addLayout(hbox1)

        vbox1 = QVBoxLayout()
        hbox1.addLayout(vbox1)
        self.subject = KeySelector(changed_callback=self.sid_changed)
        vbox1.addWidget(self.subject)

        self.identifier = QComboBox(editable=True)
        self.identifier.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.identifier.currentTextChanged.connect(self.show_courses)
        vbox1.addWidget(self.identifier)

        self.identifier.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        validator = QRegularExpressionValidator(TAG_FORMAT)
        self.identifier.setValidator(validator)

        self.lesson_table = TableWidget()  # Read-only, no focus, no selection
        self.lesson_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.lesson_table.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )
        self.lesson_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        vbox1.addWidget(self.lesson_table)
        self.lesson_table.setColumnCount(3)

        self.lesson_table.setHorizontalHeaderLabels(
            (T["LENGTH"], T["Time"], T["Partners"])
        )
        Hhd = self.lesson_table.horizontalHeader()
        Hhd.setMinimumSectionSize(60)
        self.lesson_table.resizeColumnsToContents()
        Hhd.setStretchLastSection(True)

        self.course_list = QListWidget()  # Read-only, no focus, no selection
        self.course_list.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )
        self.course_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        hbox1.addWidget(self.course_list)

        buttonBox = QDialogButtonBox()
        vbox0.addWidget(buttonBox)
        self.bt_save = buttonBox.addButton(QDialogButtonBox.StandardButton.Save)
        bt_cancel = buttonBox.addButton(QDialogButtonBox.StandardButton.Cancel)
        self.bt_save.clicked.connect(self.do_accept)
        bt_cancel.clicked.connect(self.reject)
        self.subject.set_items(get_subjects())

    def activate(self, sid, tag):
        self.value0 = self.sidtag2value(sid, tag)
        self.result = None
        try:
            self.subject.reset(sid)
            if tag == "#":
                tag = ""
        except GuiError:
            SHOW_ERROR(f"{T['UNKNOWN_SUBJECT_TAG']}: {sid[1:]}")
            tag = ""
        self.sid_changed(sid, tag)
        self.exec()
        return self.result

    def sid_changed(self, sid, tag=""):
        # print("sid changed:", sid)
        taglist = db_values(
            "LESSONS",
            "TIME",
            f"TIME LIKE '>{sid}#%'",
            distinct=True,
            sort_field="TIME",
        )
        # Disable show_courses callbacks here ...
        self.__block_show = True
        self.identifier.clear()
        self.identifier.addItems([t.split("#", 1)[1] for t in taglist])
        # ... until here, to avoid a spurious call
        self.__block_show = False
        # Set a dummy tag before initializing the tag editor, to ensure
        # that there is a call to <show_courses>.
        self.identifier.setEditText("#")
        self.identifier.setEditText(tag)
        return True  # accept

    def do_accept(self):
        tag = self.identifier.currentText()
        # An invalid tag should not be possible at this stage ...
        sid = self.subject.selected()
        time_field = self.sidtag2value(sid, tag)
        # print("OK", time_field)
        # An unchanged value should not be possible here ...
        # if time_field != self.value0:
        self.result = time_field
        if self.identifier.findText(tag) < 0:
            self.result = "+" + time_field
        self.accept()

    def show_courses(self, identifier):
        """Populate the list widget with all courses having a lesson entry
        in the block.
        """
        if self.__block_show or identifier == "#":
            return
        self.course_list.clear()
        tag = f">{self.subject.selected()}#{identifier}"
        self.bt_save.setEnabled(tag != self.value0)
        courselist = block_courses(tag)
        dlist = []
        for c in courselist:
            # Present info about the course
            ci = get_course_info(c)
            dlist.append(f"{ci.CLASS}.{ci.GRP}: {ci.SUBJECT} ({ci.TEACHER})")
        self.course_list.addItems(dlist)
        lesson_list = sublessons(tag)
        # print("§§§ LENGTHS:", lesson_list)
        ltable = self.lesson_table
        ltable.clearContents()
        nrows = len(lesson_list)
        ltable.setRowCount(nrows)
        for r in range(nrows):
            lessonfields = lesson_list[r]
            # print("???", lessonfields)
            ltable.setItem(r, 0, QTableWidgetItem(lessonfields.LENGTH))
            ltime, ltag = parse_time_field(lessonfields.TIME)
            ltable.setItem(r, 1, QTableWidgetItem(ltime))
            ltable.setItem(r, 2, QTableWidgetItem(ltag))


class BlockTagSelector(QLineEdit):
    def __init__(self, parent=None, modified=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.__callback = modified

    def set_block(self, block_tag):
        """Display the value as subject-name + (optional) identifier-tag."""
        self.sid, self.tag, subject = BlockTagDialog.parse_block_tag(block_tag)
        self.setText((subject + f" #{self.tag}") if self.tag else subject)

    def get_block(self):
        return BlockTagDialog.sidtag2value(self.sid, self.tag)

    def mousePressEvent(self, event):
        result = BlockTagDialog.popup(self.sid, self.tag)
        # print("--->", result)
        if not result:
            return
        if self.__callback and not self.__callback(result):
            return
        # print("§ set:", result)
        self.set_block(result.lstrip("+"))


class RoomDialog(QDialog):
    @classmethod
    def popup(cls, start_value="", classroom=""):
        d = cls()
        d.init()
        return d.activate(start_value, classroom)

    def __init__(self):
        super().__init__()
        vbox0 = QVBoxLayout(self)
        hbox1 = QHBoxLayout()
        vbox0.addLayout(hbox1)
        vboxl = QVBoxLayout()
        hbox1.addLayout(vboxl)

        self.roomchoice = QTableWidget()
        self.roomchoice.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.roomchoice.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.roomchoice.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.roomchoice.setColumnCount(2)
        vboxl.addWidget(self.roomchoice)

        vboxm = QVBoxLayout()
        hbox1.addLayout(vboxm)

        bt_up = QToolButton()
        bt_up.setToolTip(T["Move_up"])
        bt_up.clicked.connect(self.move_up)
        vboxm.addWidget(bt_up)
        bt_up.setArrowType(Qt.ArrowType.UpArrow)
        bt_up.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        bt_down = QToolButton()
        bt_down.setToolTip(T["Move_down"])
        bt_down.clicked.connect(self.move_down)
        vboxm.addWidget(bt_down)
        bt_down.setArrowType(Qt.ArrowType.DownArrow)

        vboxm.addStretch(1)
        bt_left = QToolButton()
        vboxm.addWidget(bt_left)
        bt_left.setArrowType(Qt.ArrowType.LeftArrow)
        bt_left.setToolTip(T["Add_to_choices"])
        bt_left.clicked.connect(self.add2choices)
        bt_right = QToolButton()
        vboxm.addWidget(bt_right)
        bt_right.setIcon(
            self.style().standardIcon(
                QStyle.StandardPixmap.SP_DialogDiscardButton
            )
        )
        bt_right.setToolTip(T["Remove_from_choices"])
        bt_right.clicked.connect(self.discard_choice)
        vboxm.addStretch(1)

        vboxr = QVBoxLayout()
        hbox1.addLayout(vboxr)

        self.roomlist = QTableWidget()
        self.roomlist.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.roomlist.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.roomlist.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.roomlist.setColumnCount(2)
        vboxr.addWidget(self.roomlist)

        self.roomtext = QLineEdit()
        self.roomtext.editingFinished.connect(self.text_edited)
        vboxl.addWidget(self.roomtext)

        self.home = QPushButton(f"+ {T['CLASSROOM']}")
        self.home.clicked.connect(self.add_classroom)
        vboxl.addWidget(self.home)
        self.extra = QCheckBox(T["OTHER_ROOMS"])
        self.extra.stateChanged.connect(self.toggle_extra)
        vboxl.addWidget(self.extra)

        vbox0.addWidget(HLine())
        buttonBox = QDialogButtonBox()
        vbox0.addWidget(buttonBox)
        bt_save = buttonBox.addButton(QDialogButtonBox.StandardButton.Save)
        bt_cancel = buttonBox.addButton(QDialogButtonBox.StandardButton.Cancel)
        bt_clear = buttonBox.addButton(QDialogButtonBox.StandardButton.Discard)

        bt_save.clicked.connect(self.do_accept)
        bt_cancel.clicked.connect(self.reject)
        bt_clear.clicked.connect(self.do_clear)

    def text_edited(self):
        self.set_choices(self.roomtext.text())

    def checkroom(self, roomid, choice_list):
        """Check that the given room-id is valid.
        If there is a "classroom", "$" may be used as a short-form.
        A valid room-id is added to the list <self.choices>, <None> is returned.
        Otherwise an error message is returned (a string).
        """
        is_classroom = False
        if roomid == "$":
            if self.classroom:
                rid = self.classroom
                is_classroom = True
            else:
                return T["NO_CLASSROOM_DEFINED"]
        else:
            rid = roomid
            if rid == self.classroom:
                is_classroom = True
        if rid in choice_list or (is_classroom and "$" in choice_list):
            if is_classroom:
                return T["CLASSROOM_ALREADY_CHOSEN"]
            else:
                return f"{T['ROOM_ALREADY_CHOSEN']}: '{rid}'"
        if rid in self.room2line:
            return None
        return f"{T['UNKNOWN_ROOM_ID']}: '{rid}'"

    def add2choices(self, roomid=None):
        if not roomid:
            # Not the most efficient handler, but it uses shared code ...
            row = self.roomlist.currentRow()
            riditem = self.roomlist.item(row, 0)
            roomid = riditem.text()
        e = self.checkroom(roomid, self.choices)
        if e:
            SHOW_ERROR(e)
            return
        self.add_valid_room_choice(roomid)
        self.write_choices()

    def discard_choice(self):
        row = self.roomchoice.currentRow()
        if row >= 0:
            self.choices.pop(row)
            self.roomchoice.removeRow(row)
            self.write_choices()

    def add_classroom(self):
        self.add2choices("$")

    def toggle_extra(self, state):
        self.write_choices()

    def move_up(self):
        row = self.roomchoice.currentRow()
        if row <= 0:
            return
        row1 = row - 1
        item = self.roomchoice.takeItem(row, 0)
        self.roomchoice.setItem(row, 0, self.roomchoice.takeItem(row1, 0))
        self.roomchoice.setItem(row1, 0, item)
        item = self.roomchoice.takeItem(row, 1)
        self.roomchoice.setItem(row, 1, self.roomchoice.takeItem(row1, 1))
        self.roomchoice.setItem(row1, 1, item)

        t = self.choices[row]
        self.choices[row] = self.choices[row1]
        self.choices[row1] = t
        self.write_choices()
        self.roomchoice.selectRow(row1)

    def move_down(self):
        row = self.roomchoice.currentRow()
        row1 = row + 1
        if row1 == len(self.choices):
            return
        item = self.roomchoice.takeItem(row, 0)
        self.roomchoice.setItem(row, 0, self.roomchoice.takeItem(row1, 0))
        self.roomchoice.setItem(row1, 0, item)
        item = self.roomchoice.takeItem(row, 1)
        self.roomchoice.setItem(row, 1, self.roomchoice.takeItem(row1, 1))
        self.roomchoice.setItem(row1, 1, item)

        t = self.choices[row]
        self.choices[row] = self.choices[row1]
        self.choices[row1] = t
        self.write_choices()
        self.roomchoice.selectRow(row1)

    def write_choices(self):
        text = "/".join(self.choices)
        if self.extra.isChecked():
            text += "+"
        self.roomtext.setText(text)

    def do_accept(self):
        val = self.roomtext.text()
        if val != self.value0:
            if val:
                self.result = val
            else:
                self.result = "-"
        self.accept()

    def do_clear(self):
        if self.value0:
            self.result = "-"
        self.accept()

    def init(self):
        self.room2line = {}
        rooms = get_rooms()
        n = len(rooms)
        self.roomlist.setRowCount(n)
        for i in range(n):
            rid = rooms[i][0]
            self.room2line[rid] = i
            item = QTableWidgetItem(rid)
            self.roomlist.setItem(i, 0, item)
            item = QTableWidgetItem(rooms[i][1])
            self.roomlist.setItem(i, 1, item)
        self.roomlist.resizeColumnsToContents()
        Hhd = self.roomlist.horizontalHeader()
        Hhd.hide()
        # Hhd.setMinimumSectionSize(20)
        # A rather messy attempt to find an appropriate size for the table
        Vhd = self.roomlist.verticalHeader()
        Vhd.hide()
        Hw = Hhd.length()
        # Vw = Vhd.sizeHint().width()
        fixed_width = Hw + 20  # + Vw, if vertical headers in use
        self.roomlist.setFixedWidth(fixed_width)
        self.roomchoice.setFixedWidth(fixed_width)
        Hhd.setStretchLastSection(True)
        hh = self.roomchoice.horizontalHeader()
        hh.hide()
        # Check that this doesn't need toggling after a clear() ...
        hh.setStretchLastSection(True)
        self.roomchoice.verticalHeader().hide()

    def activate(self, start_value="", classroom=None):
        self.value0 = start_value
        self.result = None
        self.classroom = classroom
        if classroom:
            self.home.show()
        else:
            self.home.hide()
        self.set_choices(start_value)
        self.roomlist.selectRow(0)
        self.roomtext.setFocus()
        self.exec()
        return self.result

    def set_choices(self, text):
        if text.endswith("+"):
            extra = True
            text = text[:-1]
        else:
            extra = False
        rids = text.split("/")
        errors = []
        _choices = []
        for rid in rids:
            if not rid:
                continue
            e = self.checkroom(rid, _choices)
            if e:
                if len(errors) > 3:
                    errors.append("  ...")
                    break
                errors.append(e)
            else:
                _choices.append(rid)
        else:
            # Perform changes only if not too many errors
            self.choices = []
            self.roomchoice.setRowCount(0)

            if _choices:
                for rid in _choices:
                    self.add_valid_room_choice(rid)
                self.roomchoice.selectRow(0)
            self.extra.setCheckState(
                Qt.CheckState.Checked if extra else Qt.CheckState.Unchecked
            )
        if errors:
            elist = "\n".join(errors)
            SHOW_ERROR(f"{T['INVALID_ROOM_IDS']}:\n{elist}")
        self.write_choices()

    def add_valid_room_choice(self, rid):
        """Append the room with given id to the choices table.
        This assumes that the validity of <rid> has already been checked!
        """
        self.choices.append(rid)
        if rid == "$":
            rid = self.classroom
        row = self.room2line[rid]
        at_row = self.roomchoice.rowCount()
        self.roomchoice.insertRow(at_row)
        self.roomchoice.setItem(at_row, 0, self.roomlist.item(row, 0).clone())
        self.roomchoice.setItem(at_row, 1, self.roomlist.item(row, 1).clone())
        self.roomchoice.resizeColumnsToContents()


class PayrollDialog(QDialog):
    @classmethod
    def popup(cls, start_value="", no_length=False):
        d = cls(no_length)
        return d.activate(start_value)

    def __init__(self, no_length=False):
        super().__init__()
        vbox0 = QVBoxLayout(self)
        vbox0.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        hbox1 = QHBoxLayout()
        vbox0.addLayout(hbox1)
        self.number = QLineEdit()
        self.number.setToolTip(T["PAYROLL_VALID_ENTRY"])
        hbox1.addWidget(self.number)
        # If <no_length> is true, there must be a number in the expression.
        regexp = QRegularExpression(
            PAYROLL_FORMAT if no_length else PAYROLL_FORMAT + "|"
        )
        validator = QRegularExpressionValidator(regexp)
        self.number.setValidator(validator)

        self.factor = KeySelector()
        hbox1.addWidget(self.factor)

        vbox0.addWidget(HLine())
        buttonBox = QDialogButtonBox()
        vbox0.addWidget(buttonBox)
        bt_save = buttonBox.addButton(QDialogButtonBox.StandardButton.Save)
        bt_cancel = buttonBox.addButton(QDialogButtonBox.StandardButton.Cancel)
        bt_save.clicked.connect(self.do_accept)
        bt_cancel.clicked.connect(self.reject)

        entries = []
        for k, v in get_payroll_weights():
            val = f"{v:.2f})".replace('.', CONFIG["DECIMAL_SEP"])
            entries.append((k, f"{k} ({val})"))
        self.factor.set_items(entries)

    def do_accept(self):
        if not self.number.hasAcceptableInput():
            SHOW_ERROR(T["INVALID_PAYROLL"])
            return
        n = self.number.text()
        f = self.factor.selected()
        text = n + "*" + f
        if text != self.text0:
            self.result = text
        self.accept()

    def activate(self, start_value=""):
        self.result = None
        self.text0 = start_value
        try:
            n, f = start_value.split("*", 1)
            self.number.setText(n)
            if not self.number.hasAcceptableInput():
                self.number.setText("")
                raise ValueError
            self.factor.reset(f)
        except (ValueError, GuiError):
            SHOW_ERROR(f"{T['INVALID_PAYROLL']}: '{start_value}'")
        self.exec()
        return self.result


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    m = TAG_FORMAT.match("")
    print(m.hasMatch(), m.captured(0))
    #    quit(0)

    open_database()

    for p in placements(">ZwE#09G10G"):
        print("!!!!", p)

    for p in partners("sp03"):
        print("??????", p)

    widget = BlockTagDialog()
    print("----->", widget.activate("ZwE", "09G10G"))
    print("----->", widget.activate("Hu", ""))

    #    quit(0)

    widget = PayrollDialog()
    print("----->", widget.activate(start_value="Fred*HuEp"))

    #    quit(0)

    widget = RoomDialog()
    widget.init()
    print("----->", widget.activate(start_value="$/rPh+", classroom="r10G"))

    #    quit(0)

    widget = PartnersDialog()
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
