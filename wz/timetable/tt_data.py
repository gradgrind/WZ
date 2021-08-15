# -*- coding: utf-8 -*-

"""
TT/tt_data.py - last updated 2021-08-15

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

_TEACHERS = "Lehrkräfte" # error reporting only, refers to the input table
_ROOMS = "Räume"         # error reporting only, refers to the input table
_SUBJECTS = "Fachnamen"  # error reporting only, refers to the input table
_MAX_DURATION = 4        # maximum length of a lesson

### Messages

_CLASS_INVALID = "Klassenbezeichnungen dürfen nur aus Zahlen und" \
        " lateinischen Buchstaben bestehen: {klass} ist ungültig."
_CLASS_TABLE_DAY_DOUBLE = "In der Klassen-Tage-Tabelle: Für Klasse {klass}" \
        " gibt es zwei Einträge für Tag {day}."
_UNKNOWN_GROUP = "Klasse {klass}: unbekannte Gruppe – '{group}'"
_UNKNOWN_SID = "Klasse {klass}: Fach {sid} ({sname}) ist unbekannt"
_GROUP_IN_MULTIPLE_SPLITS = "Klasse {klass}: Gruppe {group} in >1 Teilung"
_INVALID_ENTRY = "Klasse {klass}, Feld_{field}: ungültiger Wert ({val})"
_ROOM_NO_LESSON = "Klasse {klass}, Fach {sname}: Raumangabe aber" \
        " keine Unterrichtsstunden"
_TAGGED_COMPONENT = "Klasse {klass}, Fach {sname} – Komponente von Block" \
        " {block}: keine Stundenkennung ({tag}) ist zulässig"
_TAG_LESSONS_MISMATCH = "Stundenkennung „{tag}“ hat unterschiedliche" \
        " Stundenzahlen in den Stunden mit\n" \
        "     Fach {sid0}, Klasse {klass0} als in\n" \
        "     Fach {sid1}, Klasse {klass1}"
_TAG_GROUP_DOUBLE = "Stundenkennung „{tag}“ hat Überschneidungen bei den" \
        " Gruppen in den Stunden mit\n" \
        "     Fach {sid0}, Klasse {klass0} als in\n" \
        "     Fach {sid1}, Klasse {klass1}"
_TAG_TEACHER_DOUBLE = "Stundenkennung „{tag}“ hat Überschneidungen bei den" \
        " Lehrern in den Stunden mit\n" \
        "     Fach {sid0}, Klasse {klass0} als in\n" \
        "     Fach {sid1}, Klasse {klass1}"
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
_UNKNOWN_ROOM = "Klasse {klass}, Fach {sname}: unbekannter Raum ({rid})"
_DOUBLED_ROOM = "Klasse {klass}, Fach {sname}: Raum ({rid}) zweimal angegeben"
_ADD_ROOM_DOUBLE = "Klasse {klass}, Fach {sname}: Raum ({rid}) wurde dem" \
        " Block {block} schon zugefügt"
_DOUBLED_KEY = "Tabelle der {table}: Feld „{key}“ muss eindeutig sein:" \
        " „{val}“ kommt zweimal vor"
_LESSON_CLASS_MISMATCH = "In der Tabelle der Unterrichtsstunden für" \
        " Klasse {klass} ist die Klasse falsch angegeben:\n  {path}"
_UNKNOWN_TAG = "Tabelle der festen Stunden: unbekannte Stundenkennung „{tag}“"
_INVALID_DAY_PERIOD = "Tabelle der festen Stunden: ungültige" \
        " Tag.Stunde-Angabe für Kennung {tag}: {d_p}"
_REPEATED_DAY_PERIOD = "Tabelle der festen Stunden: wiederholte" \
        " Tag.Stunde-Angabe für Kennung {tag}: {d_p}"
_PREPLACE_TOO_MANY = "Warnung: zu viele feste Stunden definiert für" \
        " Stundenkennung {tag}"
_PREPLACE_TOO_FEW = "Zu wenig feste Stunden definiert für" \
        " Stundenkennung {tag}"
_TABLE_ERROR = "In Klasse {klass}: {e}"
_SUBJECT_NAME_MISMATCH = "Klasse {klass}, Fach {sname} ({sid}):" \
        " Name weicht von dem in der Fachliste ab ({sname0})."
_MULTIPLE_BLOCK = "Klasse {klass}: Block {sname} mehrfach definiert"
_BLOCK_REF_NO_TAG = "Klasse {klass}: Fach {sname} (Epoche = '*') hat" \
        " keine Block-Kennung"
_BLOCK_TAG_UNDEFINED = "Klasse {klass}: Fach {sname} (Epoche = '*') hat" \
        " undefinierter Block-Kennung '{tag}'"
_BLOCK_SID_NOT_BLOCK = "Klasse {klass}, Fach {sname}:" \
        "Block-Fach (Epoche = {sid}) ist kein Block"
_COMPONENT_BAD_LENGTH_TAG = "Klasse {klass}, Fach {sname}:" \
        " Block-Komponente, Kennung{tag} – Länge muss EINE Zahl oder '*' sein"
_COMPONENT_BAD_LENGTH_SID = "Klasse {klass}, Fach {sname}:" \
        " Block-Komponente in {sid}, Länge muss EINE Zahl oder '*' sein"
_NONLESSON_BAD_LENGTH = "Klasse {klass}, EXTRA-Fach {sname}: ungültige" \
        " Länge ({length})"
_PARALLEL_TO_NONLESSON = "Kennung „{tag}“ ist ein EXTRA-Eintrag (Klasse" \
        " {klass}).\n Es gibt parallele Einträge in Klasse(n) {pclasses}"
_BLOCK_TAG_DEFINED = "Klasse {klass}: Kennung {tag} für Block '{sname}'" \
        "schon definiert"
_PLUSTAG_INVALID = "Klasse {klass}, Fach {sname}: Kennung mit '+' ({tag})" \
        " ungültig"

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

###

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
        self.atomics_lists = {}
        self.element_groups = {}
        self.extended_groups = {}

#?
        self.class_divisions = {}
        self.class_groups = {}
        self.groupsets_class = {}
        self.classrooms = {}
        self.lessons = {}
        self.parallel_tags = {} # {tag: [indexed parallel tags]}
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
#TODO: Cater for multiple classless tables?
        _xx = 'XX'
        if self.read_class_data(_xx):
            classes.append(_xx)
        for klass in self.class_days_periods:
            if self.read_class_data(klass):
                classes.append(klass)
        # Post-processing of lesson data (tags, etc.)
        new_parallel = {}
        for tag, subtags in self.parallel_tags.items():
            if len(subtags) < 2:
                continue
            # Check the compatibility of the fields
            g, t, nl  = None, None, None
            for _tag in subtags:
                l = self.lessons[_tag]
                if l['block'] == '--':
                    raise TT_Error(_PARALLEL_TO_NONLESSON.format(
                            tag = tag, klass = l['CLASS'],
                            pclasses = ', '.join([self.lessons[t]['CLASS']
                                for t in subtags])))
                # The actual lessons must match in number and length
                if nl:
                    if l['lengths'] != nl:
                        raise TT_Error(_TAG_LESSONS_MISMATCH.format(
                                tag = tag,
                                sid0 = s, klass0 = k,
                                sid1 = l['SID'], klass1 = l['CLASS']))
                else:
                    nl = l['lengths']
                    g = l['GROUPS']
                    t = l['TIDS']
                    k = l['CLASS']
                    s = l['SID']
                    continue
                # The teachers must be fully distinct
                if t.intersection(l['TIDS']):
                    raise TT_Error(_TAG_TEACHER_DOUBLE.format(
                                tag = tag,
                                sid0 = s, klass0 = k,
                                sid1 = l['SID'], klass1 = l['CLASS']))
                # The groups must be fully distinct
                if g.intersection(l['GROUPS']):
                    raise TT_Error(_TAG_GROUP_DOUBLE.format(
                                tag = tag,
                                sid0 = s, klass0 = k,
                                sid1 = l['SID'], klass1 = l['CLASS']))
                # The rooms are probably too complicated to compare ...
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
        As the class divisions must be given as a set of non-intersecting
        groups, the atomic (undotted) groups may need to be expressed
        (for the timetable) as a combination of dotted groups, e.g. B as
        "B.G,B.R".
        """
        if klass.startswith('XX'):
            return
        ### Add declared class divisions (and their groups).
        divisions = [['*']]
        divs = []
        atomic_groups = [frozenset()]
        all_atoms = set()
        for glist in raw_groups.split('|'):
            dgroups = glist.split()
            divisions.append(dgroups)
            division = [frozenset(item.split('.')) for item in dgroups]
            divs.append(division)
            ag2 = []
            for item in atomic_groups:
                for item2 in division:
                    all_atoms |= item2
                    ag2.append(item | item2)
            atomic_groups = ag2
        self.class_divisions[klass] = divisions
        al = ['.'.join(sorted(ag)) for ag in atomic_groups]
        al.sort()
        self.atomics_lists[klass] = al  # All (dotted) atomic groups
