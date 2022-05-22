import sys, os
this = sys.path[0]
appdir = os.path.dirname(this)
sys.path[0] = appdir
#basedir = os.path.dirname(appdir)
from core.base import start

from ui.ui_base import (
    QStyledItemDelegate, QTableWidget, QTableWidgetItem, run, QComboBox,
    Qt,
    QLineEdit, QCompleter, QTimer, QDialog,
    QAbstractItemView
)

class ComboBoxItemDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        # Create the combobox and populate it
        cb = QComboBox(parent)
        row = index.row()
        cb.addItem(f"one in row {row}")
        cb.addItem(f"two in row {row}")
        cb.addItem(f"three in row {row}")
        return cb

    def setEditorData(self, editor, index):
        # get the index of the text in the combobox that matches the
        # current value of the item
        currentText = index.data(Qt.EditRole)
        cbIndex = editor.findText(currentText);
        # if it is valid, adjust the combobox
        if cbIndex >= 0:
           editor.setCurrentIndex(cbIndex)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)

class LineEdit(QLineEdit):
    def showEvent(self, event):
        if self.completer() is not None:
            QTimer.singleShot(0, self.completer().complete)
        super().showEvent(event)


class CompleterItemDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        completer = QCompleter(["test", "test2", "alternative", "other", "taste"])
        completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        edit = LineEdit(parent)
        edit.setCompleter(completer)
        return edit

class MyLineEdit(QLineEdit):
    def showEvent(self, event):
        if self.myPopup:
            QTimer.singleShot(0, self.myPopup.exec)
        super().showEvent(event)

class MyItemDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        popup = QDialog(parent)
        popup.setMinimumSize(500, 200)
        edit = MyLineEdit(parent)
        edit.myPopup = popup
        return edit


####### A styled tableview with delete-cell and activate-on-return handling

#class XTableView(QTableView):
#    def keyPressEvent(self, e):
#        key = e.key()
#        i = self.currentIndex()
#        if not self.isPersistentEditorOpen(i):
#            if key == Qt.Key_Return:
#                # start editing
#                self.edit(i)
#                return
#            elif key == Qt.Key_Delete:
#                # clear cell
#                self.model().setData(i, "")
#                return
#        super().keyPressEvent(e)

#    table = XTableView()
#    table.setStyleSheet(
#        """QTableView {
#           selection-background-color: #e0e0ff;
#           selection-color: black;
#        }
#        QTableView::item:focus {
#            selection-background-color: #d0ffff;
#        }
#        """
#    )


class TableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
#        self.activated.connect(self.do_activated)
        self.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.AnyKeyPressed
            | QAbstractItemView.EditTrigger.SelectedClicked # this one has a delay!
        )
# Note that the <Return> key doesn't cause the editor to be opened ...
# Event handling may be necessary for that ... but see below!

    def do_activated(self):
        i = self.currentItem()
        print("Activated", self.currentRow(), self.currentColumn())
        # Note that there must be a TableWidgetItem installed on the
        # cell for this to work!
        if self.state() != self.EditingState:
            self.editItem(self.currentItem())

    def keyPressEvent(self, e):
        key = e.key()
        if key == Qt.Key_Return and self.state() != self.EditingState:
            self.editItem(self.currentItem())
        else:
            super().keyPressEvent(e)


tw = TableWidget()

cbid = ComboBoxItemDelegate(tw)
cpid = CompleterItemDelegate(tw)
myid = MyItemDelegate(tw)
# ComboBox only in column 2
tw.setItemDelegateForColumn(1, cbid)
# Completer only in column 3
tw.setItemDelegateForColumn(2, cpid)
# My delegate only in column 4
tw.setItemDelegateForColumn(3, myid)
ncols, nrows = 4, 10
tw.setColumnCount(ncols)
tw.setRowCount(nrows)
for r in range(nrows):
    for c in range(ncols):
        twi = QTableWidgetItem()
        tw.setItem(r, c, twi)
tw.resize(600,400)
run(tw)

quit(0)
