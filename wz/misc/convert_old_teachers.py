"""
misc/convert_old_teachers.py - last updated 2022-02-12

Convert a single teachers table to a folder of individual tables.

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
_UNBROKEN_WITH_LUNCH = (
    "Lehrer-Tabelle: für {tname} ist sowohl Blocklänge"
    " wie auch Mittag angegeben"
)
_TEACHER_INVALID = (
    "Lehrerkürzel dürfen nur aus Zahlen und"
    " lateinischen Buchstaben bestehen: {tid} ist ungültig."
)
_TEACHER_NDAYS = (
    "{name} ({tid}), verfügbare Stunden: Daten für genau"
    " {ndays} Tage sind notwendig"
)
_TEACHER_DAYS_INVALID = "{name} ({tid}), verfügbare Stunden: ungültige Daten"


########################################################################

import sys, os

if __name__ == "__main__":
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    start.setup(os.path.join(basedir, 'TESTDATA'))
    #start.setup(os.path.join(basedir, 'DATA'))
    #start.setup(os.path.join(basedir, "NEXT"))

### +++++

from tables.spreadsheet import read_DataTable, filter_DataTable, \
    make_DataTable, TableError
from misc.teachers import Teachers


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


class TT_TeachersX(dict):
    NO = "0"
    YES = "1"

    def __init__(self, days, periods):
        def sequence(period_string):
            """Generator function for the characters of a string."""
            for ch in period_string:
                yield ch

        def get_minlessons(val, message, teacher=None):
            try:
                n = int(val)
                if n < 0 or n > len(periods):
                    raise ValueError
            except ValueError:
                raise TT_Error(message.format(val=val, teacher=teacher))
            return n

        def get_lunch_periods(val, message, teacher=None):
            plist = []
            for p in val.split():
                if p in plist or p not in periods:
                    raise TT_Error(message.format(val=val, teacher=teacher))
                plist.append(p)
            return plist

        def get_lessons_weight(val, message, teacher=None):
            try:
                x, w = [int(a) for a in val.split("@")]
                if x < 0 or x > 10:
                    raise ValueError
                if w < 0 or w > 10:
                    raise ValueError
            except:
                raise TT_Error(message.format(val=val, teacher=teacher))
            return x, w

        def get_gaps(val, message, teacher=None):
            try:
                x = int(val)
                if x < 0 or x > 10:
                    raise ValueError
            except:
                raise TT_Error(message.format(val=val, teacher=teacher))
            return x

        super().__init__()
        self.alphatag = {}  # shortened, ASCII version of name, sortable
        teachers = Teachers()
        self.blocked_periods = {}
        self.constraints = {}
        _teachers = {}  # buffer to allow resorting
        for tid, tdata in teachers.items():
            tname, times = teachers.name(tid), tdata["AVAILABLE"]
            if not tid.isalnum():
                raise TT_Error(_TEACHER_INVALID.format(tid=tid))
            self.alphatag[tid] = tdata["SORTNAME"]
            _teachers[tid] = tname
            if times:
                day_list = [d.strip() for d in times.split(",")]
                if len(day_list) != len(days):
                    raise TT_Error(
                        _TEACHER_NDAYS.format(
                            name=tname, tid=tid, ndays=len(days)
                        )
                    )
                dlist = []
                for dperiods in day_list:
                    pblist = []
                    val = None
                    rd = sequence(dperiods)
                    for p in periods:
                        try:
                            b = next(rd)
                            if b == self.YES:
                                val = "X"  # not blocked
                            elif b == self.NO:
                                val = ""   # blocked
                            else:
                                val = None
                                raise StopIteration
                        except StopIteration:
                            if val == None:
                                raise TT_Error(
                                    _TEACHER_DAYS_INVALID.format(
                                        name=tname, tid=tid
                                    )
                                )
                        pblist.append(val)
                    dlist.append(pblist)
                self.blocked_periods[tid] = dlist
            g = tdata["MAXGAPSPERWEEK"]
            u = tdata["MAXBLOCK"]
            m = tdata["MINPERDAY"]
            l = tdata["LUNCHBREAK"]
            if l and u:
                REPORT("WARNING", _UNBROKEN_WITH_LUNCH.format(tname=tname))
            self.constraints[tid] = {
                "MAXGAPSPERDAY": "*" if g else "",
                "MAXGAPSPERWEEK": g,
                "MAXBLOCK": u,
                "MINPERDAY": m,
                "LUNCHBREAK": l,
            }
        # Sort tags alphabetically (to make finding them easier)
        for t in sorted(_teachers):
            self[t] = _teachers[t]


def teachers_convert(days, periods, filetype='tsv'):
    teachers = TT_TeachersX(
        {d.short: d for d in days},
        {p.short: p for p in periods}
    )
    fields = MINION(DATAPATH("CONFIG/TEACHER_FIELDS"))
    tf = fields["TABLE_FIELDS"]
    for p in periods:
        tf.append({
            "NAME": p.short
        })
    fields["TABLE_FIELDS"] = tf
    fnames = [f["NAME"] for f in tf]
    #print("fnames:", fnames)

    folder = DATAPATH("testing/tmp/TEACHERS")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    lbperiods = ('5', '4', '3')
    for k, v in teachers.items():
        info = {
            "NAME": v,
            "TID": k,
            "SORTNAME": teachers.alphatag[k]
        }
        info.update(teachers.constraints[k])
        blocked = teachers.blocked_periods.get(k)
        if not blocked:
            continue
        rows = []
        for d in days:
            ddata = blocked.pop(0)
            day = d.short
            row = {
                "DAY": day,
                "FULL_DAY": d.full
            }
            for p in periods:
                period = p.short
                row[period] = ddata.pop(0)
            rows.append(row)
            if info["LUNCHBREAK"]:
                # Add (possible) lunch breaks
                for p in lbperiods:
                    if not row[p]:
                        break
                else:
                    for p in lbperiods:
                        row[p] = '+'

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

    print("\nTEACHERS:")
    teachers_convert(days, periods)
