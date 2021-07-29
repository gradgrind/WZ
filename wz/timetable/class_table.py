# -*- coding: utf-8 -*-

"""
TT/class_table.py - last updated 2021-07-28

Manage a grid of lessons for a school-class

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

#TODO ... read the lessons from the basic data and show a class in a grid.

__TEST = False
__TEST = True

### Messages


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

import xmltodict

from timetable.grid_periods_days import gui_setup
from timetable.tt_data import Classes, Days, Periods, Placements, Rooms, \
        Subjects, Teachers, TT_Error, get_duration_map

### -----


class Classes_TT(Classes):
    def class_timeoff(self, daymap):
        """Return a "timeoff" entry for the given <daymap> (value for
        a class from <self.class_days_periods>.
        """
        weektags = []
        for day in self.days:
            dayperiods = daymap[day]
            daytags = []
            for p in self.periods:
                daytags.append('1' if dayperiods[p] else '0')
            weektags.append(''.join(daytags))
        return ','.join(weektags)
#
#asc:
    def groups(self, klass):
        """Return a list of aSc group definitions for the given class.
        """
        group_list = []
        gi = 0 # "division" number (a list of mutually exclusive sub-groups)
        for division in self.class_divisions[klass]:
            for g in division:
                if g == '*':
                    g = _WHOLE_CLASS
                group_list.append(
                    {   '@id': idsub(f'{klass}-{g}'),
                        '@classid': klass,
                        '@name': g,
                        '@entireclass': '1' if len(division) == 1 else '0',
                        '@divisiontag': str(gi),
                    }
                )
            gi += 1
        return group_list
#
#asc:
    def class_data(self, klass):
        """Return the aSc record for the given class.
        """
        return {
            '@id': klass, '@short': klass,
            '@name': self.class_name[klass],
            '@classroomids': ','.join(self.classrooms[klass]),
            '@timeoff': self.class_days(klass)
        }
#
#asc:
#TODO: adapt for my grid display.
# The tiles could be generated "on demand", i.e. when they need to be
# displayed. That is probably easiest using a class instance for a
# lesson.
    def get_lessons(self):
        lesson_list = []
        for tag, data in self.lessons.items():
            block = data['block']
            if block and block != '*':
                continue
            sid = data['SID']
#TODO: For each class involved make separate tiles?
# A big question is, whether it is possible to handle source changes ...
# I think almost certainly not "dynamically". What might work is restarting
# from scratch and importing a set of placements. Those that match in
# classes, groups, subject, duration, teachers and rooms can be
# accepted.
# That would require a matching function, maybe a dictionary using keys
# based on the above info (as tuple or string).
            classes = ','.join(sorted(data['CLASSES']))
            groups = ','.join([idsub(g) for g in sorted(data['GROUPS'])])
#TODO: Nasty bodge – think of some better way of doing this:
            if sid == 'Hu' and block == '*':
                tids = ''
            else:
                tids = ','.join(sorted(data['TIDS']))
            rooms = ','.join(sorted(data['ROOMS']))
            durations = data['durations']
            if durations:
                _, dmap = get_duration_map(durations)
                tags = []
                for d, n in dmap.items():
                    t = f'{tag}__{d}' if len(dmap) > 1 else tag
                    tags.append((t, d, n))
#TODO: check use of tags for placement, etc.!
                if len(tags) > 1:
                    print("&&& multitags:", tags)
                for tag, d, n in tags:
                    lesson = {
                        '@id': tag,
                        '@classids': classes,
                        '@subjectid': sid,
                        '@groupids': groups,
                        '@teacherids': tids,
                        '@durationperiods': str(d),
                        # Note that the number of periods in aSc means the
                        # number of _single_ periods:
                        '@periodsperweek': str(n * d),
                        '@classroomids': rooms
                    }
                    lesson_list.append(lesson)
        return lesson_list

##########

class Teachers_TT(Teachers):
    def get_blocked_periods(self, tid):
        """Return the blocked periods.
        """
        dlist = self.blocked_periods.get(tid)
        if not dlist:
            return ''
        week_list = []
        for pblist in dlist:
            blist = [self.NO if b else self.YES for b in pblist]
            week_list.append(''.join(blist))
        return ','.join(week_list)
#
#asc:
    def get_teachers(self):
        return [
            {   '@id': tid,
                '@short': tid,
                '@name': name,
                '@timeoff': self.get_blocked_periods(tid)
            } for tid, name in self.items()
        ]

###

class Rooms_aSc(Rooms):
    def get_rooms(self):
        return [{'@id': rid, '@short': rid, '@name': name}
                for rid, name in self.items()]

###

class Subjects_aSc(Subjects):
    def get_subjects(self):
        sbj_list = []
        sbj_tag = {}
        for sid, name in self.items():
            _sid = idsub(sid)
            try:
                sid0 = sbj_tag[_sid]
            except:
                sbj_tag[_sid] = sid
                sbj_list.append({'@id': _sid, '@short': sid, '@name': name})
            else:
                raise TT_Error(_DUPLICATE_TAG.format(
                        tag = _sid, key = self.tfield['SID'],
                        source1 = sid0, source2 = sid))
        return sbj_list

########################################################################


class Placements_aSc(Placements):
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


###

class Lesson:
#TODO
# Need a separate tile for each class and each duration.
# ... though if only one class is shown at a time, in principle the same
# tile could be used in various classes ... but that might be confusing,
# and wouldn't work in a multiclass view.
    def __init__(self, tag, data):
        """Manage the tiles, etc., associated with this (group of) lessons.

        """
        self.tag = tag
        self.basedata = data
        self.sublessons = []
        for d in durations:
            self.sublessons.append(Sublesson(self, d))
        """
                self.lessons[tag] = {
                    'CLASSES': {klass},
                    'GROUPS': _groups.copy(),
                    'SID': sid,
                    'TIDS': teachers,
                    'ROOMS': rooms,
                    'durations': durations,
                    'block': block      # or block-tag components
                }
        """

class Sublesson:
    """
    """
    def __init__(self, lesson, d):
        pass


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    import sys
#    app, window, grid = gui_setup(sys.argv)
#    sys.exit(app.exec())
#    quit(0)


    _days = Days()
    _periods = Periods()
    _classes = Classes_TT(_periods)
    if _classes.days != list(_days):
        print("\nDAYS MISMATCH:", _classes.days, "\n", list(_days))
        quit(1)
    _teachers = Teachers_TT(_classes.days, _periods)
    _rooms = Rooms()
    _subjects = Subjects()
    c_list = _classes.all_lessons(SUBJECTS = _subjects, ROOMS = _rooms,
            TEACHERS = _teachers)
    print("\n ... read data for:", c_list)



    if __TEST:
        print("\n*** DAYS ***")
        for _day in _days:
            print('   ', f"'{_days.get_id(_day)}'", _days[_day])
        print("\n  ==================================================")

    if __TEST:
        print("\n*** PERIODS ***")
        for _pkey in _periods:
            print('   ', f"'{_periods.get_id(_pkey)}'", _periods[_pkey])
        print("\n  ==================================================")

    if __TEST:
        print("\n*** CLASS-DAYS ***")
        for klass, daymap in _classes.class_days_periods.items():
            print(f"   class {klass:4}:", _classes.class_timeoff(daymap))
        print("\n  ==================================================")

    if __TEST:
        print("\nTEACHERS:")
        for tid, tname in _teachers.items():
            blocked = _teachers.get_blocked_periods(tid) or '–––'
            alphatag = _teachers.alphatag[tid]
            print(f"   {tid:4} : {tname:20} ({alphatag})")
            print(f"       {blocked}")

    if __TEST:
        print("\nROOMS:")
        for rid, name in _rooms.items():
            print(f"   {rid:8}: {name}")

    if __TEST:
        print("\nSUBJECTS:")
        for sid, name in _subjects.items():
            print(f"   {sid:8}: {name}")

    if __TEST:
        print("\n ********** LESSON DATA **********\n")

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
    outpath = os.path.join(outdir, 'teacher_check2.txt')
    with open(outpath, 'w', encoding = 'utf-8') as fh:
        fh.write("STUNDENPLAN 2021/22: Lehrer-Stunden\n"
                "===================================\n")
        fh.write(_classes.teacher_check_list2())
    print("\nTEACHER CHECK-LIST ->", outpath)


#    classes = []
#    groups = []
#    for klass in c_list:
#        classes.append(_classes.class_data(klass))
#        groups += _classes.groups(klass)
#    if __TEST:
#        print("\n ********** aSc DATA **********")
#        print("\n  aSc-CLASSES:", classes)
#        print("\n  aSc-GROUPS:", groups)

#    lessons = _classes.get_lessons()
    if __TEST:
        print("\n ********* LESSONS *********\n")
        for l, data in _classes.lessons.items():
            print(f"   {l}:", data)
#        for l in lessons:
#            print("   ", l)
        print("\n  ======================================================\n")

    quit(0)

    cards = Placements_aSc(_classes.lessons)
    if __TEST:
        print("\n ********* FIXED LESSONS *********\n")
        #for l, data in _classes.lessons.items():
        #    print(f"   {l}:", data)
        for card in cards.placements_aSc():
            print("   ", card)

    xml_aSc = xmltodict.unparse(build_dict(
            ROOMS = classrooms,
            PERIODS = periods,
            TEACHERS = teachers,
            SUBJECTS = subjects,
            CLASSES = classes,
            GROUPS = groups,
            LESSONS = lessons,
            CARDS = cards.placements(),
        ),
        pretty = True
    )

    outpath = os.path.join(outdir, 'tt_out.xml')
    with open(outpath, 'w', encoding = 'utf-8') as fh:
        fh.write(xml_aSc.replace('\t', '   '))
    print("\nTIMETABLE XML ->", outpath)
