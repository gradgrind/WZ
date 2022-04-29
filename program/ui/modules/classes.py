"""
ui/modules/classes.py

Last updated:  2022-04-26

Edit classes' data.


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

#TODO ...

########################################################################

if __name__ == "__main__":
    import sys, os, builtins

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

T = TRANSLATIONS("ui.modules.classes")

### +++++

from core.db_management import open_database, db_key_value_list, read_pairs

from ui.ui_base import (
    HLine,
    LoseChangesDialog,
    TableViewRowSelect,
    FormLineEdit,
    # QtWidgets
    QSplitter,
    QFrame,
    QScrollArea,
    QWidget,
    QFormLayout,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableView,
    QHeaderView,
    # QtCore
    Qt,
    # QtSql
    QSqlTableModel,
)
from ui.editable import EdiTableWidget

# Class table fields
CLASS_COLS = [
    (f, T[f]) for f in ("CLASS", "NAME", "CLASSROOM", "TT_DATA")
]

from timetable.constraints_class import CONSTRAINT_FIELDS, period_validator

### -----


def init():
    MAIN_WIDGET.add_tab(Classes())


class Classes(Page):
    name = T["MODULE_NAME"]
    title = T["MODULE_TITLE"]

    def __init__(self):
        super().__init__()
        self.class_editor = ClassEditor()
        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.class_editor)

    def enter(self):
        open_database()
        self.class_editor.init_data()

    def is_modified(self):
        return bool(self.class_editor.form_change_set)


# ++++++++++++++ The widget implementation ++++++++++++++


class ClassEditor(QSplitter):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setChildrenCollapsible(False)

        leftframe = QFrame()
        self.addWidget(leftframe)
        leftframe.setLineWidth(2)
        leftframe.setFrameShape(self.Box)
        vbox1 = QVBoxLayout(leftframe)

        # The main class table
        self.classtable = TableViewRowSelect(self)
        self.classtable.setEditTriggers(
            QTableView.NoEditTriggers
        )  # non-editable
        self.classtable.verticalHeader().hide()
        vbox1.addWidget(self.classtable)

        self.rightframe = QFrame()
        self.addWidget(self.rightframe)
        self.rightframe.setLineWidth(2)
        self.rightframe.setFrameShape(QFrame.Box)

        vbox2 = QVBoxLayout(self.rightframe)
        editorbox = QFrame()
        self.classeditor = QFormLayout(editorbox)
        vbox2.addWidget(editorbox)
        self.editors = {}
        for f, t in CLASS_COLS:
            if f == "TT_DATA":
                editwidget = FormSpecialEdit(f, self.form_modified, t)
                for f_, t_ in CONSTRAINT_FIELDS:
                    if f_ == "AVAILABLE":
                        ewidget = WeekTable(f_, editwidget.form_modified, t_)
                        editwidget.addBox(f_, ewidget)
                    else:
                        ewidget = FormLineEdit(f_, editwidget.form_modified)
                        editwidget.addRow(f_, ewidget, t_)

                self.classeditor.addRow(editwidget)
            else:
                editwidget = FormLineEdit(f, self.form_modified)
                self.classeditor.addRow(t, editwidget)
            self.editors[f] = editwidget

        hbox2 = QHBoxLayout()
        vbox2.addLayout(hbox2)
        hbox2.addStretch(1)
        self.class_delete_button = QPushButton(T["DELETE"])
        self.class_delete_button.clicked.connect(self.class_delete)
        hbox2.addWidget(self.class_delete_button)
        self.class_update_button = QPushButton(T["UPDATE"])
        self.class_update_button.clicked.connect(self.class_update)
        hbox2.addWidget(self.class_update_button)
        self.class_add_button = QPushButton(T["NEW"])
        self.class_add_button.clicked.connect(self.class_add)
        hbox2.addWidget(self.class_add_button)
        vbox2.addStretch(1)

        self.form_change_set = None
        self.setStretchFactor(0, 1)  # stretch only left panel

    def modified(self):
        return bool(self.form_change_set)

    def leave_ok(self):
        if self.form_change_set:
            return LoseChangesDialog()
        return True

    def form_modified(self, field, changed):
        """Handle a change in a form editor field.
        Maintain the set of changed fields (<self.form_change_set>).
        Enable and disable the pushbuttons appropriately.
        """
        # print("???form_modified:", field, changed, self.form_change_set)
        if changed:
            self.form_change_set.add(field)
        else:
            self.form_change_set.discard(field)
        self.set_buttons()

    def set_buttons(self):
        if self.table_empty:
            self.class_update_button.setEnabled(False)
            self.class_add_button.setEnabled(True)
            self.class_delete_button.setEnabled(False)
        elif self.form_change_set:
            self.class_update_button.setEnabled(True)
            self.class_add_button.setEnabled(True)
            self.class_delete_button.setEnabled(True)
        else:
            self.class_update_button.setEnabled(False)
            self.class_add_button.setEnabled(False)
            self.class_delete_button.setEnabled(True)

    def init_data(self):
        # Set up the class model, first clearing the "model-view"
        # widgets (in case this is a reentry)
        self.classtable.setModel(None)
        self.classmodel = QSqlTableModel()
        self.classmodel.setTable("CLASSES")
        self.classmodel.setEditStrategy(QSqlTableModel.OnManualSubmit)
        # Set up the class view
        self.classtable.setModel(self.classmodel)
        selection_model = self.classtable.selectionModel()
        selection_model.currentChanged.connect(self.class_changed)
        for f, t in CLASS_COLS:
            i = self.classmodel.fieldIndex(f)
            self.classmodel.setHeaderData(i, Qt.Horizontal, t)
            if f == "TT_DATA":
                self.tt_data_col = i
                self.classtable.hideColumn(i)
                # Set up the week table
                self.editors[f].widgets["AVAILABLE"].setup()
        # Initialize the class table
        self.fill_class_table()

    def fill_class_table(self):
        """Set filter and sort criteria, then populate table."""
        self.classmodel.setSort(
            self.classmodel.fieldIndex("SORTNAME"),
            Qt.AscendingOrder,
        )
        # print("SELECT:", self.classmodel.selectStatement())
        self.classmodel.select()
        self.classtable.selectRow(0)
        if not self.classtable.currentIndex().isValid():
            self.class_changed(None, None)
        self.classtable.resizeColumnsToContents()

    def class_changed(self, new, old):
        self.form_change_set = set()
        if new:
            self.table_empty = False
            row = new.row()
            # print("CURRENT", old.row(), "->", row)
            record = self.classmodel.record(row)
            for f, t in CLASS_COLS:
                self.editors[f].setText(str(record.value(f)))
        else:
            # e.g. when entering an empty table
            self.table_empty = True
            # print("EMPTY TABLE")
            for f, t in CLASS_COLS:
                self.editors[f].setText("")
        # print("===", self.form_change_set)
        self.set_buttons()

    def class_delete(self):
        """Delete the current class."""
        model = self.classmodel
        if self.form_change_set:
            if not LoseChangesDialog():
                return
        index = self.classtable.currentIndex()
        row = index.row()
        model.removeRow(row)
        if model.submitAll():
            if row >= model.rowCount():
                row = model.rowCount() - 1
            self.classtable.selectRow(row)
            if not self.classtable.currentIndex().isValid():
                self.class_changed(None, None)
        else:
            error = model.lastError()
            SHOW_ERROR(error.text())
            model.revertAll()

    def class_add(self):
        """Add the data in the form editor as a new class."""
        model = self.classmodel
        index = self.classtable.currentIndex()
        row0 = index.row()
        row = 0
        model.insertRow(row)
        for f, t in CLASS_COLS:
            col = model.fieldIndex(f)
            val = self.editors[f].text()
            if f == "CLASS":
                inserted = val
                icol = col
            model.setData(model.index(row, col), val)
        if model.submitAll():
            # print("INSERTED:", inserted)
            # Try to select the new entry
            for r in range(model.rowCount()):
                if model.data(model.index(r, icol)) == inserted:
                    self.classtable.selectRow(r)
                    break
            else:
                self.classtable.selectRow(row0)
        else:
            error = model.lastError()
            if "UNIQUE" in error.databaseText():
                SHOW_ERROR(T["UNIQUE_FIELDS"])
            else:
                SHOW_ERROR(error.text())
            model.revertAll()

    def class_update(self):
        """Update the current class with the data in the form editor."""
        model = self.classmodel
        index = self.classtable.currentIndex()
        klass = model.data(index)
        row = index.row()
        # print("???class_update:", self.form_change_set)
        for f in self.form_change_set:
            if f:
                col = model.fieldIndex(f)
                val = self.editors[f].text()
                model.setData(model.index(row, col), val)
        if model.submitAll():
            # The selection is lost – the changed row may even be in a
            # different place, perhaps not even displayed.
            # Try to stay with the same id, if it is displayed,
            # otherwise the same (or else the last) row.
            # print("UPDATED:", klass)
            for r in range(model.rowCount()):
                if model.data(model.index(r, 0)) == klass:
                    self.classtable.selectRow(r)
                    break
            else:
                if row >= model.rowCount():
                    row = model.rowCount() - 1
                self.classtable.selectRow(row)
        else:
            error = model.lastError()
            if "UNIQUE" in error.databaseText():
                SHOW_ERROR(T["UNIQUE_FIELDS"])
            else:
                SHOW_ERROR(error.text())
            model.revertAll()


class WeekTable(QFrame):
    def __init__(self, field, modified, title, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        self.__table = EdiTableWidget(align_centre=True)
        self.__table.setStyleSheet(
            """QTableView {
               selection-background-color: #e0e0ff;
               selection-color: black;
            }
            QTableView::item:focus {
                selection-background-color: #d0ffff;
            }
            """
        )

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(3, 3, 3, 3)

        label = QLabel(f"<h4>{title}</h4>")
        vbox.addWidget(label)
        vbox.addWidget(self.__table)
        self.__modified = modified
        self.__field = field

    def setup(self):
        tt_days = db_key_value_list("TT_DAYS", "N", "NAME", "N")
        tt_periods = db_key_value_list("TT_PERIODS", "N", "TAG", "N")
        self.__table.setup(
            colheaders=[p[1] for p in tt_periods],
            rowheaders=[d[1] for d in tt_days],
            undo_redo=False,
            cut=False,
            paste=True,
            row_add_del=False,
            column_add_del=False,
            on_changed=self.table_changed,
        )
        Hhd = self.__table.horizontalHeader()
        Hhd.setMinimumSectionSize(20)
        self.__table.resizeColumnsToContents()
        # A rather messy attempt to find an appropriate size for the table
        Vhd = self.__table.verticalHeader()
        Hw = Hhd.length()
        Hh = Hhd.sizeHint().height()
        Vw = Vhd.sizeHint().width()
        Vh = Vhd.length()
        self.__table.setMinimumWidth(Hw + Vw + 10)
        self.__table.setFixedHeight(Vh + Hh + 10)
        # self.__table.setMaximumHeight(Vh + Hh + 10)
        Hhd.setSectionResizeMode(QHeaderView.Stretch)
        Vhd.setSectionResizeMode(QHeaderView.Stretch)

    def text(self):
        table = self.__table.read_all()
        return "_".join(["".join(row) for row in table])

    def setText(self, text):
        # Set up table
        table = self.__table
        tdata = []
        daysdata = text.split("_")
        nrows = table.row_count()
        ncols = table.col_count()
        if len(daysdata) > nrows:
            errors = len(daysdata) - nrows
        else:
            errors = 0
        for d in range(nrows):
            ddata = []
            tdata.append(ddata)
            try:
                daydata = daysdata[d]
                if len(daydata) > ncols:
                    errors += 1
            except IndexError:
                daydata = ""
            for p in range(ncols):
                try:
                    v = daydata[p]
                except IndexError:
                    errors += 1
                    v = "+"
                else:
                    # Check validity
                    if period_validator(v):
                        errors += 1
                        v = "+"
                ddata.append(v)
        table.init_data(tdata)
        self.block_unchanged = bool(errors)
        if errors:
            SHOW_WARNING(T["INVALID_PERIOD_VALUES"].format(n=errors, val=text))
            self.__modified(self.__field, True)
        # Add cell validators
        for r in range(nrows):
            for c in range(ncols):
                table.set_validator(r, c, period_validator)

    def table_changed(self, mod):
        if not self.block_unchanged:
            self.__modified(self.__field, mod)


class FormSpecialEdit(QVBoxLayout):
    """A specialized editor widget – though as far as Qt is concerned,
    it is actually a layout – for use in the editor form for a
    "TableViewRowSelect" table view.

    The constructor receives the name of the field and a function which
    is to be called when the selected value is changed. This function
    takes the field name and a boolean (value != initial value, set by
    the "setText" method).
    """

    def __init__(self, field, modified, title, parent=None):
        super().__init__(parent)
        # self.setContentsMargins(0, 0, 0, 0)
        self.addWidget(HLine())
        self.addWidget(QLabel(f"<h4>{title}</h4>"))
        formbox = QScrollArea()
        formbox.setWidgetResizable(True)
        self.addWidget(formbox)
        formwidget = QWidget()
        self.__form = QFormLayout(formwidget)
        self.__form.setContentsMargins(3, 3, 3, 3)
        formbox.setWidget(formwidget)
        self.widgets = {}
        self.__modified = modified
        self.__field = field
        self.text0 = None

    def addRow(self, tag, widget, name):
        self.__form.addRow(name, widget)
        self.widgets[tag] = widget

    def addBox(self, tag, widget):
        self.addWidget(widget)
        self.widgets[tag] = widget

    def text(self):
        # Construct value from the component widgets
        vals = [f"{f}:{w.text()}" for f, w in self.widgets.items()]
        return "\n".join(vals)

    def setText(self, text):
        self.change_set = set()
        self.text0 = text
        # Set up subwidgets
        data = dict(read_pairs(text))
        for f, t in CONSTRAINT_FIELDS:
            self.widgets[f].setText(data.get(f) or "")

    def form_modified(self, field, changed):
        # print(f"???FormSpecialEdit ({self.__field}): <{field}> {changed}\n +++ {self.change_set}")
        if changed:
            if not self.change_set:
                self.__modified(self.__field, True)
            self.change_set.add(field)
        elif self.change_set:
            self.change_set.discard(field)
            if not self.change_set:
                self.__modified(self.__field, False)


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from ui.ui_base import run

    widget = Classes()
    widget.enter()
    widget.resize(1000, 550)
    run(widget)
