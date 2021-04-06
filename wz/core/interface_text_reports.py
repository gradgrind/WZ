# -*- coding: utf-8 -*-

"""
core/interface_text_reports.py - last updated 2021-04-06

Controller/dispatcher for text-report management.

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

#TODO: At present only cover-sheets are supported.

### Messages
_MADE_COVERS = "Mantelbögen erstellt in:\n  {path}"
_MADE_ONE_COVER = "Mantelbogen erstellt:\n  {path}"

### Labels, etc.
_ALL_PUPILS = "* Ganze Klasse *"

from core.base import Dates
from core.pupils import PUPILS
from template_engine.coversheet import CoverSheets

###

NONE = ''

def get_calendar():
    CALLBACK('text_SET_CALENDAR', calendar = Dates.get_calendar(SCHOOLYEAR))
    pupils = PUPILS(SCHOOLYEAR)
    class_list = pupils.classes()
    class_list.reverse()   # start with the highest classes
    CALLBACK('text_SET_CLASSES', classes = class_list)
    return True

###

def set_class(klass):
    pupils = PUPILS(SCHOOLYEAR)
    plist = [('', _ALL_PUPILS)] + [(pdata['PID'], pupils.name(pdata))
            for pdata in pupils.class_pupils(klass)]
    CALLBACK('text_SET_PUPILS', pupil_list = plist)
    return True

###

def make_covers(date, klass):
    coversheets = CoverSheets(SCHOOLYEAR)
    fpath = coversheets.for_class(klass, date)
    REPORT('INFO', _MADE_COVERS.format(path = fpath))
    return True
#
def covername(pid):
    coversheets = CoverSheets(SCHOOLYEAR)
    CALLBACK('text_MAKE_ONE_COVER', filename = coversheets.filename1(pid))
    return True
#
def make_one_cover(pid, date, filepath):
    coversheets = CoverSheets(SCHOOLYEAR)
    pdfbytes = coversheets.for_pupil(pid, date)
    with open(filepath, 'wb') as fh:
        fh.write(pdfbytes)
    REPORT('INFO', _MADE_ONE_COVER.format(path = filepath))
    return True


FUNCTIONS['TEXT_get_calendar'] = get_calendar
FUNCTIONS['TEXT_set_class'] = set_class
FUNCTIONS['TEXT_make_covers'] = make_covers
FUNCTIONS['TEXT_covername'] = covername
FUNCTIONS['TEXT_make_one_cover'] = make_one_cover
