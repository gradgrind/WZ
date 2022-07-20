"""
timetable/activities.py

Last updated:  2022-07-20

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
    Table,
    TableStyle,
)
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib import colors

from core.db_access import db_read_fields
from core.basic_data import (
    get_group_info,
    get_classes,
    get_teachers,
    get_subjects,
    get_rooms,
    check_group,
    read_payment,
    read_block_tag,
    BlockTag,
    PaymentData,
)

DECIMAL_SEP = CONFIG["DECIMAL_SEP"]

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


class ClassBlockInfo(NamedTuple):
    course: CourseData
    lessons: list[int]
    block: BlockTag
    periods: float  # (per week, averaged over the year)
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


class Courses:
    def __init__(self):
        ### First read the COURSES table.
        course2data = {}
        for course, klass, group, sid, tid in db_read_fields(
            "COURSES", ("course", "CLASS", "GRP", "SUBJECT", "TEACHER")
        ):
            # CLASS, SUBJECT and TEACHER are foreign keys and should be
            # automatically bound to appropriate entries in the database.
            # GRP should be checked here ...
            if klass == "--":
                if group:
                    REPORT(
                        "ERROR",
                        T["NULL_CLASS_GROUP"].format(
                            group=group, sid=sid, tid=tid
                        ),
                    )
                    continue
            elif not check_group(klass, group):
                REPORT(
                    "ERROR",
                    T["UNKNOWN_GROUP"].format(
                        klass=klass, group=group, sid=sid, tid=tid
                    ),
                )
                continue

            course2data[course] = CourseData(
                klass=klass, group=group, sid=sid, tid=tid
            )
            if not tid:
                raise Bug(f"Empty teacher field in {course2data[course]}")

        ### Now read the LESSONS table.
        ## Block sublessons are the records for the actual lessons:
        sublesson_lengths = {}  # {block-tag -> [length, ... ]}
        for tag, length in db_read_fields("LESSONS", ("TAG", "LENGTH")):
            try:
                sublesson_lengths[tag].append(length)
            except KeyError:
                sublesson_lengths[tag] = [length]

        ### Now read the BLOCKS table.
        self.paydata = []  # [(CourseData, PaymentData), ... ]
        self.tid2paydata = {}  # {tid -> [(CourseData, PaymentData), ... ]}
        tag2entries = {}  # {block-tag -> [BlockInfo, ... ]}
        self.tag2entries = tag2entries
        tid2tags = {}  # {tid -> {block-tag -> [BlockInfo, ... ]}}
        self.tid2tags = tid2tags
        klass2tags = {}  # {klass -> {block-tag -> [BlockInfo, ... ]}}
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
                        f"(DB-BLOCKS, {coursedata}) TAG ({tag}) -> LENGTHS: {e}",
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
                    __tag2entries = klass2tags[klass]
                except KeyError:
                    klass2tags[klass] = {tag: [entry]}
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
                    self.tid2paydata[tid] = [pd]

                # Check multiple such entries for any one course
                if course in paycourses:
                    REPORT(
                        "WARNING",
                        T["COURSE_MULTIPLE_PAY"].format(course=coursedata),
                    )
                else:
                    paycourses.add(course)

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
        For "continuous" items, a partner-tag is just the block-tag; if
        there is a pay-tag, the partner-tag is "block-tag+sid&pay-tag".
        """
        teachers = get_teachers()
        tlist = []
        for tid in teachers:
            tname = teachers.name(tid)
            ### Divide the data into classes
            ## lesson data
            c2tags = {}
            tag2courses = {}  # {partner-tag -> [course, ... ]}
            for tag, blockinfolist in (self.tid2tags.get(tid) or {}).items():
                continuous = None
                total_length = 0
                tagged = {}
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
                                    course=course, tag=tag
                                ),
                            )
                            continue

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
                                    blockinfo.rooms,
                                )
                                tag2courses[f"{tag}+{stkey}"] = __courses
                            else:
                                if pay != (payinfo.number, payinfo.factor):
                                    REPORT(
                                        "ERROR",
                                        T["PARTNER_PAY_MISMATCH"].format(
                                            course1=clist[0],
                                            course2=course,
                                            tag=tag,
                                        ),
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
                                            tag=tag,
                                        ),
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
                                ),
                            )
                            continue
                        if continuous:
                            if continuous[1] != (
                                payinfo.number,
                                payinfo.factor,
                            ):
                                REPORT(
                                    "ERROR",
                                    T["PARTNER_PAY_MISMATCH"].format(
                                        course1=continuous[0][0],
                                        course2=course,
                                        tag=tag,
                                    ),
                                )
                                continue
                            if continuous[0][0].sid != course.sid:
                                REPORT(
                                    "ERROR",
                                    T["PARTNER_SID_MISMATCH"].format(
                                        course1=continuous[0][0],
                                        course2=course,
                                        tag=tag,
                                    ),
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
                                        tag=tag,
                                    ),
                                )
                                continue
                            continuous[0].append(course)
                        else:
                            continuous = (
                                [course],
                                (payinfo.number, payinfo.factor),
                                blockinfo.rooms,
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
                                course=continuous[0][0], tag=tag
                            ),
                        )
                elif total_length > sum(blockinfolist[0].lessons):
                    REPORT(
                        "WARNING",
                        T["BLOCK_TOO_FULL"].format(teacher=tname, tag=tag),
                    )

            ## Payment-only data
            c2paydata = {}
            for course_pay_data in self.tid2paydata.get(tid) or []:
                klass = course_pay_data[0].klass
                try:
                    c2paydata[klass].append(course_pay_data)
                except KeyError:
                    c2paydata[klass] = [course_pay_data]
            ### Add teacher data to list of all teachers
            tlist.append((tid, tname, c2tags, c2paydata, tag2courses))
        return tlist

    def read_class_blocks(self):
        """Organize the data according to classes.
        This method isolates the actual lessons taught in the various
        classes – as far as the available information allows.
        Payment-only entries are ignored.
        Return an ordered list of the classes, each with its own data.
        The entries in this list are tuples:
            class: str
            name: str
            lesson-data: {tag -> [ClassBlockInfo, ... ]}
            period-counts: {basic-group -> average number of periods per week}
        """
        classes = get_classes()
        clist = []
        tag2classes = {}  # {tag -> {klass}}
        self.tag2classes = tag2classes
        for klass, kname in classes.get_class_list():
            tag2blocks = {}  # {tag -> [ClassBlockInfo, ... ]}
            # Prepare group data – the null class is excluded
            group_info = get_group_info(klass)
            basic_groups = group_info["BASIC"]
            if basic_groups:
                group2basic = group_info["GROUP_MAP"]
            else:
                # If no class divisions, add an entry for the whole class
                basic_groups = {"*"}
                group2basic = {"*": ["*"]}
            # Counters for number of periods per basic-group:
            group_counts = {g: 0.0 for g in basic_groups}
            # Read blocklist for each tag
            try:
                tag2blocklist = self.klass2tags[klass]
            except KeyError:
                clist.append((klass, kname, tag2blocks, group_counts))
                continue
            for tag, blockinfolist in tag2blocklist.items():
                try:
                    tag2classes[tag].add(klass)
                except KeyError:
                    tag2classes[tag] = {klass}
                blocks = []
                tag2blocks[tag] = blocks
                total_length = {g: 0.0 for g in basic_groups}
                lesson_sum = 0
                for blockinfo in blockinfolist:
                    if not lesson_sum:
                        lesson_sum = sum(blockinfo.lessons)
                    course = blockinfo.course
                    if not blockinfo.block.sid:
                        ## A "plain" lesson
                        # No block-sid, nothing parallel
                        if len(blockinfolist) > 1:
                            REPORT(
                                "ERROR",
                                T["BAD_PLAIN_BLOCK"].format(
                                    course=course, tag=tag
                                ),
                            )
                            continue
                    # Only include info if there are real pupils
                    if course.group:
                        # Add number of periods to totals for basic groups
                        if course.group == "*":
                            basics = basic_groups
                        else:
                            basics = group2basic[course.group]
                        payinfo = blockinfo.payment_data
                        if payinfo.number:
                            if payinfo.divisor:
                                n = payinfo.number_val / float(
                                    payinfo.divisor.replace(",", ".")
                                )
                            else:
                                n = payinfo.number_val
                            for group in basics:
                                l = total_length[group]
                                if l < 0.0:
                                    REPORT(
                                        "ERROR",
                                        T["EXCESS_LESSONS"].format(
                                            klass=klass, tag=tag
                                        ),
                                    )
                                else:
                                    total_length[group] = l + n
                        else:
                            for group in basics:
                                l = total_length[group]
                                if l > 0.0:
                                    REPORT(
                                        "ERROR",
                                        T["EXCESS_LESSONS"].format(
                                            klass=klass, tag=tag
                                        ),
                                    )
                                elif l == 0.0:
                                    total_length[group] = -1.0
                            n = lesson_sum
                        # Collect the necessary information about the block
                        blocks.append(
                            ClassBlockInfo(
                                course,
                                blockinfo.lessons,
                                blockinfo.block,
                                n,
                                blockinfo.notes,
                            )
                        )

                # Check that no group has more lessons than is possible ...
                xsgroups = [
                    g for g, n in total_length.items() if n > lesson_sum
                ]
                if xsgroups:
                    REPORT(
                        "WARNING",
                        T["EXCESS_LESSONS"].format(klass=klass, tag=tag),
                    )
                # Update total period counts
                for g in group_counts:
                    gx = total_length[g]
                    if gx > 0.0:
                        group_counts[g] += gx
                    elif gx < 0.0:
                        group_counts[g] += lesson_sum

            ## Payment-only data is not collected for classes

            ### Add class data to list of all classes
            clist.append((klass, kname, tag2blocks, group_counts))
            # print(f"$$$ {klass}:", group_counts)
        return clist


