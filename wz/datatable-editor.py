# -*- coding: utf-8 -*-
"""
datatable-editor.py

Last updated:  2021-11-08

Gui editor for "DataTables".

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
PROGRAM_NAME        = "DataTable Editor"
_FILE_MENU          = "Datei"
_OPEN_FILE          = "Tabellendatei öffnen"
_SAVE_FILE          = "Tabellendatei speichern"
_SAVE_FILE_AS       = "Tabellendatei speichern unter"
_EXIT               = "Schließen"
_OPEN_TABLETYPE     = "Tabellendatei"
_INVALID_DATATABLE  = "Ungültige DataTable: {path}\n ... {message}"

_SAVE_AS_TSV        = "Als tsv-Datei speichern?\n\n{path}"
_UNSUPPORTED_SAVE   = "Tabelle speichern – Dateityp '.{ending}'" \
        " wird nicht unterstützt"

_LOSE_CHANGES       = "Es gibt ungespeicherte Änderungen.\n" \
        "Wirklich schließen?"
_LOSE_CHANGES_OPEN  = "Es gibt ungespeicherte Änderungen.\n" \
        "Neue Datei trotzdem öffnen?"
_SAVING_FORMAT      = "Formatierungen werden möglicherweise verloren gehen:" \
        "\n{path}\nÜberschreiben?"


########################################################################

import sys, os, builtins, traceback
if __name__ == '__main__':
    try:
        builtins.PROGRAM_DATA = os.environ['PROGRAM_DATA']
    except KeyError:
        this = sys.path[0]
        basedir = os.path.dirname(this)
        builtins.PROGRAM_DATA = os.path.join(basedir, 'wz-data')

from ui.ui_base import APP, run, openDialog, saveDialog, get_icon, \
        QWidget, QToolBar, QStatusBar, QVBoxLayout, \
        QAction, QKeySequence, Qt

# This seems to deactivate activate-on-single-click in filedialog
# (presumably elsewhere as well?)
APP.setStyleSheet("QAbstractItemView { activate-on-singleclick: 0; }")

from core.base import Dates
from ui.datatable_widget import DataTableEditor as DataTableWidget
from ui.ui_base import openDialog, saveDialog, get_icon
from tables.spreadsheet import Spreadsheet, read_DataTable, TableError, \
        make_DataTable, make_DataTable_filetypes, read_DataTable_filetypes

### -----

class DataTableEditor(QWidget):
    def new_action(self, icon, text, shortcut):
        action = QAction(self)
        if shortcut:
            text += f" – [{shortcut.toString()}]"
            action.setShortcut(shortcut)
        action.setText(text)
        action.setIcon(get_icon(icon))
        return action

    def __init__(self, ofile = None):
        super().__init__()
        icon = get_icon('datatable')
        self.setWindowIcon(icon)
        self.action_open = self.new_action('open', _OPEN_FILE,
                QKeySequence(Qt.CTRL + Qt.Key_O))
        self.action_save = self.new_action('save', _SAVE_FILE,
                QKeySequence(Qt.CTRL + Qt.Key_S))
        self.action_save_as = self.new_action('saveas', _SAVE_FILE_AS,
                QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_S))

        vbox = QVBoxLayout(self)
        toolbar = QToolBar()
        vbox.addWidget(toolbar)
        self.datatable = DataTableWidget(self.modified)
        vbox.addWidget(self.datatable)

        toolbar.addAction(self.action_open)
        toolbar.addAction(self.action_save)
        toolbar.addAction(self.action_save_as)

        # Exit QAction
        toolbar.addSeparator()
        exit_action = self.new_action('quit', _EXIT,
                QKeySequence(Qt.CTRL + Qt.Key_Q))
        exit_action.triggered.connect(self.close)
        toolbar.addAction(exit_action)

        self.action_open.triggered.connect(self.get_file)
        self.action_save.triggered.connect(self.save_file)
        self.action_save_as.triggered.connect(self.save_as_file)

        self.set_current_file(None)
        self.modified(False)
        self.action_save_as.setEnabled(False)
        if ofile:
            self.open_file(ofile)

    def closeEvent(self, event):
        if self.__modified:
            if SHOW_CONFIRM(_LOSE_CHANGES):
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def modified(self, mod):
        print("MOD:", mod)
        self.__modified = mod
        self.action_save.setEnabled(mod)
        self.set_title(mod)

    def set_title(self, changed):
        x = ' *' if changed else ''
        title = f"{PROGRAM_NAME} – {self.filename}{x}" \
                if self.filename else PROGRAM_NAME
        self.setWindowTitle(title)

    def set_current_file(self, path):
        self.current_file = path
        self.filename = os.path.basename(path) if path else None

    def get_file(self):
        if self.__modified and not SHOW_CONFIRM(_LOSE_CHANGES_OPEN):
            return
        filetypes = ' '.join(['*.' + fte
                for fte in Spreadsheet.filetype_endings()])
        ofile = openDialog(f"{_OPEN_TABLETYPE} ({filetypes})", _OPEN_FILE)
        if ofile:
            self.open_file(ofile)

    def open_file(self, filepath):
        """Read in a DataTable from the given path.
        """
        try:
            datatable = read_DataTable(filepath)
        except TableError as e:
            SHOW_ERROR(_INVALID_DATATABLE.format(path = str(filepath),
                    message = str(e)))
            return
        except:
            SHOW_ERROR(f"BUG while reading {str(filepath)}:\n"
                    f" ... {traceback.format_exc()}")
            return
        self.set_current_file(filepath)
        self.datatable.open_table(datatable)
        self.action_save_as.setEnabled(True)
        self.saved = False
        self.modified(False)

    def save_as_file(self):
        endings = make_DataTable_filetypes()
        ftypes = ' '.join(['*.' + e for e in endings])
        filepath = saveDialog(f"{_OPEN_TABLETYPE} ({ftypes})",
                self.currrent_file, _SAVE_FILE)
        if filepath:
            fpath, ending = filepath.rsplit('.', 1)
            if ending in endings:
                data = self.centralwidget.get_data()
                fbytes = make_DataTable(data, ending,
                        __MODIFIED__ = Dates.timestamp())
                with open(filepath, 'wb') as fh:
                    fh.write(fbytes)
                self.currrent_file = filepath
                self.centralwidget.reset_modified()
            else:
                SHOW_ERROR(_UNSUPPORTED_SAVE.format(ending = ending))

    def save_file(self):
        fpath, ending = self.currrent_file.rsplit('.', 1)
        if ending == 'tsv':
            filepath = self.currrent_file
        else:
            if ending in read_DataTable_filetypes():
                filepath = fpath + '.tsv'
            else:
                filepath = self.currrent_file + '.tsv'
            if not SHOW_CONFIRM(_SAVE_AS_TSV.format(path = filepath)):
                self.save_as_file()
                return
        data = self.centralwidget.get_data()
        tsvbytes = make_DataTable(data, 'tsv',
                __MODIFIED__ = Dates.timestamp())
        with open(filepath, 'wb') as fh:
            fh.write(tsvbytes)
        self.currrent_file = filepath
        self.centralwidget.reset_modified()


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    edit = DataTableEditor()
    #print("???", sys.argv)
    if len(sys.argv) == 2:
        edit.open_file(sys.argv[1])
    edit.show()
    # Window dimensions
#    geometry = edit.screen().availableGeometry()
#    edit.setFixedSize(geometry.width() * 0.7, geometry.height() * 0.7)
#    #edit.resize(800, 600)
    geometry = APP.primaryScreen().availableGeometry()
    edit.resize(int(geometry.width() * 0.7),
            int(geometry.height() * 0.7))
    run(edit)
