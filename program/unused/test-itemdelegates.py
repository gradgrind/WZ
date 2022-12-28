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
    QAbstractItemView,
    QColor,
    QHeaderView,
    QSize,
    QRect,
)


class RotatedHeaderView(QHeaderView):
    """Rotate header items by 90°.
    I think the header texts must be set before assigning a header
    instance to the table widget.
    """
    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        #self.setDefaultAlignment(Qt.AlignLeft)
        #self._font = QtGui.QFont("helvetica", 15)
        #self._metrics = QtGui.QFontMetrics(self._font)
        self._metrics = self.fontMetrics()
        self._descent = self._metrics.descent()
        self._margin = 10

    def _paintSection(self, painter, rect, index):
        # This version has no border
        data = self._get_data(index)
        painter.rotate(-90)
        #painter.setFont(self._font)
        painter.drawText(
            - rect.height() + self._margin,
            int(rect.left() + (rect.width() + self._descent) / 2),
            data
        )

    def paintSection(self, painter, rect, index):
        # Has problems with the border
        painter.save()
        painter.rotate(-90)
        print("???1", rect)
        rect2 = QRect(rect)
        print("???2", rect2)
        rect2.setY(int(rect.left()))
        rect2.setX(- rect.height() + 2) # +2 is an experimental tweak
        rect2.setWidth(rect.height())
        rect2.setHeight(rect.width())
        print("???2+", rect2)
        super().paintSection(painter, rect2, index)
        painter.restore()

    def sizeHint(self):
        return QSize(0, self._get_text_width() + 2 * self._margin)

# Not used by resizeColumnsToContents?
    def sectionSizeHint(self, column):
        return self._metrics.height()

    def _get_text_width(self):
        return max([self._metrics.width(self._get_data(i))
                    for i in range(0, self.model().columnCount())])

    def _get_data(self, index):
        return self.model().headerData(index, self.orientation())

#You can use this class in your view as follows:
# headerView = MyHeaderView()
# tableView.setHorizontalHeader(headerView)


class ReadOnlyDelegate(QStyledItemDelegate):
    def createEditor(self, *args):
        return None


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

#    def setModelData(self, editor, model, index):
#        model.setData(index, editor.currentText(), Qt.EditRole)


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
headerView = RotatedHeaderView()

cbid = ComboBoxItemDelegate(tw)
cpid = CompleterItemDelegate(tw)
myid = MyItemDelegate(tw)
roid = ReadOnlyDelegate(tw)
# ComboBox only in column 2
tw.setItemDelegateForColumn(1, cbid)
# Completer only in column 3
tw.setItemDelegateForColumn(2, cpid)
# My delegate only in column 4
tw.setItemDelegateForColumn(3, myid)
# Column 5 is read-only
tw.setItemDelegateForColumn(4, roid)
ncols, nrows = 5, 10
tw.setColumnCount(ncols)
tw.setRowCount(nrows)

tw.setHorizontalHeaderLabels(("Column 100", "Column 2", "Col 3", "Column 4", "Column 5"))
tw.setHorizontalHeader(headerView)

colours = [
    QColor(255, 200, 230),
    QColor("#EEFFDD"),
    QColor("#ffddee"),
    QColor("#ddeeff"),
    QColor("#eeddff"),
]
for r in range(nrows):
    for c in range(ncols):
        twi = QTableWidgetItem()
        twi.setText(f"({r} | {c})")
#???
        twi.setBackground(colours[c])
        tw.setItem(r, c, twi)

tw.resizeColumnsToContents() # doesn't work – uses header text width?
# Might need to get width of each cell in column (measure text)

print("???", headerView._descent)
for c in range(ncols):
    print("COL", c, headerView.sectionSizeHint(c))

tw.resize(600,400)
run(tw)

quit(0)
