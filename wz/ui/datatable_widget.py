# -*- coding: utf-8 -*-
"""
ui/datatable_widget.py

Last updated:  2021-11-10

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

### Messages

OPEN_FILE          = "Tabellendatei öffnen"
SAVE_FILE          = "Tabellendatei speichern"
SAVE_FILE_AS       = "Tabellendatei speichern unter"
EXIT               = "Schließen"

########################################################################

from ui.ui_base import get_icon, QSizePolicy, QSplitter, \
        QScrollArea, QWidget, QToolBar, QVBoxLayout, QGridLayout, \
        QLineEdit, QLabel, QAction, QKeySequence, \
        Qt, Qt, QSize, QEvent, QObject

from ui.editable import EdiTableWidget
from tables.spreadsheet import Spreadsheet, read_DataTable

### -----

"""
class ShortcutEater(QObject):
    def eventFilter(self, obj, event):
        if (event.type() == QEvent.KeyPress):
            if event.modifiers() & Qt.ControlModifier:
                #print("Key press Ctrl-%d" % event.key())
                return True
        elif (event.type() == QEvent.ShortcutOverride):
            if event.modifiers() & Qt.ControlModifier:
                #print("Override %d" % event.key())
                event.ignore()
                return True
        # standard event processing
        return QObject.eventFilter(self, obj, event)
shortcutEater = ShortcutEater()
"""

class TextLine(QLineEdit):
    def __init__(self, index, dataTableEditor):
        self.index = index
        self.dataTableEditor = dataTableEditor
        super().__init__()
#        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.__text = ''
#        self.textEdited.connect(self.newtext)
        self.editingFinished.connect(self.newtext)
#        self.installEventFilter(shortcutEater)

    def set(self, text):
        self.setText(text)
        self.__text = text

    def newtext(self):
        text = self.text()
        if text != self.__text:
            self.__text = text
            self.dataTableEditor.modified(True)

    def focusInEvent(self, event):
        self.dataTableEditor.focussed = self.index
        print("FOCUSSED", self.index)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.dataTableEditor.focussed = -1
        print("FOCUSSED", -1)
        super().focusOutEvent(event)

"""
Toolbar:
    copy
    cut
    paste

    only table:
        insert row
        delete row

    undo
    redo


    The basic editor application adds:
        open
        save
        save as
        exit

Need to handle NAME vs. DISPLAY_NAME (translation) somewhere.

Perhaps a new format for the specification tables, using mappings
of field descriptors instead of lists?

TABLE_FIELDS: [
    {NAME: field-name 1, DISPLAY_NAME: tr1, REQUIRED: true}
    {NAME: field-name 2, DISPLAY_NAME: tr2}

]

self.select_all
self.unselect
self.copyCellsAction
self.pasteCellsAction
self.cutCellsAction
self.insertRowAction
self.deleteRowsAction
self.insertColumnAction
self.deleteColumnsAction
self.undoAction
self.redoAction
"""

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

#    def focusInEvent(self, event):
#    def focusOutEvent(self, event):
# Can be used to set current info line?

# I would actually need to trigger info shortcuts ... perhaps:
#    eventPress = QKeyEvent(QEvent.KeyPress, Qt.Key_C, Qt.ControlModifier)
#    eventRealease = QKeyEvent(QEvent.KeyRelease, Qt.Key_C, Qt.ControlModifier)
#    QApplication.postEvent(targetWidget, eventPress)
#    QApplication.postEvent(targetWidget, eventRealease)

#class DataTableEditor(QSplitter):
class DataTableEditor(QWidget):
    def new_action(self, icon, text, shortcut):
        action = QAction(self)
        if shortcut:
            text += f" – [{shortcut.toString()}]"
            action.setShortcut(shortcut)
        action.setText(text)
        action.setIcon(get_icon(icon))
        return action

    def __init__(self, on_exit = None,
            on_open = None, on_save = None, on_save_as = None):
        super().__init__()
        vbox = QVBoxLayout(self)
        self.toolbar = QToolBar()
        vbox.addWidget(self.toolbar)
        # File QActions
        if on_open:
            self.action_open = self.new_action('open', OPEN_FILE,
                    QKeySequence(Qt.CTRL + Qt.Key_O))
            self.action_open.triggered.connect(on_open)
            self.toolbar.addAction(self.action_open)
        if on_save:
            self.action_save = self.new_action('save', SAVE_FILE,
                QKeySequence(Qt.CTRL + Qt.Key_S))
            self.action_save.triggered.connect(on_save)
            self.toolbar.addAction(self.action_save)
        if on_save_as:
            self.action_save_as = self.new_action('saveas', SAVE_FILE_AS,
                QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_S))
            self.action_save_as.triggered.connect(on_save_as)
            self.toolbar.addAction(self.action_save_as)
        # Exit QAction
        if on_exit:
            self.toolbar.addSeparator()
            self.exit_action = self.new_action('quit', EXIT,
                    QKeySequence(Qt.CTRL + Qt.Key_Q))
            self.exit_action.triggered.connect(on_exit)
            self.toolbar.addAction(self.exit_action)

        self.splitter = QSplitter()
        vbox.addWidget(self.splitter)
        self.splitter.setOrientation(Qt.Vertical)
        self.splitter.setChildrenCollapsible(False)
        self.info = InfoTable()
        self.splitter.addWidget(self.info)

        self.table = EdiTableWidget()
        self.table.horizontalHeader().setStyleSheet("QHeaderView::section{" \
            "background-color:#FFFF80;" \
            "padding: 2px;" \
            "border: 1px solid #808080;" \
            "border-bottom: 2px solid #0000C0;" \
        "}")
        self.splitter.addWidget(self.table)

        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setHandleWidth(20)

    def modified(self, mod):
        """Dummy method for "change of changed" notification.
        <mod> is true/false.
        OVERRIDE this to customize behaviour.
        """
        print(f"** MODIFIED: {mod} **")

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
        self.splitter.setSizes([h, 0])
        self.focussed = -1      # index of currently "focussed" info entry

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