#        print(f'$$$ "Atomic" groups in class {klass}:', al)
        ### Make a mapping of single, undotted groups to sets of dotted
        ### atomic groups.
        gmap = {a: frozenset(['.'.join(sorted(ag))
                        for ag in atomic_groups if a in ag])
                for a in all_atoms}
#        print(f'$$$ "Element" groups in class {klass}:', gmap)
        self.element_groups[klass] = gmap
#
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
#
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
            gmap[k] = frozenset([f'{klass}.{ag}' for ag in v])
        self.class_groups[klass] = gmap
        # And now a reverse map, avoiding duplicate values (use the
        # first occurrence, which is likely to be simpler)
        reversemap = {}
        for k, v in gmap.items():
            if v not in reversemap:
                reversemap[v] = f'{klass}.{k}'
        self.groupsets_class[klass] = reversemap
        # Add "whole class" elements to both mappings
        _whole_class = klass
        fs_whole = frozenset([_whole_class])
        reversemap[fs_whole] = _whole_class
        all_groups = frozenset([f'{klass}.{ag}'
                for ag in self.atomics_lists[klass]])
        if all_groups:
            gmap['*'] = all_groups
            reversemap[all_groups] = _whole_class
        else:
            gmap['*'] = fs_whole
#        print("+++", klass, gmap)
#        print("---", klass, reversemap)
#
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
        gsplit = group.split('.')
        if len(gsplit) > 1:
            group = '.'.join(sorted(gsplit))
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
                        grev[gset] = f'{klass}.{group}'
                    return gset
        raise TT_Error(_UNKNOWN_GROUP.format(klass = klass, group = group))
