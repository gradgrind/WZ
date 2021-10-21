# -*- coding: utf-8 -*-
"""
ui/datatable_widget.py

Last updated:  2021-10-21

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

#TODO: Callback for modification of info items – separate from main table?
# Undo/redo for info items?

from PySide6.QtWidgets import QSizePolicy, QSplitter, \
        QScrollArea, QWidget, QGridLayout, QLabel, QLineEdit
from PySide6.QtCore import Qt, QSize

from ui.editable import EdiTableWidget
from tables.spreadsheet import Spreadsheet, read_DataTable

### -----

class TextLine(QLineEdit):
    def __init__(self, index, dataTableEditor):
        self.index = index
        self.dataTableEditor = dataTableEditor
        super().__init__()
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.__text = ''
#        self.textEdited.connect(self.newtext)
        self.editingFinished.connect(self.newtext)

    def set(self, text):
        self.setText(text)
        self.__text = text

    def newtext(self):
        text = self.text()
        if text != self.__text:
            self.__text = text
            self.dataTableEditor.modified(True)


class InfoTable(QScrollArea):
    def __init__(self):
        super().__init__()
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(False)
        self.setSizePolicy(sizePolicy)
        self.setWidgetResizable(True)

    def init(self, info, dataTableEditor):
        contents = QWidget()
        gridLayout = QGridLayout(contents)
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
    def __init__(self):
        super().__init__()
        self.setOrientation(Qt.Vertical)
        self.info = InfoTable()
        self.addWidget(self.info)

        self.table = EdiTableWidget()
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(1)
        sizePolicy1.setHeightForWidth(False)
        self.table.setSizePolicy(sizePolicy1)
        self.addWidget(self.table)

    def modified(self, mod):
        """Indicate data changed.
        """
        print(f"** MODIFIED: {mod} **")

    def open_table(self, datatable):
        """Read in a DataTable from the given path.
        """
#TODO: If it is done within another application, there might be translated headers
# (calling for <filter_DataTable(data, fieldlist, infolist, extend = True)>).
        info = datatable['__INFO__']
        columns = datatable['__FIELDS__']
        rows = datatable['__ROWS__']

        self.info.init(info, self)
        self.table.setColumnCount(len(columns))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels(columns)
        data = []
        for row in rows:
            rowdata = []
            data.append(rowdata)
            c = 0
            for h in columns:
                rowdata.append(row[h])
                c += 1
        self.table.setup(colheaders = columns,
                undo_redo = True, row_add_del = True,
                cut = True, paste = True,
                on_changed = self.modified)
        self.table.init_data(data)
        self.table.resizeColumnsToContents()
