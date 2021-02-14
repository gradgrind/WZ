# -*- coding: utf-8 -*-

"""
core/interface_calendar.py - last updated 2021-02-13

Controller/dispatcher for management of calendar-related data.

==============================
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
"""

### Messages


import core.base as CORE
from local.base_config import year_path, CALENDAR_FILE, CALENDER_HEADER
from template_engine.attendance import AttendanceTable, AttendanceError
from local.attendance_config import ATTENDANCE_FILE

def read_calendar():
    CALLBACK('calendar_SET_TEXT',
            text = CORE.Dates.read_calendar(SCHOOLYEAR))
    return True

FUNCTIONS['CALENDAR_get_calendar'] = read_calendar

###

def save_calendar(text):
    text = CORE.Dates.save_calendar(SCHOOLYEAR, text)
    CALLBACK('calendar_SET_TEXT', text = text)
    return True

FUNCTIONS['CALENDAR_save_calendar'] = save_calendar

###

def migrate_calendar():
    CORE.Dates.migrate_calendar(SCHOOLYEAR)
    return True

FUNCTIONS['CALENDER_migrate_calendar'] = migrate_calendar

###


#TODO ...


class _MakeAttendanceTable:#(CORE.ThreadFunction):
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

class _UpdateAttendanceTable:#(CORE.ThreadFunction):
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





