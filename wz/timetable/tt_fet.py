"""
timetable/tt_fet.py - last updated 2022-02-27

Prepare fet-timetables input from the various sources ...

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

__TEST = False
__TEST = True

FET_VERSION = "6.2.7"

WEIGHTS = [None, "50", "67", "80", "88", "93", "95", "97", "98", "99", "100"]

LUNCH_BREAK = ("mp", "Mittagspause")
VIRTUAL_ROOM = ("dummy", "Zusatzraum")

_MAX_GAPS_PER_WEEK = 10 # maximum value for max. gaps per week (for classes)


### Messages

_LESSON_NO_GROUP = "Klasse {klass}, Fach {sid}: „Unterricht“ ohne Gruppe"
_LESSON_NO_TEACHER = (
    "Klasse {klass}, Fach {sid}: „Unterricht“ ohne"
    " Lehrer.\nDieser Unterricht wird NICHT im Stundenplan erscheinen."
)
_LAST_LESSON_TAG_INVALID = (
    "Bedingung „LAST_LESSON“: Die Kennung {tag}" " wird mehr als einmal benutzt"
)
_SUBJECT_PAIR_INVALID = (
    "Ungültiges Fach-Paar ({item}) unter den „weiteren Bedingungen“"
)
_DODGY_GAPS_PER_WEEK = (
    "Bedingung GAPS für Klasse {klass} ist" " wahrscheinlich fehlerhaft: {gaps}"
)
_BAD_GAPS_PER_WEEK = (
    "Bedingung GAPS für Klasse {klass} ist" " fehlerhaft: {gaps}"
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
_XX_SID_IN_CLASS = (
    "Klasse {klass}: Fachkürzel „{sid}“ von XX-Klasse ist auch in dieser"
    " Klasse definiert"
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

from typing import NamedTuple, Dict, List, Set, FrozenSet, Tuple

### +++++

from itertools import combinations

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
)

### -----


class Days_fet(TT_Days):
    def get_days(self):
        """Return an ordered list of fet elements for the days."""
        return [{"Name": d.short} for d in self]


class Periods_fet(TT_Periods):
    def get_periods(self):
        """Return an ordered list of fet elements for the periods."""
        return [{"Name": p.short} for p in self]


class Classes_fet(Classes):
    __slots__ = (
        "activities",
        "fet_rooms",
        "__virtual_rooms",
        "sid_groups",
        "time_constraints",
        "space_constraints",
        "lid2aids",
        "class2sid2ag2aids",
    )

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
            for g, sgs in class_groups.items():
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
                        for sg in sgs
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
            for d in self.DAYS:
                pblist = daylist[i]
                i += 1
                j = 0
                for p in self.PERIODS:
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
        """Return a virtual room for the given list of room lists. These
        virtual rooms are cached so that they can be reused, should
        the <roomlists> argument be repeated.
        """
        # First need a hashable representation of <roomlists>, use a string.
        hashable = "&".join(["|".join(rooms) for rooms in roomlists])
        # print("???????", hashable)
        try:
            return self.__virtual_rooms[hashable]
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
        room = {
            "Name": name,
            "Building": None,
            "Capacity": "30000",
            "Virtual": "true",
            "Number_of_Sets_of_Real_Rooms": str(len(roomlists)),
            "Set_of_Real_Rooms": roomlist,
            "Comments": None,
        }
        self.__virtual_rooms[hashable] = room
        self.fet_rooms.append(room)
        return name

    def next_activity_id(self):
        return str(len(self.activities) + 1)

    def get_lessons(self):
        """Build list of lessons for fet-timetables."""

        def make_room_constraint(aid: str, rlist: List[str]) -> None:
            """Make a room constraint for the given activity id and room
            list.
            """
            n = len(rlist)
            if n > 1:
                r_c = "ConstraintActivityPreferredRooms"
                s_c = {
                    "Weight_Percentage": "100",
                    "Activity_Id": aid,
                    "Number_of_Preferred_Rooms": n,
                    "Preferred_Room": rlist,
                    "Active": "true",
                    "Comments": None,
                }
            elif n == 1:
                r_c = "ConstraintActivityPreferredRoom"
                s_c = {
                    "Weight_Percentage": "100",
                    "Activity_Id": aid,
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
        self.activities = []  # fet activities
        # Get initial room list in fet form
        self.fet_rooms: List[dict] = self.ROOMS.get_rooms()
        self.__virtual_rooms = {}  # virtual room cache, internal
        # For constraints concerning relative placement of individual
        # lessons in the various subjects, collect the tags and their
        # pupil groups for each subject:
        #    {sid: [(group-set, activity id), ... ]}
        self.sid_groups: Dict[str, List[Tuple[FrozenSet[str], str]]] = {}
        self.lid2aids: Dict[int, List[str]] = {}

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
            ignore_rooms = []
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
            activity0["Subject"] = sid
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
                        "Id": activity_id,
                        "Comments": f"{lesson_index}",
                    }
                )
                self.activities.append(activity0)
                if rooms:
                    make_room_constraint(activity_id, rooms)
                try:
                    self.sid_groups[sid].append((groups, activity_id))
                except KeyError:
                    self.sid_groups[sid] = [(groups, activity_id)]
            else:
                i = 0
                aids = []
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
                            "Id": activity_id,
                            "Comments": f"{lesson_index}.{i}",
                        }
                    )
                    self.activities.append(activity)
                    if rooms:
                        make_room_constraint(activity_id, rooms)
                    try:
                        self.sid_groups[sid].append((groups, activity_id))
                    except KeyError:
                        self.sid_groups[sid] = [(groups, activity_id)]

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
            print(f"??? {klass}", atomic_groups)
            d = -1
            for periods in weekdata:
                d += 1
                if periods:
                    nperiods = str(len(periods))
                    day = self.DAYS[d]
                    print(f"LUNCH {klass}, {day}: {periods}")
                    # Add lunch-break activity
                    for g in atomic_groups:
                        aid = self.next_activity_id()
                        activity = {
                            #"Teacher": {},
                            "Subject": LUNCH_BREAK[0],
                            "Students": groupsets.get(frozenset([g])) or g,
                            "Duration": "1",
                            "Total_Duration": "1",
                            "Id": aid,
                            "Activity_Group_Id": "0",
                            "Active": "true",
                            "Comments": None,
                        }
                        self.activities.append(activity)
                        # Add constraint
                        constraints.append(
                            {
                                "Weight_Percentage": "100",
                                "Activity_Id": aid,
                                "Number_of_Preferred_Starting_Times": nperiods,
                                "Preferred_Starting_Time": [
                                    {
                                        "Preferred_Starting_Day": day,
                                        "Preferred_Starting_Hour": self.PERIODS[p],
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
            constraints
        )

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
                sid1, sid2 = item.split("+")
            except ValueError:
                raise TT_Error(_SUBJECT_PAIR_INVALID.format(item=item))
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
                classes = {
                    class_group_split(g)[0] for g in self.tag_get_groups(tag)
                }
                for klass in classes:
                    tset1 = set()
                    for t in tset:
                        for g in self.tag_get_groups(t):
                            if class_group_split(g)[0] == klass:
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

    def subject_activities(self):
        """Collect the activity ids for every subject in every (atomic)
        group in every class.
        """
        aids: List[str]
        ag2aids: Dict[str,List[str]]
        sid2ag2aids: Dict[str,Dict[str,List[str]]]
        self.class2sid2ag2aids: Dict[str,Dict[str,Dict[str,List[str]]]] = {}
        for _klass, lids in self.class_lessons.items():
            ### Collect subjects
            for lid in lids:
                aids = self.lid2aids.get(lid)
                if not aids:
                    continue
                lesson: Lesson = self.lesson_list[lid]
                sid: str = lesson.SID.split("+", 1)[0] # remove "+"-tags
                for group in lesson.GROUPS:
                    # For each group, add the activity ids in the appropriate class
                    klass = group.split(".", 1)[0]
                    try:
                        sid2ag2aids = self.class2sid2ag2aids[klass]
                    except KeyError:
                        ag2aids = {group: list(aids)}
                        self.class2sid2ag2aids[klass] = {sid: ag2aids}
                        continue
                    try:
                        ag2aids = sid2ag2aids[sid]
                    except KeyError:
                        sid2ag2aids[sid] = {group: list(aids)}
                        continue
                    try:
                        ag2aids[group] += aids
                    except KeyError:
                        ag2aids[group] = list(aids)


    def constraint_day_separation(self):
        """Add constraints to ensure that multiple lessons in any subject
        are not placed on the same day.
        """
        constraints: List[dict] = []
        # Use <self.class2sid2ag2aids> to find activities.
        sid2ag2aids: Dict[str,Dict[str,List[str]]]
        ag2aids: Dict[str,List[str]]
        aids: List[str]
        aidset_map: Dict[int,Set[FrozenSet[str]]] = {}
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
                        aids_i = frozenset(int(aid) for aid in aids)
                        try:
                            aidset_map[l].add(aids_i)
                        except KeyError:
                            aidset_map[l] = {aids_i}
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
            aids_s = [str(a) for a in aids]
            #print("§§§§§§§§§§§", aids_s)
            constraints.append(
                {
                    "Weight_Percentage": "100",
                    "Consecutive_If_Same_Day": "true",
                    "Number_of_Activities": str(len(aids)),
                    "Activity_Id": aids,
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

    def constraint_MIN_PERIODS_DAILY(self, klass, n, t_constraint):
        if n:
            try:
                i = int(n)
                if i < 1 or i > len(self.PERIODS):
                    raise ValueError
            except ValueError:
                REPORT("ERROR", _INVALID_CLASS_CONSTRAINT.format(
                        klass=klass, constraint=t_constraint))
                return
            add_constraints(
                self.time_constraints,
                "ConstraintStudentsSetMinHoursDaily",
                [
                    {
                        "Weight_Percentage": "100", # necessary!
                        "Minimum_Hours_Daily": n,
                        "Students": klass,
                        "Allow_Empty_Days": "false",
                        "Active": "true",
                        "Comments": None,
                    }
                ],
            )
            print(f"++ ConstraintStudentsSetMinHoursDaily {klass}: {n}")

    # Version for all classes:
    #    time_constraints['ConstraintStudentsMinHoursDaily'] = [
    #        {   'Weight_Percentage': '100',
    #            'Minimum_Hours_Daily': str(min_lessons),
    #            'Allow_Empty_Days': 'false',
    #            'Active': 'true',
    #            'Comments': None
    #        }
    #    ]

    def constraint_MAX_GAPS_WEEKLY(self, klass, n, t_constraint):
        """Maximum gaps per week for the specified class.
        If <n> is not supplied (also if the condition is not specified!)
        use 0 (no gaps).
        """
        if n:
            try:
                i = int(n)
                if i < 0 or i > _MAX_GAPS_PER_WEEK:
                    raise ValueError
            except ValueError:
                REPORT("ERROR", _INVALID_CLASS_CONSTRAINT.format(
                        klass=klass, constraint=t_constraint))
                return
        else:
            n = "0"
        add_constraints(
            self.time_constraints,
            "ConstraintStudentsSetMaxGapsPerWeek",
            [
                {
                    "Weight_Percentage": "100", # necessary!
                    "Max_Gaps": n,
                    "Students": klass,
                    "Active": "true",
                    "Comments": None,
                }
            ],
        )
        print(f"++ ConstraintStudentsSetMaxGapsPerWeek {klass}: {n}")

    def class_constraint_data(self, data):
        """Extract info for the various classes, jandling default values."""
        cmap = {}
        try:
            default = data.pop("*")  # WARNING: The entry is now gone!
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


    def tag_get_sid(self, tag):
        # ?
        return self.lessons[tag.split("__", 1)[0]]["SID"]

    def tag_get_groups(self, tag):
        # ?
        return self.lessons[tag.split("__", 1)[0]]["GROUPS"]

    # TODO: This might be easier using lists of tags and data for each class!
    def NOT_AFTER(self, data):
        """Two subjects should be in the given order, if on the same day."""
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
                        # print("???", klass, item, percent, lid1, lids2)
                        for lid2 in lids2:
                            constraints.append(
                                {
                                    "Weight_Percentage": percent,
                                    "First_Activity_Id": lid1,
                                    "Second_Activity_Id": lid2,
                                    "Active": "true",
                                    "Comments": None,
                                }
                            )
        add_constraints(
            self.time_constraints,
            "ConstraintTwoActivitiesOrderedIfSameDay",
            constraints,
        )

    def PAIR_GAP(self, data):
        """Two subjects should have at least one lesson in between."""
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
                        # print("???", klass, item, percent, lid1, lids2)
                        for lid2 in lids2:
                            constraints.append(
                                {
                                    "Weight_Percentage": percent,
                                    "Number_of_Activities": "2",
                                    "Activity_Id": [lid1, lid2],
                                    "MinGaps": "1",
                                    "Active": "true",
                                    "Comments": None,
                                }
                            )
        add_constraints(
            self.time_constraints,
            "ConstraintMinGapsBetweenActivities",
            constraints,
        )

    def add_class_constraints(self):
        info_names = self.class_constraints['__INFO_NAMES__']
        for klass in sorted(self.class_constraints):
            if klass[0] == "_":
                continue
            for key, val in self.class_constraints[klass].items():
                if key[0] == "_":
                    continue
                try:
                    func = getattr(self, f"constraint_{key}")
                except AttributeError:
                    print(f"CONSTRAINT {key}: Not yet implemented")
                    continue
                func(klass, val, info_names[key])


class Teachers_fet(TT_Teachers):
    def get_teachers(self, classes):
        """Generate the teacher definitions for fet.
        This method should be called before the others, to set up
        <self.tidlist>.
        """
        self.classes = classes
        tlist = []
        self.tidlist = []  # Just tids used in the timetable
        for tid, name in self.items():
            if tid in classes.timetable_teachers:
                tlist.append(
                    {
                        "Name": tid,
                        "Target_Number_of_Hours": "0",
                        "Qualified_Subjects": None,
                        "Comments": name,
                    }
                )
                self.tidlist.append(tid)
        return tlist

    def add_constraints(self):
        time_constraints = self.classes.time_constraints
        # Not-available times
        blocked = self.constraint_available()
        add_constraints(
            time_constraints, "ConstraintTeacherNotAvailableTimes", blocked
        )

        constraints_m = []  # MINPERDAY
        constraints_gd = []  # MAXGAPSPERDAY
        constraints_gw = []  # MAXGAPSPERWEEK
        constraints_u = []  # MAXBLOCK
        for tid in self.tidlist:
            # The constraint values are <None> or a (number, weight) pair
            # (integers, though the weight may be <None>)
            cdata = self.constraints[tid]
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
            time_constraints, "ConstraintTeacherMinHoursDaily", constraints_m
        )
        add_constraints(
            time_constraints, "ConstraintTeacherMaxGapsPerDay", constraints_gd
        )
        add_constraints(
            time_constraints, "ConstraintTeacherMaxGapsPerWeek", constraints_gw
        )
        add_constraints(
            time_constraints,
            "ConstraintTeacherMaxHoursContinuously",
            constraints_u,
        )
        constraints = self.lunch_breaks()
        add_constraints(
            time_constraints,
            "ConstraintActivityPreferredStartingTimes",
            constraints,
        )

    def constraint_available(self):
        """Return the blocked periods in the form needed by fet.
        <days> and <periods> are lists of the fet tags.
        """
        days = self.classes.DAYS
        periods = self.classes.PERIODS
        blocked = []
        for tid in self.tidlist:
            dlist = self.available[tid]
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
        return blocked

    def lunch_breaks(self):
        """Add a special activity on the days with specified lunch breaks.
        Also add a constraint to limit the activity to the lunch times.
        """
        constraints = []
        days = self.classes.DAYS
        periods = self.classes.PERIODS
        for tid in self.tidlist:
            d = 0
            for daylist in self.lunch_periods[tid]:
                if daylist:
                    aid = self.classes.next_activity_id()
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
                    self.classes.activities.append(activity)
                    # Add constraint
                    plist = [
                        {
                            "Preferred_Starting_Day": days[d],
                            "Preferred_Starting_Hour": periods[p],
                        }
                        for p in daylist
                    ]
                    constraints.append(
                        {
                            "Weight_Percentage": "100",
                            "Activity_Id": aid,
                            "Number_of_Preferred_Starting_Times": str(
                                len(plist)
                            ),
                            "Preferred_Starting_Time": plist,
                            "Active": "true",
                            "Comments": None,
                        }
                    )
                d += 1
        return constraints


class Rooms_fet(TT_Rooms):
    def get_rooms(self):
        return [
            {
                "Name": rid,
                "Building": None,
                "Capacity": "30000",
                "Virtual": "false",
                "Comments": name,
            }
            for rid, name in self.items()
        ]


# TODO: special fet bodge.
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


class Subjects_fet(TT_Subjects):
    def get_subjects(self):
        sids = [{"Name": sid, "Comments": name} for sid, name in self.items()]
        sids.append({"Name": VIRTUAL_ROOM[0], "Comments": VIRTUAL_ROOM[1]})
        sids.append({"Name": LUNCH_BREAK[0], "Comments": LUNCH_BREAK[1]})
        return sids


########################################################################

""" 'ConstraintStudentsSetNotAvailableTimes': [
        {'Weight_Percentage': '100', 'Students': '01G',
            'Number_of_Not_Available_Times': '20',
            'Not_Available_Time': [
                {'Day': 'Mo', 'Hour': '4'},
                {'Day': 'Mo', 'Hour': '5'},
                {'Day': 'Mo', 'Hour': '6'},
                {'Day': 'Mo', 'Hour': '7'},
                {'Day': 'Di', 'Hour': '4'},
                {'Day': 'Di', 'Hour': '5'},
...
            ],
            'Active': 'true', 'Comments': None
        },
        {'Weight_Percentage': '100',
...
        },
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
"""


def build_dict_fet(
    ROOMS,
    DAYS,
    PERIODS,
    TEACHERS,
    SUBJECTS,
    CLASSES,
    LESSONS,
    time_constraints,
    space_constraints,
):
    fet_dict = {
        "@version": f"{FET_VERSION}",
        "Mode": "Official",
        "Institution_Name": "FWS Bothfeld",
        "Comments": "Default comments",
        "Days_List": {"Number_of_Days": f"{len(DAYS)}", "Day": DAYS},
        "Hours_List": {"Number_of_Hours": f"{len(PERIODS)}", "Hour": PERIODS},
        "Subjects_List": {"Subject": SUBJECTS},
        "Activity_Tags_List": None,
        "Teachers_List": {"Teacher": TEACHERS},
        "Students_List": {"Year": CLASSES},
        # Try single activities instead?
        "Activities_List": {
            "Activity": LESSONS
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
        "Buildings_List": None,
        "Rooms_List": {
            "Room": ROOMS
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
        # {'Number_of_Real_Rooms': '2', 'Real_Room': ['r2', 'r3']}
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
    tc_dict.update(time_constraints)
    sc_dict.update(space_constraints)
    fet_dict["Time_Constraints_List"] = tc_dict
    fet_dict["Space_Constraints_List"] = sc_dict
    return {"fet": fet_dict}


###################
"""
 Alternative with single activities
<Activity>
    <Teacher>JS</Teacher>
    <Subject>Hu</Subject>
    <Students>01G</Students>
    <Duration>2</Duration>
    <Total_Duration>2</Total_Duration>
    <Id>5</Id>
    <Activity_Group_Id>0</Activity_Group_Id>
    <Active>true</Active>
    <Comments></Comments>
</Activity>

...

<ConstraintActivityPreferredStartingTime>
    <Weight_Percentage>100</Weight_Percentage>
    <Activity_Id>1</Activity_Id>
    <Preferred_Day>Mo</Preferred_Day>
    <Preferred_Hour>A</Preferred_Hour>
    <Permanently_Locked>true</Permanently_Locked>
    <Active>true</Active>
    <Comments></Comments>
</ConstraintActivityPreferredStartingTime>
<ConstraintActivityPreferredStartingTime>
    <Weight_Percentage>100</Weight_Percentage>
    <Activity_Id>2</Activity_Id>
    <Preferred_Day>Di</Preferred_Day>
    <Preferred_Hour>A</Preferred_Hour>
    <Permanently_Locked>true</Permanently_Locked>
    <Active>true</Active>
    <Comments></Comments>
</ConstraintActivityPreferredStartingTime>

# As dict entry:
'ConstraintMinDaysBetweenActivities': [
        {'Weight_Percentage': '100', 'Consecutive_If_Same_Day': 'true',
            'Number_of_Activities': '2', 'Activity_Id': ['6', '7'],
            'MinDays': '1', 'Active': 'true', 'Comments': None
        },
        {'Weight_Percentage': '100', 'Consecutive_If_Same_Day': 'true',
            'Number_of_Activities': '2', 'Activity_Id': ['6', '8'],
            'MinDays': '1', 'Active': 'true', 'Comments': None
        }
    ]
},

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

