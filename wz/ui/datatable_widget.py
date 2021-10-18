# -*- coding: utf-8 -*-
"""
ui/datatable_widget.py

Last updated:  2021-10-16

Gui editor widget for "DataTables".

=+LICENCE=================================
Copyright 2021 Michael Towers

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

=-LICENCE=================================
"""

### Messages
_OPEN_FILE          = "Tabellendatei öffnen"
_SAVE_FILE          = "Tabellendatei speichern"
_OPEN_TABLETYPE     = "Tabellendatei"
#_NOT_DATATABLE        = "Keine Tabellendatei: {filepath}"

########################################################################

from PySide6.QtWidgets import QSizePolicy, QSplitter, \
        QScrollArea, QWidget, QGridLayout, QLabel, QLineEdit
from PySide6.QtCore import Qt, Signal, QSize

from ui.table import TableWidget
from tables.spreadsheet import Spreadsheet, read_DataTable

### -----

#class TsvError(Exception):
#    pass

###

#TODO: Add/delete columns? Rather not ...
# Undo/redo?

class InfoTable0(TableWidget):
    def __init__(self):
        super().__init__()
        self.setup(#row_add_del = True,
                # column_add_del = True,
                #cut = True,
                paste = True)
        self.setSelectionMode(self.NoSelection)
#?
        self.setMinimumSize(0, 30)

        sizePolicy0 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        sizePolicy0.setHorizontalStretch(0)
        sizePolicy0.setVerticalStretch(1)
        sizePolicy0.setHeightForWidth(False)
        self.setSizePolicy(sizePolicy0)
        self.setRowCount(1)
        self.setColumnCount(1)

        self.horizontalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
#
    def sizeHint(self):
        h = 4
        for r in range(self.rowCount()):
            h += self.rowHeight(r)
        return QSize(0, h)


class TextLine(QLineEdit):
    def __init__(self, index, dataTableEditor):
        self.index = index
        self.dataTableEditor = dataTableEditor
        super().__init__()
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.__text = ''
#        self.textEdited.connect(self.newtext)
        self.editingFinished.connect(self.newtext)
#
    def set(self, text):
        self.setText(text)
        self.__text = text
#
#    def newtext(self, text):
#        self.dataTableEditor.modified.emit(0, self.index, 1, text)
    def newtext(self):
        text = self.text()
        if text != self.__text:
            self.__text = text
            self.dataTableEditor.modified.emit(0, self.index, 1, text)


class InfoTable(QScrollArea):
    def __init__(self):
        super().__init__()

#?        self.setMinimumSize(0, 30)

        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(False)
        self.setSizePolicy(sizePolicy)
        self.setWidgetResizable(True)
#
    def init(self, info, dataTableEditor):
        contents = QWidget()
        gridLayout = QGridLayout(contents)
#        self.contents.setGeometry(QRect(0, 0, 597, 96))
        self.info = []
        r = 0
        for key, val in info.items():
            if key[0] != '_':
                gridLayout.addWidget(QLabel(key), r, 0, 1, 1)
                lineEdit = TextLine(0, dataTableEditor)
                lineEdit.set(val)
                gridLayout.addWidget(lineEdit, r, 1, 1, 1)
                self.info.append([key, lineEdit])
                r += 1
        self.setWidget(contents)


class DataTableEditor(QSplitter):
    modified = Signal(int, int, int, str)
    #+
    def __init__(self):
        super().__init__()
        self.setOrientation(Qt.Vertical)
        self.info = InfoTable()
        self.addWidget(self.info)

        self.table = TableWidget()
        self.table.setup(row_add_del = True,
                # column_add_del = True,
                cut = True, paste = True)
        self.table.setSelectionMode(self.table.ContiguousSelection)

        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(1)
        sizePolicy1.setHeightForWidth(False)
        self.table.setSizePolicy(sizePolicy1)
        self.addWidget(self.table)

#        self.info.cellChanged.connect(self.info_cell_changed)
        self.table.cellChanged.connect(self.table_cell_changed)
#---?
        self.modified.connect(self.__modified)
#
    def __modified(self, table, row, column, val):
        print("§§§", table, row, column, val)
#
#    def info_cell_changed(self, row, column):
#        """Indicate data changed.
#        """
#        self.modified.emit(0, row, column, self.info.get_text(row, column))
#
    def table_cell_changed(self, row, column):
        """Indicate data changed.
        """
        self.modified.emit(1, row, column, self.table.get_text(row, column))
#
    def open_table(self, datatable):
        """Read in a DataTable from the given path.
        """
#TODO: If it is done within another application, there might be translated headers
# (calling for <filter_DataTable(data, fieldlist, infolist, extend = True)>).
        info = datatable['__INFO__']
        columns = datatable['__FIELDS__']
        rows = datatable['__ROWS__']

        self.info.init(info, self)
# Setting the height of the info table is a bit of a problem
# (a weakness/bug in qt?). Consider using a grid of label / textedit pairs,
# perhaps with the ability to hide them (groupbox?)
#        self.info.setRowCount(len(info))
#        self.info.setVerticalHeaderLabels(info)
#        r = 0
#        for val in info.values():
#            self.info.set_text(r, 0, val)
#            r += 1
#        print("???", self.info.rowHeight(0), self.info.sizeHint())

        self.table.setColumnCount(len(columns))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels(columns)
        r = 0
        for row in rows:
            c = 0
            for h in columns:
                self.table.set_text(r, c, row[h])
                c += 1
            r += 1
        self.table.resizeColumnsToContents()
