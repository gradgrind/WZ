# -*- coding: utf-8 -*-
"""
datatable-editor.py

Last updated:  2021-10-21

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

########################################################################

import sys, os, builtins, traceback
if __name__ == '__main__':
    try:
        builtins.PROGRAM_DATA = os.environ['PROGRAM_DATA']
    except KeyError:
        this = sys.path[0]
        basedir = os.path.dirname(this)
        builtins.PROGRAM_DATA = os.path.join(basedir, 'wz-data')

#TODO: IF I use this feature, this is probably the wrong path ...
# Without the environment variable there is a disquieting error message.
#    os.environ['PYSIDE_DESIGNER_PLUGINS'] = PROGRAM_DATA

from ui.ui_base import openDialog, saveDialog, get_icon, \
        QMainWindow, QMenu, QMenuBar, QStatusBar, QAction, \
        QKeySequence

from core.base import Dates
from ui.datatable_widget import DataTableEditor as DataTableWidget
from ui.ui_base import openDialog, saveDialog, get_icon
from tables.spreadsheet import Spreadsheet, read_DataTable, TableError, \
        make_DataTable, make_DataTable_filetypes, read_DataTable_filetypes

### -----

class MainTable(DataTableWidget):
    def modified(self, mod):
        """Indicate data changed.
        """
        self.parent().modified(mod)


class DataTableEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(PROGRAM_NAME)
        icon = get_icon('datatable')
        self.setWindowIcon(icon)
        self.action_open = QAction(_OPEN_FILE, self)
        self.action_open.setShortcut(QKeySequence.Open)
        self.action_save = QAction(_SAVE_FILE, self)
        self.action_save.setShortcut(QKeySequence.Save)
        self.action_save_as = QAction(_SAVE_FILE_AS, self)
        self.action_save_as.setShortcut(QKeySequence.SaveAs)
        self.centralwidget = MainTable()
        self.setCentralWidget(self.centralwidget)
        menubar = self.menuBar()
        menu_file = menubar.addMenu(_FILE_MENU)
#        self.setMenuBar(menubar)
#        statusbar = self.statusBar()
#        self.setStatusBar(statusbar)

#        menubar.addAction(menu_file.menuAction())
        menu_file.addAction(self.action_open)
        menu_file.addAction(self.action_save)
        menu_file.addAction(self.action_save_as)

        # Exit QAction
        sep = QAction(" ", self)
        sep.setSeparator(True)
        menu_file.addAction(sep)
        exit_action = QAction(_EXIT, self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        menu_file.addAction(exit_action)

        self.action_open.triggered.connect(self.get_file)
        self.action_save.triggered.connect(self.save_file)
        self.action_save_as.triggered.connect(self.save_as_file)

    def modified(self, mod):
        self.__modified = mod
        if mod:
            self.setWindowTitle(f"{PROGRAM_NAME} – {self.filename} *")
        else:
            self.setWindowTitle(f"{PROGRAM_NAME} – {self.filename}")

    def get_file(self):
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
        self.currrent_file = filepath
        self.filename = os.path.basename(filepath)
        self.centralwidget.open_table(datatable)
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


"""
####???? Just as an example ...
class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle("Eartquakes information")

        # Menu
        menu = self.menuBar()
        file_menu = menu.addMenu("File")

        # Exit QAction
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(exit_action)

        # Status Bar
        status = self.statusBar()
        status.showMessage("Data loaded and plotted")

        # Window dimensions
        geometry = self.screen().availableGeometry()
        self.setFixedSize(geometry.width() * 0.8, geometry.height() * 0.7)
"""

if __name__ == '__main__':
    edit = DataTableEditor()
    #print("???", sys.argv)
    if len(sys.argv) == 2:
        edit.open_file(sys.argv[1])
    edit.show()
    # Window dimensions
    geometry = edit.screen().availableGeometry()
    edit.setFixedSize(geometry.width() * 0.7, geometry.height() * 0.7)
    #edit.resize(800, 600)
    sys.exit(app.exec())
