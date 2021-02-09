# -*- coding: utf-8 -*-

"""
core/interface_subjects.py - last updated 2021-02-08

Controller/dispatcher for subjects management.

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
_SUBJECTS_CLASS = " ... Tabelle für Klasse {klass} aktualisiert"

from core.courses import Subjects

def update_subjects(filepath):
        subjects = Subjects(SCHOOLYEAR)
        srctable = subjects.read_source_table(filepath)
        opath = subjects.save_table(srctable)
        REPORT('INFO', _SUBJECTS_CLASS.format(klass = srctable.klass))
        return True

FUNCTIONS['SUBJECT_table_update'] = update_subjects
