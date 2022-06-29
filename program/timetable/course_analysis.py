"""
timetable/courses.py

Last updated:  2022-06-29

Collect information on activities for teachers and classes/groups.

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

from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm

from core.db_management import db_read_fields
from core.basic_data import (
    get_classes,
    get_teachers,
    get_rooms,
    get_payroll_weights,
)

# from timetable.courses import blocktag2blocksid

### -----


class CourseData(NamedTuple):
    klass: str
    group: str
    sid: str
    tid: str


class LessonData(NamedTuple):
    id: int
    course: Optional[int]
    length: str
    payroll: Optional[tuple[Optional[float], float]]
    room: Optional[list[str]]
    time: str
    place: str


class Courses:
    """Collect and collate information relating to the courses and lessons.
    The following data structures are available as attributes:
        course2data:        {course-id -> <CourseData>}
        class2courses:      {class -> {course-id, ... ]}
        teacher2courses:    {tid -> {course-id, ... ]}
        lesson2data:        {lesson-id -> <LessonData>}
        course2payroll:     {course-id -> [lesson-id, ... ]}
        course2block:       {course-id -> [lesson-id, ... ]}
        course2plain:       {course-id -> [lesson-id, ... ]}
        block_sublessons:   {block-tag -> [lesson-id, ... ]}
        partners_time:      {partner-tag -> lesson-id}
    """

    def __init__(self):
        ### First read the COURSES table
        classes = get_classes()
        class2groups = {
            klass: classes.group_info(klass)["GROUPS"]
            for klass, _ in classes.get_class_list()
        }
        self.course2data = {}
        self.class2courses = {}
        self.teacher2courses = {}
        payroll_weights = get_payroll_weights()
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
            self.course2data[course] = CourseData(
                klass=klass, group=group, sid=sid, tid=tid
            )
            try:
                self.class2courses[klass].append(course)
            except KeyError:
                self.class2courses[klass] = [course]
            if tid and tid != "--":
                try:
                    self.teacher2courses[tid].append(course)
                except KeyError:
                    self.teacher2courses[tid] = [course]
        ### Now read the LESSONS table
        self.lesson2data = {}  # {lesson-id -> <LessonData>}
        # Partners time records are the entries which specify the actual time
        self.partners_time = {}  # {partner-tag -> lesson-id}
#TODO:
        # Partners records are the teaching lessons which are parallel
        self.partners = {}      # {course-id -> [lesson-id, ... ]}
        self.course2payroll = {}  # {course-id -> [lesson-id, ... ]}
        self.course2block = {}  # {course-id -> [lesson-id, ... ]}
        self.course2plain = {}  # {course-id -> [lesson-id, ... ]}
        # Block sublessons are the records for the actual lessons:
        self.block_sublessons = {}  # {block-tag -> [lesson-id, ... ]}
        # Block members are the records for the courses sharing the slots:
        self.block_members = {} # {block-tag -> [lesson-id, ... ]}
        for id, course, length, payroll, room, time, place in db_read_fields(
            "LESSONS",
            ("id", "course", "LENGTH", "PAYROLL", "ROOM", "TIME", "PLACE"),
        ):
            if course:
                if payroll:
                    try:
                        n, f = payroll.split("*", 1)
                        payroll_val = (
                            float(payroll_weights.map(f).replace(",", ".")),
                            float(n.replace(",", ".")) if n else None,
                        )
                    except (ValueError, KeyError):
                        REPORT(
                            "ERROR",
                            T["INVALID_PAYROLL"].format(id=id, payroll=payroll),
                        )
                        continue
                else:
                    REPORT("WARNING", T["NO_PAYROLL"].format(id=id))
                    payroll_val = None

                if length == "--":
                    ## non-lesson
                    if time or place or room:
                        REPORT("ERROR", T["INVALID_NON_LESSON"].format(id=id))
                        continue
                    if payroll_val and payroll_val[0] is None:
                        REPORT(
                            "ERROR",
                            T["PAYROLL_NO_NUMBER"].format(
                                id=id, payroll=payroll
                            ),
                        )
                    try:
                        self.course2payroll[course].append(id)
                    except KeyError:
                        self.course2payroll[course] = [id]
                # TODO: Is it at all sensible to support multiple such entries for a course?

                elif length == "*":
                    ## block-member
                    if not time.startswith(">"):
                        REPORT("ERROR", T["INVALID_BLOCK"].format(id=id))
                        continue
                    try:
                        self.course2block[course].append(id)
                    except KeyError:
                        self.course2block[course] = [id]
                    try:
                        self.block_members[time].append(id)
                    except KeyError:
                        self.block_members[time] = [id]

                else:
                    ## plain lesson
                    if not length.isnumeric():
                        REPORT(
                            "ERROR",
                            T["LENGTH_NOT_NUMBER"].format(id=id, length=length),
                        )
                        continue
                    if time.startswith("="):
                        try:
                            self.partners[time].append(id)
                        except KeyError:
                            self.partners[time] = [id]
                    elif not time.startswith("@"):
                        REPORT("ERROR", T["INVALID_TIME"].format(
                            id=id, time=time)
                        )
                        continue
                    try:
                        self.course2plain[course].append(id)
                    except KeyError:
                        self.course2plain[course] = [id]

                roomlist = lesson_rooms(room, self.course2data[course], id)

            else:
                if payroll:
                    REPORT(
                        "ERROR",
                        T["PAYROLL_UNEXPECTED"].format(id=id, payroll=payroll),
                    )
                if place.startswith(">"):
                    ## block-sublesson: add the length to the list for this block-tag
                    if not length.isnumeric():
                        REPORT(
                            "ERROR",
                            T["LENGTH_NOT_NUMBER"].format(id=id, length=length),
                        )
                        continue
#TODO: Do I really want to allow partnering with block sublessons?
# It might at least be useful for "pseudoblocks"?
                    if time.startswith("="):
                        try:
                            self.partners[time].append(id)
                        except KeyError:
                            self.partners[time] = [id]
                    elif not time.startswith("@"):
                        REPORT("ERROR", T["INVALID_TIME"].format(
                            id=id, time=time)
                        )
                        continue
                    try:
                        self.block_sublessons[place].append(id)
                    except KeyError:
                        self.block_sublessons[place] = [id]
                    roomlist = room.split("/") if room else None

                elif place.startswith("="):
                    ## partner-time
                    if length or room:
                        REPORT("ERROR", T["INVALID_PARTNER_TIME"].format(id=id))
                        continue
                    if not time.startswith("@"):
                        REPORT("ERROR", T["INVALID_TIME"].format(
                            id=id, time=time)
                        )
                        continue
                    if place in self.partners_time:
                        REPORT(
                            "ERROR", T["DOUBLE_PARTNER_TIME"].format(tag=place)
                        )
                        continue
                    else:
                        self.partners_time[place] = id
                    if room:
                        REPORT(
                            "ERROR",
                            T["ROOM_NOT_EXPECTED"].format(id=id, room=room),
                        )
                        continue
                    roomlist = None

                else:
                    ## anything else is a bug
                    REPORT("ERROR", T["INVALID_LESSON"].format(id=id))
                    continue

            self.lesson2data[id] = LessonData(
                id=id,
                course=course,
                length=length,
                payroll=payroll,
                room=roomlist,
                time=time,
                place=place,
            )


def lesson_rooms(
    room: str, course: CourseData, lesson_id: int
) -> Optional[list[str]]:
    """Read a list of possible rooms for the given lesson.
    Check the components.
    """
    if not room:
        return None
    rlist = []
    room_list = get_rooms()
    rooms = room.rstrip("+")
    if rooms:
        for r in rooms.split("/"):
            if r == "$":
                # Get classroom
                classroom = get_classes().get_classroom(course.klass)
                if not classroom:
                    SHOW_ERROR(
                        T["NO_CLASSROOM"].format(
                            klass=course.klass, id=lesson_id
                        )
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
                            klass=course.klass,
                            group=course.group,
                            sid=course.sid,
                            tid=course.tid,
                        )
                    )
                else:
                    rlist.append(r)
    if room[-1] == "+":
        rlist.append("+")
    return rlist or None


# ----------------------------------------------------------
# TODO ...


def get_course_info():
    """Return course information for classes and teachers.
    In particular, this information can be used to build activity tables
    for teachers and classes/groups.
    """
    # Get group info for checking groups
    __classes = get_classes()
    class2groups = {
        klass: __classes.group_info(klass)["GROUPS"]
        for klass, _ in __classes.get_class_list()
    }

    course2data = {}
    class2courses = {}
    teacher2courses = {}
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
        if tid and tid != "--":
            try:
                teacher2courses[tid].append(course)
            except KeyError:
                teacher2courses[tid] = [course]

    course2payroll = {}  # {course-id -> [payroll, ... ]}
    course2block = {}  # {course-id -> [(block-tag, payroll), ... ]}
    course2plain = {}  # {course-id -> [(length, payroll), ... ]}
    block_sublessons = {}  # {block-tag -> [length, ... ]}
    for id, course, length, payroll, time, place in db_read_fields(
        "LESSONS",
        ("id", "course", "LENGTH", "PAYROLL", "TIME", "PLACE"),
    ):
        if course:
            if length == "--" and not time:
                ## non-lesson
                try:
                    course2payroll[course].append(payroll)
                except KeyError:
                    course2payroll[course] = [payroll]
            # TODO: Is it at all sensible to support multiple such entries for a course?

            elif length == "*" and time.startswith(">"):
                ## block-member
                val = (time, payroll)
                try:
                    course2block[course].append(val)
                except KeyError:
                    course2block[course] = [val]

            else:
                try:
                    l = int(length)
                except ValueError:
                    REPORT(
                        "ERROR",
                        T["LENGTH_NOT_NUMBER"].format(id=id, length=length),
                    )
                    continue
                if time and time[0] in "@=":
                    ## plain lesson
                    val = (l, payroll)
                    try:
                        course2plain[course].append(val)
                    except KeyError:
                        course2plain[course] = [val]
                else:
                    REPORT(
                        "ERROR",
                        T["INVALID_LESSON"].format(
                            id=id, length=length, time=time
                        ),
                    )
                    continue

        elif place.startswith(">"):
            ## block-sublesson: add the length to the list for this block-tag
            try:
                i = int(length)
                block_sublessons[place].append(i)
            except KeyError:
                block_sublessons[place] = [i]
            except ValueError:
                raise Bug(
                    f"Invalid block-sublesson: block-tag={place}, length={length}"
                )

        elif not place.startswith("="):
            ## partner-time is ignored, anything else is a bug
            raise Bug(f"LESSON id={id}, error in PLACE field: {place}")

    return {
        "COURSE2DATA": course2data,  # {course-id -> CourseData}
        "CLASS2COURSES": class2courses,  # {class -> {course-id, ... ]}
        "TEACHER2COURSES": teacher2courses,  # {tid -> {course-id, ... ]}
        "COURSE2PAYROLL": course2payroll,  # {course-id -> [payroll, ... ]}
        "COURSE2BLOCK": course2block,  # {course-id -> [(block-tag, payroll), ... ]}
        "COURSE2PLAIN": course2plain,  # {course-id -> [(length, payroll), ... ]}
        "BLOCK_SUBLESSONS": block_sublessons,  # {block-tag -> [length, ... ]}
    }


"""

    def teacher_check_list(self):
        ### Return a "check-list" of the lessons for each teacher.

        lines = []
        tmap = self.lessons_teacher_lists()
        for tid, lessons in tmap.items():
            class_lessons = {}
            for tag, block, klass, sid, groups, dmap, rooms in lessons:
                try:
                    class_list, class_blocks = class_lessons[klass]
                except KeyError:
                    class_list = []
                    class_blocks = []
                    class_lessons[klass] = [class_list, class_blocks]
                n = len(rooms)
                _rooms = f" [{n}: {', '.join(sorted(rooms))}]" if n else ""
                sname = self.SUBJECTS[sid]
                if block == '--':
                    d = list(dmap)[0] if dmap else 0
                    entry = f"    // {sname} [{','.join(groups)}]: EXTRA x {d}"
                    class_blocks.append(entry)
                elif block == '++':
                    ll = ", ".join(lesson_lengths(dmap))
                    entry = f"    // {sname} [{','.join(groups)}]: BLOCK: {ll}{_rooms}"
                    class_blocks.append(entry)
                elif block:
                    # Component
                    blesson = self.lessons[block]
                    bname = self.SUBJECTS[blesson['SID']]
                    if dmap:
                        entry = f"    {sname} [{','.join(groups)}]: EPOCHE ({bname}) x {list(dmap)[0]}"
                    else:
                        entry = f"    {sname} [{','.join(groups)}]: ({bname})"
                    class_list.append(entry)
                else:
                    ll = ", ".join(lesson_lengths(dmap))
                    entry = f"    {sname} [{','.join(groups)}]: {ll}{_rooms}"
                    class_list.append(entry)

            if class_lessons:
                lines.append("")
                lines.append("")
                lines.append(f"$$$ {tid} ({self.TEACHERS[tid]})")
                for klass, clb in class_lessons.items():
                    class_list, class_blocks = clb
                    clines = []
                    clines += class_blocks
                    if class_blocks:
                        clines.append("")
                    clines += class_list
                    if clines:
                        lines.append("")
                        lines.append(f"  Klasse {klass}:")
                        lines += clines
        return "\n".join(lines)