#
    @staticmethod
    def split_class_group(group):
        """Given a "full" group (with class), return class and group
        separately.
        This method may need to be overridden in the back-end (see
        <make_class_groups>)
        """
        k_g = group.split('.', 1)
        return k_g if len(k_g) == 2 else (group, '')
#
    def read_lessons(self, klass, lesson_lines):
        def read_field(field):
            try:
                return row[field]
            except KeyError:
                raise TT_Error(_FIELD_MISSING.format(klass = klass,
                        field = self.LESSON_FIELDS[field]))
        #+
        def add_block_component():
            if not '--' in teachers:
                block_lesson['TIDS'].update(teachers)
            block_lesson['GROUPS'].update(_groups)
            if rooms:
                if block_lesson['block'] == '--':
                    raise TT_Error(_ROOM_NO_LESSON.format(
                        klass = klass, sname = sname))
                # Add rooms to lesson, but only if they are really new
                block_rooms = block_lesson['ROOMS']
                for rid in rooms:
                    if rid in block_rooms:
                        _block = block_lesson['SID']
                        if tag:
                            _block += f"/{tag}"
                        REPORT("WARN", _ADD_ROOM_DOUBLE.format(
                                klass = klass, sname = sname,
                                block = _block, rid = rid))
                    else:
                        block_rooms.append(rid)
        #+
        lesson_id = 0
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
                durations = []
                dmap = {}
                if _durations != '*':
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
                sname0 = self.SUBJECTS[sid.split('+', 1)[0]]
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
            if tids[0] == '*':
                # No teachers
                if len(tids) > 1:
                    raise TT_Error(_BAD_TIDS.format(klass = klass,
                            sname = sname, tids = _tids))
            else:
                for tid in tids:
                    if tid == '--' or tid in self.TEACHERS:
                        teachers.add(tid)
                    else:
                        raise TT_Error(_UNKNOWN_TEACHER.format(
                                klass = klass, sname = sname, tid = tid))

            ### Rooms
            _ritems = read_field('ROOMS').split()
            # There is one item per room needed. The items can be a room,
            # a list of possible rooms ("r1/r2/ ...") or "?" (unspecified
            # room for the current class).
            # The result is a number of rooms needed and a set of possible
            # rooms. Only '?' may be added multiple times.
            rooms = []
            if _ritems:
                for _ritem in _ritems:
                    if _ritem != '?':
                        _choices = set()
                        for rid in _ritem.split('/'):
                            if rid in self.ROOMS:
                                if rid in _choices:
                                    raise TT_Error(_DOUBLED_ROOM.format(
                                            klass = klass, sname = sname,
                                            rid = rid))
                                else:
                                    _choices.add(rid)
                            else:
                                raise TT_Error(_UNKNOWN_ROOM.format(
                                        klass = klass, sname = sname,
                                        rid = rid))

                        _ritem = '/'.join(sorted(_choices))
                        if _ritem in rooms:
                            raise TT_Error(_DOUBLED_ROOM.format(
                                        klass = klass, sname = sname,
                                        rid = _ritem))
                    rooms.append(_ritem)

            ### Group
            group = read_field('GROUP')
            _groups = self.group_classgroups(klass, group) if group else set()

            ### Lesson-id generation
