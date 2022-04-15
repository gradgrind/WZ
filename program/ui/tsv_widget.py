# -*- coding: utf-8 -*-
"""
ui/tsv-editor.py

Last updated:  2021-11-19

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

PROGRAM_NAME = "tsv Editor"
_OPEN_FILE = "Tabellendatei öffnen"
_SAVE_FILE = "Tabellendatei speichern"
_SAVE_FILE_AS = "Tabellendatei speichern unter"
_EXIT = "Schließen"
_TABLEFILE = "Tabellendatei"
_LOSE_CHANGES = "Es gibt ungespeicherte Änderungen.\n" "Wirklich schließen?"
_LOSE_CHANGES_OPEN = (
    "Es gibt ungespeicherte Änderungen.\n" "Neue Datei trotzdem öffnen?"
)
_SAVING_FORMAT = (
    "Formatierungen werden möglicherweise verloren gehen:" "\n{path}\nÜberschreiben?"
)
_TABLETYPE_NOT_SUPPORTED = "Tabellentyp '{ending}' ist nicht unterstützt"

########################################################################

import sys, os, builtins

if __name__ == "__main__":
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    # TODO: Temporary redirection to use real data (there isn't any test data yet!)
    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    #    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))

    try:
        builtins.PROGRAM_DATA = os.environ["PROGRAM_DATA"]
    except KeyError:
        #        basedir = os.path.dirname(os.path.dirname(this))
        builtins.PROGRAM_DATA = os.path.join(basedir, "wz-data")
#    print("???", PROGRAM_DATA)

### +++++

from ui.ui_base import (
    run,
    openDialog,
    saveDialog,
    QWidget,
    Qt,
    QVBoxLayout,
    QToolBar,
    get_icon,
    QKeySequence,
    QAction,
    APP,
)
from ui.editable import EdiTableWidget, table2tsv

# This seems to deactivate activate-on-single-click in filedialog
# (presumably elsewhere as well?)
APP.setStyleSheet("QAbstractItemView { activate-on-singleclick: 0; }")

from tables.spreadsheet import Spreadsheet, TableError, NewSpreadsheet

### -----

# TODO:
# Info/Help?


class TsvEditor(QWidget):
    def new_action(self, icon, text, shortcut):
        action = QAction(self)
        if shortcut:
            text += f" – [{shortcut.toString()}]"
            action.setShortcut(shortcut)
        action.setText(text)
        action.setIcon(get_icon(icon))
        return action

    def __init__(self, ofile=None):
        super().__init__()
        icon = get_icon("tsv")
        self.setWindowIcon(icon)
        self.action_open = self.new_action(
            "open", _OPEN_FILE, QKeySequence(Qt.CTRL + Qt.Key_O)
        )
        self.action_save = self.new_action(
            "save", _SAVE_FILE, QKeySequence(Qt.CTRL + Qt.Key_S)
        )
        self.action_save_as = self.new_action(
            "saveas", _SAVE_FILE_AS, QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_S)
        )

        vbox = QVBoxLayout(self)
        # Build the toolbar
        toolbar = QToolBar()
        vbox.addWidget(toolbar)
        self.table = EdiTableWidget()
        vbox.addWidget(self.table)

        toolbar.addAction(self.action_open)
        toolbar.addAction(self.action_save)
        toolbar.addAction(self.action_save_as)

        # Add the actions from table widget
        toolbar.addSeparator()
        self.table.copyCellsAction.setIcon(get_icon("copy"))
        toolbar.addAction(self.table.copyCellsAction)
        self.table.cutCellsAction.setIcon(get_icon("cut"))
        toolbar.addAction(self.table.cutCellsAction)
        self.table.pasteCellsAction.setIcon(get_icon("paste"))
        toolbar.addAction(self.table.pasteCellsAction)
        self.table.insertRowAction.setIcon(get_icon("insertrowsafter"))
        toolbar.addAction(self.table.insertRowAction)
        self.table.deleteRowsAction.setIcon(get_icon("deleterows"))
        toolbar.addAction(self.table.deleteRowsAction)
        self.table.insertColumnAction.setIcon(get_icon("insertcolumnsafter"))
        toolbar.addAction(self.table.insertColumnAction)
        self.table.deleteColumnsAction.setIcon(get_icon("deletecolumns"))
        toolbar.addAction(self.table.deleteColumnsAction)

        toolbar.addSeparator()
        self.table.undoAction.setIcon(get_icon("undo"))
        toolbar.addAction(self.table.undoAction)
        self.table.redoAction.setIcon(get_icon("redo"))
        toolbar.addAction(self.table.redoAction)

        # Exit QAction
        toolbar.addSeparator()
        exit_action = self.new_action("quit", _EXIT, QKeySequence(Qt.CTRL + Qt.Key_Q))
        exit_action.triggered.connect(self.close)
        toolbar.addAction(exit_action)

        self.action_open.triggered.connect(self.get_file)
        self.action_save.triggered.connect(self.save_file)
        self.action_save_as.triggered.connect(self.save_as_file)

        self.table.setup(
            undo_redo=True,
            row_add_del=True,
            column_add_del=True,
            cut=True,
            paste=True,
            on_changed=self.modified,
        )

        self.set_current_file(None)
        self.action_save.setEnabled(False)
        self.action_save_as.setEnabled(False)
        if ofile:
            self.open_file(ofile)
        self.set_title(False)

    def closeEvent(self, event):
        if self.table.is_modified():
            if SHOW_CONFIRM(_LOSE_CHANGES):
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def modified(self, mod):
        # print("MOD:", mod)
        self.action_save.setEnabled(mod)
        self.set_title(mod)

    def set_title(self, changed):
        x = " *" if changed else ""
        title = (
            f"{PROGRAM_NAME} – {self.filename}{x}" if self.filename else PROGRAM_NAME
        )
        self.setWindowTitle(title)

    def set_current_file(self, path):
        self.current_file = path
        self.filename = os.path.basename(path) if path else None

    def get_file(self):
        if self.table.is_modified() and not SHOW_CONFIRM(_LOSE_CHANGES_OPEN):
            return
        filetypes = " ".join(["*." + fte for fte in Spreadsheet.filetype_endings()])
        ofile = openDialog(f"{_TABLEFILE} ({filetypes})", _OPEN_FILE)
        if ofile:
            self.open_file(ofile)

    def open_file(self, filepath):
        """Read a tab-separated-value table as a list of rows,
        each row is a list of cell values.
        <filepath> can be the path to a tsv file, but it could be an
        <io.BytesIO> object.
        All values are returned as "stripped" strings.
        All lines are padded to the length of the longest line.
        """
        try:
            sheet = Spreadsheet(filepath)
        except TableError as e:
            SHOW_ERROR(str(e))
            return
        self.set_current_file(sheet.filepath)
        self.table.init_data(sheet.table())
        self.table.resizeColumnsToContents()
        self.action_save_as.setEnabled(True)
        self.saved = False
        self.modified(False)

    def save_as_file(self):
        sfile = saveDialog(
            f"{_TABLEFILE} (*.tsv *.xlsx)", self.current_file, _SAVE_FILE
        )
        if sfile and self.save_file(sfile):
            self.set_current_file(sfile)
            self.modified(False)

    def save_file(self, sfile=None):
        if not sfile:  # "Save"
            sfile = self.current_file
            if (not self.saved) and (not sfile.endswith(".tsv")):
                if not SHOW_CONFIRM(_SAVING_FORMAT.format(path=sfile)):
                    return False
        if sfile.endswith(".tsv"):
            with open(sfile, "w", encoding="utf-8") as fh:
                fh.write(table2tsv(self.table.read_all()))
        elif sfile.endswith(".xlsx"):
            NewSpreadsheet.make(self.table.read_all(), sfile)
        else:
            try:
                _, ending = sfile.rsplit(".", 1)
            except ValueError:
                ending = ""
            SHOW_ERROR(_TABLETYPE_NOT_SUPPORTED.format(ending=ending))
            return False
        # Tell the table editor widget to register "no changes"
        self.table.reset_modified()
        self.saved = True
        #        self.modified(False)
        return True


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    ofile = sys.argv[1] if len(sys.argv) == 2 else None
    # print("tsv-editor.py:", sys.argv, "-->", ofile)
    tsv_edit = TsvEditor(ofile)
    # Window dimensions
    geometry = APP.primaryScreen().availableGeometry()
    tsv_edit.resize(int(geometry.width() * 0.7), int(geometry.height() * 0.7))
    run(tsv_edit)
