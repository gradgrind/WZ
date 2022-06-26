"""
timetable/courses.py

Last updated:  2022-06-26

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

    # start.setup(os.path.join(basedir, "TESTDATA"))
    start.setup(os.path.join(basedir, "DATA-2023"))

T = TRANSLATIONS("timetable.courses")

### +++++

from typing import NamedTuple, Optional

from core.db_management import open_database, db_read_fields
from core.basic_data import get_classes, get_rooms

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


def get_timetable_data():
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
    # Get group info for checking groups
    __classes = get_classes()
    class2groups = {
        klass: __classes.group_info(klass)["GROUPS"]
        for klass, _ in __classes.get_class_list()
    }

    course2data = {}
    class2courses = {}
    for course, klass, group, sid, tid in db_read_fields(
        "COURSES", ("course", "CLASS", "GRP", "SUBJECT", "TEACHER")
    ):
        # CLASS, SUBJECT and TEACHER are foreign keys and should be
        # automatically bound to appropriate entries in the database.
        # GRP should be checked here ...
        if group and group not in class2groups[klass]:
            if klass != "--" and group != "*":
                SHOW_ERROR(
                    T["UNKNOWN_GROUP"].format(
                        klass=klass, group=group, sid=sid, tid=tid
                    )
                )
                continue
        course2data[course] = CourseData(
            klass=klass, group=group, sid=sid, tid=tid
        )
        try:
            class2courses[klass].append(course)
        except KeyError:
            class2courses[klass] = [course]

    lessons = []
    idmax = 0
    class2lessons = {}

    block_members = {}
    block_sublessons = {}
    partners = {}
    partners_time = {}
    timetable_cells = []

    for id, course, length, room, time, place, notes in db_read_fields(
        "LESSONS",
        ("id", "course", "LENGTH", "ROOM", "TIME", "PLACE", "NOTES"),
    ):
        if id > idmax:
            idmax = id
        if time:
            # Only "non-lessons" (payroll) entries should have an empty
            # TIME field.
            coursedata = course2data[course] if course else None
            if coursedata:
                try:
                    class2lessons[coursedata.klass].append(id)
                except KeyError:
                    class2lessons[coursedata.klass] = [id]

            if time[0] == "@":
                # This is something to be placed in the timetable.
                timetable_cells.append(id)

                if place.startswith(">"):
                    ## block sublesson with direct time
                    try:
                        block_sublessons[place].append(id)
                    except KeyError:
                        block_sublessons[place] = [id]

                elif place.startswith("="):
                    ## partner time
                    if place in partners_time:
                        SHOW_ERROR()
                    else:
                        partners_time[place] = id

                ## else: plain lesson with direct time

            elif time[0] == ">":
                ## block member
                try:
                    block_members[time].append(id)
                except KeyError:
                    block_members[time] = [id]

            elif time[0] == "=":
                ## plain lesson or block sublesson with shared time
                # A block sublesson has the block tag in the PLACE field.
                if place.startswith(">"):
                    try:
                        block_sublessons[place].append(id)
                    except KeyError:
                        block_sublessons[place] = [id]
                try:
                    partners[time].append(id)
                except KeyError:
                    partners[time] = [id]

            else:
                SHOW_ERROR(T["BAD_TIME_FIELD"].format(id=id, time=time))
                continue

            lessons.append(
                LessonData(
                    id=id,
                    course=coursedata,
                    length=length,
                    room=room,
                    time=time,
                    place=place,
                    notes=notes,
                )
            )
        else:
            #print(" --", id, course, length, room, time)
            if length != "--":
                SHOW_ERROR(T["INVALID_NON_LESSON_RECORD"] + str(id))

    __usage = len(lessons) / idmax
    if __usage < 0.5:
        SHOW_WARNING(f"Sparse lesson table: usage {__usage:4.2f}%")

    lessonlist = [None] * (idmax + 1)
    for lessondata in lessons:
        lessonlist[lessondata.id] = lessondata

    return {
        "LESSONLIST": lessonlist,
        "CLASS2LESSONS": class2lessons,
        "BLOCK_MEMBERS": block_members,
        "BLOCK_SUBLESSONS": block_sublessons,
        "PARTNERS": partners,
        "PARTNERS_TIME": partners_time,
        "TIMETABLE_CELLS": timetable_cells,
    }


def blocktag2blocksid(tag: str) -> str:
    return tag.split("#", 1)[0].lstrip(">")


def lesson_rooms(lessondata: LessonData) -> list[str]:
    """Read a list of possible rooms for the given lesson.
    Check the components.
    """
    rlist = []
    room_list = get_rooms()
    if not lessondata.room:
        return rlist
    rooms = lessondata.room.rstrip("+")
    if rooms:
        for r in rooms.split("/"):
            if r == "$":
                # Get classroom
                classroom = get_classes().get_classroom(lessondata.course.klass)
                if not classroom:
                    SHOW_ERROR(
                        T["NO_CLASSROOM"].format(klass=lessondata.course.klass)
                    )
                    continue
                rlist.append(classroom)
            else:
                try:
                    room_list.index(r)
                except KeyError:
                    SHOW_ERROR(
                        T["INVALID_ROOM"].format(
                            rid=r,
                            klass=lessondata.course.klass,
                            group=lessondata.course.group,
                            sid=lessondata.course.sid,
                            tid=lessondata.course.tid,
                        )
                    )
                else:
                    rlist.append(r)
    if lessondata.room[-1] == "+":
        rlist.append("+")
    return rlist


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    open_database()

    tt_data = get_timetable_data()
    for l in tt_data["LESSONLIST"]:
        if l:
            print(f"  {l}")
            print("  -->", lesson_rooms(l))
