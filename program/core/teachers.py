"""
core/teachers.py - last updated 2022-02-12

Manage teacher data.

=+LICENCE=================================
Copyright 2022 Michael Towers

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
=-LICENCE=================================

The teachers' data is supplied in individual "DataTables".
In this module there is support for reading these tables.
"""

### Messages
_FILTER_ERROR = "Lehrerdaten-Fehler: {msg}"
_DOUBLE_TID = "Lehrerdaten-Fehler: Kürzel {tid} doppelt vorhanden"
_TEACHER_INVALID = "Lehrerkürzel „{tid}“ ist ungültig, in\n  {path}"

###############################################################

import sys, os

if __name__ == "__main__":
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    #    start.setup(os.path.join(basedir, "DATA"))
    start.setup(os.path.join(basedir, "NEXT"))

### +++++

from tables.spreadsheet import (
    read_DataTable,
    filter_DataTable,
    TableError,
)

class TeacherError(Exception):
    pass

### -----


def Teachers():
    return __TeachersCache._instance()


class __TeachersCache(dict):
    """Handler for teacher data.
    The internal teacher data should be read and written only through this
    interface.
    An instance of this class is a <dict> holding the teacher data as a
    mapping: {tid -> {field: value, ...}}.
    The fields defined for a teacher are read from the configuration file
    CONFIG/TEACHER_FIELDS.
    This is a "singleton" class, i.e. there should be only one instance,
    which is accessible via the <_instance> method.
    """
    __instance = None

    @classmethod
    def _clear_cache(cls):
        cls.__instance = None

    @classmethod
    def _instance(cls):
        """Fetch the cached instance of this class.
        If the school-year has changed, reinitialize the instance.
        """
        try:
            if cls.__instance.__schoolyear == SCHOOLYEAR:
                return cls.__instance
        except:
            pass
        cls.__instance = cls()
        cls.__instance.__schoolyear = SCHOOLYEAR
        return cls.__instance

    def __init__(self):
        super().__init__()
        folder = DATAPATH("TEACHERS")
        self.fields = MINION(DATAPATH("CONFIG/TEACHER_FIELDS"))
        for f in os.listdir(folder):
            fpath = os.path.join(folder, f)
            try:
                ttable = read_DataTable(fpath)
                ttable = filter_DataTable(ttable, self.fields, matrix=True)
            except TableError as e:
                raise TeacherError(_FILTER_ERROR.format(msg=f"{e} in\n {fpath}"))
            info = ttable["__INFO__"]
            tid = info.pop("TID")
            if not tid.isalnum():
                raise Teacher(_TEACHER_INVALID.format(tid=tid, path=fpath))
            available = {}
            info["AVAILABLE"] = available
            for row in ttable["__ROWS__"]:
                day = row.pop("DAY")
                del(row["FULL_DAY"])
                available[day] = row
            if tid in self:
                raise TeacherError(_DOUBLE_TID.format(tid=tid))
            self[tid] = info

    def name(self, tid):
        return self[tid]["NAME"].replace("|", "")

    def list_teachers(self):
        """Return a sorted list of teacher ids.
        """
        return sorted(self, key=lambda x:self[x]["SORTNAME"])


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    teachers = Teachers()
    for tid in teachers.list_teachers():
        print(f"  {tid}: {teachers.name(tid)} // {teachers[tid]}")
