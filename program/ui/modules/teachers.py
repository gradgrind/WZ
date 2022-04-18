"""
ui/modules/teachers.py

Last updated:  2022-04-18

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

#TODO: get from db? info table?
DAYS = [1,2,3,4,5]

### Messages

### Labels
_NAME = "Lehrkräfte"
_TITLE = "Lehrerdaten verwalten"

#TODO? ...
# Teacher field editor buttons
_DELETE = "Löschen"
_UPDATE = "Übernehmen"
_NEW = "Hinzufügen"
_COPY_NEW = "Neu (Kopie)"

# Teacher table fields
TEACHER_COLS = [
    ("TID", "Kürzel"),
    ("NAME", "Name"),
    ("FULLNAME", "Vollname"),
    ("SORTNAME", "Sortiername"),
    ("TT_DATA", "Stundenplandaten"),
]

# Lesson table
_LESSONS = "Verfügbarkeit"

_DAY = "Tag"
#TODO: The period tags are in a configuration file? Or in the database?

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
    from ui.ui_base import StandalonePage as Page
    from core.base import start

    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    #    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))
else:
    from ui.ui_base import StackPage as Page

### +++++

from utility.db_management import open_database, db_key_value_list

from ui.ui_base import (
    HLine,
    LoseChangesDialog,
    TableViewRowSelect,
    FormLineEdit,
    # QtWidgets
    QSplitter,
    QFrame,
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

### -----


def init():
    MAIN_WIDGET.add_tab(Teachers())


class Teachers(Page):
    name = _NAME
    title = _TITLE

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
            editwidget = FormLineEdit(f, self.form_modified)
            self.editors[f] = editwidget
            if f != "TT_DATA":
                self.teachereditor.addRow(t, editwidget)

        hbox2 = QHBoxLayout()
        vbox2.addLayout(hbox2)
        hbox2.addStretch(1)
        self.teacher_delete_button = QPushButton(_DELETE)
        self.teacher_delete_button.clicked.connect(self.teacher_delete)
        hbox2.addWidget(self.teacher_delete_button)
        self.teacher_update_button = QPushButton(_UPDATE)
        self.teacher_update_button.clicked.connect(self.teacher_update)
        hbox2.addWidget(self.teacher_update_button)
        self.teacher_add_button = QPushButton(_NEW)
        self.teacher_add_button.clicked.connect(self.teacher_add)
        hbox2.addWidget(self.teacher_add_button)

        vbox2.addWidget(HLine())

#TODO: constraint fields ...

        lessonbox = QFrame()
        vbox2.addWidget(lessonbox)
        vbox3 = QVBoxLayout(lessonbox)
        vbox3.setContentsMargins(0, 0, 0, 0)
        vbox3.addWidget(QLabel(f"<h4>{_LESSONS}</h4>"))

        # The lesson table
# Rather use an "editable", or a simplified version? With validation?
        self.weektable = EdiTableWidget()
#        self.lessontable = QTableView()
#        self.lessontable.setSelectionMode(QTableView.SingleSelection)
#        self.lessontable.setSelectionBehavior(QTableView.SelectRows)

#        self.weektable.verticalHeader().hide()

        vbox3.addWidget(self.weektable)

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
#?                if not self.form_change_set.intersection(COURSE_KEY_FIELDS):
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

#        self.lessontable.setModel(None)

        self.teachermodel = QSqlTableModel()
        self.teachermodel.setTable("TEACHERS")
        self.teachermodel.setEditStrategy(QSqlTableModel.OnManualSubmit)
        # Set up the teacher view
        self.teachertable.setModel(self.teachermodel)
        selection_model = self.teachertable.selectionModel()
        selection_model.currentChanged.connect(self.teacher_changed)
        for f, t in TEACHER_COLS:
            i = self.teachermodel.fieldIndex(f)
#            editwidget = self.editors[f]
            self.teachermodel.setHeaderData(i, Qt.Horizontal, t)
            if f == "TT_DATA":
                self.tt_data_col = i
                self.teachertable.hideColumn(i)

        # Set up the week table
        self.tt_days = db_key_value_list("TT_DAYS", "N", "NAME", "N")
        self.tt_periods = db_key_value_list("TT_PERIODS", "N", "TAG", "N")
        self.weektable.setup(
            colheaders=[p[1] for p in self.tt_periods],
            rowheaders=[d[1] for d in self.tt_days],
            undo_redo=False,
            cut=False,
            paste=True,
            row_add_del=False,
            column_add_del=False,
            on_changed=None,
        )
        self.weektable.resizeColumnsToContents()
        hh = self.weektable.horizontalHeader().length()
        vh = self.weektable.verticalHeader().sizeHint().width()
        self.weektable.setMinimumWidth(hh + vh + 10)

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
            self.set_teacher(record.value(0))
        else:
            # e.g. when entering an empty table
            self.table_empty = True
            # print("EMPTY TABLE")
            for f, t in TEACHER_COLS:
                self.editors[f].setText("")
            self.editors[self.filter_field].setText(self.filter_value)
            self.set_teacher(0)
        self.form_change_set = set()
        self.form_modified("", False)  # initialize form button states

    def teacher_delete(self):
        """Delete the current teacher."""
        model = self.teachermodel
        if self.form_change_set:
            if not LoseChangesDialog():
                return
        # teacher = self.editors["teacher"].text()
        index = self.teachertable.currentIndex()
        row = index.row()
        model.removeRow(row)
        if model.submitAll():
            # The LESSONS table should have its "teacher" field (foreign
            # key) defined as "ON DELETE CASCADE" to ensure that when
            # a teacher is deleted also the lessons are removed.
            # print("DELETED:", teacher)
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
        for f, t in TEACHER_COLS[1:]:
            col = model.fieldIndex(f)
            val = self.editors[f].text()
            model.setData(model.index(row, col), val)
        if model.submitAll():
            teacher = model.query().lastInsertId()
            # print("INSERTED:", teacher)
            for r in range(model.rowCount()):
                if model.data(model.index(r, 0)) == teacher:
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

    def set_teacher(self, teacher):
        # print("SET TEACHER:", teacher)
        self.this_teacher = teacher
#TODO
        tt_data = self.editors["TT_DATA"].text()
        print("§§§", tt_data)
#? self.tt_data_col ... perhaps not needed
# Use a special "editor widget" to handle the tt data?
        return

        # print("SELECT:", self.lessonmodel.selectStatement())
        self.lessonmodel.select()
        self.lessontable.selectRow(0)
        self.lessontable.resizeColumnsToContents()
        # Enable or disable lesson butttons
        if self.lessonmodel.rowCount():
            self.lesson_delete_button.setEnabled(True)
        else:
            self.lesson_delete_button.setEnabled(False)
        self.lesson_add_button.setEnabled(teacher > 0)

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
        if self.this_teacher:
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
                record.setValue(1, self.this_teacher)
                n = 0
            if model.insertRecord(-1, record):
                model.select()  # necessary to make new row immediately usable
                self.lessontable.selectRow(n)
                self.lesson_delete_button.setEnabled(True)
            else:
                SHOW_ERROR(f"DB Error: {model.lastError().text()}")



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