<ConstraintTeacherMaxHoursContinuously>
    <Weight_Percentage>90</Weight_Percentage>
    <Teacher_Name>AA</Teacher_Name>
    <Maximum_Hours_Continuously>9</Maximum_Hours_Continuously>
    <Active>true</Active>
    <Comments></Comments>
</ConstraintTeacherMaxHoursContinuously>

<ConstraintTeacherMaxGapsPerDay>
    <Weight_Percentage>100</Weight_Percentage>
    <Teacher_Name>AA</Teacher_Name>
    <Max_Gaps>1</Max_Gaps>
    <Active>true</Active>
    <Comments></Comments>
</ConstraintTeacherMaxGapsPerDay>

<ConstraintTeacherMaxGapsPerWeek>
    <Weight_Percentage>100</Weight_Percentage>
    <Teacher_Name>AA</Teacher_Name>
    <Max_Gaps>3</Max_Gaps>
    <Active>true</Active>
    <Comments></Comments>
</ConstraintTeacherMaxGapsPerWeek>
"""

"""
# Should I have this one?
<ConstraintStudentsEarlyMaxBeginningsAtSecondHour>
    <Weight_Percentage>100</Weight_Percentage>
    <Max_Beginnings_At_Second_Hour>0</Max_Beginnings_At_Second_Hour>
    <Active>true</Active>
    <Comments></Comments>
