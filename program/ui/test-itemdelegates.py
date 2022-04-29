import sys, os
this = sys.path[0]
appdir = os.path.dirname(this)
sys.path[0] = appdir
#basedir = os.path.dirname(appdir)
from core.base import start

from ui.ui_base import (
    QStyledItemDelegate, QTableWidget, run, QComboBox, Qt,
    QLineEdit, QCompleter, QTimer, QDialog
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







tw = QTableWidget()

cbid = ComboBoxItemDelegate(tw)
cpid = CompleterItemDelegate(tw)
myid = MyItemDelegate(tw)
# ComboBox only in column 2
tw.setItemDelegateForColumn(1, cbid)
# Completer only in column 3
tw.setItemDelegateForColumn(2, cpid)
# My delegate only in column 4
tw.setItemDelegateForColumn(3, myid)
tw.setColumnCount(4)
tw.setRowCount(10)
tw.resize(600,400)
run(tw)

quit(0)
