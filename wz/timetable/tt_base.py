"""
timetable/tt_base.py - last updated 2022-02-22

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
_N_ROOM_COMBINATIONS = 20  # Warn if a block has more room combinations

_SINGLE = "Einzel"
_DOUBLE = "Doppel"
_EXTRA = "EXTRA"
_BLOCK = "BLOCK"
_BLOCK_COURSE = "EPOCHE"

### Messages

_UNKNOWN_GROUP = "Klasse {klass}: unbekannte Gruppe – '{group}'"
_INVALID_ENTRY = (
    "Klasse {klass}, Fach {sname}, Feld_{field}:" " ungültiger Wert ({val})"
)
_TAGGED_NO_LESSON = (
    "Klasse {klass}, Fach {sname}: „Extra-Einträge“ sollten keine „Kennung“"
    " haben (gegeben: {tag})"
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
_UNKNOWN_TEACHER = "Klasse {klass}: unbekannte Lehrkraft ({tid}) für {sname}"
_ROOM_INVALID = (
    "Raumkürzel dürfen nur aus Zahlen und"
    " lateinischen Buchstaben bestehen: {rid} ist ungültig."
)
_UNKNOWN_ROOM = "Klasse {klass}, Fach {sname}: unbekannter Raum ({rid})"
_DOUBLED_RID = "Tabelle der Räume: Kürzel „{rid}“ kommt doppelt vor"
_BAD_XROOMS = (
    "Ungültige Info-Angabe <EXTRA> („Zusatzräume“) in Raumliste: {val}"
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
_BAD_CONDITION_DEF = "Ungültige Bedingungsdefinition: {name}"
_NOT_IN_RANGE = "Wert ({val}) nicht im Bedingungsbereich für {name}"
_NOT_SUBSET = "Bedingung {name}: ungültiger Wert ({val})"
_FILTER_ERROR = "Klassendaten-Fehler: {msg}"
_DOUBLE_DAY = "Klassendaten-Fehler: Tag-Zeile {day} doppelt vorhanden"
_ELEMENT_IN_MULTIPLE_DIVISIONS = (
    "Klasse {klass}: Gruppe {e} erscheint in mehr als eine „Division“"
)
_BAD_CLASSROOM = "Klasse {klass}: unbekannter Klassenraum ({rid})"
_NO_CLASSROOM = (
    "Klasse {klass} hat keinen eigenen Raum. Dieser kann"
    " also nicht eingesetzt werden (als „$“)"
)
_CLASSROOM_REPEATED = "Klasse {klass}: Klassenraum doppelt in Raumliste"
_BAD_PLACEMENT_WEIGHTING = (
    "Ungültige Gewichtung in Tabelle der Platzierungskennungen:\n"
    "  Kennung {tag}: {w}"
)
_TAG_NO_ENTRY = "Unbekannte Platzierungskennung: „{tag}“"
_REPEATED_ROOM = "Klasse {klass}, Block „{block}“: Raum {rid} mehrfach benutzt"
_MINUS_NO_ROOM = (
    "Klasse {klass}, Fach {sname}: Im Raumfeld steht „-“, aber kein Raum"
)
_MINUS_NOT_BLOCK_COURSE = (
    "Klasse {klass}, Fach {sname}: Im Raumfeld steht „-“, der Eintrag ist"
    " aber kein Block-Kurs"
)
_BAD_SID_TAG = (
    "Klasse {klass}, Fachkürzel: {sid}: Fachkürzel mit „+“ sind nur in"
    " Block-Definitionen („++“ und „--“) erlaubt."
)
_BLOCK_NO_COURSES = "Klasse {klass}, Fachkürzel {sid}: Block ohne Kurse"
_BLOCK_NO_ROOM_COMBINATIONS = (
    "Klasse {klass}, Fachkürzel {sid}: Block hat keine möglichen"
    " Raumkombinationen"
)
_WARN_ROOM_COMBINATIONS = (
    "Klasse {klass}, Fachkürzel {sid}: Block mit sehr vielen ({n}) möglichen"
    " Raumkombinationen. Das könnte die Verarbeitung verlangsamen."
)
_BLOCK_COURSE_NO_ROOM = (
    "Klasse {klass}, Fachkürzel {sid} (Block {block}): Die Raumwahl"
    " wurde nicht reserviert"
)
_BLOCK_COURSES_ROOM_PROBLEM = (
    "Block {block} (Klasse {klass}): Nicht alle Kursräume („-“-Raumlisten)"
    " wurden reserviert"
)
_WARN_ROOMS_LOST = (
    "Klasse {klass}, Fachkürzel {sid} (Block {block}): Nicht alle"
    " Raumkombinations des Blocks decken den Raumbedarf für diesen Kurs ab."
    " Vielleicht sollte dieser Raumbedarf zu einem der Pflichträume werden?"
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

### +++++

from itertools import product
from typing import NamedTuple, Dict, List, Set, FrozenSet, Tuple, Sequence

from tables.spreadsheet import read_DataTable, filter_DataTable, TableError
from core.base import class_group_split
from core.courses import Subjects
from core.teachers import Teachers


class TT_Error(Exception):
    pass


### -----


class Day(NamedTuple):
    short: str  # Short name (e.g. "Do")
    full: str  # Full name (e.g. "Donnerstag")
    tag: str  # Day number as string, starting at "1"
    bitmap: int  # Each day has a bit, e.g. 8 (2^3) for the fourth day


class TT_Days(List[Day]):
    """Manage various representations of the days of the (timetable) week.
    The primary internal representation of a day is the index, starting
    at 0 for the first day of the school week.
    """

    def __init__(self):
        super().__init__()
        b = 1  # for bitmap
        i = 0  # for tag
        for k, l in MINION(DATAPATH("TIMETABLE/DAYS"))["DAYS"]:
            i += 1
            self.append(Day(k, l, str(i), b))
            b *= 2

    def short2index(self):
        """Return a mapping from "short" form to index."""
        dayx = {}
        i = 0
        for d in self:
            dayx[d.short] = i
            i += 1
        return dayx

    def bitstring(self, day: int) -> str:
        """Return the bitmap as a string of 1s and 0s, but reversed, so
        that the first day comes first in the string.
        """
        return f"{self[day].bitmap:0{len(self)}b}"[::-1]


class Period(NamedTuple):
    short: str  # Short name (e.g. "2")
    full: str  # Full name (e.g. "2. Fachstunde")
    tag: str  # Period number as string, starting at "1"
    starttime: str  # Time of period start
    endtime: str  # Time of period end


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

    def short2index(self):
        """Return a mapping from "short" form to index."""
        periodx = {}
        i = 0
        for p in self:
            periodx[p.short] = i
            i += 1
        return periodx


class TT_Rooms(Dict[str, str]):
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
        self.rooms_for_class: Dict[str, List[str]] = {}
        # [extra rooms] ... a bodge to get around missing rooms
        self.xrooms: List[str] = []
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
                    raise (TT_Error(_BAD_XROOMS.format(val=x)))
                for ix in range(1, i + 1):
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


class TT_Subjects(Dict[str, str]):
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


class TT_Teachers(Dict[str, str]):
    """The internal representation of a subject is the short name (a
    number/index would make no sense here).
    The class instance maps the short name to the full name.
    There are also timetable constraints which can be associated with
    teachers. These are available as a mapping via the attribute
    <constraints>.
    The attribute <alphatag> maps the short name to the sorting name.
    The attribute <available> maps the short name to a list of
    available periods (list of days, each day is a list of periods:
    <True> => available).
    """

    def __init__(self, days, periods):
        super().__init__()
        self.address = {}
        self.alphatag = {}  # shortened, ASCII version of name, sortable
        teachers = Teachers()
        conditions = Conditions(teachers.fields)
        self.available = {}
        self.lunch_periods = {}
        self.constraints = {}
        for tid in teachers.list_teachers():
            tdata = teachers[tid]
            tname, times = teachers.name(tid), tdata["AVAILABLE"]
            if times:
                atable = []
                lunch = []
                self.lunch_periods[tid] = lunch
                for d in days:
                    l = []
                    lunch.append(l)
                    daydata = times[d.short]
                    daylist = []
                    atable.append(daylist)
                    i = 0
                    for p in periods:
                        val = daydata[p.short]
                        if val == "+":
                            l.append(i)
                        i += 1
                        daylist.append(bool(val))
                self.available[tid] = atable
            else:
                # TODO: Should such a teacher be excluded?
                # Or count as "always available"???
                self.available[tid] = None
                self.lunch_periods[tid] = None
            self[tid] = tname
            self.address[tid] = tdata["__FILEPATH__"]
            self.alphatag[tid] = tdata["SORTNAME"]
            constraints = {}
            self.constraints[tid] = constraints
            for c, f in conditions.conditions.items():
                constraints[c] = f.value(tdata[c])

    def list_teachers(self):
        """Return a sorted list of teacher ids."""
        return sorted(self.alphatag, key=lambda x: self.alphatag[x])


class Conditions:
    """Handle teacher "conditions", as defined in the "DEFAULTS" entry in
    the configuration file TEACHER_FIELDS.
    """

    def __init__(self, fields):
        """Produce a handler for each condition via the mapping
        <self.conditions>.
        The handlers are then used for each teacher by calling their
        <value> method, which handles:
            no value -> <None>
            '*'      -> default value
            other    -> check validity, preprocess
        """
        self.name2display = {}
        for line in fields["INFO_FIELDS"]:
            self.name2display[line["NAME"]] = line["DISPLAY_NAME"]
        self.conditions = {}
        for name, value in fields["DEFAULTS"].items():
            if not isinstance(value, list):
                raise TT_Error(_BAD_CONDITION_DEF.format(name=name))
            try:
                f = getattr(self, value[1])
            except AttributeError:
                raise TT_Error(_BAD_CONDITION_DEF.format(name=name))
            self.conditions[name] = f(name, *value)

    @staticmethod
    def value(val):
        """Parse a condition value.
        It may have a weighting as suffix: @n, where n is in the range
        0 to 10.
        """
        try:
            v, w = val.rsplit("@", 1)
        except ValueError:
            return val, None
        return v, int(w)  # Can raise <ValueError>

    @classmethod
    def RANGE(cls, name, default, key, *args):
        """Build a handler for RANGE conditions. A minimum and maximum
        are supplied.
        """

        class Range:
            def __init__(self, condition, default, vmin, vmax):
                self.condition = condition
                self.default = default
                self.vmin = vmin
                self.vmax = vmax

            def value(self, val):
                if val:
                    if val == "*":
                        return self.default
                    v0, w = cls.value(val)
                    try:
                        v = int(v0)
                        if v < self.vmin or v > self.vmax:
                            raise ValueError
                    except ValueError:
                        raise TT_Error(
                            _NOT_IN_RANGE.format(name=self.condition, val=val)
                        )
                    return v, w
                return None

        try:
            vmin = int(args[0])
            vmax = int(args[1])
            if vmax < vmin:
                raise ValueError
            if len(args) != 2:
                raise ValueError
            if default:
                v, w = cls.value(default)
                d = int(v)
                if d < vmin or d > vmax:
                    raise ValueError
                val = (d, w)
            else:
                val = None
        except ValueError:
            raise TT_Error(_BAD_CONDITION_DEF.format(name=name))
        return Range(name, val, vmin, vmax)

    @classmethod
    def FROM(cls, name, default, key, *args):
        """Build a handler for FROM conditions: accepting a subset of
        a preset set of values.
        """

        class From:
            def __init__(self, condition, default, vals):
                self.condition = condition
                self.default = default
                self.vals = vals

            def value(self, val):
                if val:
                    if val == "*":
                        return self.default
                    v0, w = cls.value(val)
                    try:
                        v = set(v0.split())
                        if v <= self.vals:
                            return v, w
                    except ValueError:
                        pass
                    raise TT_Error(
                        _NOT_SUBSET.format(name=self.condition, val=val)
                    )
                    return v, w
                return None

        if default:
            try:
                v, w = cls.value(default)
                d = set(v.split())
                vset = set(args)
                if d <= vset:
                    return From(name, (d, w), vset)
            except ValueError:
                pass
            raise TT_Error(_BAD_CONDITION_DEF.format(name=name))
        return From(name, None, args)


class BlockCourse(NamedTuple):
    CLASS: str  # Class (short) name (e.g. "09G")
    GROUPS: FrozenSet[str]  # Full name (e.g. "Donnerstag")
    SID: str  # Subject-id
    NUMBER: int  # Number of course blocks (for "++"), otherwise 0
    REALTIDS: Set[str]  # Set of teacher-ids
    ROOMLIST: List[
        str
    ]  # List of possible room-ids (the first entry can be "-")


class Lesson(NamedTuple):
    BLOCK: str  # "++", "--" or ""
    CLASS: str  # Class (short) name (e.g. "09G")
    GROUPS: FrozenSet[str]  # Full name (e.g. "Donnerstag")
    SID: str  # Subject-id
    TIDS: Set[str]  # for timetable-clash checking,
    REALTIDS: Set[str]  # Set of teacher-ids
    ROOMLIST: List[str]  # List of possible room-ids
    LENGTHS: List[int]


class Classes:
    __slots__ = (
        "lesson_list",  # a list of the <Lesson>s from all classes
        "available",  # class -> a list of day-lists of period availability
        "address",  # class -> class data-table path
        "lunch_periods",  # class -> a list of day-lists of possible break periods
        "__lesson_index",  # internal counter
        "class_name",  # class -> long class name:
        "atomics_lists",  # class -> list of "atomic" groups
        "element_groups",  # class -> "element" groups -> frozenset of atomic groups
        # As element groups, but for the dotted groups from the group divisions:
        "extended_groups",  # class -> "dotted" groups -> frozenset of atomic groups
        "class_divisions",  # class -> list of divisions (which are lists of strings)
        # Similar to element_groups, but the atomic groups have a class prefix
        # (e.g. "11G.A.G" instead of just "A.G").
        # Also the "extended" groups are included and there is an entry for the whole
        # class (with key "*").
        "class_groups",
        # The reverse mapping, basically turning class_groups around,
        # so that the values (frozensets of atomic groups) become the keys.
        # The values to which these map get a class prefix (e.g. "11G.A"
        # instead of just "A"). The value corresponding to the frozenset
        # of all atomic groups is the class (e.g. "11G") instead of "*".
        # There is also an entry mapping the frozenset of the full class
        # (e.g. "11G") to the class itself.
        "groupsets_class",
        "timetable_teachers",  # tid -> list of lesson-indexes
        "class_lessons",  # class -> list of lesson-indexes
        "class2room",  # class -> class "home" room
        "parallel_tags",  # tag -> list of parallel lesson-indexes
        "block2courselist",  # lesson-index -> list of courses in block
        "block2rooms",  # lesson-index -> list of possible room combinations
        "block2roomlists",  # lesson-index -> list of room-choice lists
        "block2minus_list", # lesson-index -> list of block courses with "-" rooms
        "classes",  # list of classes whose subject tables have been read in
        "SUBJECTS",
        "ROOMS",
        "TEACHERS",
        "__global_blocks",  # internal mapping of blocks
    )

    def __init__(self, days, periods, SUBJECTS, ROOMS, TEACHERS):
        """Initialize with the valid lesson slots for each class. The
        data is read from the class-days-tables.
        Build a mapping available via attribute <available>:
                {class: class availability}.
        The value is a day/periods matrix of <bool> values.
        Also, possible periods for lunch breaks are extracted from the
        class tables.
        Finally read and process the data for the individual classes.
        """
        self.available = {}
        self.address = {}
        self.lunch_periods: Dict[str, List[List[int]]] = {}
        folder = DATAPATH("TIMETABLE/CLASSES")
        fields = MINION(DATAPATH("TIMETABLE/CLASS_PERIODS_FIELDS"))
        for f in os.listdir(folder):
            fpath = os.path.join(folder, f)
            try:
                ctable = read_DataTable(fpath)
                ctable = filter_DataTable(ctable, fields, matrix=True)
            except TableError as e:
                raise TT_Error(_FILTER_ERROR.format(msg=f"{e} in\n {fpath}"))
            info = ctable["__INFO__"]
            klass = info["CLASS"]
            available = {}
            for row in ctable["__ROWS__"]:
                #                day = row.pop("DAY")
                day = row["DAY"]
                if day in available:
                    raise TT_Error(_DOUBLE_DAY.format(day=day))
                #                del(row["FULL_DAY"])
                available[day] = row
            self.address[klass] = fpath
            atable = []
            self.available[klass] = atable
            lunch = []
            self.lunch_periods[klass] = lunch
            for d in days:
                l = []
                lunch.append(l)
                daydata = available[d.short]
                daylist = []
                atable.append(daylist)
                i = 0
                for p in periods:
                    val = daydata[p.short]
                    if val == "+":
                        l.append(i)
                    i += 1
                    daylist.append(bool(val))
            self.available[klass] = atable

        ### Now initialize the lesson-reading structures
        # <Lesson>s are referenced by their index in the list <self.lesson_list>
        self.__lesson_index: int = -1
        self.lesson_list: List[Lesson] = []
        self.class_name: Dict[str, str] = {}
        self.atomics_lists: Dict[str, List[str]] = {}
        self.element_groups: Dict[str, Dict[str, FrozenSet[str]]] = {}
        self.extended_groups = {}
        self.class_divisions: Dict[str, List[List[str]]] = {}
        self.class_groups: Dict[str, Dict[str, FrozenSet[str]]] = {}
        self.groupsets_class: Dict[str, Dict[FrozenSet[str], str]] = {}
        self.timetable_teachers: Dict[str, List[int]] = {}
        self.class_lessons: Dict[str, List[int]] = {}
        self.class2room: Dict[str, str] = {}
        self.parallel_tags: Dict[str, List[int]] = {}
        self.block2courselist: Dict[int, List[BlockCourse]] = {}
        self.block2rooms: Dict[int, Set[FrozenSet[str]]] = {}
        self.block2roomlists: Dict[int,List[List[str]]] = {}
        self.block2minus_list: Dict[int,List[BlockCourse]] = {}

        # +++++++ Now the stuff dealing with the class-group-lesson data
        ### Read the lesson data (etc.) for all classes readable by the
        ### <Subjects> class (courses.py).
        ### The successfully read classes are listed at <self.classes>.

        self.SUBJECTS: TT_Subjects = SUBJECTS
        self.ROOMS: TT_Rooms = ROOMS
        self.TEACHERS: TT_Teachers = TEACHERS
        self.classes: List[str] = []
        self.__global_blocks = {}

        # Start with "classless" data
        __classes = []
        for k in Subjects().classes():
            if k.startswith("XX"):
                self.read_class_data(k)
                self.classes.append(k)
            else:
                __classes.append(k)
        for k in __classes:
            self.read_class_data(k)
            self.classes.append(k)

        ### Check room lists of blocks
        # For each ++-block build a set of room-sets, each set having a
        # possible room combination for the block.
        # Build the cartesian product of a list of roomlists and select
        # only the results which have distinct elements (rooms).
        # The value in <self.block2rooms> is a list of lists/sequences.
        for blockix, courselist in self.block2courselist.items():
            # Build list of needed rooms and a separate list of block
            # courses which specify rooms but no additional ones ("-").
            block: Lesson = self.lesson_list[blockix]
            if not courselist and block.BLOCK == "++":
                raise TT_Error(
                    _BLOCK_NO_COURSES.format(klass=block.CLASS, sid=block.SID)
                )
            roomlists: List[List[str]] = []
            self.block2roomlists[blockix] = roomlists
            minus_list: List[BlockCourse] = []
            self.block2minus_list[blockix] = minus_list
            if block.ROOMLIST:
                roomlists.append(block.ROOMLIST)
            for bcourse in courselist:
                if bcourse.ROOMLIST:
                    if bcourse.ROOMLIST[0] == "-":
                        minus_list.append(bcourse)
                    else:
                        roomlists.append(bcourse.ROOMLIST)
            # Now generate the cartesian product, then filter out those
            # permutations which have duplicated rooms and those
            # combinations which are already in the result list.
            l = len(roomlists)
            resultset: Set[FrozenSet[str]] = set()
            results: List[Sequence[str]] = []
            for cpx in product(*roomlists):
                cps = frozenset(cpx)
                if len(cps) == l and cps not in resultset:
                    resultset.add(cps)
                    results.append(cpx)
            if not results:
                TT_Error(
                    _BLOCK_NO_ROOM_COMBINATIONS.format(
                        klass=block.CLASS, sid=block.SID
                    )
                )
            if len(results) > _N_ROOM_COMBINATIONS:
                REPORT(
                    "WARNING",
                    _WARN_ROOM_COMBINATIONS.format(
                        klass=block.CLASS, sid=block.SID, n=len(results)
                    ),
                )
            # Check "minus" courses. There should be some intersection
            # with the room combinations ...
            # There are actually (at least) two types of problem:
            #  - A "minus" room list may be unsupported by any of the
            #    possible room combinations.
            #  - A group of "minus" room lists may not all be supported
            #    by any of the possible room combinations.
            room_sets = []
            for rlist in results:
                # <rlist> is a sequence of rooms
                room_sets.append(set(rlist))
            course_results: List[List[Sequence[str]]] = []
            for bcourse in minus_list:
                roomlist: List[str] = bcourse.ROOMLIST[1:]
                newroomlist: List[Sequence[str]] = []
                i = 0
                disjoint = False
                for roomset in room_sets:
                    if roomset.isdisjoint(roomlist):
                        disjoint = True
                    else:
                        newroomlist.append(results[i])
                    i += 1
                if newroomlist:
                    # Add the possibly reduced list to <results2>
                    course_results.append(newroomlist)
                    if disjoint:
                        REPORT(
                            "WARNING",
                            _WARN_ROOMS_LOST.format(
                                klass=bcourse.CLASS,
                                sid=bcourse.SID,
                                block=block.SID,
                            ),
                        )
                else:
                    # bcourse has an unsupported room
                    raise TT_Error(
                        _BLOCK_COURSE_NO_ROOM.format(
                            klass=bcourse.CLASS,
                            sid=bcourse.SID,
                            block=block.SID,
                        )
                    )
            # Now check for no overlap in <course_results>.
            if course_results:
                list0: List[Sequence[str]] = course_results[0]
                for listn in course_results[1:]:
                    list1: List[Sequence[str]] = [
                        l for l in listn if l in list0
                    ]
                    if list1:
                        list0 = list1
                    else:
                        raise TT_Error(
                            _BLOCK_COURSES_ROOM_PROBLEM.format(
                                block=block.SID, klass=block.CLASS
                            )
                        )
                self.block2rooms[blockix] = list0
            else:
                self.block2rooms[blockix] = results
        ### Post-processing of lesson data (tags, etc.)
        for tag, lesson_indexes in self.parallel_tags.items():
            if len(lesson_indexes) < 2:
                continue
            # Check the compatibility of the fields
            nl, g, t, k, s = None, None, None, None, None
            for lx in lesson_indexes:
                l = self.lesson_list[lx]
                # The actual lessons must match in number and length
                if nl:
                    if l.LENGTHS != nl:
                        raise TT_Error(
                            _TAG_LESSONS_MISMATCH.format(
                                tag=tag,
                                sid0=s,
                                klass0=k,
                                sid1=l.SID,
                                klass1=l.CLASS,
                            )
                        )
                else:
                    nl = l.LENGTHS
                    g = l.GROUPS
                    t = l.TIDS
                    k = l.CLASS
                    s = l.SID
                    continue
                # The teachers must be fully distinct
                if t.intersection(l.TIDS):
                    raise TT_Error(
                        _TAG_TEACHER_DOUBLE.format(
                            tag=tag,
                            sid0=s,
                            klass0=k,
                            sid1=l.SID,
                            klass1=l.CLASS,
                        )
                    )
                # The groups must be fully distinct
                if g.intersection(l.GROUPS):
                    raise TT_Error(
                        _TAG_GROUP_DOUBLE.format(
                            tag=tag,
                            sid0=s,
                            klass0=k,
                            sid1=l.SID,
                            klass1=l.CLASS,
                        )
                    )
                # TODO: The rooms are probably too complicated to compare ...

        # Add the blocks to the teachers' lesson lists
        for lesson_index in self.block2courselist:
            data = self.lesson_list[lesson_index]
            for tid in data.REALTIDS:
                try:
                    self.timetable_teachers[tid].append(lesson_index)
                except KeyError:
                    self.timetable_teachers[tid] = [lesson_index]

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

        ### Classroom
        rid = info["CLASSROOM"]
        if rid:
            if rid in self.ROOMS:
                self.class2room[klass] = rid
            else:
                raise TT_Error(_BAD_CLASSROOM.format(klass=klass, rid=rid))
        else:
            self.class2room[klass] = ""

        ### Add the lessons.
        self.read_lessons(klass, subjects.class_subjects(klass))

    def read_groups(self, klass, raw_groups):
        """Parse the GROUPS data for the given class.
        This is a '|'-separated list of mutually exclusive class divisions.
        A division is a space-separated list of groups. These groups
        may contain '.' characters, in which case they are intersections
        of "element" groups (no dot). Neither these element groups nor their
        dotted intersections may appear in more than one division.
        A division might be "r1 r2 r3", or "A.G B.G B.R".
        As the class divisions must be given as a set of non-intersecting
        groups, the element (undotted) groups may need to be expressed
        (internally for the timetable) as a combination of dotted groups,
        e.g. B as "B.G,B.R".
        The "minimal subgroups" for the class are all possible combinations
        of the element groups from different divisions. Here I call them
        "atomic" groups, their elements are separated by dots, e.g. "A.G.r1".
        """
        if klass.startswith("XX"):
            return
        ### Add declared class divisions (and their groups).
        divisions = [["*"]]
        division_ix = 0
        __element2division = {}  # To check uniqueness of elements
        divs = []
        atomic_groups = [frozenset()]
        all_atoms = set()
        for glist in raw_groups.split("|"):
            division_ix += 1
            dgroups = glist.split()
            divisions.append(dgroups)
            __division = []
            for item in dgroups:
                elist = item.split(".")
                __division.append(frozenset(elist))
                # Check for element duplication in other divisions
                for e in elist:
                    try:
                        if __element2division[e] != division_ix:
                            raise TT_Error(
                                _ELEMENT_IN_MULTIPLE_DIVISIONS.format(
                                    klass=klass, e=e
                                )
                            )
                    except KeyError:
                        __element2division[e] = division_ix
            divs.append(__division)
            ### Update the list of element combinations with the elements
            ### from the current division. Each entry in the list is a
            ### frozenset of one element from each division.
            ag2 = []
            for item in atomic_groups:
                for item2 in __division:
                    all_atoms |= item2
                    ag2.append(item | item2)
            atomic_groups = ag2
        self.class_divisions[klass] = divisions
        ### Build a sorted list of "atomic" groups for the class
        al = [".".join(sorted(ag)) for ag in atomic_groups]
        al.sort()
        self.atomics_lists[klass] = al  # All (possibly dotted) atomic groups
        ### Make a mapping of element groups to frozensets of their
        ### dotted atomic groups.
        gmap = {
            a: frozenset(
                [".".join(sorted(ag)) for ag in atomic_groups if a in ag]
            )
            for a in all_atoms
        }
        self.element_groups[klass] = gmap

        ### The same for the dotted groups from the divisions (if any)
        xmap = {}
        for division in divs:
            for item in division:
                if len(item) < 2:  # Check dotted
                    continue
                if item not in gmap:
                    xmap[".".join(sorted(item))] = frozenset.intersection(
                        *[gmap[i] for i in item]
                    )
        self.extended_groups[klass] = xmap
        self.make_class_groups(klass)

    def make_class_groups(self, klass):
        """Build the entry for <self.class_groups> for the given class.
        Also build the reversed mapping <self.groupsets_class>.
        This method may need to be overridden for specific timetable
        generators.
        """
        gmap = {}
        reversemap = {}
        for _map in self.element_groups[klass], self.extended_groups[klass]:
            for k, v in _map.items():
                vset = frozenset([f"{klass}.{ag}" for ag in v])
                gmap[k] = vset
                ### Avoid duplicate values – the first entry (from
                ### <self.element_groups>) will be simpler.
                if vset not in reversemap:
                    reversemap[vset] = f"{klass}.{k}"
        self.class_groups[klass] = gmap
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

    def group_classgroups(self, klass, group):
        """Return the frozenset of "full" atomic groups for the given class
        and group. The group may be an "element" group, or a dotted
        group declared within a "division".
        This method may need to be overridden in a specific timetable
        generator (see <make_class_groups>),
        """
        cg = self.class_groups[klass]
        try:
            return cg[group]
        except KeyError:
            pass
        # Try reordering a dotted group
        gsplit = group.split(".")
        if len(gsplit) > 1:
            try:
                return cg[".".join(sorted(gsplit))]
            except KeyError:
                pass
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

        class_blocks = {}  # collect {block-sid: block-lesson-tag}
        class_lessons = []  # collect all lesson-indexes for this class
        self.class_lessons[klass] = class_lessons
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
                if _durations != "*":
                    for d in _durations.split():
                        i = int(d)
                        if i > 0 and i <= _MAX_DURATION:
                            durations.append(i)
                        else:
                            raise ValueError
            except ValueError:
                raise TT_Error(
                    _INVALID_ENTRY.format(
                        klass=klass,
                        field=Subjects().SUBJECT_FIELDS["LENGTHS"],
                        sname=sname,
                        val=_durations,
                    )
                )
            # Sort the durations
            durations.sort()

            ### Teachers
            _tids = read_field("TIDS")
            real_teachers: Set[str] = set()
            teachers = real_teachers  # yes, the same set!
            if not _tids:
                # "Block" only: teachers may be added
                pass
            elif _tids == "--":
                teachers = set()
                # <teachers> now remains empty
            else:
                tids = _tids.split()
                for tid in tids:
                    if tid in self.TEACHERS:
                        real_teachers.add(tid)
                    else:
                        raise TT_Error(
                            _UNKNOWN_TEACHER.format(
                                klass=klass, sname=sname, tid=tid
                            )
                        )

            ### Rooms
            _rids: str = read_field("ROOMS")
            minus_room: bool
            if _rids.startswith("-"):
                # Only valid in an entry for a ++-block course.
                # Don't add a new room requirement to the block. This
                # allows a room to be used in a block course without
                # causing an error because of multiple usage.
                minus_room = True
                _rids = _rids.lstrip("- ")
                if not _rids:
                    raise TT_Error(
                        _MINUS_NO_ROOM.format(klass=klass, sname=sname)
                    )
            else:
                minus_room = False
            # Each lesson line may specify the need for one room. This
            # room may be given explicitly, or as a list of possibilities,
            # separated by "/". Earlier items in the list are given
            # priority, if the allocation algortihm can handle it.
            # There are special symbols for the class's "home" room ("$")
            # and for the list of rooms which have been flagged as being
            # usable by this class ("?"). Any "extra" ("fake") rooms
            # will be added to the end of the "?-list" automatically.
            roomlist: List[str] = []
            if _rids:
                _extra = False
                for rid in _rids.split("/"):
                    if rid == "$":
                        r = self.class2room[klass]
                        if r:
                            if r in roomlist:
                                raise TT_Error(
                                    _CLASSROOM_REPEATED.format(klass=klass)
                                )
                            roomlist.append(r)
                        else:
                            raise TT_Error(_NO_CLASSROOM.format(klass=klass))
                    elif rid == "?":
                        _extra = True
                        for r in self.ROOMS.rooms_for_class[klass]:
                            if r not in roomlist:
                                roomlist.append(r)
                    elif rid in self.ROOMS:
                        roomlist.append(rid)
                    else:
                        raise TT_Error(
                            _UNKNOWN_ROOM.format(
                                klass=klass, sname=sname, rid=rid
                            )
                        )
                if _extra:
                    roomlist += self.ROOMS.xrooms

            ### Group
            group = read_field("GROUP")
            _groups = (
                self.group_classgroups(klass, group) if group else frozenset()
            )

            # The TAG value is a label for a set of lessons which should
            # be parallel, if possible. It should be an ASCII alphanumeric
            # string. This label can also be used to enforce particular
            # (fixed) times for the lesson(s).
            # A weighting can be set for both types of usage, but there is
            # no guarantee that the timetable generator will use this value.
            # In general, fixed placements should probably not have weightings
            # less than 10 (100%, the default). A weighting may be more useful
            # for lessons which should be simultaneous (without fixed placement).
            # The placement data is in the table PLACEMENT_TAGS.
            #
            # Also "blocks" (see below) may use the TAG field, but their
            # component lessons (which don't appear in the timeatable –
            # they are represented by the block) may not.
            #
            # To enable multi-class blocks, there can be one or more
            # special "classes", starting with "XX". They are not real
            # classes. These files can be used to enter blocks which are
            # for multiple classes, but also "lessons" (or other activities)
            # which have no entry in a class timetable.
            #
            # Such multi-class blocks must have a special way of referring
            # to them, so their subject ids have a suffix:  '+tag'.
            # This suffix serves only to label the block entry, has no
            # inherent relationship to a tag in the TAG field (so a tag
            # can appear in both) and is removed in the SID  field of the
            # generated data. This subject tag can not be used for
            # placements – though the same tag could be used here.
            # Note that '+tag' can also be used in normal class files to
            # disambiguate blocks – in case the subject id is used more
            # than once.

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
            #
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
            #                   this limitation can be overcome. Subject-ids with
            #                   suffix are also "known" in other classes (so
            #                   long as these are read in later). These subject-ids
            #                   may appear in BLOCK fields, to indicate that the
            #                   lesson belongs to this block.
            #                   The suffix will be stripped except for this usage
            #                   as block reference.
            #
            # BLOCK = '--'      "Non-lesson", not placed in timetable (for "EXTRA"
            #                   entries). This is handled like a timetabled block
            #                   (see above), except that the LENGTHS field specifies
            #                   the "total lessons" (~ payment units) – a single
            #                   number. Trying to specify a placement for such an
            #                   entry makes no sense, so the TAG field should be empty.
            #
            # BLOCK = sid       A block "component". <sid> is the subject-id
            #                   (potentially with '+tag' suffix). With '+tag' the
            #                   block entry may be in another file – presumably an
            #                   "XX"-class file. The block entry must be previously
            #                   defined and globally unique (only "XX"-class files
            #                   are guaranteed to be read in before another table.
            #                   Without such a suffix the block entry must be unique
            #                   and previously defined within the same table.
            #
            #                   This entry does not appear in the timetable.
            #                   It gets an entry as a <BlockCourse> in the list of
            #                   components for the associated block, accessed
            #                   via <self.block2courselist> (key is the block's
            #                   lesson-id).
            #                   Teachers and groups are added to the lesson
            #                   entry for the block (they may occur in more than
            #                   one block-course). If additional rooms are needed,
            #                   they are accessed via the block-course entry.
            #
            # TODO: what are the implications of "parallel" blocks?
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

            if block:
                if block == "++":
                    # A "block" entry.
                    pass
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
                    if roomlist:
                        raise TT_Error(
                            _ROOM_NO_LESSON.format(klass=klass, sname=sname)
                        )
                else:
                    # A block component, <block> = block-sid
                    if len(sidx) > 1:
                        raise TT_Error(
                            _BAD_SID_TAG.format(klass=klass, sid=sid)
                        )
                    try:
                        # First check within this table
                        block_lesson_index = class_blocks[block]
                    except KeyError:
                        try:
                            block_lesson_index = self.__global_blocks[block]
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
                        # If the LENGTHS field is "*", the durations list
                        # will be empty.
                        if len(durations) > 1:
                            raise TT_Error(
                                _COMPONENT_BAD_LENGTH_SID.format(
                                    klass=klass, sname=sname, sid=block
                                )
                            )
                        number = durations[0]
                    else:
                        number = 0
                    block_lesson = self.lesson_list[block_lesson_index]
                    block_course_list = self.block2courselist[
                        block_lesson_index
                    ]

                    # For each component of a block, a block-course is added
                    # to the list for the associated block.
                    # Teachers and groups are also added to (unioned with –
                    # they are sets) the lesson item for the block, but if
                    # an additional room is needed, this is available only via
                    # the block-course.
                    block_lesson.REALTIDS.update(real_teachers)
                    # As the groups are frozensets the whole block lesson
                    # must be replaced if there is a chenge.
                    __groups = block_lesson.GROUPS | _groups
                    if __groups != block_lesson.GROUPS:
                        block_lesson = block_lesson._replace(GROUPS=__groups)
                        self.lesson_list[block_lesson_index] = block_lesson
                    if roomlist:
                        if block_lesson.BLOCK == "--":
                            raise TT_Error(
                                _ROOM_NO_LESSON.format(klass=klass, sname=sname)
                            )
                        if minus_room:
                            roomlist.insert(0, "-")
                    # Add data for the block component,
                    # it can register the need for a room
                    block_course_list.append(
                        BlockCourse(
                            CLASS=klass,
                            GROUPS=_groups,
                            SID=sid,
                            NUMBER=number,
                            REALTIDS=real_teachers,  # all associated teachers
                            ROOMLIST=roomlist,
                        )
                    )
                    continue
            else:
                # A "normal" lesson
                if len(sidx) > 1:
                    raise TT_Error(_BAD_SID_TAG.format(klass=klass, sid=sid))
            if minus_room:
                raise TT_Error(
                    _MINUS_NOT_BLOCK_COURSE.format(klass=klass, sname=sname)
                )

            ### Lesson-id generation
            self.__lesson_index += 1
            if block:
                self.block2courselist[self.__lesson_index] = []
                # This must be the only definition of a block for
                # this subject-id in this table.
                if sid in class_blocks:
                    raise TT_Error(
                        _MULTIPLE_BLOCK.format(klass=klass, sname=sname)
                    )
                class_blocks[sid] = self.__lesson_index
                if len(sidx) > 1:
                    # This must be the only definition of a block for
                    # this subject-id in any table.
                    if sid in self.__global_blocks:
                        raise TT_Error(
                            _MULTIPLE_BLOCK.format(klass=klass, sname=sname)
                        )
                    self.__global_blocks[sid] = self.__lesson_index
            else:
                for tid in real_teachers:
                    try:
                        self.timetable_teachers[tid].append(self.__lesson_index)
                    except KeyError:
                        self.timetable_teachers[tid] = [self.__lesson_index]
            if tag:
                try:
                    self.parallel_tags[tag].append(self.__lesson_index)
                except KeyError:
                    self.parallel_tags[tag] = [self.__lesson_index]
            class_lessons.append(self.__lesson_index)
            self.lesson_list.append(
                Lesson(
                    BLOCK=block,
                    CLASS=klass,
                    GROUPS=_groups,
                    SID=sid,
                    TIDS=teachers,  # for timetable-clash checking,
                    REALTIDS=real_teachers,  # all associated teachers
                    ROOMLIST=roomlist,
                    LENGTHS=durations,
                )
            )

    def combine_atomic_groups(self, groups):
        """Given a set of atomic groups, possibly from more than one
        class, try to reduce it to elemental groups (as used in the data
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
                fg = gmap[frozenset(glist)]
                _groups.add(fg)
            except:
                _groups.update(glist)
        return _groups

    def teacher_check_list(self):
        """Return a "check-list" of the lessons for each teacher."""
        tlist = []
        for tid in self.TEACHERS:
            lesson_indexes = self.timetable_teachers.get(tid)
            if lesson_indexes:
                class_lessons = {}
                for lesson_index in lesson_indexes:
                    data = self.lesson_list[lesson_index]
                    klass = data.CLASS
                    try:
                        class_list, class_blocks = class_lessons[klass]
                    except KeyError:
                        class_list = []
                        class_blocks = []
                        class_lessons[klass] = [class_list, class_blocks]
                    if data.ROOMLIST:
                        rooms = f" // {','.join(data.ROOMLIST[:3])}"
                        if len(data.ROOMLIST) > 3:
                            rooms += ", ..."
                    else:
                        rooms = ""
                    sname = self.SUBJECTS[data.SID.split("+", 1)[0]]
                    # Combine subgroups
                    groups = sorted(self.combine_atomic_groups(data.GROUPS))
                    durations = data.LENGTHS
                    if data.BLOCK == "--":
                        d = durations[0] if durations else 0
                        entry = (
                            f"-- {sname} [{','.join(groups)}]:"
                            f" {_EXTRA} x {d}"
                        )
                        class_blocks.append(entry)
                    elif data.BLOCK == "++":
                        ll = ", ".join(lesson_lengths(durations))
                        entry = (
                            f"++ {sname} [{','.join(groups)}]:"
                            f" {_BLOCK}: {ll}{rooms}"
                        )
                        class_blocks.append(entry)
                    else:
                        ll = ", ".join(lesson_lengths(durations))
                        entry = f"{sname} [{','.join(groups)}]:" f" {ll}{rooms}"
                        class_list.append(entry)
                    if data.BLOCK:
                        # Get components
                        for component in self.block2courselist[lesson_index]:
                            if tid in component.REALTIDS:
                                cname = self.SUBJECTS[component.SID]
                                # Combine subgroups
                                groups = ",".join(
                                    sorted(
                                        self.combine_atomic_groups(
                                            component.GROUPS
                                        )
                                    )
                                )
                                if component.NUMBER:
                                    class_list.append(
                                        f"{cname}"
                                        f" [{groups}]:"
                                        f" {_BLOCK_COURSE}"
                                        f" ({sname}) x {component.NUMBER}"
                                    )
                                else:
                                    class_list.append(
                                        f"{cname}" f" [{groups}]:" f" ({sname})"
                                    )
                if class_lessons:
                    lines = []
                    tlist.append((tid, self.TEACHERS[tid], lines))
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
                            lines.append((f"Klasse {klass}", clines))
        return tlist


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
# B.G might also be used (A.G and B.R probably not, because they are
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


class TT_Placements(Dict[str, Tuple[int, List[Tuple[int, int]]]]):
    def __init__(self, classes_data, days, periods):
        super().__init__()
        self.dayx = days.short2index()
        self.periodx = periods.short2index()
        self.classes_data = classes_data
        lessons = classes_data.lesson_list
        parallel_tags = classes_data.parallel_tags
        try:
            place_data = read_DataTable(DATAPATH("TIMETABLE/PLACEMENT_TAGS"))
        except TableError as e:
            REPORT("ERROR", str(e))
            return
        place_data = filter_DataTable(
            place_data, MINION(DATAPATH("CONFIG/TT_PLACEMENTS"))
        )
        for row in place_data["__ROWS__"]:
            tag: str = row["TAG"]
            w: str = row["WEIGHTING"]
            weighting: int
            if w:
                try:
                    weighting = int(w)
                    if weighting < 0 or weighting > 10:
                        raise ValueError
                except ValueError:
                    raise TT_Error(
                        _BAD_PLACEMENT_WEIGHTING.format(tag=tag, w=w)
                    )
            else:
                # Default weighting is 100%
                weighting = 10
            places_list: List[Tuple[int, int]] = []
            for d_p in row["PLACE"].split():
                try:
                    d, p = d_p.strip().split(".")
                    dp: Tuple[int, int] = (self.dayx[d], self.periodx[p])
                except:
                    raise TT_Error(_INVALID_DAY_PERIOD.format(tag=tag, d_p=d_p))
                if dp in places_list:
                    raise TT_Error(
                        _REPEATED_DAY_PERIOD.format(tag=tag, d_p=d_p)
                    )
                places_list.append(dp)
            try:
                taglist = parallel_tags[tag]
            except KeyError:
                raise TT_Error(_UNKNOWN_TAG.format(tag=tag))
            durations: List[int] = lessons[taglist[0]].LENGTHS
            if len(durations) != len(places_list):
                if len(durations) > len(places_list):
                    REPORT("WARNING", _PREPLACE_TOO_FEW.format(tag=tag))
                else:
                    raise TT_Error(_PREPLACE_TOO_MANY.format(tag=tag))
            self[tag] = (weighting, places_list)

    def get_info(self, tag: str) -> Tuple[int, List[Tuple[int, int]]]:
        """Fetch the weighting and placement list for the given tag.
        If there is no entry in the table for the tag, return a default
        value and issue a warning.
        """
        try:
            return self[tag]
        except KeyError:
            REPORT("WARNING", _TAG_NO_ENTRY.format(tag=tag))
            return (10, [])


def lesson_lengths(durations):
    """Build a textual representation of the lesson numbers and lengths."""
    ll = []
    size = {}
    single, double = 0, 0
    for d in durations:
        if d == 1:
            single += 1
        elif d == 2:
            double += 1
        else:
            try:
                size[d] += 1
            except KeyError:
                size[d] = 1
    if single:
        ll.append(f" {_SINGLE} x {single}")
    if double:
        ll.append(f" {_DOUBLE} x {double}")
    for d, n in size.items():  # uses ordered nature of <dict>
        ll.append(f" {d} x {n}")
    return ll


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
    teachers = TT_Teachers(days, periods)
    for tid in teachers.list_teachers():
        v = teachers[tid]
        print(f"\n  {tid} ({teachers.alphatag[tid]}): {v}")
        print("   ", teachers.available[tid] or "–––")
        print("   ", teachers.lunch_periods[tid] or "–––")
        print("   ", teachers.constraints[tid])

    print("\nCLASSES:")
    classes = Classes(days, periods, subjects, rooms, teachers)

    #quit(0)

    for k in sorted(classes.available):
        print(f"\nCLASS {k} ({classes.class_name[k]}): {classes.address[k]}")
        print("*** HOME ROOM ***", classes.class2room[k])
        print("*** AVAILABLE ***", classes.available[k])
        print("*** LUNCH ***", classes.lunch_periods[k])
        print("*** DIVISIONS ***", classes.class_divisions[k])
        print("*** ATOMIC GROUPS ***", classes.atomics_lists[k])
        print("*** ELEMENT GROUPS ***", classes.element_groups[k])
        print("*** EXTENDED GROUPS ***", classes.extended_groups[k])
        print("*** CLASS GROUPS ***", classes.class_groups[k])
        print("*** GROUP SETS ***", classes.groupsets_class[k])
        print("*** CLASS LESSONS ***")
        for lx in classes.class_lessons[k]:
            l = classes.lesson_list[lx]
            print("      ", l.SID, l.GROUPS, l.LENGTHS)
        print("-----------------------------------------------------")

    # Further attributes:
    #        "timetable_teachers",  # tid -> list of lesson-indexes
    #        "class_lessons",  # class -> list of lesson-indexes
    #        "parallel_tags",  # tag -> list of parallel lesson-indexes
    #        "block2courselist",  # lesson-index -> list of courses in block
    #        "block2rooms",  # lesson-index -> list of room lists for block

    print("\nBLOCK2COURSELIST")
    for li, cl in classes.block2courselist.items():
        l = classes.lesson_list[li]
        print(f"  {l.CLASS} {l.SID}: {l.BLOCK} --- {l.REALTIDS}")
    #        print(f"  {li}: {cl}")

    tcl = classes.teacher_check_list()
    odir = DATAPATH("testing/tmp")
    os.makedirs(odir, exist_ok=True)
    from timetable.tt_check_list import teacher_class_subjects

    pdfbytes = teacher_class_subjects(tcl)
    pdffile = os.path.join(odir, "Lehrer-Stunden-Kontrolle.pdf")
    with open(pdffile, "wb") as fh:
        fh.write(pdfbytes)
        print("\nTeacher check list:", pdffile)

    print("\nPLACEMENTS:")
    placements = TT_Placements(classes, days, periods)
    for tag, wp in placements.items():
        print(
            f"  {tag:10} @{wp[0]:02}: {', '.join([f'{d}.{p}' for d, p in wp[1]])}"
        )
    print()
    print(f" ... 'unknown': {placements.get_info('unknown')}")

    print("\nLESSONS:")
    i = 0
    for l in classes.lesson_list:
        i += 1
        print(f" {i:3}: {l}")
