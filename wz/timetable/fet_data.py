# -*- coding: utf-8 -*-

"""
TT/asc_data.py - last updated 2021-07-22

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

FET_VERSION = '6.0.4'

GROUP_SEPARATOR = '_'

### Messages

_DUPLICATE_TAG = "Fachtabelle, im Feld {key}: Werte „{source1}“ und" \
        " „{source2}“ sind intern nicht unterscheidbar."

########################################################################

import sys, os, datetime, re
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
#TODO: maybe put this back in later?
#    from core.base import start
#    start.setup(os.path.join(basedir, 'TESTDATA'))

#TODO: classrooms
#TODO: "Epochen": get the teachers from the lines with 'Epoche: Hu.2', etc.

# IMPORTANT: Note that some uses of Python dicts here may assume ordered
# entries. If the implementation is altered, this should be taken into
# account. One place is the definition of pre-placed lessons
# for a subject. If there is more than one entry for this subject and
# varying durations, the placement could be affected.

### +++++

import xmltodict

from timetable.tt_data import Classes, Days, Periods, Placements, Rooms, \
        Subjects, Teachers, TT_Error, DATAPATH, get_duration_map

#?
def idsub(tag):
    """In aSc, "id" fields may only contain ASCII alphanumeric characters,
    '-' and '_'. So this is also used here? Substitute anything else by '_'.
    """
    return re.sub('[^-_A-Za-z0-9]', '_', tag)
#TODO: fet has integer ids for activities

### -----

class Days_fet(Days):
    def get_days(self):
        """Return an ordered list of fet elements for the days.
        """
        return [{'Name': dkey} for dkey in self]

###

class Periods_fet(Periods):
    def get_periods(self):
        """Return an ordered list of fet elements for the periods.
        """
        return [{'Name': pkey} for pkey in self]

###

class Classes_fet(Classes):
    def class_data(self, klass):
        """Return a fet students_list/year entry for the given class.
        """
        divisions = self.class_divisions[klass]
        number_of_categories = len(divisions) - 1
        year_entry = {
            'Name': klass, 'Number_of_Students': '0',
#TODO: long name?
            'Comments': None, # '1. Großklasse'. etc.?
            'Number_of_Categories': f'{number_of_categories}',
            'Separator': GROUP_SEPARATOR
        }
        if number_of_categories == 1:
            glist = divisions[1]
            year_entry['Category'] = {
                'Number_of_Divisions': f'{len(glist)}',
                'Division': glist
            }
            year_entry['Group'] = [
                {   'Name': '{klass}{GROUP_SEPARATOR}{g}',
                    'Number_of_Students': '0',
                    'Comments': None} for g in glist
            ]
        elif number_of_categories > 1:
            year_entry['Category'] = [
                {'Number_of_Divisions': f'{len(glist)}',
                    'Division': glist
                } for glist in divisions[1:]
            ]
            #print("\n$$$", year_entry)
            groups = []
            subgroups = [[klass]]
            for glist in divisions[1:]:
                nsg = []
                for g in glist:
                    groups.append(g)
                    for s in subgroups:
                        nsg.append(s + [g])
                subgroups = nsg
            #print("\n$$$g", groups)
            #print("\n$$$s", subgroups)
            g_sg = {}
            for g in groups:
                g_sg[g] = []
                for sg in subgroups:
                    if g in sg:
                        try:
                            g_sg[g].append(GROUP_SEPARATOR.join(sg))
                        except KeyError:
                            g_sg[g] = [GROUP_SEPARATOR.join(sg)]
            year_entry['Group'] = [
                {   'Name': f'{klass}{GROUP_SEPARATOR}{g}',
                    'Number_of_Students': '0',
                    'Comments': None,
                    'Subgroup': [
                        {'Name': sg,'Number_of_Students': '0',
                         'Comments': None
                        } for sg in sglist
                    ]
                } for g, sglist in g_sg.items()
            ]
            #for yeg in year_entry['Group']: print("\n§§§", yeg)
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
#TODO: Constraint students set not available ...
#
    def get_lessons(self):
        """Build list of lessons for fet-timetables.
        """
        lesson_list = []
        lid = 0
        for tag, data in self.lessons.items():
            block = data['block']
            if block and block != '*':
                continue
            sid = idsub(data['SID'])
#            classes = ','.join(sorted(data['CLASSES']))
            gids = sorted(data['GROUPS'])
            if not gids:
#TODO: Is this possible?
                print(f"!!! LESSON WITHOUT GROUP: classes {classes};"
                        f" sid {sid}")
                continue
            if len(gids) == 1:
                g = gids[0]
            else:
                g = gids
            tids = sorted(data['TIDS'])
            if not tids:
#TODO?
                print(f"!!! LESSON WITHOUT TEACHER: classes {classes};"
                        f" sid {sid}")
                continue
            if len(tids) == 1:
                t = tids[0]
            else:
                t = tids
#TODO: add room constraints
#            rooms = ','.join(sorted(data['ROOMS']))
            duration = data['duration']
            n = data['number']
            if not n:
#TODO?
                print(f"!!! LESSON WITHOUT NUMBER: classes {classes};"
                        f" sid {sid}")
                quit(1)
            if n == 1:
                aid = '0'
            else:
                aid = str(lid + 1)
            td = str(n * duration)
#TODO: Switch to repeating entries with Duration == Total_Duration?
# (no multiple-lesson chips)
            for i in range(n):
                lid += 1
                lesson = {
                    'Teacher': t,
                    'Subject': sid,
                    'Students': g,
                    'Duration': str(duration),
                    'Total_Duration': td,
                    'Id': str(lid),
                    'Activity_Group_Id': aid,
                    'Active': 'true',
                    'Comments': None
                }
                lesson_list.append(lesson)
        return lesson_list
#TODO: This is not picking up the right groups.
# 1) '12K-alle', etc.
# 2) ['09G-B.G', '09G-B.R'], etc.


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
#TODO: Constraint: teacher not available ...

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
        sbj_list = []
        sbj_tag = {}
        for sid, name in self.items():
#TODO: Scrap this transformation?
            _sid = idsub(sid)
            try:
                sid0 = sbj_tag[_sid]
            except:
                sbj_tag[_sid] = sid
                sbj_list.append({'Name': _sid, 'Comments': name})
            else:
                raise TT_Error(_DUPLICATE_TAG.format(
                        tag = _sid, key = self.tfield['SID'],
                        source1 = sid0, source2 = sid))
        return sbj_list

########################################################################

def build_dict_fet(ROOMS, DAYS, PERIODS, TEACHERS, SUBJECTS,
        CLASSES, GROUPS, LESSONS, CARDS):
    BASE = {
        'fet': {
                '@version': '6.0.4',
                'Mode': 'Official',
                'Institution_Name': 'FWS Bothfeld',
                'Comments': 'Default comments',

                'Days_List': {
                    'Number_of_Days': f'{len(PERIODS)}',
                    'Day': DAYS
                },

                'Hours_List': {
                    'Number_of_Hours': f'{len(PERIODS)}',
                    'Hour': PERIODS
                },

                'Subjects_List': {
                    'Subject': [
                        {'Name': 'En', 'Comments': 'Englisch'},
                        {'Name': 'Fr', 'Comments': 'Französisch'},
                    ]
                },

                'Activity_Tags_List': None,

                'Teachers_List': {
                    'Teacher': [
                        {'Name': 'JS', 'Target_Number_of_Hours': '0',
                                'Qualified_Subjects': None,
                                'Comments': 'Johannes Schüddekopf'
                        },
                        {'Name': 'CF', 'Target_Number_of_Hours': '0',
                                'Qualified_Subjects': None,
                                'Comments': 'Caroline Franke'
                        },
                    ]
                },

                'Students_List': {
                    'Year': CLASSES
                },

# Try single activities instead?
                'Activities_List': {
                    'Activity': [
                        {'Teacher': 'JS', 'Subject': 'Hu', 'Students': '01G',
                            'Duration': '2', 'Total_Duration': '10',
                            'Id': '1', 'Activity_Group_Id': '1',
                            'Active': 'true', 'Comments': None
                        },
                        {'Teacher': 'JS', 'Subject': 'Hu', 'Students': '01G',
                            'Duration': '2', 'Total_Duration': '10',
                            'Id': '2', 'Activity_Group_Id': '1',
                            'Active': 'true', 'Comments': None
                        },
                        {'Teacher': 'JS', 'Subject': 'Hu', 'Students': '01G',
                            'Duration': '2', 'Total_Duration': '10',
                            'Id': '3', 'Activity_Group_Id': '1',
                            'Active': 'true', 'Comments': None
                        },
                        {'Teacher': 'JS', 'Subject': 'Hu', 'Students': '01G',
                            'Duration': '2', 'Total_Duration': '10',
                            'Id': '4', 'Activity_Group_Id': '1',
                            'Active': 'true', 'Comments': None
                        },
                        {'Teacher': 'JS', 'Subject': 'Hu', 'Students': '01G',
                            'Duration': '2', 'Total_Duration': '10',
                            'Id': '5', 'Activity_Group_Id': '1',
                            'Active': 'true', 'Comments': None
                        },
                        {'Teacher': 'CF', 'Subject': 'Hu', 'Students': '01K',
                            'Duration': '2', 'Total_Duration': '10',
                            'Id': '6', 'Activity_Group_Id': '6',
                            'Active': 'true', 'Comments': None
                        },
# ...
# To specify more than one student group, use, e.g. ['01G_A', '02G_A'].
# Also the 'Teacher' field can take multiple entries: ['JS', 'CC']
                    ]
                },

                'Buildings_List': None,

                'Rooms_List': {
                    'Room': [
                        {'Name': 'r1', 'Building': None, 'Capacity': '30000',
                            'Virtual': 'false', 'Comments': None
                        },
                        {'Name': 'r2', 'Building': None, 'Capacity': '30000',
                            'Virtual': 'false', 'Comments': None
                        },
# Virtual room (to get multiple rooms)
                        {'Name': 'V1', 'Building': None, 'Capacity': '30000',
                            'Virtual': 'true',
                            'Number_of_Sets_of_Real_Rooms': '2',
                            'Set_of_Real_Rooms': [
                                {'Number_of_Real_Rooms': '1', 'Real_Room': 'r1'},
                                {'Number_of_Real_Rooms': '1', 'Real_Room': 'r2'}
                            ], 'Comments': None
                        }
                    ]
                },
# To include more than one room in a set:
#{'Number_of_Real_Rooms': '2', 'Real_Room': ['r2', 'r3']}






                'Time_Constraints_List': {
                    'ConstraintBasicCompulsoryTime': {
                        'Weight_Percentage': '100', 'Active': 'true', 'Comments': None
                    },
                    'ConstraintStudentsSetNotAvailableTimes': [
                        {'Weight_Percentage': '100', 'Students': '01G',
                            'Number_of_Not_Available_Times': '20',
                            'Not_Available_Time': [
                                {'Day': 'Mo', 'Hour': '4'},
                                {'Day': 'Mo', 'Hour': '5'},
                                {'Day': 'Mo', 'Hour': '6'},
                                {'Day': 'Mo', 'Hour': '7'},
                                {'Day': 'Di', 'Hour': '4'},
                                {'Day': 'Di', 'Hour': '5'},
# ...
                            ],
                            'Active': 'true', 'Comments': None
                        },
#                        {'Weight_Percentage': '100',
# ...
#                        },
                    ],

                    'ConstraintActivitiesPreferredStartingTimes': {
                        'Weight_Percentage': '99.9',
                        'Teacher_Name': None,
                        'Students_Name': None,
                        'Subject_Name': 'Hu',
                        'Activity_Tag_Name': None,
                        'Duration': None,
                        'Number_of_Preferred_Starting_Times': '5',
                        'Preferred_Starting_Time': [
                            {'Preferred_Starting_Day': 'Mo', 'Preferred_Starting_Hour': 'A'},
                            {'Preferred_Starting_Day': 'Di', 'Preferred_Starting_Hour': 'A'},
                            {'Preferred_Starting_Day': 'Mi', 'Preferred_Starting_Hour': 'A'},
                            {'Preferred_Starting_Day': 'Do', 'Preferred_Starting_Hour': 'A'},
                            {'Preferred_Starting_Day': 'Fr', 'Preferred_Starting_Hour': 'A'}
                        ],
                        'Active': 'true',
                        'Comments': None
                    },

                    'ConstraintActivityPreferredStartingTime': {
                        'Weight_Percentage': '100',
                        'Activity_Id': '8',
                        'Preferred_Day': 'Mi',
                        'Preferred_Hour': '1',
                        'Permanently_Locked': 'true',
                        'Active': 'true',
                        'Comments': None
                    }
                },

                'Space_Constraints_List': {
                    'ConstraintBasicCompulsorySpace': {
                        'Weight_Percentage': '100',
                        'Active': 'true',
                        'Comments': None
                    }
                }
            }
    }
    return BASE



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



###################


#                {   '@options': 'canadd,canremove,canupdate,silent',
#                    '@columns': 'id,name,short,days',
#                    'daysdef':
#                        [   {'@id': 'any', '@name': 'beliebigen Tag', '@short': 'X', '@days': '10000,01000,00100,00010,00001'},
#                            {'@id': 'every', '@name': 'jeden Tag', '@short': 'A', '@days': '11111'},
#                            {'@id': '1', '@name': 'Montag', '@short': 'Mo', '@days': '10000'},
#                            {'@id': '2', '@name': 'Dienstag', '@short': 'Di', '@days': '01000'},
#                            {'@id': '3', '@name': 'Mittwoch', '@short': 'Mi', '@days': '00100'},
#                            {'@id': '4', '@name': 'Donnerstag', '@short': 'Do', '@days': '00010'},
#                            {'@id': '5', '@name': 'Freitag', '@short': 'Fr', '@days': '00001'},
#                        ]
#                },
"""
            'periods':
                {   '@options': 'canadd,canremove,canupdate,silent',
                    '@columns': 'period,name,short,starttime,endtime',
                    'period': PERIODS
                },

            'teachers':
                {   '@options': 'canadd,canremove,canupdate,silent',
                    '@columns': 'id,short,name,timeoff',
                    'teacher': TEACHERS
                },

            'classes':
                {   '@options': 'canadd,canremove,canupdate,silent',
                    '@columns': 'id,short,name,classroomids,timeoff',
                    'class': CLASSES
                },

            'groups':
                {   '@options': 'canadd,canremove,canupdate,silent',
                    '@columns': 'id,classid,name,entireclass,divisiontag',
                    'group': GROUPS
                },

            'subjects':
                {   '@options': 'canadd,canremove,canupdate,silent',
                    '@columns': 'id,name,short',
                    'subject': SUBJECTS
                },

            'classrooms':
                {   '@options': 'canadd,canremove,canupdate,silent',
                    '@columns': 'id,name,short',
                    'classroom': ROOMS
                },

            'lessons':
            # Use durationperiods instead of periodspercard (deprecated)
            # As far as I can see, the only way in aSc to make lessons
            # parallel is to combine them to a single subject.
                {   '@options': 'canadd,canremove,canupdate,silent',
                    '@columns': 'id,classids,groupids,subjectid,durationperiods,periodsperweek,teacherids,classroomids',
                    'lesson': LESSONS
                },

            # Initial (fixed?) placements
            'cards':
                {   '@options': 'canadd,canremove,canupdate,silent',
                    '@columns': 'lessonid,period,day,classroomids,locked',
                    'card': CARDS
                },
        }
    }
    return BASE
