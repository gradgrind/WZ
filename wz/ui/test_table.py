# -*- coding: utf-8 -*-
import sys
from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._data[0])


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.table = QtWidgets.QTableView()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()

        data = [
          ['FIELD1', 'VALUE1'],
          ['FIELD2', 'VALUE2'],
          ['FIELD3', 'VALUE3'],
          ['FIELD4_D', '2021-02-08'],
          ['FIELD5', 'VALUE5'],
        ]

        self.model = TableModel(data)
        self.table.setModel(self.model)

        self.setCentralWidget(self.table)


app=QtWidgets.QApplication(sys.argv)
window=MainWindow()
window.show()
app.exec_()