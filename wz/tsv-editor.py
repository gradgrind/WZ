# -*- coding: utf-8 -*-
"""
ui/tsv-editor.py

Last updated:  2021-10-08

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

# Messages
import traceback
import builtins
import os
import sys
from ui.ui_support import ui_load, openDialog, saveDialog
_OPEN_FILE = "tsv-Datei öffnen"
_SAVE_FILE = "tsv-Datei speichern"
_NOT_TSV = "Keine tsv-Datei: {filepath}"

########################################################################

if __name__ == '__main__':
    # TODO: IF I use this feature, this is probably the wrong path ...
    # Without the environment variable there is a disquieting error message.
    builtins.DATADIR = os.environ['PROGRAM_DATA']
    os.environ['PYSIDE_DESIGNER_PLUGINS'] = DATADIR

    from PySide6.QtWidgets import QApplication  # , QStyleFactory
    from PySide6.QtCore import QLocale, QTranslator, QLibraryInfo, QSettings
    # print(QStyleFactory.keys())
    # QApplication.setStyle('windows')
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

    print(DATADIR)

# Uses the modified QTableWidget in table.py (via <ui_load>).

# -----

# class TsvError(Exception):
#    pass

###

# TODO: Add/delete columns?


class TsvEditor:
    def __init__(self, ofile=None):
        self.window = ui_load('tsv-editor.ui')
        self.table = self.window.table_widget
        self.table.setup(row_add_del=True,  # column_add_del = True,
                         cut=True, paste=True)
        self.table.setSelectionMode(self.table.ExtendedSelection)
#        self.table.setWindowTitle("TableWidget")
        self.window.action_open.triggered.connect(self.get_file)
        self.window.action_save.triggered.connect(self.save_file)
        self.window.action_save_as.triggered.connect(self.save_as_file)
        if ofile:
            self.open_file(ofile)
#

    def get_file(self):
        ofile = openDialog("tsv-Datei (*.tsv)", _OPEN_FILE)
        if ofile:
            self.open_file(ofile)
#
# TODO: Indicator for unsaved data?
#

    def save_as_file(self):
        # TODO: Check that there is data?
        sfile = saveDialog("tsv-Datei (*.tsv)", self.currrent_file, _SAVE_FILE)
        if sfile:
            self.save_file(sfile)
#

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
                    # print(repr(row_b))
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
            SHOW_ERROR(_NOT_TSV.format(filepath=filepath))
            return None
        self.currrent_file = filepath

# TODO: Set column headers to header line? Maybe in special DataTable editor ...
        self.table.setColumnCount(maxlen)
        self.table.setRowCount(len(rows))
        r = 0
        for row in rows:
            c = 0
            for cell in row:
                self.table.set_text(r, c, cell)
                c += 1
            r += 1
#

    def save_file(self, sfile=None):
        if not sfile:
            sfile = self.currrent_file
        copied_text = self.table.getAllCells()
        if not sfile.endswith('.tsv'):
            sfile += '.tsv'
        with open(sfile, 'w', encoding='utf-8') as fh:
            fh.write(copied_text)


if __name__ == '__main__':
    #    import ui.qrc_icons
    from PySide6.QtGui import QIcon
    ofile = sys.argv[1] if len(sys.argv) == 2 else None
    print("tsv-editor.py:", sys.argv, "-->", ofile)
    tsv_edit = TsvEditor(ofile)
    WINDOW = tsv_edit.window
#    WINDOW.setWindowIcon(QIcon(os.path.join(DATADIR, 'icons', 'tsv.svg')))
    WINDOW.show()
    sys.exit(app.exec())
