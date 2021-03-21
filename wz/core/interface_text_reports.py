# -*- coding: utf-8 -*-

"""
core/interface_text_reports.py - last updated 2021-03-20

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

### Messages


#from core.base import Dates
#from core.pupils import PUPILS, Pupils
#from core.courses import Subjects
#from local.base_config import year_path, SubjectsBase
#from local.grade_config import STREAMS
from template_engine.coversheet import CoverSheets


    def SET_CLASS(self, klass, pupil_list):
#TODO: check changes? (What does that mean?)
        pupils = PUPILS(SCHOOLYEAR)
        pdlist = pupils.class_pupils(klass)
        plist = [('', _ALL_PUPILS)] + [(pdata['PID'], pupils.name(pdata))
                for pdata in pdlist]
        CALLBACK('text_SET_CLASS', klass = klass, pupil_list = plist)



def make_covers(self, date):
#TODO: individual pupils
    coversheets = CoverSheets(SCHOOLYEAR)
    fn = _MakeCovers(coversheets, self.klass, date)
    files = REPORT('RUN', runme = fn)

###

class _MakeCovers(CORE.ThreadFunction):
    def __init__(self, coversheets, klass, date, pids = None):
        super().__init__()
        self._coversheets = coversheets
        self._klass = klass
        self._date = date
        self._pids = pids
#
    def run(self):
        fpath = self._coversheets.for_class(self._klass, self._date,
                self._pids)
        REPORT('INFO', _MADE_COVERS.format(path = fpath))
#
    def terminate(self):
        return False


FUNCTIONS['TEXT_set_class'] = set_class
FUNCTIONS['TEXT_make_covers'] = make_covers
