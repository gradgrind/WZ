"""
timetable/activities.py

Last updated:  2022-07-17

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

T = TRANSLATIONS("timetable.activities")

### +++++

from typing import NamedTuple, Optional

from io import BytesIO
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    PageBreak,
    Spacer,
    Preformatted
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_RIGHT


from core.db_access import db_read_fields
from core.basic_data import (
    get_classes,
    get_teachers,
    get_subjects,
    get_rooms,
    get_payment_weights,
    read_payment,
    read_block_tag,
    BlockTag,
    PaymentData,
)

### -----


class CourseData(NamedTuple):
    klass: str
    group: str
    sid: str
    tid: str

    def __str__(self):
        return T["CourseData"].format(
            klass=self.klass, group=self.group, sid=self.sid, tid=self.tid
        )


class BlockInfo(NamedTuple):
    course: CourseData
    lessons: list[int]
    block: BlockTag
    rooms: list[str]
    payment_data: PaymentData
    notes: str


def lesson_rooms(room: str, course: CourseData, lesson_id: int) -> list[str]:
    """Read a list of possible rooms for the given lesson.
    Check the validity of the individual rooms, convert '$' to the
    corresponding classroom.
    The lesson-id is only passed for use in error messages.
    """
    if not room:
        return []
    rlist = []
    room_list = get_rooms()
    rooms = room.rstrip("+")
    if rooms:
        for r in rooms.split("/"):
            if r == "$":
                # Get classroom
                classroom = get_classes().get_classroom(course.klass)
                if not classroom:
                    REPORT(
                        "ERROR",
                        T["NO_CLASSROOM"].format(course=course, id=lesson_id),
                    )
                    continue
                rlist.append(classroom)
            else:
                try:
                    room_list.index(r)
                except KeyError:
                    REPORT(
                        "ERROR",
                        T["UNKNOWN_ROOM"].format(
                            rid=r, course=course, id=lesson_id
                        ),
                    )
                else:
                    rlist.append(r)
    if room[-1] == "+":
        rlist.append("+")
    return rlist


#TODO: Am I checking that also rooms are the same (or empty) in partner-courses?
class Courses:
    def __init__(self):
        ### First read the COURSES table.
        classes = get_classes()
        class2groups = {
            klass: classes.group_info(klass)["GROUPS"]
            for klass, _ in classes.get_class_list()
        }
        course2data = {}
        payment_weights = get_payment_weights()
        for course, klass, group, sid, tid in db_read_fields(
            "COURSES", ("course", "CLASS", "GRP", "SUBJECT", "TEACHER")
        ):
            # CLASS, SUBJECT and TEACHER are foreign keys and should be
            # automatically bound to appropriate entries in the database.
            # GRP should be checked here ...
            if group and group not in class2groups[klass]:
                if klass != "--" and group != "*":
                    REPORT(
                        "ERROR",
                        T["UNKNOWN_GROUP"].format(
                            klass=klass, group=group, sid=sid, tid=tid
                        )
                    )
                    continue
            course2data[course] = CourseData(
                klass=klass, group=group, sid=sid, tid=tid
            )
            if not tid:
                raise Bug(f"Empty teacher field in {course2data[course]}")

#                try:
#                    self.teacher2courses[tid].append(course)
#                except KeyError:
#                    self.teacher2courses[tid] = [course]

        ### Now read the LESSONS table.
        ## Block sublessons are the records for the actual lessons:
        sublesson_lengths = {}      # {block-tag -> [length, ... ]}
        for tag, length in db_read_fields("LESSONS", ("TAG", "LENGTH")):
            try:
                sublesson_lengths[tag].append(length)
            except KeyError:
                sublesson_lengths[tag] = [length]

        ### Now read the BLOCKS table.
        self.paydata = []       # [(CourseData, PaymentData), ... ]
        self.tid2paydata = {}   # {tid -> [(CourseData, PaymentData), ... ]}
        tag2entries = {}    # {block-tag -> [BlockInfo, ... ]}
        self.tag2entries = tag2entries
        tid2tags = {}   # {tid -> {block-tag -> [BlockInfo, ... ]}}
        self.tid2tags = tid2tags
        klass2tags = {} # {klass -> {block-tag -> [BlockInfo, ... ]}}
        self.klass2tags = klass2tags
        # Collect payment-only entries for courses (check for multiple entries):
        paycourses = set()
        # The "id" field is read only for error reports
        for id, course, payment, room, tag, notes in db_read_fields(
            "BLOCKS",
            ("id", "course", "PAYMENT", "ROOM", "LESSON_TAG", "NOTES"),
        ):
            coursedata = course2data[course]
            try:
                payment_data = read_payment(payment)
            except ValueError as e:
                REPORT(
                    "ERROR",
                    T["LESSON_ERROR"].format(id=id, course=coursedata, e=e),
                )
                continue
            if tag:
                ## Build a mapping {tag -> [BlockInfo, ... ]}.
                try:
                    blocktag = read_block_tag(tag)
                except ValueError as e:
                    REPORT(
                        "ERROR",
                        T["LESSON_ERROR"].format(id=id, course=coursedata, e=e),
                    )
                    continue
                try:
                    lessons = sublesson_lengths[tag]
                except KeyError as e:
                    REPORT(
                        "ERROR",
                        f"(DB-BLOCKS, {coursedata}) TAG ({tag}) -> LENGTHS: {e}"
                    )
                    continue
                roomlist = lesson_rooms(room, coursedata, id)
                entry = BlockInfo(
                    coursedata, lessons, blocktag, roomlist, payment_data, notes
                )
                try:
                    tag2entries[tag].append(entry)
                except KeyError:
                    tag2entries[tag] = [entry]

                # Add to teacher mapping
                tid = coursedata.tid
                try:
                    __tag2entries = tid2tags[tid]
                except KeyError:
                    tid2tags[tid] = {tag: [entry]}
                else:
                    try:
                        __tag2entries[tag].append(entry)
                    except KeyError:
                        __tag2entries[tag] = [entry]

                # Add to class mapping
                klass = coursedata.klass
                try:
                    __tag2entries = klass2tags[tid]
                except KeyError:
                    klass2tags[tid] = {tag: [entry]}
                else:
                    try:
                        __tag2entries[tag].append(entry)
                    except KeyError:
                        __tag2entries[tag] = [entry]

            else:
                ## non-lesson, additional duties (with payment) for teachers
                if room:
                    REPORT(
                        "ERROR",
                        T["ROOM_NON_LESSON"].format(
                            id=id, course=coursedata, room=room
                        ),
                    )
                    continue
                if coursedata.tid == "--":
                    REPORT(
                        "ERROR",
                        T["NON_LESSON_NO_TEACHER"].format(
                            id=id, course=coursedata
                        ),
                    )
                    continue
                if not payment_data[0]:
                    REPORT(
                        "ERROR",
                        T["PAYMENT_NO_NUMBER"].format(
                            id=id, course=coursedata, payment=payment
                        ),
                    )
                pd = (coursedata, payment_data)
                self.paydata.append(pd)

                # Add to teacher mapping
                tid = coursedata.tid
                try:
                    self.tid2paydata[tid].append(pd)
                except KeyError:
                    self.tid2paydata [tid] = [pd]

                # Check multiple such entries for any one course
                if course in paycourses:
                    REPORT(
                        "WARNING",
                        T["COURSE_MULTIPLE_PAY"].format(course=coursedata)
                    )
                else:
                    paycourses.add(course)


# The main criterion for differentiation is probably the comparison of
# course-subject with block-subject.
# There are "blocks" without a block-subject, just a tag. These are
# normally plain lesson "blocks". Indeed I have tried in the editor to
# prevent these tags from being shared between courses.
# There is also the "number" part of a "payment". If this is empty, the
# item is to be regarded as continuous, not in time-blocks. Could there
# be valid reasons for giving even these a number?

# Treat payments with no number as a special case.
# As all the lessons are used, there can be no other
# subjects for a given teacher. There can be the same
# subject in another group, which implies combining the
# groups.
# If the course name is the same as the block name, it
# can be treated as a normal subject with more than one
# group.
# I suppose if there was only one course of a block in
# a class (probably rather unlikely ... better handled
# as parallel lessons?), I could use the course name
# instead of the block name?

# TODO: Maybe blocks should not be treated as blocks when there is no
# number for the payment AND member subject == block subject?
# Maybe being a block or "plain" is not really so important?
# I should collect co-teachers? Actually only relevant for parallel
# lessons handled as blocks. But I should gather tag maps anyway!

# TODO: IMPORTANT!
# There are cases where blocks are used for teaching simultaneously in
# several groups. I'm not sure that my data structures cover this
# properly. If no number is given for a member, it means "continuous",
# i.e. not in time-blocks. If a teacher has members of the same block-tag
# in more than one class and these are continuous, then these cannot
# be cumulative. However if they really are parallel, but not continuous
# there is no way to distinguish them from separate time-blocks.
# Perhaps a special marker could be used in the LENGTH field for parallel
# blocks?
# Another possibility would be the PAYMENT entry. This could have a special
# tag to indicate sharing, or fractional numbers could be used. The former
# should allow easier tracing of the parallel classes.
# Actually, the PAYMENT field is the better choice, because this detail
# is not directly relevant for the timetabling itself. It might also be
# worth considering restricting the number component to integer values
# (for compatibility with the LENGTH field, and given the possiblity of
# handling fractional values in the factor-part).

# Normally a block subject is identified by class.group, teacher and subject,
# i.e. the "course". For any given block-tag, a course may have only one
# entry. The number of lessons can be added up and should result in a
# number smaller than or equal to the number of lessons for the block-tag.
# However, the parallel flag indicates that two or more groups are
# taught at the same time, so their lessons should not be added more
# than once.
# The information needed for a teacher is a list of subjects, together
# with their class.groups, room and payment entry. There is also the
# lesson contingent, but that is common to all entries. So, something like:
#    BLOCK Hauptunterricht # – Stunden: [2,2,2,2,2]
#      Mathematik (09G.alle, 09K.alle) {} – 2 Epochen
#      Physik (09G.alle) {rPh} – 1 Epoche
#
#    BLOCK Mathematik #09 – Stunden: [1,1]
#      Mathematik (09G.B, 09K.alle) {r09G} – durchgehend
#
# Ideally the latter would be displayed differently, because it is not
# really a block, actually it is a normal lesson, but it uses the block
# form to include the other class. Something like:
#    FACHSTUNDEN
#      Mathematik (09G.B, 09K.alle) {r09G} – Stunden: [1,1]
#
# This special case would arise when an empty number of lessons is
# specified in the payment field AND when the block and course subjects
# are the same.

        # self.paydata:                 [(CourseData, PaymentData), ... ]
        # self.tid2paydata:     {tid -> [(CourseData, PaymentData), ... ]}
        # self.tag2entries:             {block-tag -> [BlockInfo, ... ]}
        # self.tid2tags:        {tid -> {block-tag -> [BlockInfo, ... ]}}
        # self.klass2tags:      {klass -> {block-tag -> [BlockInfo, ... ]}}

    def teacher_class_subjects(self):
        """Organize the data according to teachers and classes, keeping
        data for real lessons and payment-only entries separate.
        Return an ordered list of the teachers, each with his/her own data.
        The entries in this list are tuples:
            teacher-id: str
            teacher-name: str
            lesson-data: {class -> {tag -> [BlockInfo, ... ]}}
            payment-only-data: {class -> [(CourseData, PaymentData), ... ]}
            partner-courses: {partner-tag -> [CourseData, ... ]}
        A partner-tag is just the block-tag for "continuous" items; if
        there is a pay-tag, the partner-tag is "block-tag+sid&pay-tag".
        """
        teachers = get_teachers()
        tlist = []
        for tid in teachers:
            tname = teachers.name(tid)
            ### Divide the data into classes
            ## lesson data
            c2tags = {}
            tag2courses = {}    # {partner-tag -> [course, ... ]}
            for tag, blockinfolist in (self.tid2tags.get(tid) or {}).items():
                continuous = None
                total_length = 0
                tagged = {}
                plain = []
                for blockinfo in blockinfolist:
                    payinfo = blockinfo.payment_data
                    course = blockinfo.course

                    if not blockinfo.block.sid:
                        ## A "plain" lesson
                        # No block-sid, nothing parallel
                        if len(blockinfolist) > 1:
                            REPORT(
                                "ERROR",
                                T["BAD_PLAIN_BLOCK"].format(
                                    course=course,
                                    tag=tag
                                )
                            )
                            continue
                        else:
                            plain.append(blockinfo)

                    elif payinfo.number:
                        if payinfo.tag:
                            stkey = f"{course.sid}&{payinfo.tag}"
                            try:
                                clist, pay, rooms = tagged[stkey]
                            except KeyError:
                                __courses = [course]
                                tagged[stkey] = (
                                    __courses,
                                    (payinfo.number, payinfo.factor),
                                    blockinfo.rooms
                                )
                                tag2courses[f"{tag}+{stkey}"] = __courses
                            else:
                                if pay != (payinfo.number, payinfo.factor):
                                    REPORT(
                                        "ERROR",
                                        T["PARTNER_PAY_MISMATCH"].format(
                                            course1=clist[0],
                                            course2=course,
                                            tag=tag
                                        )
                                    )
                                    continue
                                if (
                                    rooms
                                    and blockinfo.rooms
                                    and blockinfo.rooms != rooms
                                ):
                                    REPORT(
                                        "ERROR",
                                        T["PARTNER_ROOM_MISMATCH"].format(
                                            course1=clist[0],
                                            course2=course,
                                            tag=tag
                                        )
                                    )
                                    continue
                                clist.append(course)

                        # else: A normal block member

                        total_length += payinfo.number_val

                    else:
                        # All parallel items must have the same subject
                        # and payment, and same (or null) rooms
                        if payinfo.tag:
                            # A pay-tag would be superfluous as only one
                            # "continuous" item is allowed anyway.
                            REPORT(
                                "ERROR",
                                T["CONTINUOUS_BLOCK_TAG"].format(
                                    course=course, tag=tag
                                )
                            )
                            continue
                        if continuous:
                            if continuous[1] != (
                                payinfo.number, payinfo.factor
                            ):
                                REPORT(
                                    "ERROR",
                                    T["PARTNER_PAY_MISMATCH"].format(
                                        course1=continuous[0][0],
                                        course2=course,
                                        tag=tag
                                    )
                                )
                                continue
                            if continuous[0][0].sid != course.sid:
                                REPORT(
                                    "ERROR",
                                    T["PARTNER_SID_MISMATCH"].format(
                                        course1=continuous[0][0],
                                        course2=course,
                                        tag=tag
                                    )
                                )
                                continue
                            if (
                                continuous[2]
                                and blockinfo.rooms
                                and blockinfo.rooms != continuous[2]
                            ):
                                REPORT(
                                    "ERROR",
                                    T["PARTNER_ROOM_MISMATCH"].format(
                                        course1=continuous[0][0],
                                        course2=course,
                                        tag=tag
                                    )
                                )
                                continue
                            continuous[0].append(course)
                        else:
                            continuous = (
                                [course],
                                (payinfo.number, payinfo.factor),
                                blockinfo.rooms
                            )
                            tag2courses[tag] = continuous[0]

                    klass = blockinfo.course.klass
                    try:
                        tag2blockinfo = c2tags[klass]
                    except KeyError:
                        c2tags[klass] = {tag: [blockinfo]}
                    else:
                        try:
                            tag2blockinfo[tag].append(blockinfo)
                        except KeyError:
                            tag2blockinfo[tag] = [blockinfo]

                if continuous:
                    if total_length:
                        REPORT(
                            "ERROR",
                            T["CONTINUOUS_PLUS_OTHERS"].format(
                                course=continuous[0][0],
                                tag=tag
                            )
                        )
                elif total_length > sum(blockinfolist[0].lessons):
                    REPORT(
                        "WARNING",
                        T["BLOCK_TOO_FULL"].format(
                            teacher=tname,
                            tag=tag
                        )
                    )

            ## Payment-only data
            c2paydata = {}
            for course_pay_data in (self.tid2paydata.get(tid) or []):
                klass = course_pay_data[0].klass
                try:
                    c2paydata[klass].append(course_pay_data)
                except KeyError:
                    c2paydata[klass] = [course_pay_data]
            ### Add teacher data to list of all teachers
            tlist.append((tid, tname, c2tags, c2paydata, tag2courses))
        return tlist


def print_teachers(teacher_data, block_tids=None, show_workload=False):
    def partners(tag, course) -> tuple[int,str]:
        try:
            courses = tag2courses[tag]
        except KeyError:
            return ""
        glist = [
            c.klass if c.group == '*' else f"{c.klass}.{c.group}"
            for c in courses
            if c != course
        ]
        return (len(glist), f' ({", ".join(glist)})' if glist else "")

    def workload(
        paymentdata:PaymentData,
        lessons:Optional[list[int]]=None,
        ngroups:int=0   # number of other groups
    ) -> tuple[float,str]:
        if paymentdata.number:
            n = paymentdata.number
            nd = paymentdata.number_val
        else:
            if lessons is None:
                n = "?"
                nd = 0.0
            else:
                n = sum(lessons)
                nd = float(n)
        val = nd*paymentdata.factor_val
        if ngroups:
            shared = f" /{ngroups+1}"
            val /= 2.0
        else:
            shared = ""
        if show_workload:
            text = f"$>>> {n} × {paymentdata.factor}{shared} = {val:.3f}"
        else:
            text = ""
        return (val, text)

    blocked_tids = set() if block_tids is None else set(block_tids)
    classes = get_classes().get_class_list(skip_null=False)

#?
#    class_lessons = {}
#    def class_lists(k):
#        try:
#            return class_lessons[k] # (class_list, class_blocks, class_payonly)
#        except KeyError:
#            lb = ([], [], [])
#            class_lessons[k] = lb
#            return lb
# ...
#        class_lessons.clear()
# ...
#        class_list, class_blocks, class_payonly = class_lists(klass)

    teacherlists = []
    for tid, tname, c2tags, c2paydata, tag2courses in teacher_data:
        if tid in blocked_tids:
            REPORT("INFO", T["TEACHER_SUPPRESSED"].format(tname=tname))
            continue
        if not (c2tags or c2paydata):
            REPORT("INFO", T["TEACHER_NO_ACTIVITIES"].format(tname=tname))
            continue
        print("\n $$$$$$", tname)
        classlists = []
        pay_total = 0.0
        for klass, kname in classes:
            class_list, class_blocks, class_payonly = [], {}, []
            try:
                tags = c2tags[klass]
            except KeyError:
                pass
            else:
                for tag, blockinfolist in tags.items():
                    #print("???TAG", tag)
                    block = blockinfolist[0].block
                    if block.sid:
                        bname = block.subject
                        for blockinfo in blockinfolist:
                            course = blockinfo.course
                            sname = get_subjects().map(course.sid)
                            rooms = f'{{{"|".join(blockinfo.rooms)}}}'
                            lessons = f'[{",".join(map(str, blockinfo.lessons))}]'
                            payment = blockinfo.payment_data
                            if payment.number:
                                # With number of units taught
                                if payment.tag:
                                    n, plist = partners(
                                        f"{tag}+{course.sid}&{payment.tag}",
                                        course
                                    )
                                else:
                                    n, plist = 0, ""
                                pay, paytext = workload(
                                    payment,
                                    blockinfo.lessons,
                                    n
                                )
                                pay_total += pay
                                text = (
                                    f"  {sname + plist:<18}"
                                    f" {rooms:<12}"
                                    f" × {payment.number}"
                                    + paytext
                                )
                                try:
                                    class_blocks[bname][1].append(text)
                                except KeyError:
                                    class_blocks[bname] = (
                                        lessons,
                                        [text]
                                    )
                                print(f"%%% ({bname} {lessons}) {text}")

                            else:
                                # Continuous teaching
                                n, plist = partners(tag, course)
                                pay, paytext = workload(
                                    payment,
                                    blockinfo.lessons,
                                    n
                                )
                                pay_total += pay
                                if course.sid == block.sid:
                                    class_list.append(
                                        f"  {sname + plist:<18}"
                                        f" {rooms:<12}"
                                        f" – {T['lessons']}: {lessons:<12}"
                                        + paytext
                                    )
                                    print("§§§", class_list[-1])

                                else:
                                    pay, paytext = workload(
                                        payment,
                                        blockinfo.lessons
                                    )
                                    pay_total += pay
                                    text = (
                                        f"  {sname:<18}"
                                        f" {rooms:<12}"
                                        " {T['continuous']}"
                                        + paytext
                                    )
                                    try:
                                        class_blocks[bname][1].append(text)
                                    except KeyError:
                                        class_blocks[bname] = (
                                            lessons,
                                            [text]
                                        )
                                    print(f"&&& ({bname} {lessons}) {text}")

                    else:
                        ## Simple, plain lesson block
                        blockinfo = blockinfolist[0]
                        course = blockinfo.course
                        sname = get_subjects().map(course.sid)
                        rooms = f'{{{"|".join(blockinfo.rooms)}}}'
                        lessons = f'[{",".join(map(str, blockinfo.lessons))}]'
                        pay, paytext = workload(
                            blockinfo.payment_data,
                            blockinfo.lessons
                        )
                        pay_total += pay
                        class_list.append(
                            f"  {sname:<18}"
                            f" {rooms:<12}"
                            f" – {T['lessons']}: {lessons:<12}"
                            + paytext
                        )
                        print("§§§", class_list[-1])

#    BLOCK Hauptunterricht # – Stunden: [2,2,2,2,2]
#      Mathematik (09G.alle, 09K.alle) {} – 2 Epochen
#      Physik (09G.alle) {rPh} – 1 Epoche
#
#    BLOCK Mathematik #09 – Stunden: [1,1]
#      Mathematik (09G.B, 09K.alle) {r09G} – durchgehend
#
# Ideally the latter would be displayed differently, because it is not
# really a block, actually it is a normal lesson, but it uses the block
# form to include the other class. Something like:
#    FACHSTUNDEN
#      Mathematik (09G.B, 09K.alle) {r09G} – Stunden: [1,1]

            try:
                paydata = c2paydata[klass]
            except KeyError:
                pass
            else:
                for course, pd in paydata:
                    pay, paytext = workload(pd)
                    pay_total += pay
                    sname = get_subjects().map(course.sid)
                    class_payonly.append(
                        f"    {sname:<20}"
                        + paytext
                    )

            # Collate the various activities
            all_items = []
            for bname, data in class_blocks.items():
                all_items.append(f"BLOCK: {bname:>18} {data[0]}")
                for line in data[1]:
                    all_items.append(line)
            all_items += class_list
            if show_workload:
                all_items += class_payonly
            if all_items:
                classlists.append((klass, all_items))

        xtid = f"({tid})"
        teacherline = f"{tname:<30} {xtid:>6}"
        if show_workload:
            teacherline += f" {pay_total:.2f}"
        print("  +++++++++++++++++++++", teacherline)
        teacherlists.append((teacherline, classlists))

    pdf = PdfCreator()
    return pdf.build_pdf(
        teacherlists, title="Lehrer-Klassen-Fächer", author="FWS Bothfeld"
    )


BASE_MARGIN = 20 * mm
# TODO
import copy

class MyDocTemplate(SimpleDocTemplate):
    def __init__(self, *args, **kargs):
        self.key = 0
        super().__init__(*args, **kargs)

    def handle_flowable(self, flowables):
        if flowables:
            flowable = flowables[0]
            if (
                isinstance(flowable, Paragraph)
                and flowable.style.name == 'Heading1'
            ):
                t = flowable.getPlainText().split("(", 1)[0].rstrip()
                self.key += 1
                k = f"key_{self.key}"
                self.canv.bookmarkPage(k)
                self.canv.addOutlineEntry(t, k, 0, 1)
        super().handle_flowable(flowables)


class PdfCreator:
    def add_page_number(self, canvas, doc):
#        key = f"t{doc.page}"
#        canvas.bookmarkPage(key)
#        canvas.addOutlineEntry(self.teacher, key, 0, 1)
        canvas.saveState()
        canvas.setFont("Times-Roman", 12)
        page_number_text = "%d" % (doc.page)
        canvas.drawCentredString(18 * mm, 18 * mm, page_number_text)
        canvas.restoreState()

    def build_pdf(self, pagelist, title, author):
        pdf_buffer = BytesIO()
        my_doc = MyDocTemplate(
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
        #body_style = sample_style_sheet["BodyText"]
        body_style = sample_style_sheet["Code"]
        body_style.fontSize = 12
        body_style.leading = 14
        body_style.alignment = 1
        body_style.leftIndent = 0

        body_style_2 = copy.deepcopy(body_style)
        body_style.spaceBefore = 10

        body_style_2.alignment = TA_RIGHT
        heading_style = sample_style_sheet["Heading1"]
        heading_style.fontSize = 16
        heading_style.spaceAfter = 24
        class_style = sample_style_sheet["Heading2"]
        class_style.fontSize = 13
        class_style.spaceBefore = 20
        # print("\n STYLES:", sample_style_sheet.list())

        flowables = []
        for teacher, clist in pagelist:
            h = Paragraph(teacher, heading_style)
#             self.teacher = teacher
            flowables.append(h)
            for klass, slist in clist:
                flowables.append(Paragraph(klass, class_style))
                for subject in slist:
                    if subject:
                        lines = subject.split("$")
#                        flowables.append(Paragraph(subject, body_style))
                        flowables.append(
                            Preformatted(
                                lines[0],
                                body_style,
                                maxLineLength=70,
                                newLineChars=' '
                            )
                        )
                        for line in lines[1:]:
                            flowables.append(
                                Paragraph(
                                    line,
                                    body_style_2,
                                )
                            )
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
    from core.db_access import open_database
    from ui.ui_base import saveDialog

    open_database()

    def run_me():
        courses = Courses()
        tlist = courses.teacher_class_subjects()
        pdfbytes = print_teachers(tlist, show_workload=True)
        filepath = saveDialog("pdf-Datei (*.pdf)", "teacher_class_subjects")
        if filepath and os.path.isabs(filepath):
            if not filepath.endswith(".pdf"):
                filepath += ".pdf"
            with open(filepath, "wb") as fh:
                fh.write(pdfbytes)
            print("  --->", filepath)

    PROCESS(run_me, "Courses() ... courses.teacher_class_subjects()")

    quit(0)

    print("\n ??????????????????????????????????????????????")

    courses.block_courses()

    print("\n§§§", courses.block_sublessons)
    print(
        "Hu# ->",
        courses.sublessonlengths(">Hu#"),
        sum(courses.sublessonlengths(">Hu#")),
    )

    print("\nBLOCKTAG >Ma#:", read_block_tag(">Ma#"))

    quit(0)

    course_info = get_course_info()
    class2courses = course_info["CLASS2COURSES"]
    for c in sorted(class2courses):
        info = class2courses[c]
        print(f"\nCLASS {c}:")
        print("  ...", info)
