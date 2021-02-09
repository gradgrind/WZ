# -*- coding: utf-8 -*-

"""
core/interface_pupils.py - last updated 2021-02-08

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
import json

class Pupils_Update:
    """Manage the updating of the pupil data from a "master" table.
    Fields not supplied in the master data will leave the field values
    in the application table unchanged. This allows certain fields to
    be maintained independently of the "master" database.
    """
    _instance = None
    @classmethod
    def start(cls, filepath):
        self = cls()
        try:
            self.ptables = self.pupils.read_source_table(filepath)
        except:
            REPORT('ERROR', _BAD_PUPIL_TABLE.format(path = filepath))
            cls._instance = None
            return False
        cls._instance = self
        cls.compare()
        return True
#
    def __init__(self):
        self.pupils = Pupils(SCHOOLYEAR)
#
    @classmethod
    def compare(cls):
        self = cls._instance
        self._changes = {}
        _delta = self.pupils.compare_update(self.ptables)
        # Return the changes class-for-class as json
        for klass, kdata in _delta.items():
            klist = json.dumps(kdata)
            CALLBACK('pupil_DELTA', klass = klass, delta = klist)
        CALLBACK('pupil_DELTA_COMPLETE')
#
    @classmethod
    def class_delta(cls, klass, delta_list):
        self = cls._instance
        self._changes[klass] = json.loads(delta_list)
        return True
#
    @classmethod
    def update(cls):
        self = cls._instance
        self.pupils.update_classes(self._changes)
        return True

FUNCTIONS['PUPIL_table_delta'] = Pupils_Update.start
FUNCTIONS['PUPIL_table_delta2'] = Pupils_Update.compare
FUNCTIONS['PUPIL_class_update'] = Pupils_Update.class_delta
FUNCTIONS['PUPIL_table_update'] = Pupils_Update.update

###

#TODO
class Pupil_Editor:
    _instance = None
    @classmethod

    def __init__(self):
        ### State variables
#        self.schoolyear = SCHOOLYEAR
        # These can persist after leaving the pupils tab
        self.klass = None
        self.pid = None
        # These don't persist after leaving the pupils tab
        self._class_list = None
        self._pdata_list = None
        self._pdata = None
#

# Maybe:
# 1) set classes
# 2) select a class ->
# 3) set pupils
# 4) select a pupil ->
# 5) show pupil data
    def enter(self):
# No pupil should be selected (there should be no pupils yet)
        self.schoolyear = SCHOOLYEAR
        self.pupils = Pupils(SCHOOLYEAR)
        self._class_list = self.pupils.classes()
        self._class_list.reverse()   # start with the highest classes
        klass = self.klass if self.klass in self._class_list \
                else self._class_list[0]
        self.klass = None
        CALLBACK('pupil_CLASSES',
                classes = json.dumps(self._class_list),
                klass = klass)
        # This needs to signal "class changed" ...
#
    def set_class(self, klass):
        if klass not in self._class_list:
            raise Bug('Invalid class passed from front-end: %s' %  klass)
        self.klass = klass
        self._pdata_list = self.pupils.class_pupils(klass)
        pupil_list = []
        pidix, ix = 0, -1
        for pd in self._pdata_list:
            ix += 1
            _pid = pd['PID']
            if _pid == self.pid:
                pidix = ix
            _pname = Pupils.name(pd)
            pupil_list.append(f'{_pid}|{_pname}')
        pdata = self._pdata_list[pidix]
        pid = self._pdata['PID']
        CALLBACK('pupil_PUPILS',
                pupils = json.dumps(pupil_list),
                pid = pid)
        # This needs to signal "pupil changed" ...
#
    def set_pupil(self, ptag):
        pid, pname = ptag.split('|', 1)
        for pd in self._pdata_list:
            if pd['PID'] == pid:
                self._pdata = pd
                self.pid = pid
                break
        else:
            raise Bug('Invalid pupil passed from front-end: %s' % ptag)
#TODO: Display pupil data
