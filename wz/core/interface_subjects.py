# -*- coding: utf-8 -*-

"""
core/interface_subjects.py - last updated 2021-02-20

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
_SUBJECTS_CLASS = " ... Fach-Tabelle für Klasse {klass} aktualisiert"
_CHOICES_SAVED = "Fach-Wahl-Tabelle für Klasse {klass} gespeichert" \
        " als:\n  {fpath}"
_CHOICES_CLASS = "Fach-Wahl-Tabelle für Klasse {klass} aktualisiert"

from core.pupils import PUPILS
from core.courses import Subjects

### +++++

class _Subject_Base:
    """A cache for subject/course information.
    """
    schoolyear = None
    subjects = None
#
    @classmethod
    def set_year(cls, year = None):
        """Load subject/course data for the given year.
        Clear data if no year.
        """
        if year == cls.schoolyear:
            return
        cls.schoolyear = year
        cls.subjects = Subjects(year) if year else None
##
def SUBJECTS():
    if _Subject_Base.schoolyear != SCHOOLYEAR:
        _Subject_Base.set_year(SCHOOLYEAR)
    return _Subject_Base.subjects

###

def get_classes():
    subjects = SUBJECTS()
    clist = [(c, c) for c in subjects.classes()]
    CALLBACK('subjects_SET_CLASSES', classes = clist)
    return True

###

def edit_choices(klass):
    subjects = SUBJECTS()
    info = (
        (subjects.SCHOOLYEAR,    SCHOOLYEAR),
        (subjects.CLASS,         klass)
    )
    slist = []
    for sdata in subjects.class_subjects(klass):
#TODO: Should there be anything else in the choice table?
        if sdata.TIDS:
            # Add subject
            slist.append((sdata.SID, sdata.SUBJECT))
            continue    # Not a "real" subject
    pupils = PUPILS(SCHOOLYEAR)
    pupil_data = []
    for pdata in pupils.class_pupils(klass):
        pid = pdata['PID']
        pupil_data.append((pid, pupils.name(pdata), pdata['STREAM'],
                list(subjects.choices(pid))))
    CALLBACK('subjects_EDIT_CHOICES', info = info,
            pupil_data = pupil_data, subjects = slist)
    return True

###

def update_subjects(filepath):
    klass = SUBJECTS().import_source_table(filepath)
    REPORT('INFO', _SUBJECTS_CLASS.format(klass = klass))
    return True
#
#def select_choice_class():
#    subjects = SUBJECTS()
#    clist = [(c, subjects.CLASS + ' ' + print_class(c))
#            for c in subjects.classes()]
#    CALLBACK('subjects_SELECT_CHOICE_TABLE', classes = clist)
#    return True
#
def make_choice_table(klass, filepath):
    xlsx_bytes = SUBJECTS().make_choice_table(klass)
    with open(filepath, 'wb') as fh:
        fh.write(xlsx_bytes)
    REPORT('INFO', _CHOICES_SAVED.format(klass = klass, fpath = filepath))
    return True
#
def update_choice_table(filepath):
    klass = SUBJECTS().import_choice_table(filepath)
    REPORT('INFO', _CHOICES_CLASS.format(klass = klass))
    return True


FUNCTIONS['SUBJECT_get_classes'] = get_classes
FUNCTIONS['SUBJECT_table_update'] = update_subjects
FUNCTIONS['SUBJECT_edit_choices'] = edit_choices

#FUNCTIONS['SUBJECT_select_choice_class'] = select_choice_class
FUNCTIONS['SUBJECT_make_choice_table'] = make_choice_table
FUNCTIONS['SUBJECT_update_choice_table'] = update_choice_table
