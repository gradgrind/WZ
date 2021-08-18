# -*- coding: utf-8 -*-

"""
TT/tt_data.py - last updated 2021-08-10

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
_SUBJECTS = "Fachnamen"  # error reporting only, refers to the input table
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
_SHARED_ENTRY_NO_TAG = "Klasse {klass}, '!'-Fach {sname}: Kennung fehlt"
_TAG_GROUP_DOUBLE = "Klasse {klass}: Stundenkennung „{tag}“ für Gruppe" \
        " {group} zweimal definiert"
_TAG_SID_MISMATCH = "Klasse {klass}: Fach {sid} mit Stundenkennung „{tag}“" \
        " ist anders als in Gruppen {group1}"
_ROOM_NO_LESSON = "Klasse {klass}, Fach {sname}: Raumangabe aber" \
        " keine Unterrichtsstunden"
_NOT_ENOUGH_ROOMS = "Klasse {klass}, Fach {sname}: zu wenig Räume zur Wahl"
_TAG_IN_BLOCK = "Klasse {klass}: Fach {sid} mit Stundenkennung „{tag}“" \
        " ist in einem Block ({block}), was nicht zulässig ist"
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
_BAD_TIDS = "Klasse {klass}: ungültige Lehrkräfte ({tids}) für {sname}"
_UNKNOWN_TEACHER = "Klasse {klass}: unbekannte Lehrkraft ({tid}) für {sname}"
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
_MULTIPLE_BLOCK = "Klasse {klass}: Block {sname} mehrfach definiert"
BLOCK_DEF_WITH_BLOCK = "Klasse {klass}: Block {sname} definiert mit" \
        "\"Epoche\" {block}"
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
        # Start with classless data
        _xx = 'XX'
        if self.read_class_data(_xx):
            classes.append(_xx)
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
        def add_rooms(ldata):
            if rooms:
                if block == '--':
                    raise TT_Error(_ROOM_NO_LESSON.format(
                        klass = klass, sname = sname))
                # Add rooms to lesson, but only if they are
                # really new
                try:
                    n, _rooms = ldata['ROOMS']
                except ValueError:
                    ldata['ROOMS'] = rooms
                else:
                    l = len(_rooms)
                    _rooms.update(rooms[1])
                    l1 = len(_rooms) - l
                    n1 = rooms[0]
                    if l1 >= n1:
                        n += n1
                    else:
                        n += l1
                    ldata['ROOMS'][0] = n
        #+
        lesson_id = 0
        group_map = self.class_groups[klass]
        blocks = {}      # collect {block-sid: block-tag}
        for row in lesson_lines:
            # Make a list of durations.
            # Then for each entry, generate a lesson or a course within
            # a teaching block.
            _durations = read_field('LENGTHS')
            if not _durations:
                # Line not relevant for timetabling
                continue
            try:
                dmap = {}
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
                        try:
                            dmap[i] += 1
                        except KeyError:
                            dmap[i] = 1
            except ValueError:
                raise TT_Error(_INVALID_ENTRY.format(klass = klass,
                        field = self.LESSON_FIELDS['LENGTHS'],
                        val = _durations))

            ### Subject
            sid = read_field('SID')
            sname = read_field('SNAME')
            try:
                sname0 = self.SUBJECTS[sid]
            except KeyError:
                raise TT_Error(_UNKNOWN_SID.format(klass = klass,
                        sname = sname, sid = sid))
            if sname != sname0:
                print(_SUBJECT_NAME_MISMATCH.format(klass = klass,
                        sname0 = sname0, sname = sname, sid = sid))

            ### Teachers
            _tids = read_field('TIDS')
            if not _tids:
                # Line not relevant for timetabling
                continue
            tids = _tids.split()
            teachers = set()
            suppress_tids = False
            # Check for "special" (block definition) lines. Special
            # lines may not have a subject-id in the BLOCK field (see
            # block handling, below).
            if tids[0] == '*':
                if len(tids) > 1:
                    raise TT_Error(_BAD_TIDS.format(klass = klass,
                            sname = sname, tids = _tids))
            else:
                if tids[0] == '--':
                    # Teacher-ids will not be included in lessons.
                    suppress_tids = True
                    tids = tids[1:]
                for tid in tids:
                    if tid in self.TEACHERS:
                        teachers.add(tid)
                    else:
                        raise TT_Error(_UNKNOWN_TEACHER.format(
                                klass = klass, sname = sname, tid = tid))

            ### Group
            group = read_field('GROUP') # check later

            ### Rooms
            _ritems = read_field('ROOMS').split()
            # There is one item per room needed. The items can be a room,
            # a list of possible rooms ("r1/r2/ ...") or "?" (unspecified
            # room).
            # The result is a number of rooms needed and a set of possible
            # rooms. Only '?' may be added multiple times.
            n = 0
            _rooms = set()
            if _ritems:
                for _ritem in _ritems:
                    if _ritem == '?':
                        n += 1
                        _rooms.add('?')
                    else:
                        _choices = []
                        for rid in _ritem.split('/'):
                            if rid in self.ROOMS:
                                if rid not in _rooms:
                                    _choices.append(rid)
                            else:
                                raise TT_Error(_UNKNOWN_ROOM.format(
                                        klass = klass, rid = rid))
                        if _choices:
                            n += 1
                            _rooms.update(_choices)
            rooms = [n, _rooms]

# The BLOCK field can contain:
#
#   nothing:    This is the "normal" case.
#
#   sid:        Specifies a course within the teaching block with
#               subject-id sid (which must be previously defined in the
#               lesson table for the class).
#               The TIDS field must contain one or more teachers.
#               The LENGTHS field must contain a single number,
#               representing the number of course blocks / payment units.
#               The LENGTHS field can also contain '*', meaning "take
#               the number from the main ('*') entry" – for permanently
#               running courses within a teaching block.
#
#   '!':        This signals a lesson shared with another class. There
#               must be an entry in the TAG field to identify the entries
#               which are to be combined. The other lines thus referenced
#               must have fully independent groups, the same subject
#               and the same number and length of lessons.
#
#   '--':       This specifies a "course" which will not itself appear
#               directly in the timetable, but specifies a number of
#               "payment units". Here there is no point in adding rooms
#               because there are no timetabled lessons.
#               The LENGTHS field must contain a single number,
#               representing the payment units (number of blocks).
#               If there is a TAG entry, this line will behave otherwise
#               like with '!' (multiple such lines are effectively just
#               like a single line).

            ### Lesson-id generation
#
            # If the TAG field is empty the lesson id(s) will
            # be generated automatically.
            # Otherwise the entry should be an ASCII alphanumeric
            # string shared by all parallel classes/groups.
            # As a special case, a tag starting with '*-' is permitted:
            # it is intended for specifying positions for lessons within
            # a class, the '*' will be replaced by the class name.
            # With a "sid" BLOCK field, TAG must be empty.
            block = read_field('BLOCK')
            tag = None
            data = None
            _groups = get_groups(group_map, group)
            _tag = row['TAG']
#TODO: Various types:
# - same lesson: ...
# - same time, if possible ( ... )
# - the tag may also be used to fix time

            if _tag:
                # Check tag, substitute class if necessary
                if _tag.isascii():
                    if _tag.startswith('*-'):
                        if _tag[2:].isalnum():
                            tag = klass + _tag[1:]
                    elif _tag.isalnum():
                        tag = _tag
                if not tag:
                    raise TT_Error(_INVALID_ENTRY.format(klass = klass,
                            field = self.LESSON_FIELDS['TAG'], val = _tag))
                if block and block not in ('!', '--'):
                    # Don't allow both sid-block and tag
                    raise TT_Error(_TAG_IN_BLOCK.format(
                                klass = klass, sid = sid, tag = tag,
                                block = block))
                data = self.lessons.get(tag)
                if data:
                    # Check compatibility with previous tagged entry
                    p_groups = data['GROUPS']
                    # The actual lessons must match in number and length
                    if data['lengths'] != dmap:
                        raise TT_Error(_TAG_LESSONS_MISMATCH.format(
                                klass = klass, tag = tag,
                                group1 = repr(p_groups)))
                    # If groups are parallel, they must be fully distinct
                    # groups!
                    if _groups.intersection(p_groups):
                        raise TT_Error(_TAG_GROUP_DOUBLE.format(
                                klass = klass, tag = tag,
                                group = repr(_groups)))

                    if block in ('!', '--'):
                        # The subject must be the same for a shared lesson
                        if sid != data['SID']:
                            raise TT_Error(_TAG_SID_MISMATCH.format(
                                    klass = klass, sid = sid, tag = tag,
                                    group1 = repr(p_groups)))
                        p_groups.update(_groups)
                        data['CLASSES'].add(klass)
                        # Add teachers
                        data['TIDS'].update(teachers)
                        # Add rooms to lesson
                        if rooms[0]:
                            add_rooms(data)
            else:
                if block == '!':
                    # Shared lesson without tag
                    raise TT_Error(_SHARED_ENTRY_NO_TAG.format(
                            klass = klass, sname = sname))
#                if block == '--':
# no lesson? But then it wouldn't appear in the teachers list
                lesson_id += 1
                tag = f'{klass}_{lesson_id:02}'


#TODO
            if teachers:
#                if durations:
#                    if len(durations) != 1:
#                        raise TT_Error(_BLOCK_NUMBER.format(
#                                klass = klass, sid = sid,
#                                sname = sname, block = block))
#                    n = durations[0]
#                else:
#                    n = None
                if block == '--':
                    # "EXTRA" item
#?
                    pass
                elif block and block != '!':
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
                    if '--' not in teachers:
                        l['TIDS'].update(teachers)
                    if rooms[0]:
                        add_rooms(l)
                    # The block must reference the main (*) lesson
                    block = btag





            else:
                # This specifies a block-lesson for the timetable
                if sid in blocks:
                    raise TT_Error(_MULTIPLE_BLOCK.format(
                            klass = klass, sname = sname))
                blocks[sid] = tag
                if block == '!':
#?
                    pass
                elif block == '--':
#?
                    pass
                elif block:
                    raise TT_Error(BLOCK_DEF_WITH_BLOCK.format(
                            klass = klass, sname = sname, block = block))


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
                    'lengths': dmap,
                    'block': block      # or block-tag components
                }
                if klass == 'XX':
                    print("???", self.lessons[tag])
#
    def lessons_teacher_lists(self):
        """Build list of lessons for each teacher.
        """
        tid_lessons = {tid: [] for tid in self.TEACHERS}
        for tag, data in self.lessons.items():
#            sid = idsub(data['SID'])
            sid = data['SID']
#            subject = self.SUBJECTS[sid]
            classes = sorted(data['CLASSES'])
#            groups = [idsub(g) for g in sorted(data['GROUPS'])]
            groups = sorted(data['GROUPS'])
            tids = data['TIDS']
            rooms = data['ROOMS']
            dmap = data['lengths']
            block = data['block']
            for tid in tids:
                tid_lessons[tid].append((tag, block, classes, sid,
                        groups, dmap, rooms))
        return {tid: lessons
                for tid, lessons in tid_lessons.items()
                if lessons}
#
    def teacher_check_list2(self):
        """Return a "check-list" of the lessons for each teacher.
        """
        lines = []
        tmap = self.lessons_teacher_lists()
        for tid, lessons in tmap.items():
            class_lessons = {}
            for tag, block, classes, sid, groups, dmap, rooms in lessons:
                klass = ','.join(classes)
                try:
                    class_list, class_blocks = class_lessons[klass]
                except KeyError:
                    class_list = []
                    class_blocks = {}
                    class_lessons[klass] = [class_list, class_blocks]
                entry = ""
                bname = ""
                n, _rooms = rooms
                _rooms = f" [{n}: {','.join(sorted(_rooms))}]" if n else ""
                sname = self.SUBJECTS[sid]
                if block and block != '!':
                    if block == '--':
                        _block = block.lstrip('- ')
                        d = list(dmap)[0] if dmap else 0
                        entry = f"EXTRA x {d}"
                        dmap = None
                    else:
                        # Get main (teaching block) lesson entry
                        l = self.lessons[block]
                        bsid = l['SID']
                        bname = self.SUBJECTS[bsid]
                        try:
                            bdata = class_blocks[bname]
                        except KeyError:
                            # Get durations from main lesson entry
                            dmapl = l['lengths']
                            if dmap:
                                # "Epoche"
                                dtotal = 0
                                for d, n in dmapl.items():
                                    dtotal += d*n
                                bdata = [
                                    f"\"{bname}\": ({dtotal} "
                                            f" Wochenstunden){_rooms}",
                                    [f"{sname}: EPOCHE x {list(dmap)[0]}"]
                                ]
                            else:
                                # Parallel lessons
                                ll = ", ".join(lesson_lengths(dmapl))
                                bdata = [
                                    f"\"{bname}\": {ll}{_rooms}",
                                    [sname]
                                ]
                            class_blocks[bname] = bdata
                            continue
                        if dmap:
                            # "Epoche"
                            bdata[1].append(
                                    f"{sname}: EPOCHE x {list(dmap)[0]}")
                        else:
                            # Parallel lessons
                            bdata[1].append(sname)
                        continue
                if dmap:
                    ll = ", ".join(lesson_lengths(dmap))
                    entry = f"{ll}{_rooms}"
                if entry:
                    class_list.append(f"    {sname}{bname}"
                                f" [{','.join(groups)}]: {entry}")
            if class_lessons:
                lines.append("")
                lines.append("")
                lines.append(f"$$$ {tid} ({self.TEACHERS[tid]})")
                for klass, clist_bmap in class_lessons.items():
                    clines = []
                    clist, bmap = clist_bmap
                    clines += clist
                    for bname, blist in bmap.items():
                        clines.append(f"    {blist[0]}")
                        for bx in blist[1]:
                            clines.append(f"      - {bx}")
                    if clines:
                        lines.append("")
                        lines.append(f"  Klasse {klass}:")
                        lines += clines
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
            dmap = ldata['lengths']
#TODO: Support cases with multiple lengths by doing in order of
# increaasing length
            if len(dmap) > 1:
                print(_PLACE_MULTIPLE_LENGTHS.format(data = repr(ldata)))
            n = 0
            for d, i in dmap.items():
                n += i
            if n != len(places_list):
                if n > len(places_list):
                    print(_PREPLACE_TOO_FEW.format(tag = tag))
                else:
                    print(_PREPLACE_TOO_MANY.format(tag = tag))
            self.predef.append((tag, places_list))

###

def lesson_lengths(duration_map):
    ll = []
    for d in sorted(duration_map):
        n = duration_map[d]
        length = "Einzel" if d == 1 \
            else "Doppel" if d == 2 \
            else f"[{d}]"
        ll.append(f" {length} x {n}")
    return ll
