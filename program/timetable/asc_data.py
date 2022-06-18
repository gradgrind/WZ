"""
timetable/asc_data.py - last updated 2022-06-18

*** Largely old code from February ... adapting to use the sqlite db data.

Prepare aSc-timetables input from the various sources ...

==============================
Copyright 2021 Michael Towers

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

# IMPORTANT: Before importing the data generated here, some setting up of
# the school data is required, especially the setting of the total number
# of lesson slots per day, which seems to be preset to 7 in the program
# and there is no obvious way of changing this via an import.

### Messages

_DUPLICATE_TAG = (
    "Fachtabelle, im Feld {key}: Werte „{source1}“ und"
    " „{source2}“ sind intern nicht unterscheidbar."
)
_NO_JOINT_ROOMS = (
    "Fach {sid} ({tag}), Klassen {classes}:" " Keine verfügbare Räume (zu '?')"
)
_LESSON_NO_GROUP = "Klasse {klass}, Fach {sid}: „Unterricht“ ohne Gruppe"
_LESSON_NO_TEACHER = "Klasse {klass}, Fach {sid}: „Unterricht“ ohne Lehrer"

########################################################################

import sys, os, re, json

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
# account. One place is the definition of pre-placed lessons
# for a subject. If there is more than one entry for this subject and
# varying durations, the placement could be affected.

T = TRANSLATIONS("timetable.asc_data")

### +++++

import xmltodict

from core.db_management import open_database, db_read_fields, db_key_value_list
from core.classes import Classes, build_group_data
from core.teachers import Teachers


#TODO
#from timetable.basic_data import (
#    Classes,
#    Days,
#    Periods,
#    Placements,
#    Rooms,
#    TT_Subjects,
#    TT_Teachers,
#    TT_Error,
#    class_group_split,
#)

def idsub(tag):
    """In aSc, "id" fields may only contain ASCII alphanumeric characters,
    '-' and '_'. Substitute anything else by '_'.
    """
    return re.sub("[^-_A-Za-z0-9]", "_", tag)

SHARED_DATA = {}

### -----


def get_days_aSc() -> list[dict]:
    """Return an ordered list of aSc elements for the days.
    This data is cached, so subsequent calls get the same data.
    """
    try:
        return SHARED_DATA["DAYS"]
    except KeyError:
        pass
    vlist = db_read_fields(
        "TT_DAYS",
        ("N", "TAG", "NAME"),
        sort_field="N"
    )
    nd = len(vlist)
    i = int(10**nd)
    dlist = []
    for n, tag, name in vlist:
        i //= 10
        dlist.append(
            {
                "@id": str(n),
                "@name": name,
                "@short": tag,
                "@days": f"{i:0{nd}d}"
            }
        )
    SHARED_DATA["DAYS"] = dlist
    return dlist


def get_periods_aSc() -> list[dict]:
    """Return an ordered list of aSc elements for the periods.
    This data is cached, so subsequent calls get the same data.
    """
    try:
        return SHARED_DATA["PERIODS"]
    except KeyError:
        pass
    vlist = db_read_fields(
        "TT_PERIODS",
        ("N", "TAG", "NAME", "START_TIME", "END_TIME"),
        sort_field="N"
    )
    plist = [
        {
            "@short": tag,
            "@name": name,
            "@starttime": stime,
            "@endtime": etime,
            "@period": str(n)
        }
        for n, tag, name, stime, etime in vlist
    ]
    SHARED_DATA["PERIODS"] = plist
    return plist


def get_classes() -> Classes:
    """Return the data for all classes as a <Classes> instance (dict).
    This data is cached, so subsequent calls get the same instance.
    """
    try:
        return SHARED_DATA["CLASSES"]
    except KeyError:
        pass
    classes = Classes()
    SHARED_DATA["CLASSES"] = classes
    return classes


def get_teachers() -> Teachers:
    """Return the data for all teachers as a <Teachers> instance (dict).
    This data is cached, so subsequent calls get the same instance.
    """
    try:
        return SHARED_DATA["TEACHERS"]
    except KeyError:
        pass
    teachers = Teachers()
    SHARED_DATA["TEACHERS"] = teachers
    return teachers


def class_days_aSc(klass: str) -> str:
    """Return a "timeoff" entry for the given class."""
    cdata = get_classes()[klass]
    try:
        day_periods = cdata.tt_data["AVAILABLE"].split("_")
    except KeyError:
        day_periods = ""
    weektags = []
    nperiods = len(get_periods_aSc())
    for d in range(len(get_days_aSc())):
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


def teacher_days_aSc(tid: str) -> str:
    """Return a "timeoff" entry for the given teacher."""
    tdata = get_teachers()[tid]
    try:
        day_periods = tdata.tt_data["AVAILABLE"].split("_")
    except KeyError:
        day_periods = ""
    weektags = []
    nperiods = len(get_periods_aSc())
    for d in range(len(get_days_aSc())):
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


def get_rooms():
    """Return an ordered mapping of rooms: {rid -> name}.
    This data is cached, so subsequent calls get the same instance.
    """
    try:
        return SHARED_DATA["ROOMS"]
    except KeyError:
        pass
    rooms = dict(db_key_value_list(
            "TT_ROOMS",
            "RID",
            "NAME",
            sort_field="RID"
        )
    )
    SHARED_DATA["ROOMS"] = rooms
    return rooms


def get_rooms_aSc() -> list[dict]:
    """Return an ordered list of aSc elements for the rooms."""
    return [
        {"@id": idsub(rid), "@short": rid, "@name": name}
        for rid, name in get_rooms().items()
    ]


def get_subjects():
    """Return an ordered mapping of subjects: {sid -> name}.
    This data is cached, so subsequent calls get the same instance.
    """
    try:
        return SHARED_DATA["SUBJECTS"]
    except KeyError:
        pass
    subjects = dict(db_key_value_list(
            "SUBJECTS",
            "SID",
            "NAME",
            sort_field="NAME"
        )
    )
    SHARED_DATA["SUBJECTS"] = subjects
    return subjects


def get_subjects_aSc() -> list[dict]:
    """Return an ordered list of aSc elements for the subjects."""
    return [
        {"@id": idsub(sid), "@short": sid, "@name": name}
        for sid, name in get_subjects().items()
    ]


def get_classes_aSc():
    """Return an ordered list of aSc elements for the classes."""
    classes = []
    for klass, cdata in get_classes().items():
        if klass.startswith("XX"):
            continue
        classes.append(
            {
                "@id": idsub(klass),
                "@short": klass,
                "@name": cdata.name,
                "@classroomids": cdata.classroom,
                "@timeoff": class_days_aSc(klass)
            }
        )
    return classes


def get_groups_aSc():
    """Return an ordered list of aSc elements for the groups within the classes."""
    def parse_groups(divisions: list[list[str]]):
        groups = [T["WHOLE_CLASS"]]

    group_list = []
    group_info = {}
    SHARED_DATA["GROUP_INFO"] = group_info
    for klass, cdata in get_classes().items():
        if klass.startswith("XX"):
            continue
        g = T["WHOLE_CLASS"]
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
        __group_info = build_group_data(cdata.divisions)
        group_info[klass] = __group_info
        divisions = __group_info["INDEPENDENT_DIVISIONS"]
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


    classes = []
    groups = []
    for klass in c_list:
        if klass.startswith("XX"):
            continue
        classes.append(_classes.class_data(klass))
        groups += _classes.groups(klass)
    if __TEST:
        print("\n ********** aSc DATA **********")
        print("\n  aSc-CLASSES:", classes)
        print("\n  aSc-GROUPS:", groups)





class Classes_aSc(Classes):
    def groups(self, klass):
        """Return a list of aSc group definitions for the given class."""
        group_list = []
        gi = 0  # "division" number (a list of mutually exclusive sub-groups)
        for division in self.class_divisions[klass]:
            for g in division:
                if g == "*":
                    g = WHOLE_CLASS
                group_list.append(
                    {
                        "@id": idsub(f"{klass}-{g}"),
                        "@classid": klass,
                        "@name": g,
                        "@entireclass": "1" if len(division) == 1 else "0",
                        "@divisiontag": str(gi),
                    }
                )
            gi += 1
        return group_list

    #

    #
    def get_lessons(self, rooms):
        """Build list of lessons for aSc-timetables."""
        lesson_list = []

        # new
        valid_groups = {}  # used for "simplifying" groups

        for tag, data in self.lessons.items():
            block = data["block"]
            if block and block != "++":
                continue  # not a timetabled lesson
            sid = idsub(data["SID"])
            klass = data["CLASS"]
            _classes = set()
            groups0 = data["GROUPS"]
            gids = sorted(groups0)
            if gids:
                _classes_groups = {}
                for g in gids:
                    k, gg = class_group_split(g)
                    _classes.add(k)
                    try:
                        _classes_groups[k].append(g)
                    except KeyError:
                        _classes_groups[k] = [g]
                # "Simplify" groups. If a combination of groups can be
                # expressed as the whole class or one of the declared
                # groups, do it.
                _gids = []
                for k, gl in _classes_groups.items():
                    try:
                        gx = self.groupsets_class[k][frozenset(gl)]
                        try:
                            _gset = valid_groups[k]
                        except KeyError:
                            # Initialize with whole class
                            _gset = {k: idsub(f"{k}-{WHOLE_CLASS}")}
                            valid_groups[k] = _gset
                            for d in self.class_divisions[k]:
                                if len(d) > 1:
                                    for g in d:
                                        _gset[g] = idsub(f"{k}-{g}")
                        try:
                            _gx = _gset[gx]
                            _gids.append(_gx)
                            # print("+++", k, gl, _gx)
                        except KeyError:
                            for kg in gl:
                                _gids.append(idsub(kg.replace(".", "-", 1)))
                            # print("---", k, gl)
                    except KeyError:
                        _gids += gl
                groups = ",".join(_gids)
                # print("???", tag, gids, "-->", groups)
            else:
                REPORT("WARN", _LESSON_NO_GROUP.format(klass=klass, sid=sid))
                groups = ""
            classes = ",".join(sorted(_classes))
            # print("???", tag, sid, "-->", groups)

            _tids = sorted(data["TIDS"])
            if (not _tids) and (not data["REALTIDS"]):
                REPORT("WARN", _LESSON_NO_TEACHER.format(klass=klass, sid=sid))
                continue
            tids = ",".join(sorted(_tids))

            # TODO: Multiple rooms are not (presently) supported in the aSc-XML files.
            # Make a simple list of all permissible rooms as options.
            _rset = set()
            for r in data["ROOMS"]:
                for _r0 in r.split("+"):
                    for _r in _r0.split("/"):
                        _rset.add(_r)
            try:
                _rset.remove("?")
            except KeyError:
                pass
            else:
                xrooms = set.intersection(
                    *[set(rooms.rooms_for_class[k]) for k in _classes]
                )
                if not xrooms:
                    raise TT_Error(
                        _NO_JOINT_ROOMS.format(
                            classes=classes, sid=sid, tag=tag
                        )
                    )
                _rset.update(xrooms)
            myrooms = ",".join(sorted(_rset))
            #            print("*** ROOMS:", myrooms)

            dmap = data["lengths"]
            if dmap:
                tags = []
                for d in sorted(dmap):
                    t = f"{tag}__{d}" if len(dmap) > 1 else tag
                    tags.append((t, d, dmap[d]))
                # TODO: check use of tags for placement, etc.!
                if len(tags) > 1:
                    print("&&& multitags:", tags)
                for tag, d, n in tags:
                    lesson = {
                        "@id": tag,
                        "@classids": classes,
                        "@subjectid": sid,
                        "@groupids": groups,
                        "@teacherids": tids,
                        "@durationperiods": str(d),
                        # Note that the number of periods in aSc means the
                        # number of _single_ periods:
                        "@periodsperweek": str(n * d),
                        "@classroomids": myrooms,
                    }
                    lesson_list.append(lesson)
        return lesson_list


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
                "@columns": "id,short,name,timeoff",
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


###


#class Placements_aSc(Placements):
class Placements_aSc:
    def get_presets(self):
        plist = []
        for tag, places_list in self.predef:
            ptags = self.classes_data.parallel_tags[tag]
            # print(f"??? {tag} X {len(ptags)}")
            for t in ptags:
                plist.append((t, places_list))
                # print("       :::", t, places_list)
        return plist

    #
    def placements(self):
        plist = self.get_presets()
        cards = []
        for tag, places_list in plist:
            l = self.classes_data.lessons[tag]
            roomset = set()
            for r in l["ROOMS"]:
                roomset.update(r.replace("+", "/").split("/"))
            rooms = ",".join(sorted(roomset))
            # print("?!?!", tag, rooms)
            for d, p in places_list:
                cards.append(
                    {
                        "@lessonid": tag,
                        "@period": p,
                        "@day": d,
                        "@classroomids": rooms,
                        "@locked": "1",
                    }
                )
        return cards

    #
    def placements_extern(self, working_folder, a_file, days, periods):
        """Get the preset placements from a fet "activities" file (<a_file>)
        which is generated by a successful run of fet.
        These activities should be "locked".
        To associate lesson "tags" with "lids" (and "xlids"), the file
        "tag-lids.json" – generated by fet_data.py – is needed.
        """
        tag_places = {}
        for tag, places_list in self.get_presets():
            tag_places[tag] = frozenset(places_list)  # {(d, p), ... }
            # print("???", tag, tag_places[tag])
        # Get the external placements
        with open(a_file, "rb") as fh:
            xml = fh.read()
        pos_data = xmltodict.parse(xml)
        pos_list = pos_data["Activities_Timetable"]["Activity"]
        lid_data = {}
        for p in pos_list:
            lid = p["Id"]
            # print(f"  ++ {lid:4}: {p['Day']}.{p['Hour']} @ {p['Room']}")
            lid_data[lid] = dict(p)
        # Get tag_lids from working_folder('tag-lids.json')
        with open(os.path.join(working_folder, "tag-lids.json"), "rb") as fh:
            tag_lid_data = json.load(fh)
        tag_lids = tag_lid_data["tag-lids"]
        lid_xlids = tag_lid_data["lid-xlids"]
        # Compile the necessary associations and construct the aSc entries
        cards = []
        tag_data = {}
        for tag, lids in tag_lids.items():
            presets = tag_places.get(tag) or set()
            data = []
            for lid in lids:
                item = lid_data[lid]
                data.append(item)
                d = days.get_id(item["Day"])
                p = periods.get_id(item["Hour"])
                # if (d, p) in presets:
                #    print("$$$", tag, d, p)
                cards.append(
                    {
                        "@lessonid": tag,
                        "@period": p,
                        "@day": d,
                        "@classroomids": item["Room"] or "",
                        "@locked": "1" if (d, p) in presets else "0",
                    }
                )
                try:
                    xlids = lid_xlids[lid]
                except KeyError:
                    pass
                else:
                    item["xrooms"] = [lid_data[xlid]["Room"] for xlid in xlids]
            tag_data[tag] = data
        # Save the associations in a general format
        outpath = os.path.join(working_folder, "tag-placements.json")
        with open(outpath, "w", encoding="utf-8") as fh:
            json.dump(tag_data, fh, indent=4)
        print("\nLesson tag placements ->", outpath)
        return cards


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
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

    if __TEST:
        _class = "10G"
        class_timeout = class_days_aSc(_class)
        print(f"\n*** CLASS AVAILABILITY: {_class} ***")
        print(f"   {class_timeout}")
        print("\n  ==================================================")

    if __TEST:
        _tid = "VT"
        teacher_timeout = teacher_days_aSc(_tid)
        print(f"\n*** TEACHER AVAILABILITY: {_tid} ***")
        print(f"   {teacher_timeout}")
        print("\n  ==================================================")

    allrooms = get_rooms()
    if __TEST:
        print("\n*** ROOMS ***")
        for rdata in get_rooms_aSc():
            print("   ", rdata)
        print("\n  ==================================================")

    allsubjects = get_subjects()
    if __TEST:
        print("\n*** SUBJECTS ***")
        for sdata in get_subjects_aSc():
            print("   ", sdata)

    if __TEST:
        print("\n*** CLASSES ***")
        for cdata in get_classes_aSc():
            print("   ", cdata)

    groups = get_groups_aSc()
    if __TEST:
        print("\n*** CLASS-GROUPS ***")
        for gdata in groups:
            print("   ", gdata)


    quit(0)

    _classes = Classes_aSc(periods)
    #    if _classes.days != list(_days):
    #        print("\nDAYS MISMATCH:", _classes.days)
    #        quit(1)
    if __TEST:
        print("\n*** CLASS-DAYS ***")
        for klass in _classes.class_days_periods:
            _class_periods = _classes.class_days(klass)
            print(f"   class {klass}:", _class_periods)
        print("\n  ==================================================")

    _rooms = Rooms_aSc()
    allrooms = _rooms.get_rooms()
    if __TEST:
        print("\nROOMS:")
        for rdata in allrooms:
            print("   ", rdata)

    _subjects = Subjects_aSc()
    subjects = _subjects.get_subjects()
    if __TEST:
        print("\nSUBJECTS:")
        for sdata in subjects:
            print("   ", sdata)

    _teachers = Teachers_aSc(_classes.days, _periods)

    if __TEST:
        print("\n ********** READ LESSON DATA **********\n")
    c_list = _classes.all_lessons(
        SUBJECTS=_subjects, ROOMS=_rooms, TEACHERS=_teachers
    )
    print("\n ... read data for:", c_list)

    if __TEST:
        print("\n  CLASSROOMS:", _classes.classrooms)
        _klass = "12G"
        print("\nCLASS", _klass)
        print("\n  DIVISIONS:", _classes.class_divisions[_klass])
        print("\n  GROUPS:", _classes.class_groups[_klass])

    teachers = _teachers.get_teachers(_classes.timetable_teachers)
    if __TEST:
        print("\nTEACHERS:")
        # for tid, tname in _teachers.items():
        #    blocked = _teachers.blocked_periods.get(tid) or '–––'
        #    print("  ", tid, tname, blocked)
        for tdata in teachers:
            print("   ", tdata)
        print("\nLONG TAGS:\n", _teachers.longtag.values())

    from timetable.basic_data import TT_CONFIG

    outdir = DATAPATH(TT_CONFIG["OUTPUT_FOLDER"])
    os.makedirs(outdir, exist_ok=True)

    # Check-lists for teachers
    outpath = os.path.join(outdir, "teacher_check.txt")
    with open(outpath, "w", encoding="utf-8") as fh:
        fh.write(
            "STUNDENPLAN 2021/22: Lehrer-Stunden\n"
            "===================================\n"
        )
        fh.write(_classes.teacher_check_list())
    print("\nTEACHER CHECK-LIST ->", outpath)

    classes = []
    groups = []
    for klass in c_list:
        if klass.startswith("XX"):
            continue
        classes.append(_classes.class_data(klass))
        groups += _classes.groups(klass)
    if __TEST:
        print("\n ********** aSc DATA **********")
        print("\n  aSc-CLASSES:", classes)
        print("\n  aSc-GROUPS:", groups)

    lessons = _classes.get_lessons(_rooms)
    if __TEST:
        print("\n ********* aSc LESSONS *********\n")
        # for l, data in _classes.lessons.items():
        #    print(f"   {l}:", data)
        for l in lessons:
            print("   ", l)
        print("\n  ======================================================\n")

    cards = Placements_aSc(_classes)
    activities_path = getActivities(outdir)
    if activities_path:
        cardlist = cards.placements_extern(
            outdir, activities_path, _days, _periods
        )
    else:
        cardlist = cards.placements()
    if __TEST:
        print("\n ********* FIXED LESSONS *********\n")
        # for l, data in _classes.lessons.items():
        #    print(f"   {l}:", data)
        for card in cardlist:
            print("   ", card)

    xml_aSc = xmltodict.unparse(
        build_dict(
            ROOMS=allrooms,
            PERIODS=periods,
            TEACHERS=teachers,
            SUBJECTS=subjects,
            CLASSES=classes,
            GROUPS=groups,
            LESSONS=lessons,
            CARDS=cardlist,
            #            CARDS = [],
        ),
        pretty=True,
    )

    outpath = os.path.join(outdir, "tt_out.xml")
    with open(outpath, "w", encoding="utf-8") as fh:
        fh.write(xml_aSc.replace("\t", "   "))
    print("\nTIMETABLE XML ->", outpath)
