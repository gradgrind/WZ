"""
timetable/courses.py

Last updated:  2022-06-06

Access course/subject/lesson data for timetable.

=+LICENCE=============================
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
=-LICENCE========================================
"""

###############################################################

if __name__ == "__main__":
    # Enable package import if running as module
    import sys, os
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    #start.setup(os.path.join(basedir, "TESTDATA"))
    start.setup(os.path.join(basedir, "DATA-2023"))

T = TRANSLATIONS("timetable.courses")

### +++++

from typing import NamedTuple, Optional

from core.db_management import open_database, db_days_periods, db_read_fields
from core.classes import get_classes_data

### -----

class CourseData(NamedTuple):
    klass: str
    group: str
    sid: str
    tid: str


class LessonData(NamedTuple):
    id: int
    course: Optional[CourseData]
    length: str
    room: str
    time: str
    place: str
    notes: str


class TimetableData:
    """There are four different types of line in the LESSONS table which
    are relevant for the timetable:

     - "plain lessons" specify a lesson (single, double, ...) for a course.

     - "block lessons" specify (via the block-tag, which is in the TIME
       field) one or more lesson units for the course. The time slots are
       shared with other courses (either through parallel teaching,
       shared teaching or spread through the year). The actual timetable
       lesson slots are specified by "block sublessons" (see below).

     - "block sublessons" specify the actual timetable lesson slots for
       a block lesson. They are associated with the corresponding block
       by means of the block-tag, which is in the PLACE field. Their
       course field is empty.

     - "partner-times" allow specified lessons to be forced to start at
       the same time. Such lessons are tied together by means of a
       partner-tag in their TIME field. The actual timetable slots (times)
       are then specified by means of these partner-times lines, which
       have the partner-tag in their PLACE field. These partner-times
       lines specify only the time (slot), the other fields are empty.

    As far as the timetable generation is concerned, the primary elements
    are the "lesson-units" that must be placed in timetable slots.
    Although block-tags and partner-tags both tie various courses together,
    they do it in slightly different ways. Within a block-group the
    courses may have overlapping components (clashes) – because they
    may be taught at different times during the year. The courses in
    a partner-group run concurrently, so such clashes are not possible.
    Also, block members share the lesson units, so each member has the
    same duration. The "partners" have their own lesson units and may
    have different lengths, so they must be checked individually for
    clashes when placing in timetable slots – or different combinations
    must be made for each of the covered time slots.
    The two types are also displayed differently. The block items have
    just one display tile (per class, if there are members from multiple
    classes, but that is an additional complication), showing the block
    subject. Each "partner" has its own tile, showing its own subject.
    """

    def __init__(self):
        self.DAYS, self.PERIODS = db_days_periods()
        self.CLASSES = get_classes_data()
#TODO: Read other tables?

        self.class2groups = {}
        self.class2atoms = {}
        for klass, data in self.CLASSES.items():
            print("\n %%", klass)
            self.class2groups, self.class2atoms = build_group_data(data.divisions)

    #TODO
    def get_timetable_data(self):
        course2data = {}
        class2courses = {}
        for course, klass, group, sid, tid in db_read_fields(
            "COURSES",
            ("course", "CLASS", "GRP", "SUBJECT", "TEACHER")
        ):
            course2data[course] = CourseData(
                klass=klass,
                group=group,
                sid=sid,
                tid=tid
            )
            try:
                class2courses[klass].append(course)
            except KeyError:
                class2courses[klass] = [course]

        lessons = []
        idmax = 0
        class2lessons = {}
        for id, course, length, room, time, place, notes in db_read_fields(
            "LESSONS",
            ("id", "course", "LENGTH", "ROOM", "TIME", "PLACE", "NOTES")
        ):
            unit_times = []
            unit_data = []
            if id > idmax:
                idmax = id
            if time:
                # Only "non-lessons" (payroll) entries should have an empty
                # TIME field.

                print(" ++", id, course, length, room, time)

                if time[0] == "@":
                    # This is something to be placed in the timetable
                    unit_id = len(unit_times)
                    u = self.timeslot_index(time)
                    unit_times.append(u)
                    coursedata = course2data[course] if course else None
                    unit_data.append(
                        self.get_unit_data(coursedata, length, room, place)
                    )
                continue

