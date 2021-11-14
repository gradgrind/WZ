# -*- coding: utf-8 -*-
"""
ui/datatable_widget.py

Last updated:  2021-11-14

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

### Messages

OPEN_FILE          = "Tabellendatei öffnen"
SAVE_FILE          = "Tabellendatei speichern"
SAVE_FILE_AS       = "Tabellendatei speichern unter"
EXIT               = "Schließen"

########################################################################

from ui.ui_base import APP, get_icon, QSizePolicy, QSplitter, \
        QScrollArea, QWidget, QToolBar, QVBoxLayout, QGridLayout, \
        QLineEdit, QLabel, QAction, QKeySequence, \
        Qt, QSize, QEvent, QObject, QKeyEvent

from ui.editable import EdiTableWidget, Change_X
from tables.spreadsheet import Spreadsheet, read_DataTable

Change_INFO = Change_X

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

#TODO: validation?
class TextLine(QLineEdit):
    def __init__(self, index, dataTableEditor):
        self.index = index
        self.dataTableEditor = dataTableEditor
        super().__init__()
#        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.__text = ''
#        self.textEdited.connect(self.text_changed)
        self.editingFinished.connect(self.newtext)
#        self.installEventFilter(shortcutEater)

    def set(self, text):
        self.setText(text)
        self.__text = text

    def newtext(self):
        text = self.text()
        self.setText(text)  # reset internal undo/modified mechanism
        if text != self.__text:
            self.dataTableEditor.changed(self.index, self.__text, text)
            self.__text = text

    def focusInEvent(self, event):
        self.dataTableEditor.set_focussed(self.index)
        #print("FOCUSSED", self.index)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.dataTableEditor.set_focussed(-1)
        #print("FOCUSSED", -1)
        super().focusOutEvent(event)

    def mousePressEvent(self, event):
        event.accept()
        self.selectAll()
        return

"""
Need to handle NAME vs. DISPLAY_NAME (translation) somewhere.

Perhaps a new format for the specification tables, using mappings
of field descriptors instead of lists?

TABLE_FIELDS: [
    {NAME: field-name 1, DISPLAY_NAME: tr1, REQUIRED: true}
    {NAME: field-name 2, DISPLAY_NAME: tr2}

]
"""

class InfoTable(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)

    def init(self, info, dataTableEditor, names):
        contents = QWidget()
        contents.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        gridLayout = QGridLayout(contents)
        self.info = []
        r = 0
        for key, val in info.items():
            if key[0] != '_':
                try:
                    n = names[key]
                except:
                    n = key
                gridLayout.addWidget(QLabel(n), r, 0, 1, 1)
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

    def set_item(self, index, val):
        self.info[index][1].set(val)


def send_control_key(key, widget):
    eventPress = QKeyEvent(QEvent.KeyPress, key, Qt.ControlModifier)
    eventRealease = QKeyEvent(QEvent.KeyRelease, key, Qt.ControlModifier)
    APP.postEvent(widget, eventPress)
    APP.postEvent(widget, eventRealease)


class TableWidget(EdiTableWidget):
    def __init__(self, dteditor):
        super().__init__()
        self.dteditor = dteditor

    def undoredo_extension(self, undo, chtype, change):
        """Handle undo/redo for changes to info entries.
        Overrides base class method.
        """
        if chtype == Change_INFO:
            val = change[1] if undo else change[2]
            self.dteditor.info.set_item(change[0], val)
            #print("UNDO-REDO", undo, chtype, change)
            return True
        return False

    def copyCellsToClipboard(self):
        """Overrides base class method.
        """
        if self.hasFocus():
            super().copyCellsToClipboard()
        else:
            send_control_key(Qt.Key_C, APP.focusWidget())

    def cutCellsToClipboard(self):
        """Overrides base class method.
        """
        if self.hasFocus():
            super().cutCellsToClipboard()
        else:
            send_control_key(Qt.Key_X, APP.focusWidget())

    def pasteCellFromClipboard(self):
        """Overrides base class method.
        """
        if self.hasFocus():
            super().pasteCellFromClipboard()
        else:
            send_control_key(Qt.Key_V, APP.focusWidget())




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

        self.splitter = QSplitter()
        vbox.addWidget(self.splitter)
        self.splitter.setOrientation(Qt.Vertical)
        self.splitter.setChildrenCollapsible(False)
        self.info = InfoTable()
        self.splitter.addWidget(self.info)

        self.table = TableWidget(self)
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

        ### Actions from table widget
        self.toolbar.addSeparator()
        self.table.copyCellsAction.setIcon(get_icon('copy'))
        self.toolbar.addAction(self.table.copyCellsAction)
        self.table.cutCellsAction.setIcon(get_icon('cut'))
        self.toolbar.addAction(self.table.cutCellsAction)
        self.table.pasteCellsAction.setIcon(get_icon('paste'))
        self.toolbar.addAction(self.table.pasteCellsAction)

        self.toolbar.addSeparator()
        self.table.insertRowAction.setIcon(get_icon('insertrowsafter'))
        self.toolbar.addAction(self.table.insertRowAction)
        self.table.deleteRowsAction.setIcon(get_icon('deleterows'))
        self.toolbar.addAction(self.table.deleteRowsAction)
        self.table.insertColumnAction.setIcon(get_icon('insertcolumnsafter'))
        self.toolbar.addAction(self.table.insertColumnAction)
        self.table.deleteColumnsAction.setIcon(get_icon('deletecolumns'))
        self.toolbar.addAction(self.table.deleteColumnsAction)

        self.toolbar.addSeparator()
        self.table.undoAction.setIcon(get_icon('undo'))
        self.toolbar.addAction(self.table.undoAction)
        self.table.redoAction.setIcon(get_icon('redo'))
        self.toolbar.addAction(self.table.redoAction)


        # Exit QAction
        if on_exit:
            self.toolbar.addSeparator()
            self.exit_action = self.new_action('quit', EXIT,
                    QKeySequence(Qt.CTRL + Qt.Key_Q))
            self.exit_action.triggered.connect(on_exit)
            self.toolbar.addAction(self.exit_action)

    def changed(self, index, old, new):
        self.table.add_change(Change_INFO, (index, old, new))

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
        """Read in a DataTable.
        """
#TODO: If it is done within another application, there might be translated headers
# (calling for <filter_DataTable(data, fieldlist, infolist, extend = True)>).
        self.__info = datatable['__INFO__']
        self.__columns = datatable['__FIELDS__']
        self.__rows = datatable['__ROWS__']
        # "Translations" of the field names:
        self.__column_titles = datatable.get('__FIELD_NAMES__')
        headers = []
        for h in self.__columns:
            try:
                headers.append(self.__column_titles[h])
            except:
                headers.append(h)
        self.__info_titles = datatable.get('__INFO_NAMES__')
        h = self.info.init(self.__info, self, self.__info_titles)
        self.splitter.setSizes([h, 0])
        self.set_focussed(-1)   # index of currently "focussed" info entry

        data = []
        for row in self.__rows:
            rowdata = []
            data.append(rowdata)
            c = 0
            for h in self.__columns:
                rowdata.append(row[h])
                c += 1
        self.table.setup(colheaders = headers,
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

    def set_focussed(self, index):
        if index >= 0:
            self.table.clearSelection()
