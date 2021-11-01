# -*- coding: utf-8 -*-
"""
ui/tsv-editor.py

Last updated:  2021-11-01

Gui editor for Tab-Separated-Value files.

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
PROGRAM_NAME    = "tsv Editor"
_OPEN_FILE      = "tsv-Datei öffnen"
_SAVE_FILE      = "tsv-Datei speichern"
_NOT_TSV        = "Keine tsv-Datei: {filepath}"

#?
_FILE_MENU          = "Datei"
_OPEN_FILE          = "Tabellendatei öffnen"
_SAVE_FILE          = "Tabellendatei speichern"
_SAVE_FILE_AS       = "Tabellendatei speichern unter"
_EXIT               = "Schließen"
_OPEN_TABLETYPE     = "Tabellendatei"
_INVALID_DATATABLE  = "Ungültige DataTable: {path}\n ... {message}"

########################################################################

import sys, os, builtins, traceback
if __name__ == '__main__':
    # Enable package import if running module directly
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)
#    print("???", sys.path)

#?
    try:
        builtins.PROGRAM_DATA = os.environ['PROGRAM_DATA']
    except KeyError:
        basedir = os.path.dirname(os.path.dirname(this))
        builtins.PROGRAM_DATA = os.path.join(basedir, 'wz-data')
#    print("???", PROGRAM_DATA)

from ui.ui_base import run, openDialog, saveDialog, QMainWindow, \
        get_icon, QKeySequence, QAction, APP
from ui.editable import EdiTableWidget

# This seems to deactivate activate-on-single-click in filedialog
# (presumably elsewhere as well?)
APP.setStyleSheet("QAbstractItemView { activate-on-singleclick: 0; }")

### -----

#class TsvError(Exception):
#    pass

###

class DataTableEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(PROGRAM_NAME)
        icon = get_icon('tsv')
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









#TODO: Add/delete columns?

class TsvEditor(QMainWindow):
    def __init__(self, ofile = None):
        super().__init__()
        self.setWindowTitle(PROGRAM_NAME)
        icon = get_icon('tsv')
        self.setWindowIcon(icon)
        self.action_open = QAction(_OPEN_FILE, self)
        self.action_open.setShortcut(QKeySequence.Open)
        self.action_save = QAction(_SAVE_FILE, self)
        self.action_save.setShortcut(QKeySequence.Save)
        self.action_save_as = QAction(_SAVE_FILE_AS, self)
        self.action_save_as.setShortcut(QKeySequence.SaveAs)
        self.table = EdiTableWidget()
        self.setCentralWidget(self.table)
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

        self.table.setup(
                undo_redo = True,
                row_add_del = True,
                column_add_del = True,
                cut = True, paste = True,
                on_changed = self.modified)
        if ofile:
            self.open_file(ofile)

    def modified(self, mod):
        print("MOD:", mod)



#TODO: Also read odt and xlsx?
    def get_file(self):
        ofile = openDialog("tsv-Datei (*.tsv)", _OPEN_FILE)
        if ofile:
            self.open_file(ofile)

#TODO: Indicator for unsaved data?

    def save_as_file(self):
#TODO: Check that there is data?
        sfile = saveDialog("tsv-Datei (*.tsv)", self.currrent_file, _SAVE_FILE)
        if sfile:
            self.save_file(sfile)

    def open_file(self, filepath):
        """Read a tab-separated-value table as a list of rows,
        each row is a list of cell values.
        <filepath> can be the path to a tsv file, but it could be an
        <io.BytesIO> object.
        All values are returned as "stripped" strings.
        All lines are padded to the length of the longest line.
        """
        if filepath.endswith('.tsv'):
            try:
                if type(filepath) == str:
                    with open(filepath, 'rb') as fbi:
                        lines = fbi.read().splitlines()
                else:
                    lines = filepath.read().splitlines()
                rows = []
                maxlen = 0
                for row_b in lines:
                    #print(repr(row_b))
                    row = [cell.decode('utf-8').strip()
                            for cell in row_b.split(b'\t')]
                    l = len(row)
                    if l > maxlen:
                        maxlen = l
                    rows.append(row)
                for row in rows:
                    dl = maxlen - len(row)
                    if dl:
                        row += [''] * dl
            except:
                SHOW_ERROR(f"Problem reading tsv-file: {filepath}\n"
                        f" ...\n{traceback.format_exc()}")
                return None
        else:
            SHOW_ERROR(_NOT_TSV.format(filepath = filepath))
            return None
        self.currrent_file = filepath
        self.table.init_data(rows)
        self.table.resizeColumnsToContents()

    def save_file(self, sfile = None):
        if not sfile:
            sfile = self.currrent_file
        copied_text = self.table.getAllCells()
        if not sfile.endswith('.tsv'):
            sfile += '.tsv'
        with open(sfile, 'w', encoding = 'utf-8') as fh:
            fh.write(copied_text)



if __name__ == '__main__':
    from ui.ui_base import QIcon
    ofile = sys.argv[1] if len(sys.argv) == 2 else None
    print("tsv-editor.py:", sys.argv, "-->", ofile)
    tsv_edit = TsvEditor(ofile)
    # Window dimensions
    geometry = APP.primaryScreen().availableGeometry()
    tsv_edit.resize(int(geometry.width() * 0.7),
            int(geometry.height() * 0.7))
    run(tsv_edit)
