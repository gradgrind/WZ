"""
ui/modules/teachers.py

Last updated:  2022-04-20

Edit teachers' data.


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
    import sys, os, builtins

    this = sys.path[0]
    appdir = os.path.dirname(os.path.dirname(this))
    sys.path[0] = appdir
    try:
        builtins.PROGRAM_DATA = os.environ["PROGRAM_DATA"]
    except KeyError:
        basedir = os.path.dirname(appdir)
        builtins.PROGRAM_DATA = os.path.join(basedir, "wz-data")
    from core.base import start
    from ui.ui_base import StandalonePage as Page

    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    #    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))
else:
    from ui.ui_base import StackPage as Page

T = TRANSLATIONS("ui.modules.teachers")

### +++++

from utility.db_management import open_database, db_key_value_list, read_pairs

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
    # QtCore
    Qt,
    # QtSql
    QSqlTableModel,
)
from ui.editable import EdiTableWidget

# Teacher table fields
TEACHER_COLS = [
    (f, T[f]) for f in ("TID", "NAME", "FULLNAME", "SORTNAME", "TT_DATA")
]

from timetable.constraints_teacher import CONSTRAINT_FIELDS

### -----


def init():
    MAIN_WIDGET.add_tab(Teachers())


class Teachers(Page):
    name = T["MODULE_NAME"]
    title = T["MODULE_TITLE"]

    def __init__(self):
        super().__init__()
        self.teacher_editor = TeacherEditor()
        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.teacher_editor)

    def enter(self):
        open_database()
        self.teacher_editor.init_data()

    def is_modified(self):
        return bool(self.teacher_editor.form_change_set)


# ++++++++++++++ The widget implementation ++++++++++++++


class TeacherEditor(QSplitter):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setChildrenCollapsible(False)

        leftframe = QFrame()
        self.addWidget(leftframe)
        leftframe.setLineWidth(2)
        leftframe.setFrameShape(self.Box)
        vbox1 = QVBoxLayout(leftframe)

        # The main teacher table
        self.teachertable = TableViewRowSelect(self)
        self.teachertable.setEditTriggers(
            QTableView.NoEditTriggers
        )  # non-editable
        self.teachertable.verticalHeader().hide()
        vbox1.addWidget(self.teachertable)

        self.rightframe = QFrame()
        self.addWidget(self.rightframe)
        self.rightframe.setLineWidth(2)
        self.rightframe.setFrameShape(QFrame.Box)

        vbox2 = QVBoxLayout(self.rightframe)
        editorbox = QFrame()
        self.teachereditor = QFormLayout(editorbox)
        vbox2.addWidget(editorbox)
        self.editors = {}
        for f, t in TEACHER_COLS:
            if f == "TT_DATA":
                editwidget = FormSpecialEdit(f, self.form_modified, t)
                for f_, t_ in CONSTRAINT_FIELDS:
                    if f_ == "AVAILABLE":
                        ewidget = WeekTable(f_, editwidget.form_modified, t_)
                        editwidget.addBox(f_, ewidget)
                    else:
                        ewidget = FormLineEdit(f_, editwidget.form_modified)
                        editwidget.addRow(f_, ewidget, t_)

                self.teachereditor.addRow(editwidget)
            else:
                editwidget = FormLineEdit(f, self.form_modified)
                self.teachereditor.addRow(t, editwidget)
            self.editors[f] = editwidget

        hbox2 = QHBoxLayout()
        vbox2.addLayout(hbox2)
        hbox2.addStretch(1)
        self.teacher_delete_button = QPushButton(T["DELETE"])
        self.teacher_delete_button.clicked.connect(self.teacher_delete)
        hbox2.addWidget(self.teacher_delete_button)
        self.teacher_update_button = QPushButton(T["UPDATE"])
        self.teacher_update_button.clicked.connect(self.teacher_update)
        hbox2.addWidget(self.teacher_update_button)
        self.teacher_add_button = QPushButton(T["NEW"])
        self.teacher_add_button.clicked.connect(self.teacher_add)
        hbox2.addWidget(self.teacher_add_button)
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
        if self.form_change_set == None:
            return
        if self.table_empty:
            self.teacher_update_button.setEnabled(False)
            self.teacher_add_button.setEnabled(True)
            self.teacher_delete_button.setEnabled(False)
        elif changed:
            self.teacher_update_button.setEnabled(True)
            self.form_change_set.add(field)
            self.teacher_add_button.setEnabled(True)
            self.form_change_set.add(field)
        else:
            self.form_change_set.discard(field)
            if self.form_change_set:
                self.teacher_add_button.setEnabled(False)
            else:
                self.teacher_delete_button.setEnabled(True)
                self.teacher_update_button.setEnabled(False)
                self.teacher_add_button.setEnabled(False)
        # print("FORM CHANGED SET:", self.form_change_set)

    def init_data(self):
        # Set up the teacher model, first clearing the "model-view"
        # widgets (in case this is a reentry)
        self.teachertable.setModel(None)
        self.teachermodel = QSqlTableModel()
        self.teachermodel.setTable("TEACHERS")
        self.teachermodel.setEditStrategy(QSqlTableModel.OnManualSubmit)
        # Set up the teacher view
        self.teachertable.setModel(self.teachermodel)
        selection_model = self.teachertable.selectionModel()
        selection_model.currentChanged.connect(self.teacher_changed)
        for f, t in TEACHER_COLS:
            i = self.teachermodel.fieldIndex(f)
            self.teachermodel.setHeaderData(i, Qt.Horizontal, t)
            if f == "TT_DATA":
                self.tt_data_col = i
                self.teachertable.hideColumn(i)
                # Set up the week table
                self.editors[f].widgets["AVAILABLE"].setup()
        # Initialize the teacher table
        self.fill_teacher_table()

    def fill_teacher_table(self):
        """Set filter and sort criteria, then populate table."""
        self.teachermodel.setSort(
            self.teachermodel.fieldIndex("SORTNAME"),
            Qt.AscendingOrder,
        )
        # print("SELECT:", self.teachermodel.selectStatement())
        self.teachermodel.select()
        self.teachertable.selectRow(0)
        if not self.teachertable.currentIndex().isValid():
            self.teacher_changed(None, None)
        self.teachertable.resizeColumnsToContents()

    def teacher_changed(self, new, old):
        if new:
            self.table_empty = False
            row = new.row()
            # print("CURRENT", old.row(), "->", row)
            record = self.teachermodel.record(row)
            for f, t in TEACHER_COLS:
                self.editors[f].setText(str(record.value(f)))
        else:
            # e.g. when entering an empty table
            self.table_empty = True
            # print("EMPTY TABLE")
            for f, t in TEACHER_COLS:
                self.editors[f].setText("")
        self.form_change_set = set()
        self.form_modified("", False)  # initialize form button states

    def teacher_delete(self):
        """Delete the current teacher."""
        model = self.teachermodel
        if self.form_change_set:
            if not LoseChangesDialog():
                return
        index = self.teachertable.currentIndex()
        row = index.row()
        model.removeRow(row)
        if model.submitAll():
            if row >= model.rowCount():
                row = model.rowCount() - 1
            self.teachertable.selectRow(row)
            if not self.teachertable.currentIndex().isValid():
                self.teacher_changed(None, None)
        else:
            error = model.lastError()
            SHOW_ERROR(error.text())
            model.revertAll()

    def teacher_add(self):
        """Add the data in the form editor as a new teacher."""
        model = self.teachermodel
        index = self.teachertable.currentIndex()
        row0 = index.row()
        row = 0
        model.insertRow(row)
        for f, t in TEACHER_COLS:
            col = model.fieldIndex(f)
            val = self.editors[f].text()
            if f == "TID":
                inserted = val
                icol = col
            model.setData(model.index(row, col), val)
        if model.submitAll():
            # print("INSERTED:", inserted)
            # Try to select the new entry
            for r in range(model.rowCount()):
                if model.data(model.index(r, icol)) == inserted:
                    self.teachertable.selectRow(r)
                    break
            else:
                self.teachertable.selectRow(row0)
        else:
            error = model.lastError()
            SHOW_ERROR(error.text())
            model.revertAll()

    def teacher_update(self):
        """Update the current teacher with the data in the form editor."""
        model = self.teachermodel
        index = self.teachertable.currentIndex()
        teacher = model.data(index)
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
            # print("UPDATED:", teacher)
            for r in range(model.rowCount()):
                if model.data(model.index(r, 0)) == teacher:
                    self.teachertable.selectRow(r)
                    break
            else:
                if row >= model.rowCount():
                    row = model.rowCount() - 1
                self.teachertable.selectRow(row)
        else:
            error = model.lastError()
            SHOW_ERROR(error.text())
            model.revertAll()


class WeekTable(QFrame):
#class WeekTable(QWidget):
    def __init__(self, field, modified, title, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        self.__table = EdiTableWidget()
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(3, 3, 3, 3)

        label = QLabel(f"<h4>{title}</h4>")
        vbox.addWidget(label)
        vbox.addWidget(self.__table)
        self.__modified = modified
        self.__field = field

    # TODO: add validators? (or use appropriate comboboxes for cells?)
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
        self.__table.resizeColumnsToContents()
        # A very dodgy attempt to find an appropriate size for the table
        Hhd = self.__table.horizontalHeader()
        Vhd = self.__table.verticalHeader()
        Hw = Hhd.length()
        Hh = Hhd.sizeHint().height()
        Vw = Vhd.sizeHint().width()
        Vh = Vhd.length()
        self.__table.setMinimumWidth(Hw + Vw + 10)
        self.__table.setFixedHeight(Vh + Hh + 10)
#        self.__table.setMaximumHeight(Vh + Hh + 10)

    def text(self):
        table = self.__table.read_all()
        return "_".join(["".join(row) for row in table])

    def setText(self, text):
        # Set up table
        tdata = []
        daysdata = text.split("_")
        for d in range(self.__table.row_count()):
            ddata = []
            tdata.append(ddata)
            try:
                daydata = daysdata[d]
            except IndexError:
                daydata = ""
            for p in range(self.__table.col_count()):

                # TODO: validate?
                try:
                    ddata.append(daydata[p])
                except IndexError:
                    ddata.append("+")

        self.__table.init_data(tdata)

    def table_changed(self, mod):
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
        #self.setContentsMargins(0, 0, 0, 0)
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
        # print("??? FormSpecialEdit.setText:", text)
        self.text0 = text
        # Set up subwidgets
        data = dict(read_pairs(text))
        for f, t in CONSTRAINT_FIELDS:
            self.widgets[f].setText(data.get(f) or "")
        # print("??? FormSpecialEdit.setText done")

    def form_modified(self, field, changed):
        # print("?????", field, changed)
        if changed:
            if not self.change_set:
                self.__modified(self.__field, True)
            self.change_set.add(field)
        elif self.change_set:
            self.change_set.discard(field)
            if not self.change_set:
                self.__modified(self.__field, False)


# ComboBox delegate?
"""
class ComboBoxItemDelegate : public QStyledItemDelegate
{
    Q_OBJECT
public:
    ComboBoxItemDelegate(QObject *parent = nullptr);
    ~ComboBoxItemDelegate();

