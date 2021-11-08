# -*- coding: utf-8 -*-
"""
ui/datatable_widget.py

Last updated:  2021-11-08

Gui editor widget for "DataTables".
See datatable-editor.py for an app which can be used for testing this
widget.

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
# Could I share the undo/redo system? At present, the shortcuts only work
# when the table is focussed.

from qtpy.QtWidgets import QSizePolicy, QSplitter, \
        QScrollArea, QWidget, QGridLayout, QLabel, QLineEdit
from qtpy.QtCore import Qt, QSize

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
        self.setWidgetResizable(True)

    def init(self, info, dataTableEditor):
        contents = QWidget()
        contents.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        gridLayout = QGridLayout(contents)
        self.info = []
        r = 0
        for key, val in info.items():
            if key[0] != '_':
                gridLayout.addWidget(QLabel(key), r, 0, 1, 1)
                lineEdit = TextLine(r, dataTableEditor)
                lineEdit.set(val)
                gridLayout.addWidget(lineEdit, r, 1, 1, 1)
                self.info.append([key, lineEdit])
                r += 1
        self.setWidget(contents)
        # Extra height may be needed to avoid a scrollbar:
        h = contents.size().height() + 2
        self.setMaximumHeight(h)
        return h

    def get_info(self):
        return [(key, w.text()) for key, w in self.info]


class DataTableEditor(QSplitter):
    def __init__(self, on_changed = None):
        # Set up handler for "change of changed" notification
        self.modified = on_changed if on_changed else self.__modified
        super().__init__()
        self.setOrientation(Qt.Vertical)
        self.setChildrenCollapsible(False)
        self.info = InfoTable()
        self.addWidget(self.info)

        self.table = EdiTableWidget()
        self.table.horizontalHeader().setStyleSheet("QHeaderView::section{" \
            "background-color:#FFFF80;" \
            "padding: 2px;" \
            "border: 1px solid #808080;" \
            "border-bottom: 2px solid #0000C0;" \
        "}")
        self.addWidget(self.table)

        self.setStretchFactor(0, 0)
        self.setStretchFactor(1, 1)
        self.setHandleWidth(20)

    def __modified(self, mod):
        """Dummy method for "change of changed" notification.
        <mod> is true/false.
        """
        #print(f"** MODIFIED: {mod} **")
        pass

#TODO?
    def reset_modified(self):
        """Reset the modified state of the data.
        """
        self.table.reset_modified()
        self.modified(False)

    def open_table(self, datatable):
        """Read in a DataTable from the given path.
        """
#TODO: If it is done within another application, there might be translated headers
# (calling for <filter_DataTable(data, fieldlist, infolist, extend = True)>).
        self.__info = datatable['__INFO__']
        self.__columns = datatable['__FIELDS__']
        self.__rows = datatable['__ROWS__']

        h = self.info.init(self.__info, self)
        self.setSizes([h, 0])

        data = []
        for row in self.__rows:
            rowdata = []
            data.append(rowdata)
            c = 0
            for h in self.__columns:
                rowdata.append(row[h])
                c += 1
        self.table.setup(colheaders = self.__columns,
                undo_redo = True, row_add_del = True,
                cut = True, paste = True,
                on_changed = self.modified)
        self.table.init_data(data)
        self.table.resizeColumnsToContents()

    def get_data(self):
        """Read the data from the widget. Return it as a "datatable".
        """
        for key, val in self.info.get_info():
            self.__info[key] = val
        self.__rows = []
        for row in self.table.table_data:
            rowdata = {}
            c = 0
            for hdr in self.__columns:
                rowdata[hdr] = row[c]
                c += 1
            self.__rows.append(rowdata)
        return {
            '__INFO__': self.__info,
            '__FIELDS__': self.__columns,
            '__ROWS__': self.__rows
        }
