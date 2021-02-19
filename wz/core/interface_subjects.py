# -*- coding: utf-8 -*-

"""
core/interface_subjects.py - last updated 2021-02-19

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
_CHOICES_SAVED = "Fach-Wahl-Tabelle für Klasse {klass} gespeichert" \
        " als:\n  {fpath}"

from core.courses import Subjects
from local.base_config import print_class

#TODO: Would it be better with a cache, like for the pupils (Pupil_Base)?

def update_subjects(filepath):
    subjects = Subjects(SCHOOLYEAR)
    klass = subjects.import_source_table(filepath)
    REPORT('INFO', _SUBJECTS_CLASS.format(klass = klass))
    return True
#
def select_choice_class():
    subjects = Subjects(SCHOOLYEAR)
    clist = [(c, subjects.CLASS + ' ' + print_class(c))
            for c in subjects.classes()]
    CALLBACK('subjects_SELECT_CHOICE_TABLE', classes = clist)
    return True
#
def make_choice_table(klass, filepath):
    subjects = Subjects(SCHOOLYEAR)
    xlsx_bytes = subjects.make_choice_table(klass)
    with open(filepath, 'wb') as fh:
        fh.write(xlsx_bytes)
    REPORT('INFO', _CHOICES_SAVED.format(klass = klass, fpath = filepath))
    return True


FUNCTIONS['SUBJECT_table_update'] = update_subjects
FUNCTIONS['SUBJECT_select_choice_class'] = select_choice_class
FUNCTIONS['SUBJECT_make_choice_table'] = make_choice_table