#
            # If the TAG field is empty the lesson id(s) will
            # be generated automatically.
            # Otherwise the entry should be an ASCII alphanumeric
            # string shared by all parallel classes/groups.
            # As a special case, a tag starting with '*-' is permitted:
            # it is intended for specifying positions for lessons within
            # a class, the '*' will be replaced by the class name.
            # A further special case, to allow parallel blocks, is an
            # alphanumeric suffix prefixed by '+'. This will be stripped
            # off for handling parallel entries.
            # With a "sid" BLOCK field, TAG must be empty.
            block = read_field('BLOCK')
            _tag = row['TAG']
            if _tag:
                # Check tag, substitute class if necessary
                try:
                    if not _tag.isascii():
                        raise TT_Error
                    try:
                        _ts0, _ts1 = _tag.split('+', 1)
                    except ValueError:
                        _ts0 = _tag
                    else:
                        if not _ts1.isalnum():
                            raise TT_Error
                    if _ts0.startswith('*-'):
                        if _ts0[2:].isalnum():
                            tag = _tag.replace('*', klass)
                        else:
                            raise TT_Error
                    elif _ts0.isalnum():
                        tag = _tag
                    else:
                        raise TT_Error
                except TT_Error:
                    raise TT_Error(_INVALID_ENTRY.format(klass = klass,
                            field = self.LESSON_FIELDS['TAG'], val = _tag))
            else:
                tag = None