"""

###

#TODO
class Placements_fet(Placements):
    def placements(self):
        cards = []
        for tag, places_list in self.predef:
            rooms = ','.join(sorted(self.lessons[tag]['ROOMS']))
            for d, p in places_list:
                cards.append({
                        '@lessonid': tag,
                        '@period': p,
                        '@day': d,
                        '@classroomids': rooms,
                        '@locked': '1'
                    }
                )
        return cards


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
        #for tid, tname in _teachers.items():
        #    blocked = _teachers.blocked_periods.get(tid) or '–––'
        #    print("  ", tid, tname, blocked)
        for tdata in teachers:
            print("   ", tdata)
        print("\nLONG TAGS:\n", _teachers.longtag.values())

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

    # Check-lists for teachers
    outpath = DATAPATH('teacher_check.txt')
    with open(outpath, 'w', encoding = 'utf-8') as fh:
        fh.write("STUNDENPLAN 2021/22: Lehrer-Stunden\n"
                "===================================\n")
        tmap = _classes.lessons_teacher_lists()
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
                            bname = f" ({_subjects[_block]})"
                        d = durations[0] if durations else 0
                        plist.append(f"EXTRA x {d}")
                        durations = None
                    else:
                        # Get main (teaching block) lesson entry
                        l = _classes.lessons[block]
                        bsid = l['SID']
                        bname = f" ({_subjects[bsid]})"
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
#                        cl.append(f" [{tag}]   {_subjects[sid]}{bname}"
#                                f" [{','.join(groups)}]: {p}\n")
                        cl.append(f"    {_subjects[sid]}{bname}"
                                f" [{','.join(groups)}]: {p}\n")
            if class_lessons:
                fh.write(f"\n\n$$$ {tid} ({_teachers[tid]})\n")
                for klass, clist in class_lessons.items():
                    fh.write(f"\n  Klasse {klass}:\n")
                    for l in clist:
                        fh.write(l)
    print("\nTEACHER CHECK-LIST ->", outpath)

    classes = []
    if __TEST:
        print(f"\nfet-CLASS {_klass}\n",_classes.class_data(_klass))
    for klass in c_list:
        classes.append(_classes.class_data(klass))

    lessons = _classes.get_lessons()
    if __TEST:
        print("\n ********* fet LESSONS *********\n")
        #for l, data in _classes.lessons.items():
        #    print(f"   {l}:", data)
        for l in lessons:
            print("   ", l)
        print("\n  ======================================================\n")

    quit(0)

    cards = Placements(_classes.lessons)
    if __TEST:
        print("\n ********* FIXED LESSONS *********\n")
        #for l, data in _classes.lessons.items():
        #    print(f"   {l}:", data)
        for card in cards.placements_aSc():
            print("   ", card)

    xml_aSc = xmltodict.unparse(build_dict(
            ROOMS = rooms,
            PERIODS = periods,
            TEACHERS = teachers,
            SUBJECTS = subjects,
            CLASSES = classes,
            GROUPS = groups,
            LESSONS = lessons,
            CARDS = cards.placements_aSc(),
        ),
        pretty = True
    )

    outpath = DATAPATH('tt_out.xml')
    with open(outpath, 'w', encoding = 'utf-8') as fh:
        fh.write(xml_aSc.replace('\t', '   '))
    print("\nTIMETABLE XML ->", outpath)
