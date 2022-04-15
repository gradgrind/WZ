# Add a table to a QDocument to print it ... probably not useful, but
# may be interesting for something. It doesn't include headers.

from PyQt5 import QtWidgets, QtCore, QtPrintSupport, QtGui

class Window(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.setWindowTitle(self.tr('Document Printer'))
        self.table = QtWidgets.QTableWidget(200, 5, self)

        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = QtWidgets.QTableWidgetItem('(%d, %d)' % (row, col))
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.table.setItem(row, col, item)
        self.table.setHorizontalHeaderLabels(
            'SKU #|NAME|DESCRIPTION|QUANTITY|PRICE'.split('|'))
        self.buttonPrint = QtWidgets.QPushButton('Print', self)
        self.buttonPrint.clicked.connect(self.handlePrint)
        self.buttonPreview = QtWidgets.QPushButton('Preview', self)
        self.buttonPreview.clicked.connect(self.handlePreview)
        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(self.table, 0, 0, 1, 2)
        layout.addWidget(self.buttonPrint, 1, 0)
        layout.addWidget(self.buttonPreview, 1, 1)

    def handlePrint(self):
        dialog = QtPrintSupport.QPrintDialog()
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.handlePaintRequest(dialog.printer())

    def handlePreview(self):
        dialog = QtPrintSupport.QPrintPreviewDialog()
        dialog.paintRequested.connect(self.handlePaintRequest)
        dialog.exec_()

    def handlePaintRequest(self, printer):
        document = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(document)
        table = cursor.insertTable(
            self.table.rowCount(), self.table.columnCount())
        for row in range(table.rows()):
            for col in range(table.columns()):
                cursor.insertText(self.table.item(row, col).text())
                cursor.movePosition(QtGui.QTextCursor.NextCell)
        document.print_(printer)

    """def handlePaintRequest(self, printer):
        tableFormat = QtGui.QTextTableFormat()
        tableFormat.setBorder(0.5)
        tableFormat.setBorderStyle(3)
        tableFormat.setCellSpacing(0);
        tableFormat.setTopMargin(0);
        tableFormat.setCellPadding(4)
        document = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(document)
        table = cursor.insertTable(
            self.table.rowCount(), self.table.columnCount(), tableFormat)
        for row in range(table.rows()):
            for col in range(table.columns()):
                cursor.insertText(self.table.item(row, col).text())
                cursor.movePosition(QtGui.QTextCursor.NextCell)
        document.print_(printer)
    """

if __name__ == '__main__':

    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.resize(640, 480)
    window.show()
    sys.exit(app.exec_())