"""


def blockdata(course_info, course):
    for blocktag, payroll in course_info["COURSE2BLOCK"]:
        sublessons = course_info["BLOCK_SUBLESSONS"][blocktag]
        coursedata = course_info["COURSE2DATA"][blocktag]
        # Need header ("Block", etc.), group, subject sublessons, payroll (+ room?)
        group = coursedata.group or "--"
        subjects = get_subjects()
        subject = subjects.map(coursedata.sid)
        block = subjects.map(blocktag2blocksid(blocktag))
        # If payroll has a number and this is not the same as the number
        # of lessons, this is continuous, not an EPOCHE.
        n, f = payroll.split("*", 1)
        # TODO: error handling

        ltotal = sum(sublessons)
        if n:
            # ???
            if n > ltotal:
                REPORT("ERROR", T["TOO_MUCH_PAY"].format(course=course))
            btype = _EPOCHE
        else:
            n = ltotal
        pay = f"{n * get_payroll_weights().map(f):.2f}".replace(
            ".", DECIMAL_SEP
        )


# TODO ...


class TeacherCourses(Courses):
# TODO ...
# Include ROOM field
    def teacher_class_subjects(self, block_tids=None):
        """For each teacher, present the subjects/courses together with
        groups, rooms etc.
        If <block_tids> is supplied, it should be a set of teacher-ids which
        will be "blocked", i.e. not appear in the output.
        Build a list of "pages", one for each teacher, with a list of his/her
        classes and subjects.

        Divide the information into blocks, plain lessons and payroll-only
        entries. Each of these sections should have the subjects and
        groups ordered alphabetically.
        """
        teachers = get_teachers()
        if block_tids is None:
            block_tids = set()
        tlist = []
        for tid in teachers:
            tname = teachers.name(tid)
            if tid in block_tids:
                REPORT("INFO", T["TEACHER_SUPPRESSED"].format(tname=tname))
                continue
            try:
                courses = self.teacher2courses[tid]
            except KeyError:
                ## teacher has no entries
                REPORT("INFO", T["TEACHER_NO_COURSES"].format(tname=tname))
                continue
            print(f"\n*** {tname} ***")
            blocks = []
            plains = []
            payrolls = []
            for course in courses:
                cdata = self.course2data[course]
                print("  +++", cdata)

#TODO: Maybe blocks should not be treated as blocks when there is no
# number for the payroll AND member subject == block subject?
# Maybe being a block or "plain" is not really so important?
# I should collect co-teachers? Actually only relevant for parallel
# lessons handled as blocks. But I should gather tag maps anyway!

                try:
                    # Get the block members
                    lids = self.course2block[course]
                    print("    --- BLOCKS")
                    for lid in lids:
                        print("      ...", self.lesson2data[lid])
#TODO
                except KeyError:
                    pass
                try:
                    # Get the plain lessons
                    lids = self.course2plain[course]
                    print("    --- LESSONS")
                    for lid in lids:
                        print("      ...", self.lesson2data[lid])
#TODO
                except KeyError:
                    pass
                try:
                    # Get the payroll-only entries
                    lids = self.course2payroll[course]
                    print("    --- EXTRA")
                    for lid in lids:
                        print("      ...", self.lesson2data[lid])
#TODO
                except KeyError:
                    pass

#        self.block_sublessons = {}  # {block-tag -> [lesson-id, ... ]}



        return
#TODO ...
        for tid, tname, clist in teacher_subjects:
            if tid in block_tids:
                REPORT("INFO", _SUPPRESSED.format(tname=tname))
                continue
            else:
                tlist.append((f"{tname} ({tid})", clist))

        pdf = PdfCreator()
        return pdf.build_pdf(
            tlist, title="Lehrer-Klassen-Fächer", author="FWS Bothfeld"
        )


BASE_MARGIN = 20 * mm
# TODO
class PdfCreator:
    def add_page_number(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Times-Roman", 12)
        page_number_text = "%d" % (doc.page)
        canvas.drawCentredString(18 * mm, 18 * mm, page_number_text)
        canvas.restoreState()

    def build_pdf(self, pagelist, title, author):
        pdf_buffer = BytesIO()
        my_doc = SimpleDocTemplate(
            pdf_buffer,
            title=title,
            author=author,
            pagesize=A4,
            topMargin=BASE_MARGIN,
            leftMargin=BASE_MARGIN,
            rightMargin=BASE_MARGIN,
            bottomMargin=BASE_MARGIN,
        )
        sample_style_sheet = getSampleStyleSheet()
        body_style = sample_style_sheet["BodyText"]
        body_style.fontSize = 14
        body_style.leading = 20
        heading_style = sample_style_sheet["Heading1"]
        heading_style.spaceAfter = 24
        class_style = sample_style_sheet["Heading2"]
        class_style.spaceBefore = 25
        # print("\n STYLES:", sample_style_sheet.list())

        flowables = []
        for teacher, clist in pagelist:
            flowables.append(Paragraph(teacher, heading_style))
            for klass, slist in clist:
                flowables.append(Paragraph(klass, class_style))
                for subject in slist:
                    if subject:
                        flowables.append(Paragraph(subject, body_style))
                    else:
                        flowables.append(Spacer(1, 4 * mm))
            flowables.append(PageBreak())
        my_doc.build(
            flowables,
            onFirstPage=self.add_page_number,
            onLaterPages=self.add_page_number,
        )
        pdf_value = pdf_buffer.getvalue()
        pdf_buffer.close()
        return pdf_value


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from core.db_management import open_database

    open_database()

    courses = TeacherCourses()
    courses.teacher_class_subjects()

    quit(0)

    course_info = get_course_info()
    class2courses = course_info["CLASS2COURSES"]
    for c in sorted(class2courses):
        info = class2courses[c]
        print(f"\nCLASS {c}:")
        print("  ...", info)
