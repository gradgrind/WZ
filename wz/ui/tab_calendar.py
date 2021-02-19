# -*- coding: utf-8 -*-
"""
ui/tab_subjects.py

Last updated:  2021-02-19

Calendar editor. Also handles school-year migration and attendance lists.


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
_EDIT_CALENDAR = "Kalender bearbeiten"
_TITLE_LOSE_CHANGES = "Ungespeicherte Änderungen"
_LOSE_CHANGES = "Sind Sie damit einverstanden, dass die Änderungen verloren gehen?"
_SAVE = "Änderungen speichern"
_ATTENDANCE = "Anwesenheit"
_GET_ATTENDANCE = "Tabelle erstellen"
_UPDATE_TABLE = "Tabelle aktualisieren"
_UPDATE_TABLE_TT = "Neue Schüler in die Tabelle aufnehmen"
_REPEATERS_TITLE = "Wiederholer"
_REPEATERS_SELECT = "Unten sind die Schüler, die am Ende des aktuellen" \
        " Schuljahres die Schule verlassen sollten.\n\n" \
        "Diejenigen, die das Jahr wiederholen werden, sollten markiert sein."

#_TABLE_FILE = "Tabellendatei (*.xlsx *.ods *.tsv)"
#_EXCEL_FILE = "Excel-Tabelle (*.xlsx)"

#####################################################

import os
from qtpy.QtWidgets import QLabel, QTextEdit, QPushButton, \
        QHBoxLayout, QVBoxLayout
from ui.ui_support import TabPage, VLine, HLine, KeySelect, \
        TreeMultiSelect#, openDialog, saveDialog

class Calendar(TabPage):
    """Editor for the calendar file.
    """
    def __init__(self):
        super().__init__(_EDIT_CALENDAR)
        topbox = QHBoxLayout()
        self.vbox.addLayout(topbox)

        #*********** The "main" widget ***********
        self.edit = QTextEdit()
        self.edit.textChanged.connect(self.text_changed)
        self.edit.setLineWrapMode(self.edit.NoWrap)
        self.edit.setAcceptRichText(False)
        self.edit.setUndoRedoEnabled(True)
        topbox.addWidget(self.edit)
        topbox.addWidget(VLine())

        cbox = QVBoxLayout()
        topbox.addLayout(cbox)

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
        self.class_select = KeySelect(changed_callback = self.class_changed)
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
    def year_changed(self):
        self.enter()
        return True
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
    def leave(self):
        """Called when the tab is deselected.
        If there are unsaved changes, ask whether it is ok to lose them.
        Return <True> if ok to lose them (or if there aren't any changes),
        otherwise <False>.
        """
        if self.modified and not QuestionDialog(
                _TITLE_LOSE_CHANGES, _LOSE_CHANGES):
            return False
        self.edit.clear()
        return True
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
        All year in the calendar are incremented.
        """
#TODO: Check whether the next year exists already. If so, it could be archived
# before regeneration.
# Maybe an archiving function would be useful anyway?
# Maybe the migration function is only available for the latest year?
        BACKEND('PUPILS_get_leavers')
#
    def SELECT_REPEATERS(self, klass_pupil_list):
        # Migrate pupils, allowing for repetition of the final classes
        pidlist = []
        for klass, pids in TreeMultiSelect(_REPEATERS_TITLE,
                _REPEATERS_SELECT, klass_pupil_list):
            pidlist += pids
        BACKEND('PUPILS_migrate', repeat_pids = pidlist)
#
#???
        return

        BACKEND('BASE_get_years')
#TODO: also need to select the new year!
        nextyear = str(int(ADMIN.current_year()) + 1)
        ADMIN.set_year(nextyear)
#THIS IS NOT WORKING!!!
#


#TODO .............


#
    def check_saved(self):
        if self.pbSave.isEnabled() and QuestionDialog(
                _TITLE_CALENDAR_SAVE, _CALENDAR_SAVE):
            self.save()
#
    def class_changed(self, klass):
        self.klass = klass
#
    def get_attendance(self):
        """Make a new attendance table for the current class.
        """
        # Get the path to which the file should be saved
        filename = ATTENDANCE_FILE.format(klass = self.klass,
                year = ADMIN.schoolyear)
        fpath = saveDialog(_EXCEL_FILE, filename + '.xlsx')
        if fpath:
            fn = _MakeAttendanceTable(self.klass, fpath)
            REPORT('RUN', runme = fn)
#
    def update_attendance(self):
        """Rebuild an attendance table, adapting to pupil and calendar
        changes. The file is overwritten, the old version being kept
        with a '_bak' ending.
        """
        # Get the path to the old file
        fpath = openDialog(_TABLE_FILE)
        if fpath:
            fn = _UpdateAttendanceTable(self.klass, fpath)
            REPORT('RUN', runme = fn)


tab_calendar = Calendar()
TABS.append(tab_calendar)
FUNCTIONS['calendar_SET_TEXT'] = tab_calendar.SET_TEXT
FUNCTIONS['calendar_SELECT_REPEATERS'] = tab_calendar.SELECT_REPEATERS