</ConstraintStudentsEarlyMaxBeginningsAtSecondHour>
"""

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


class Placements_fet(TT_Placements):
    def placements(self):
        days = self.classes.DAYS
        ndays = str(len(days))
        periods = self.classes.PERIODS
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
                for i in range(l):
                    parallel = [e[i] for e in excess]
                    constraints_parallel.append(
                        {
                            "Weight_Percentage": w,
                            "Number_of_Activities": str(l),
                            "Activity_Id": parallel,
                            "Permanently_Locked": "true",
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


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    _days = Days_fet()

    days = _days.get_days()
    if __TEST:
        print("\n*** DAYS ***")
        for _day in _days:
            print("   ", _day)
        print("\n    ... for fet ...\n   ", days)
        print("\n  ==================================================")

    _periods = Periods_fet()
    periods = _periods.get_periods()
    if __TEST:
        print("\n*** PERIODS ***")
        for _period in _periods:
            print("   ", _period)
        print("\n    ... for fet ...\n   ", periods)
        print("\n  ==================================================")

    _rooms = Rooms_fet()

    _subjects = Subjects_fet()
    subjects = _subjects.get_subjects()
    if __TEST:
        print("\nSUBJECTS:")
        for sdata in subjects:
            print("   ", sdata)

    _teachers = Teachers_fet(_days, _periods)

    if __TEST:
        print("\n ********** READ LESSON DATA **********\n")
    _classes = Classes_fet(
        _days, _periods, SUBJECTS=_subjects, ROOMS=_rooms, TEACHERS=_teachers
    )

    # Generate the fet activities
    _classes.get_lessons()

    c_list = _classes.classes
    print("\n ... read data for:", c_list)

    if __TEST:
        print("\nROOMS:")
        for rdata in _classes.fet_rooms:
            print("   ", rdata)

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
        # for l, data in _classes.lessons.items():
        #    print(f"   {l}:", data)
        for l in activities:
            print("   ", l)
        print("\n  ======================================================\n")

    # Classes' not-available times
    _classes.constraint_blocked_periods()

    # Fixed placements for activities
    cards = Placements_fet(_classes, _days, _periods)
    cards.placements()

# TODO: Should this be later? ... as it adds activities
    _classes.lunch_breaks()

    print("\nBuild subject – activity mapping")

    _classes.subject_activities()
    for klass in _classes.classes:
        if klass.startswith("XX"):
            continue
        print(f"\n **** Class {klass}")
        for sid, ag2aids in _classes.class2sid2ag2aids[klass].items():
            for ag, aids in ag2aids.items():
                print(f"     {sid:8}: {ag:10} --> {aids}")

    print("\nSubject day-separation constraints:")
    _classes.constraint_day_separation()

    print("\nCLASS CONSTRAINTS:")
    _classes.add_class_constraints()

    # Activity info is available thus:
    _aid = "550"
    print(f"\n???? {_aid}:", _classes.activities[int(_aid) - 1])

    quit(0)



    EXTRA_CONSTRAINTS = MINION(DATAPATH("TIMETABLE/EXTRA_CONSTRAINTS"))
    for key, value in EXTRA_CONSTRAINTS.items():
        try:
            func = getattr(_classes, key)
        except AttributeError:
            print(f"CONSTRAINT {key}: Not yet implemented")
            continue
        func(value)

    xml_fet = xmltodict.unparse(
        build_dict_fet(
            ROOMS=rooms,
            DAYS=days,
            PERIODS=periods,
            TEACHERS=teachers,
            SUBJECTS=subjects,
            CLASSES=classes,
            LESSONS=activities,
            time_constraints=t_constraints,
            space_constraints=s_constraints
            #            space_constraints = {}
        ),
        pretty=True,
    )

    outpath = os.path.join(outdir, "tt_out.fet")
    with open(outpath, "w", encoding="utf-8") as fh:
        fh.write(xml_fet.replace("\t", "   "))
    print("\nTIMETABLE XML ->", outpath)

    #    for sid, gs in sid_group_sets.items():
    #        print(f"\n +++ {sid}:", gs)
    #    print(f"\n +++ Mal:", sid_group_sets['Mal'])
    #    print("\n???divisions 01K:", _classes.class_divisions['01K'])
    #    print("\n???class_groups 01K:", _classes.class_groups['01K'])

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
