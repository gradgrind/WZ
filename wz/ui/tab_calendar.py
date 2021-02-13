# -*- coding: utf-8 -*-
"""
ui/tab_subjects.py

Last updated:  2021-02-13

Calendar editor.


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
_EDIT_CALENDAR = "Kalender bearbeiten"
_TITLE_LOSE_CHANGES = "Ungespeicherte Änderungen"
_LOSE_CHANGES = "Sind Sie damit einverstanden, dass die Änderungen verloren gehen?"
_SAVE = "Änderungen speichern"

#####################################################
import os
from qtpy.QtWidgets import QLabel, QTextEdit, QPushButton, \
        QHBoxLayout, QVBoxLayout
from ui.ui_support import TabPage, VLine

class Calendar(TabPage):
    """Editor for the calendar file.
    """
    def __init__(self):
        super().__init__(_EDIT_CALENDAR)
        topbox = QHBoxLayout()
        self.vbox.addLayout(topbox)

        #*********** The "main" widget ***********
        self.text_editor = QTextEdit()
        self.text_editor.setAcceptRichText(False)
        self.text_editor.textChanged.connect(self.text_changed)
        topbox.addWidget(self.text_editor)
        topbox.addWidget(VLine())

        cbox = QVBoxLayout()
        self.save_button = QPushButton(_SAVE)
        cbox.addWidget(self.save_button)
        self.save_button.clicked.connect(self.save)
        self.modified = False
#
#    def enter(self):
#        """Called when the tab is selected.
#        """
#
    def leave(self):
        """Called when the tab is deselected.
        If there are unsaved changes, ask whether it is ok to lose them.
        Return <True> if ok to lose them (or if there aren't any changes),
        otherwise <False>.
        """
        if self.modified and not QuestionDialog(
                _TITLE_LOSE_CHANGES, _LOSE_CHANGES):
            return False
        self.text_editor.clear()
        return True
#
    def text_changed(self):
        # Set self.text when a file is loaded or saved.
        # ... self.text_editor.setPlainText(text)
        # self.modified = False
        self.modified = self.text_editor.toPlainText() != self.text
        if self.modified:
            self.save_button.setEnabled(True)
        else:
            self.save_button.setEnabled(False)

#
    def update(self):
        dir0 = ADMIN._loaddir or os.path.expanduser('~')
        fpath = QFileDialog.getOpenFileName(self, _FILEOPEN,
                dir0, _TABLE_FILE)[0]
        if not fpath:
            return
        ADMIN.set_loaddir(os.path.dirname(fpath))
        cc = BACKEND('SUBJECT_table_update', filepath = fpath)
#
    def save(self):
        print("TODO")


tab_calendar = Calendar()
TABS.append(tab_calendar)
