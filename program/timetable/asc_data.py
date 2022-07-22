"""
timetable/asc_data.py - last updated 2022-07-21

Prepare aSc-timetables input from the various sources ...

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
__TESTX = False
__TESTY = False


# IMPORTANT: Before importing the data generated here, some setting up of
# the school data is required, especially the setting of the total number
# of lesson slots per day, which seems to be preset to 7 in the program
# and there is no obvious way of changing this via an import.

### Messages

_NO_JOINT_ROOMS = (
    "Fach {sid} ({tag}), Klassen {classes}:" " Keine verfügbare Räume (zu '?')"
)
_LESSON_NO_GROUP = "Klasse {klass}, Fach {sid}: „Unterricht“ ohne Gruppe"
_LESSON_NO_TEACHER = "Klasse {klass}, Fach {sid}: „Unterricht“ ohne Lehrer"

########################################################################

if __name__ == "__main__":
    # Enable package import if running as module
    import sys, os

    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    #    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))


# IMPORTANT: Note that some uses of Python dicts here may assume ordered
# entries. If the implementation is altered, this should be taken into
# account.

T = TRANSLATIONS("timetable.asc_data")

### +++++

import re, json

import xmltodict

from core.db_access import db_read_fields
from core.basic_data import (
    get_days,
    get_periods,
    get_classes,
    get_teachers,
    get_subjects,
    get_rooms,
    timeslot2index
)

from activities import lesson_rooms, read_block_tag

#TODO: deprecated?
from timetable.courses import (
    get_timetable_data,
    blocktag2blocksid,
)


def idsub(tag):
    """In aSc, "id" fields may only contain ASCII alphanumeric characters,
    '-' and '_'. Substitute anything else by '_'.
    """
    return re.sub("[^-_A-Za-z0-9]", "_", tag)


WHOLE_CLASS = T["WHOLE_CLASS"]

TIMETABLE_TEACHERS = set()
TIMETABLE_SUBJECTS = set()

### -----


def get_days_aSc() -> list[dict]:
    """Return an ordered list of aSc elements for the days."""
    days = get_days()
    nd = len(days)
    i = int(10 ** nd)
    dlist = []
    n = 0
    for tag, name in days:
        n += 1
        i //= 10
        dlist.append(
            {
                "@id": str(n),
                "@name": name,
                "@short": tag,
                "@days": f"{i:0{nd}d}",
            }
        )
    return dlist


def get_periods_aSc() -> list[dict]:
    """Return an ordered list of aSc elements for the periods."""
    vlist = db_read_fields(
        "TT_PERIODS",
        ("N", "TAG", "NAME", "START_TIME", "END_TIME"),
        sort_field="N",
    )
    plist = [
        {
            "@short": tag,
            "@name": name,
            "@starttime": stime,
            "@endtime": etime,
            "@period": str(n),
        }
        for n, tag, name, stime, etime in vlist
    ]
    return plist


def get_rooms_aSc() -> list[dict]:
    """Return an ordered list of aSc elements for the rooms."""
    rooms = [
        {"@id": idsub(rid), "@short": rid, "@name": name}
        for rid, name in get_rooms()
    ]
    rooms.append({"@id": "rXXX", "@short": "rXXX", "@name": T["ROOM_TODO"]})
    return rooms


def get_subjects_aSc() -> list[dict]:
    """Return an ordered list of aSc elements for the subjects."""
    return [
        {"@id": idsub(sid), "@short": sid, "@name": name}
        for sid, name in get_subjects()
        if sid in TIMETABLE_SUBJECTS
    ]


def get_classes_aSc():
    """Return an ordered list of aSc elements for the classes."""
    __classes = get_classes()
    return [
        {
            "@id": idsub(klass),
            "@short": klass,
            "@name": name,
            "@classroomids": __classes.get_classroom(klass),
            "@timeoff": timeoff_aSc(__classes[klass].tt_data)
        }
        for klass, name in __classes.get_class_list()
    ]


def get_groups_aSc():
    """Return an ordered list of aSc elements for the groups within the classes."""
    group_list = []
    classes = get_classes()
    for klass, _ in classes.get_class_list():
        g = WHOLE_CLASS
        group_list.append(
            {
                "@id": idsub(f"{klass}-{g}"),
                "@classid": klass,
                "@name": g,
                "@entireclass": "1",
                "@divisiontag": "0",
            }
        )
        # Sort out the divisions ...
        divisions = classes.group_info(klass)["INDEPENDENT_DIVISIONS"]
        dix = 0
        for div in divisions:
            dix += 1
            for grp in div:
                group_list.append(
                    {
                        "@id": idsub(f"{klass}-{grp}"),
                        "@classid": klass,
                        "@name": grp,
                        "@entireclass": "0",
                        "@divisiontag": str(dix),
                    }
                )
    return group_list


def timeoff_aSc(tt_data: dict) -> str:
    """Return a "timeoff" entry for the given <tt_data> field."""
    try:
        day_periods = tt_data["AVAILABLE"].split("_")
    except KeyError:
        day_periods = ""
    weektags = []
    nperiods = len(get_periods())
    for d in range(len(get_days())):
        default = "1"
        try:
            ddata = day_periods[d]
        except IndexError:
            ddata = ""
        daytags = []
        for p in range(nperiods):
            try:
                px = "0" if ddata[p] == "-" else "1"
                default = px
            except IndexError:
                px = default
            daytags.append(px)
        weektags.append("." + "".join(daytags))
    return ",".join(weektags)


def get_teachers_aSc():
    """Return an ordered list of aSc elements for the teachers."""
    return [
        {
            "@id": idsub(tdata.tid),
            "@short": tdata.tid,
            "@name": tdata.signed,
#TODO: "@gender": "M" or "F"?
            "@firstname": tdata.firstname,
            "@lastname": tdata.lastname,
            "@timeoff": timeoff_aSc(tdata.tt_data)
        }
        for tdata in get_teachers().values()
        if tdata.tid in TIMETABLE_TEACHERS
    ]


def aSc_lesson(classes, sid, groups, tids, duration, rooms):
    """Given the data for an aSc lesson item, return the school class
    ("XX" if there are multiple classes) and the lesson item prototype –
    the id is added later.
    """
    if tids:
        tids.discard("--")
        TIMETABLE_TEACHERS.update(tids)
    classes.discard("--")
    if groups and classes:
        __classes = sorted(classes)
    else:
        __classes = []
    if sid:
        if sid == "--":
            raise Bug("sid = '--'")
        TIMETABLE_SUBJECTS.add(sid)

    # <id> is initially empty, it is added later
    return (
        "XX" if len(__classes) != 1 else idsub(__classes[0]),  # class
        {
            "@id": None,
            "@classids": ",".join(__classes),
            "@subjectid": sid,
            "@groupids": ",".join(sorted(groups)),
            "@teacherids": ",".join(sorted(tids)),
            "@durationperiods": duration,
            # Note that in aSc the number of periods means the
            # number of _single_ periods, so it is the same as
            # the previous field – lessons are added singly, not
            # as multiples.
            "@periodsperweek": duration,
            "@classroomids": ",".join(rooms),
        },
    )


def aSc_block_lesson(lesson, length):
    """Build an aSc lesson record for a block sublesson based on an
    earlier record (cached).
    """
    l2 = lesson.copy()
    l2["@durationperiods"] = length
    l2["@periodsperweek"] = length
    return l2


def get_lessons():
    """Build list of lessons for aSc-timetables."""

    def new_lesson(__klass, __sid, __lesson, __place):
        """Add lesson item to <presorted> mapping."""
        try:
            classmap = presorted[__klass]
        except KeyError:
            classmap = {}
            presorted[__klass] = classmap
        try:
            classmap[__sid].append(__lesson)
        except KeyError:
            classmap[__sid] = [__lesson]
        # If time set, add lessondata.time as card.
        # TODO: Would it make sense to include lessondata.id?
        # Rooms are supplied as __place
        if lessondata.time != "@?":
            if lessondata.time.startswith("@"):
                # Get 0-based indexes for day and period
                try:
                    d, p = timeslot2index(lessondata.time[1:])
                except TimeSlotError:
                    pass
                else:
                    place = __place or __lesson["@classroomids"]
                    # print("$$$ CARDLIST +", __lesson, "\n ...", d+1, p+1, place)
                    cardlist.append(
                        (
                            __lesson,
                            d + 1,
                            p + 1,
                            place,
                            "0" if lessondata.time[1] == "?" else "1",
                        )
                    )
                    return
            SHOW_ERROR(
                T["BAD_TIME"].format(time=lessondata.time, id=lessondata.id)
            )

    def parse_rooms(lessondata):
        rooms = lesson_rooms(lessondata)
        if rooms and rooms[-1] == "+":
            rooms[-1] = "rXXX"
        return rooms

    def block_lesson(ldata):
#TODO: use read_block_tag instead
        blocksid = blocktag2blocksid(ldata.place)
        try:
            klass, blesson, place = block_cache[ldata.place]
        except KeyError:
            pass
        else:
            # Use the cached lesson item as a basis for the new one
            lesson = aSc_block_lesson(blesson, ldata.length)
            new_lesson(klass, blocksid, lesson, place)
            return

        # Accumulate the tids, groups and rooms ...
        btids = set()
        bgroups = set()
        broomlist = set()  # Collect distinct room lists (text form)
        brooms = set()  # Collect distinct rooms
        bplaces = set()  # Collect used rooms
        bclasses = set()
        for id in block_members[ldata.place]:
            bldata = lessons[id]
            bcdata = bldata.course
            bclasses.add(bcdata.klass)
            # TODO: Null teacher possible?
            btids.add(bcdata.tid)
            bgroups.update(full_group(bcdata.klass, bcdata.group))
            # As aSc doesn't support XML input of multiple rooms,
            # the multiple rooms are collected independently – for
            # manual intervention!
            # For aSc all rooms and teachers can be lumped together
            # as there are no features for handling the involved
            # classes separately.
            # TODO: It might in some cases be better to suppress the teachers and rooms?
            # These could be taken out of circulation by some other means?
            if bldata.room:
                # Check rooms, replace "$"
                ll = lesson_rooms(bldata)
                llt = "/".join(ll)
                if llt not in broomlist:
                    brooms.update(ll)
                    broomlist.add(llt)
            if bldata.place:
                __place = check_place(bldata)
                if _place:
                    bplaces.add(__place)

        # The lesson data is cached for repeated instances of the
        # same block tag (change length).
        if "+" in brooms:
            brooms.discard("+")
            brooms.add("rXXX")
        klass, lesson = aSc_lesson(
            bclasses, blocksid, bgroups, btids, ldata.length, sorted(brooms)
        )
        place = ",".join(sorted(bplaces))
        block_cache[ldata.place] = (klass, lesson, place)
        new_lesson(klass, blocksid, lesson, place)

    # TODO: aSc can't cope with multiple rooms, so it might be best to make a
    # list and emit this for the user ...

    TIMETABLE_TEACHERS.clear()
    TIMETABLE_SUBJECTS.clear()
    courses = Courses()

#?
    tt_data = get_timetable_data()
    # Fields:
    #   LESSONLIST
    #   CLASS2LESSONS
    #   BLOCK_MEMBERS
    #   BLOCK_SUBLESSONS
    #   PARTNERS
    #   PARTNERS_TIME
    #   TIMETABLE_CELLS

    presorted = {}
    block_cache = {}  # cache for block lessons: {tag -> lesson dict}
    lessons = tt_data["LESSONLIST"]  # id-indexed LessonData items
    block_members = tt_data["BLOCK_MEMBERS"]
    cardlist = []  # for collecting placements
    for tt_cell in tt_data["TIMETABLE_CELLS"]:
        lessondata = lessons[tt_cell]
        coursedata = lessondata.course
        if lessondata.place.startswith(">"):
            ## block sublesson with direct time
            block_lesson(lessondata)

        elif lessondata.place.startswith("="):
            ## partner time
            # As far as I can tell, it is not possible in aSc to specify
            # that a group of lessons must start at the same time.
            # Thus I just add normal lessons, setting the time if it is
            # specified, and emit a list of parallel lessons for the
            # user.
            for id in tt_data["PARTNERS"][lessondata.place]:
                # print("***********", lessons[id])
                plesson = lessons[id]
                if plesson.place.startswith(">"):
                    ## block sublesson with indirect time
                    # TODO: Not supported in aSc generator?
                    SHOW_WARNING(f"Partner tag in block sublesson: {plesson}")
                    # ?
                    block_lesson(plesson)

                else:
                    ## plain lesson with indirect time
                    pcdata = plesson.course
                    klass, lesson = aSc_lesson(
                        {pcdata.klass},
                        pcdata.sid,
                        full_group(pcdata.klass, pcdata.group),
                        {pcdata.tid},
                        plesson.length,
                        parse_rooms(plesson),  # ordered, so a set can't be used
                    )
                    new_lesson(klass, pcdata.sid, lesson,
                        check_place(plesson)
                    )

        else:
            ## plain lesson with direct time
            klass, lesson = aSc_lesson(
                {coursedata.klass},
                coursedata.sid,
                full_group(coursedata.klass, coursedata.group),
                {coursedata.tid},
                lessondata.length,
                parse_rooms(lessondata),  # ordered, so a set can't be used
            )
            new_lesson(klass, coursedata.sid, lesson,
                check_place(lessondata)
            )

    lesson_list = []  # final lesson list
    class_counter = {}  # for indexing lessons on a class-by-class basis
    for klass in sorted(presorted):
        kpmap = presorted[klass]
        for sid in sorted(kpmap):
            for lesson in kpmap[sid]:
                # Add id and move lesson to <lesson_list>
                i = class_counter.get(klass) or 0
                i += 1
                class_counter[klass] = i
                # It is not likely that there will be >99 lessons for a class:
                lesson["@id"] = f"{klass}_{i:02}"
                lesson_list.append(lesson)

    cards = []
    for l, d, p, r, locked in sorted(cardlist, key=lambda x: x[0]["@id"]):
        # print("CARD:", l, "\n  ...", d, p, r, locked)
        cards.append(
            {
                "@lessonid": l["@id"],
                "@period": str(p),
                "@day": str(d),
                "@classroomids": r,
                "@locked": locked,
            }
        )
    return lesson_list, cards


def full_group(klass, group):
    """Return the group as a "full group" – also containing the class.
    The result is a set.
    """
    if klass and klass != "--":
        if group:
            if group == "*":
                return {f"{klass}-{WHOLE_CLASS}"}
            # Some groups are compounds – I need to get the components!
            groups = get_classes().group_info(klass)["GROUP_MAP"][group]
            return {f"{klass}-{g}" for g in groups}
    return set()


def check_place(lessondata):
    __place = lessondata.place
    if __place:
        try:
            get_rooms().index(__place)
            return __place
        except KeyError:
            SHOW_ERROR(
                T["INVALID_PLACE"].format(
                    rid=__place,
                    klass=lessondata.course.klass,
                    group=lessondata.course.group,
                    sid=lessondata.course.sid,
                    tid=lessondata.course.tid,
                )
            )
    return ""


########################################################################


def build_dict(
    ROOMS, PERIODS, TEACHERS, SUBJECTS, CLASSES, GROUPS, LESSONS, CARDS
):
    BASE = {
        "timetable": {
            "@importtype": "database",
            "@options": "idprefix:WZ,daynumbering1",
            # 'daysdefs' seems unnecessary, there are sensible defaults
            #            'daysdefs':
            #                {   '@options': 'canadd,canremove,canupdate,silent',
            #                    '@columns': 'id,name,short,days',
            #                    'daysdef':
            #                        [   {'@id': 'any', '@name': 'beliebigen Tag', '@short': 'X', '@days': '10000,01000,00100,00010,00001'},
            #                            {'@id': 'every', '@name': 'jeden Tag', '@short': 'A', '@days': '11111'},
            #                            {'@id': '1', '@name': 'Montag', '@short': 'Mo', '@days': '10000'},
            #                            {'@id': '2', '@name': 'Dienstag', '@short': 'Di', '@days': '01000'},
            #                            {'@id': '3', '@name': 'Mittwoch', '@short': 'Mi', '@days': '00100'},
            #                            {'@id': '4', '@name': 'Donnerstag', '@short': 'Do', '@days': '00010'},
            #                            {'@id': '5', '@name': 'Freitag', '@short': 'Fr', '@days': '00001'},
            #                        ]
            #                },
            "periods": {
                "@options": "canadd,canremove,canupdate,silent",
                "@columns": "period,name,short,starttime,endtime",
                "period": PERIODS,
            },
            "teachers": {
                "@options": "canadd,canremove,canupdate,silent",
                "@columns": "id,short,name,firstname,lastname,timeoff",
                "teacher": TEACHERS,
            },
            "classes": {
                "@options": "canadd,canremove,canupdate,silent",
                "@columns": "id,short,name,classroomids,timeoff",
                "class": CLASSES,
            },
            "groups": {
                "@options": "canadd,canremove,canupdate,silent",
                "@columns": "id,classid,name,entireclass,divisiontag",
                "group": GROUPS,
            },
            "subjects": {
                "@options": "canadd,canremove,canupdate,silent",
                "@columns": "id,name,short",
                "subject": SUBJECTS,
            },
            "classrooms": {
                "@options": "canadd,canremove,canupdate,silent",
                "@columns": "id,name,short",
                "classroom": ROOMS,
            },
            "lessons":
            # Use durationperiods instead of periodspercard (deprecated)
            # As far as I can see, the only way in aSc to make lessons
            # parallel is to combine them to a single subject.
            {
                "@options": "canadd,canremove,canupdate,silent",
                "@columns": "id,classids,groupids,subjectid,durationperiods,periodsperweek,teacherids,classroomids",
                "lesson": LESSONS,
            },
            # Initial (fixed?) placements
            "cards": {
                "@options": "canadd,canremove,canupdate,silent",
                "@columns": "lessonid,period,day,classroomids,locked",
                "card": CARDS,
            },
        }
    }
    return BASE


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from core.db_access import open_database
    open_database()
    from qtpy.QtWidgets import QApplication, QFileDialog

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

    days = get_days_aSc()
    if __TEST:
        print("\n*** DAYS ***")
        for d in days:
            print(f"   {d}")
        print("\n  ==================================================")

    periods = get_periods_aSc()
    if __TEST:
        print("\n*** PERIODS ***")
        for p in periods:
            print(f"   {p}")
        print("\n  ==================================================")

    allrooms = get_rooms_aSc()
    if __TEST:
        print("\n*** ROOMS ***")
        for rdata in allrooms:
            print("   ", rdata)
        print("\n  ==================================================")

    classes = get_classes_aSc()
    if __TEST:
        print("\n*** CLASSES ***")
        for cdata in classes:
            print("   ", cdata)

    groups = get_groups_aSc()
    if __TEST:
        print("\n*** CLASS-GROUPS ***")
        for gdata in groups:
            print("   ", gdata)

    lessons, cards = get_lessons()

    allsubjects = get_subjects_aSc() # must be after call to <get_lessons>
    if __TEST:
        print("\n*** SUBJECTS ***")
        for sdata in allsubjects:
            print("   ", sdata)

    teachers = get_teachers_aSc() # must be after call to <get_lessons>
    if __TEST:
        print("\n*** TEACHERS ***")
        for tdata in teachers:
            print("   ", tdata)

#    quit(0)

    if __TESTX:
        print("\n*** LESSON ITEMS ***")
        for l in lessons:
            print("  +++", l)

    if __TESTY:
        print("\n*** CARDS ***")
        for c in cards:
            print("  !!!", c)

    quit(0)

    outdir = DATAPATH("TIMETABLE/out")
    os.makedirs(outdir, exist_ok=True)

    xml_aSc = xmltodict.unparse(
        build_dict(
            ROOMS=allrooms,
            PERIODS=periods,
            TEACHERS=teachers,
            SUBJECTS=allsubjects,
            CLASSES=classes,
            GROUPS=groups,
            LESSONS=lessons,
            CARDS=cards,
            #            CARDS = [],
        ),
        pretty=True,
    )

    outpath = os.path.join(outdir, "tt_out.xml")
    with open(outpath, "w", encoding="utf-8") as fh:
        fh.write(xml_aSc.replace("\t", "   "))
    print("\nTIMETABLE XML ->", outpath)
