"""
core/classes.py - last updated 2022-06-16

Manage class data.

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
"""

########################################################################

if __name__ == "__main__":
    import sys, os

    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    #    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))

T = TRANSLATIONS("core.classes")

### +++++

from typing import NamedTuple

from core.db_management import (
    open_database,
    db_read_fields,
    db_key_value_list,
    db_values,
)

### -----


class ClassData(NamedTuple):
    klass: str
    name: str
    divisions: list[list[str]]
    classroom: str
    tt_data: str


class Classes(dict):
    def __init__(self):
        super().__init__()
        # ?    open_database()
        for klass, name, divisions, classroom, tt_data in db_read_fields(
            "CLASSES",
            ("CLASS", "NAME", "DIVISIONS", "CLASSROOM", "TT_DATA"),
            sort_field="CLASS"
        ):
            # Parse groups
            divlist = []
            if divisions:
                for div in divisions.split("|"):
                    # print("???", klass, repr(div))
                    groups = div.split()
                    if groups:
                        divlist.append(groups)
                    else:
                        SHOW_ERROR(T["INVALID_GROUP_FIELD"].format(klass=klass))
            self[klass] = ClassData(
                klass=klass,
                name=name,
                divisions=divlist,
                classroom=classroom,
                tt_data=tt_data,
            )

    def get_class_list(self, skip_null=True):
        classes = []
        for k, data in self.items():
            if k == "--" and skip_null:
                continue
            classes.append((k, data.name))
        return classes

    def get_classroom(self, klass):
        return self[klass].classroom


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    open_database()
    _classes = Classes()
    for cdata in _classes.values():
        print("\n", cdata)

    print("\n -------------------------------\n")

    for k, v in _classes.get_class_list(False):
        print(f" ::: {k:6}: {v} // {_classes.get_classroom(k)}")
