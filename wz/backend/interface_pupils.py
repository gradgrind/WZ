# -*- coding: utf-8 -*-

"""
backend/interface_pupils.py - last updated 2021-05-22

Controller/dispatcher for pupil management.

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
_BAD_PUPIL_TABLE = "Schülerdaten fehlerhaft:\n  {path}"
_BAD_CLASS_TABLE = "Ungültige Schülertabelle für Klasse {klass}:\n  {path}"
_PID_EXISTS = "Schülerkennung {pid} existiert schon"
_YEAR_ALREADY_EXISTS = "Neues Schuljahr: Daten für {year} existieren schon"
_NO_DELTA = "Keine Änderungen in angegebener Tabelle"
_UPDATED_SOME = "Die gewählten Änderungen wurden übernommen.\n" \
        "Die anderen werden noch angezeigt."
_UPDATED_ALL = "Alle Änderungen wurden übernommen"

from core.base import Dates
from core.pupils import PUPILS, Pupils_File, PupilError
from local.base_config import SubjectsBase, PupilsBase
#from local.grade_config import STREAMS
# year_path ... !
###

class Pupils_Update:
    """Manage the updating of the pupil data from a "master" table.
    Fields not supplied in the master data will leave the field values
    in the application table unchanged. This allows certain fields to
    be maintained independently of the "master" database.
    """
    @classmethod
    def start(cls, filepath):
        pupils = PUPILS(SCHOOLYEAR)
        try:
            cls.ptables = Pupils_File(SCHOOLYEAR, filepath,
                    norm_fields = False)
        except PupilError:
            REPORT('ERROR', _BAD_PUPIL_TABLE.format(path = filepath))
            return False
        if Pupil_Editor.klass:
            clist = cls.ptables.classes()
            if (len(clist) != 1) \
                    or (Pupil_Editor.klass not in clist):
                REPORT('ERROR', _BAD_CLASS_TABLE.format(
                        klass = Pupil_Editor.klass, path = filepath))
                return False
        cls.compare()
        return True
#
    @classmethod
    def compare(cls, rerun = False):
        cls._changes = {}   # Collect confirmed changes
        _delta = PUPILS(SCHOOLYEAR).compare_update(cls.ptables)
        # If limited to a single class, extract the data for this class
        if Pupil_Editor.klass:
            try:
                _delta = {Pupil_Editor.klass: _delta[Pupil_Editor.klass]}
            except KeyError:
                _delta = None
        if _delta:
            if rerun:
                REPORT('INFO', _UPDATED_SOME)
            CALLBACK('pupils_DELTA_START')
            # Return the changes class-for-class
            for klass, kdata in _delta.items():
                CALLBACK('pupils_DELTA', klass = klass, delta = kdata)
            CALLBACK('pupils_DELTA_COMPLETE')
        elif rerun:
            REPORT('INFO', _UPDATED_ALL)
            Pupil_Editor.get_classes(reset = False)
        else:
            REPORT('INFO', _NO_DELTA)
        return True
#
    @classmethod
    def class_delta(cls, klass, delta_list):
        cls._changes[klass] = delta_list
        return True
#
    @classmethod
    def update(cls):
        PUPILS(SCHOOLYEAR).update_classes(cls._changes)
        return cls.compare(rerun = True)

###

class Pupil_Editor:
    """Editor for the data of individual pupils.
        1) entry: set classes -> ...
        2) select a class: set pupils -> ...
        3) select a pupil: show pupil data
    """
    # Remember class and pupil-id
    klass = NONE
    pid = NONE

    @classmethod
    def get_classes(cls, reset = True):
        pupils = PUPILS(SCHOOLYEAR)
        cls._class_list = pupils.classes()
        cls._class_list.reverse()   # start with the highest classes
        if reset:
            cls.klass = NONE
            cls.pid = NONE
        elif cls.klass not in cls._class_list:
            cls.klass = NONE
        CALLBACK('pupils_SET_CLASSES',
                classes = cls._class_list,
                klass = cls.klass)
        # This needs to signal "class changed" ...
        return True
#
    @classmethod
    def set_class(cls, klass):
        _pid = cls.pid
        cls.pid = NONE
        plist = []
        cls.pdata_map = {}
        if klass:
            pupils = PUPILS(SCHOOLYEAR)
            if klass not in cls._class_list:
                raise Bug('Invalid class passed from front-end: %s' %  klass)
            cls.klass = klass
            for pd in pupils.class_pupils(klass):
                pid = pd['PID']
                plist.append((pid, pupils.name(pd)))
                cls.pdata_map[pid] = pd
                if pid == _pid:
                    cls.pid = pid
        else:
            cls.klass = NONE
        CALLBACK('pupils_SET_PUPILS',
                pupils = plist,
                pid = cls.pid)
        # This needs to signal "pupil changed" ...
        return True
#
    @classmethod
    def set_pupil(cls, pid):
        try:
            pdata = cls.pdata_map[pid]
        except KeyError:
            cls.pid = NONE
            if cls.klass:
                CALLBACK('pupils_SET_CLASS_VIEW',
                        pdata_list = list(cls.pdata_map.values()))
            else:
                CALLBACK('pupils_SET_INFO_VIEW')
        else:
            cls.pid = pid
            # Display pupil data
            CALLBACK('pupils_SET_PUPIL_VIEW', pdata = pdata,
                    name = PupilsBase.name(pdata))
        return True
#
    @classmethod
    def new_pupil(cls, pid = NONE):
        pupils = PUPILS(SCHOOLYEAR)
        pdata = pupils.nullPupilData(cls.klass)
        if pid:
            try:
                pupils.check_new_pid_valid(pid)
            except ValueError as e:
                pdata['__ERROR__'] = str(e)
            else:
                if pid in pupils:
                    pdata['__ERROR__'] = _PID_EXISTS.format(pid = pid)
                else:
                    pdata['PID'] = pid
                    CALLBACK('pupils_NEW_PUPIL', data = pdata)
                    return True
        CALLBACK('pupils_NEW_PUPIL', data = pdata, ask_pid = pdata['PID'])
        return True
#
    @classmethod
    def new_data(cls, data):
        """New data for a single pupil (from single-pupil editor).
        """
        # Update pupil data in database
        if PUPILS(SCHOOLYEAR).modify_pupil([data]):
            cls.pid = data['PID']
            cls.klass = data['CLASS']
            # Redisplay class and pid
            return cls.get_classes(reset = False)
        return False
#
    @classmethod
    def new_table_data(cls, data):
        """New data from class-table editor.
        """
        # Update pupil data in database
        if PUPILS(SCHOOLYEAR).modify_pupil(data):
            # Redisplay class and pid
            return cls.get_classes(reset = False)
        return False
#
    @classmethod
    def remove(cls, pid):
        if PUPILS(SCHOOLYEAR).remove_pupil(pid):
            # Redisplay class
            cls.pid = NONE
            return cls.get_classes(reset = False)
        return False
#
    @classmethod
    def export_data(cls, filepath, klass):
        PUPILS(SCHOOLYEAR).backup(filepath, klass)
        return True

###

def get_leavers():
    """The first stage of a migration to the next year. It is only
    available when there is currently no data for the next year.
    Get class lists of final classes – so that individuals can be
    selected to repeat a year.
    """
    nextyear = str(int(SCHOOLYEAR) + 1)
    if nextyear in Dates.get_years():
        REPORT('ERROR', _YEAR_ALREADY_EXISTS.format(year = nextyear))
        return False
    classes = []
    pupils = PUPILS(SCHOOLYEAR)
    for klass in pupils.classes():
        leavers = pupils.final_year_pupils(klass)
        if leavers:
            classes.append((klass, leavers))
    CALLBACK('calendar_SELECT_REPEATERS', klass_pupil_list = classes)
    return True
#
def migrate(repeat_pids):
    """Create a pupil-data structure for the following year.
    """
    # Create a pupil-data structure for the following year.
    PUPILS(SCHOOLYEAR).migrate(repeat_pids)
    # Copy the subject-data, as a "starting point" for the new year.
    subjects = Subjects(SCHOOLYEAR)
    subjects.migrate()
    # Create a rough calendar for the new year.
    Dates.migrate_calendar(SCHOOLYEAR)
    # Set years, select new one
    return FUNCTIONS['BASE_get_years'](str(int(SCHOOLYEAR) + 1))

###

def get_info():
    CALLBACK('pupils_SET_INFO',
            fields = [(f, t) for f, t in PupilsBase.FIELDS.items()],
            SEX = PupilsBase.SEX)
    return True

########################################################################
def init():
    FUNCTIONS['PUPILS_table_delta'] = Pupils_Update.start
    FUNCTIONS['PUPILS_table_delta2'] = Pupils_Update.compare
    FUNCTIONS['PUPILS_class_update'] = Pupils_Update.class_delta
    FUNCTIONS['PUPILS_table_update'] = Pupils_Update.update

    FUNCTIONS['PUPILS_get_info'] = get_info
    FUNCTIONS['PUPILS_get_classes'] = Pupil_Editor.get_classes
    FUNCTIONS['PUPILS_set_class'] = Pupil_Editor.set_class
    FUNCTIONS['PUPILS_set_pupil'] = Pupil_Editor.set_pupil
    FUNCTIONS['PUPILS_new_pupil'] = Pupil_Editor.new_pupil
    FUNCTIONS['PUPILS_new_data'] = Pupil_Editor.new_data
    FUNCTIONS['PUPILS_new_table_data'] = Pupil_Editor.new_table_data
    FUNCTIONS['PUPILS_remove'] = Pupil_Editor.remove
    FUNCTIONS['PUPILS_export_data'] = Pupil_Editor.export_data
    FUNCTIONS['PUPILS_get_leavers'] = get_leavers
    FUNCTIONS['PUPILS_migrate'] = migrate