# BLOCK = empty     Normal lesson, may be tagged. Lessons with the same
#                   tag will be placed in the same slot, if possible. If
#                   a slot is specified (in the "fixed-lessons" table)
#                   this placement is compulsory for all items.
#                   The teachers of all the items must be independent of
#                   each other (no intersections).
#                   The groups of all the items must be independent of
#                   each other (no intersections).
#TODO:
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
#                   However, by adding a suffix ('+' + alphanumeric),
#                   this limitation can be overcome (note that this
#                   feature is only really useful in classless tables).
#                   The suffix will be stripped except in the class-local
#                   <blocks> mapping.
#
#                   With a tag, this block must be the only one using the
#                   tag. To avoid this limitation when specifying
#                   parallel entries, a suffix ('+' + alphanumeric) can
#                   be added. The suffix will be stripped for the
#                   <parallel_tags> key.
#
# BLOCK = '--'      "Non-lesson", not placed in timetable (for "EXTRA"
#                   entries). This is handled like a timetabled block
#                   (see above), except that the LENGTHS field specifies
#                   the "total lessons" (~ payment units) – a single
#                   number. Trying to specify a placement for such an
#                   entry makes no sense, so specifying parallel entries
#                   is also pointless.
#
# BLOCK = '*'       A "component". There must be a tag and this tag must
#                   be that of a block or a non-lesson. This entry does
#                   not appear in the timetable.
#                   The teachers will be added to the block entry (they
#                   may be repeated).
#                   The groups will be added to the block entry, they
#                   need not be independent.
#TODO:
#                   The rooms will be added to the block entry. New rooms
#                   will cause the number of needed rooms to increase
#                   accordingly, but repeated rooms will cause no increase.
#                   The LENGTHS field can be '*', which means the value
#                   will be taken from the block entry. As far as payment
#                   units are concerned this is counted only once per tag
#                   as the use of the tag indicates a single item.
#                   For a block this means effectively that the lesson
#                   is taught throughout the year, but parallel to other
#                   components.
#                   The LENGTHS field can also be a number. This indicates
#                   a time-limited subject-block within the block
#                   ("Epoche"). Each entry counts separately as far as
#                   payment units are concerned.
#
# BLOCK = sid       A block "component". <sid> is the subject-id of a
#                   block (not non-lesson) within the same table. This
#                   <sid> must be unique and previously defined within
#                   the table. It is an alternative for blocks whose
#                   components are all in the same table. There may also
#                   be a tag, normally for placement.

            block_field = None
            if block:
                if block == '*':
                    # A block component, <tag> = block-tag
                    if not tag:
                        raise TT_Error(_BLOCK_REF_NO_TAG.format(
                                klass = klass, sname = sname))
                    try:
                        block_lesson = self.lessons[tag]
                    except KeyError:
                        raise TT_Error(_BLOCK_TAG_UNDEFINED.format(
                                klass = klass, sname = sname, tag = tag))
                    if durations and len(durations) > 1:
                        raise TT_Error(_COMPONENT_BAD_LENGTH_TAG.format(
                                klass = klass, sname = sname, tag = tag))
                    block_field = tag
                    add_block_component()
                    block = None
                elif block == '++':
                    # A "block" entry.
                    block_field = '++'
                elif block == '--':
                    # An EXTRA (non-lesson) entry
                    if len(durations) != 1:
                        TT_Error(_NONLESSON_BAD_LENGTH.format(
                                klass = klass, sname = sname,
                                length = _durations))
                    if rooms:
                        raise TT_Error(_ROOM_NO_LESSON.format(
                                klass = klass, sname = sname))
                    block_field = '--'
                else:
                    # A block component, <block> = block-sid
                    try:
                        block_field = blocks[block]     # block-tag
                    except KeyError:
                        raise TT_Error(_BLOCK_SID_NOT_BLOCK.format(
                                klass = klass, sname = sname, sid = block))
                    # Don't allow a tag in a sid-block-component
                    if tag:
                        raise TT_Error(_TAGGED_COMPONENT.format(
                                klass = klass, sname = sname,
                                tag = tag, block = block))
                    if durations:
                        if len(durations) > 1:
                            raise TT_Error(_COMPONENT_BAD_LENGTH_SID.format(
                                    klass = klass, sname = sname, sid = block))
                    block_lesson = self.lessons[block_field]
                    add_block_component()
                    block = None
                if block:
                    # This must be the only definition of a block for
                    # this subject-id in this table.
                    if sid in blocks:
                        raise TT_Error(_MULTIPLE_BLOCK.format(
                                klass = klass, sname = sname))
                    if tag:
                        # Check that there is no previous use of this tag
                        if tag in self.lessons:
                            raise TT_Error(_BLOCK_TAG_DEFINED.format(
                                klass = klass, tag = tag, sname = sname))
                    else:
                        lesson_id += 1
                        tag = f'{klass}_{lesson_id:02}'
                    blocks[sid] = tag
                    # Add to parallel-tags mapping
                    _tag = tag.split('+')[0]
                    try:
                        ptags = self.parallel_tags[_tag]
                    except KeyError:
                        ptags = []
                        self.parallel_tags[_tag] = ptags
                    ptags.append(tag)
                else:
                    # Block component - new tag
                    lesson_id += 1
                    tag = f'{klass}_{lesson_id:02}'
            else:
                # A "normal" lesson
                lesson_id += 1
                _tag = f'{klass}_{lesson_id:02}'
                block_field = ''
                if tag:
                    if '+' in tag:
                        raise TT_Error(_PLUSTAG_INVALID.format(
                                klass = klass, sname = sname, tag = tag))
                    try:
                        ptags = self.parallel_tags[tag]
                    except KeyError:
                        ptags = []
                        self.parallel_tags[tag] = ptags
                    ptags.append(_tag)
                tag = _tag
            self.lessons[tag] = {
                'CLASS': klass,
                'GROUPS': set(_groups),
                'SID': sid.split('+', 1)[0],
                'TIDS': teachers,
                'ROOMS': rooms,
                'lengths': dmap,
                'block': block_field
            }
