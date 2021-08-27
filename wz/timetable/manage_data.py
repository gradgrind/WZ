# -*- coding: utf-8 -*-

"""
TT/manage_data.py - last updated 2021-08-26

Coordinate and process the timetable data

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

#TODO ...
__TEST = False

FET_VERSION = '6.1.1'

WEIGHTS = [None, '50', '67', '80', '88', '93', '95', '97', '98', '99', '100']

LUNCH_BREAK = ('mp', "Mittagspause")
VIRTUAL_ROOM = ('dummy', "Zusatzraum")

### Messages
_LESSON_NO_GROUP = "Klasse {klass}, Fach {sid}: „Unterricht“ ohne Gruppe"
_LESSON_NO_TEACHER = "Klasse {klass}, Fach {sid}: „Unterricht“ ohne" \
        " Lehrer.\nDieser Unterricht wird NICHT im Stundenplan erscheinen."
_LAST_LESSON_TAG_INVALID = "Bedingung „LAST_LESSON“: Die Kennung {tag}" \
        " wird mehr als einmal benutzt"
_SUBJECT_PAIR_INVALID = "Ungültiges Fach-Paar ({item}) in:\n  {path}"
_DODGY_GAPS_PER_WEEK = "Bedingung GAPS für Klasse {klass} ist" \
        " wahrscheinlich fehlerhaft: {gaps}"
_BAD_GAPS_PER_WEEK = "Bedingung GAPS für Klasse {klass} ist" \
        " fehlerhaft: {gaps}"
_TEACHER_DAYS_WRONG = "Lehrer-Tabelle: {tname} hat die falsche Anzahl" \
        " an Tagesangaben"
_TEACHER_PERIODS_WRONG = "Lehrer-Tabelle: {tname} hat die falsche Anzahl" \
        " an Stunden für {day}"
_NO_LESSON_WITH_TAG = "Tabelle der festen Stunden: Kennung {tag} hat keine" \
        " entsprechenden Unterrichtsstunden"
_TAG_TOO_MANY_TIMES = "Tabelle der festen Stunden: Kennung {tag} gibt" \
        " mehr Zeiten an, als es dafür Unterrichtsstunden gibt"


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

# IMPORTANT: Note that some uses of Python dicts here may assume ordered
# entries. If the implementation is altered, this should be taken into
# account. One place is the definition of pre-placed lessons
# for a subject. If there is more than one entry for this subject and
# varying durations, the placement could be affected.

### +++++

from itertools import combinations

import xmltodict

from timetable.basic_data import Classes, Days, Periods, Placements, \
        Rooms, Subjects, Teachers, TT_Error, TT_CONFIG

### -----

# class Days: use the keys for the short forms

# class Periods: use the keys for the short forms

###

class Classes_gui(Classes):
#?
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self.atomic_groups = {}
#
    def class_data(self, klass):
        """Group information for the class.
        """
        print(f"\nCLASS GROUPS in {klass} ->", self.class_groups[klass])
        # This contains as keys: elemental groups, the whole class ('*')
        # and also any dotted groups which are actually used in the class
        # lessons table (the latter being added by the method
        # <Classes.group_classgroups>.

        print(f"\nATOMIC GROUPS in {klass} ->", self.atomics_lists[klass])
        return {}
#
    def constraint_blocked_periods(self):
        """Constraint: students set not available ...
        """
        print("\nCLASS NOT AVAILABLE:")
        for klass in self.class_days_periods:
            print(f"   {klass}:", self.class_days_periods[klass])
#TODO: Suggestion: make separate table for each class and include
# info for lunch break (e.g. 'M' in possible slots).

#
    def get_lessons(self):
        """Build list of lessons for fet-timetables.
        """



        space_constraints = {}  # for room placements
        time_constraints = {}   # for "virtual" lessons (multiple rooms)
        self.lesson_list = []
        self.tag_lids = {}      # {tag: [lesson-id, ...]}
        self.xlids = []         # [[lid, xlid1, xlid2, ... ], ... ]
        self.multirooms = []
        # For constraints concerning relative placement of individual
        # lessons in the various subjects, collect the tags and their
        # pupil groups for each subject:

        lid = 0
        for tag, data in self.lessons.items():
            block = data['block']
            if block and block != '++':
                continue    # not a timetabled lesson
            sid = data['SID']
            klass = data['CLASS']
            groups = data['GROUPS']
            if not groups:
                REPORT("WARN", _LESSON_NO_GROUP.format(klass = klass,
                        sid = sid))

            # Here I can get the involved classes – not any more ...
            #print("+++", sorted(_classes_groups))
# A disadvantage of a class-based approach to handling constraints
# concerning relative placements of lessons is that a single lesson
# can appear in two (or more) classes, potentially making the constraint
# too strong, through repetition. It might be simplest and safest to
# disallow relative constraints of this sort. Using the class of origin
# (here <klass>) might make it workable, though not perfect.

            tids = sorted(data['TIDS'])
            if (not tids) and (not data['REALTIDS']):
                REPORT("WARN", _LESSON_NO_TEACHER.format(klass = klass,
                        sid = sid))
                continue

            roomlists = data['ROOMLISTS']
#?
            # Keep a list of subjects with multiple rooms
            if len(roomlists) > 1:
                self.multirooms.append({
                        'CLASS': klass,
                        'GROUPS': groups,
                        'SID': sid,
                        'NUMBER': len(roomlists)
                    }
                )
                print("???", self.multirooms[-1])


#TODO: How to manage the lessons? Roughly as for fet?
# But what about multiple rooms?

# Or just extend the self.lessons list?
# e.g. for multiple lessons add new entries with constraint (day between).
# For fixed lessons, the constraint is actually not necessary, but
# consider manual adjustment including "unfixing" – the constraints
# would need regenerating. It might be easier to make these constraints
# independent of fixing?


#            self.lessons[tag] = {
#                'CLASS': klass,
#                'GROUPS': set(_groups),
#                'SID': sid.split('+', 1)[0],
#                'TIDS': teachers,       # for timetable-clash checking,
#                # tid '--' makes it empty even if there are teachers
#                'REALTIDS': real_teachers, # all associated teachers
#                'ROOMS': rooms,
#                'lengths': dmap,
#                'block': block_field
#            }


#TODO
            # Generate the lesson items
            dmap = data['lengths']
            if dmap:
                for d in sorted(dmap):
                    _tag_lids = []
                    __tag = f'{tag}__{d}' if len(dmap) > 1 else tag
                    for i in range(dmap[d]):
                        lid += 1
                        _lid = str(lid)
                        _tag_lids.append(_lid)
                        dstr = str(d)
                        lesson = lesson0.copy()
                        lesson.update({
                            'Duration': dstr,
                            'Total_Duration': dstr,
                            'Id': _lid,
                            'Comments': __tag
                        })
                        self.lesson_list.append(lesson)
                        if room_constraints:
                            _pc, _ac = room_constraints[0]
                            # Add the space constraints
                            if _pc:
                                add_room_constraint(_pc[0], _pc[1], _lid)
                            add_room_constraint(_ac[0], _ac[1], _lid)
                            if len(room_constraints) > 1:
                                # Multiple room: generate "virtual" lessons
                                _rids = [_lid]
                                for _pc, _ac in room_constraints[1:]:
                                    lid += 1
                                    _xlid = str(lid)
                                    _rids.append(_xlid)
                                    lesson = {
#                                        'Teacher': {},
                                        'Subject': VIRTUAL_ROOM[0],
#                                        'Students': {},
                                        'Duration': dstr,
                                        'Total_Duration': dstr,
                                        'Id': _xlid,
                                        'Activity_Group_Id': '0',
                                        'Active': 'true',
                                        'Comments': f'++{_lid}'
                                    }
                                    self.lesson_list.append(lesson)
                                    # Add the space constraints
                                    if _pc:
                                        add_room_constraint(_pc[0], _pc[1],
                                                _xlid)
                                    add_room_constraint(_ac[0], _ac[1],
                                            _xlid)
                                # Note the list of coupled lids
                                self.xlids.append(_rids)
                                # Add start-time constraint
                                time_constraint = {
                                    'Weight_Percentage': '100',
                                    'Number_of_Activities': str(len(_rids)),
                                    'Activity_Id': _rids,
                                    'Active': 'true',
                                    'Comments': None
                                }
                                tc_tag = 'ConstraintActivitiesSameStartingTime'
                                try:
                                    t_c = time_constraints[tc_tag]
                                except KeyError:
                                    t_c = []
                                    time_constraints[tc_tag] = t_c
                                t_c.append(time_constraint)
                    self.tag_lids[__tag] = _tag_lids
                    try:
                        self.sid_groups[sid].append((groups, __tag))
                    except KeyError:
                        self.sid_groups[sid] = [(groups, __tag)]
        self.last_lesson_id = lid
#TODO--
#        print("???", self.tag_lids)
        self.time_constraints = time_constraints
        self.space_constraints = space_constraints
#
    def lunch_breaks(self, lessons):
#TODO: This is very much tied to a concrete situation. Think of a more
# general approach.
# I need a special lesson on the long days AND a constraint to limit it
# to periods 3,4 or 5.
# There needs to be a lunch-break lesson for every sub-group of the class!
        constraints = []
        for klass, weekdata in self.class_days_periods.items():
            atomic_groups = self.class_groups[klass]['*']
            groupsets = self.groupsets_class[klass]
            #print(f"??? {klass}", atomic_groups)
            for day, daydata in weekdata.items():
                if daydata['5']:
#                    print(f"??? {klass}, {day}")
                    # Add lesson lunch-break
                    for g in atomic_groups:
                        self.last_lesson_id += 1
                        lid = str(self.last_lesson_id)
                        lesson = {
#                            'Teacher': {},
                            'Subject': LUNCH_BREAK[0],
                            'Students': groupsets.get(frozenset([g])) or g,
                            'Duration': '1',
                            'Total_Duration': '1',
                            'Id': lid,
                            'Activity_Group_Id': '0',
                            'Active': 'true',
                            'Comments': None
                        }
                        lessons.append(lesson)
                        # Add constraint
                        constraints.append(
                            {   'Weight_Percentage': '100',
                                'Activity_Id': lid,
                                'Number_of_Preferred_Starting_Times': '3',
                                'Preferred_Starting_Time': [
                                    {'Preferred_Starting_Day': day,
                                        'Preferred_Starting_Hour': '3'},
                                    {'Preferred_Starting_Day': day,
                                        'Preferred_Starting_Hour': '4'},
                                    {'Preferred_Starting_Day': day,
                                        'Preferred_Starting_Hour': '5'},
                                ],
                                'Active': 'true',
                                'Comments': None
                            }
                        )
        if constraints:
            try:
                self.time_constraints[
                        'ConstraintActivityPreferredStartingTimes'] \
                    += constraints
            except KeyError:
                self.time_constraints[
                        'ConstraintActivityPreferredStartingTimes'] \
                    = constraints
#
    def __subject_atomic_group_tags(self, tglist):
        """Given a list of (atomic-group-set, tag) pairs, collect the
        tags which have common groups {tag: {tag, ... }]. Tags which
        have no other tags sharing groups will also be included (as
        tag1: {tag1}) if the tag represents more than one lesson.
        The result can, of course, be empty.
        """
        tgmap = {}
        for agroups, tag in tglist:
            collect = {t for gset, t in tglist if agroups & gset}
            # This includes single tags (because items are also
            # compared with themselves).
            if len(collect) > 1 or len(self.tag_lids[tag]) > 1:
                # Also include tags with multiple lessons!
                tgmap[tag] = collect
        return tgmap
#
    def __tag_sets_common_groups(self, tgmap):
        """Given a mapping {tag: {tag, ... } as returned by
        <__subject_atomic_group_tags>, return a list of tags-sets
        (with more than one element) with group intersections.
        Subsets are eliminated.
        """
        kcombis = set()
        for tag, partners in tgmap.items():
            for l in range(len(partners), 0, -1):
                for c in combinations(partners, l):
                    if tag in c:
                        kcombis.add(frozenset(c))
        xcombis = []
        for ycombi in kcombis:
            # Check with all components
#                print("&&&", combi)
            for p in ycombi:
#                    print("%%%", p)
                plist = tgmap[p]
                for q in ycombi:
                    if q not in plist:
                        break
                else:
                    # ok
                    continue
                break
            else:
                xcombis.append(ycombi)
        # Eliminate subsets
        combis = []
        for c in xcombis:
            for c2 in xcombis:
                if c < c2:
                    break
            else:
                combis.append(c)
        return combis
#
    def __pairs_common_groups(self, cmap):
        """For each item (sid1+sid2) get all tag sets with common groups.
        The result is a mapping. For each item, there is a further mapping,
        {class: [(tag_sid1, {tag_sid2, ... }), ... ]}.
        """
        # First get all subject keys, so that the tag sets need only be
        # generated once
        pairs = {}
        for klass, item_map in cmap.items():
            for item in item_map:
                pairs[item] = None
        for item in pairs:
            try:
                sid1, sid2 = item.split('+')
            except ValueError:
                raise TT_Error(_SUBJECT_PAIR_INVALID.format(item = item,
                        path = YEARPATH(TT_CONFIG['CONSTRAINTS'])))
            tglist1 = self.sid_groups[sid1]
            tglist2 = self.sid_groups[sid2]
            # <tglistX> is a list of ({set of "atomic" groups}, tag)
            # pairs for each tag.
            # Collect the tags which share groups (for this subject)
            _tgmap = self.__subject_atomic_group_tags(tglist1 + tglist2)
            tgmap = {k: v for k, v in _tgmap.items() if len(v) > 1}
            if not tgmap:
                continue
            # Get sets of tags with (group) intersections
            cc = self.__tag_sets_common_groups(tgmap)
            # Remove tag sets containing only fixed lessons (this
            # can't cope with tags whose lessons are only partially
            # placed – they are handled as tags with full placed
            # lessons).
            tagsets = set()
            for tags in cc:
                for tag in tags:
                    if tag not in self.placements:
                        tagsets.add(tags)
                        break
            # For every tag-set containing sid1, collect all tags
            # with joint groups and sid2
            tagmap = {}
            for tset in tagsets:
                _st = {}
                for tag in tset:
                    sid = self.tag_get_sid(tag)
                    try:
                        _st[sid].append(tag)
                    except KeyError:
                        _st[sid] = [tag]
                if len(_st) > 1:
                    for tag in _st[sid1]:
                        for tag2 in _st[sid2]:
                            try:
                                tagmap[tag].add(tag2)
                            except KeyError:
                                tagmap[tag] = {tag2}
            # Divide up the sets into classes
            class_map = {}
            for tag, tset in tagmap.items():
                classes = {self.split_class_group(g)[0]
                        for g in self.tag_get_groups(tag)}
                for klass in classes:
                    tset1 = set()
                    for t in tset:
                        for g in self.tag_get_groups(t):
                            if self.split_class_group(g)[0] == klass:
                                tset1.add(t)
                    if tset1:
                        tag_tset = (tag, tset1)
                        try:
                            class_map[klass].append(tag_tset)
                        except KeyError:
                            class_map[klass] = [tag_tset]
            pairs[item] = class_map
#            for k in sorted(class_map):
#                for tset in class_map[k]:
#                    print("+++", k, tset)
        return pairs
#
#TODO: This is rather a hammer-approach which could perhaps be improved
# by collecting data class-wise?
    def constraint_day_separation(self, placements):
        """Add constraints to ensure that multiple lessons in any subject
        are not placed on the same day.
        <placements> supplies the tags, as list of (tag, positions) pairs,
        which have fixed positions, and so do not need this constraint.
        """
        self.placements = {k for k, v in placements}
        sid_group_sets = {}
        constraints = []
        for sid, tglist in self.sid_groups.items():
            if sid == VIRTUAL_ROOM[0]:
                continue    # ignore dummy subject
            # <tglist> is a list of ({set of "atomic" groups}, tag) pairs
            # for each tag.
            # Collect the tags which share groups (for this subject)
            tgmap = self.__subject_atomic_group_tags(tglist)
            if not tgmap:
                continue

            # Get sets of tags with (group) intersections
            cc = self.__tag_sets_common_groups(tgmap)

            # Remove tag sets containing only fixed lessons (this
            # can't cope with tags whose lessons are only partially
            # placed – they are handled as tags with full placed
            # lessons).
            tagsets = set()
            for tags in cc:
                for tag in tags:
                    if tag not in self.placements:
                        tagsets.add(tags)
                        break
            if tagsets:
                sid_group_sets[sid] = tagsets
                # Now add the constraints
                for tagset in tagsets:
                    ids = []
                    for tag in tagset:
                        ids += self.tag_lids[tag]
                    constraints.append(
                        {   'Weight_Percentage': '100',
                            'Consecutive_If_Same_Day': 'true',
                            'Number_of_Activities': str(len(ids)),
                            'Activity_Id': ids,
                            'MinDays': '1',
                            'Active': 'true',
                            'Comments': None
                        }
                    )
        if constraints:
            self.time_constraints['ConstraintMinDaysBetweenActivities'] \
                    = constraints
        return sid_group_sets
#
    def constraint_min_lessons_per_day(self, default, custom_table):
        constraints = []
        for klass in self.class_days_periods:
            try:
                n = custom_table[klass]
            except KeyError:
                n = default
            if n:
                constraints.append(
                    {   'Weight_Percentage': '100',
                        'Minimum_Hours_Daily': str(n),
                        'Students': klass,
                        'Allow_Empty_Days': 'false',
                        'Active': 'true',
                        'Comments': None
                    }
                )
        if constraints:
            self.time_constraints['ConstraintStudentsSetMinHoursDaily'] \
                    = constraints

    ############### FURTHER CONSTRAINTS ###############

    def class_constraint_data(self, data):
        """Extract info for the various classes, jandling default values.
        """
        cmap = {}
        try:
            default = data.pop('*')     # WARNING: The entry is now gone!
        except KeyError:
            pass
        else:
            for klass in _classes.class_days_periods:
                cmap[klass] = default.copy()
        for klass, v in data.items():
            try:
                cmap[klass].update(v)
            except KeyError:
                cmap[klass] = v
        return cmap
#
    def GAPS(self, data):
        """Maximum gaps per week for each specified class.
        """
        constraints = []
        cmap = {}
        try:
            default = data.pop('*')     # WARNING: The entry is now gone!
        except KeyError:
            pass
        else:
            for klass in _classes.class_days_periods:
                cmap[klass] = default
        for klass, v in data.items():
            cmap[klass] = v
        for klass, gpw in cmap.items():
            try:
                _gpw = int(gpw)
                if _gpw < 0:
                    raise ValueError
                if _gpw > 5:
                    REPORT("WARN", _DODGY_GAPS_PER_WEEK.format(
                            klass = klass, gaps = gpw))
                    continue
            except ValueError:
                raise TT_Error(_BAD_GAPS_PER_WEEK.format(
                            klass = klass, gaps = gpw))
            constraints.append(
                {   'Weight_Percentage': '100',
                    'Max_Gaps': _gpw,
                    'Students': klass,
                    'Active': 'true',
                    'Comments': None
                }
            )
        if constraints:
            self.time_constraints['ConstraintStudentsSetMaxGapsPerWeek'] \
                    = constraints
#
    def LAST_LESSON(self, data):
        """The lessons should end the day for the respective classes.
        """
        constraints = []
        for tag in data:
            _tags = self.parallel_tags[tag]
            if len(_tags) > 1:
                REPORT("WARN", _LAST_LESSON_TAG_INVALID.format(tag = tag))
            for lid in self.tag_lids[_tags[0]]:
                constraints.append(
                    {   'Weight_Percentage': '100',
                        'Activity_Id': lid,
                        'Active': 'true',
                        'Comments': None
                    }
                )
        if constraints:
            self.time_constraints['ConstraintActivityEndsStudentsDay'] \
                    = constraints
#
    def tag_get_sid(self, tag):
        return self.lessons[tag.split('__', 1)[0]]['SID']
#
    def tag_get_groups(self, tag):
        return self.lessons[tag.split('__', 1)[0]]['GROUPS']
#
#TODO: This might be easier using lists of tags and data for each class!
    def ORDERED_IF_SAME_DAY(self, data):
        """Two subjects should be in the given order, if on the same day.
        """
        constraints = []
        cmap = self.class_constraint_data(data)
        pairs = self.__pairs_common_groups(cmap)
        for klass, item_map in cmap.items():
            for item, weight in item_map.items():
                percent = WEIGHTS[int(weight)]
                if not percent:
                    continue
                taglist = pairs[item].get(klass) or []
                for tag, tagset in taglist:
                    lids2 = []
                    for t in tagset:
                        lids2 += self.tag_lids[t]
                    for lid1 in self.tag_lids[tag]:
                        #print("???", klass, item, percent, lid1, lids2)
                        for lid2 in lids2:
                            constraints.append(
                                {   'Weight_Percentage': percent,
                                    'First_Activity_Id': lid1,
                                    'Second_Activity_Id': lid2,
                                    'Active': 'true',
                                    'Comments': None
                                }
                            )
        if constraints:
            self.time_constraints['ConstraintTwoActivitiesOrderedIfSameDay'] \
                    = constraints
#
    def PAIR_GAPS(self, data):
        """Two subjects should have at least one lesson in between.
        """
        constraints = []
        cmap = self.class_constraint_data(data)
        pairs = self.__pairs_common_groups(cmap)
        for klass, item_map in cmap.items():
            for item, weight in item_map.items():
                percent = WEIGHTS[int(weight)]
                if not percent:
                    continue
                taglist = pairs[item].get(klass) or []
                for tag, tagset in taglist:
                    lids2 = []
                    for t in tagset:
                        lids2 += self.tag_lids[t]
                    for lid1 in self.tag_lids[tag]:
                        #print("???", klass, item, percent, lid1, lids2)
                        for lid2 in lids2:
                            constraints.append(
                                {   'Weight_Percentage': percent,
                                    'Number_of_Activities': '2',
                                    'Activity_Id': [lid1, lid2],
                                    'MinGaps': '1',
                                    'Active': 'true',
                                    'Comments': None
                                }
                            )
        if constraints:
            self.time_constraints['ConstraintMinGapsBetweenActivities'] \
                    = constraints

###

class Teachers_fet(Teachers):
    def get_teachers(self, timetable_teachers):
        return [
            {   'Name': tid,
                'Target_Number_of_Hours': '0',
                'Qualified_Subjects': None,
                'Comments': name
            } for tid, name in self.items() if tid in timetable_teachers
        ]
#
    def add_constraints(self, days, periods, classes):
#TODO: Passing in <classes> is a nasty bodge! There should be universal
# access to the days, the periods, the constraints and the lesson data.
        time_constraints = classes.time_constraints
        # Not-available times
        blocked = self.constraint_blocked_periods(days, periods)
        if blocked:
            time_constraints['ConstraintTeacherNotAvailableTimes'] = blocked
        # Gaps per week and contiguous lessons
        constraints_g = []
        constraints_u = []
        for tid in self:
            cdata = self.constraints[tid]
            g = cdata['GAPS']
            u = cdata['UNBROKEN']
            # These are <None> or a (number, weight) pair (integers)
            if g != None:
                constraints_g.append(
                    {   'Weight_Percentage': '100', # necessary!
                        'Teacher_Name': tid,
                        'Max_Gaps': str(g),
                        'Active': 'true',
                        'Comments': None
                    }
                )
            if u:
                n, w = u
                if w:
                    constraints_u.append(
                        {   'Weight_Percentage': WEIGHTS[w],
                            'Teacher_Name': tid,
                            'Maximum_Hours_Continuously': str(n),
                            'Active': 'true',
                            'Comments': None
                        }
                    )
        if constraints_g:
            time_constraints['ConstraintTeacherMaxGapsPerWeek'] \
                    = constraints_g
        if constraints_u:
            time_constraints['ConstraintTeacherMaxHoursContinuously'] \
                    = constraints_u

        constraints = self.lunch_breaks(days, periods, classes)
        if constraints:
            try:
               time_constraints[
                        'ConstraintActivityPreferredStartingTimes'] \
                    += constraints
            except KeyError:
                time_constraints[
                        'ConstraintActivityPreferredStartingTimes'] \
                    = constraints

        constraints = self.min_lessons_daily(classes)
        if constraints:
            time_constraints['ConstraintTeacherMinHoursDaily'] = constraints

    def constraint_blocked_periods(self, days, periods):
        """Return the blocked periods in the form needed by fet.
        """
        blocked = []
        for tid in self:
            dlist = self.blocked_periods.get(tid)
            if dlist:
                if len(dlist) != len(days):
                    REPORT("ERROR", _TEACHER_DAYS_WRONG.format(
                            tname = self[tid]))
                    continue
                tlist = []
                i = 0
                for d in days:
                    pblist = dlist[i]
                    i += 1
                    if len(pblist) != len(periods):
                        REPORT("ERROR", _TEACHER_PERIODS_WRONG.format(
                                tname = self[tid], day = d))
                        continue
                    j = 0
                    for p in periods:
                        if pblist[j]:
                            tlist.append(
                                {
                                    'Day': d,
                                    'Hour': p
                                }
                            )
                        j += 1
                blocked.append(
                    {   'Weight_Percentage': '100',
                        'Teacher': tid,
                        'Number_of_Not_Available_Times': str(len(tlist)),
                        'Not_Available_Time': tlist
                    }
                )
        return blocked
#
    def lunch_breaks(self, days, periods, classes):
        """Add a special lesson on the long days AND a constraint to
        limit it to the lunch times.
        """
        constraints = []
        for tid in classes.timetable_teachers:
            lbperiods = self.constraints[tid]['LUNCH']
            if not lbperiods:
                continue
            bp = self.blocked_periods.get(tid)
            for d in range(len(days)):
                try:
                    for p in lbperiods:
                        i = periods.index(p)
                        if bp[d][i]:
                            break    # No lunch break needed
                    else:
                        raise ValueError
                    continue
                except:
                    # need lunch break
                    pass
                classes.last_lesson_id += 1
                lid = str(classes.last_lesson_id)
                lesson = {
                    'Teacher': tid,
                    'Subject': LUNCH_BREAK[0],
#                    'Students': {},
                    'Duration': '1',
                    'Total_Duration': '1',
                    'Id': lid,
                    'Activity_Group_Id': '0',
                    'Active': 'true',
                    'Comments': None
                }
                classes.lesson_list.append(lesson)
                # Add constraint
                day = days[d]
                plist = [
                    {   'Preferred_Starting_Day': day,
                        'Preferred_Starting_Hour': p
                    } for p in lbperiods
                ]
                constraints.append(
                    {   'Weight_Percentage': '100',
                        'Activity_Id': lid,
                        'Number_of_Preferred_Starting_Times': str(len(
                                plist)),
                        'Preferred_Starting_Time': plist,
                        'Active': 'true',
                        'Comments': None
                    }
                )
        return constraints
#
    def min_lessons_daily(self, classes):
        """ConstraintTeacherMinHoursDaily
        """
        constraints = []
        for tid in classes.timetable_teachers:
            minl = self.constraints[tid]['MINLESSONS']
            if not minl:
                continue
            constraints.append(
                {   'Weight_Percentage': '100',
                    'Teacher_Name': tid,
                    'Minimum_Hours_Daily': str(minl),
                    'Allow_Empty_Days': 'true',
                    'Active': 'true',
                    'Comments': None
                }
            )
        return constraints

###

class Rooms_fet(Rooms):
    def get_rooms(self):
        return [{'Name': rid, 'Building': None, 'Capacity': '30000',
                'Virtual': 'false', 'Comments': name}
                for rid, name in self.items()]

###

class Subjects_fet(Subjects):
    def get_subjects(self):
        sids = [{'Name': sid, 'Comments': name}
                for sid, name in self.items()
        ]
        sids.append({'Name': VIRTUAL_ROOM[0], 'Comments': VIRTUAL_ROOM[1]})
        sids.append({'Name': LUNCH_BREAK[0], 'Comments': LUNCH_BREAK[1]})
        return sids

###

def build_dict_fet(ROOMS, DAYS, PERIODS, TEACHERS, SUBJECTS,
        CLASSES, LESSONS, time_constraints, space_constraints):
    fet_dict = {
        '@version': f'{FET_VERSION}',
        'Mode': 'Official',
        'Institution_Name': 'FWS Bothfeld',
        'Comments': 'Default comments',

        'Days_List': {
            'Number_of_Days': f'{len(DAYS)}',
            'Day': DAYS
        },

        'Hours_List': {
            'Number_of_Hours': f'{len(PERIODS)}',
            'Hour': PERIODS
        },

        'Subjects_List': {
            'Subject': SUBJECTS
        },

        'Activity_Tags_List': None,

        'Teachers_List': {
            'Teacher': TEACHERS
        },

        'Students_List': {
            'Year': CLASSES
        },

        'Activities_List': {
            'Activity': LESSONS
        },

        'Buildings_List': None,
        'Rooms_List': {
            'Room': ROOMS
        },
    }
    tc_dict = {
        'ConstraintBasicCompulsoryTime': {
            'Weight_Percentage': '100',
            'Active': 'true',
            'Comments': None
        }
    }
    sc_dict = {
        'ConstraintBasicCompulsorySpace': {
            'Weight_Percentage': '100',
            'Active': 'true',
            'Comments': None
        }
    }
    tc_dict.update(time_constraints)
    sc_dict.update(space_constraints)
    fet_dict['Time_Constraints_List'] = tc_dict
    fet_dict['Space_Constraints_List'] = sc_dict
    return {'fet': fet_dict}

###

class Placements_fet(Placements):
    def placements(self, days, periods, classes):
        tag_lids = classes.tag_lids
#        print("\n tag_lids::::::::::::::::::")
#        for k, v in tag_lids.items():
#            print(f"  {k}:", v)
#        print("\n*** Parallel tags ***")
#        for k, v in self.parallel_tags.items():
#            print(f"  {k}:", v)
        cards = []
        for _tag, places_list in self.predef:
            for tag in classes.parallel_tags[_tag]:
                try:
                    lids = tag_lids[tag]
                except KeyError:
                    REPORT("WARN", _NO_LESSON_WITH_TAG.format(tag = tag))
                    continue
                i = 0
                for d, p in places_list:
                    try:
                        lid = lids[i]
                    except ValueError:
                        REPORT("ERROR", _TAG_TOO_MANY_TIMES.format(tag = tag))
                        continue
                    i += 1
                    cards.append({
                            'Weight_Percentage': '100',
                            'Activity_Id': lid,
                            'Preferred_Day': days[d],
                            'Preferred_Hour': periods[p],
                            'Permanently_Locked': 'true',
                            'Active': 'true',
                            'Comments': None
                        }
                    )
        classes.time_constraints['ConstraintActivityPreferredStartingTime'] \
                    = cards


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    _days = Days()

    _periods = Periods()

    _classes = Classes_gui(_periods)
    if _classes.days != list(_days):
        print("\nDAYS MISMATCH:", _classes.days)
        quit(1)

    _rooms = Rooms_fet()
    rooms = _rooms.get_rooms()
    if __TEST:
        print("\nROOMS:")
        for rdata in rooms:
            print("   ", rdata)

    _subjects = Subjects_fet()
    subjects = _subjects.get_subjects()
    if __TEST:
        print("\nSUBJECTS:")
        for sdata in subjects:
            print("   ", sdata)

    _teachers = Teachers_fet(_classes.days, _periods)

    if __TEST:
        print("\n ********** READ LESSON DATA **********\n")
    c_list = _classes.all_lessons(SUBJECTS = _subjects, ROOMS = _rooms,
            TEACHERS = _teachers)
    print("\n ... read data for:", c_list)

    if __TEST:
        print("\n  CLASSROOMS:", _classes.classrooms)
        _klass = '12G'
        print("\nCLASS", _klass)
        print("\n  DIVISIONS:", _classes.class_divisions[_klass])
        print("\n  GROUPS:", _classes.class_groups[_klass])

    teachers = _teachers.get_teachers(_classes.timetable_teachers)
    if __TEST:
        print("\nTEACHERS:")
        for tid, tname in _teachers.items():
            blocked = _teachers.blocked_periods.get(tid) or '–––'
            print("  ", tid, tname, blocked)
        for tdata in teachers:
            print("   ", tdata)
#TODO:
#        print("\nLONG TAGS:\n", _teachers.longtag.values())

    from timetable.tt_data import TT_CONFIG
    outdir = YEARPATH(TT_CONFIG['OUTPUT_FOLDER'])
    os.makedirs(outdir, exist_ok = True)

    # Check-lists for teachers
    outpath = os.path.join(outdir, 'teacher_check.txt')
    with open(outpath, 'w', encoding = 'utf-8') as fh:
        fh.write("STUNDENPLAN 2021/22: Lehrer-Stunden\n"
                "===================================\n")
        fh.write(_classes.teacher_check_list())
    print("\nTEACHER CHECK-LIST ->", outpath)

    classes = []
    for klass in c_list:
        if klass.startswith('XX'): continue
        class_data = _classes.class_data(klass)
        classes.append(class_data)
        if __TEST:
            print(f"\nfet-CLASS {klass}")
            for g in class_data.get('Group') or []:
                print("  ---", g['Name'])
                for sg in g.get('Subgroup') or []:
                    print("     +", sg['Name'])

    _classes.get_lessons()
    lessons, s_constraints, t_constraints = _classes.lesson_list, \
            _classes.space_constraints, _classes.time_constraints
    if __TEST:
        print("\n ********* fet LESSONS *********\n")
        #for l, data in _classes.lessons.items():
        #    print(f"   {l}:", data)
        for l in lessons:
            print("   ", l)
        print("\n  ======================================================\n")

#TODO: At present the input is 1-based indexes. It might be better to use
# the ids ...
    i = 0
    d2 = {}
    d2list = []
    for d in _days:
        did =_days.get_id(d)
        d2list.append(did)
        i += 1
        d2[str(i)] = did
    i = 0
    p2 = {}
    p2list = []
    for p in _periods:
        pid =_periods.get_id(p)
        p2list.append(pid)
        i += 1
        p2[str(i)] = pid

    # Teachers' constraints
    _teachers.add_constraints(d2list, p2list, _classes)

    # Classes' not-available times
    _classes.constraint_blocked_periods()

    # Fixed placements for lessons
    cards = Placements_fet(_classes)
    cards.placements(d2, p2, _classes)

    sid_group_sets = _classes.constraint_day_separation(cards.predef)

    # For all classes, and with custom values for some classes:
    # minimum lessons per day
#TODO: This one could be table driven?
    mintable = {k: 5 for k in ('01K', '02K', '03K', '04K', '05K', '06K',
            '07K', '08K', '09K', '10K', '11K', '12K')}
    _classes.constraint_min_lessons_per_day(4, mintable)

    EXTRA_CONSTRAINTS = MINION(YEARPATH(TT_CONFIG['CONSTRAINTS']))
    for key, value in EXTRA_CONSTRAINTS.items():
        try:
            func = getattr(_classes, key)
        except AttributeError:
            print(f"CONSTRAINT {key}: Not yet implemented")
            continue
        func(value)

#TODO: Should this be before the extra constraints?
    _classes.lunch_breaks(lessons)

    """xml_fet = xmltodict.unparse(build_dict_fet(
            ROOMS = rooms,
            DAYS = days,
            PERIODS = periods,
            TEACHERS = teachers,
            SUBJECTS = subjects,
            CLASSES = classes,
            LESSONS = lessons,
            time_constraints = t_constraints,
            space_constraints = s_constraints
#            space_constraints = {}
        ),
        pretty = True
    )"""

    outpath = os.path.join(outdir, 'tt_out.fet')
#    with open(outpath, 'w', encoding = 'utf-8') as fh:
#        fh.write(xml_fet.replace('\t', '   '))
#    print("\nTIMETABLE XML ->", outpath)

#    for sid, gs in sid_group_sets.items():
#        print(f"\n +++ {sid}:", gs)
#    print(f"\n +++ Mal:", sid_group_sets['Mal'])
#    print("\n???divisions 01K:", _classes.class_divisions['01K'])
#    print("\n???class_groups 01K:", _classes.class_groups['01K'])

    import json
    outpath = os.path.join(outdir, 'tag-lids.json')
    # Save association of lesson "tags" with "lids" and "xlids"
    lid_data = {
        'tag-lids': _classes.tag_lids,
        'lid-xlids': {lids[0]: lids[1:] for lids in _classes.xlids}
    }
 #   with open(outpath, 'w', encoding = 'utf-8') as fh:
 #       json.dump(lid_data, fh, indent = 4)
 #   print("\nTag – Lesson associations ->", outpath)

#    outpath = os.path.join(outdir, 'multiple-rooms')
#    with open(outpath, 'w', encoding = 'utf-8') as fh:
#        for mr in _classes.multirooms:
#            groups = ', '.join(mr['GROUPS'])
#            sname = _classes.SUBJECTS[mr['SID']]
#            fh.write(f"\nKlasse {mr['CLASS']} ({groups})"
#                    f" :: {sname}: {mr['NUMBER']}")

#    print("\nSubjects with multiple rooms ->", outpath)

