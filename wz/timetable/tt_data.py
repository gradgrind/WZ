# -*- coding: utf-8 -*-

"""
TT/tt_data.py - last updated 2021-07-27

Read timetable information from the various sources ...

==============================
Copyright 2021 Michael Towers

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

WHOLE_CLASS = "alle"    # name for a "group" comprising the whole class
_TEACHERS = "Lehrkräfte" # error reporting only, refers to the input table
_ROOMS = "Räume"         # error reporting only, refers to the input table
_MAX_DURATION = 4        # maximum length of a lesson

### Messages

_CLASS_INVALID = "Klassenbezeichnungen dürfen nur aus Zahlen und" \
        " lateinischen Buchstaben bestehen: {klass} ist ungültig."
_CLASS_TABLE_DAY_DOUBLE = "In der Klassen-Tage-Tabelle: Für Klasse {klass}" \
        " gibt es zwei Einträge für Tag {day}."
_UNKNOWN_GROUP = "Klasse {klass}: unbekannte Gruppe – {group}"
_UNKNOWN_SID = "Klasse {klass}: Fach {sid} ({sname}) ist unbekannt"
_GROUP_IN_MULTIPLE_SPLITS = "Klasse {klass}: Gruppe {group} in >1 Teilung"
_INVALID_ENTRY = "Klasse {klass}, Feld_{field}: ungültiger Wert ({val})"
_TAG_GROUP_DOUBLE = "Klasse {klass}: Stundenkennung „{tag}“ für Gruppe" \
        " {group} zweimal definiert"
_TAG_SID_MISMATCH = "Klasse {klass}: Fach {sid} mit Stundenkennung „{tag}“" \
        " ist anders als in Gruppen {group1}"
_TAG_BLOCK_MISMATCH = "Klasse {klass}: Epoche {block} mit Stundenkennung" \
        " „{tag}“ ist anders als in Gruppen {group1}"
_TAG_LESSONS_MISMATCH = "Klasse {klass}: Stundenkennung „{tag}“ hat" \
        " unterschiedliche Stundenzahlen als in Gruppen {group1}"
_FIELD_MISSING = "Klasse {klass}: Feld {field} fehlt in Fachtabelle"
_TEACHER_INVALID = "Lehrerkürzel dürfen nur aus Zahlen und" \
        " lateinischen Buchstaben bestehen: {tid} ist ungültig."
_TEACHER_NDAYS = "{name} ({tid}), verfügbare Stunden: Daten für genau" \
        " {ndays} Tage sind notwendig"
_TEACHER_DAYS_INVALID = "{name} ({tid}), verfügbare Stunden: ungültige Daten"
_UNKNOWN_TEACHER = "Klasse {klass}: unbekannte Lehrkraft ({tid})"
_ROOM_INVALID = "Raumkürzel dürfen nur aus Zahlen und" \
        " lateinischen Buchstaben bestehen: {rid} ist ungültig."
_UNKNOWN_ROOM = "Klasse {klass}: unbekannter Raum ({rid})"
_DOUBLED_KEY = "Tabelle der {table}: Feld „{key}“ muss eindeutig sein:" \
        " „{val}“ kommt zweimal vor"
_DUPLICATE_TAG = "Fachtabelle, im Feld {key}: Werte „{source1}“ und" \
        " „{source2}“ sind intern nicht unterscheidbar."
_LESSON_CLASS_MISMATCH = "In der Tabelle der Unterrichtsstunden für" \
        " Klasse {klass} ist die Klasse falsch angegeben:\n  {path}"
_UNKNOWN_TAG = "Tabelle der festen Stunden: unbekannte Stundenkennung „{tag}“"
_INVALID_DAY_PERIOD = "Tabelle der festen Stunden: ungültige" \
        " Tag.Stunde-Angabe: {d_p}"
_PREPLACE_TOO_MANY = "Warnung: zu viele feste Stunden definiert für" \
        " Stundenkennung {tag}"
_PREPLACE_TOO_FEW = "Warnung: zu wenig feste Stunden definiert für" \
        " Stundenkennung {tag}"
_TABLE_ERROR = "In Klasse {klass}: {e}"
_SUBJECT_NAME_MISMATCH = "Klasse {klass}, Fach {sname} ({sid}):" \
        " Name weicht von dem in der Fachliste ab ({sname0})."
_MULTIPLE_BLOCK = "Klasse {klass}: Epoche mit Fach-Kürzel {sid} mehrfach" \
        " definiert"
_BLOCK_TAG_UNDEFINED = "Klasse {klass}: Fach {sname} ({sid}) in" \
        " undefinierter Epoche ({block})"
_BLOCK_TAG_DEFINED = "Klasse {klass}: „Unechtes“ Fach {sname} ({sid}) in" \
        " definierter „Epoche“ ({block})"
_BLOCK_TAG_UNKNOWN = "Klasse {klass}: „Unechtes“ Fach {sname} ({sid}) in" \
        " unbekannter „Epoche“ ({block})"
_BLOCK_NUMBER = "Klasse {klass}, Fach {sname} ({sid}): Anzahl der Epochen" \
        " in {block} ungültig"
_GROUP_NOT_SUBSET = "Klasse {klass}, Fach {sname} ({sid}), Epoche {block}:" \
        "\n  Gruppe {group} nicht (völlig) enthalten"
_PLACE_MULTIPLE_LENGTHS = "Unterricht mit verschiedenen Längen kann nicht" \
        " platziert werden: {data}"

########################################################################

import sys, os, datetime, re
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start
#TODO: Temporary redirection to use real data (there isn't any test data yet!)
#    start.setup(os.path.join(basedir, 'TESTDATA'))
    start.setup(os.path.join(basedir, 'DATA'))

#TODO: classrooms

# IMPORTANT: Note that some uses of Python dicts here may assume ordered
# entries. If the implementation is altered, this should be taken into
# account. One place is the definition of pre-placed lessons
# for a subject. If there is more than one entry for this subject and
# varying durations, the placement could be affected.

### +++++

from tables.spreadsheet import Spreadsheet, \
        read_DataTable, filter_DataTable, \
        make_DataTable, make_DataTable_filetypes, \
        TableError, spreadsheet_file_complete

from minion import Minion
_Minion = Minion()
MINION = _Minion.parse_file
#TODO: proper path:
TT_CONFIG = MINION(DATAPATH('CONFIG_timetable'))

class TT_Error(Exception):
    pass

### -----

class Days(dict):
    def __init__(self):
        super().__init__()
        fields = TT_CONFIG['DAY_FIELDS']
        days = read_DataTable(YEARPATH(TT_CONFIG['DAY_DATA']))
        days = filter_DataTable(days, fieldlist = fields,
                infolist = [], extend = False)['__ROWS__']
        bitmaps = []
        b = 1
        for day in days:
            bitmaps.append(str(b).zfill(len(days)))
            b *= 10
        i = 0
        for day in days:
            i += 1
            day['day'] = str(i)     # day-index starts at 1
            day['bitmap'] = bitmaps.pop()
            self[day['short']] = day
#
    def get_id(self, key):
        return self[key]['day']

##########

class Periods(dict):
    def __init__(self):
        super().__init__()
        fields = TT_CONFIG['PERIOD_FIELDS']
        periods = read_DataTable(YEARPATH(TT_CONFIG['PERIOD_DATA']))
        periods = filter_DataTable(periods, fieldlist = fields,
                infolist = [], extend = False)['__ROWS__']
        i = 0
        for pdata in periods:
            i += 1
            pdata['period'] = str(i) # Period-index starts at 1.
            key = pdata['short']
            self[key] = pdata
#
    def get_id(self, key):
        return self[key]['period']

###

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
        ptags = TT_CONFIG['CLASS_PERIODS_HEADERS'] + \
                [(p, '', '') for p in periods]
        class_table = read_DataTable(YEARPATH(TT_CONFIG['CLASS_PERIODS_DATA']))
        class_table = filter_DataTable(class_table, fieldlist = ptags,
                infolist = [], extend = False)['__ROWS__']
        for row in class_table:
            klass = row.pop('CLASS')
            if not klass.isalnum():
                raise TT_Error(_CLASS_INVALID.format(klass = klass))
            day = row.pop('DAY')
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
                    raise TT_Error(_CLASS_TABLE_DAY_DOUBLE.format(
                            klass = klass, day = day))
                kmap[day] = row

        ### Now initialize the lesson-reading structures
        self.class_name = {}
        self.class_divisions = {}
        self.class_groups = {}
        self.classrooms = {}
        self.lessons = {}
        self.LESSON_FIELDS = {f: t
                for f, t, *x in TT_CONFIG['LESSON_FIELDS']}
        self.class_blocks = {}

#++++++++++++++++ Now the stuff dealing with the class-group-lesson data

    def all_lessons(self, SUBJECTS, ROOMS, TEACHERS):
        """Read the lesson data (etc.) for all classes defined in the
        class-day-periods table.
        Return a list of successfully read classes.
        """
        self.SUBJECTS = SUBJECTS
        self.ROOMS = ROOMS
        self.TEACHERS = TEACHERS
        classes = []
        self.blocks = {}    # collect block lessons
        for klass in self.class_days_periods:
            if self.read_class_data(klass):
                classes.append(klass)
        return classes
#
    def read_class_data(self, klass):
        """Read the information pertaining to the teaching groups within
        the given class and the associated lessons from the lessons file
        for the class.
        """
        filepath = YEARPATH(TT_CONFIG['CLASS_LESSONS']).format(klass = klass)
        try:
            lesson_data = read_DataTable(filepath)
        except TableError as e:
#TODO: fix print
            print("!!!", str(e))
            return False
        try:
            lesson_data = filter_DataTable(lesson_data,
                    TT_CONFIG['LESSON_FIELDS'],
                    TT_CONFIG['LESSON_INFO']
            )
        except TableError as e:
            raise TT_Error(_TABLE_ERROR.format(klass = klass, e = str(e)))
        info = lesson_data['__INFO__']

        ### Add a class entry.
        info = lesson_data['__INFO__']
        if info['CLASS'] != klass:
            raise TT_Error(_LESSON_CLASS_MISMATCH.format(klass = klass,
                    path = filepath))
        self.class_name[klass] = info['NAME'] or klass

        ### Add the groups.
        self.read_groups(klass, info['GROUPS'])

        ### Classrooms?
        self.classrooms[klass] = info['CLASSROOMS'].split()

        ### Add the lessons.
        self.read_lessons(klass, lesson_data['__ROWS__'])

        return True
#
    def read_groups(self, klass, raw_groups):
        """Parse the GROUPS data for the given class.
        This is a '|'-separated list of mutually exclusive class divisions.
        A division is a space-separated list of groups. These groups
        may contain '.' characters, in which case they are intersections
        of "atomic" groups (no dot). Neither these atomic groups nor the
        dotted intersections may appear in more than one division.
        A division might be "A.G B.G B.R".
        <group_map> collects "atomic" groups (no dot) as well as
        "dotted" groups, e.g. A.G is the dotted group containing those
        pupils in both group A and group G. The values in this mapping
        are sets of division-groups, e.g. (for the example division above):
            group_map['A.G'] -> {'A.G'},
            group_map['B'] -> {'B.G', 'B.R'}, etc.
        As the class divisions must be given as a set of non-intersecting
        groups, the atomic (undotted) groups may need to be expressed
        (for the timetable) as a combination of dotted groups, e.g. B as
        "B.G,B.R".
        """
        ### Add a group entry for the whole class.
        group_map = {'*': {f'{klass}-{WHOLE_CLASS}'}}
        ### Add declared class divisions (and their groups).
        divisions = [['*']]
        for glist in raw_groups.split('|'):
            division = []
            xgmap = {}
            dgroups = glist.split()
            divisions.append(dgroups)
            for gsub in dgroups:
                gsub_g = f'{klass}-{gsub}'
                if gsub in group_map:
                    raise TT_Error(_GROUP_IN_MULTIPLE_SPLITS.format(
                            klass = klass, group = gsub))
                gsplit = gsub.split('.')
                if len(gsplit) > 1:
                    # Determine the component groups for each atomic group
                    for g in gsplit:
                        if g in group_map:
                            raise TT_Error(_GROUP_IN_MULTIPLE_SPLITS.format(
                                    klass = klass, group = g))
                        try:
                            xgmap[g].add(gsub_g)
                        except KeyError:
                            xgmap[g] = {gsub_g}
                group_map[gsub] = {gsub_g}
            ## Add the entries for the atomic groups to <group_map>
            group_map.update(xgmap)
        self.class_divisions[klass] = divisions
        self.class_groups[klass] = group_map
#
    def read_lessons(self, klass, lesson_lines):
        def read_field(field):
            try:
                return row[field]
            except KeyError:
                raise TT_Error(_FIELD_MISSING.format(klass = klass,
                        field = self.LESSON_FIELDS[field]))
        #+
        lesson_id = 0
#TODO: This may be wrong for fet (class-group ...)
        group_map = self.class_groups[klass]
        blocks = {}      # collect block-sids -> block-tag
        self.class_blocks[klass] = blocks
        for row in lesson_lines:
            # Make a list of durations.
            # Then for each entry, generate a lesson or a course within
            # a teaching block.
            _durations = read_field('LENGTHS')

            try:
                if not _durations:
                    raise ValueError
                if _durations == '*':
                    durations = None
                else:
                    durations = []
                    for d in _durations.split():
                        i = int(d)
                        if i > 0 and i <= _MAX_DURATION:
                            durations.append(i)
                        else:
                            raise ValueError
            except ValueError:
                raise TT_Error(_INVALID_ENTRY.format(klass = klass,
                        field = self.LESSON_FIELDS['LENGTHS'],
                        val = _durations))

            ### Teachers
            tids = read_field('TIDS').split()
            if tids:
                teachers = set(tids)
                for tid in tids:
                    if tid not in self.TEACHERS:
                        teachers.remove(tid)
                        print(_UNKNOWN_TEACHER.format(klass = klass,
                                tid = tid))
            else:
                teachers = set()

            ### Subject
            sid = read_field('SID')
#TODO: This can now happen because I am not filtering out lines with no lessons ...
# Either pass all subjects for timetable use (don't need special column then)
# or use some other test for timetable relevance.
            sname = read_field('SNAME')
            try:
                sname0 = self.SUBJECTS[sid]
            except KeyError:
                raise TT_Error(_UNKNOWN_SID.format(klass = klass,
                        sname = sname, sid = sid))
            if sname != sname0:
                print(_SUBJECT_NAME_MISMATCH.format(klass = klass,
                        sname0 = sname0, sname = sname, sid = sid))

            ### Group
            group = read_field('GROUP') # check later

            ### Rooms
            rids = read_field('ROOMS').split()
            if rids:
                rooms = set(rids)
                for rid in rids:
                    if rid not in self.ROOMS:
                        rooms.remove(rid)
                        print(_UNKNOWN_ROOM.format(klass = klass,
                                rid = rid))
            else:
                rooms = set()

# The BLOCK field can contain:
#   - nothing:  This is the "normal" case, for typical lesson entries.
#   - '*':      This means that the lesson is a teaching block covering
#               several courses, rather than a single course. It may also
#               be used for non-block parallel courses which each have
#               their own name for reports.
#               The LENGTHS field has its normal meaning, the lengths of
#               the component timetable lessons. However, it can also
#               specify a number of "payment units" for blocks (of lessons
#               or something else ...) which do not appear in the
#               timetable. This is achieved by entries starting with '*'.
#               After this comes a single number.
#               The teachers field (TIDS) can take the special value '*'
#               (~ "empty"), the teachers (or additional teachers) being
#               supplied by the contained courses.
#   - '--' [sid]: This specifies a "course" which will not itself appear
#               directly in the timetable, but specifies a number of
#               "payment units". Here there is no point in adding rooms
#               because there are no timetabled lessons.
#               The LENGTHS field must contain a single number,
#               representing the payment units (number of blocks).
#               Here, the optional sid is just used for documentation
#               purposes, specifying a sort of category for the entry.
#               sid should probably not be used to specify a lesson entry,
#               but it must be defined in the subject table.
#   sid:        Specifies a course within the teaching block with
#               subject-id sid (which must be previously defined in the
#               lesson table for the class).
#               The LENGTHS field must contain a single number,
#               representing the number of course blocks / payment units.
#               The LENGTHS field can also contain '*', meaning "take
#               the number from the main ('*') entry" – for permanently
#               running courses within a teaching block.

            ### Lesson-id generation
            # If the TAG field is empty the lesson id(s) will
            # be generated automatically.
            # Otherwise the entry should be an ASCII alphanumeric
            # string shared by all parallel classes/groups.
            # As a special case, a tag starting with '*-' is permitted:
            # it is intended for specifying positions for lessons within
            # a class, the '*' will be replaced by the class name.
            block = read_field('BLOCK')
            tag = None
            data = None
            _groups = get_groups(group_map, group)
            _tag = row['TAG']
            # Check compatibility with previous tagged entries
            if _tag:
                if _tag.isascii():
                    if _tag.startswith('*-'):
                        if _tag[2:].isalnum():
                            tag = klass + _tag[1:]
                    elif _tag.isalnum():
                        tag = _tag
                if not tag:
                    raise TT_Error(_INVALID_ENTRY.format(klass = klass,
                            field = self.LESSON_FIELDS['TAG'], val = _tag))
                data = self.lessons.get(tag)
                if data:
                    p_groups = data['GROUPS']
                    # The subject must be the same
                    if sid != data['SID']:
                        raise TT_Error(_TAG_SID_MISMATCH.format(
                                klass = klass, sid = sid, tag = tag,
                                group1 = repr(p_groups)))
                    # Also the actual lessons must match in number and length
                    if data['durations'] != durations:
                        raise TT_Error(_TAG_LESSONS_MISMATCH.format(
                                klass = klass, tag = tag,
                                group1 = repr(p_groups)))
                    # If groups are parallel, they must be fully distinct
                    # groups!
                    if _groups.intersection(p_groups):
                        raise TT_Error(_TAG_GROUP_DOUBLE.format(
                                klass = klass, tag = tag,
                                group = repr(_groups)))
                    p_groups.update(_groups)
                    data['CLASSES'].add(klass)
                    # Add teachers and rooms
                    data['TIDS'].update(teachers)
                    data['ROOMS'].update(rooms)
            else:
                lesson_id += 1
                tag = f'{klass}_{lesson_id:02}'
            if block:
                if block == '*':
                    # This specifies a block-lesson for the timetable
                    if sid in blocks:
                        raise TT_Error(_MULTIPLE_BLOCK.format(klass = klass,
                                sid = sid))
                    blocks[sid] = tag
                else:
                    if durations:
                        if len(durations) != 1:
                            raise TT_Error(_BLOCK_NUMBER.format(
                                    klass = klass, sid = sid,
                                    sname = sname, block = block))
                        n = durations[0]
                    else:
                        n = None
                    if block[0] == '-':
                        # Block with no lessons
                        _block = block.lstrip('- ')
                        if _block in blocks:
                            raise TT_Error(_BLOCK_TAG_DEFINED.format(
                                    klass = klass, sid = sid,
                                    sname = sname, block = block))
                        if _block and _block not in self.SUBJECTS:
                            raise TT_Error(_BLOCK_TAG_UNKNOWN.format(
                                    klass = klass, sid = sid,
                                    sname = sname, block = _block))
                    else:
                        # Epoche (etc.)
                        try:
                            btag = blocks[block]
                        except KeyError:
                            raise TT_Error(_BLOCK_TAG_UNDEFINED.format(
                                    klass = klass, sid = sid,
                                    sname = sname, block = block))
                        l = self.lessons[btag]  # "main" (real) lesson
                        # Check group is a subset of group in <data>
                        if not groups_are_subset(_groups, l['GROUPS']):
                            raise TT_Error(_GROUP_NOT_SUBSET.format(
                                    klass = klass, sname = sname,
                                    sid = sid, block = block, group = group))
                        # add teachers, rooms to main (*) lesson
                        l['TIDS'].update(teachers)
                        l['ROOMS'].update(rooms)
                        # The block must reference the main (*) lesson
                        block = btag
            if data:
                # The block-field must be the same
                if block != data['block']:
                    raise TT_Error(_TAG_BLOCK_MISMATCH.format(
                            klass = klass, block = block, tag = tag,
                            group1 = repr(p_groups)))
            else:
                self.lessons[tag] = {
                    'CLASSES': {klass},
                    'GROUPS': _groups.copy(),
                    'SID': sid,
                    'TIDS': teachers,
                    'ROOMS': rooms,
                    'durations': durations,
                    'block': block      # or block-tag components
                }
#
    def lessons_teacher_lists(self):
        """Build list of lessons for each teacher.
        """
        tid_lessons = {tid: [] for tid in self.TEACHERS}
        for tag, data in self.lessons.items():
#            sid = idsub(data['SID'])
            sid = data['SID']
#            subject = self.SUBJECTS[sid]
            classes = data['CLASSES']
#            groups = [idsub(g) for g in sorted(data['GROUPS'])]
            groups = sorted(data['GROUPS'])
            tids = data['TIDS']
            rooms = sorted(data['ROOMS'])
            durations = data['durations']
            block = data['block']
            for tid in tids:
                tid_lessons[tid].append((tag, block, classes, sid,
                        groups, durations, rooms))
        return {tid: lessons
                for tid, lessons in tid_lessons.items()
                if lessons}
#
    def teacher_check_list(self):
        """Return a "check-list" of the lessons for each teacher.
        """
        lines = []
        tmap = self.lessons_teacher_lists()
        for tid, lessons in tmap.items():
            class_lessons = {}
            for tag, block, classes, sid, groups, durations, rooms in lessons:
                if len(classes) > 1:
                    klass = '+++'
                else:
                    klass = list(classes)[0]
                plist = []
                bname = ""
                _rooms = f" [{','.join(rooms)}]" if rooms else ""
                if block:
                    if block == '*':
                        continue
                    if block[0] == '-':
                        _block = block.lstrip('- ')
                        if _block:
                            bname = f" ({self.SUBJECTS[_block]})"
                        d = durations[0] if durations else 0
                        plist.append(f"EXTRA x {d}")
                        durations = None
                    else:
                        # Get main (teaching block) lesson entry
                        l = self.lessons[block]
                        bsid = l['SID']
                        bname = f" ({self.SUBJECTS[bsid]})"
                        if durations:
                            d = durations[0]
                            plist.append(f"EPOCHE x {d} {_rooms}")
                            durations = None
                        else:
                            # Get durations from main lesson entry
                            durations = l['durations']
                if durations:
                    dtotal, dmap = get_duration_map(durations)
                    for d in sorted(dmap):
                        n = dmap[d]
                        length = "Einzel" if d == 1 else "Doppel" \
                            if d == 2 else str(dur)
                        plist.append(f" {length} x {n} {_rooms}")
                if plist:
                    try:
                        cl = class_lessons[klass]
                    except KeyError:
                        cl = []
                        class_lessons[klass] = cl
                    for p in plist:
#                        cl.append(f" [{tag}]   {self.SUBJECTS[sid]}{bname}"
#                                f" [{','.join(groups)}]: {p}")
                        cl.append(f"    {self.SUBJECTS[sid]}{bname}"
                                f" [{','.join(groups)}]: {p}")
            if class_lessons:
                lines.append("")
                lines.append("")
                lines.append(f"$$$ {tid} ({self.TEACHERS[tid]})")
                for klass, clist in class_lessons.items():
                    lines.append("")
                    lines.append(f"  Klasse {klass}:")
                    lines += clist
        return "\n".join(lines)

###

class Teachers(dict):
    NO = '0'
    YES = '1'
    def __init__(self, days, periods):
        def sequence(period_string):
            """Generator function for the characters of a string.
            """
            for ch in period_string:
                yield ch
        #+
        super().__init__()
        self.alphatag = {}   # shortened, ASCII version of name, sortable
        fields = TT_CONFIG['TEACHER_FIELDS']
        self.tfield = {f: t or f for f, t, *x in fields}
        teachers = read_DataTable(YEARPATH(CONFIG['TEACHER_DATA']))
        teachers = filter_DataTable(teachers, fieldlist = fields,
                infolist = [], extend = False)['__ROWS__']
        self.blocked_periods = {}
        for tdata in teachers:
            tid, tname, times = tdata['TID'], tdata['NAME'], tdata['TIMES']
            if tid in self:
                raise TT_Error(_DOUBLED_KEY.format(table = _TEACHERS,
                        key = self.tfield['TID'], val = tid))
            if not tid.isalnum():
                raise TT_Error(_TEACHER_INVALID.format(tid = tid))
            self.alphatag[tid] = tdata['TAG']
            self[tid] = tname
            if times:
                day_list = [d.strip() for d in times.split(',')]
                if len(day_list) != len(days):
                    raise TT_Error(_TEACHER_NDAYS.format(name = tname,
                            tid = tid, ndays = len(days)))
                dlist = []
                for dperiods in day_list:
                    pblist = []
                    val = None
                    rd = sequence(dperiods)
                    for p in periods:
                        try:
                            b = next(rd)
                            if b == self.YES:
                                val = False     # not blocked
                            elif b == self.NO:
                                val = True      # blocked
                            else:
                                val = None
                                raise StopIteration
                        except StopIteration:
                            if val == None:
                                raise TT_Error(_TEACHER_DAYS_INVALID.format(
                                        name = tname, tid = tid))
                        pblist.append(val)
                    dlist.append(pblist)
                self.blocked_periods[tid] = dlist

###

class Rooms(dict):
    def __init__(self):
        super().__init__()
        fields = TT_CONFIG['ROOM_FIELDS']
        self.tfield = {f: t or f for f, t, *x in fields}
        rooms = read_DataTable(YEARPATH(TT_CONFIG['ROOM_DATA']))
        rooms = filter_DataTable(rooms, fieldlist = fields,
                infolist = [], extend = False)['__ROWS__']
        for room in rooms:
            rid = room['RID']
            if rid in self:
                raise TT_Error(_DOUBLED_KEY.format(table = _ROOMS,
                        key = self.tfield['RID'], val = rid))
            if not rid.isalnum():
                raise TT_Error(_ROOM_INVALID.format(rid = rid))
            self[rid] = room['NAME']

###

class Subjects(dict):
    def __init__(self):
        super().__init__()
        fields = TT_CONFIG['SUBJECT_FIELDS']
        self.tfield = {f: t or f for f, t, *x in fields}
        sbjs = read_DataTable(YEARPATH(CONFIG['SUBJECT_DATA']))
        sbjs = filter_DataTable(sbjs, fieldlist = fields,
                infolist = [], extend = False)['__ROWS__']
        for sbj in sbjs:
            if not sbj['TT']:
                continue
            sid = sbj['SID']
            if sid in self:
                raise TT_Error(_DOUBLED_KEY.format(table = _SUBJECTS,
                        key = self.tfield['SID'], val = sid))
            self[sid] = sbj['NAME']

###

#*** Group handling ***#
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

def get_groups(group_map, group):
    """Convert a group from the lesson input table to a set of
    timetable-groups.
    """
    try:
        return group_map[group]
    except KeyError:
        pass
    gsplit = group.split('.')
    if len(gsplit) > 1:
        glist = []
        for g in gsplit:
            try:
                glist.append(group_map[g])
            except KeyError:
                break
        else:
            gisct = set.intersection(*glist)
            if gisct:
                return gisct
    raise TT_Error(_UNKNOWN_GROUP.format(klass = klass, group = group))

#

def groups_are_subset(gset, allset):
    if len(allset) == 1 and list(allset)[0].split('-')[1] == WHOLE_CLASS:
        return True
    return gset <= allset

###

class Placements:
    def __init__(self, lessons):
        self.lessons = lessons
        fields = TT_CONFIG['PLACEMENT_FIELDS']
        try:
            place_data = read_DataTable(YEARPATH(TT_CONFIG['PLACEMENT_DATA']))
        except TableError as e:
            print("!!!", str(e))
            return []
        place_data = filter_DataTable(place_data, fields, [])
        self.predef = []
        for row in place_data['__ROWS__']:
            tag = row['TAG']
            places_list = []
            for d_p in row['PLACE'].split(','):
                try:
                    d, p = d_p.strip().split('.')
                except:
                    raise TT_Error(_INVALID_DAY_PERIOD.format(d_p = d_p))
                places_list.append((d, p))
            try:
                ldata = lessons[tag]
            except KeyError:
                print(_UNKNOWN_TAG.format(tag = tag))
                continue
            durations = ldata['durations']
            _, dmap = get_duration_map(durations)
#TODO: Add support for cases with multiple lengths (somehow ...)?
            if len(dmap) > 1:
                print(_PLACE_MULTIPLE_LENGTHS.format(data = repr(ldata)))
            n = len(durations)
            if n != len(places_list):
                if n > len(places_list):
                    print(_PREPLACE_TOO_FEW.format(tag = tag))
                else:
                    print(_PREPLACE_TOO_MANY.format(tag = tag))
            self.predef.append((tag, places_list))

###

def get_duration_map(durations):
    dmap = {}
    dtotal = 0
    for d in durations:
        dtotal += d
        try:
            dmap[d] += 1
        except KeyError:
            dmap[d] = 1
    return (dtotal, dmap)


