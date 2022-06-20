"""
core/basic_data.py - last updated 2022-06-20

Handle caching of the basic data sources

==============================
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
"""

from core.db_management import db_key_value_list
from core.classes import Classes
from core.teachers import Teachers

SHARED_DATA = {}

### -----


def clear_cache():
    SHARED_DATA.clear()


def get_classes() -> Classes:
    """Return the data for all classes as a <Classes> instance (dict).
    This data is cached, so subsequent calls get the same instance.
    """
    try:
        return SHARED_DATA["CLASSES"]
    except KeyError:
        pass
    classes = Classes()
    SHARED_DATA["CLASSES"] = classes
    return classes


def get_teachers() -> Teachers:
    """Return the data for all teachers as a <Teachers> instance (dict).
    This data is cached, so subsequent calls get the same instance.
    """
    try:
        return SHARED_DATA["TEACHERS"]
    except KeyError:
        pass
    teachers = Teachers()
    SHARED_DATA["TEACHERS"] = teachers
    return teachers


def get_subjects():
    """Return an ordered mapping of subjects: {sid -> name}.
    This data is cached, so subsequent calls get the same instance.
    """
    try:
        return SHARED_DATA["SUBJECTS"]
    except KeyError:
        pass
    subjects = dict(
        db_key_value_list("SUBJECTS", "SID", "NAME", sort_field="NAME")
    )
    SHARED_DATA["SUBJECTS"] = subjects
    return subjects


def get_rooms() -> dict[str, str]:
    """Return an ordered mapping of rooms: {rid -> name}.
    This data is cached, so subsequent calls get the same instance.
    """
    try:
        return SHARED_DATA["ROOMS"]
    except KeyError:
        pass
    rooms = dict(db_key_value_list("TT_ROOMS", "RID", "NAME", sort_field="RID"))
    SHARED_DATA["ROOMS"] = rooms
    return rooms
