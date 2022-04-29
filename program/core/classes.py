"""
core/classes.py - last updated 2022-04-27

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

#T = TRANSLATIONS("core.classes")

### +++++

from core.db_management import open_database, db_key_value_list, db_values

### -----

def get_class_list(skip_null=True):
#?    open_database()

    classes = []
    for k, v in db_key_value_list("CLASSES", "CLASS", "NAME", "CLASS"):
        if k == '--' and skip_null:
            continue
        classes.append((k, v))
    return classes

def get_classroom(klass):
    vlist = db_values("CLASSES", "CLASSROOM", CLASS=klass)
    if len(vlist) != 1:
        raise Bug(f"Single entry expected, not {repr(vlist)}")
    return vlist[0]


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    open_database()
    for k, v in get_class_list(False):
        print(f" ::: {k:6}: {v} // {get_classroom(k)}")

