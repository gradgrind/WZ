# -*- coding: utf-8 -*-
"""
ui/tab_subjects.py

Last updated:  2021-02-19

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
        " muss die entsprechende Struktur aufweisen." \
        "\n\nDie Fächerwahl-Tabelle für eine Klasse kann als xlsx-Datei" \
        " \"exportiert\" werden.\n" \
        "Eine solche Tabelle kann auch \"importiert\" werden, um die" \
        " Daten für diese Klasse zu aktualisieren."
_UPDATE_SUBJECTS_TABLE = "Fachtabelle laden"
_MAKE_CHOICE_TABLE = "Fach-Wahl-Tabelle erstellen"
_UPDATE_CHOICE_TABLE = "Fach-Wahl-Tabelle laden"
_SELECT_CLASS_TITLE = "Klasse wählen"
_SELECT_CLASS = "Klicken Sie auf die Klasse, für die eine" \
        " Fächerwahltabelle erstellt werden soll."

_SUBJECT_CHOICE_FILE = 'Fachwahl_{klass}.xlsx'
_TABLE_FILE = "Tabellendatei (*.xlsx *.ods *.tsv)"
_EXCEL_FILE = "Excel-Tabelle (*.xlsx)"

#####################################################

import os
from qtpy.QtWidgets import QLabel, QTextEdit, QHBoxLayout, QVBoxLayout, \
        QPushButton
from ui.ui_support import TabPage, VLine, ListSelect, openDialog, saveDialog

class Subjects(TabPage):
    """Update (import) the subjects list for a class from a table (ods
    or xlsx).
    Export (xlsx) and import (ods or xlsx) the "choice" table for a class.
    """
    def __init__(self):
        super().__init__(_UPDATE_SUBJECTS)
        topbox = QHBoxLayout()
        self.vbox.addLayout(topbox)

        #*********** The "main" widget ***********
        display = QTextEdit()
        display.setAcceptRichText(False)
        display.setReadOnly(True)
        topbox.addWidget(display)
        display.setPlainText(_UPDATE_SUBJECTS_TEXT)
        topbox.addWidget(VLine())

        cbox = QVBoxLayout()
        topbox.addLayout(cbox)

        pb_ust = QPushButton(_UPDATE_SUBJECTS_TABLE)
        cbox.addWidget(pb_ust)
        pb_ust.clicked.connect(self.update_subjects)
        cbox.addSpacing(30)
        pb_mct = QPushButton(_MAKE_CHOICE_TABLE)
        cbox.addWidget(pb_mct)
        pb_mct.clicked.connect(self.choice_table)
        pb_uct = QPushButton(_UPDATE_CHOICE_TABLE)
        cbox.addWidget(pb_uct)
        pb_uct.clicked.connect(self.update_choices)

        cbox.addStretch(1)

#
    def leave(self):
        """Called when the tab is deselected.
        """
        return True
#
    def update_subjects(self):
        fpath = openDialog(_TABLE_FILE)
        if not fpath:
            return
        cc = BACKEND('SUBJECT_table_update', filepath = fpath)
#
    def update_choices(self):
        SHOW_ERROR("TODO: update_choices")
#
#TODO: Would it be better to have a selected class permanently visible?
    def choice_table(self):
        BACKEND('SUBJECT_select_choice_class')
#
    def select_choice_table(self, classes):
        c = ListSelect(_SELECT_CLASS_TITLE, _SELECT_CLASS, classes)
        if c:
            fpath = saveDialog(_EXCEL_FILE,
                    _SUBJECT_CHOICE_FILE.format(klass = c))
            if fpath:
                BACKEND('SUBJECT_make_choice_table', klass = c,
                        filepath = fpath)


tab_subjects = Subjects()
TABS.append(tab_subjects)
FUNCTIONS['subjects_SELECT_CHOICE_TABLE'] = tab_subjects.select_choice_table