def ljtrim(text, n):
    if len(text) > n:
        m = n - 4
        return f"{text[:m]:<{m}} ..."
    return f"{text:<{n}}"


def class_group(course):
    if course.group:
        return f"{course.klass}.{course.group}"
    else:
        return f"({course.klass})"


def print_teachers(teacher_data, block_tids=None, show_workload=False):
    def partners(tag, course) -> tuple[int, str]:
        try:
            courses = tag2courses[tag]
        except KeyError:
            return ""
        glist = [
            c.klass if c.group == "*" else f"{c.klass}.{c.group}"
            for c in courses
            if c != course
        ]
        return (len(glist), f' //{",".join(glist)}' if glist else "")

    def workload(
        paymentdata: PaymentData,
        lessons: Optional[list[int]] = None,
        ngroups: int = 0,  # number of other groups
    ) -> tuple[float, str]:
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
        val = nd * paymentdata.factor_val
        if ngroups:
            shared = f" /{ngroups+1}"
            val /= float(ngroups + 1)
        else:
            shared = ""
        if show_workload:
            val_str = f"{val:.3f}".replace(".", DECIMAL_SEP)
            text = f"{n} × {paymentdata.factor or '--'}{shared} = {val_str}"
        else:
            text = ""
        return (val, text)

    blocked_tids = set() if block_tids is None else set(block_tids)
    classes = get_classes().get_class_list(skip_null=False)
    teacherlists = []
    for tid, tname, c2tags, c2paydata, tag2courses in teacher_data:
        if tid in blocked_tids:
            REPORT("INFO", T["TEACHER_SUPPRESSED"].format(tname=tname))
            continue
        if not (c2tags or c2paydata):
            REPORT("INFO", T["TEACHER_NO_ACTIVITIES"].format(tname=tname))
            continue
        # print("\n $$$$$$", tname)
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
                    # print("???TAG", tag)
                    block = blockinfolist[0].block
                    if block.sid:
                        bname = block.subject
                        for blockinfo in blockinfolist:
                            course = blockinfo.course
                            sname = get_subjects().map(course.sid)
                            rooms = "|".join(blockinfo.rooms)
                            lessons = ",".join(map(str, blockinfo.lessons))
                            payment = blockinfo.payment_data
                            if payment.number:
                                # With number of units taught
                                if payment.tag:
                                    n, plist = partners(
                                        f"{tag}+{course.sid}&{payment.tag}",
                                        course,
                                    )
                                else:
                                    n, plist = 0, ""
                                pay, paytext = workload(
                                    payment, blockinfo.lessons, n
                                )
                                pay_total += pay
                                if payment.number_val >= sum(blockinfo.lessons):
                                    if course.sid == block.sid:
                                        class_list.append(
                                            (
                                                sname,
                                                class_group(course),
                                                sname + plist,
                                                rooms,
                                                lessons,
                                                paytext,
                                            )
                                        )
                                        continue
                                    extent = T["continuous"]
                                else:
                                    extent = payment.number
                                line = (
                                    sname,
                                    f" – {class_group(course)}",
                                    sname + plist,
                                    rooms,
                                    f"[{extent}]",
                                    paytext,
                                )
                                try:
                                    class_blocks[bname][1].append(line)
                                except KeyError:
                                    class_blocks[bname] = (lessons, [line])
                                # print(f"%%% ({bname} {lessons}) {line}")

                            else:
                                # Continuous teaching
                                n, plist = partners(tag, course)
                                pay, paytext = workload(
                                    payment, blockinfo.lessons, n
                                )
                                pay_total += pay
                                if course.sid == block.sid:
                                    class_list.append(
                                        (
                                            sname,
                                            class_group(course),
                                            sname + plist,
                                            rooms,
                                            lessons,
                                            paytext,
                                        )
                                    )
                                    # print("§§§", class_list[-1])

                                else:
                                    line = (
                                        sname,
                                        f" – {class_group(course)}",
                                        sname,
                                        rooms,
                                        f'[{T["continuous"]}]',
                                        paytext,
                                    )
                                    try:
                                        class_blocks[bname][1].append(line)
                                    except KeyError:
                                        class_blocks[bname] = (lessons, [line])
                                    # print(f"&&& ({bname} {lessons}) {line}")

                    else:
                        ## Simple, plain lesson block
                        blockinfo = blockinfolist[0]
                        course = blockinfo.course
                        sname = get_subjects().map(course.sid)
                        rooms = "|".join(blockinfo.rooms)
                        lessons = ",".join(map(str, blockinfo.lessons))
                        pay, paytext = workload(
                            blockinfo.payment_data, blockinfo.lessons
                        )
                        pay_total += pay
                        class_list.append(
                            (
                                sname,
                                class_group(course),
                                sname,
                                rooms,
                                lessons,
                                paytext,
                            )
                        )
                        # print("§§§", class_list[-1])

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
                        (
                            sname,
                            f"({class_group(course)})",
                            sname,
                            "",
                            "",
                            paytext,
                        )
                    )

            # Collate the various activities
            all_items = []
            for bname, data in class_blocks.items():
                all_items.append((f"[[{bname}]]", "", "", data[0], ""))
                for line in sorted(data[1]):
                    all_items.append(line[1:])
            # if all_items:
            #     all_items.append(None)
            all_items += [item[1:] for item in sorted(class_list)]
            if show_workload:
                # if all_items:
                #     all_items.append(None)
                all_items += [item[1:] for item in sorted(class_payonly)]
            if all_items:
                classlists.append((klass, all_items))

        teacherline = f"{tname} ({tid})"
        xclass = ("", [])
        classlists.append(xclass)
        if show_workload:
            pay_str = f"{pay_total:.2f}".replace(".", DECIMAL_SEP)
            xclass[1].append(("-----", "", "", "", "", pay_str))
            # teacherline = f"{teacherline:<30} – {T['WORKLOAD']}: {pay_str}"

        # print("\n  +++++++++++++++++++++", teacherline)
        # print(classlists)
        teacherlists.append((teacherline, classlists))

    pdf = PdfCreator()
    headers = [
        T[h] for h in ("H_group", "H_subject", "H_room", "H_lessons_blocks")
    ]
    if show_workload:
        headers.append(T["H_workload"])
        colwidths = (20, 50, 30, 30, 40)
    else:
        colwidths = (20, 60, 40, 40)
    return pdf.build_pdf(
        teacherlists,
        title=T["teachers-subjects"],
        author=CONFIG["SCHOOL_NAME"],
        headers=headers,
        colwidths=colwidths,
        #        do_landscape=True
    )


