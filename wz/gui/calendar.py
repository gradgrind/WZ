# -*- coding: utf-8 -*-
"""
gui/calendar.py

Last updated:  2021-01-06

Manage calendar data, attendance tables, etc.

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

### Messages
_SAVED_AS = "Tabelle gespeichert als:\n  {path}"
_UPDATED = "Tabelle aktualisiert:\n  {path}"
_NO_AUTO_HEADER = "Automatische Kopfzeilen fehlen"

### Labels, etc.
_CALENDAR = "Schulkalender"
_SAVE = "Änderungen speichern"
_CLASS = "Klasse"
_ATTENDANCE = "Anwesenheit"
_GET_ATTENDANCE = "Tabelle erstellen"
_UPDATE_TABLE = "Tabelle aktualisieren"
_UPDATE_TABLE_TT = "Neue Schüler in die Tabelle aufnehmen"
_FILESAVE = "Datei speichern"
_EXCEL_FILE = "Excel-Datei (*.xlsx)"
_FILEOPEN = "Datei öffnen"
_TABLE_FILE = "Tabellendatei (*.xlsx *.ods *.tsv)"

#####################################################

import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)
# <core.base> must be the first WZ-import
import core.base as CORE

from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, \
        QPushButton, QTextEdit, QFileDialog
from qtpy.QtGui import QTextOption

from gui.gui_support import VLine, HLine, KeySelect, TabPage, GuiError
from core.pupils import Pupils
from local.base_config import year_path, CALENDAR_FILE, CALENDER_HEADER
from template_engine.attendance import AttendanceTable, AttendanceError
from local.attendance_config import ATTENDANCE_FILE

###

class Calendar(TabPage):
    def __init__(self):
        super().__init__(_CALENDAR)
        topbox = QHBoxLayout()
        self.vbox.addLayout(topbox)

        #*********** The "main" widget ***********
        self.edit = QTextEdit()
        #self.edit.setWordWrapMode(QTextOption.NoWrap)
        self.edit.setLineWrapMode(self.edit.NoWrap)
        self.edit.setAcceptRichText(False)
        self.edit.setUndoRedoEnabled(True)
        topbox.addWidget(self.edit)
        topbox.addWidget(VLine())

        cbox = QVBoxLayout()
        topbox.addLayout(cbox)

        self.pbSave = QPushButton(_SAVE)
        cbox.addWidget(self.pbSave)
        self.pbSave.clicked.connect(self.save)
        self.pbSave.setEnabled(False)
        self.edit.undoAvailable.connect(self.pbSave.setEnabled)
        cbox.addSpacing(30)
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
        self.year_changed()
#
    def leave(self):
        self.check_saved()
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
    def save(self):
        header = CALENDER_HEADER.format(date = CORE.Dates.today())
        text = self.edit.toPlainText()
        try:
            text = text.split('#---', 1)[1]
            text = text.lstrip('-')
            text = text.lstrip()
        except:
            pass
        text = header + text

        with open(self.calendar_file, 'w', encoding = 'utf-8') as fh:
            fh.write(text)
        self.edit.setPlainText(text)    # clear undo/redo history
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

###

class _MakeAttendanceTable(CORE.ThreadFunction):
    def __init__(self, klass, filepath):
        super().__init__()
        self._klass = klass
        self._filepath = filepath
#
    def run(self):
        try:
            xlsxBytes = AttendanceTable.makeAttendanceTable(
                    ADMIN.schoolyear, self._klass)
        except AttendanceError as e:
            REPORT('ERROR', e)
        else:
            if xlsxBytes:
                with open(self._filepath, 'wb') as fh:
                    fh.write(xlsxBytes)
                REPORT('INFO', _SAVED_AS.format(path = self._filepath))
#
    def terminate(self):
        return False

###

class _UpdateAttendanceTable(CORE.ThreadFunction):
    def __init__(self, klass, filepath):
        super().__init__()
        self._klass = klass
        self._filepath = filepath
#
    def run(self):
        try:
            xlsxBytes = AttendanceTable.makeAttendanceTable(
                    ADMIN.schoolyear, self._klass, self._filepath)
        except AttendanceError as e:
            REPORT('ERROR', e)
        else:
            if xlsxBytes:
                os.replace(self._filepath, self._filepath + '_bak')
                with open(self._filepath, 'wb') as fh:
                    fh.write(xlsxBytes)
                REPORT('INFO', _UPDATED.format(path = self._filepath))
#
    def terminate(self):
        return False


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication
    app = QApplication([])
    CORE.init()

    class ADMIN:
        schoolyear = '2016'
        _loaddir = None
        _savedir = None
        @classmethod
        def set_savedir(cls, path):
            cls._savedir = path
        @classmethod
        def set_loaddir(cls, path):
            cls._loaddir = path

    main = Calendar()
    main.enter()
    main.show()
    sys.exit(app.exec_())
