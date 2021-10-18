# -*- coding: utf-8 -*-
"""
datatable-editor.py

Last updated:  2021-10-16

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

#TODO: file saving, _-info items (title, modified),
# change handling – also on line add/delete, undo/redo

### Messages
PROGRAM_NAME        = "DataTable Editor"
_FILE_MENU          = "Datei"
_OPEN_FILE          = "Tabellendatei öffnen"
_SAVE_FILE          = "Tabellendatei speichern"
_SAVE_FILE_AS       = "Tabellendatei speichern unter"
_EXIT               = "Schließen"
_OPEN_TABLETYPE     = "Tabellendatei"
#_NOT_DATATABLE        = "Keine Tabellendatei: {filepath}"
_INVALID_DATATABLE  = "Ungültige DataTable: {path}\n ... {message}"

########################################################################

import sys, os, builtins, traceback
if __name__ == '__main__':
#TODO: IF I use this feature, this is probably the wrong path ...
# Without the environment variable there is a disquieting error message.
    builtins.DATADIR = os.environ['PROGRAM_DATA']
    os.environ['PYSIDE_DESIGNER_PLUGINS'] = DATADIR

    from PySide6.QtWidgets import QApplication#, QStyleFactory
    from PySide6.QtCore import QLocale, QTranslator, QLibraryInfo, QSettings
    #print(QStyleFactory.keys())
    #QApplication.setStyle('windows')
    # Qt initialization
    app = QApplication(sys.argv)
    # Set up language/locale for Qt
    LOCALE = QLocale(QLocale.German, QLocale.Germany)
    QLocale.setDefault(LOCALE)
    qtr = QTranslator()
    qtr.load("qt_" + LOCALE.name(),
            QLibraryInfo.location(QLibraryInfo.TranslationsPath))
    app.installTranslator(qtr)
    # Persistent Settings:
    builtins.SETTINGS = QSettings(
            QSettings.IniFormat, QSettings.UserScope, 'MT', 'WZ')

from PySide6.QtWidgets import QMainWindow, QMenu, QMenuBar, QStatusBar
from PySide6.QtGui import QAction, QKeySequence
#from PySide6.QtCore import Qt

from ui.datatable_widget import DataTableEditor as DataTableWidget
from ui.ui_extra import openDialog, saveDialog, get_icon
from tables.spreadsheet import Spreadsheet, read_DataTable, TableError

### -----

#class TsvError(Exception):
#    pass

###

#TODO: Add/delete columns? Rather not ...
# Undo/redo?

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
        self.centralwidget = DataTableWidget()
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
#
    def get_file(self):
        filetypes = ' '.join(['*.' + fte
                for fte in Spreadsheet.filetype_endings()])
        ofile = openDialog(f"{_OPEN_TABLETYPE} ({filetypes})", _OPEN_FILE)
        if ofile:
            self.open_file(ofile)
#
    def save_as_file(self):
#TODO: Check that there is data?
# File type? tsv or xlsx as choice or preset.
        sfile = saveDialog("tsv-Datei (*.tsv)", self.currrent_file, _SAVE_FILE)
        if sfile:
            self.save_file(sfile)
#
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
        self.setWindowTitle(f"{PROGRAM_NAME} – {self.filename}")

#
#TODO
    def save_file(self, sfile = None):
        if not sfile:
            sfile = self.currrent_file
        copied_text = self.table.getAllCells()
        if not sfile.endswith('.tsv'):
            sfile += '.tsv'
        with open(sfile, 'w', encoding = 'utf-8') as fh:
            fh.write(copied_text)

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

if __name__ == '__main__':
#    edit = MainWindow()
    edit = DataTableEditor()
    print("???", sys.argv)
    if len(sys.argv) == 2:
        edit.open_file(sys.argv[1])
    edit.show()
    sys.exit(app.exec())