#            if klass == 'XX':
#                print("???", tag, self.lessons[tag])
#
    def lessons_teacher_lists(self):
        """Build list of lessons for each teacher.
        """
        tid_lessons = {tid: [] for tid in self.TEACHERS}
        for tag, data in self.lessons.items():
            sid = data['SID']
#            subject = self.SUBJECTS[sid]
            klass = data['CLASS']
            # Combine subgroups
            _groups = data['GROUPS']
            kgroups = {}
            for g in _groups:
                k, group = self.split_class_group(g)
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
            groups = sorted(_groups)
            tids = data['TIDS']
            rooms = data['ROOMS']
            dmap = data['lengths']
            block = data['block']
            for tid in tids:
                if tid != '--':
                    tid_lessons[tid].append((tag, block, klass, sid,
                            groups, dmap, rooms))
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
            for tag, block, klass, sid, groups, dmap, rooms in lessons:
                try:
                    class_list, class_blocks = class_lessons[klass]
                except KeyError:
                    class_list = []
                    class_blocks = []
                    class_lessons[klass] = [class_list, class_blocks]
                n = len(rooms)
                _rooms = f" [{n}: {', '.join(sorted(rooms))}]" if n else ""
                sname = self.SUBJECTS[sid]
                if block == '--':
                    d = list(dmap)[0] if dmap else 0
                    entry = f"    // {sname} [{','.join(groups)}]: EXTRA x {d}"
                    class_blocks.append(entry)
                elif block == '++':
                    ll = ", ".join(lesson_lengths(dmap))
                    entry = f"    // {sname} [{','.join(groups)}]: BLOCK: {ll}{_rooms}"
                    class_blocks.append(entry)
                elif block:
                    # Component
                    blesson = self.lessons[block]
                    bname = self.SUBJECTS[blesson['SID']]
                    if dmap:
                        entry = f"    {sname} [{','.join(groups)}]: EPOCHE ({bname}) x {list(dmap)[0]}"
                    else:
                        entry = f"    {sname} [{','.join(groups)}]: ({bname})"
                    class_list.append(entry)
                else:
                    ll = ", ".join(lesson_lengths(dmap))
                    entry = f"    {sname} [{','.join(groups)}]: {ll}{_rooms}"
                    class_list.append(entry)

            if class_lessons:
                lines.append("")
                lines.append("")
                lines.append(f"$$$ {tid} ({self.TEACHERS[tid]})")
                for klass, clb in class_lessons.items():
                    class_list, class_blocks = clb
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

        self.rooms_for_class = {}       # {class: [available rooms]}

        for room in rooms:
            rid = room['RID']
            if rid in self:
                raise TT_Error(_DOUBLED_KEY.format(table = _ROOMS,
                        key = self.tfield['RID'], val = rid))
            if not rid.isalnum():
                raise TT_Error(_ROOM_INVALID.format(rid = rid))
            self[rid] = room['NAME']
            usage = room['USAGE'].split()
            if usage:
                # The classes which can use this room
                for k in usage:
                    try:
                        self.rooms_for_class[k].append(rid)
                    except KeyError:
                        self.rooms_for_class[k] = [rid]

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

###

class Placements:
    def __init__(self, classes_data):
        lessons = classes_data.lessons
        parallel_tags = classes_data.parallel_tags
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
                    raise TT_Error(_INVALID_DAY_PERIOD.format(tag = tag,
                            d_p = d_p))
#TODO: Check the validity of the places
                dp = (d, p)
                if dp in places_list:
                    raise TT_Error(_REPEATED_DAY_PERIOD.format(tag = tag,
                            d_p = d_p))
                places_list.append(dp)
            try:
                taglist = parallel_tags[tag]
            except KeyError:
                raise TT_Error(_UNKNOWN_TAG.format(tag = tag))
            dmap = lessons[taglist[0]]['lengths']
            n = 0
            for d, i in dmap.items():
                n += i
            if n != len(places_list):
                if n > len(places_list):
                    REPORT("WARN", _PREPLACE_TOO_FEW.format(tag = tag))
                else:
                    raise TT_Error(_PREPLACE_TOO_MANY.format(tag = tag))
            self.predef.append((tag, places_list))
#TODO: Support cases with multiple lengths by doing in order of
# increaasing length

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

