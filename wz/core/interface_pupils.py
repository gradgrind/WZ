# -*- coding: utf-8 -*-

"""
core/interface_pupils.py - last updated 2021-02-20

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
_PID_EXISTS = "Schülerkennung {pid} existiert schon"

from core.base import Dates
from core.pupils import Pupils
from local.grade_config import STREAMS

class _Pupil_Base:
    """A cache for pupil information.
    """
    schoolyear = None
    pupils = None
    klass = None
    pid = None
#
    @classmethod
    def set_year(cls, year = None):
        """Load pupil data for the given year. Clear data if no year.
        """
        if year == cls.schoolyear:
            return
        cls.schoolyear = year
        cls.pupils = Pupils(year) if year else None
        # Additional data used only in this module
        cls.klass = None
        cls.pid = None
##
def PUPILS():
    if _Pupil_Base.schoolyear != SCHOOLYEAR:
        _Pupil_Base.set_year(SCHOOLYEAR)
    return _Pupil_Base.pupils

###

class Pupils_Update:
    """Manage the updating of the pupil data from a "master" table.
    Fields not supplied in the master data will leave the field values
    in the application table unchanged. This allows certain fields to
    be maintained independently of the "master" database.
    """
    @classmethod
    def start(cls, filepath):
        pupils = PUPILS()
        try:
            cls.ptables = pupils.read_source_table(filepath)
        except:
            REPORT('ERROR', _BAD_PUPIL_TABLE.format(path = filepath))
            return False
        cls.compare()
        return True
#
    @classmethod
    def compare(cls):
        cls._changes = {}
        _delta = PUPILS().compare_update(cls.ptables)
        # Return the changes class-for-class
        for klass, kdata in _delta.items():
            CALLBACK('pupil_DELTA', klass = klass, delta = kdata)
        CALLBACK('pupil_DELTA_COMPLETE')
        return True
#
    @classmethod
    def class_delta(cls, klass, delta_list):
        cls._changes[klass] = delta_list
        return True
#
    @classmethod
    def update(cls):
        PUPILS().update_classes(cls._changes)
        return True

FUNCTIONS['PUPIL_table_delta'] = Pupils_Update.start
FUNCTIONS['PUPIL_table_delta2'] = Pupils_Update.compare
FUNCTIONS['PUPIL_class_update'] = Pupils_Update.class_delta
FUNCTIONS['PUPIL_table_update'] = Pupils_Update.update

###

class Pupil_Editor:
    """Editor for the data of individual pupils.
        1) entry: set classes -> ...
        2) select a class: set pupils -> ...
        3) select a pupil: show pupil data
    """
    @classmethod
    def enter(cls):
        pupils = PUPILS()
        cls._class_list = pupils.classes()
        cls._class_list.reverse()   # start with the highest classes
        klass = _Pupil_Base.klass if _Pupil_Base.klass in cls._class_list \
                else cls._class_list[0]
        _Pupil_Base.klass = None
        CALLBACK('pupil_SET_CLASSES',
                classes = cls._class_list,
                klass = klass)
        # This needs to signal "class changed" ...
        return True
#
    @classmethod
    def set_class(cls, klass):
        pupils = PUPILS()
        if klass not in cls._class_list:
            raise Bug('Invalid class passed from front-end: %s' %  klass)
        _Pupil_Base.klass = klass
        cls._pdata_list = pupils.class_pupils(klass)
        pupil_list = []
        pidix, ix = 0, -1
        for pd in cls._pdata_list:
            ix += 1
            _pid = pd['PID']
            if _pid == _Pupil_Base.pid:
                pidix = ix
            pupil_list.append((_pid, Pupils.name(pd)))
        pdata = cls._pdata_list[pidix]
        pid = pdata['PID']
        CALLBACK('pupil_SET_PUPILS',
                pupils = pupil_list,
                pid = pid)
        # This needs to signal "pupil changed" ...
        return True
#
    @classmethod
    def set_pupil(cls, pid):
        try:
            pdata = cls._pdata_list._pidmap[pid]
        except KeyError:
            raise Bug('Invalid pupil passed from front-end: %s' % pid)
        _Pupil_Base.pid = pid
        # Display pupil data
        CALLBACK('pupil_SET_PUPIL_DATA',
                data = pdata,
                name = Pupils.name(pdata))
        return True
#
    @classmethod
    def new_pupil(cls, pid = None):
        pupils = PUPILS()
        pdata = pupils.nullPupilData(_Pupil_Base.klass)
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
                    CALLBACK('pupil_NEW_PUPIL', data = pdata)
                    return True
        CALLBACK('pupil_NEW_PUPIL', data = pdata, ask_pid = pdata['PID'])
        return True
#
    @classmethod
    def new_data(cls, data):
        # Update pupil data in database
        if PUPILS().modify_pupil(data):
            _Pupil_Base.pid = data['PID']
            _Pupil_Base.klass = data['CLASS']
            CALLBACK('pupil_CLEAR_CHANGES')
            return cls.enter()
        return False
#
    @classmethod
    def remove(cls, pid):
        if PUPILS().remove_pupil(pid):
            CALLBACK('pupil_CLEAR_CHANGES')
            return cls.enter()
        return False

###

def get_leavers():
    """Get class lists of final classes – so that individuals can be
    selected to repeat a year.
    """
    classes = []
    pupils = PUPILS()
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
    PUPILS().migrate(repeat_pids)
#TODO: Copy the subject-data, as a "starting point" for the new year.
    # Create a rough calendar for the new year.
    Dates.migrate_calendar(SCHOOLYEAR)
    # Set years, select new one
    return FUNCTIONS['BASE_get_years'](str(int(SCHOOLYEAR) + 1))

###

def get_info():
    CALLBACK('pupil_SET_INFO',
            fields = [(f, t) for f, t in Pupils.FIELDS.items()],
            sex = Pupils.SEX,
            streams = STREAMS)
    return True

FUNCTIONS['PUPIL_get_info'] = get_info
FUNCTIONS['PUPIL_enter'] = Pupil_Editor.enter
FUNCTIONS['PUPIL_set_class'] = Pupil_Editor.set_class
FUNCTIONS['PUPIL_set_pupil'] = Pupil_Editor.set_pupil
FUNCTIONS['PUPIL_new_pupil'] = Pupil_Editor.new_pupil
FUNCTIONS['PUPIL_new_data'] = Pupil_Editor.new_data
FUNCTIONS['PUPIL_remove'] = Pupil_Editor.remove
FUNCTIONS['PUPILS_get_leavers'] = get_leavers
FUNCTIONS['PUPILS_migrate'] = migrate