    QWidget *createEditor(QWidget *parent, const QStyleOptionViewItem &option, const QModelIndex &index) const override;
    void setEditorData(QWidget *editor, const QModelIndex &index) const override;
    void setModelData(QWidget *editor, QAbstractItemModel *model, const QModelIndex &index) const override;
};

#endif // COMBOBOXITEMDELEGATE_H


File comboboxitemdelegate.cpp


#include "comboboxitemdelegate.h"
#include <QComboBox>

ComboBoxItemDelegate::ComboBoxItemDelegate(QObject *parent)
    : QStyledItemDelegate(parent)
{
}


ComboBoxItemDelegate::~ComboBoxItemDelegate()
{
}


QWidget *ComboBoxItemDelegate::createEditor(QWidget *parent, const QStyleOptionViewItem &option, const QModelIndex &index) const
{
    // Create the combobox and populate it
    QComboBox *cb = new QComboBox(parent);
    const int row = index.row();
    cb->addItem(QString("one in row %1").arg(row));
    cb->addItem(QString("two in row %1").arg(row));
    cb->addItem(QString("three in row %1").arg(row));
    return cb;
}


void ComboBoxItemDelegate::setEditorData(QWidget *editor, const QModelIndex &index) const
{
    QComboBox *cb = qobject_cast<QComboBox *>(editor);
    Q_ASSERT(cb);
    // get the index of the text in the combobox that matches the current value of the item
    const QString currentText = index.data(Qt::EditRole).toString();
    const int cbIndex = cb->findText(currentText);
    // if it is valid, adjust the combobox
    if (cbIndex >= 0)
       cb->setCurrentIndex(cbIndex);
}


void ComboBoxItemDelegate::setModelData(QWidget *editor, QAbstractItemModel *model, const QModelIndex &index) const
{
    QComboBox *cb = qobject_cast<QComboBox *>(editor);
    Q_ASSERT(cb);
    model->setData(index, cb->currentText(), Qt::EditRole);
}



File main.cpp


#include <QApplication>
#include <QTableWidget>

#include "comboboxitemdelegate.h"

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    QTableWidget tw;

    ComboBoxItemDelegate* cbid = new ComboBoxItemDelegate(&tw);
    // ComboBox only in column 2
    tw.setItemDelegateForColumn(1, cbid);
    tw.setColumnCount(4);
    tw.setRowCount(10);
    tw.resize(600,400);
    tw.show();

    return a.exec();
}
"""


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from ui.ui_base import run

    widget = Teachers()
    widget.enter()
    widget.resize(1000, 550)
    run(widget)
