# -*- coding: utf-8 -*-
"""
attendance.py

Last updated:  2021-11-18

Gui editor for attendance tables.

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
PROGRAM_NAME = "Attendance"
#_OPEN_TABLETYPE = "Tabellendatei"
#_INVALID_DATATABLE = "Ungültige DataTable: {path}\n ... {message}"

#_SAVE_AS_TSV = "Als tsv-Datei speichern?\n\n{path}"
#_UNSUPPORTED_SAVE = "Tabelle speichern – Dateityp '.{ending}'" " wird nicht unterstützt"

#_LOSE_CHANGES = "Es gibt ungespeicherte Änderungen.\n" "Wirklich schließen?"
#_LOSE_CHANGES_OPEN = (
#    "Es gibt ungespeicherte Änderungen.\n" "Neue Datei trotzdem öffnen?"
#)
#_SAVING_FORMAT = (
#    "Formatierungen werden möglicherweise verloren gehen:" "\n{path}\nÜberschreiben?"
#)


########################################################################

import sys, os, builtins, traceback

if __name__ == "__main__":
    try:
        builtins.PROGRAM_DATA = os.environ["PROGRAM_DATA"]
    except KeyError:
        this = sys.path[0]
        basedir = os.path.dirname(this)
        builtins.PROGRAM_DATA = os.path.join(basedir, "wz-data")

from ui.ui_base import APP, run, openDialog, saveDialog, get_icon, \
        QWidget, QVBoxLayout

# This seems to deactivate activate-on-single-click in filedialog
# (presumably elsewhere as well?)
APP.setStyleSheet("QAbstractItemView { activate-on-singleclick: 0; }")

from core.base import Dates
from ui.grid0 import GridViewRescaling

### -----


class AttendanceEditor(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.grid = GridViewRescaling()
        layout.addWidget(self.grid)


    def open_file(self, filepath):
        pupils = (
            ("0006", "Henry King"),
            ("1001", "Catherine d'Aragon"),
            ("1002", "Anne Boleyn"),
        )

        rows = (25, 3)
        row0 = len(rows)
        rows += (25,) * len(pupils)
        cols = (120, 3,)
        col0 = len(cols)
        cols += (25,) * 31
        self.grid.init(rows, cols, 25)

        col = col0
        for day in range(1, 32):
            self.grid.basic_tile(0, col, text=str(day))
            col += 1
        row = row0
        pupilmap = {}
        for pupil in pupils:
            pupilmap[pupil[0]] = row
            self.grid.basic_tile(row, 0, text=pupil[1], halign="l")
            row += 1


        self.grid.add_title("This is the title", halign="l")

#        self.set_current_file(None)
#        self.modified(False)
#        self.action_save_as.setEnabled(False)
        return int(self.grid.grid_width), int(self.grid.grid_height)

    def closeEvent(self, event):
        return

        w = APP.focusWidget()
        if w and isinstance(w, QLineEdit) and w.isModified():
            # Editing cell
            if SHOW_CONFIRM(_EDITING_CELL):
                event.accept()
            else:
                event.ignore()
        elif self.__modified:
            if SHOW_CONFIRM(_LOSE_CHANGES):
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def modified(self, mod):
        # print("MOD:", mod)
        self.__modified = mod
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
        if self.__modified and not SHOW_CONFIRM(_LOSE_CHANGES_OPEN):
            return
        filetypes = " ".join(["*." + fte for fte in Spreadsheet.filetype_endings()])
        ofile = openDialog(f"{_OPEN_TABLETYPE} ({filetypes})", OPEN_FILE)
        if ofile:
            self.open_file(ofile)

    def _open_file(self, filepath):
        """Read in a DataTable from the given path."""
        try:
            datatable = read_DataTable(filepath)
        except TableError as e:
            SHOW_ERROR(_INVALID_DATATABLE.format(path=str(filepath), message=str(e)))
            return
        except:
            SHOW_ERROR(
                f"BUG while reading {str(filepath)}:\n" f" ... {traceback.format_exc()}"
            )
            return
        self.set_current_file(filepath)
        self.open_table(datatable)
        self.action_save_as.setEnabled(True)
        self.saved = False
        self.modified(False)

    def save_as_file(self):
        endings = make_DataTable_filetypes()
        ftypes = " ".join(["*." + e for e in endings])
        filepath = saveDialog(
            f"{_OPEN_TABLETYPE} ({ftypes})", self.current_file, SAVE_FILE
        )
        if filepath:
            fpath, ending = filepath.rsplit(".", 1)
            if ending in endings:
                data = self.get_data()
                fbytes = make_DataTable(data, ending, __MODIFIED__=Dates.timestamp())
                with open(filepath, "wb") as fh:
                    fh.write(fbytes)
                self.current_file = filepath
                self.reset_modified()
            else:
                SHOW_ERROR(_UNSUPPORTED_SAVE.format(ending=ending))

    def save_file(self):
        fpath, ending = self.current_file.rsplit(".", 1)
        if ending == "tsv":
            filepath = self.current_file
        else:
            if ending in read_DataTable_filetypes():
                filepath = fpath + ".tsv"
            else:
                filepath = self.current_file + ".tsv"
            if not SHOW_CONFIRM(_SAVE_AS_TSV.format(path=filepath)):
                self.save_as_file()
                return
        data = self.get_data()
        tsvbytes = make_DataTable(data, "tsv", __MODIFIED__=Dates.timestamp())
        with open(filepath, "wb") as fh:
            fh.write(tsvbytes)
        self.current_file = filepath
        self.reset_modified()


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    # Enable package import if running as module
    import sys, os
    # print(sys.path)
    this = sys.path[0]
    basedir = os.path.dirname(this)
#    sys.path[0] = appdir
    from core.base import start
    start.setup(os.path.join(basedir, "TESTDATA"))

    edit = AttendanceEditor()
    icon = get_icon("attendance")
    edit.setWindowIcon(icon)

    x, y = edit.open_file(None)

# This may well not be the best approach to resizing. By using
# GridViewRescaling it shows the whole table ...
# The trouble with allowing scrollbars is that I haven't built fixed
# headers into the table widget.
    geometry = APP.primaryScreen().availableGeometry()
    max_x = int(geometry.width() * 0.9)
    max_y = int(geometry.height() * 0.9)
    if x + 50 > max_x or y + 50 > max_y:
        edit.resize(max_x, max_y)
    else:
        edit.resize(x + 50, y + 50)
    edit.show()
    run(edit)
    quit(0)


    # print("???", sys.argv)
    if len(sys.argv) == 2:
        edit.open_file(sys.argv[1])


#        if ofile:
#            self.open_file(ofile)

    grid.resize(600, 400)
    grid.show()


    fpath = os.path.join(os.path.expanduser("~"), "test.pdf")
    fpath = DATAPATH("testing/tmp/grid0.pdf")
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    grid.to_pdf(fpath)
    #    grid.to_pdf(fpath, can_rotate = False)



    # Window dimensions
    #    geometry = edit.screen().availableGeometry()
    #    edit.setFixedSize(geometry.width() * 0.7, geometry.height() * 0.7)
    #    #edit.resize(800, 600)
    geometry = APP.primaryScreen().availableGeometry()
    edit.resize(int(geometry.width() * 0.7), int(geometry.height() * 0.7))
    run(edit)