#??
                coursedata = course2data[course] if course else None
                lessondata = LessonData(
                    id=id,
                    course=coursedata,
                    length=length,
                    room=room,
                    time=time,
                    place=place,
                    notes=notes
                )
                lessons.append(lessondata)
                try:
                    class2lessons[coursedata.klass].append(id)
                except KeyError:
                    class2lessons[coursedata.klass] = [id]

            else:
                print(" --", id, course, length, room, time)
                if length != "--":
                    SHOW_ERROR(T["INVALID_NON_LESSON_RECORD"] + str(id))

        return


        lessonlist = [None] * (idmax + 1)
        print("idmax =", idmax)
        for id, lessondata in lessons:
            lessonlist[id] = lessondata

        print("???", sys.getsizeof(lessons), sys.getsizeof(lessonlist))

        return lessonlist, class2lessons

    def timeslot_index(self, time: str) -> Optional[tuple[int,int]]:
        if time == "@?":
            return None
        d, p = time[1:].split(".", 1)
        return (self.DAYS.index(d), self.PERIODS.index(p))

    def get_unit_data(self, course, length, room, place):
        if course:
            # a "plain" lesson with no partners
            link = None
            classroom = self.CLASSES[course.klass].classroom
            roomlist = get_rooms(room, classroom)
            tidlist = [] if course.tid == "--" else [course.tid]
# Check tid validity?
            group = get_group(course.klass, course.group)
            return (link, tidlist, group, roomlist)
# ...else:

    def get_classroom(self, klass):
        return self.CLASSES[klass].classroom


def get_rooms(roomlist:str, classroom: str) -> list[str]:
# check validity?
    rlist = []
    if not roomlist:
        return rlist
    for r in roomlist.rstrip("+").split("/"):
        if r == "$":
            if not classroom:
                raise RoomError(T["NO_CLASSROOM"])
            rlist.append(classroom)
        else:
            rlist.append(r)
    return rlist

def get_group(klass:str, group:str):
# check validity?
    return (klass, group)


def build_group_data(divisions):
    """Process a class's group (GRP) field to get a list of groups and
    minimal subgroups.
    Return (groups, minimal subgroups)
    """
    groups = set()
    impossible_partners = {}
    # Collect groups and build map giving all groups which are
    # incompatible with each group
    for div in divisions:
        for g in div:
            groups.add(g)
            snew = set(div) - {g}
            try:
                impossible_partners[g] |= snew
            except KeyError:
                impossible_partners[g] = snew
    # Collect minimal subgroups
    cross_terms = [set()]
    for div in divisions:
        __cross_terms = []
        for g in div:
            for ct in cross_terms:
                if g in ct:
                    __cross_terms.append(ct)
                elif not (ct & impossible_partners[g]):
                    gg = set(g.split("."))
                    if len(gg) > 1:
                        for gx in gg:
                            try:
                                nopairx = impossible_partners[gx]
                            except KeyError:
                                continue
                            if (ct & nopairx):
                                break
                        else:
                            __cross_terms.append(ct | gg)
                    else:
                        __cross_terms.append(ct | gg)
        cross_terms = __cross_terms
        #print("\n???", cross_terms)
    #print("\nXXX", impossible_partners)
    #print("\n§GROUPS:", sorted(groups))
    #print("\n§XTERMS:", cross_terms)
    return sorted(groups), [frozenset(ct) for ct in cross_terms]


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":

    """
    build_group_data([("A", "B"), ("G", "R"), ("A", "X", "Y")])
    print("\n  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    build_group_data([("A", "B"), ("G", "R"), ("A", "B.G", "B.R")])
    print("\n  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    build_group_data([("A", "B.G", "B.R"), ("G", "R"), ("A", "B")])
    print("\n  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    """
    #_divs = [("A", "B"), ("G", "R"), ("A", "X", "Y")]
    #_divs = [("A", "B"), ("G", "R"), ("A", "B.G", "B.R")]
    #_divs = [("A", "B.G", "B.R"), ("G", "R"), ("A", "B")]
    _divs = [("G", "R"), ("A", "B.G", "B.R"), ("A", "B"), ("I", "II", "III")]
    print("\nGROUP DIVISIONS:", _divs, "->")
    groups, minsubgroups = build_group_data(_divs)
    print("\n ... Groups:", groups)
    print("\n ... Atoms:", minsubgroups)

    #quit(0)

    open_database()

    ttdata = TimetableData()

    #testing
    ttdata.get_timetable_data()
    quit(0)

    # For the timetable
    lessons, class2lessons = get_timetable_data()
    klass = "10G"
    print(f"CLASS {klass}:")
    lids = class2lessons[klass]
    for lid in lids:
        print(f"  {lessons[lid]}")
