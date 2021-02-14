# -*- coding: utf-8 -*-
"""
ui/tab_subjects.py

Last updated:  2021-02-14

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

#####################################################
import os
from qtpy.QtWidgets import QLabel, QTextEdit, QPushButton, \
        QHBoxLayout, QVBoxLayout
from ui.ui_support import TabPage, VLine, HLine, KeySelect, TreeMultiSelect

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
# Check whether the next year exists already. If so, it could be archived
# before regeneration.
# Maybe an archiving function would be useful anyway?
# Maybe the migration function is only available for the latest year?

# Copy current calendar and open in editor. Check core dates?
# Migrate pupils:
#TODO: Some way of easily allowing class repetitions?
# A tree for 13 and 12-non-Gym?
#   - all classes + 1.
#   - streams: default from class 5(G) is "Gym", others (currently) empty.
#   - 12(G/Gym) -> 13.
#   - other 12 removed.
# Copy subject lists.
        print("TODO")
        data = (
            ('12', (
                ('100', 'Alan Able'),
                ('102', 'Betty Bot')
            )),
            ('13', (
                ('090', 'Carly Clone'),
                ('091', 'Danny Drone')
            ))
        )
        print (TreeMultiSelect('TITLE', 'Select this or that',
                data))


#


#TODO .............

#
    def year_changed(self):
        self.calendar_file = year_path(ADMIN.schoolyear, CALENDAR_FILE)
        with open(self.calendar_file, encoding = 'utf-8') as fh:
            text = fh.read()
        self.edit.setPlainText(text)

        pupils = Pupils(ADMIN.schoolyear)
        self.class_select.set_items([(c, c)
                for c in pupils.classes()])
        self.class_select.trigger()
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
        dir0 = ADMIN._savedir or os.path.expanduser('~')
        fpath = QFileDialog.getSaveFileName(self, _FILESAVE,
                os.path.join(dir0, filename + '.xlsx'), _EXCEL_FILE)[0]
        if fpath:
            ADMIN.set_savedir(os.path.dirname(fpath))
            fn = _MakeAttendanceTable(self.klass, fpath)
            REPORT('RUN', runme = fn)
#
    def update_attendance(self):
        """Rebuild an attendance table, adapting to pupil and calendar
        changes. The file is overwritten, the old version being kept
        with a '_bak' ending.
        """
        # Get the path to the old file
        dir0 = ADMIN._loaddir or os.path.expanduser('~')
        fpath = QFileDialog.getOpenFileName(self, _FILEOPEN,
                dir0, _TABLE_FILE)[0]
        if fpath:
            ADMIN.set_loaddir(os.path.dirname(fpath))
            fn = _UpdateAttendanceTable(self.klass, fpath)
            REPORT('RUN', runme = fn)





tab_calendar = Calendar()
TABS.append(tab_calendar)
FUNCTIONS['calendar_SET_TEXT'] = tab_calendar.SET_TEXT
