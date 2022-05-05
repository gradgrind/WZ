"""
ui/modules/course_lessons.py

Last updated:  2022-05-05

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

#TODO: Rework using Dialogs for the form editors

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

from core.db_management import open_database, db_key_value_list

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

#?
    QDialog,
    QWidget,
    QComboBox,
    QCheckBox,
    QValidator,
    QStackedLayout,
    QGridLayout,
    QSizePolicy,
    QSize,

#    QTableView,
    QAbstractItemView,
    ### QtCore:
    Qt,
    ### QtSql:
    QSqlTableModel,
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
        "TAG",
        "ROOM",
        "PLACE",
        "NOTES"
    )
]
LESSONCOLS_SHOW = ("LENGTH", "PAYROLL", "TAG")

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

    def is_modified(self):
        return bool(self.course_editor.form_change_set)

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

        self.rightframe = QFrame()
        self.addWidget(self.rightframe)
        self.rightframe.setLineWidth(2)
        self.rightframe.setFrameShape(QFrame.Box)

        vbox2 = QVBoxLayout(self.rightframe)

        # Course management buttons
        hboxB = QHBoxLayout()
        vbox2.addLayout(hboxB)
        #+
        self.course_delete_button = QPushButton(T["DELETE_COURSE"])
        hboxB.addWidget(self.course_delete_button)
        self.course_delete_button.clicked.connect(self.course_delete)
#TODO: self.course_delete_button: handle enabling and disabling (empty table)
        #+
        hboxB.addStretch(1)
        #+
        self.course_dialog = CourseEditorForm()
        edit_button = QPushButton(T["EDIT_COURSE"])
        hboxB.addWidget(edit_button)
        edit_button.clicked.connect(self.edit_course)

        vbox2.addWidget(HLine())
        vbox2.addStretch(1)

        vbox2.addWidget(QLabel(f"<h4>{T['LESSONS']}</h4>"))

        # The lesson table
        self.lessontable = RowSelectTable(name="lessons")
        self.lessontable.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )  # non-editable
        self.lessontable.verticalHeader().hide()
        self.lessontable.set_callback(self.lesson_selected)
        self.lessontable.activated.connect(self.lesson_activate)
        vbox2.addWidget(self.lessontable)

        form = QFormLayout()
        vbox2.addLayout(form)
        self.field_lines = {}
        for f, t in LESSON_COLS:
            if f not in LESSONCOLS_SHOW:
                widget = QLineEdit()
                widget.setReadOnly(True)
                self.field_lines[f] = widget
                form.addRow(t, widget)

        vbox2.addSpacing(20)
        hbox3 = QHBoxLayout()
        vbox2.addLayout(hbox3)
        self.lesson_delete_button = QPushButton(T['DELETE'])
        hbox3.addWidget(self.lesson_delete_button)
        self.lesson_delete_button.clicked.connect(self.lesson_delete)
        self.lesson_add_button = QPushButton(T['COPY_NEW'])
        hbox3.addWidget(self.lesson_add_button)
        self.lesson_add_button.clicked.connect(self.lesson_add)

        self.setStretchFactor(0, 1)  # stretch only left panel

        self.lesson_editor = LessonEditor()
#        vbox3.addWidget(self.lesson_editor)

    def course_activate(self, modelindex):
        self.edit_course()

    def edit_course(self):
        row = self.course_dialog.activate(
            self.current_row,
            (self.filter_field, self.filter_value)
        )
        if row >= 0:
            self.coursetable.selectRow(row)



#    def modified(self):
#        #return self.form_change_set
#        return bool(self.form_change_set)

#    def clear_modified(self):
#        self.form_change_set = set()

    def leave_ok(self):
#        if self.form_change_set:
#            return LoseChangesDialog()
        return True

    def set_filter_field(self, field):
#        if self.modified():
#            if LoseChangesDialog():
#                self.clear_modified()
#            else:
#                return False
        self.filter_value_select.set_items(self.filter_list[field])
        # print("FILTER FIELD:", field)
        self.filter_field = field
        self.filter_value_select.trigger()
        return True

    def set_filter(self, key):
#        if self.modified():
#            if LoseChangesDialog():
#                self.clear_modified()
#            else:
#                return False
        # print("FILTER KEY:", key)
        self.filter_value = key
        self.fill_course_table(key)
        return True

# TODO: This now only handles empty tables? DEPRECATED, not used
#    def form_modified(self, field, changed):
#        print("???????!!!:", repr(field), changed, self.table_empty, self.form_change_set)

#Enter empty table ->
#???????!!!: '' False True set()
#Otherwise ->
#???????!!!: '' False False set()


        """Handle a change in a form editor field.
        Maintain the set of changed fields (<self.form_change_set>).
        Enable and disable the pushbuttons appropriately.
        """
        if self.form_change_set == None:
            return
        if self.table_empty:
#            self.course_update_button.setEnabled(False)
#            self.course_add_button.setEnabled(True)
            self.course_delete_button.setEnabled(False)
        elif changed:
#            self.course_update_button.setEnabled(True)
            self.form_change_set.add(field)
#            if field in COURSE_KEY_FIELDS:
#                self.course_add_button.setEnabled(True)
            self.form_change_set.add(field)
        else:
            self.form_change_set.discard(field)
            if self.form_change_set:
                pass
#                if not self.form_change_set.intersection(COURSE_KEY_FIELDS):
#                    self.course_add_button.setEnabled(False)
            else:
                self.course_delete_button.setEnabled(True)
#                self.course_update_button.setEnabled(False)
#                self.course_add_button.setEnabled(False)
        # print("FORM CHANGED SET:", self.form_change_set)

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
        else:
            # e.g. when entering an empty table
            #print("EMPTY TABLE")
            self.set_course(0)
            self.course_delete_button.setEnabled(False)

    def course_delete(self):
        """Delete the current course."""
        model = self.coursemodel
#        if self.form_change_set:
#            if not LoseChangesDialog():
#                return
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
        # Enable or disable lesson butttons
        if not self.lessonmodel.rowCount():
            self.lesson_selected(-1)
        self.lesson_add_button.setEnabled(course > 0)

        # Toggle the stretch on the last section here because of a
        # possible bug in Qt, where the stretch can be lost when
        # repopulating.
        hh = self.lessontable.horizontalHeader()
        hh.setStretchLastSection(False)
        hh.setStretchLastSection(True)

    def lesson_selected(self, row):
        #print("SELECT LESSON", row)
        if row >= 0:
            self.lesson_delete_button.setEnabled(True)
        else:
            self.lesson_delete_button.setEnabled(False)
        record = self.lessonmodel.record(row)
        for f, t in LESSON_COLS:
            if f not in LESSONCOLS_SHOW:
                self.field_lines[f].setText(str(record.value(f)))

    def lesson_activate(self, index):
#TODO
        print("ACTIVATE LESSON", index.row())

    def lesson_add(self):
        """Add a new "lesson", copying the current one if possible."""
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
            record.setValue("PLACE", "?")
            if model.insertRecord(-1, record) and model.submitAll():
                #lid = model.query().lastInsertId()
                #print("INSERTED:", lid, model.rowCount())
                self.lessontable.selectRow(n)
            else:
                SHOW_ERROR(f"DB Error: {model.lastError().text()}")
                model.revertAll()

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


class EditableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent=parent, editable=True)

    def focusOutEvent(self, e):
        """Close the editor when focus leaves it. This reverts any
        partially entered text.
        """
        self.clearEditText()
        self.setCurrentIndex(self.currentIndex())


class BlocknameValidator(QValidator):
    def validate(self, text, pos):
        print("VALIDATE:", pos, text)
        if text.startswith("+"):
            return (QValidator.State.Invalid, text, pos)
        if text.endswith("+"):
            return (QValidator.State.Intermediate, text, pos)
        return (QValidator.State.Acceptable, text, pos)


class LessonEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        vbox1 = QVBoxLayout(self)
        vbox1.setContentsMargins(0, 0, 0, 0)
        hbox1 = QHBoxLayout()
        vbox1.addLayout(hbox1)
        self.blockmember = QCheckBox("Blockmitglied")
        hbox1.addWidget(self.blockmember)
        hbox1.addStretch(1)
        hbox1.addWidget(QLabel("Kennzeichen:"))
# It might be preferable to use a non-editable combobox with a separate
# button+popup (or whatever) to add a new identifier.
        self.identifier = EditableComboBox()
        #self.identifier.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        #self.identifier.setInsertPolicy(QComboBox.InsertPolicy.InsertAtTop)
        # Alphabetical insertion doesn't apply to the items added programmatically
        self.identifier.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
        self.identifier.addItems(("10Gzwe", "Short", "Long_identifier"))
        self.identifier.setItemData(0, "First item", Qt.ToolTipRole)
        self.identifier.setItemData(1, "A rather longer tooltip,\n very rambly actually ...", Qt.ToolTipRole)
        bn_validator = BlocknameValidator()
        self.identifier.setValidator(bn_validator)
        self.identifier.textActivated.connect(self.text_activated)
        hbox1.addWidget(self.identifier)

        self.stack = QStackedLayout(vbox1)

        box1 = QFrame()
        self.stack.addWidget(box1)
        #editor1 = QFormLayout(box1)
        editor1 = QGridLayout(box1)
        editor1.setContentsMargins(0, 0, 0, 0)

        self.elist2 = {}
#        for f, t in COURSE_COLS:
#            e1 = FormLineEdit("LENGTH", self.lform_modified)
        e1 = MiniLineEdit()
        #e1.setMinimumWidth(50)
        self.elist2["LENGTH"] = e1
        editor1.addWidget(QLabel("LENGTH:"), 0, 0)
        editor1.addWidget(e1, 0, 1)
        editor1.setColumnMinimumWidth(2, 30)
        editor1.setColumnStretch(2, 1)
        #e1.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        e2 = MiniLineEdit()
        #e2.setMinimumWidth(50)
        self.elist2["PAYROLL"] = e2
        editor1.addWidget(QLabel("PAYROLL:"), 0, 3)
        editor1.addWidget(e2, 0, 4)
        e3 = QLineEdit()
        editor1.addWidget(QLabel("ROOM:"), 1, 0)
        editor1.addWidget(e3, 1, 1, 1, 4)
        self.elist2["ROOM"] = e3
        e4 = QLineEdit()
        editor1.addWidget(QLabel("NOTES:"), 2, 0)
        self.elist2["NOTES"] = e4
        editor1.addWidget(e4, 2, 1, 1, 4)

#TODO: Pane for block members, pane activation, pane filling ...


    def text_activated(self, text):
        # Seems just like activated_index, but passes text
        print("ACTIVATED TEXT:", text)

    def set_data(self, data):
        tag = data["TAG"]
        if tag.startswith(">"):
            self.blockmember.setChecked(True)
            # ...
        else:
            self.blockmember.setChecked(False)
            # ...
        self.identifier.setCurrentText(tag)
        self.elist2["LENGTH"].setText(data["LENGTH"])
        self.elist2["PAYROLL"].setText(data["PAYROLL"])
        self.elist2["ROOM"].setText(data["ROOM"])
        self.elist2["NOTES"].setText(data["NOTES"])



# Use FormLineEdit instead
class MiniLineEdit(QLineEdit):
#    def __init__(self, parent=None):
#        super().__init__(parent)

    def sizeHint(self):
        sh = super().sizeHint()
        if sh.isValid():
            return QSize(50, sh.height())
        else:
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
        #return self.form_change_set
        return bool(self.form_change_set)

    def clear_modified(self):
        self.form_change_set = set()

    def leave_ok(self):
        if self.modified():
            return LoseChangesDialog()
        return True

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


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from ui.ui_base import run

    widget = Courses()
    widget.enter()
    widget.resize(1000, 550)
    run(widget)
