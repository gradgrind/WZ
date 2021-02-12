# -*- coding: utf-8 -*-

"""
core/interface_pupils.py - last updated 2021-02-12

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

from core.pupils import Pupils
from local.grade_config import STREAMS

class Pupil_Base:
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
        cls.klass = None
        cls.pid = None
        cls.pupils = Pupils(year) if year else None
#
    @classmethod
    def classes(cls):
        if not cls.pupils:
            cls.set_year(SCHOOLYEAR)
        return cls.pupils.classes()

###

class Pupils_Update:
    """Manage the updating of the pupil data from a "master" table.
    Fields not supplied in the master data will leave the field values
    in the application table unchanged. This allows certain fields to
    be maintained independently of the "master" database.
    """
    @classmethod
    def start(cls, filepath):
        try:
            cls.ptables = Pupil_Base.pupils.read_source_table(filepath)
        except:
            REPORT('ERROR', _BAD_PUPIL_TABLE.format(path = filepath))
            return False
        Pupil_Base.set_year(SCHOOLYEAR)
        cls.compare()
        return True
#
    @classmethod
    def compare(cls):
        cls._changes = {}
        _delta = Pupil_Base.pupils.compare_update(cls.ptables)
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
        Pupil_Base.pupils.update_classes(cls._changes)
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
        cls._class_list = Pupil_Base.classes()
        cls._class_list.reverse()   # start with the highest classes
        klass = Pupil_Base.klass if Pupil_Base.klass in cls._class_list \
                else cls._class_list[0]
        Pupil_Base.klass = None
        CALLBACK('pupil_SET_CLASSES',
                classes = cls._class_list,
                klass = klass)
        # This needs to signal "class changed" ...
        return True
#
    @classmethod
    def set_class(cls, klass):
        if klass not in cls._class_list:
            raise Bug('Invalid class passed from front-end: %s' %  klass)
        Pupil_Base.klass = klass
        cls._pdata_list = Pupil_Base.pupils.class_pupils(klass)
        pupil_list = []
        pidix, ix = 0, -1
        for pd in cls._pdata_list:
            ix += 1
            _pid = pd['PID']
            if _pid == Pupil_Base.pid:
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
        Pupil_Base.pid = pid
        # Display pupil data
        CALLBACK('pupil_SET_PUPIL_DATA',
                data = pdata,
                name = Pupils.name(pdata))
        return True
#
    @classmethod
    def new_pupil(cls):
        pdata = Pupils.nullPupilData(Pupil_Base)
        CALLBACK('pupil_NEW_PUPIL', data = pdata)
        return True
#
    @classmethod
    def new_data(cls, data):
        # Update pupil data in database
        if Pupil_Base.pupils.modify_pupil(data):
            if not data.get('*REMOVE*'):
                Pupil_Base.pid = data['PID']
                Pupil_Base.klass = data['CLASS']
            CALLBACK('pupil_CLEAR_CHANGES')
            return cls.enter()
        return False

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
