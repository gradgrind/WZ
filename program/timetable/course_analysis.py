"""
timetable/courses.py

Last updated:  2022-06-28

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

#TODO: Move to translations:
_SUPPRESSED = "Lehrkraft ausgeschlossen: {tname}"

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
from core.basic_data import get_classes, get_teachers
from timetable.courses import CourseData, blocktag2blocksid

### -----


class CourseData(NamedTuple):
    klass: str
    group: str
    sid: str
    tid: str


class LessonData(NamedTuple):
    id: int
    course: Optional[int]
    #course: Optional[CourseData]
    length: str
    payroll: str
    room: str
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
        self.lesson2data = {}       # {lesson-id -> <LessonData>}
        self.partners_time = {}     # {partner-tag -> lesson-id}
        self.course2payroll = {}    # {course-id -> [lesson-id, ... ]}
        self.course2block = {}      # {course-id -> [lesson-id, ... ]}
        self.course2plain = {}      # {course-id -> [lesson-id, ... ]}
        self.block_sublessons = {}  # {block-tag -> [lesson-id, ... ]}
        for id, course, length, payroll, room, time, place in db_read_fields(
            "LESSONS",
            ("id", "course", "LENGTH", "PAYROLL", "ROOM", "TIME", "PLACE"),
        ):
            if course:
                if length == "--":
                    ## non-lesson
                    if time or place or room:
                        REPORT("ERROR", T["INVALID_NON_LESSON"].format(id=id))
                        continue
                    try:
                        self.course2payroll[course].append(id)
                    except KeyError:
                        self.course2payroll[course] = [id]
#TODO: Is it at all sensible to support multiple such entries for a course?

                elif length == "*":
                    if not time.startswith(">"):
                        REPORT("ERROR", T["INVALID_BLOCK"].format(id=id))
                        continue
                    ## block-member
                    try:
                        self.course2block[course].append(id)
                    except KeyError:
                        self.course2block[course] = [id]

                else:
                    if not length.isnumeric():
                        REPORT("ERROR", T["LENGTH_NOT_NUMBER"].format(
                            id=id, length=length)
                        )
                        continue
                    if time and time[0] in "@=":
                        ## plain lesson
                        try:
                            self.course2plain[course].append(id)
                        except KeyError:
                            self.course2plain[course] = [id]
                    else:
                        REPORT("ERROR", T["INVALID_PLAIN_LESSON"].format(
                            id=id, length=length, time=time)
                        )
                        continue

            elif place.startswith(">"):
                ## block-sublesson: add the length to the list for this block-tag
                if not length.isnumeric():
                    REPORT("ERROR", T["LENGTH_NOT_NUMBER"].format(
                        id=id, length=length)
                    )
                    continue
                try:
                    self.block_sublessons[place].append(id)
                except KeyError:
                    self.block_sublessons[place] = [id]

            elif place.startswith("="):
                ## partner-time
                if place in self.partners_time:
                    REPORT("ERROR", T["DOUBLE_PARTNER_TIME"].format(tag=place))
                    continue
                else:
                    self.partners_time[place] = id

            else:
                ## anything else is a bug
                REPORT("ERROR", T["INVALID_LESSON"].format(id=id))
                continue

            self.lesson2data[id] = LessonData(
                id=id,
                course=course,
                length=length,
                payroll=payroll,
                room=room,
                time=time,
                place=place,
            )




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

    course2payroll = {}     # {course-id -> [payroll, ... ]}
    course2block = {}       # {course-id -> [(block-tag, payroll), ... ]}
    course2plain = {}       # {course-id -> [(length, payroll), ... ]}
    block_sublessons = {}   # {block-tag -> [length, ... ]}
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
#TODO: Is it at all sensible to support multiple such entries for a course?

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
                    REPORT("ERROR", T["LENGTH_NOT_NUMBER"].format(
                        id=id, length=length)
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
                    REPORT("ERROR", T["INVALID_LESSON"].format(
                        id=id, length=length, time=time)
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
                raise Bug(f"Invalid block-sublesson: block-tag={place}, length={length}")

        elif not place.startswith("="):
            ## partner-time is ignored, anything else is a bug
            raise Bug(f"LESSON id={id}, error in PLACE field: {place}")

    return {
        "COURSE2DATA":    course2data,      # {course-id -> CourseData}
        "CLASS2COURSES":  class2courses,    # {class -> {course-id, ... ]}
        "TEACHER2COURSES": teacher2courses, # {tid -> {course-id, ... ]}
        "COURSE2PAYROLL": course2payroll,   # {course-id -> [payroll, ... ]}
        "COURSE2BLOCK":   course2block,     # {course-id -> [(block-tag, payroll), ... ]}
        "COURSE2PLAIN":   course2plain,     # {course-id -> [(length, payroll), ... ]}
        "BLOCK_SUBLESSONS": block_sublessons # {block-tag -> [length, ... ]}
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
#TODO: error handling

        ltotal = sum(sublessons)
        if n:
#???
            if n > ltotal:
                REPORT("ERROR", T["TOO_MUCH_PAY"].format(course=course))
            btype = _EPOCHE
        else:
            n = ltotal
        pay = f"{n * get_payroll_weights().map(f):.2f}".replace(".", DECIMAL_SEP)
#TODO ...


#TODO ...
# Include ROOM field?
def teacher_class_subjects(course_info, block_tids=None):
    """For each teacher, present the subjects/courses together with
    groups, rooms etc.
    If <block_tids> is supplied, it should be a set of teacher-ids which
    will be "blocked", i.e. not appear in the output.
    Build a list of "pages", one for each teacher, with a list of his/her
    classes and subjects.
    """
    teachers = get_teachers()
    tid2courses = course_info["TEACHER2COURSES"]
    course2data = course_info["COURSE2DATA"]
    if block_tids is None:
        block_tids = set()
    tlist = []
    for tid in teachers:
        try:
            courses = tid2courses[tid]
        except KeyError:
            ## teacher has no entries
            continue
        if tid in block_tids:
            REPORT("INFO", _SUPPRESSED.format(tname=tname))
            continue
        tname = teachers.name(tid)
        for course in courses:
            cdata = course2data[course]


    for tid, tname, clist in teacher_subjects:
        if tid in block_tids:
            REPORT("INFO", _SUPPRESSED.format(tname=tname))
            continue
        else:
            tlist.append((f"{tname} ({tid})", clist))

    pdf = PdfCreator()
    return pdf.build_pdf(tlist, title="Lehrer-Klassen-Fächer",
            author="FWS Bothfeld")


BASE_MARGIN = 20 * mm
#TODO
class PdfCreator:
    def add_page_number(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman', 12)
        page_number_text = "%d" % (doc.page)
        canvas.drawCentredString(
            18 * mm,
            18 * mm,
            page_number_text
        )
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
            bottomMargin=BASE_MARGIN
        )
        sample_style_sheet = getSampleStyleSheet()
        body_style = sample_style_sheet['BodyText']
        body_style.fontSize = 14
        body_style.leading = 20
        heading_style = sample_style_sheet['Heading1']
        heading_style.spaceAfter = 24
        class_style = sample_style_sheet['Heading2']
        class_style.spaceBefore = 25
        #print("\n STYLES:", sample_style_sheet.list())

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

    courses = Courses()

    quit(0)

    course_info = get_course_info()
    class2courses = course_info["CLASS2COURSES"]
    for c in sorted(class2courses):
        info = class2courses[c]
        print(f"\nCLASS {c}:")
        print("  ...", info)