def print_classes(class_data, tag2classes):
    classlists = []
    for klass, kname, tag2blocks, counts in class_data:
        if not tag2blocks:
            REPORT("INFO", T["CLASS_NO_ACTIVITIES"].format(klass=klass))
            continue
        class_list, class_blocks = [], {}
        for tag in tag2blocks:
            blockinfolist = tag2blocks[tag]
            # print("???TAG", tag)
            try:
                __blockinfo = blockinfolist[0]
            except IndexError:
                REPORT(
                    "ERROR", T["TAG_NO_ACTIVITIES"].format(klass=klass, tag=tag)
                )
                continue
            block = __blockinfo.block
            lessons = ",".join(map(str, __blockinfo.lessons))
            if block.sid:
                ## All block types with block name
                blocklist = []
                # Include parallel classes
                try:
                    tag_classes = tag2classes[tag] - {klass}
                except KeyError:
                    raise Bug(f"Tag {tag} not in 'tag2classes'")
                if tag_classes:
                    parallel = f' //{",".join(tag_classes)}'
                else:
                    parallel = ""
                # Add block entry
                class_blocks[block] = (lessons, blocklist, parallel)
                # Add members
                for blockinfo in blockinfolist:
                    course = blockinfo.course
                    sname = get_subjects().map(course.sid)
                    group_periods = f"{blockinfo.periods:.2f}".replace(
                        ".", DECIMAL_SEP
                    )
                    blocklist.append(
                        (
                            f" – {sname}",
                            course.group,
                            course.tid,
                            "",
                            group_periods,
                        )
                    )
                blocklist.sort()

            else:
                ## Simple, plain lesson block
                course = __blockinfo.course
                sname = get_subjects().map(course.sid)
                group_periods = f"{__blockinfo.periods:.2f}".replace(
                    ".", DECIMAL_SEP
                )
                class_list.append(
                    (sname, course.group, course.tid, lessons, group_periods)
                )

        # Collate the various activities
        all_items = []
        for block in sorted(class_blocks):
            data = class_blocks[block]
            sbj, tag = block.subject, block.tag
            if tag:
                blockname = f"[[{sbj} #{tag}]]"
            else:
                blockname = f"[[{sbj}]]"
            all_items.append((blockname + data[2], "", "", data[0], ""))
            for line in data[1]:
                all_items.append(line)
        if all_items:
            all_items.append(None)
        all_items += sorted(class_list)

        classline = f"{kname} ({klass})"
        line = []
        countlines = [line]
        for g in sorted(counts):
            n = counts[g]
            if len(line) >= 6:
                line = []
                countlines.append(line)
            item = f"   {g}: " + f"{n:.1f}".replace(".", DECIMAL_SEP)
            line.append(f"{item:<16}")
        while len(line) < 6:
            line.append(" " * 16)
        countlines.append([""])
        classlists.append((classline, [("#", countlines), ("", all_items)]))

    pdf = PdfCreator()
    headers = [
        T[h]
        for h in ("H_subject", "H_group", "H_teacher", "H_lessons", "H_total")
    ]
    colwidths = (75, 20, 20, 30, 25)
    return pdf.build_pdf(
        classlists,
        title=T["classes-subjects"],
        author=CONFIG["SCHOOL_NAME"],
        headers=headers,
        colwidths=colwidths,
        #        do_landscape=True
    )


