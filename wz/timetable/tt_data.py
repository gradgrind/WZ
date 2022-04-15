"""
timetable/tt_data.py - last updated 2022-03-16

Prepare timetables input from the various sources ...

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

#TODO ...

_TEST = False
_TEST = True

WEIGHTS = [None, "50", "67", "80", "88", "93", "95", "97", "98", "99", "100"]

LUNCH_BREAK = ("mp", "Mittagspause")

_MAX_GAPS_PER_WEEK = 10 # maximum value for max. gaps per week (for classes)


### Messages

_LESSON_NO_GROUP = "Klasse {klass}, Fach {sid}: „Unterricht“ ohne Gruppe"
_LESSON_NO_TEACHER = (
    "Klasse {klass}, Fach {sid}: „Unterricht“ ohne"
    " Lehrer.\nDieser Unterricht wird NICHT im Stundenplan erscheinen."
)
_NO_LESSON_WITH_TAG = (
    "Tabelle der festen Stunden: Kennung {tag} hat keine"
    " entsprechenden Unterrichtsstunden"
)
_TAG_TOO_MANY_TIMES = (
    "Tabelle der festen Stunden: Kennung {tag} gibt"
    " mehr Zeiten an, als es dafür Unterrichtsstunden gibt"
)
_INVALID_CLASS_CONSTRAINT = (
    "Klasse {klass}: ungültige Wert für Bedingung {constraint}"
)
_UNKNOWN_CONSTRAINT = "Klassenbedingung „{name}“ unbekannt"
_MISSING_TEACHER_CONSTRAINT = "Lehrerbedingung „{key}“ wird nicht unterstützt"

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

from typing import NamedTuple, Dict, List, Set, FrozenSet, Tuple

### +++++

from itertools import product

import xmltodict

from timetable.tt_base import (
    Classes,
    TT_Days,
    TT_Periods,
    TT_Placements,
    TT_Rooms,
    TT_Subjects,
    TT_Teachers,
    TT_Error,
    class_group_split,
    LAST_LESSON,
    weight_value,
)

#from timetable.tt_process import Timetable

### -----

class Activity(NamedTuple):
    SID: str  # Subject-id
    GROUPS: FrozenSet[str]
    TIDS: Set[str]  # for timetable-clash checking,
    ROOMLISTS: List[List[str]]  # List of lists of possible room-ids
    LENGTH: int
    LIDX: Tuple[int,int]    # lesson index (0-based), subindex (1-based)
#?
    CONSTRAINTS: List[int]
# The associated constraints can be in an array, the entries in the list
# here would be indexes.


class Classes_data(Classes):
    __slots__ = (
        "activities",
        "constraints",
#        "time_constraints",
#        "space_constraints",
        "lid2aids",
        "class2sid2ag2aids",

        "periods_per_day",
        "periods_per_week",
        "teacher_placements",
        "room_placements",
        "group_placements",
    )

    def init(self):
#TODO: set up lessons, activities, constraints, etc.

#        self.periods_per_day: int = len(self.PERIODS)
#        self.periods_per_week: int = self.periods_per_day * len(self.daytags)

        ### Collect teacher constraints
        teacher_info = []
        warnings = set()

#######+
# Here is some code for using a single week-map for all teachers:
        # Build an initial week-map for the teachers including all their
        # blocked periods.
        # This can be deep-copied (!), or freshly generated, at the start
        # of a run.
        teacher_map = [
            [set() for p in self.PERIODS] for d in self.DAYS
        ]
        for tid in self.teacher_tags():
            d = 0
            for daylist in self.TEACHERS.available[tid]:
                p = 0
                for pok in daylist:
                    if not pok:
                        teacher_map[d][p].add(tid)
                    p += 1
                d += 1
        #print("§§§§§§teacher_map", teacher_map)
# Using day/period indexing is perhaps "neater" but it does require
# double indexing for each period, which will surely be somewhat
# inefficient.
# The alternative would be:
        teacher_map = tuple(
            set() for p in self.PERIODS for d in self.DAYS
        )
        for tid in self.teacher_tags():
            p = 0
            for daylist in self.TEACHERS.available[tid]:
                for pok in daylist:
                    if not pok:
                        teacher_map[p].add(tid)
                    p += 1
        print("§§§§§§teacher_map", teacher_map)
#######-

        for tid in self.teacher_tags():
            ## Period map for the teacher
# Would a single map for all teachers be "better"?
# Also a single group map would allow checks for groups' free periods ...
# There could be a map of activity lists to find which activities are in
# a period. Also the placements for each activity should be easily
# available – but separate from the fixed activity data.
            # Activity indexes start at 1, -1 is for a blocked period, 0
            # for an empty period.
            activities_map = []
            for daylist in self.TEACHERS.available[tid]:
                for p in daylist:
                    activities_map.append(0 if p else -1)
            #print("§§§§§§", tid, activities_map)

            ## Teacher's lunch breaks
            # For each period (or at least each possible lunch period)
            # there should be a list of other periods, such that one of
            # them needs to be free.
            lunch_map = tuple(set()
                for i in range(self.periods_per_week)
            )
            x = 0
            for daylist in self.TEACHERS.lunch_periods[tid]:
                for p in daylist:
                    lunch_map[x + p].update(x + i for i in daylist if i != p)
                x += self.periods_per_day

constraint_list = [Teacher_LUNCHBREAK(self, tid)]
cdata = self.TEACHERS.constraints[tid]
for key, val in cdata.items():
    if val:
        try:
            class_ = getattr(tt_process, f"Teacher_{key}")
        except AttributeError:
            if key not in warnings:
                REPORT("Warning",
                    _MISSING_TEACHER_CONSTRAINT.format(
                        key=key
                    )
                )
                warnings.add(key)
            continue
        constraint_list.append(class_(self, tid, val))
#print("§§§§§§", tid, constraint_list)
teacher_info.append((tid, activities_map, constraint_list))

            constraint_list = [(Timetable.teacher_constraint_LUNCHBREAK, lunch_map)]
            # The following constraint values are <None> or a
            # (number, weight) pair (integers, though the weight may be <None>)
            cdata = self.TEACHERS.constraints[tid]
            #print("§§§§§§", tid, cdata)
            for key, val in cdata.items():
                if val:
                    try:
                        func = getattr(Timetable, f"teacher_constraint_{key}")
                    except AttributeError:
                        if key not in warnings:
                            REPORT("Warning",
                                _MISSING_TEACHER_CONSTRAINT.format(
                                    key=key
                                )
                            )
                            warnings.add(key)
                        continue
                    constraint_list.append((func, val))
            #print("§§§§§§", tid, constraint_list)
            teacher_info.append((tid, activities_map, constraint_list))

##############################




        self.room_placements = tuple({}
            for i in range(self.periods_per_week)
        )
        self.group_placements = tuple({}
            for i in range(self.periods_per_week)
        )
        # Constraint: class not available. Add entries for the blocked
        # periods to the classes' week-programmes.
        for klass in sorted(self.available):
            daylist = self.available[klass]
            for ag in sorted(self.class_groups[klass]["*"]):
                i, x = 0, 0
                for d in self.daytags:
                    pblist = daylist[i]
                    i += 1
                    j = 0
                    for p in self.PERIODS:
                        if not pblist[j]:
                            self.group_placements[x][ag] = -1
                        j += 1
                        x += 1

#?
    def teacher_in_period(self, tid, day_period):
        return tid in self.teacher_placements[
            day_period[0] * self.periods_per_day + day_period[1]
        ]
# or ...
        return self.teacher_placements[
            day_period[0] * self.periods_per_day + day_period[1]
        ].get(tid)




    def next_activity_id(self):
        return len(self.activities) + 1

    def get_activities(self):
        """Build list of activities for timetable."""
#?
#        self.time_constraints = {}
#        self.space_constraints = {}

        self.activities: List[dict] = []  # fet activities
        # For constraints concerning relative placement of individual
        # lessons in the various subjects, collect the "atomic" pupil
        # groups and their activity ids for each subject, divided by class:
        self.class2sid2ag2aids: Dict[str,Dict[str,Dict[str,List[int]]]] = {}
        self.lid2aids: Dict[int, List[int]] = {}

        lesson_index: int = -1  # index of the current "lesson"
        for lesson in self.lesson_list:
            lesson_index += 1
            if lesson.BLOCK == "--":
                continue  # not a timetabled lesson
            sid: str = lesson.SID
            klass: str = lesson.CLASS
#?
            if not lesson.GROUPS:
                REPORT("WARNING", _LESSON_NO_GROUP.format(klass=klass, sid=sid))
                #continue
            if (not lesson.TIDS) and (not lesson.REALTIDS):
                REPORT(
                    "WARNING", _LESSON_NO_TEACHER.format(klass=klass, sid=sid)
                )
                continue

            ### Add room constraint(s) for lesson
            roomlists: List[List[str]] = []
            ignore_rooms: List[List[str]] = []
            if lesson.ROOMLIST:
                roomlists.append(lesson.ROOMLIST)
            try:
                for bc in self.block2courselist[lesson_index]:
                    _rlist = bc.ROOMLIST
                    if _rlist:
                        if _rlist[0] == "-":
                            ignore_rooms.append(_rlist[1:])
                        else:
                            roomlists.append(_rlist)
            except KeyError:
                # No additional rooms
                pass

            ### Generate the activity or activities
            # Split off possible "+" extension on subject id
            sid0 = sid.split("+", 1)[0]
            i = 0
            aids: List[int] = []
            self.lid2aids[lesson_index] = aids
            for d in lesson.LENGTHS:
                i += 1
                activity_id = self.next_activity_id()
                aids.append(activity_id)
                activity = Activity(
                    SID=sid0,
                    GROUPS=lesson.GROUPS,
                    TIDS=lesson.TIDS,
                    ROOMLISTS=roomlists,
                    LENGTH=d,
                    LIDX=(lesson_index, i),
                    CONSTRAINTS=[],
                )
                self.activities.append(activity)
                self.subject_group_activity(sid0, lesson.GROUPS, activity_id)

#TODO
# Checked before each allocation? But for the groups, not activities!
# If it is done for an activity placement, actually only the groups
# within the activity would need to be checked (assuming it is a 100%
# constraint).
# Could there be group constraints and class constraints?
    def lunch_breaks(self):
        """Add constraints for lunch breaks.
        There needs to be a lunch-break constraint for every sub-group of
        the class, to be on the safe side.
        """
        for klass in self.classes:
            try:
                weekdata = self.lunch_periods[klass]
            except KeyError:
                continue
            cn = self.new_constraint(
                GroupLunchBreak(
                    CLASS=klass,    # info only?
                    WEEKDATA=weekdata
                )
            )
            for g in self.class_groups[klass]["*"]:
                self.group_constraints[g].append(cn)

    def subject_group_activity(self, sid:str, groups:FrozenSet[str],
            activity_id:int) -> None:
        """Add the activity/groups to the collection for the appropriate
        class and subject.
        """
        aids: List[int]
        ag2aids: Dict[str,List[int]]
        sid2ag2aids: Dict[str,Dict[str,List[int]]]

        for group in groups:
            klass = group.split(".", 1)[0]
            try:
                sid2ag2aids = self.class2sid2ag2aids[klass]
            except KeyError:
                sid2ag2aids = {}
                self.class2sid2ag2aids[klass] = {sid: {group: [activity_id]}}
                continue
            try:
                ag2aids = sid2ag2aids[sid]
            except KeyError:
                ag2aids = {}
                sid2ag2aids[sid] = {group: [activity_id]}
                continue
            try:
                ag2aids[group].append(activity_id)
            except KeyError:
                ag2aids[group] = [activity_id]

    def constraint_day_separation(self):
        """Add constraints to ensure that multiple lessons in any subject
        are not placed on the same day.
        """
        constraints: List[dict] = []
        # Use <self.class2sid2ag2aids> to find activities.
        sid2ag2aids: Dict[str,Dict[str,List[int]]]
        ag2aids: Dict[str,List[int]]
        aids: List[int]
        aidset_map: Dict[int,Set[FrozenSet[int]]] = {}
        for klass in self.classes:
            try:
                sid2ag2aids = self.class2sid2ag2aids[klass]
            except KeyError:
                continue
            for sid, ag2aids in sid2ag2aids.items():
                for aids in ag2aids.values():
                    # Skip sets with only one element
                    l = len(aids)
                    if l > 1:
                        aids_fs = frozenset(aids)
                        try:
                            aidset_map[l].add(aids_fs)
                        except KeyError:
                            aidset_map[l] = {aids_fs}
        ### Eliminate subsets
        lengths = sorted(aidset_map, reverse=True)
        newsets = aidset_map[lengths[0]]   # the largest sets
        for l in lengths[1:]:
            xsets = set()
            for aidset in aidset_map[l]:
                for s in newsets:
                    if aidset < s:
                        break
                else:
                    xsets.add(aidset)
            newsets.update(xsets)
        ### Sort the sets
        aids_list = sorted([sorted(s) for s in newsets])
        for aids in aids_list:
            self.new_constraint(
#TODO: Rather a handler function? For Python maybe the indirection is better.
                "ActivitiesNotOnSameDay",
                aids
            )
# Maybe there are different NamedTuples for each constraint? The class
# could be passed?

#?
    def new_constraint(self, constraint:str, aids:List[int], **kargs):
        l = len(self.constraints)
        self.constraints.append((constraint, aids, kargs))
        for aid in aids:
            self.activities[aid].CONSTRAINTS.append(l)

    ############### FURTHER CONSTRAINTS ###############




# Add weighting (ignored here)?
# Evaluating this constraint should perhaps only be done when all lessons
# have been allocated?
    def constraints_MIN_PERIODS_DAILY(self, t_constraint):
        clist: List[dict] = []
#TODO: Get default from somewhere?
        default = "4"
        for klass in self.classes:
            try:
                n = self.class_constraints[klass]["MIN_PERIODS_DAILY"]
            except KeyError:
                # If the constraint is not present, don't add it for
                # this class
                continue
            if n:
                if n == '*':
                    n = default
                else:
                    try:
                        i = int(n)
                        if i < 1 or i > len(self.PERIODS):
                            raise ValueError
                    except ValueError:
                        REPORT("ERROR", _INVALID_CLASS_CONSTRAINT.format(
                                klass=klass, constraint=t_constraint))
                        return
                    n = str(i)
                clist.append(
                    {
                        "Weight_Percentage": "100", # necessary!
                        "Minimum_Hours_Daily": n,
                        "Students": klass,
                        "Allow_Empty_Days": "false",
                        "Active": "true",
                        "Comments": None,
                    }
                )
                #print(f"++ ConstraintStudentsSetMinHoursDaily {klass}: {n}")
        return "ConstraintStudentsSetMinHoursDaily", clist

# Also here, there is perhaps little point to evaluating this before all
# activities have been allocated.
    def constraints_MAX_GAPS_WEEKLY(self, t_constraint):
        """Maximum gaps per week for the specified classes.
        If the constraint is not specified for a class, that class will
        not have the constraint. The default value ("*") is "0" (no gaps).
        """
        clist: List[dict] = []
        for klass in self.classes:
            try:
                n = self.class_constraints[klass]["MAX_GAPS_WEEKLY"]
            except KeyError:
                # If the constraint is not present, don't add it for
                # this class
                continue
            if n:
                if n == '*':
                    # default is "0"
                    n = "0"
                else:
                    try:
                        i = int(n)
                        if i < 0 or i > _MAX_GAPS_PER_WEEK:
                            raise ValueError
                    except ValueError:
                        REPORT("ERROR", _INVALID_CLASS_CONSTRAINT.format(
                                klass=klass, constraint=t_constraint))
                        continue
                    n = str(i)
                clist.append(
                    {
                        "Weight_Percentage": "100", # necessary!
                        "Max_Gaps": n,
                        "Students": klass,
                        "Active": "true",
                        "Comments": None,
                    }
                )
                #print(f"++ ConstraintStudentsSetMaxGapsPerWeek {klass}: {n}")
        return "ConstraintStudentsSetMaxGapsPerWeek", clist

    def pair_constraint(self, klass, pairs, t_constraint) -> List[
            Tuple[Set[Tuple[int,int]],str]]:
        """Find pairs of activity ids of activities which link two
        subjects (subject tags) for a constraint.
        The returned pairs share at least one "atomic" group.
        The subject pairs are supplied as parameter <pairs>. There can
        be multiple pairs (space separated) and each pair can have a
        weighting (0-10) after a ":" separator, e.g. "En+Fr:8 Eu+Sp".
        The result is a list of pairs, (set of activity ids, fet-weighting).
        fet-weighting is a string in the range "0" to "100".
        """
        result: List[Tuple[Set[Tuple[int,int]],str]] = []
        sid2ag2aids = self.class2sid2ag2aids[klass]
        for wpair in pairs.split():
            try:
                pair, _w = wpair.split(":", 1)
            except ValueError:
                pair, w = wpair, 10
            else:
                try:
                    w = weight_value(_w)
                except ValueError:
                    REPORT("ERROR", _INVALID_CLASS_CONSTRAINT.format(
                            klass=klass, constraint=t_constraint))
                    return
            percent = WEIGHTS[w]
            if not percent:
                continue
            try:
                sid1, sid2 = pair.split("+")
            except ValueError:
                REPORT("ERROR", _INVALID_CLASS_CONSTRAINT.format(
                        klass=klass, constraint=t_constraint))
                return []
            try:
                ag2aids1 = sid2ag2aids[sid1]
                ag2aids2 = sid2ag2aids[sid2]
            except KeyError:
                continue
            aidpairs = set()
            for ag in ag2aids1:
                if ag in ag2aids2:
                    for aidpair in product(ag2aids1[ag], ag2aids2[ag]):
                        aidpairs.add(aidpair)
            result.append((aidpairs, percent))
        return result

    def constraints_NOT_AFTER(self, t_constraint):
        """Two subjects should NOT be in the given order, if on the same day."""
        aidmap: Dict[Tuple[str,str],] = {}
        for klass in self.classes:
            try:
                pairs = self.class_constraints[klass]["NOT_AFTER"]
            except KeyError:
                # If the constraint is not present, don't add it for
                # this class
                continue
            for aidpairs, percent in self.pair_constraint(klass, pairs,
                    t_constraint):
                for aidpair in aidpairs:
                    ap = (aidpair[1], aidpair[0])
                    if ap in aidmap:
                        if int(percent) <= int(aidmap[ap]):
                            continue
                    aidmap[ap] = percent
        clist: List[dict] = []
        for aidpair in sorted(aidmap):
            percent = aidmap[aidpair]
            clist.append(
                {
                    "Weight_Percentage": percent,
                    "First_Activity_Id": str(aidpair[0]),
                    "Second_Activity_Id": str(aidpair[1]),
                    "Active": "true",
                    "Comments": None,
                }
            )
            #a1 = self.activities[aidpair[0] - 1]["Subject"]
            #a2 = self.activities[aidpair[1] - 1]["Subject"]
            #print(f" ++ ConstraintTwoActivitiesOrderedIfSameDay:"
            #    f" {a1}/{aidpair[0]} {a2}/{aidpair[1]}")
        return "ConstraintTwoActivitiesOrderedIfSameDay", clist

    def constraints_PAIR_GAP(self, t_constraint):
        """Two subjects should have at least one lesson in between."""
        aidmap: Dict[Tuple[str,str],] = {}
        for klass in self.classes:
            try:
                pairs = self.class_constraints[klass]["PAIR_GAP"]
            except KeyError:
                # If the constraint is not present, don't add it for
                # this class
                continue
            for aidpairs, percent in self.pair_constraint(klass, pairs,
                    t_constraint):
                for aidpair in aidpairs:
                    # Order the pair elements
                    if aidpair[0] > aidpair[1]:
                        aidpair = (aidpair[1], aidpair[0])
                    if aidpair in aidmap:
                        if int(percent) <= int(aidmap[aidpair]):
                            continue
                    aidmap[aidpair] = percent
        clist: List[dict] = []
        for aidpair in sorted(aidmap):
            percent = aidmap[aidpair]
            clist.append(
                {
                    "Weight_Percentage": percent,
                    "Number_of_Activities": "2",
                    "Activity_Id": [str(a) for a in aidpair],
                    "MinGaps": "1",
                    "Active": "true",
                    "Comments": None,
                }
            )
            #a1 = self.activities[aidpair[0] - 1]["Subject"]
            #a2 = self.activities[aidpair[1] - 1]["Subject"]
            #print(f" ++ ConstraintMinGapsBetweenActivities:"
            #    f" {a1}/{aidpair[0]} {a2}/{aidpair[1]}")
        return "ConstraintMinGapsBetweenActivities", clist

    def add_class_constraints(self):
        """Add time constraints according to the "info" entries in the
        timetable data files for each class.
        """
        constraints: List[dict] = []
        # Get "local" names of constraints, call handlers
        for name, t_name in self.class_constraints['__INFO_NAMES__'].items():
            try:
                func = getattr(self, f"constraints_{name}")
            except AttributeError:
                raise TT_Error(_UNKNOWN_CONSTRAINT.format(name=name_t))
#TODO
            cname, clist = func(t_name)
            add_constraints(self.time_constraints, cname, clist)


class Placements_data(TT_Placements):
    def placements(self):
        days = self.classes.daytags
        ndays = str(len(days))
        periods = self.classes.periodtags
        nperiods = str(len(periods))
        lid2aids: Dict[int, List[str]] = self.classes.lid2aids
        constraints_parallel = []
        constraints_fixed = []
        constraints_multi = []
        constraints_l = []
        # print("\n*** Parallel tags ***")
        for tag, lids in self.classes.parallel_tags.items():
            # for i in lids:
            #    print(f"  {tag}: {i} --> {lid2aids[i]}")
            #    print(f"    ... {self.get_info(tag)}")
            weighting, places_list = self.get_info(tag)
            # What exactly the weighting applies to is not clear.
            # It could be the placement, or the parallel activities ...
            # I assume the placement(s), if there are any, otherwise
            # the parallel activities.
            w = WEIGHTS[weighting]
            # Collect tagged activities where there is no places list,
            # also where there are not enough places:
            excess = []
            for lid in lids:
                try:
                    aids = lid2aids[lid]
                except KeyError:
                    REPORT("WARN", _NO_LESSON_WITH_TAG.format(tag=tag))
                    continue
                i = 0
                for d, p in places_list:
                    try:
                        aid = aids[i]
                    except IndexError:
                        REPORT("ERROR", _TAG_TOO_MANY_TIMES.format(tag=tag))
                        continue
                    i += 1
                    if p == LAST_LESSON:
                        constraints_l.append(
                            {
                                "Weight_Percentage": "100",  # necessary!
                                "Activity_Id": aid,
                                "Active": "true",
                                "Comments": None,
                            }
                        )
                        if d < 0:
                            # Any day, no further constraint is needed
                            continue
                        else:
                            # A constraint to fix the day is needed
                            p = -2
                    if p < 0:
                        # Fix the day (any period)
                        xd = days[d]
                        constraints_multi.append(
                            {
                                "Weight_Percentage": w,
                                "Activity_Id": aid,
                                "Number_of_Preferred_Starting_Times": nperiods,
                                "Preferred_Starting_Time": [
                                    {
                                        "Preferred_Starting_Day": xd,
                                        "Preferred_Starting_Hour": xp,
                                    }
                                    for xp in periods
                                ],
                                "Active": "true",
                                "Comments": None,
                            }
                        )
                    elif d < 0:
                        # Fix the period (any day)
                        xp = periods[p]
                        constraints_multi.append(
                            {
                                "Weight_Percentage": w,
                                "Activity_Id": aid,
                                "Number_of_Preferred_Starting_Times": ndays,
                                "Preferred_Starting_Time": [
                                    {
                                        "Preferred_Starting_Day": xd,
                                        "Preferred_Starting_Hour": xp,
                                    }
                                    for xd in days
                                ],
                                "Active": "true",
                                "Comments": None,
                            }
                        )
                    else:
                        # Fix day and period
                        constraints_fixed.append(
                            {
                                "Weight_Percentage": w,
                                "Activity_Id": aid,
                                "Preferred_Day": days[d],
                                "Preferred_Hour": periods[p],
                                "Permanently_Locked": "true",
                                "Active": "true",
                                "Comments": None,
                            }
                        )
                excess.append(aids[i:])
            # Only those lists containing more than one list are
            # interesting for parallel activities.
            # Others may be used for special placement rules ...
            if len(excess) > 1:
                # Check that all lists are of equal length
                l = len(excess[0])
                for e in excess[1:]:
                    if len(e) != l:
                        raise Bug("Mismatch in parallel tag lists, tag = {tag}")
                excess_n = str(len(excess))
                for i in range(l):
                    parallel = [e[i] for e in excess]
                    constraints_parallel.append(
                        {
                            "Weight_Percentage": w,
                            "Number_of_Activities": excess_n,
                            "Activity_Id": parallel,
                            "Active": "true",
                            "Comments": None,
                        }
                    )
        time_constraints = self.classes.time_constraints
        add_constraints(
            time_constraints,
            "ConstraintActivityPreferredStartingTime",
            constraints_fixed,
        )
        add_constraints(
            time_constraints,
            "ConstraintActivitiesSameStartingTime",
            constraints_parallel,
        )
        add_constraints(
            time_constraints,
            "ConstraintActivityPreferredStartingTimes",
            constraints_multi,
        )
        add_constraints(
            time_constraints, "ConstraintActivityEndsStudentsDay", constraints_l
        )


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    if _TEST:
        print("\n ********** READ LESSON DATA **********\n")
    classes = Classes_data()

    classes.init()

    print("\nBLOCKED PERIODS", classes.group_placements)

    # Generate the activities
    classes.get_activities()

    c_list = classes.classes
    print("\n ... read data for:", c_list)

    # Fixed placements for activities
    cards = Placements_fet(classes)
    cards.placements()

    classes.lunch_breaks()

    if _TEST:
        print("\nSubject – activity mapping")
        for klass in classes.classes:
            if klass.startswith("XX"):
                continue
            print(f"\n **** Class {klass}")
            for sid, ag2aids in classes.class2sid2ag2aids[klass].items():
                for ag, aids in ag2aids.items():
                    print(f"     {sid:8}: {ag:10} --> {aids}")

    print("\nSubject day-separation constraints ...")
    classes.constraint_day_separation()

    print("\nClass constraints ...")
    classes.add_class_constraints()

    # Activity info is available thus:
    for _aid in (550,):
        print(f"\n???? {_aid}:", classes.activities[_aid - 1])

    # quit(0)

    outdir = DATAPATH("TIMETABLE/out")
    os.makedirs(outdir, exist_ok=True)

    # Check-lists for teachers
    tcl = classes.teacher_check_list()
    from timetable.tt_check_list import teacher_class_subjects

    pdfbytes = teacher_class_subjects(tcl)
    pdffile = os.path.join(outdir, f"Lehrer-Stunden-Kontrolle_{SCHOOLYEAR}.pdf")
    with open(pdffile, "wb") as fh:
        fh.write(pdfbytes)
    print("\nTEACHER CHECK-LIST ->", pdffile)

    quit(0)



    days = TT_Days()

    if __TEST:
        print("\n*** DAYS ***")
        for _day in days:
            print("   ", _day)

    periods = TT_Periods()
    if __TEST:
        print("\n*** PERIODS ***")
        for _period in periods:
            print("   ", _period)

    rooms = TT_Rooms()

    subjects = TT_Subjects()
    if __TEST:
        print("\nSUBJECTS:")
        for sdata in subjects:
            print("   ", sdata)

    teachers = Teachers_data(days, periods)

    if __TEST:
        print("\n ********** READ LESSON DATA **********\n")
    _classes = Classes_data(
        days, periods, SUBJECTS=subjects, ROOMS=rooms, TEACHERS=teachers
    )

    # Generate the fet activities
    _classes.get_lessons()

    c_list = _classes.classes
    print("\n ... read data for:", c_list)

    if __TEST:
        print("\nROOMS:")
        for rdata in _classes.fet_rooms:
            print("   ", rdata)

    #quit(0)

    if __TEST:
        print("\nTEACHERS:")
    teachers = _teachers.get_teachers(_classes)
    _teachers.add_constraints()
    if __TEST:
        for tdata in teachers:
            print("   ", tdata)
    # TODO:
    #        print("\nLONG TAGS:\n", _teachers.longtag.values())

    outdir = DATAPATH("TIMETABLE/out")
    os.makedirs(outdir, exist_ok=True)

    # Check-lists for teachers
    tcl = _classes.teacher_check_list()
    from timetable.tt_check_list import teacher_class_subjects

    pdfbytes = teacher_class_subjects(tcl)
    pdffile = os.path.join(outdir, f"Lehrer-Stunden-Kontrolle_{SCHOOLYEAR}.pdf")
    with open(pdffile, "wb") as fh:
        fh.write(pdfbytes)
    print("\nTEACHER CHECK-LIST ->", pdffile)

    classes = []
    for klass in c_list:
        if klass.startswith("XX"):
            continue
        class_data = _classes.class_data(klass)
        classes.append(class_data)
        if __TEST:
            print(f"\nfet-CLASS {klass}")
            for g in class_data.get("Group") or []:
                print("  ---", g["Name"])
                for sg in g.get("Subgroup") or []:
                    print("     +", sg["Name"])

    activities, s_constraints, t_constraints = (
        _classes.activities,
        _classes.space_constraints,
        _classes.time_constraints,
    )
    if __TEST:
        print("\n ********* fet LESSONS *********\n")
        ## for l, data in _classes.lessons.items():
        ##    print(f"   {l}:", data)
        #for l in activities:
        #    print("   ", l)
        #print("\n  ======================================================\n")

    # Classes' not-available times
    _classes.constraint_blocked_periods()

    # Fixed placements for activities
    cards = Placements_fet(_classes, _days, _periods)
    cards.placements()

    _classes.lunch_breaks()

    print("\nBuild subject – activity mapping")

    for klass in _classes.classes:
        if klass.startswith("XX"):
            continue
        print(f"\n **** Class {klass}")
        for sid, ag2aids in _classes.class2sid2ag2aids[klass].items():
            for ag, aids in ag2aids.items():
                print(f"     {sid:8}: {ag:10} --> {aids}")

    print("\nSubject day-separation constraints ...")
    _classes.constraint_day_separation()

    print("\nClass constraints ...")
    _classes.add_class_constraints()

    # Activity info is available thus:
    for _aid in (550,):
        print(f"\n???? {_aid}:", _classes.activities[_aid - 1])
