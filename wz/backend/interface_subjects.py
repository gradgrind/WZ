# -*- coding: utf-8 -*-

"""
backend/interface_subjects.py - last updated 2021-05-22

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
_CHOICES_SAVED = "Fächerwahl für Klasse {klass} aktualisiert"
_CHOICE_TABLE_SAVED = "Fach-Wahl-Tabelle für Klasse {klass} gespeichert" \
        " als:\n  {fpath}"
_CHOICES_CLASS = "Fach-Wahl-Tabelle für Klasse {klass} aktualisiert"

from core.pupils import PUPILS
from core.courses import SUBJECTS, CourseError
from tables.spreadsheet import TableError

TRUE, FALSE = 'X', ''

### +++++

def get_classes():
    subjects = SUBJECTS(SCHOOLYEAR)
    clist = subjects.classes()
    clist.reverse()
    CALLBACK('subjects_SET_CLASSES', classes = clist)
    return True

###

def edit_choices(klass):
    subjects = SUBJECTS(SCHOOLYEAR)
    info = (
        (subjects.SCHOOLYEAR,    SCHOOLYEAR),
        (subjects.CLASS,         klass)
    )
    pid_sidmap, sid_name = subjects.class_subjects(klass)
    # Note that this includes "composite" subjects
    slist = [(sid, sname) for sid, sname in sid_name.items()]
    pupils = PUPILS(SCHOOLYEAR)
    pupil_data = []
    for pid, sid_sdata in pid_sidmap.items():
        pdata = pupils[pid]
        pid = pdata['PID']
        # Get saved choices
        pchoice = subjects.optouts(pid)
        clist = {sid: TRUE if sid in pchoice else FALSE
                for sid, sname in slist if sid in sid_sdata}
        pupil_data.append((pid, pupils.name(pdata), pdata['GROUPS'], clist))
    CALLBACK('subjects_EDIT_CHOICES', info = info,
            pupil_data = pupil_data, subjects = slist)
    return True

###

def save_choices(klass, data):
    """Save the choice table for the given pupils.
        <data>: [[pid, [sid, ... ]], ... ]
    """
    SUBJECTS(SCHOOLYEAR).save_choices(klass, data)
    REPORT('INFO', _CHOICES_SAVED.format(klass = klass))
    return get_classes()

###

def update_subjects(filepath):
    try:
        klass = SUBJECTS(SCHOOLYEAR).import_source_table(filepath)
    except (CourseError, TableError) as e:
        REPORT('ERROR', str(e))
    else:
        REPORT('INFO', _SUBJECTS_CLASS.format(klass = klass))
    return True
#
def make_choice_table(klass, filepath):
    xlsx_bytes = SUBJECTS(SCHOOLYEAR).make_choice_table(klass)
    with open(filepath, 'wb') as fh:
        fh.write(xlsx_bytes)
    REPORT('INFO', _CHOICE_TABLE_SAVED.format(klass = klass,
            fpath = filepath))
    return True
#
def update_choice_table(filepath):
    try:
        klass = SUBJECTS(SCHOOLYEAR).import_choice_table(filepath)
    except TableError as e:
        REPORT('ERROR', str(e))
    else:
        REPORT('INFO', _CHOICES_CLASS.format(klass = klass))
        get_classes()
    return True


########################################################################
def init():
    FUNCTIONS['SUBJECT_get_classes'] = get_classes
    FUNCTIONS['SUBJECT_table_update'] = update_subjects
    FUNCTIONS['SUBJECT_edit_choices'] = edit_choices
    FUNCTIONS['SUBJECT_save_choices'] = save_choices

    #FUNCTIONS['SUBJECT_select_choice_class'] = select_choice_class
    FUNCTIONS['SUBJECT_make_choice_table'] = make_choice_table
    FUNCTIONS['SUBJECT_update_choice_table'] = update_choice_table
