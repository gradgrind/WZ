# -*- coding: utf-8 -*-

"""
TT/asc_data.py - last updated 2021-08-15

Prepare fet-timetables input from the various sources ...

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

__TEST = False
#__TEST = True

FET_VERSION = '6.1.1'

LUNCH_BREAK_SID = 'mp'

### Messages
_NO_JOINT_ROOMS = "Fach {sid} ({tag}), Klassen {classes}:" \
        " Keine verfügbare Räume (zu '?')"
_LESSON_NO_GROUP = "Klasse {klass}, Fach {sid}: „Unterricht“ ohne Gruppe"
_LESSON_NO_TEACHER = "Klasse {klass}, Fach {sid}: „Unterricht“ ohne Lehrer"


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
#TODO: "Epochen": get the teachers from the lines with 'Epoche: Hu.2', etc.

# IMPORTANT: Note that some uses of Python dicts here may assume ordered
# entries. If the implementation is altered, this should be taken into
# account. One place is the definition of pre-placed lessons
# for a subject. If there is more than one entry for this subject and
# varying durations, the placement could be affected.

### +++++

from itertools import combinations

import xmltodict

from timetable.tt_data import Classes, Days, Periods, Placements, Rooms, \
        Subjects, Teachers, TT_Error

### -----

class Days_fet(Days):
    def get_days(self):
        """Return an ordered list of fet elements for the days.
        """
        return [{'Name': dkey} for dkey in self]
#
    def get_id(self, key):
        return self[key]['short']

###

class Periods_fet(Periods):
    def get_periods(self):
        """Return an ordered list of fet elements for the periods.
        """
        return [{'Name': pkey} for pkey in self]
#
    def get_id(self, key):
        return self[key]['short']

###

class Classes_fet(Classes):
#?
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self.atomic_groups = {}
#
    def class_data(self, klass):
        """Return a fet students_list/year entry for the given class.
        """
        class_groups = self.class_groups[klass]
        division = self.atomics_lists[klass]
# Try with just 0 or 1 category.
        # The groups are all the "elemental" groups plus any dotted groups
        # which are used and not "atomic" groups already defined as subgroups.
        year_entry = {
            'Name': klass,
#TODO: long name?
            'Number_of_Students': '0',
            'Comments': None, # '1. Großklasse'. etc.?
            'Number_of_Categories': '1' if division else '0',
            'Separator': '.'
        }
        if division:
            _groups = []
            _agset = set()
            for g, sgs in class_groups.items():
                if g == '*': continue
                g = f'{klass}.{g}'
                if g in sgs:
                    # This group is an atomic group
                    if g not in _agset:
                        _agset.add(g)
                        _groups.append(
                            {   'Name': g,
                                'Number_of_Students': '0',
                                'Comments': None
                            }
                        )
                else:
                    _agset.update(sgs)
                    _subgroups = [
                        {   'Name': sg,
                            'Number_of_Students': '0',
                            'Comments': None
                        } for sg in sgs
                    ]
                    _groups.append(
                        {   'Name': g,
                            'Number_of_Students': '0',
                            'Comments': None,
                            'Subgroup': _subgroups
                        }
                    )
            year_entry['Category'] = {
                'Number_of_Divisions': f'{len(division)}',
                'Division': division
            }
            year_entry['Group'] = _groups
        return year_entry
#
    def class_days(self, klass):
        """Return a 'ConstraintStudentsSetNotAvailableTimes' for the
        class.
        """
        daymap = self.class_days_periods[klass]
        weektags = []
        for day in self.days:
            dayperiods = daymap[day]
            for p in self.periods:
                if not dayperiods[p]:
                    weektags.append({'Day': day, 'Hour': p})
        return {'Weight_Percentage': '100', 'Students': klass,
            'Number_of_Not_Available_Times': f'{len(weektags)}',
            'Not_Available_Time': weektags,
            'Active': 'true', 'Comments': None
        }
#
    def classes_timeoff(self):
        """Constraint: students set not available ...
        """
        return [self.class_days(klass) for klass in self.class_days_periods]
#
    def get_lessons(self, rooms):
        """Build list of lessons for fet-timetables.
        """
        space_constraints = {}  # for room placements
        lesson_list = []
        self.tag_lids = {}      # {tag: [lesson-id (int), ...]}
        # For constraints concerning relative placement of individual
        # lessons in the various subjects:
        self.sid_groups = {}    # {sid: [(group-set, lesson-tag), ... ]}
        lid = 0
        for tag, data in self.lessons.items():
            block = data['block']
            if block and block not in ('++', '--'):
                continue    # not a timetabled lesson
            sid = data['SID']
            klass = data['CLASS']
            groups = data['GROUPS']
            gids = sorted(groups)
            if gids:
                _classes_groups = {}
                for g in gids:
                    k, gg = self.split_class_group(g)
                    try:
                        _classes_groups[k].append(g)
                    except KeyError:
                        _classes_groups[k] = [g]
                _gids = []
                for k, gl in _classes_groups.items():
                    try:
                        _gids.append(self.groupsets_class[k][frozenset(gl)])
                    except KeyError:
                        _gids += gl
                g = _gids[0] if len(_gids) == 1 else _gids
#                print("???", tag, gids, "-->", g)
            else:
                REPORT("WARN", _LESSON_NO_GROUP.format(klass = klass,
                        sid = sid))
                g = None
            classes = ','.join(sorted(_classes_groups))
            tids = sorted(data['TIDS'])
            if not tids:
                REPORT("WARN", _LESSON_NO_TEACHER.format(klass = klass,
                        sid = sid))
                continue
            if '--' in tids:
                t = None
            elif len(tids) == 1:
                t = tids[0]
            else:
                t = tids

#TODO: add room constraints
            _roomlist = data['ROOMS']
            room_constraint = None
            if len(_roomlist) == 0:
                pass    # no room constraints

            elif len(_roomlist) == 1:
                _r = _roomlist[0]
                if _r == '?':
                    _rlist = sorted(set.intersection(*[
                                set(rooms.rooms_for_class[k])
                                        for k in _classes_groups
                            ]
                        )
                    )
                    if not _rlist:
                        raise TT_Error(_NO_JOINT_ROOMS.format(
                                klass = klass, sid = sid, tag = tag))
#

                else:
                    _rlist = _r.split('/')
                if len(_rlist) == 1:
                    room_constraint = 'ConstraintActivityPreferredRoom'
                    rc_item = {
                        'Weight_Percentage': '100',
                        'Activity_Id': None,
                        'Room': _rlist[0],
                        'Permanently_Locked': 'true',
                        'Active': 'true',
                        'Comments': None
                    }
                else:
                    room_constraint = 'ConstraintActivityPreferredRooms'
                    rc_item = {
                        'Weight_Percentage': '100',
                        'Activity_Id': None,
                        'Number_of_Preferred_Rooms': len(_rlist),
                        'Preferred_Room': _rlist,
                        'Active': 'true',
                        'Comments': None
                    }
            else:
                # Multiple rooms ...
#TODO
                pass

#        space_constraints['ConstraintActivityPreferredRoom'] = [rc_list]






            dmap = data['lengths']
            if dmap:
                aid = '0'
                for d in sorted(dmap):
                    _tag_lids = []
                    __tag = f'{tag}__{d}' if len(dmap) > 1 else tag
                    for i in range(dmap[d]):
                        lid += 1
                        _tag_lids.append(lid)
                        dstr = str(d)
                        lesson = {'Teacher': t} if t else {}
                        if g:
                            lesson['Students'] = g
                        _lid = str(lid)
                        lesson.update({
                            'Subject': sid,
                            'Duration': dstr,
                            'Total_Duration': dstr,
                            'Id': _lid,
                            'Activity_Group_Id': aid,
                            'Active': 'true',
                            'Comments': __tag
                        })
                        lesson_list.append(lesson)
                        if room_constraint:
                            try:
                                rc = space_constraints[room_constraint]
                            except KeyError:
                                rc = []
                                space_constraints[room_constraint] = rc
                            rci = rc_item.copy()
                            rci['Activity_Id'] = _lid
                            rc.append(rci)
                    try:
                        self.tag_lids[__tag] += _tag_lids
                    except KeyError:
                        self.tag_lids[__tag] = _tag_lids
                    try:
                        self.sid_groups[sid].append((groups, __tag))
                    except KeyError:
                        self.sid_groups[sid] = [(groups, __tag)]
        self.last_lesson_id = lid
#TODO--
#        print("???", self.tag_lids)


        return lesson_list, space_constraints
#
    def constraint_no_gaps(self, time_constraints):
        """Set no gaps (in the lower classes?).
        """
#TODO: specify in config file?
        time_constraints['ConstraintStudentsSetMaxGapsPerWeek'] = [
            {   'Weight_Percentage': '100',
                'Max_Gaps': '0',
                'Students': klass,
                'Active': 'true',
                'Comments': None
            } for klass in self.class_days_periods
#                if klass < '09'
        ]
#
    def lunch_breaks(self, lessons, time_constraints):
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
                            'Subject': LUNCH_BREAK_SID,
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
            time_constraints['ConstraintActivityPreferredStartingTimes'] \
                    = constraints
#
    def constraint_day_separation(self, placements, time_constraints):
        """Add constraints to ensure that multiple lessons in any subject
        are not placed on the same day.
        <placements> supplies the tags, as list of (tag, positions) pairs,
        which have fixed positions, and so do not need this constraint.
        """
        _placements = {k for k, v in placements}
        sid_group_sets = {}
        constraints = []
        for sid, sdata in self.sid_groups.items():
            # Get a set of tags for each "atomic" group (for this subject)
            tglist = []
            for groups, tag in sdata:
                gset = set()
                for g in groups:
                    k, x = self.split_class_group(g)
                    if x:
                        gset.add(g)
                    else:
                        gset.update(self.class_groups[k]['*'])
                tglist.append((gset, tag))
            tgmap = {}
#TODO: extract the lesson-ids from the tags?
            # Collect the tags which share groups (for this subject)
            for groups, tag in tglist:
                collect = {t for gset, t in tglist if groups & gset}
                if len(collect) > 1 or len(self.tag_lids[tag]) > 1:
                    tgmap[tag] = collect
            # Get sets of tags with (group) intersections
            kcombis = set()
            for tag, partners in tgmap.items():
                for l in range(len(partners), 0, -1):
                    for c in combinations(partners, l):
                        if tag in c:
                            kcombis.add(frozenset(c))
            xcombis = []
            for combi in kcombis:
                # Check with all components
#                print("&&&", combi)
                for p in combi:
#                    print("%%%", p)
                    plist = tgmap[p]
                    for q in combi:
                        if q not in plist:
                            break
                    else:
                        # ok
                        continue
                    break
                else:
                    xcombis.append(combi)
            # Eliminate subsets
            ycombis = []
            for c in xcombis:
                for c2 in xcombis:
                    if c < c2:
                        break
                else:
                    ycombis.append(c)
            if tag.startswith('01K_0'):
                print("§§§1:", xcombis, "\n  ->", ycombis)
            # Remove tag sets containing only fixed lessons (this
            # can't cope with tags whose lessons are only partially
            # placed – they are handled as tags with full placed
            # lessons).
            tagsets = set()
            for tags in ycombis:
                for tag in tags:
                    if tag not in _placements:
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
            time_constraints['ConstraintMinDaysBetweenActivities'] \
                    = constraints
        return sid_group_sets

#TODO: This is rather a hammer-approach which could perhaps be improved
# by collecting data class-wise?

###

class Teachers_fet(Teachers):
    def get_teachers(self):
        return [
            {   'Name': tid,
                'Target_Number_of_Hours': '0',
                'Qualified_Subjects': None,
                'Comments': name
            } for tid, name in self.items()
        ]
#
    def get_all_blocked_periods(self, days, periods):
        """Return the blocked periods in the form needed by fet.
        """
        blocked = []
        for tid in self:
            dlist = self.blocked_periods.get(tid)
            if dlist:
                if len(dlist) != len(days):
#TODO:
                    print(f"ERROR: Teacher {tid} availability has"
                            " wrong number of days")
                    continue
                tlist = []
                i = 0
                for d in days:
                    pblist = dlist[i]
                    i += 1
                    if len(pblist) != len(periods):
#TODO:
                        print(f"ERROR: Teacher {tid} availability has"
                                f" wrong number of periods, day {d}")
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

###

class Rooms_fet(Rooms):
    def get_rooms(self):
        return [{'Name': rid, 'Building': None, 'Capacity': '30000',
                'Virtual': 'false', 'Comments': name}
                for rid, name in self.items()]
#TODO: special fet bodge.
# Add virtual rooms when a lesson needs more than one room.
# Name them according to the contained rooms, e.g. 'rid1,rid2'?
#                {'Name': 'V1', 'Building': None, 'Capacity': '30000',
#                    'Virtual': 'true',
#                    'Number_of_Sets_of_Real_Rooms': '2',
#                    'Set_of_Real_Rooms': [
#                        {'Number_of_Real_Rooms': '1', 'Real_Room': 'rid1'},
#                        {'Number_of_Real_Rooms': '1', 'Real_Room': 'rid2'}
#                    ], 'Comments': None
#                },
# To include more than one room in a set (possibly best to avoid this?):
# {'Number_of_Real_Rooms': '2', 'Real_Room': ['r2', 'r3']}

###

class Subjects_fet(Subjects):
    def get_subjects(self):
        return [{'Name': sid, 'Comments': name}
                for sid, name in self.items()
        ]

########################################################################
def build_time_constraints(CLASSFREE, TEACHERFREE, CARDS):
    return {
        'ConstraintStudentsSetNotAvailableTimes': CLASSFREE,
#                        {'Weight_Percentage': '100', 'Students': '01G',
#                            'Number_of_Not_Available_Times': '20',
#                            'Not_Available_Time': [
#                                {'Day': 'Mo', 'Hour': '4'},
#                                {'Day': 'Mo', 'Hour': '5'},
#                                {'Day': 'Mo', 'Hour': '6'},
#                                {'Day': 'Mo', 'Hour': '7'},
#                                {'Day': 'Di', 'Hour': '4'},
#                                {'Day': 'Di', 'Hour': '5'},
# ...
#                            ],
#                            'Active': 'true', 'Comments': None
#                        },
#                        {'Weight_Percentage': '100',
# ...
#                        },
#                    ],

#                    'ConstraintActivitiesPreferredStartingTimes': {
#                        'Weight_Percentage': '99.9',
#                        'Teacher_Name': None,
#                        'Students_Name': None,
#                        'Subject_Name': 'Hu',
#                        'Activity_Tag_Name': None,
#                        'Duration': None,
#                        'Number_of_Preferred_Starting_Times': '5',
#                        'Preferred_Starting_Time': [
#                            {'Preferred_Starting_Day': 'Mo', 'Preferred_Starting_Hour': 'A'},
#                            {'Preferred_Starting_Day': 'Di', 'Preferred_Starting_Hour': 'A'},
#                            {'Preferred_Starting_Day': 'Mi', 'Preferred_Starting_Hour': 'A'},
#                            {'Preferred_Starting_Day': 'Do', 'Preferred_Starting_Hour': 'A'},
#                            {'Preferred_Starting_Day': 'Fr', 'Preferred_Starting_Hour': 'A'}
#                        ],
#                        'Active': 'true',
#                        'Comments': None
#                    },

#                    'ConstraintActivityPreferredStartingTime': {
#                        'Weight_Percentage': '100',
#                        'Activity_Id': '8',
#                        'Preferred_Day': 'Mi',
#                        'Preferred_Hour': '1',
#                        'Permanently_Locked': 'true',
#                        'Active': 'true',
#                        'Comments': None
#                    }

        'ConstraintTeacherNotAvailableTimes': TEACHERFREE,

        'ConstraintActivityPreferredStartingTime': CARDS

    }

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

# Try single activities instead?
        'Activities_List': {
            'Activity': LESSONS

#                    [
#                        {'Teacher': 'JS', 'Subject': 'Hu', 'Students': '01G',
#                            'Duration': '2', 'Total_Duration': '10',
#                            'Id': '1', 'Activity_Group_Id': '1',
#                            'Active': 'true', 'Comments': None
#                        },
#                        {'Teacher': 'JS', 'Subject': 'Hu', 'Students': '01G',
#                            'Duration': '2', 'Total_Duration': '10',
#                            'Id': '2', 'Activity_Group_Id': '1',
#                            'Active': 'true', 'Comments': None
#                        },
#
# ...
# To specify more than one student group, use, e.g. ['01G_A', '02G_A'].
# Also the 'Teacher' field can take multiple entries: ['JS', 'CC']
#                    ]
        },

        'Buildings_List': None,
#TODO:
        'Rooms_List': {
            'Room': ROOMS

#                    [
#                        {'Name': 'r1', 'Building': None, 'Capacity': '30000',
#                            'Virtual': 'false', 'Comments': None
#                        },
#                        {'Name': 'r2', 'Building': None, 'Capacity': '30000',
#                            'Virtual': 'false', 'Comments': None
#                        },
## Virtual room (to get multiple rooms)
#                        {'Name': 'V1', 'Building': None, 'Capacity': '30000',
#                            'Virtual': 'true',
#                            'Number_of_Sets_of_Real_Rooms': '2',
#                            'Set_of_Real_Rooms': [
#                                {'Number_of_Real_Rooms': '1', 'Real_Room': 'r1'},
#                                {'Number_of_Real_Rooms': '1', 'Real_Room': 'r2'}
#                            ], 'Comments': None
#                        }
#                    ]
        },
# To include more than one room in a set:
#{'Number_of_Real_Rooms': '2', 'Real_Room': ['r2', 'r3']}
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



###################
# Alternative with single activities
#<Activity>
#    <Teacher>JS</Teacher>
#    <Subject>Hu</Subject>
#    <Students>01G</Students>
#    <Duration>2</Duration>
#    <Total_Duration>2</Total_Duration>
#    <Id>5</Id>
#    <Activity_Group_Id>0</Activity_Group_Id>
#    <Active>true</Active>
#    <Comments></Comments>
#</Activity>

#...

#<ConstraintActivityPreferredStartingTime>
#    <Weight_Percentage>100</Weight_Percentage>
#    <Activity_Id>1</Activity_Id>
#    <Preferred_Day>Mo</Preferred_Day>
#    <Preferred_Hour>A</Preferred_Hour>
#    <Permanently_Locked>true</Permanently_Locked>
#    <Active>true</Active>
#    <Comments></Comments>
#</ConstraintActivityPreferredStartingTime>
#<ConstraintActivityPreferredStartingTime>
#    <Weight_Percentage>100</Weight_Percentage>
#    <Activity_Id>2</Activity_Id>
#    <Preferred_Day>Di</Preferred_Day>
#    <Preferred_Hour>A</Preferred_Hour>
#    <Permanently_Locked>true</Permanently_Locked>
#    <Active>true</Active>
#    <Comments></Comments>
#</ConstraintActivityPreferredStartingTime>

#'ConstraintMinDaysBetweenActivities': [
#        {'Weight_Percentage': '100', 'Consecutive_If_Same_Day': 'true',
#            'Number_of_Activities': '2', 'Activity_Id': ['6', '7'],
#            'MinDays': '1', 'Active': 'true', 'Comments': None
#        },
#        {'Weight_Percentage': '100', 'Consecutive_If_Same_Day': 'true',
#            'Number_of_Activities': '2', 'Activity_Id': ['6', '8'],
#            'MinDays': '1', 'Active': 'true', 'Comments': None
#        }
#    ]
#},
"""
<ConstraintTeacherNotAvailableTimes>
    <Weight_Percentage>100</Weight_Percentage>
    <Teacher>MFN</Teacher>
    <Number_of_Not_Available_Times>9</Number_of_Not_Available_Times>
    <Not_Available_Time>
        <Day>Do</Day>
        <Hour>A</Hour>
    </Not_Available_Time>
    <Not_Available_Time>
        <Day>Do</Day>
        <Hour>B</Hour>
    </Not_Available_Time>
    <Not_Available_Time>
        <Day>Do</Day>
        <Hour>1</Hour>
    </Not_Available_Time>
    <Not_Available_Time>
        <Day>Do</Day>
        <Hour>2</Hour>
    </Not_Available_Time>
    <Not_Available_Time>
        <Day>Do</Day>
        <Hour>3</Hour>
    </Not_Available_Time>
    <Not_Available_Time>
        <Day>Do</Day>
        <Hour>4</Hour>
    </Not_Available_Time>
    <Not_Available_Time>
        <Day>Do</Day>
        <Hour>5</Hour>
    </Not_Available_Time>
    <Not_Available_Time>
        <Day>Do</Day>
        <Hour>6</Hour>
    </Not_Available_Time>
    <Not_Available_Time>
        <Day>Do</Day>
        <Hour>7</Hour>
    </Not_Available_Time>
    <Active>true</Active>
    <Comments></Comments>
