"""
core/courses.py

Last updated:  2022-04-24

Access course/subject/lesson data.

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

### +++++

from typing import NamedTuple

from utility.db_management import open_database, db_read_fields

### -----

def get_timetable_data():
    class CourseData(NamedTuple):
        klass: str
        group: str
        sid: str
        tid: str

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

    class LessonData(NamedTuple):
        id: int
        course: CourseData
        length: str
        tag: str
        room: str
        notes: str

    class2lessons = {}
    for id, course, length, tag, room, notes in db_read_fields(
        "LESSONS",
        ("id", "course", "LENGTH", "TAG", "ROOM", "NOTES")
    ):
        if length:
            coursedata = course2data[course]
            lessondata = LessonData(
                id=id,
                course=coursedata,
                length=length,
                tag=tag,
                room=room,
                notes=notes
            )
            try:
                class2lessons[coursedata.klass].append(lessondata)
            except KeyError:
                class2lessons[coursedata.klass] = [lessondata]
    return class2lessons


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    open_database()

    # For the timetable
    class2lessons = get_timetable_data()
    for klass, lessonlist in class2lessons.items():
        print(f"CLASS {klass}:")
        for lessondata in lessonlist:
            print(f"  {lessondata}")

