"""
core/basic_data.py - last updated 2022-07-08

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

T = TRANSLATIONS("core.basic_data")

### +++++

from typing import Optional, NamedTuple

from core.db_management import (
    db_read_unique_field,
    db_key_value_list,
    KeyValueList
)
from core.classes import Classes
from core.teachers import Teachers
from ui.ui_base import QRegularExpression  ### QtCore

SHARED_DATA = {}

DECIMAL_SEP = CONFIG["DECIMAL_SEP"]
PAYROLL_FORMAT = "[1-9]?[0-9](?:$[0-9]{1,3})?".replace("$", DECIMAL_SEP)

### -----


def clear_cache():
    # IMPORTANT: This must be called after any data change.
    SHARED_DATA.clear()


def get_days() -> KeyValueList:
    """Return the timetable days as a KeyValueList of (tag, name) pairs.
    This data is cached, so subsequent calls get the same instance.
    """
    try:
        return SHARED_DATA["DAYS"]
    except KeyError:
        pass
    days = db_key_value_list("TT_DAYS", "TAG", "NAME", "N")
    SHARED_DATA["DAYS"] = days
    return days


def get_periods() -> KeyValueList:
    """Return the timetable "periods" as a KeyValueList of (tag, name) pairs.
    This data is cached, so subsequent calls get the same instance.
    """
    try:
        return SHARED_DATA["PERIODS"]
    except KeyError:
        pass
    periods = db_key_value_list("TT_PERIODS", "TAG", "NAME", "N")
    SHARED_DATA["PERIODS"] = periods
    return periods


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


def get_subjects() -> KeyValueList:
    """Return the subjects as a KeyValueList of (sid, name) pairs.
    This data is cached, so subsequent calls get the same instance.
    """
    try:
        return SHARED_DATA["SUBJECTS"]
    except KeyError:
        pass
    subjects = db_key_value_list("SUBJECTS", "SID", "NAME", sort_field="NAME")
    SHARED_DATA["SUBJECTS"] = subjects
    return subjects


def get_rooms() -> KeyValueList:
    """Return the rooms as a KeyValueList of (rid, name) pairs.
    This data is cached, so subsequent calls get the same instance.
    """
    try:
        return SHARED_DATA["ROOMS"]
    except KeyError:
        pass
    rooms = db_key_value_list("TT_ROOMS", "RID", "NAME", sort_field="RID")
    SHARED_DATA["ROOMS"] = rooms
    return rooms


def get_payroll_weights() -> KeyValueList:
    """Return the "payroll lesson weightings" as a KeyValueList of
    (tag, weight) pairs.
    This data is cached, so subsequent calls get the same instance.
    """

    def check(item):
        i2 = item[1]
        if regexp.match(i2).hasMatch():
            return i2
        else:
            SHOW_ERROR(T["BAD_WEIGHT"].format(key=item[0], val=i2))
            return None

    regexp = QRegularExpression(f"^{PAYROLL_FORMAT}$")
    try:
        return SHARED_DATA["PAYROLL"]
    except KeyError:
        pass
    payroll_weights = db_key_value_list(
        "XDPT_WEIGHTINGS", "TAG", "WEIGHT", check=check
    )
    SHARED_DATA["PAYROLL"] = payroll_weights
    return payroll_weights


class BlockTag(NamedTuple):
    sid: str
    tag: str    # includes the '#'
    subject: str

    def __str__(self):
        return f">{self.sid}{self.tag}"


def read_blocktag(tag: str) -> BlockTag:
    """Return block subject and #-tag for a block-tag.
    An invalid value raises a <ValueError> exception.
    """
    try:
        i = tag.index("#")
        sid = tag[1:i]  # strips initial ">"
        sbj = get_subjects().map(sid)
    except ValueError:
        raise ValueError(T["BLOCKTAG_INVALID"].format(tag=tag))
    except KeyError:
        raise ValueError(T["BLOCKTAG_UNKNOWN_SUBJECT"].format(tag=tag, sid=sid))
    return BlockTag(sid, tag[i:], sbj)


def check_lesson_length(length: str) -> int:
    """Return the length of a valid lesson duration as an <int>.
    Otherwise raise a <ValueError> exception.
    """
    try:
        i = int(length)
    except ValueError:
        raise ValueError(T["LENGTH_NOT_NUMBER"].format(val=length))
    if i < 1 or i > len(get_periods()):
        raise ValueError(T["LENGTH_NOT_VALID"].format(val=length))
    return i


class PayrollData(NamedTuple):
    number: Optional[float]
    factor: Optional[float]
    text: str

    def isNone(self):
        return self.factor is None

    def __str__(self):
        return self.text


def read_payroll(payroll: str) -> PayrollData:
    """Read the individual parts of a payroll entry.
    If the input is invalid a <ValueError> exception wil be raised.
    """
    if not payroll:
        return PayrollData(None, None, "")
    try:
        n, f = payroll.split("*", 1)  # can raise ValueError
    except ValueError:
        raise ValueError(T["INVALID_PAYROLL"].format(text=payroll))
    if n:
        regexp = QRegularExpression(f"^{PAYROLL_FORMAT}$")
        if regexp.match(n).hasMatch():
            nn = float(n.replace(",", "."))
        else:
            raise ValueError(T["BAD_NUMBER"].format(val=n))
    else:
        nn = None
    try:
        nf = float(get_payroll_weights().map(f).replace(",", "."))
    except KeyError:
        raise ValueError(T["UNKNOWN_PAYROLL_WEIGHT"].format(key=f))
    return PayrollData(nn, nf, payroll)


# ********** Handling the data in TIME-fields **********

def read_time_field(tag):
    """Convert a lesson time-field to a (Time, Tag) pair – assuming
    the given value is a valid time slot or "partners" tag.
    """
    if tag.startswith("="):
        tag = tag[1:]
        return get_time_entry(tag), tag
    else:
        # Check validity of time
        return check_start_time(tag), ""


def timeslot2index(timeslot):
    """Convert a "timeslot" in the tag-form (e.g. "Mo.3") to a pair
    of 0-based indexes, (day, period).
    THere may be a "?"-prefix, indicating that the time is not fixed.
    Both a null value and a single "?" are accepted as "unspecified time",
    returning (-1, -1).
    Invalid values cause a <ValueError> exception.
    """
    if timeslot and timeslot != "?":
        if timeslot[0] == "?":
            # Remove "unfixed" flag
            timeslot = timeslot[1:]
        d, p = timeslot.split(".")  # Can raise <ValueError>
        try:
            return (get_days().index(d), get_periods().index(p))
        except KeyError:
            raise ValueError(T["INVALID_TIMESLOT"].format(val=timeslot))
    return -1, -1


def index2timeslot(index):
    """Convert a pair of 0-based indexes to a "timeslot" in the
    tag-form (e.g. "Mo.3").
    """
    d = get_days()[index[0]][0]
    p = get_periods()[index[1]][0]
    return f"{d}.{p}"


def get_time_entry(tag):
    try:
        ltime = db_read_unique_field("LESSONS", "TIME", PLACE=f"={tag}")
    except NoRecord:
        raise ValueError(T["NO_TIME_FOR_PARTNERS"].format(tag=tag))
#TODO: -- or ...
        REPORT("ERROR", T["NO_TIME_FOR_PARTNERS"].format(tag=tag))
        # TODO: add a time entry?
        # TIME="?", PLACE=f"={tag}", everything else empty
        return "?"
    # Check validity
    return check_start_time(ltime)


def check_start_time(tag):
    if tag.startswith("@"):
        ltime = tag[1:]
        timeslot2index(ltime)
        return ltime
    raise ValueError(T['BAD_TIME'].format(tag=tag))
#TODO: -- or ...
    REPORT("ERROR", T['BAD_TIME'].format(tag=tag))
    return "?"

