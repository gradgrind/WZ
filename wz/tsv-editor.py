# -*- coding: utf-8 -*-
"""
ui/tsv-editor.py

Last updated:  2021-11-04

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
#    sys.path[0] = os.path.dirname(this)
#    print("???", sys.path)

#?
    try:
        builtins.PROGRAM_DATA = os.environ['PROGRAM_DATA']
    except KeyError:
#        basedir = os.path.dirname(os.path.dirname(this))
        basedir = os.path.dirname(this)
        builtins.PROGRAM_DATA = os.path.join(basedir, 'wz-data')
#    print("???", PROGRAM_DATA)

from ui.ui_base import run, openDialog, saveDialog, QWidget, \
        QVBoxLayout, QToolBar, get_icon, QKeySequence, QAction, APP
from ui.editable import EdiTableWidget, table2tsv

# This seems to deactivate activate-on-single-click in filedialog
# (presumably elsewhere as well?)
APP.setStyleSheet("QAbstractItemView { activate-on-singleclick: 0; }")

### -----

#TODO: Add all actions to toolbar (with enable/diable?)
# Handle modified -> ask on exit/open
# Info/Help?
# Show shortcuts somehow.

class TsvEditor(QWidget):
    def __init__(self, ofile = None):
        super().__init__()
        self.setWindowTitle(PROGRAM_NAME)
        icon = get_icon('tsv')
        self.setWindowIcon(icon)
        self.action_open = QAction(get_icon('open'), _OPEN_FILE, self)
        self.action_open.setShortcut(QKeySequence.Open)
        self.action_save = QAction(get_icon('save'), _SAVE_FILE, self)
        self.action_save.setShortcut(QKeySequence.Save)
        self.action_save_as = QAction(get_icon('saveas'), _SAVE_FILE_AS, self)
        self.action_save_as.setShortcut(QKeySequence.SaveAs)

        vbox = QVBoxLayout(self)
        toolbar = QToolBar()
        vbox.addWidget(toolbar)
        self.table = EdiTableWidget()
        vbox.addWidget(self.table)

        toolbar.addAction(self.action_open)
        toolbar.addAction(self.action_save)
        toolbar.addAction(self.action_save_as)

        # Actions from table widget
        toolbar.addSeparator()
        self.table.copyCellsAction.setIcon(get_icon('copy'))
        toolbar.addAction(self.table.copyCellsAction)
        self.table.cutCellsAction.setIcon(get_icon('cut'))
        toolbar.addAction(self.table.cutCellsAction)
        self.table.pasteCellsAction.setIcon(get_icon('paste'))
        toolbar.addAction(self.table.pasteCellsAction)
        self.table.insertRowAction.setIcon(get_icon('insertrowsafter'))
        toolbar.addAction(self.table.insertRowAction)
        self.table.deleteRowsAction.setIcon(get_icon('deleterows'))
        toolbar.addAction(self.table.deleteRowsAction)
        self.table.insertColumnAction.setIcon(get_icon('insertcolumnsafter'))
        toolbar.addAction(self.table.insertColumnAction)
        self.table.deleteColumnsAction.setIcon(get_icon('deletecolumns'))
        toolbar.addAction(self.table.deleteColumnsAction)

        # Undo/redo
        toolbar.addSeparator()
        undo_action = QAction(get_icon('undo'), "Undo", self)
        undo_action.triggered.connect(self.table.undoredo.undo)
        toolbar.addAction(undo_action)
        redo_action = QAction(get_icon('redo'), "Undo", self)
        redo_action.triggered.connect(self.table.undoredo.redo)
        toolbar.addAction(redo_action)

        # Exit QAction
        toolbar.addSeparator()
        exit_action = QAction(get_icon('quit'), _EXIT, self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        toolbar.addAction(exit_action)

        self.action_open.triggered.connect(self.get_file)
        self.action_save.triggered.connect(self.save_file)
        self.action_save_as.triggered.connect(self.save_as_file)

        self.table.setup(
                undo_redo = True,
                row_add_del = True,
                column_add_del = True,
                cut = True, paste = True,
                on_changed = self.modified)

        self.currrent_file = None
        self.action_save.setEnabled(False)
        self.action_save_as.setEnabled(False)
        if ofile:
            self.open_file(ofile)


        return


#class TsvEditor(QMainWindow):
#    def __init__(self, ofile = None):
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
        self.action_save.setEnabled(mod)




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
            self.currrent_file = sfile

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
        self.action_save_as.setEnabled(True)

    def save_file(self, sfile = None):
        if not sfile:
            sfile = self.currrent_file
        if not sfile.endswith('.tsv'):
            sfile += '.tsv'
        with open(sfile, 'w', encoding = 'utf-8') as fh:
            fh.write(table2tsv(self.table.table_data))
        # Tell the table editor widget to register "no changes"
        self.table.reset_modified()
        self.modified(False)


if __name__ == '__main__':
    ofile = sys.argv[1] if len(sys.argv) == 2 else None
    #print("tsv-editor.py:", sys.argv, "-->", ofile)
    tsv_edit = TsvEditor(ofile)
    # Window dimensions
    geometry = APP.primaryScreen().availableGeometry()
    tsv_edit.resize(int(geometry.width() * 0.7),
            int(geometry.height() * 0.7))
    run(tsv_edit)
