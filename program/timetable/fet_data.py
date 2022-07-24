"""
timetable/fet_data.py - last updated 2022-07-24

Prepare fet-timetables input from the database ...

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

_TEST = False
_TEST = True

FET_VERSION = "6.2.7"

WEIGHTS = [None, "50", "67", "80", "88", "93", "95", "97", "98", "99", "100"]

#TODO: T ...
LUNCH_BREAK = ("mp", "Mittagspause")

_MAX_GAPS_PER_WEEK = 10  # maximum value for max. gaps per week (for classes)


### Messages

#TODO ...
_LESSON_NO_GROUP = "Klasse {klass}, Fach {sid}: „Unterricht“ ohne Gruppe"
_LESSON_NO_TEACHER = (
    "Klasse {klass}, Fach {sid}: „Unterricht“ ohne"
    " Lehrer.\nDieser Unterricht wird NICHT im Stundenplan erscheinen."
)
# _SUBJECT_PAIR_INVALID = (
#    "Ungültiges Fach-Paar ({item}) unter den „weiteren Bedingungen“"
# )
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
    start.setup(os.path.join(basedir, "DATA-2023"))

from typing import Dict, List, Set, FrozenSet, Tuple

### +++++

from itertools import product

import xmltodict

from core.basic_data import (
    get_days,
    get_periods,
    get_classes,
    get_teachers,
    get_subjects,
    get_rooms,
    sublessons,
    timeslot2index,
)
from timetable.activities import Courses


### -----


def get_days_fet() -> list[dict[str,str]]:
    return [{"Name": d[0]} for d in get_days()]



class Classes_fet:#(Classes):
    __slots__ = (
        "activities",
        "__virtual_room_map",
        "__virtual_rooms",
        "time_constraints",
        "space_constraints",
        "lid2aids",
        "class2sid2ag2aids",
    )




    def gen_fetdata(self):
        # Build an ordered list of fet elements for the days
        fet_days = [{"Name": d.short} for d in self.DAYS]
        if _TEST:
            print("\n*** DAYS ***")
            for _day in self.DAYS:
                print("   ", _day)
            print("\n    ... for fet ...\n   ", fet_days)
            print("\n  ==================================================")

        # Build an ordered list of fet elements for the periods
        fet_periods = [{"Name": p.short} for p in self.PERIODS]
        if _TEST:
            print("\n*** PERIODS ***")
            for _period in self.PERIODS:
                print("   ", _period)
            print("\n    ... for fet ...\n   ", fet_periods)
            print("\n  ==================================================")

        # Build an ordered list of fet elements for the rooms
        fet_rooms = [
            {
                "Name": rid,
                "Building": None,
                "Capacity": "30000",
                "Virtual": "false",
                "Comments": self.ROOMS[rid],
            }
            for rid in sorted(self.ROOMS)
        ]
        fet_rooms += self.__virtual_rooms.values()
        if _TEST:
            print("\nROOMS:")
            for rdata in fet_rooms:
                print("   ", rdata)

        fet_subjects = [
            {"Name": sid, "Comments": name}
            for sid, name in self.SUBJECTS.items()
        ]
        fet_subjects.append(
            {"Name": LUNCH_BREAK[0], "Comments": LUNCH_BREAK[1]}
        )
        if _TEST:
            print("\nSUBJECTS:")
            for sdata in fet_subjects:
                print("   ", sdata)

        fet_teachers: List[dict] = []
        for tid in self.teacher_tags():
            fet_teachers.append(
                {
                    "Name": tid,
                    "Target_Number_of_Hours": "0",
                    "Qualified_Subjects": None,
                    "Comments": self.TEACHERS[tid],
                }
            )
        if _TEST:
            print("\nTEACHERS:")
            for tdata in fet_teachers:
                print("   ", tdata)
        fet_classes = []
        if _TEST:
            print("\nCLASSES:")
        for klass in self.classes:
            if klass.startswith("XX"):
                continue
            class_data = self.class_data(klass)
            fet_classes.append(class_data)
            if _TEST:
                print(f"\nfet-CLASS {klass}")
                for g in class_data.get("Group") or []:
                    print("  ---", g["Name"])
                    for sg in g.get("Subgroup") or []:
                        print("     +", sg["Name"])

        fet_dict = {
            "@version": f"{FET_VERSION}",
            "Mode": "Official",
            "Institution_Name": f"{CONFIG['SCHOOL_NAME']}",
            "Comments": "Default comments",
            "Days_List": {
                "Number_of_Days": f"{len(fet_days)}",
                "Day": fet_days,
            },
            "Hours_List": {
                "Number_of_Hours": f"{len(fet_periods)}",
                "Hour": fet_periods,
            },
            "Subjects_List": {"Subject": fet_subjects},
            "Activity_Tags_List": None,
            "Teachers_List": {"Teacher": fet_teachers},
            "Students_List": {"Year": fet_classes},
            "Activities_List": {"Activity": self.activities},
            "Buildings_List": None,
            "Rooms_List": {"Room": fet_rooms},
        }
        tc_dict = {
            "ConstraintBasicCompulsoryTime": {
                "Weight_Percentage": "100",
                "Active": "true",
                "Comments": None,
            }
        }
        sc_dict = {
            "ConstraintBasicCompulsorySpace": {
                "Weight_Percentage": "100",
                "Active": "true",
                "Comments": None,
            }
        }
        tc_dict.update(self.time_constraints)
        sc_dict.update(self.space_constraints)
        fet_dict["Time_Constraints_List"] = tc_dict
        fet_dict["Space_Constraints_List"] = sc_dict
        return {"fet": fet_dict}

    def class_data(self, klass):
        """Return a fet students_list/year entry for the given class."""
        class_groups = self.class_groups[klass]
        division = self.atomics_lists[klass]
        # Try with just 0 or 1 category.
        # The groups are all the "elemental" groups plus any dotted groups
        # which are used and not "atomic" groups already defined as subgroups.
        year_entry = {
            "Name": klass,
            # TODO: long name?
            "Number_of_Students": "0",
            "Comments": None,  # '1. Großklasse'. etc.?
            "Number_of_Categories": "1" if division else "0",
            "Separator": ".",
        }
        if division:
            _groups = []
            _agset = set()
            for g in sorted(class_groups):
                sgs = class_groups[g]
                if g == "*":
                    continue
                g = f"{klass}.{g}"
                if g in sgs:
                    # This group is an atomic group
                    if g not in _agset:
                        _agset.add(g)
                        _groups.append(
                            {
                                "Name": g,
                                "Number_of_Students": "0",
                                "Comments": None,
                            }
                        )
                else:
                    _agset.update(sgs)
                    _subgroups = [
                        {
                            "Name": sg,
                            "Number_of_Students": "0",
                            "Comments": None,
                        }
                        for sg in sorted(sgs)
                    ]
                    _groups.append(
                        {
                            "Name": g,
                            "Number_of_Students": "0",
                            "Comments": None,
                            "Subgroup": _subgroups,
                        }
                    )
            year_entry["Category"] = {
                "Number_of_Divisions": f"{len(division)}",
                "Division": division,
            }
            year_entry["Group"] = _groups
        return year_entry

    def constraint_blocked_periods(self):
        """Constraint: students set not available ..."""
        constraints = []
        for klass, daylist in self.available.items():
            tlist = []
            i = 0
            for d in self.daytags:
                pblist = daylist[i]
                i += 1
                j = 0
                for p in self.periodtags:
                    if not pblist[j]:
                        tlist.append({"Day": d, "Hour": p})
                    j += 1
            if tlist:
                constraints.append(
                    {
                        "Weight_Percentage": "100",
                        "Students": klass,
                        "Number_of_Not_Available_Times": str(len(tlist)),
                        "Not_Available_Time": tlist,
                        "Active": "true",
                        "Comments": None,
                    }
                )
        add_constraints(
            self.time_constraints,
            "ConstraintStudentsSetNotAvailableTimes",
            constraints,
        )

    def virtual_room(self, roomlists: List[List[str]]) -> str:
        """Return a virtual room id for the given list of room lists.
        These virtual rooms are cached so that they can be reused, should
        the <roomlists> argument be repeated.
        """
        # First need a hashable representation of <roomlists>, use a string.
        hashable = "&".join(["|".join(rooms) for rooms in roomlists])
        # print("???????", hashable)
        try:
            return self.__virtual_room_map[hashable]
        except KeyError:
            pass
        # Construct a new virtual room
        name = f"v{len(self.__virtual_rooms) + 1:03}"
        roomlist = []
        for rooms in roomlists:
            nrooms = len(rooms)
            roomlist.append(
                {
                    "Number_of_Real_Rooms": str(nrooms),
                    "Real_Room": rooms[0] if nrooms == 1 else rooms,
                }
            )
        self.__virtual_rooms[name] = {
            "Name": name,
            "Building": None,
            "Capacity": "30000",
            "Virtual": "true",
            "Number_of_Sets_of_Real_Rooms": str(len(roomlists)),
            "Set_of_Real_Rooms": roomlist,
            "Comments": None,
        }
        self.__virtual_room_map[hashable] = name
        return name

    def next_activity_id(self):
        return len(self.activities) + 1

    def get_lessons(self):
        """Build list of lessons for fet-timetables."""

        def make_room_constraint(aid: int, rlist: List[str]) -> None:
            """Make a room constraint for the given activity id and room
            list.
            """
            n = len(rlist)
            if n > 1:
                r_c = "ConstraintActivityPreferredRooms"
                s_c = {
                    "Weight_Percentage": "100",
                    "Activity_Id": str(aid),
                    "Number_of_Preferred_Rooms": str(n),
                    "Preferred_Room": rlist,
                    "Active": "true",
                    "Comments": None,
                }
            elif n == 1:
                r_c = "ConstraintActivityPreferredRoom"
                s_c = {
                    "Weight_Percentage": "100",
                    "Activity_Id": str(aid),
                    "Room": rlist[0],
                    "Permanently_Locked": "true",
                    "Active": "true",
                    "Comments": None,
                }
            else:
                raise Bug("No room(s) passed to 'make_room_constraint'")
            add_constraints(self.space_constraints, r_c, [s_c])

        self.time_constraints = {}
        self.space_constraints = {}
        self.activities: List[dict] = []  # fet activities
        # Used for managing "virtual" rooms:
        self.__virtual_room_map: Dict[str, str] = {}  # rooms hash -> room id
        self.__virtual_rooms: Dict[str, dict] = {}  # room id -> fet room
        # For constraints concerning relative placement of individual
        # lessons in the various subjects, collect the "atomic" pupil
        # groups and their activity ids for each subject, divided by class:
        self.class2sid2ag2aids: Dict[str, Dict[str, Dict[str, List[int]]]] = {}
        self.lid2aids: Dict[int, List[int]] = {}

        lesson_index: int = -1  # index of the current "lesson"
        for lesson in self.lesson_list:
            lesson_index += 1
            if lesson.BLOCK == "--":
                continue  # not a timetabled lesson
            sid: str = lesson.SID
            klass: str = lesson.CLASS
            groups: FrozenSet[str] = lesson.GROUPS
            activity_groups: List[str]
            if groups:
                # "Simplify" the groups, building a list of groups
                activity_groups = sorted(self.combine_atomic_groups(groups))
                # print("*****", groups, "-->", activity_groups)
            else:
                REPORT("WARNING", _LESSON_NO_GROUP.format(klass=klass, sid=sid))
                activity_groups = []

            tids = sorted(lesson.TIDS)
            if (not tids) and (not lesson.REALTIDS):
                REPORT(
                    "WARNING", _LESSON_NO_TEACHER.format(klass=klass, sid=sid)
                )
                continue

            ### Add room constraint(s) for lesson
            # Keep it as simple as possible. I don't think fet has list-
            # order prioritization, so don't even try. Some post-processing
            # may be able to improve the situation, otherwise manual
            # editing will be necessary.
            rooms: List[str]
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
            if len(roomlists) == 1:
                rooms = roomlists[0]
            elif len(roomlists) > 1:
                rooms = [self.virtual_room(roomlists)]
            else:
                rooms = []

            ### Generate the activity or activities
            if tids:
                if len(tids) == 1:
                    activity0 = {"Teacher": tids[0]}
                else:
                    activity0 = {"Teacher": tids}
            else:
                activity0 = {}
            if activity_groups:
                activity0["Students"] = (
                    activity_groups[0]
                    if len(activity_groups) == 1
                    else activity_groups
                )
            # Split off possible "+" extension on subject id
            sid0 = sid.split("+", 1)[0]
            activity0["Subject"] = sid0
            activity0["Activity_Group_Id"] = "0"
            activity0["Active"] = "true"
            durations: List[int] = lesson.LENGTHS
            if len(durations) == 1:
                d = durations[0]
                dstr = str(d)
                activity_id = self.next_activity_id()
                self.lid2aids[lesson_index] = [activity_id]
                activity0.update(
                    {
                        "Duration": dstr,
                        "Total_Duration": dstr,
                        "Id": str(activity_id),
                        "Comments": f"{lesson_index}",
                    }
                )
                self.activities.append(activity0)
                if rooms:
                    make_room_constraint(activity_id, rooms)
                self.subject_group_activity(sid0, groups, activity_id)
            else:
                i = 0
                aids: List[int] = []
                self.lid2aids[lesson_index] = aids
                for d in durations:
                    i += 1
                    dstr = str(d)
                    activity_id = self.next_activity_id()
                    aids.append(activity_id)
                    activity = activity0.copy()
                    activity.update(
                        {
                            "Duration": dstr,
                            "Total_Duration": dstr,
                            "Id": str(activity_id),
                            "Comments": f"{lesson_index}.{i}",
                        }
                    )
                    self.activities.append(activity)
                    if rooms:
                        make_room_constraint(activity_id, rooms)
                    self.subject_group_activity(sid0, groups, activity_id)

    def lunch_breaks(self):
        """Add activities and constraints for lunch breaks.
        There needs to be a lunch-break activity for every sub-group of
        the class, to be on the safe side.
        """
        constraints = []
        for klass in self.classes:
            try:
                weekdata = self.lunch_periods[klass]
            except KeyError:
                continue
            atomic_groups = self.class_groups[klass]["*"]
            groupsets = self.groupsets_class[klass]
            # print(f"??? {klass}", atomic_groups)
            d = -1
            for periods in weekdata:
                d += 1
                if periods:
                    nperiods = str(len(periods))
                    day = self.daytags[d]
                    # print(f"LUNCH {klass}, {day}: {periods}")
                    # Add lunch-break activity
                    for g in atomic_groups:
                        aid_s = str(self.next_activity_id())
                        activity = {
                            # "Teacher": {},
                            "Subject": LUNCH_BREAK[0],
                            "Students": groupsets.get(frozenset([g])) or g,
                            "Duration": "1",
                            "Total_Duration": "1",
                            "Id": aid_s,
                            "Activity_Group_Id": "0",
                            "Active": "true",
                            "Comments": None,
                        }
                        self.activities.append(activity)
                        # Add constraint
                        constraints.append(
                            {
                                "Weight_Percentage": "100",
                                "Activity_Id": aid_s,
                                "Number_of_Preferred_Starting_Times": nperiods,
                                "Preferred_Starting_Time": [
                                    {
                                        "Preferred_Starting_Day": day,
                                        "Preferred_Starting_Hour": self.periodtags[
                                            p
                                        ],
                                    }
                                    for p in periods
                                ],
                                "Active": "true",
                                "Comments": None,
                            }
                        )
        add_constraints(
            self.time_constraints,
            "ConstraintActivityPreferredStartingTimes",
            constraints,
        )

    def subject_group_activity(
        self, sid: str, groups: FrozenSet[str], activity_id: int
    ) -> None:
        """Add the activity/groups to the collection for the appropriate
        class and subject.
        """
        aids: List[int]
        ag2aids: Dict[str, List[int]]
        sid2ag2aids: Dict[str, Dict[str, List[int]]]

        for group in groups:
            klass, _ = class_group_split(group)
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
        sid2ag2aids: Dict[str, Dict[str, List[int]]]
        ag2aids: Dict[str, List[int]]
        aids: List[int]
        aidset_map: Dict[int, Set[FrozenSet[int]]] = {}
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
        newsets = aidset_map[lengths[0]]  # the largest sets
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
            constraints.append(
                {
                    "Weight_Percentage": "100",
                    "Consecutive_If_Same_Day": "true",
                    "Number_of_Activities": str(len(aids)),
                    "Activity_Id": [str(a) for a in aids],
                    "MinDays": "1",
                    "Active": "true",
                    "Comments": None,
                }
            )
        add_constraints(
            self.time_constraints,
            "ConstraintMinDaysBetweenActivities",
            constraints,
        )

    ############### FURTHER CONSTRAINTS ###############

    # Add weighting (ignored here)?
    def constraints_MIN_PERIODS_DAILY(self, t_constraint):
        clist: List[dict] = []
        # TODO: Get default from somewhere?
        default = "4"
        for klass in self.classes:
            try:
                n = self.class_constraints[klass]["MIN_PERIODS_DAILY"]
            except KeyError:
                # If the constraint is not present, don't add it for
                # this class
                continue
            if n:
                if n == "*":
                    n = default
                else:
                    try:
                        i = int(n)
                        if i < 1 or i > len(self.periodtags):
                            raise ValueError
                    except ValueError:
                        REPORT(
                            "ERROR",
                            _INVALID_CLASS_CONSTRAINT.format(
                                klass=klass, constraint=t_constraint
                            ),
                        )
                        return
                    n = str(i)
                clist.append(
                    {
                        "Weight_Percentage": "100",  # necessary!
                        "Minimum_Hours_Daily": n,
                        "Students": klass,
                        "Allow_Empty_Days": "false",
                        "Active": "true",
                        "Comments": None,
                    }
                )
                # print(f"++ ConstraintStudentsSetMinHoursDaily {klass}: {n}")
        return "ConstraintStudentsSetMinHoursDaily", clist

    # Version for all classes:
    #    time_constraints['ConstraintStudentsMinHoursDaily'] = [
    #        {   'Weight_Percentage': '100',
    #            'Minimum_Hours_Daily': str(min_lessons),
    #            'Allow_Empty_Days': 'false',
    #            'Active': 'true',
    #            'Comments': None
    #        }
    #    ]

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
                if n == "*":
                    # default is "0"
                    n = "0"
                else:
                    try:
                        i = int(n)
                        if i < 0 or i > _MAX_GAPS_PER_WEEK:
                            raise ValueError
                    except ValueError:
                        REPORT(
                            "ERROR",
                            _INVALID_CLASS_CONSTRAINT.format(
                                klass=klass, constraint=t_constraint
                            ),
                        )
                        continue
                    n = str(i)
                clist.append(
                    {
                        "Weight_Percentage": "100",  # necessary!
                        "Max_Gaps": n,
                        "Students": klass,
                        "Active": "true",
                        "Comments": None,
                    }
                )
                # print(f"++ ConstraintStudentsSetMaxGapsPerWeek {klass}: {n}")
        return "ConstraintStudentsSetMaxGapsPerWeek", clist

    def pair_constraint(
        self, klass, pairs, t_constraint
    ) -> List[Tuple[Set[Tuple[int, int]], str]]:
        """Find pairs of activity ids of activities which link two
        subjects (subject tags) for a constraint.
        The returned pairs share at least one "atomic" group.
        The subject pairs are supplied as parameter <pairs>. There can
        be multiple pairs (space separated) and each pair can have a
        weighting (0-10) after a ":" separator, e.g. "En+Fr:8 Eu+Sp".
        The result is a list of pairs, (set of activity ids, fet-weighting).
        fet-weighting is a string in the range "0" to "100".
        """
        result: List[Tuple[Set[Tuple[int, int]], str]] = []
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
                    REPORT(
                        "ERROR",
                        _INVALID_CLASS_CONSTRAINT.format(
                            klass=klass, constraint=t_constraint
                        ),
                    )
                    return
            percent = WEIGHTS[w]
            if not percent:
                continue
            try:
                sid1, sid2 = pair.split("+")
            except ValueError:
                REPORT(
                    "ERROR",
                    _INVALID_CLASS_CONSTRAINT.format(
                        klass=klass, constraint=t_constraint
                    ),
                )
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
        aidmap: Dict[
            Tuple[str, str],
        ] = {}
        for klass in self.classes:
            try:
                pairs = self.class_constraints[klass]["NOT_AFTER"]
            except KeyError:
                # If the constraint is not present, don't add it for
                # this class
                continue
            for aidpairs, percent in self.pair_constraint(
                klass, pairs, t_constraint
            ):
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
            # a1 = self.activities[aidpair[0] - 1]["Subject"]
            # a2 = self.activities[aidpair[1] - 1]["Subject"]
            # print(f" ++ ConstraintTwoActivitiesOrderedIfSameDay:"
            #    f" {a1}/{aidpair[0]} {a2}/{aidpair[1]}")
        return "ConstraintTwoActivitiesOrderedIfSameDay", clist

    def constraints_PAIR_GAP(self, t_constraint):
        """Two subjects should have at least one lesson in between."""
        aidmap: Dict[
            Tuple[str, str],
        ] = {}
        for klass in self.classes:
            try:
                pairs = self.class_constraints[klass]["PAIR_GAP"]
            except KeyError:
                # If the constraint is not present, don't add it for
                # this class
                continue
            for aidpairs, percent in self.pair_constraint(
                klass, pairs, t_constraint
            ):
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
            # a1 = self.activities[aidpair[0] - 1]["Subject"]
            # a2 = self.activities[aidpair[1] - 1]["Subject"]
            # print(f" ++ ConstraintMinGapsBetweenActivities:"
            #    f" {a1}/{aidpair[0]} {a2}/{aidpair[1]}")
        return "ConstraintMinGapsBetweenActivities", clist

    def add_class_constraints(self):
        """Add time constraints according to the "info" entries in the
        timetable data files for each class.
        """
        # Get "local" names of constraints, call handlers
        for name, t_name in self.class_constraints["__INFO_NAMES__"].items():
            try:
                func = getattr(self, f"constraints_{name}")
            except AttributeError:
                raise TT_Error(_UNKNOWN_CONSTRAINT.format(name=t_name))
            cname, clist = func(t_name)
            add_constraints(self.time_constraints, cname, clist)


def add_teacher_constraints(classes):
    ### Not-available times
    days = classes.daytags
    periods = classes.periodtags
    blocked = []
    for tid in classes.teacher_tags():
        dlist = classes.TEACHERS.available[tid]
        tlist = []
        i = 0
        for d in days:
            pblist = dlist[i]
            i += 1
            j = 0
            for p in periods:
                if not pblist[j]:
                    tlist.append({"Day": d, "Hour": p})
                j += 1
        if tlist:
            blocked.append(
                {
                    "Weight_Percentage": "100",
                    "Teacher": tid,
                    "Number_of_Not_Available_Times": str(len(tlist)),
                    "Not_Available_Time": tlist,
                }
            )
    add_constraints(
        classes.time_constraints, "ConstraintTeacherNotAvailableTimes", blocked
    )

    ### Lunch breaks
    # Add a special activity on the days with specified lunch breaks.
    # Also add a constraint to limit the activity to the lunch times.
    constraints_lb = []
    for tid in classes.teacher_tags():
        d = 0
        for daylist in classes.TEACHERS.lunch_periods[tid]:
            if daylist:
                aid = classes.next_activity_id()
                activity = {
                    "Teacher": tid,
                    "Subject": LUNCH_BREAK[0],
                    #'Students': {},
                    "Duration": "1",
                    "Total_Duration": "1",
                    "Id": aid,
                    "Activity_Group_Id": "0",
                    "Active": "true",
                    "Comments": None,
                }
                classes.activities.append(activity)
                # Add constraint
                plist = [
                    {
                        "Preferred_Starting_Day": days[d],
                        "Preferred_Starting_Hour": periods[p],
                    }
                    for p in daylist
                ]
                constraints_lb.append(
                    {
                        "Weight_Percentage": "100",
                        "Activity_Id": aid,
                        "Number_of_Preferred_Starting_Times": str(len(plist)),
                        "Preferred_Starting_Time": plist,
                        "Active": "true",
                        "Comments": None,
                    }
                )
            d += 1

    ### Constraints in the "info" part of the teacher's data
    constraints_m = []  # MINPERDAY
    constraints_gd = []  # MAXGAPSPERDAY
    constraints_gw = []  # MAXGAPSPERWEEK
    constraints_u = []  # MAXBLOCK
    for tid in classes.teacher_tags():
        # The constraint values are <None> or a (number, weight) pair
        # (integers, though the weight may be <None>)
        cdata = classes.TEACHERS.constraints[tid]
        minl = cdata["MINPERDAY"]
        if minl:
            constraints_m.append(
                {
                    "Weight_Percentage": "100",  # necessary!
                    "Teacher_Name": tid,
                    "Minimum_Hours_Daily": str(minl[0]),
                    "Allow_Empty_Days": "true",
                    "Active": "true",
                    "Comments": None,
                }
            )
        gd = cdata["MAXGAPSPERDAY"]
        if gd != None:
            constraints_gd.append(
                {
                    "Weight_Percentage": "100",  # necessary!
                    "Teacher_Name": tid,
                    "Max_Gaps": str(gd[0]),
                    "Active": "true",
                    "Comments": None,
                }
            )
        gw = cdata["MAXGAPSPERWEEK"]
        if gw != None:
            constraints_gw.append(
                {
                    "Weight_Percentage": "100",  # necessary!
                    "Teacher_Name": tid,
                    "Max_Gaps": str(gw[0]),
                    "Active": "true",
                    "Comments": None,
                }
            )
        u = cdata["MAXBLOCK"]
        if u:
            n, w = u
            if w:
                constraints_u.append(
                    {
                        "Weight_Percentage": WEIGHTS[w],
                        "Teacher_Name": tid,
                        "Maximum_Hours_Continuously": str(n),
                        "Active": "true",
                        "Comments": None,
                    }
                )
    add_constraints(
        classes.time_constraints,
        "ConstraintTeacherMinHoursDaily",
        constraints_m,
    )
    add_constraints(
        classes.time_constraints,
        "ConstraintTeacherMaxGapsPerDay",
        constraints_gd,
    )
    add_constraints(
        classes.time_constraints,
        "ConstraintTeacherMaxGapsPerWeek",
        constraints_gw,
    )
    add_constraints(
        classes.time_constraints,
        "ConstraintTeacherMaxHoursContinuously",
        constraints_u,
    )
    add_constraints(
        classes.time_constraints,
        "ConstraintActivityPreferredStartingTimes",
        constraints_lb,
    )


class Placements_fet:#(TT_Placements):
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


def add_constraints(constraints, ctype, constraint_list):
    """Add a (possibly empty) list of constraints, of type <ctype>, to
    the master constraint list-mapping <constraints> (either time or
    space constraints).
    """
    if constraint_list:
        try:
            constraints[ctype] += constraint_list
        except KeyError:
            constraints[ctype] = constraint_list


# Taken from old asc-handler ...
#TODO: I can perhaps use some of it here for loading results from a fet run.
# from qtpy.QtWidgets import QApplication, QFileDialog
def getActivities(working_folder):
    app = QApplication.instance()
    if app is None:
        # if it does not exist then a QApplication is created
        app = QApplication(sys.argv)
    d = QFileDialog(
        None, "Open fet 'activities' file", "", "XML Files (*.xml)"
    )
    d.setFileMode(QFileDialog.ExistingFile)
    d.setOptions(QFileDialog.DontUseNativeDialog)
    history_file = os.path.join(working_folder, "activities_history")
    if os.path.isfile(history_file):
        with open(history_file, "r", encoding="utf-8") as fh:
            history = fh.read().split()
        d.setHistory(history)
    d.exec()
    files = d.selectedFiles()
    if files:
        with open(history_file, "w", encoding="utf-8") as fh:
            fh.write("\n".join(d.history()[-10:]))
        return files[0]
    return None



# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from core.db_access import open_database
    open_database()

    fet_days = get_days_fet()
    if _TEST:
        print("\n*** DAYS ***")
        for _day in get_days():
            print("   ", _day)
        print("\n    ... for fet ...\n   ", fet_days)
        print("\n  ==================================================")

    quit(0)

    if _TEST:
        print("\n ********** READ LESSON DATA **********\n")
    classes = Classes_fet()

    # Generate the fet activities
    classes.get_lessons()

    c_list = classes.classes
    print("\n ... read data for:", c_list)

    add_teacher_constraints(classes)

    # Classes' not-available times
    classes.constraint_blocked_periods()

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

    classes.gen_fetdata()

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

    # quit(0)

    xml_fet = xmltodict.unparse(classes.gen_fetdata(), pretty=True)

    outpath = os.path.join(outdir, "tt_out.fet")
    with open(outpath, "w", encoding="utf-8") as fh:
        fh.write(xml_fet.replace("\t", "   "))
    print("\nTIMETABLE XML ->", outpath)

    quit(0)

    # ??? tag-lids are gone, and multirooms are now available as virtual rooms
    import json

    outpath = os.path.join(outdir, "tag-lids.json")
    # Save association of lesson "tags" with "lids" and "xlids"
    lid_data = {
        "tag-lids": _classes.tag_lids,
        "lid-xlids": {lids[0]: lids[1:] for lids in _classes.xlids},
    }
    with open(outpath, "w", encoding="utf-8") as fh:
        json.dump(lid_data, fh, indent=4)
    print("\nTag – Lesson associations ->", outpath)

    outpath = os.path.join(outdir, "multiple-rooms")
    with open(outpath, "w", encoding="utf-8") as fh:
        for mr in _classes.multirooms:
            groups = ", ".join(mr["GROUPS"])
            sname = _classes.SUBJECTS[mr["SID"]]
            fh.write(
                f"\nKlasse {mr['CLASS']} ({groups})"
                f" :: {sname}: {mr['NUMBER']}"
            )

    print("\nSubjects with multiple rooms ->", outpath)
