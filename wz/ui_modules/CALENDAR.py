# -*- coding: utf-8 -*-
"""
ui_modules/CALENDAR.py

Last updated:  2021-05-24

Calendar editor. Also handles school-year migration.

#TODO: attendance lists -> other module


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
_CLASS = "Klasse"

_ATTENDANCE = "Anwesenheit"
_GET_ATTENDANCE = "Tabelle erstellen"
_UPDATE_TABLE = "Tabelle aktualisieren"
_UPDATE_TABLE_TT = "Neue Schüler in die Tabelle aufnehmen"
_REPEATERS_TITLE = "Wiederholer"
_REPEATERS_SELECT = "Unten sind die Schüler, die am Ende des aktuellen" \
        " Schuljahres die Schule verlassen sollten.\n\n" \
        "Diejenigen, die das Jahr wiederholen werden, sollten markiert sein."

# Filename for attendance table:
_ATTENDANCE_FILE = 'Klassenbuch_{klass}_{year}'  # .xlsx

_TABLE_FILE = "Tabellendatei (*.xlsx *.ods *.tsv)"
_EXCEL_FILE = "Excel-Tabelle (*.xlsx)"

#####################################################

import os
from PySide6.QtWidgets import QLabel, QTextEdit, QPushButton, \
        QHBoxLayout, QVBoxLayout
from ui.ui_support import StackPage, KeySelector, \
        TreeMultiSelect, YesOrNoDialog, openDialog, saveDialog

class Calendar(StackPage):
    """Editor for the calendar file.
    """
    def __init__(self):
        super().__init__('tab_calendar')
        self.widget.textChanged.connect(self.text_changed)



        self.save_button = QPushButton(_SAVE)
        cbox.addWidget(self.save_button)
        self.save_button.clicked.connect(self.save)

        cbox.addSpacing(30)
        cbox.addStretch(1)

        ### Migration to next school-year
        migrate_button = QPushButton('MIGRATE')
        cbox.addWidget(migrate_button)
        migrate_button.clicked.connect(self.migrate)

        cbox.addStretch(1)
        ### Attendance tables
        cbox.addWidget(HLine())
        cbox.addWidget(QLabel('<b>%s</b>' % _ATTENDANCE))
        # Select class
        self.class_select = KeySelect()
        cbox.addWidget(QLabel(_CLASS))
        cbox.addWidget(self.class_select)
        # Get table
        cbox.addSpacing(5)
        pbAttendance = QPushButton(_GET_ATTENDANCE)
        cbox.addWidget(pbAttendance)
        pbAttendance.clicked.connect(self.get_attendance)
        # Update table
        cbox.addSpacing(5)
        pbAttUpdate = QPushButton(_UPDATE_TABLE)
        pbAttUpdate.setToolTip(_UPDATE_TABLE_TT)
        cbox.addWidget(pbAttUpdate)
        pbAttUpdate.clicked.connect(self.update_attendance)
#
    def is_modified(self):
        return self.modified
#
    def enter(self):
        """Called when the tab is selected.
        """
        # Get the calendar file
        BACKEND('CALENDAR_get_calendar')
#
    def SET_TEXT(self, text):
        self.text = text
        self.modified = False
        self.save_button.setEnabled(False)
        self.edit.setPlainText(text)
#
    def SET_CLASSES(self, classes):
        self.class_select.set_items([(c, c) for c in classes])
#
    def leave(self):
        """Called when the tab is deselected.
        """
        self.edit.clear()
#
    def text_changed(self):
        """Callback when the text is edited.
        """
        self.modified = self.edit.toPlainText() != self.text
        if self.modified:
            self.save_button.setEnabled(True)
        else:
            self.save_button.setEnabled(False)
#
    def save(self):
        BACKEND('CALENDAR_save_calendar', text = self.edit.toPlainText())

#*** School-year migration (starting a new school-year) ***#

    def migrate(self):
        """Create basic data for the next school-year.
        Pupils are moved to the next class.
        Subjects are retained.
        All years in the calendar are incremented.
        This function will fail if there is already data for the next year.
        """
        BACKEND('PUPILS_get_leavers')
#
    def SELECT_REPEATERS(self, klass_pupil_list):
        # Migrate pupils, allowing for repetition of the final classes
        kp = TreeMultiSelect(_REPEATERS_TITLE,
                _REPEATERS_SELECT, klass_pupil_list)
        if kp:
            pidlist = []
            for klass, pids in kp:
                pidlist += pids
            BACKEND('PUPILS_migrate', repeat_pids = pidlist)
#
#*** Attendance tables ***#
#
    def get_attendance(self):
        """Make a new attendance table for the current class.
        """
        # Get the path to which the file should be saved
        klass = self.class_select.selected()
        filename = _ATTENDANCE_FILE.format(klass = klass,
                year = ADMIN.current_year())
        fpath = saveDialog(_EXCEL_FILE, filename + '.xlsx')
        if fpath:
            BACKEND('ATTENDANCE_make_table', klass = klass, filepath = fpath)
#
    def update_attendance(self):
        """Rebuild an attendance table, adapting to pupil and calendar
        changes. The file is overwritten, the old version being kept
        with a '_bak' ending.
        """
        klass = self.class_select.selected()
        # Get the path to the old file
        fpath = openDialog(_TABLE_FILE)
        if fpath:
            BACKEND('ATTENDANCE_update_table', klass = klass, filepath = fpath)

#TODO .............


#???
    def check_saved(self):
        if self.pbSave.isEnabled() and QuestionDialog(
                _TITLE_CALENDAR_SAVE, _CALENDAR_SAVE):
            self.save()
#???
    def class_changed(self, klass):
        self.klass = klass

###

tab_calendar = Calendar()
TABS.append(tab_calendar)
FUNCTIONS['calendar_SET_TEXT'] = tab_calendar.SET_TEXT
FUNCTIONS['attendance_SET_CLASSES'] = tab_calendar.SET_CLASSES
FUNCTIONS['calendar_SELECT_REPEATERS'] = tab_calendar.SELECT_REPEATERS
