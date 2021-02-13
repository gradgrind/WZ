# -*- coding: utf-8 -*-
"""
ui/tab_subjects.py

Last updated:  2021-02-13

Subject table management.


=+LICENCE=============================
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

=-LICENCE========================================
"""

### Labels, etc.
_UPDATE_SUBJECTS = "Fachliste aktualisieren"
_UPDATE_SUBJECTS_TEXT = "Die Fachliste für eine Klasse kann von einer" \
        " Tabelle (xlsx oder ods) aktualisiert werden.\nDiese Tabelle" \
        " muss die entsprechende Struktur aufweisen."
_UPDATE_SUBJECTS_TABLE = "Tabellendatei wählen"

_FILEOPEN = "Datei öffnen"
_TABLE_FILE = "Tabellendatei (*.xlsx *.ods *.tsv)"

#####################################################
import os
from qtpy.QtWidgets import QLabel, QTextEdit, QPushButton, QFileDialog
from ui.ui_support import TabPage

class Subjects(TabPage):
    """Update the subjects list for a class from a table (ods or xlsx).
    """
    def __init__(self):
        super().__init__(_UPDATE_SUBJECTS)
        l = QLabel(_UPDATE_SUBJECTS_TEXT)
        l.setWordWrap(True)
        self.vbox.addWidget(l)
        p = QPushButton(_UPDATE_SUBJECTS_TABLE)
        self.vbox.addWidget(p)
        p.clicked.connect(self.update)
        self.output = QTextEdit()
        self.vbox.addWidget(self.output)
#
    def leave(self):
        """Called when the tab is deselected.
        """
        self.output.clear()
        return True
#
    def update(self):
        dir0 = ADMIN._loaddir or os.path.expanduser('~')
        fpath = QFileDialog.getOpenFileName(self, _FILEOPEN,
                dir0, _TABLE_FILE)[0]
        if not fpath:
            return
        ADMIN.set_loaddir(os.path.dirname(fpath))
        cc = BACKEND('SUBJECT_table_update', filepath = fpath)

tab_subjects = Subjects()
TABS.append(tab_subjects)
