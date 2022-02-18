"""
misc/convert_old_class_periods.py - last updated 2022-02-11

Convert a single class-periods table to a folder of individual tables.

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

### Messages
_CLASS_INVALID = (
    "Klassenbezeichnungen dürfen nur aus Zahlen und"
    " lateinischen Buchstaben bestehen: {klass} ist ungültig."
)

########################################################################

import sys, os

if __name__ == "__main__":
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    #start.setup(os.path.join(basedir, 'TESTDATA'))
    #start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "NEXT"))

### +++++

from tables.spreadsheet import read_DataTable, filter_DataTable, \
    make_DataTable, TableError


class TT_Error(Exception):
    pass

from typing import NamedTuple, Dict, List

### -----

class Day(NamedTuple):
    short: str      # Short name (e.g. "Do")
    full: str       # Full name (e.g. "Donnerstag")
    tag: str        # Day number as string, starting at "1"
    bitmap: int     # Each day has a bit, e.g. 8 (2^3) for the fourth day

class TT_Days(List[Day]):
    """Manage various representations of the days of the (timetable) week.
    The primary internal representation of a day is the index, starting
    at 0 for the first day of the school week.
    """
    def __init__(self):
        super().__init__()
        b = 1   # for bitmap
        i = 0   # for tag
        for k, l in MINION(DATAPATH("TIMETABLE/DAYS"))["DAYS"]:
            i += 1
            self.append(Day(k, l, str(i), b))
            b *= 2

    def bitstring(self, day:int) -> str:
        """Return the bitmap as a string of 1s and 0s, but reversed, so
        that the first day comes first in the string.
        """
        return f"{self[day].bitmap:0{len(self)}b}"[::-1]


class Period(NamedTuple):
    short: str      # Short name (e.g. "2")
    full: str       # Full name (e.g. "2. Fachstunde")
    tag: str        # Period number as string, starting at "1"
    starttime: str  # Time of period start
    endtime: str    # Time of period end

class TT_Periods(List[Period]):
    """Manage information about the periods of the school day.
    The primary internal representation of a period is the index, starting
    at 0 for the first period of the school day.
    """
    def __init__(self):
        super().__init__()
        i = 0
        for k, l, s, e in MINION(DATAPATH("TIMETABLE/PERIODS"))["PERIODS"]:
            i += 1
            self.append(Period(k, l, str(i), s, e))


def class_periods_convert(days, periods, filetype='tsv'):
    class_days_periods = {}
    periods = periods
    xdays = None
    ptags = [
        {"NAME": "CLASS",  "DISPLAY_NAME": "Klasse", "REQUIRED": "true"},
        {"NAME": "DAY",    "DISPLAY_NAME": "Tag", "REQUIRED": "true"}
    ] + [{"NAME": p.short} for p in periods]
    class_table = read_DataTable(DATAPATH("OLD/Klassen_Stunden"))
    class_table = filter_DataTable(
        class_table,
        {"INFO_FIELDS": [], "TABLE_FIELDS": ptags},
        extend=False,
    )["__ROWS__"]
    for row in class_table:
        klass = row.pop("CLASS")
        if not klass.isalnum():
            raise ValueError(_CLASS_INVALID.format(klass=klass))
        day = row.pop("DAY")
        if xdays:
            if xdays[-1] != day:
                xdays.append(day)
        else:
            xdays = [day]
        try:
            kmap = class_days_periods[klass]
        except KeyError:
            class_days_periods[klass] = {day: row}
        else:
            if day in kmap:
                raise TT_Error(
                    _CLASS_TABLE_DAY_DOUBLE.format(klass=klass, day=day)
                )
            kmap[day] = row

    fields = MINION(DATAPATH("TIMETABLE/CLASS_PERIODS_FIELDS"))
    tf = fields["TABLE_FIELDS"] + [{"NAME": p.short} for p in periods]
    fields["TABLE_FIELDS"] = tf
    fnames = [f["NAME"] for f in tf]
    #print("fnames:", fnames)

    folder = DATAPATH("testing/tmp/CLASSES")
    if not os.path.isdir(folder):
        os.makedirs(folder)

    lbperiods = ('5', '4', '3')
    for k, v in class_days_periods.items():
        info = {"CLASS": k}
        rows = []
        for d in days:
            day = d.short
            pmap = v[day]
            # Add (possible) lunch breaks
            for p in lbperiods:
                if not pmap[p]:
                    break
            else:
                for p in lbperiods:
                    pmap[p] = '+'
            row = {
                "DAY": day,
                "FULL_DAY": d.full
            }
            for p in periods:
                period = p.short
                row[period] = pmap[period]
            rows.append(row)
        data = {
            "__INFO__": info,
            "__ROWS__": rows,
            "__FIELDS__": fnames
        }
#        print("\n", data)

        fpath = os.path.join(folder, k)
        tbytes = make_DataTable(data, filetype, fields)
        with open(f"{fpath}.{filetype}", 'wb') as fh:
            fh.write(tbytes)
        print(f"  -> {fpath}.{filetype}")


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    print("\nDAYS: {len(days)}")
    days = TT_Days()
    i = 0
    for d in days:
        print(f"  {d} // {days.bitstring(i)}")
        i += 1

    print("\nPERIODS: {len(periods)}")
    periods = TT_Periods()
    for p in periods:
        print(f"  {p}")

    print("\nCLASSES:")
    class_periods_convert(days, periods)