BASE_MARGIN = 20 * mm


class MyDocTemplate(SimpleDocTemplate):
    """This is adapted to emit an "outline" for the teacher pages."""

    def __init__(self, *args, **kargs):
        self.key = 0
        super().__init__(*args, **kargs)

    def handle_flowable(self, flowables):
        if flowables:
            flowable = flowables[0]
            try:
                flowable.toc(self.canv)
            except AttributeError:
                pass
        super().handle_flowable(flowables)


tablestyle0 = [
    ("FONT", (0, 0), (-1, -1), "Helvetica"),
    ("FONTSIZE", (0, 0), (-1, -1), 12),
    ("LINEABOVE", (0, -1), (-1, -1), 1, colors.lightgrey),
]

tablestyle = [
    #         ('ALIGN', (0, 1), (-1, -1), 'RIGHT'),
    ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
    ("LINEBELOW", (0, -1), (-1, -1), 1, colors.black),
    ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
    #         ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
    ("FONT", (0, 1), (-1, -1), "Helvetica"),
    #         ('BACKGROUND', (1, 1), (-2, -2), colors.white),
    ("TEXTCOLOR", (0, 0), (1, -1), colors.black),
    ("FONTSIZE", (0, 0), (-1, -1), 11),
]


class PdfCreator:
    def add_page_number(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Times-Roman", 12)
        page_number_text = "%d" % (doc.page)
        canvas.drawCentredString(18 * mm, 18 * mm, page_number_text)
        canvas.restoreState()

    def build_pdf(
        self,
        pagelist,
        title,
        author,
        headers,
        colwidths=None,
        do_landscape=False,
    ):
        all_refs = set()

        class PageHeader(Paragraph):
            # class PageHeader(Preformatted):
            def __init__(self, text, ref):
                if ref in all_refs:
                    REPORT("ERROR", T["Repeated_page_title"].format(ref=ref))
                    self.ref = None
                else:
                    self.ref = ref
                    all_refs.add(ref)
                super().__init__(text, heading_style)

            def toc(self, canvas):
                if self.ref:
                    canvas.bookmarkPage(self.ref)
                    canvas.addOutlineEntry(self.ref, self.ref, 0, 0)

        pdf_buffer = BytesIO()
        my_doc = MyDocTemplate(
            pdf_buffer,
            title=title,
            author=author,
            pagesize=landscape(A4) if do_landscape else A4,
            topMargin=BASE_MARGIN,
            leftMargin=BASE_MARGIN,
            rightMargin=BASE_MARGIN,
            bottomMargin=BASE_MARGIN,
        )
        sample_style_sheet = getSampleStyleSheet()
        body_style = sample_style_sheet["BodyText"]
        # body_style = sample_style_sheet["Code"]
        body_style.fontSize = 11
        # body_style.leading = 14
        # body_style.leftIndent = 0

        # body_style_2 = copy.deepcopy(body_style)
        # body_style.spaceBefore = 10
        # body_style_2.alignment = TA_RIGHT

        heading_style = sample_style_sheet["Heading1"]
        # print("????????????", heading_style.fontName)
        # heading_style = copy.deepcopy(body_style)
        heading_style.fontName = "Helvetica-Bold"
        heading_style.fontSize = 14
        heading_style.spaceAfter = 24

        # sect_style = sample_style_sheet["Heading2"]
        # sect_style.fontSize = 13
        # sect_style.spaceBefore = 20
        # print("\n STYLES:", sample_style_sheet.list())

        flowables = []
        for pagehead, plist in pagelist:
            # print("§§§", repr(pagehead))
            tstyle = tablestyle.copy()
            # h = Paragraph(pagehead, heading_style)
            h = PageHeader(pagehead, pagehead)  # .split("(", 1)[0].rstrip())
            flowables.append(h)
            lines = [headers]
            nh = len(headers)
            for secthead, slist in plist:
                if secthead == "#":
                    table = Table(slist)
                    table_style = TableStyle(tablestyle0)
                    table.setStyle(table_style)
                    flowables.append(table)
                    continue
                lines.append("")
                for sline in slist:
                    r = len(lines)
                    if sline:
                        if sline[0].startswith("[["):
                            tstyle.append(("SPAN", (0, r), (2, r)))
                        if sline[0] == "-----":
                            tstyle.append(
                                ("LINEABOVE", (0, r), (-1, r), 1, colors.black),
                            )
                            sline = sline[1:]
                        lines.append(sline[:nh])
                    else:
                        lines.append("")
                lines.append("")

            kargs = {"repeatRows": 1}
            if colwidths:
                kargs["colWidths"] = [w * mm for w in colwidths]
            table = Table(lines, **kargs)
            table_style = TableStyle(tstyle)
            table.setStyle(table_style)
            flowables.append(table)

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
        # pdfbytes = print_teachers(tlist)
        filepath = saveDialog("pdf-Datei (*.pdf)", "teachers_subjects")
        if filepath and os.path.isabs(filepath):
            if not filepath.endswith(".pdf"):
                filepath += ".pdf"
            with open(filepath, "wb") as fh:
                fh.write(pdfbytes)
            print("  --->", filepath)

        clist = courses.read_class_blocks()
        pdfbytes = print_classes(clist, courses.tag2classes)
        filepath = saveDialog("pdf-Datei (*.pdf)", "class_subjects")
        if filepath and os.path.isabs(filepath):
            if not filepath.endswith(".pdf"):
                filepath += ".pdf"
            with open(filepath, "wb") as fh:
                fh.write(pdfbytes)
            print("  --->", filepath)

    PROCESS(run_me, "Courses() ... print teacher and class workload")