</ConstraintTeacherNotAvailableTimes>
"""

def constraint_min_lessons_all(min_lessons, time_constraints):
    time_constraints['ConstraintStudentsMinHoursDaily'] = [
        {   'Weight_Percentage': '100',
            'Minimum_Hours_Daily': str(min_lessons),
            'Allow_Empty_Days': 'false',
            'Active': 'true',
            'Comments': None
        }
    ]

def constraint_min_lessons(group, min_lessons, time_constraints):
    item = {
        'Weight_Percentage': '100',
        'Minimum_Hours_Daily': str(min_lessons),
        'Students': group,
        'Allow_Empty_Days': 'false',
        'Active': 'true',
        'Comments': None
    }
    try:
        time_constraints['ConstraintStudentsSetMinHoursDaily'].append(item)
    except KeyError:
        time_constraints['ConstraintStudentsSetMinHoursDaily'] = [item]

###

def constraint_teacher_breaks(max_lessons, time_constraints):
    time_constraints['ConstraintTeachersMaxHoursContinuously'] = [
#TODO: Percentage?
        {   'Weight_Percentage': '95',
            'Maximum_Hours_Continuously': str(max_lessons),
            'Active': 'true',
            'Comments': None
        }
    ]

"""
# This one seems to make the generation impossible (it must be 100%):
<ConstraintTeachersMinHoursDaily>
    <Weight_Percentage>100</Weight_Percentage>
    <Minimum_Hours_Daily>2</Minimum_Hours_Daily>
    <Allow_Empty_Days>true</Allow_Empty_Days>
    <Active>true</Active>
    <Comments></Comments>
