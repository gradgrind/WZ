# -*- coding: utf-8 -*-

"""
backend/interface_calendar.py - last updated 2021-05-22

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
# ---

import os

import core.base as CORE
from backend.interface_pupils import PUPILS
#from local.base_config import year_path, CALENDAR_FILE, CALENDER_HEADER
from template_engine.attendance import AttendanceTable, AttendanceError

def read_calendar():
    CALLBACK('calendar_SET_TEXT',
            text = CORE.Dates.read_calendar(SCHOOLYEAR))
    pupils = PUPILS(SCHOOLYEAR)
    classes = pupils.classes()
    CALLBACK('attendance_SET_CLASSES', classes = classes)
    return True

###

def save_calendar(text):
    text = CORE.Dates.save_calendar(SCHOOLYEAR, text)
    CALLBACK('calendar_SET_TEXT', text = text)
    return True

###

def make_attendance_table(klass, filepath):
    try:
        xlsxBytes = AttendanceTable.makeAttendanceTable(SCHOOLYEAR, klass)
    except AttendanceError as e:
        REPORT('ERROR', e)
    else:
        if xlsxBytes:
            with open(filepath, 'wb') as fh:
                fh.write(xlsxBytes)
            REPORT('INFO', '--> ' + filepath)
            return True
    return False

###

def update_attendance_table(klass, filepath):
    try:
        xlsxBytes = AttendanceTable.makeAttendanceTable(
                SCHOOLYEAR, klass, filepath)
    except AttendanceError as e:
        REPORT('ERROR', e)
    else:
        if xlsxBytes:
            os.replace(filepath, filepath + '_bak')
            with open(filepath, 'wb') as fh:
                fh.write(xlsxBytes)
            REPORT('INFO', '--> ' +  filepath)
            return True
    return False

########################################################################
def init():
    FUNCTIONS['CALENDAR_get_calendar'] = read_calendar
    FUNCTIONS['CALENDAR_save_calendar'] = save_calendar
    FUNCTIONS['ATTENDANCE_make_table'] = make_attendance_table
    FUNCTIONS['ATTENDANCE_update_table'] = update_attendance_table
