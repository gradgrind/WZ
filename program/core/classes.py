"""
core/classes.py - last updated 2022-06-07

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


def get_classes_data():
    # ?    open_database()
    classes = []
    for klass, name, divisions, classroom, tt_data in db_read_fields(
        "CLASSES", ("CLASS", "NAME", "DIVISIONS", "CLASSROOM", "TT_DATA")
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
        classes.append(
            (
                klass,
                ClassData(
                    klass=klass,
                    name=name,
                    divisions=divlist,
                    classroom=classroom,
                    tt_data=tt_data,
                ),
            )
        )
    return dict(sorted(classes))


def get_class_list(skip_null=True):
    # ?    open_database()
    classes = []
    for k, v in db_key_value_list("CLASSES", "CLASS", "NAME", "CLASS"):
        if k == "--" and skip_null:
            continue
        classes.append((k, v))
    return classes


def get_classroom(klass):
    # ?    open_database()
    vlist = db_values("CLASSES", "CLASSROOM", CLASS=klass)
    if len(vlist) != 1:
        raise Bug(f"Single entry expected, not {repr(vlist)}")
    return vlist[0]


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    open_database()
    _classes = get_classes_data()
    for cdata in _classes.values():
        print("\n", cdata)

    print("\n -------------------------------\n")

    for k, v in get_class_list(False):
        print(f" ::: {k:6}: {v} // {get_classroom(k)}")