</ConstraintTeachersMinHoursDaily>
"""

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
#TODO:
                    print(f"WARNING: No lesson with tag {tag}")
                    continue
                i = 0
                for d, p in places_list:
                    try:
                        lid = lids[i]
                    except ValueError:
#TODO:
                        print(f"ERROR: too many placements for tag {tag}")
                    i += 1
                    cards.append({
                            'Weight_Percentage': '100',
                            'Activity_Id': str(lid),
                            'Preferred_Day': days[d],
                            'Preferred_Hour': periods[p],
                            'Permanently_Locked': 'true',
                            'Active': 'true',
                            'Comments': None
                        }
                    )
        return cards

###

def read_placements(tag_lids, folder):
    stem = os.path.basename(folder).rsplit('-', 1)[0]
    pos_file = os.path.join(folder, stem + '_activities.xml')
    with open(pos_file, 'rb') as fh:
        xml = fh.read()
    pos_data = xmltodict.parse(xml)
    pos_list = pos_data['Activities_Timetable']['Activity']
    lid_data = {}
    for p in pos_list:
        lid = p['Id']
#        print(f"  ++ {lid:4}: {p['Day']}.{p['Hour']} @ {p['Room']}")
        lid_data[int(lid)] = dict(p)
    tag_data = {}
    for tag, lids in tag_lids.items():
        d = [lid_data[lid] for lid in lids]
        tag_data[tag] = d
#        print(f"  ++ {tag:12}:", d)
# The other info can be extracted from here, but may not be necessary ...
#    fet_file = os.path.join(folder, stem + '_data_and_timetable.fet')
#    with open(fet_file, 'rb') as fh:
#        xml = fh.read()
#    fet_data = xmltodict.parse(xml)
    return tag_data

#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    _days = Days_fet()

    days = _days.get_days()
    if __TEST:
        print("\n*** DAYS ***")
        for _day in _days:
            print('   ', f"'{_days.get_id(_day)}'", _days[_day])
        print("\n    ... for fet ...\n   ", days)
        print("\n  ==================================================")

    _periods = Periods_fet()
    periods = _periods.get_periods()
    if __TEST:
        print("\n*** PERIODS ***")
        for _pkey in _periods:
            print('   ', f"'{_periods.get_id(_pkey)}'", _periods[_pkey])
        print("\n    ... for fet ...\n   ", periods)
        print("\n  ==================================================")

    _classes = Classes_fet(_periods)
    if _classes.days != list(_days):
        print("\nDAYS MISMATCH:", _classes.days)
        quit(1)
    if __TEST:
        print("\n*** CLASS-DAYS ***")
        for klass in _classes.class_days_periods:
            _class_periods = _classes.class_days(klass)
            print(f"   class {klass}:", _class_periods)
        print("\n  ==================================================")

    _teachers = Teachers_fet(_classes.days, _periods)
    teachers = _teachers.get_teachers()
    if __TEST:
        print("\nTEACHERS:")
        for tid, tname in _teachers.items():
            blocked = _teachers.blocked_periods.get(tid) or '–––'
            print("  ", tid, tname, blocked)
        for tdata in teachers:
            print("   ", tdata)
#TODO:
#        print("\nLONG TAGS:\n", _teachers.longtag.values())

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

    lessons, space_constraints = _classes.get_lessons(_rooms)
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
    cards = Placements_fet(_classes)
    if __TEST:
        print("\n ********* FIXED LESSONS *********\n")
        #for l, data in _classes.lessons.items():
        #    print(f"   {l}:", data)
        for card in cards.placements(d2, p2, _classes):
            print("   ", card)

    time_constraints = build_time_constraints(
            CLASSFREE = _classes.classes_timeoff(),
            TEACHERFREE = _teachers.get_all_blocked_periods(d2list, p2list),
            CARDS = cards.placements(d2, p2, _classes)
        )

    _classes.lunch_breaks(lessons, time_constraints)

    sid_group_sets = _classes.constraint_day_separation(cards.predef,
            time_constraints)

    _classes.constraint_no_gaps(time_constraints)

#?
    constraint_min_lessons_all(4, time_constraints)
#?
    for g in ('01K', '02K', '03K', '04K', '05K', '06K',
            '07K', '08K', '09K', '10K', '11K', '12K'):
        constraint_min_lessons(g, 5, time_constraints)
#?
    constraint_teacher_breaks(4, time_constraints)

    xml_fet = xmltodict.unparse(build_dict_fet(
            ROOMS = rooms,
            DAYS = days,
            PERIODS = periods,
            TEACHERS = teachers,
            SUBJECTS = subjects,
            CLASSES = classes,
            LESSONS = lessons,
            time_constraints = time_constraints,
            space_constraints = space_constraints
#            space_constraints = {}
        ),
        pretty = True
    )

    outpath = os.path.join(outdir, 'tt_out.fet')
    with open(outpath, 'w', encoding = 'utf-8') as fh:
        fh.write(xml_fet.replace('\t', '   '))
    print("\nTIMETABLE XML ->", outpath)

#    for sid, gs in sid_group_sets.items():
#        print(f"\n +++ {sid}:", gs)
#    print(f"\n +++ Mal:", sid_group_sets['Mal'])
#    print("\n???divisions 01K:", _classes.class_divisions['01K'])
#    print("\n???class_groups 01K:", _classes.class_groups['01K'])

    fetoutdir = os.path.expanduser('~/fet-results/timetables/tt_out-single')
    pos = read_placements(_classes.tag_lids, fetoutdir)
    plist = []
    for tag, tlist in pos.items():
        for tdata in tlist:
            tdata['Tag'] = tag
            plist.append(tdata)
    xml_pos = xmltodict.unparse({'Activities_Positions':
            { 'Activity': plist}}, pretty = True)
    outpath = os.path.join(outdir, 'placements.xml')
    with open(outpath, 'w', encoding = 'utf-8') as fh:
        fh.write(xml_pos.replace('\t', '   '))
    print("\nPLACEMENTS XML ->", outpath)
