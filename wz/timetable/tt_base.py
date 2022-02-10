"""
timetable/tt_base.py - last updated 2022-02-10

Read timetable information from the various sources ...

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

_MAX_DURATION = 4  # maximum length of a lesson

### Messages

_BAD_COURSE_FILE = (
    "Klasse {klass}: Kursdaten konnten nicht eingelesen"
    " werden\n       ({path})\n --> {report}"
)
_TAG_INVALID = "Klasse {klass}, Fach {sname}: Kennung '{tag}' ist ungültig"
_CLASS_INVALID = (
    "Klassenbezeichnungen dürfen nur aus Zahlen und"
    " lateinischen Buchstaben bestehen: {klass} ist ungültig."
)
_CLASS_TABLE_DAY_DOUBLE = (
    "In der Klassen-Tage-Tabelle: Für Klasse {klass}"
    " gibt es zwei Einträge für Tag {day}."
)
_UNKNOWN_GROUP = "Klasse {klass}: unbekannte Gruppe – '{group}'"
_GROUP_IN_MULTIPLE_SPLITS = "Klasse {klass}: Gruppe {group} in >1 Teilung"
_INVALID_ENTRY = (
    "Klasse {klass}, Fach {sname}, Feld_{field}:" " ungültiger Wert ({val})"
)
_TAGGED_NO_LESSON = (
    "Klasse {klass}, Fach {sname}: keine Kennung bei"
    " „Extra-Einträge“ erwartet (gegeben: {tag})"
)
_ROOM_NO_LESSON = (
    "Klasse {klass}, Fach {sname}: Raumangabe aber" " keine Unterrichtsstunden"
)
_TAGGED_COMPONENT = (
    "Klasse {klass}, Fach {sname} – Komponente von Block"
    " {block}: keine Stundenkennung ({tag}) ist zulässig"
)
_TAG_LESSONS_MISMATCH = (
    "Stundenkennung „{tag}“ hat unterschiedliche"
    " Stundenzahlen in den Stunden mit\n"
    "     Fach {sid0}, Klasse {klass0} als in\n"
    "     Fach {sid1}, Klasse {klass1}"
)
_TAG_GROUP_DOUBLE = (
    "Stundenkennung „{tag}“ hat Überschneidungen bei den"
    " Gruppen in den Stunden mit\n"
    "     Fach {sid0}, Klasse {klass0} als in\n"
    "     Fach {sid1}, Klasse {klass1}"
)
_TAG_TEACHER_DOUBLE = (
    "Stundenkennung „{tag}“ hat Überschneidungen bei den"
    " Lehrern in den Stunden mit\n"
    "     Fach {sid0}, Klasse {klass0}\n"
    "     Fach {sid1}, Klasse {klass1}"
)
_FIELD_MISSING = "Klasse {klass}: Feld {field} fehlt in Fachtabelle"
_TEACHER_INVALID = (
    "Lehrerkürzel dürfen nur aus Zahlen und"
    " lateinischen Buchstaben bestehen: {tid} ist ungültig."
)
_TEACHER_NDAYS = (
    "{name} ({tid}), verfügbare Stunden: Daten für genau"
    " {ndays} Tage sind notwendig"
)
_TEACHER_DAYS_INVALID = "{name} ({tid}), verfügbare Stunden: ungültige Daten"
_BAD_TIDS = "Klasse {klass}: ungültige Lehrkräfte ({tids}) für {sname}"
_UNKNOWN_TEACHER = "Klasse {klass}: unbekannte Lehrkraft ({tid}) für {sname}"
_ROOM_INVALID = (
    "Raumkürzel dürfen nur aus Zahlen und"
    " lateinischen Buchstaben bestehen: {rid} ist ungültig."
)
_UNKNOWN_ROOM = "Klasse {klass}, Fach {sname}: unbekannter Raum ({rid})"
_BAD_ROOM = "Klasse {klass}, Fach {sname}: ungültige Raumangabe ({rid})"
_DOUBLED_ROOM = "Klasse {klass}, Fach {sname}: Raum ({rid}) zweimal angegeben"
_ADD_ROOM_DOUBLE = (
    "Klasse {klass}, Fach {sname}: Raum ({rid}) wurde dem"
    " Block {block} schon zugefügt"
)
_DOUBLED_RID = (
    "Tabelle der Räume: Kürzel „{rid}“ kommt doppelt vor"
)
_BAD_XROOMS = "Ungültige Info-Angabe <EXTRA> („Zusatzräume“) in Raumliste: {val}"
_LESSON_CLASS_MISMATCH = (
    "In der Tabelle der Unterrichtsstunden für"
    " Klasse {klass} ist die Klasse falsch angegeben:\n  {path}"
)
_UNKNOWN_TAG = "Tabelle der festen Stunden: unbekannte Stundenkennung „{tag}“"
_INVALID_DAY_PERIOD = (
    "Tabelle der festen Stunden: ungültige"
    " Tag.Stunde-Angabe für Kennung {tag}: {d_p}"
)
_REPEATED_DAY_PERIOD = (
    "Tabelle der festen Stunden: wiederholte"
    " Tag.Stunde-Angabe für Kennung {tag}: {d_p}"
)
_PREPLACE_TOO_MANY = (
    "Warnung: zu viele feste Stunden definiert für" " Stundenkennung {tag}"
)
_PREPLACE_TOO_FEW = (
    "Zu wenig feste Stunden definiert für" " Stundenkennung {tag}"
)
_TABLE_ERROR = "In Klasse {klass}: {e}"
_MULTIPLE_BLOCK = "Klasse {klass}: Block {sname} mehrfach definiert"
_BLOCK_SID_NOT_BLOCK = (
    "Klasse {klass}, Fach {sname}:" "Block-Fach (Epoche = {sid}) ist kein Block"
)
_COMPONENT_BAD_LENGTH_SID = (
    "Klasse {klass}, Fach {sname}:"
    " Block-Komponente in {sid}, Länge muss EINE Zahl oder '*' sein"
)
_NONLESSON_BAD_LENGTH = (
    "Klasse {klass}, EXTRA-Fach {sname}: ungültige" " Länge ({length})"
)
_PARALLEL_TO_NONLESSON = (
    "Kennung „{tag}“ ist ein EXTRA-Eintrag (Klasse"
    " {klass}).\n Es gibt parallele Einträge in Klasse(n) {pclasses}"
)
_PLUSTAG_INVALID = (
    "Klasse {klass}, Fach {sname}: Kennung mit '+' ({tag})" " ungültig"
)
_INVALID_DEFAULT_GAPS = (
    "Lehrer-Tabelle: ungültige Standard-Lücken-Angabe" " ({val})"
)
_INVALID_DEFAULT_UNBROKEN = (
    "Lehrer-Tabelle: ungültige" " Standard-Blocklänge-Angabe ({val})"
)
_INVALID_GAPS = "Lehrer-Tabelle: ungültige Lücken-Angabe für {teacher} ({val})"
_INVALID_UNBROKEN = (
    "Lehrer-Tabelle: ungültige Blocklänge-Angabe für" " {teacher} ({val})"
)
_INVALID_DEFAULT_MINLESSONS = (
    "Lehrer-Tabelle: ungültige Standard-Angabe"
    " für min. Stunden pro Tag ({val})"
)
_INVALID_MINLESSONS = (
    "Lehrer-Tabelle, {teacher}: ungültige Angabe"
    " für min. Stunden pro Tag ({val})"
)
_INVALID_DEFAULT_LUNCH = (
    "Lehrer-Tabelle: ungültige Standard-Angabe"
    " für die Mittagsstunden ({val})"
)
_INVALID_LUNCH = (
    "Lehrer-Tabelle, {teacher}: ungültige Angabe"
    " für die Mittagsstunden ({val})"
)
_UNBROKEN_WITH_LUNCH = (
    "Lehrer-Tabelle: für {tname} ist sowohl Blocklänge"
    " wie auch Mittag angegeben"
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

    # TODO: Temporary redirection to use real data (there isn't any test data yet!)
    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    #    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "NEXT"))

# IMPORTANT: Note that some uses of Python dicts here may assume ordered
# entries. If the implementation is altered, this should be taken into
# account. One place is the definition of pre-placed lessons
# for a subject. If there is more than one entry for this subject and
# varying durations, the placement could be affected.
#TODO: Can I avoid that with the rewrite?

### +++++

from tables.spreadsheet import read_DataTable, filter_DataTable, TableError
from core.base import class_group_split
from core.courses import Subjects
from core.teachers2 import Teachers

#???
TT_CONFIG = MINION(DATAPATH("CONFIG/TIMETABLE"))


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


class TT_Rooms(Dict[str,str]):
    """The internal representation of a room is the short name (a number/index
    would make no sense here).
    The class instance maps the short name to the full name.
    <self.rooms_for_class> maps the classes to the list of rooms
    available for each one.
    <self.xrooms> is a list of "extra" (non-existent) rooms provided only
    to alleviate the blockage of timetables when there are too few rooms
    available. It doesn't actually solve the problem, but can help the
    automatic generation process. The failed room allocations must be
    fixed manually.
    """
    def __init__(self):
        super().__init__()
        # {class: [available rooms]}
        self.rooms_for_class : Dict[str,List[str]] = {}
        # [extra rooms] ... a bodge to get around missing rooms
        self.xrooms : List[str] = []
        roomdata = read_DataTable(DATAPATH("TIMETABLE/ROOMS"))
        try:
            x = roomdata["__INFO__"]["EXTRA"]
        except KeyError:
            pass
        else:
            if x:
                try:
                    xname, n = x.rsplit("*", 1)
                    i = int(n)
                    xroom = xname.strip()
                except ValueError:
                    raise(TT_Error(_BAD_XROOMS.format(val=x)))
                for ix in range(1, i+1):
                    rid = f"rX{ix}"
                    self[rid] = xroom.format(i=ix)
                    self.xrooms.append(rid)
                    i -= 1
        for room in roomdata["__ROWS__"]:
            rid = room["short"]
            if rid in self:
                raise TT_Error(_DOUBLED_RID.format(rid=rid))
            if not rid.isalnum():
                raise TT_Error(_ROOM_INVALID.format(rid=rid))
            self[rid] = room["full"]
            users = room["users"].split()
            if users:
                # The classes which can use this room
                for k in users:
                    try:
                        self.rooms_for_class[k].append(rid)
                    except KeyError:
                        self.rooms_for_class[k] = [rid]


class TT_Subjects(Dict[str,str]):
    """The internal representation of a subject is the short name (a
    number/index would make no sense here).
    The class instance maps the short name to the full name.
    For timetabling no other functions are required.
    "Special" subjects introduced for grade reporting begin with a
    non-alphabetical character ("$") and are skipped here.
    Also other subjects will not be relevant for timetabling, but they
    can just be ignored.
    """
    def __init__(self):
        super().__init__()
        for sid, name in Subjects().sid2name.items():
            if sid[0].isalpha():
                self[sid] = name


class TT_Teachers(dict):
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
        default_minlessons = None
        _dm = teachers.info["MINPERDAY"]  # min.lessons per day
        if _dm:
            default_minlessons = get_minlessons(
                _dm, _INVALID_DEFAULT_MINLESSONS
            )
        default_lunch = None
        _dl = teachers.info["LUNCHBREAK"]  # possible lunch periods
        if _dl:
            default_lunch = get_lunch_periods(_dl, _INVALID_DEFAULT_LUNCH)
        default_gaps = None
        default_unbroken = None
        _dg = teachers.info["MAXGAPSPERWEEK"]  # gaps per week
        if _dg:
            default_gaps = get_gaps(_dg, _INVALID_DEFAULT_GAPS)
        _du = teachers.info["MAXBLOCK"]  # max. contiguous lessons
        if _du:
            default_unbroken = get_lessons_weight(
                _du, _INVALID_DEFAULT_UNBROKEN
            )
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
                                val = False  # not blocked
                            elif b == self.NO:
                                val = True  # blocked
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
            _g = tdata["MAXGAPSPERWEEK"]
            if _g:
                if _g == "*":
                    g = default_gaps
                else:
                    g = get_gaps(_g, _INVALID_GAPS, tname)
            else:
                g = None
            _u = tdata["MAXBLOCK"]
            if _u:
                if _u == "*":
                    u = default_unbroken
                else:
                    u = get_lessons_weight(_u, _INVALID_UNBROKEN, tname)
            else:
                u = None
            _m = tdata["MINPERDAY"]
            if _m:
                if _m == "*":
                    m = default_minlessons
                else:
                    m = get_minlessons(_m, _INVALID_MINLESSONS, tname)
            else:
                m = None
            _l = tdata["LUNCHBREAK"]
            if _l:
                if _l == "*":
                    l = default_lunch
                else:
                    l = get_lunch_periods(_l, _INVALID_LUNCH, tname)
            else:
                l = None
            if l and u:
                REPORT("WARNING", _UNBROKEN_WITH_LUNCH.format(tname=tname))
            self.constraints[tid] = {
                "MAXGAPSPERWEEK": g,
                "MAXBLOCK": u,
                "MINPERDAY": m,
                "LUNCHBREAK": l,
            }
        # Sort tags alphabetically (to make finding them easier)
        for t in sorted(_teachers):
            self[t] = _teachers[t]


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
        default_minlessons = None
        _dm = teachers.info["MINPERDAY"]  # min.lessons per day
        if _dm:
            default_minlessons = get_minlessons(
                _dm, _INVALID_DEFAULT_MINLESSONS
            )
        default_lunch = None
        _dl = teachers.info["LUNCHBREAK"]  # possible lunch periods
        if _dl:
            default_lunch = get_lunch_periods(_dl, _INVALID_DEFAULT_LUNCH)
        default_gaps = None
        default_unbroken = None
        _dg = teachers.info["MAXGAPSPERWEEK"]  # gaps per week
        if _dg:
            default_gaps = get_gaps(_dg, _INVALID_DEFAULT_GAPS)
        _du = teachers.info["MAXBLOCK"]  # max. contiguous lessons
        if _du:
            default_unbroken = get_lessons_weight(
                _du, _INVALID_DEFAULT_UNBROKEN
            )
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


class Classes:
    def __init__(self, periods):
        """Initialize with the valid lesson slots for each class. The
        data is read from the class-days-table.
        Build a mapping {class: {day: {period: possible}}}.
        <possible> is true or false.
        Also the number of days is defined here, though I haven't
        considered the implications of, say, fortnight-plans.
        """
        self.class_days_periods = {}
        self.periods = periods
        self.days = None
        ptags = TT_CONFIG["CLASS_PERIODS_HEADERS"] + [
            {"NAME": p} for p in periods
        ]
        class_table = read_DataTable(DATAPATH(TT_CONFIG["CLASS_PERIODS_DATA"]))
        class_table = filter_DataTable(
            class_table,
            {"INFO_FIELDS": [], "TABLE_FIELDS": ptags},
            extend=False,
        )["__ROWS__"]
        for row in class_table:
            klass = row.pop("CLASS")
            if not klass.isalnum():
                raise TT_Error(_CLASS_INVALID.format(klass=klass))
            day = row.pop("DAY")
            if self.days:
                if self.days[-1] != day:
                    self.days.append(day)
            else:
                self.days = [day]
            try:
                kmap = self.class_days_periods[klass]
            except KeyError:
                self.class_days_periods[klass] = {day: row}
            else:
                if day in kmap:
                    raise TT_Error(
                        _CLASS_TABLE_DAY_DOUBLE.format(klass=klass, day=day)
                    )
                kmap[day] = row

        ### Now initialize the lesson-reading structures
        self.class_name = {}
        self.atomics_lists = {}
        self.element_groups = {}
        #        self.extended_groups = {}
        # ?
        self.class_divisions = {}
        self.class_groups = {}
        self.groupsets_class = {}
        self.timetable_teachers = {}  # {tid -> [lesson-tag, ... ]}
        self.__pending_teachers = []  # teacher-tags todo-list
        self.class_tags = {}  # [class -> [lesson-tag, ... ]}
        self.classrooms = {}
        self.lessons = {}
        self.parallel_tags = {}  # {tag: [indexed parallel lesson-tags]}

    # ++++++++++++++++ Now the stuff dealing with the class-group-lesson data

    def all_lessons(self, SUBJECTS, ROOMS, TEACHERS):
        """Read the lesson data (etc.) for all classes defined in the
        class-day-periods table.
        Return a list of successfully read classes.
        """
        self.SUBJECTS = SUBJECTS
        self.ROOMS = ROOMS
        self.TEACHERS = TEACHERS
        classes = []
        self.__global_blocks = {}
        # Start with classless data
        # TODO: Cater for multiple classless tables?
        _xx = "XX"
        if self.read_class_data(_xx):
            classes.append(_xx)
        for klass in self.class_days_periods:
            if self.read_class_data(klass):
                classes.append(klass)
        ### Post-processing of lesson data (tags, etc.)
        for tag, subtags in self.parallel_tags.items():
            if len(subtags) < 2:
                continue
            # Check the compatibility of the fields
            g, t, nl = None, None, None
            for _tag in subtags:
                l = self.lessons[_tag]
                if l["block"] == "--":
                    raise TT_Error(
                        _PARALLEL_TO_NONLESSON.format(
                            tag=tag,
                            klass=l["CLASS"],
                            pclasses=", ".join(
                                [self.lessons[t]["CLASS"] for t in subtags]
                            ),
                        )
                    )
                # The actual lessons must match in number and length
                if nl:
                    if l["lengths"] != nl:
                        raise TT_Error(
                            _TAG_LESSONS_MISMATCH.format(
                                tag=tag,
                                sid0=s,
                                klass0=k,
                                sid1=l["SID"],
                                klass1=l["CLASS"],
                            )
                        )
                else:
                    nl = l["lengths"]
                    g = l["GROUPS"]
                    t = l["TIDS"]
                    k = l["CLASS"]
                    s = l["SID"]
                    continue
                # The teachers must be fully distinct
                if t.intersection(l["TIDS"]):
                    raise TT_Error(
                        _TAG_TEACHER_DOUBLE.format(
                            tag=tag,
                            sid0=s,
                            klass0=k,
                            sid1=l["SID"],
                            klass1=l["CLASS"],
                        )
                    )
                # The groups must be fully distinct
                if g.intersection(l["GROUPS"]):
                    raise TT_Error(
                        _TAG_GROUP_DOUBLE.format(
                            tag=tag,
                            sid0=s,
                            klass0=k,
                            sid1=l["SID"],
                            klass1=l["CLASS"],
                        )
                    )
                # The rooms are probably too complicated to compare ...
        for tag in self.__pending_teachers:
            data = self.lessons[tag]
            for tid in data["REALTIDS"]:
                try:
                    self.timetable_teachers[tid].append(tag)
                except KeyError:
                    self.timetable_teachers[tid] = [tag]
        return classes

    def read_class_data(self, klass):
        """Read the information pertaining to the teaching groups within
        the given class and the associated lessons from the lessons file
        for the class.
        """
        subjects = Subjects()
        info = subjects.class_info(klass)
        self.class_name[klass] = info.get("NAME") or klass

        ### Add the groups.
        self.read_groups(klass, info["GROUPS"])

        ### Classrooms?
        self.classrooms[klass] = info["CLASSROOMS"].split()

        ### Add the lessons.
        self.read_lessons(klass, subjects.class_subjects(klass))

        return True

    def read_groups(self, klass, raw_groups):
        """Parse the GROUPS data for the given class.
        This is a '|'-separated list of mutually exclusive class divisions.
        A division is a space-separated list of groups. These groups
        may contain '.' characters, in which case they are intersections
        of "atomic" groups (no dot). Neither these atomic groups nor the
        dotted intersections may appear in more than one division.
        A division might be "A.G B.G B.R".
        As the class divisions must be given as a set of non-intersecting
        groups, the atomic (undotted) groups may need to be expressed
        (for the timetable) as a combination of dotted groups, e.g. B as
        "B.G,B.R".
        """
        if klass.startswith("XX"):
            return
        ### Add declared class divisions (and their groups).
        divisions = [["*"]]
        divs = []
        atomic_groups = [frozenset()]
        all_atoms = set()
        for glist in raw_groups.split("|"):
            dgroups = glist.split()
            divisions.append(dgroups)
            division = [frozenset(item.split(".")) for item in dgroups]
            divs.append(division)
            ag2 = []
            for item in atomic_groups:
                for item2 in division:
                    all_atoms |= item2
                    ag2.append(item | item2)
            atomic_groups = ag2
        self.class_divisions[klass] = divisions
        # print("§§§ DIVISIONS:", klass, divisions)
        al = [".".join(sorted(ag)) for ag in atomic_groups]
        al.sort()
        self.atomics_lists[klass] = al  # All (dotted) atomic groups
        # print(f'$$$ "Atomic" groups in class {klass}:', al)
        ### Make a mapping of single, undotted groups to sets of dotted
        ### atomic groups.
        gmap = {
            a: frozenset(
                [".".join(sorted(ag)) for ag in atomic_groups if a in ag]
            )
            for a in all_atoms
        }
        # print(f'$$$ "Element" groups in class {klass}:', gmap)
        self.element_groups[klass] = gmap

        #        ### The same for the dotted groups from the divisions (if any)
        #        xmap = {}
        #        for division in divs:
        #            for item in division:
        #                if item not in gmap:
        #                    xmap['.'.join(sorted(item))] = frozenset.intersection(
        #                            *[gmap[i] for i in item])
        #        print(f'$$$ "Extended" groups in class {klass}:', xmap)
        #        self.extended_groups[klass] = xmap
        self.make_class_groups(klass)

    def make_class_groups(self, klass):
        """Build the entry for <self.class_groups> for the given class.
        Also build the reversed mapping <self.groupsets_class>.
        This method may need to be overriden in the back-end.
        """
        gmap = {}
        #        for _map in self.element_groups[klass], self.extended_groups[klass]:
        #            for k, v in _map.items():
        #                gmap[k] = frozenset([f'{klass}.{ag}' for ag in v])
        for k, v in self.element_groups[klass].items():
            gmap[k] = frozenset([f"{klass}.{ag}" for ag in v])
            # print(")))", gmap[k])
        self.class_groups[klass] = gmap
        # And now a reverse map, avoiding duplicate values (use the
        # first occurrence, which is likely to be simpler)
        reversemap = {}
        for k, v in gmap.items():
            if v not in reversemap:
                reversemap[v] = f"{klass}.{k}"
        self.groupsets_class[klass] = reversemap
        # Add "whole class" elements to both mappings
        _whole_class = klass
        fs_whole = frozenset([_whole_class])
        reversemap[fs_whole] = _whole_class
        all_groups = frozenset(
            [f"{klass}.{ag}" for ag in self.atomics_lists[klass]]
        )
        if all_groups:
            gmap["*"] = all_groups
            reversemap[all_groups] = _whole_class
        else:
            gmap["*"] = fs_whole

        # print("+++", klass, gmap)
        # print("---", klass, reversemap)

    def group_classgroups(self, klass, group):
        """Return the (frozen)set of "full" groups for the given class
        and group. The group may be dotted. Initially only the "elemental"
        groups, including the full class, are available, but dotted
        groups will be added if they are not already present.
        This method may need to be overridden in the back-end (see
        <make_class_groups>)
        """
        cg = self.class_groups[klass]
        try:
            return cg[group]
        except KeyError:
            pass
        gsplit = group.split(".")
        if len(gsplit) > 1:
            group = ".".join(sorted(gsplit))
            try:
                return cg[group]
            except KeyError:
                pass
            try:
                gset = frozenset.intersection(*[cg[g] for g in gsplit])
            except KeyError:
                pass
            else:
                if gset:
                    # Add to group mapping
                    cg[group] = gset
                    # and to reverse mapping
                    grev = self.groupsets_class[klass]
                    if gset not in grev:
                        # ... if there isn't already an entry
                        grev[gset] = f"{klass}.{group}"
                    return gset
        raise TT_Error(_UNKNOWN_GROUP.format(klass=klass, group=group))

    def read_lessons(self, klass, lesson_lines):
        def read_field(field):
            try:
                return row[field]
            except KeyError:
                raise TT_Error(
                    _FIELD_MISSING.format(
                        klass=klass, field=Subjects().SUBJECT_FIELDS[field]
                    )
                )

        lesson_id = 0
        class_blocks = {}  # collect {block-sid: block-lesson-tag}
        class_tags = []  # collect all lesson-tags for this class
        self.class_tags[klass] = class_tags
        for row in lesson_lines:
            ### Subject
            sid = read_field("SID")
            if not sid[0].isalpha():
                continue
            sidx = sid.rsplit("+", 1)
            sname = self.SUBJECTS[sidx[0]]
            ### Make a list of durations.
            # Then for each entry, generate a lesson or a course within
            # a teaching block.
            _durations = read_field("LENGTHS")
            if not _durations:
                # Line not relevant for timetabling
                continue
            try:
                durations = []
                dmap = {}
                if _durations != "*":
                    for d in _durations.split():
                        i = int(d)
                        if i > 0 and i <= _MAX_DURATION:
                            durations.append(i)
                        else:
                            raise ValueError
                        try:
                            dmap[i] += 1
                        except KeyError:
                            dmap[i] = 1
            except ValueError:
                raise TT_Error(
                    _INVALID_ENTRY.format(
                        klass=klass,
                        field=Subjects().SUBJECT_FIELDS["LENGTHS"],
                        sname=sname,
                        val=_durations,
                    )
                )
            # Sort the keys
            dmap = {d: dmap[d] for d in sorted(dmap)}

            ### Teachers
            _tids = read_field("TIDS")
            if not _tids:
                # Line not relevant for timetabling
                continue
            tids = _tids.split()
            real_teachers = set()
            teachers = real_teachers  # yes, the same set!
            if tids[0] == "*":
                # No teachers
                if len(tids) > 1:
                    raise TT_Error(
                        _BAD_TIDS.format(klass=klass, sname=sname, tids=_tids)
                    )
            else:
                for tid in tids:
                    if tid == "--":
                        teachers = set()
                    elif tid in self.TEACHERS:
                        real_teachers.add(tid)
                    else:
                        raise TT_Error(
                            _UNKNOWN_TEACHER.format(
                                klass=klass, sname=sname, tid=tid
                            )
                        )

            ### Rooms
            _ritems = read_field("ROOMS").split()
            # There is one item per room needed. The items can be a room,
            # a list of possible rooms ("r1/r2/ ...") or "?" (unspecified
            # room for the current class). It is also possible to use (just)
            # one '+' instead of a '/'. In that case the rooms before
            # the '+' get preference, if the algorithm permits this.
            # The order of the rooms is preserved, in case the algorithm
            # allows giving preference to rooms which are earlier in the
            # list (regardless of a '+').
            # The result is a list of "sanitized" room choices, one item
            # per necessary room. The validity of the rooms is checked
            # and '$' and '?' are substituted.
            rooms, roomlists = [], []
            if _ritems:
                for _ritem in _ritems:
                    try:
                        _n, ritem = _ritem.split("*", 1)
                    except ValueError:
                        ritem = _ritem
                        n = 1
                    else:
                        try:
                            n = int(_n)
                            if not ritem:
                                raise ValueError
                        except ValueError:
                            raise TT_Error(
                                _BAD_ROOM.format(
                                    klass=klass, sname=sname, rid=_ritem
                                )
                            )
                    try:
                        _i1, _i2 = ritem.split("+", 1)
                        if (not _i1) or (not _i2):
                            raise TT_Error(
                                _BAD_ROOM.format(
                                    klass=klass, sname=sname, rid=_ritem
                                )
                            )
                        i1, i2 = _i1.split("/"), _i2.split("/")
                    except ValueError:
                        # No "preferred" rooms
                        i1, i2 = [], ritem.split("/")
                    _choices = set()
                    _roomlist = []
                    for i in i1, i2:
                        _rlist = []
                        # check room, add to list if new
                        for rid in i:
                            if rid in _choices:
                                raise TT_Error(
                                    _DOUBLED_ROOM.format(
                                        klass=klass, sname=sname, rid=rid
                                    )
                                )
                            _choices.add(rid)
                            if rid == "$":
                                for r in self.classrooms[klass]:
                                    if r not in _choices:
                                        _choices.add(r)
                                        _rlist.append(r)
                            elif rid == "?":
                                for r in self.ROOMS.rooms_for_class[klass]:
                                    if r not in _choices:
                                        _choices.add(r)
                                        _rlist.append(r)
                            elif rid in self.ROOMS:
                                _rlist.append(rid)
                            else:
                                raise TT_Error(
                                    _UNKNOWN_ROOM.format(
                                        klass=klass, sname=sname, rid=rid
                                    )
                                )
                        if _rlist:
                            _roomlist.append(_rlist)
                    if len(_roomlist) == 1:
                        if self.ROOMS.xrooms and "?" in _choices:
                            # Add fake rooms
                            _roomlist.append(self.ROOMS.xrooms)
                    else:
                        if self.ROOMS.xrooms and "?" in _choices:
                            # Add fake rooms
                            _roomlist[1] += self.ROOMS.xrooms
                    _ritem = "+".join(["/".join(_r) for _r in _roomlist])
                    if _ritem in rooms:
                        raise TT_Error(
                            _DOUBLED_ROOM.format(
                                klass=klass, sname=sname, rid=_ritem
                            )
                        )
                    for i in range(n):
                        rooms.append(_ritem)
                        roomlists.append(_roomlist)
                # _rstr = repr(rooms)
                # if '+' in _rstr:
                #    print("§§§", klass, sid, _rstr)

            ### Group
            group = read_field("GROUP")
            _groups = self.group_classgroups(klass, group) if group else set()

            ### Lesson-id generation

            # The TAG value is a label for a set of lessons which should
            # be parallel, if possible. It should be an ASCII alphanumeric
            # string. This label can also be used to enforce particular
            # (fixed) times for the lesson(s). If there is no specified
            # placement, the program will treat the wish for simultaneity
            # as a soft constraint, whose weight can be set.
            # TODO: Where is the weight set?
            #
            # Also "blocks" (see below) may use the TAG field, but their
            # component lessons (which don't appear in the timeatable –
            # they are represented by the block) may not.
            #
            # To enable multi-class blocks, there can be a special class
            # data file for class 'XX', which is not a real class. This
            # file can be used to enter blocks which are for multiple
            # classes, but also "lessons" which have no class or in some
            # other way no presence in the timetable of a class.
            #
            # Such multi-class blocks must have a special way of referring
            # to them, so their subject ids have a suffix:  '+tag'.
            # This suffix serves only to label the block entry, has no
            # inherent relationship to a tag in the TAG field (so a tag
            # can appear in both) and is removed in the SID  field of the
            # generated data. This subject tag can not be used for
            # placements – though the same tag could be used here.
            # TODO: Note that '+tag' can also be used in normal class files to
            # disambiguate blocks – in case the subject id is used more than once?
            # Or perhaps this is superfluous, as there may be only one block among
            # several sid usages?
            block = read_field("BLOCK")
            tag = row["TAG"]
            # Check tag
            if tag and not (tag.isascii() and tag.isalnum()):
                raise TT_Error(
                    _INVALID_ENTRY.format(
                        klass=klass,
                        field=Subjects().SUBJECT_FIELDS["TAG"],
                        sname=sname,
                        val=tag,
                    )
                )

            # BLOCK = empty     Normal lesson, may be tagged. Lessons with the same
            #                   tag will be placed in the same slot, if possible. If
            #                   a slot is specified (in the "fixed-lessons" table)
            #                   this placement is compulsory for all items.
            #                   The teachers of all the items must be independent of
            #                   each other (no intersections).
            #                   The groups of all the items must be independent of
            #                   each other (no intersections).
            # TODO:
            #                   Also, compulsory rooms must be independent of
            #                   each other, but this will be practically impossible
            #                   to test at this stage ...
            #                   The number and lengths of all lessons with the same
            #                   tag must be identical.
            #
            # BLOCK = '++'      "Block" definition. In many respects this is like a
            #                   normal lesson, but it can have "components" (lessons
            #                   which don't appear in the timetable because they are
            #                   part of a block). All components must be defined
            #                   (that is, read in) after the block entry – to allow
            #                   checking.
            #
            #                   The subject-id must be unique within this table.
            #                   However, by adding a suffix ('+' + ASCII-alphanumeric),
            #                   this limitation can be overcome. The suffix is also
            #                   accessible to components in other classes, instead
            #                   of the subject id in their BLOCK field.
            # ?
            #                   The suffix will be stripped except in the class-local
            #                   <blocks> mapping.
            #
            # BLOCK = '--'      "Non-lesson", not placed in timetable (for "EXTRA"
            #                   entries). This is handled like a timetabled block
            #                   (see above), except that the LENGTHS field specifies
            #                   the "total lessons" (~ payment units) – a single
            #                   number. Trying to specify a placement for such an
            #                   entry makes no sense, so the TAG field should be empty.
            #
            # BLOCK = '+tag'    A "component". The tag must be the subject suffix
            #                   of a block or a non-lesson.
            #
            # BLOCK = sid       A block "component". <sid> is the subject-id
            #                   (potentially with '+tag' suffix). With '+tag' the
            #                   block entry may be in another file – presumably the
            #                   non-class file. The block entry must be previously
            #                   defined and globally unique (only the non-class file
            #                   is guaranteed to be read in before another table.
            #                   Without such a suffix the block entry must be unique
            #                   and previously defined within the same table.
            #
            #                   This entry does not appear in the timetable.
            #
            #                   The teachers will be added to the block entry (they
            #                   may be repeated).
            #
            #                   The groups will be added to the block entry, they
            #                   need not be independent.
            #
            #                   The rooms will be added to the block entry. New rooms
            #                   will cause the number of needed rooms to increase
            #                   accordingly, but repeated rooms will cause no increase.
            #
            #                   The LENGTHS field can be '*', which means the value
            #                   will be taken from the block entry. As far as payment
            #                   units are concerned this is counted only once per tag
            #                   as the use of the tag indicates a single item.
            #                   For a block this means effectively that the lesson
            #                   is taught throughout the year, but parallel to other
            #                   components.
            #
            #                   The LENGTHS field can also be a number. This indicates
            #                   a time-limited subject-block within the block
            #                   ("Epoche"). Each entry counts separately as far as
            #                   payment units are concerned.

            block_field = None
            lesson_id += 1
            lesson_tag = f"{klass}_{lesson_id:02}"
            if block:
                if block == "++":
                    # A "block" entry.
                    block_field = "++"
                elif block == "--":
                    # An EXTRA (non-lesson) entry
                    if len(durations) != 1:
                        TT_Error(
                            _NONLESSON_BAD_LENGTH.format(
                                klass=klass, sname=sname, length=_durations
                            )
                        )
                    if tag:
                        raise TT_Error(
                            _TAGGED_NO_LESSON.format(
                                klass=klass, sname=sname, tag=tag
                            )
                        )
                    if rooms:
                        raise TT_Error(
                            _ROOM_NO_LESSON.format(klass=klass, sname=sname)
                        )
                    block_field = "--"
                else:
                    # A block component, <block> = block-sid
                    try:
                        # First check within this table
                        block_field = class_blocks[block]
                    except KeyError:
                        try:
                            block_field = self.__global_blocks[block]
                        except KeyError:
                            raise TT_Error(
                                _BLOCK_SID_NOT_BLOCK.format(
                                    klass=klass, sname=sname, sid=block
                                )
                            )
                    # Don't allow a tag in a block-component
                    if tag:
                        raise TT_Error(
                            _TAGGED_COMPONENT.format(
                                klass=klass, sname=sname, tag=tag, block=block
                            )
                        )
                    if durations:
                        if len(durations) > 1:
                            raise TT_Error(
                                _COMPONENT_BAD_LENGTH_SID.format(
                                    klass=klass, sname=sname, sid=block
                                )
                            )
                    block_lesson = self.lessons[block_field]
                    # ? Rather use <real_teachers>?
                    block_lesson["REALTIDS"].update(teachers)
                    block_lesson["GROUPS"].update(_groups)
                    if rooms:
                        if block_lesson["block"] == "--":
                            raise TT_Error(
                                _ROOM_NO_LESSON.format(klass=klass, sname=sname)
                            )
                        # Add rooms to lesson, but only if they are really new
                        block_rooms = block_lesson["ROOMS"]
                        block_roomlists = block_lesson["ROOMLISTS"]
                        i = 0
                        for rid in rooms:
                            if rid in block_rooms:
                                REPORT(
                                    "WARNING",
                                    _ADD_ROOM_DOUBLE.format(
                                        klass=klass,
                                        sname=sname,
                                        block=block_lesson["SID"],
                                        rid=rid,
                                    ),
                                )
                            else:
                                block_rooms.append(rid)
                                block_roomlists.append(roomlists[i])
                            i += 1
                    block = None
            # else:
            # A "normal" lesson
            if block:
                # This must be the only definition of a block for
                # this subject-id in this table.
                if sid in class_blocks:
                    raise TT_Error(
                        _MULTIPLE_BLOCK.format(klass=klass, sname=sname)
                    )
                class_blocks[sid] = lesson_tag
                if len(sidx) > 1:
                    # This must be the only definition of a block for
                    # this subject-id in any table.
                    if sid in self.__global_blocks:
                        raise TT_Error(
                            _MULTIPLE_BLOCK.format(klass=klass, sname=sname)
                        )
                    self.__global_blocks[sid] = lesson_tag
                self.__pending_teachers.append(lesson_tag)
            else:
                for tid in real_teachers:
                    try:
                        self.timetable_teachers[tid].append(lesson_tag)
                    except KeyError:
                        self.timetable_teachers[tid] = [lesson_tag]
            if tag:
                try:
                    self.parallel_tags[tag].append(lesson_tag)
                except KeyError:
                    self.parallel_tags[tag] = [lesson_tag]
            class_tags.append(lesson_tag)
            self.lessons[lesson_tag] = {
                "CLASS": klass,
                "GROUPS": set(_groups),
                "SID": sidx[0],
                "TIDS": teachers,  # for timetable-clash checking,
                # tid '--' makes it empty even if there are teachers
                "REALTIDS": real_teachers,  # all associated teachers
                "ROOMS": rooms,
                "ROOMLISTS": roomlists,
                "lengths": dmap,
                "block": block_field,
            }

    #            if klass == 'XX':
    #                print("???", tag, self.lessons[tag])

    def combine_atomic_groups(self, groups):
        """Given a set of atomic groups, possibly from more than one
        class,try to reduce it to elemental groups (as used in the data
        input).
        Return the possibly "simplified" groups as a set.
        """
        kgroups = {}
        for g in groups:
            k, group = class_group_split(g)
            try:
                kgroups[k].append(g)
            except KeyError:
                kgroups[k] = [g]
        _groups = set()
        for k, glist in kgroups.items():
            try:
                gmap = self.groupsets_class[k]
                _groups.add(gmap[frozenset(glist)])
            except:
                _groups.update(glist)
        return _groups

    def teacher_check_list(self):
        """Return a "check-list" of the lessons for each teacher."""
        lines = []
        for tid in self.TEACHERS:
            tags = self.timetable_teachers.get(tid)
            if tags:
                class_lessons = {}
                for tag in tags:
                    data = self.lessons[tag]
                    klass = data["CLASS"]
                    try:
                        class_list, class_blocks = class_lessons[klass]
                    except KeyError:
                        class_list = []
                        class_blocks = []
                        class_lessons[klass] = [class_list, class_blocks]
                    rooms = data["ROOMS"]
                    n = len(rooms)
                    _rooms = f" [{n}: {', '.join(sorted(rooms))}]" if n else ""
                    sname = self.SUBJECTS[data["SID"]]
                    # Combine subgroups
                    groups = sorted(self.combine_atomic_groups(data["GROUPS"]))
                    dmap = data["lengths"]
                    block = data["block"]
                    if block == "--":
                        d = list(dmap)[0] if dmap else 0
                        entry = (
                            f"    // {sname} [{','.join(groups)}]:"
                            f" EXTRA x {d}"
                        )
                        class_blocks.append(entry)
                    elif block == "++":
                        ll = ", ".join(lesson_lengths(dmap))
                        entry = (
                            f"    // {sname} [{','.join(groups)}]:"
                            f" BLOCK: {ll}{_rooms}"
                        )
                        class_blocks.append(entry)
                    elif block:
                        # Component
                        blesson = self.lessons[block]
                        bname = self.SUBJECTS[blesson["SID"]]
                        if dmap:
                            entry = (
                                f"    {sname} [{','.join(groups)}]:"
                                f" EPOCHE ({bname}) x {list(dmap)[0]}"
                            )
                        else:
                            entry = (
                                f"    {sname} [{','.join(groups)}]:"
                                f" ({bname})"
                            )
                        class_list.append(entry)
                    else:
                        ll = ", ".join(lesson_lengths(dmap))
                        entry = (
                            f"    {sname} [{','.join(groups)}]:"
                            f" {ll}{_rooms}"
                        )
                        class_list.append(entry)
                if class_lessons:
                    lines.append("")
                    lines.append("")
                    lines.append(f"$$$ {tid} ({self.TEACHERS[tid]})")
                    # Present the "dummy" classes first
                    first, second = [], []
                    for klass in class_lessons:
                        if klass.startswith("XX"):
                            first.append(klass)
                        else:
                            second.append(klass)
                    for klass in first + second:
                        class_list, class_blocks = class_lessons[klass]
                        clines = []
                        clines += class_blocks
                        if class_blocks:
                            clines.append("")
                        clines += class_list
                        if clines:
                            lines.append("")
                            lines.append(f"  Klasse {klass}:")
                            lines += clines
        return "\n".join(lines)


# *** Group handling ***#
# Anything more complicated than "two-level" grouping ('A.G', etc.) is
# likely to prove too confusing. It is probably best to leave any further
# consideration of such exotic combinations until a case actually
# arises.
# However, it can be supported in principal by adopting a general approach
# to dotted (intersecting) groups. A minimal set of non-intersecting
# groups (in dotted notation) is defined for the timetabling program.
# Take (A.G, B.G, B.R) as an example. The normal teaching groups (which
# would appear in the source subject table) are A, B, G, R. The subgroup
# B.R. might also be used (A.G and B.R probably not, because they are
# the same as A and R).
# A mapping from the undotted groups to a set of their component dotted
# group is constructed:
#   A: {A.G}
#   B: {B.G, B.R}
#   G: {A.G, B.G}
#   R: {B.R}
# This can in turn be used to build the set of basic groups for any
# dotted combination (the intersection of the sets for each of the
# components), e.g: B.G -> B  G = {B.G}.
# Of course, here we could just have added the basic dotted groups to
# the group mapping. But the intersection approach would also be valid
# for dotted combinations which are not in the basic groups (possible
# if there are basic groups like A.P.X, with two dots).


class Placements:
    def __init__(self, classes_data):
        self.classes_data = classes_data
        lessons = classes_data.lessons
        parallel_tags = classes_data.parallel_tags
        try:
            place_data = read_DataTable(DATAPATH(TT_CONFIG["PLACEMENT_DATA"]))
        except TableError as e:
            REPORT("ERROR", str(e))
            return
        place_data = filter_DataTable(
            place_data, MINION(DATAPATH("CONFIG/TT_PLACEMENTS"))
        )
        self.predef = []
        for row in place_data["__ROWS__"]:
            tag = row["TAG"]
            places_list = []
            for d_p in row["PLACE"].split(","):
                try:
                    d, p = d_p.strip().split(".")
                except:
                    raise TT_Error(_INVALID_DAY_PERIOD.format(tag=tag, d_p=d_p))
                # TODO: Check the validity of the places
                dp = (d, p)
                if dp in places_list:
                    raise TT_Error(
                        _REPEATED_DAY_PERIOD.format(tag=tag, d_p=d_p)
                    )
                places_list.append(dp)
            try:
                taglist = parallel_tags[tag]
            except KeyError:
                raise TT_Error(_UNKNOWN_TAG.format(tag=tag))
            dmap = lessons[taglist[0]]["lengths"]
            n = 0
            for d, i in dmap.items():
                n += i
            if n != len(places_list):
                if n > len(places_list):
                    REPORT("WARNING", _PREPLACE_TOO_FEW.format(tag=tag))
                else:
                    raise TT_Error(_PREPLACE_TOO_MANY.format(tag=tag))
            self.predef.append((tag, places_list))


# TODO: Support cases with multiple lengths by doing in order of
# increasing length


def lesson_lengths(duration_map):
    ll = []
    for d in sorted(duration_map):
        n = duration_map[d]
        length = "Einzel" if d == 1 else "Doppel" if d == 2 else f"[{d}]"
        ll.append(f" {length} x {n}")
    return ll


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

def teachers_convert(days, periods, filetype='tsv'):
    teachers = TT_TeachersX(
        {d.short: d for d in days},
        {p.short: p for p in periods}
    )
    fields = MINION(DATAPATH("CONFIG/TEACHER_FIELDS"))
    tf = fields["TABLE_FIELDS_STUB"]
    for p in periods:
        tf.append({
            "NAME": p.short
        })
    fields["TABLE_FIELDS"] = tf
    fnames = [f["NAME"] for f in tf]
    #print("fnames:", fnames)

    from tables.spreadsheet import make_DataTable
    folder = DATAPATH("testing/tmp/TEACHERS")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    for k, v in teachers.items():
#        print(f"  {k} ({teachers.alphatag[k]}): {v}")
#        print("   ", teachers.blocked_periods.get(k) or "–––")
#        print("   ", teachers.constraints[k])

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

    print("\nROOMS:")
    rooms = TT_Rooms()
    for r in sorted(rooms):
        print(f"  {r:8}: {rooms[r]}")
    print("\nXROOMS:", rooms.xrooms)
    print("\nCLASS -> ROOMS:")
    for k in sorted(rooms.rooms_for_class):
        print(f"  {k:4}: {sorted(rooms.rooms_for_class[k])}")

    print("\nSUBJECTS:")
    subjects = TT_Subjects()
    for k in sorted(subjects):
        print(f"  {k:8}: {subjects[k]}")

    print("\nTEACHERS:")
#    teachers_convert(days, periods)


    for k, v in teachers.items():
        print(f"  {k} ({teachers.alphatag[k]}): {v}")
        print("   ", teachers.blocked_periods.get(k) or "–––")
        print("   ", teachers.constraints[k])

    quit(0)

    print("\nCLASSES:")
    classes = Classes(periods)
    for klass in sorted(classes.class_days_periods):
        print(f"  {klass}: {classes.class_days_periods[klass]}")

    print("\nREAD LESSONS:", classes.all_lessons(subjects, rooms, teachers))

    print("\nPLACEMENTS:")
    placements = Placements(classes)
#    for k, v in classes.lessons.items():
#        print("§§§", k, ":", v)
