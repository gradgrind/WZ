"""
ui/modules/timetable_editor.py

Last updated:  2022-08-29

Show a timetable grid and allow placement of lesson tiles.


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

#TODO --
### Labels, etc.
_TITLE = "WZ – Stundenplanung"

#####################################################

import sys, os, builtins

if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(os.path.dirname(this))
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start
    builtins.STANDALONE = True
    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    #    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))
try:
    standalone = STANDALONE
except NameError:
    standalone = False
if standalone:
    from ui.ui_base import StandalonePage as Page
else:
    from ui.ui_base import StackPage as Page

T = TRANSLATIONS("ui.modules.timetable_editor")

### +++++

from typing import NamedTuple

from ui.modules.timetable_gui import GridViewRescaling, GridPeriodsDays
from core.db_access import open_database
from core.basic_data import (
    get_days,
    get_periods,
    get_classes,
    get_sublessons,
    get_subjects,
    timeslot2index
)
from core.classes import class_divisions
from timetable.activities import Courses, filter_roomlists
from ui.ui_base import (
    QHBoxLayout,
    QVBoxLayout,
    HLine,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QTableWidget,
    QTableWidgetItem,
    QTableView,
    QMenu,
)

### -----

def init():
    MAIN_WIDGET.add_tab(TimetableEditor())


class TimetableEditor(Page):
    name = T["MODULE_NAME"]
    title = T["MODULE_TITLE"]

    def __init__(self):
        super().__init__()
        self.grid_view = GridViewRescaling()
        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(1, 1, 1, 1)
        hbox.addWidget(self.grid_view)
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 5, 0, 0)
        hbox.addLayout(vbox)
#TODO: T ...
        vbox.addWidget(QLabel("Klasse:"))
        self.list1 = QListWidget()
        # self.list1.setMinimumWidth(30)
        self.list1.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        vbox.addWidget(self.list1)
        vbox.addWidget(HLine())
#TODO: T ...
        vbox.addWidget(QLabel("Unterrichtseinheiten:"))
        self.list1.currentTextChanged.connect(self.change_class)
        self.tile_list = QTableWidget()
        self.tile_list.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.tile_list.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.tile_list.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )  # non-editable
        self.tile_list.verticalHeader().hide()
        self.tile_list.horizontalHeader().hide()
        self.tile_list.setShowGrid(False)
        self.tile_list.setColumnCount(4) # sid, duration, groups, teachers
# Do I keep the references to the tiles separately? Does indexing work
# properly if rows are hidden? Yes!
#TODO: T ...
#        self.tile_list.setHorizontalHeaderLabels(("Fach", "Dauer", "Grp", "Lehrer"))
#
# can hide "placed" rows
        self.tile_list.currentCellChanged.connect(self.selected_tile)
        vbox.addWidget(self.tile_list)

#TODO: Use splitter?
        self.list1.setFixedWidth(200)
        self.tile_list.setFixedWidth(200)

    def enter(self):
#TODO
        open_database()

        self.TT_CONFIG = MINION(DATAPATH("CONFIG/TIMETABLE"))
        days = get_days().key_list()
        periods = get_periods().key_list()
        breaks = self.TT_CONFIG["BREAKS_BEFORE_PERIODS"]
        self.grid = WeekGrid(days, periods, breaks)
        self.grid_view.setScene(self.grid)

        self.timetable = Timetable(self)

        self.init_data()

    def init_data(self):
        for k, name in get_classes().get_class_list():
            _item = QListWidgetItem(k)
            _item.setToolTip(name)
            self.list1.addItem(_item)

    def change_class(self, klass):
#TODO
        print("§§§ SELECT CLASS:", klass)
        self.grid.remove_tiles()
        self.timetable.show_class(klass)

    def selected_tile(self, row, col, row0, col0):
        if row >= 0 and row != row0:
            print("§SELECT", row, row0)
#TODO: Will need all the data to enable a search for possible placements:
# Primarily teachers, groups, rooms
# To calculate penalties also other stuff, including placements of all
# other items.
# Should 100% constraints be included with the primaries?

# Can use set_background on the period cell to mark the possible cells.
# Various colours for various degrees of possibility? E.g. absolute no-go
# if a tile in another class must be moved? Only vie direct, conscious
# removal?


#class BlockInfo(NamedTuple):
#    course: CourseData
#    block: BlockTag
#    rooms: list[str]
#    payment_data: PaymentData
#    notes: str
#
#class Sublesson(NamedTuple):
#    id: int
#    TAG: str
#    LENGTH: int
#    TIME: str
#    ROOMS: str

class Activity(NamedTuple):
    sid: str
    subject: str
    tag: str
    classgroups: list[tuple[str,set[str],set[str]]]
    roomlists: list[list[str]]
    alltids: set[str]

    def __str__(self):
        rooms = []
        for rl in self.roomlists:
            rooms.append('|'.join(rl))
        cg = [
            f"{k}:{','.join(gs)}/{','.join(gr) or '-'}"
            for k, gs, gr in self.classgroups
        ]
        return (
            f"<Activity {self.tag}: {self.sid} ({self.subject})"
            f" {'|'.join(sorted(cg))}"
            f" // {','.join(sorted(self.alltids))}"
            f" [{'&'.join(rooms)}]>"
#?
#            f"\n ??? {self.roomlists}"
        )


class Timetable:
    def __init__(self, gui):
        self.gui = gui

# Do these structures really need to be retained? Couldn't they be
# temporarily fetched at the point of use?
        self.courses = Courses()
        # {block-tag -> [Sublesson, ... ]}
        self.tag2lessons = get_sublessons()     # not resetting cache
        self.subjects = get_subjects()

    def gather_info(self):
        activity_list = []
        tag2activity_index = {}
        self.activity_list = activity_list
        self.tag2activity_index = tag2activity_index
        classes = get_classes()
        for tag, infolist in self.courses.tag2entries.items():
            info_ = infolist[0]
            sid = info_.block.sid or info_.course.sid
            name = self.subjects.map(sid)
            a_classes = {}      # {class: {group, ...}} for the activity
            alltids = set()     # tids for the activity as a whole
            allroomlists = []   # rooms for the activity as a whole
            for info_ in infolist:
                tid_ = info_.course.tid
                if tid_ != "--":
                    alltids.add(tid_)
                klass = info_.course.klass
                group = info_.course.group

                # Everything in this list should be related to some
                # timetabled activity.
                # The class can be '--', the group can be empty.
                # Group '*' means "whole class".
                # If class is '--', group must be empty (but that may
                # have been checked earlier).

                if group and klass != "--":
                    if group == '*':
                        a_classes[klass] = None
                    else:
                        try:
                            a_classes[klass].add(group)
                        except KeyError:
                            # no entry for class yet
                            a_classes[klass] = {group}
                        except AttributeError:
                            # whole class already entered
                            pass
                if info_.rooms:
                    allroomlists.append(info_.rooms)
            class_groups = []
            for k in sorted(a_classes):
                gset = a_classes[k]
                if gset:
                    ginfo = classes.group_info(k)
                    chipdata = class_divisions(
                        gset,
                        ginfo["GROUP_MAP"],
                        ginfo["INDEPENDENT_DIVISIONS"]
                    )
                    class_groups.append(
                        (k, chipdata.basic_groups, chipdata.rest_groups)
                    )
                else:
                    class_groups.append((k, {'*'}, set()))
            try:
                room_lists = filter_roomlists(allroomlists)
            except ValueError:
                SHOW_ERROR(
                    T["BLOCK_ROOM_CONFLICT"].format(
                        klass=klass,
                        sid=sid,
                        tag=tag,
                        rooms=repr(allroomlists),
                    ),
                )
                room_lists = [['+']]
            activity = Activity(
                sid=sid,
                subject=name,
                tag=tag,
                classgroups=class_groups,
                roomlists=room_lists,
                alltids=alltids,
            )
            ix = len(activity_list)
# --
            print(f"§ACTIVITY {ix}:", activity)
            activity_list.append(activity)
            tag2activity_index[tag] = ix
#TODO: also need lists for classes and teachers – with specialized
# entries for groups, teachers and – somehow – rooms (because of the
# simplification function, this could be a bit tricky).





#TODO: At the moment this is just a collection of sketches ...
    def sort_groups(self):

        self.fullgroup2index = {}
        self.class2group2division = {}
        # Build group/division mappings for some class
        classes = get_classes()
        group_index = 0
        for klass, kname in classes.get_class_list():
            group_info = classes.group_info(klass)
            divisions = group_info["INDEPENDENT_DIVISIONS"]
            self.fullgroup2index[klass] = group_index
            group_index += 1
#? How will the structures be used???
            i = 0
            group2division = {'*': i}
            self.class2group2division[klass] = group2division
            for div in divisions:
                i += 1
                for g in div:
                    group2division[g] = i
# Actually, I could give all groups (in all classes) a unique index
# instead of the string. Would that help?

# An activity has a set/list of groups, which can be the group-indexes.
# To perform a placement check:
#   for each group in the activity:
#      pick up the class entry for the slot(s)
#      if not empty, check that the new group is in the ok-list
# (it is probably ok to assume that the groups in the activity are not
# in conflict with each other – this should be enforced at construction
# time)
# Perhaps it would also be worth considering a bitmap – on a class or
# division basis.

#TODO: A replacement for show_class?
    def enter_class(self, klass):
        grid = self.gui.grid
        tile_list = self.gui.tile_list
        tile_list.clearContents()
#?
        tiledata = []
        tiles = []
        tile_list_hidden = []
        for a_index in self.klass2activities[klass]:
            activity = self.activity_list[a_index]

# ... I might want lesson placement info (time and rooms) from a
# temporary store here, rather than directly from the database.
            lessons = self.tag2lessons.get(activity.tag)
            if lessons:
                for l in lessons:
                    print("  +++", l)

                    d, p = timeslot2index(l.TIME)
                    print("   ---", activity.sid, d, p)

                    t_tids = ','.join(activity.tids)
                    t_groups = '/'.join(activity.groups)
                    t_rooms = l.ROOMS
                    tiledata.append( # for the list of tiles, etc.
                        (
                            activity.sid,
                            str(l.LENGTH),
                            t_groups,
                            t_tids,
                            l.id,
# The room list is probably needed as a list or set ...
                            t_rooms.split(','),

#?
                            chipdata.groups,
                            chipdata.basic_groups,
                        )
                    )

                    tile_index = len(tiles)
                    tile = make_tile(
                        grid,
                        tile_index,
                        duration=l.LENGTH,
#?
                        n_parts=chipdata.num,
                        n_all=chipdata.den,
                        offset=chipdata.offset,

                        text=activity.sid,
# Might want to handle the placing of the corners in the configuration?
# Rooms can perhaps only be added when placed, and even then not always ...
                        tl=t_tids,
                        tr=t_groups,
                        br=t_rooms,
                    )
                    tiles.append(tile)
                    if d >= 0:
                        grid.place_tile(tile_index, (d, p))
                        tile_list_hidden.append(True)
                    else:
                        tile_list_hidden.append(False)
            else:
                print("\nNO LESSONS:", a.tag)

        tile_list.setRowCount(len(tiledata))
        row = 0
        for tdata in tiledata:
            for col in range(4):
                twi = QTableWidgetItem(tdata[col])
                tile_list.setItem(row, col, twi)
            if tile_list_hidden[row]:
                tile_list.hideRow(row)
            row += 1
        tile_list.resizeColumnsToContents()
        tile_list.resizeRowsToContents()
        # Toggle the stretch on the last section here because of a
        # possible bug in Qt, where the stretch can be lost when
        # repopulating.
        hh = tile_list.horizontalHeader()
        hh.setStretchLastSection(False)
        hh.setStretchLastSection(True)





    def show_class(self, klass):
        grid = self.gui.grid
        tile_list = self.gui.tile_list
        tile_list.clearContents()
        classes = get_classes()
        group_info = classes.group_info(klass)
        divisions = group_info["INDEPENDENT_DIVISIONS"]
        # atoms = group_info["MINIMAL_SUBGROUPS"]
        group_map = group_info["GROUP_MAP"]
        # group2atoms = atomic_maps(atoms, list(group_map))
#TODO: How to calculate tile offsets ... maybe using independent-divisions?

        # {block-tag -> [BlockInfo, ... ]}
        tag2infolist = self.courses.klass2tags[klass]

        alist = []
        for tag, infolist in tag2infolist.items():
            info_ = infolist[0]
            sid = info_.block.sid or info_.course.sid
            name = self.subjects.map(sid)
            activity = Activity_(sid, name, tag)

            # Get tids and room lists (from which to choose)
            tids_ = set()       # tids for just this class
            groups_ = set()     # groups for just this class
            allgroups = set()   # groups for the activity as a whole
            alltids = set()     # tids for the activity as a whole
            allroomlists_ = []  # rooms for the activity as a whole
            # Room info for just this class is not really useful, it is
            # possible that the actual rooms used for this class cannot
            # be determined accurately.

            for info_ in infolist:
                tid_ = info_.course.tid
                if tid_ != "--":
                    tids_.add(tid_)
                if info_.course.group:
                    groups_.add(info_.course.group)
            activity.set_tids(sorted(tids_))
            activity.set_groups(sorted(groups_))

            # For the other stuff, info from all classes is needed
            for info_ in self.courses.tag2entries[tag]:
                tid_ = info_.course.tid
                if tid_ != "--":
                    alltids.add(tid_)
                cg = info_.course.class_group()
                if cg:
                    allgroups.add(cg)
                if info_.rooms:
                    allroomlists_.append(info_.rooms)
            activity.set_all_tids(alltids)
            activity.set_all_groups(allgroups)
#TODO: This was already done for the Activity!
            activity.set_all_rooms(
                simplify_room_lists_(allroomlists_, klass, tag)
            )
            alist.append(activity)
# Sort lesson names?
        alist.sort(key=lambda a: a.subject)

        tiledata = []
        tiles = []
        tile_list_hidden = []
        for a in alist:
            print("\n§§§", a.groups, a.allgroups, a.tag, a.sid, a.subject, a.tids, a.alltids)
# a.allgroups is a – possibly unoptimized – set of all groups, with class,
# and is needed for clash checking. However, if group clash checking is
# done on a class-by-class basis, I will probably need the groups as in
# chipdata.basic_groups below, but for each involved class.
# Perhaps as an ordered list of (class, group-set) pairs.


# Shouldn't some of this Activity stuff be done just once for all classes?

            chipdata = class_divisions(
                    a.groups,
                    group_map,
                    divisions
                )
# The chipdata stuff covers only the current class
            print("    GROUPS:", chipdata.groups)
            print("    SET:", chipdata.basic_groups)
            print(f"    {chipdata.num}/{chipdata.den} @ {chipdata.offset}")



# a.alltids is a set of all tids and is needed for clash checking

            print("    ALL ROOMS:", a.roomlists)
# a.roomlists will be needed for allocating and reallocating rooms

            lessons = self.tag2lessons.get(a.tag)
            if lessons:
                for l in lessons:
                    print("  +++", l)

                    d, p = timeslot2index(l.TIME)
                    print("   ---", a.sid, d, p)

                    t_tids = ','.join(a.tids)
                    t_groups = '/'.join(a.groups)
                    t_rooms = l.ROOMS
                    tiledata.append( # for the list of tiles, etc.
                        (
                            a.sid,
                            str(l.LENGTH),
                            t_groups,
                            t_tids,
                            l.id,
# The room list is probably needed as a list or set ...
                            t_rooms.split(','),
                            chipdata.groups,
                            chipdata.basic_groups,
                        )
                    )

                    tile_index = len(tiles)
                    tile = make_tile(
                        grid,
                        tile_index,
                        duration=l.LENGTH,
                        n_parts=chipdata.num,
                        n_all=chipdata.den,
                        offset=chipdata.offset,
                        text=a.sid,
# Might want to handle the placing of the corners in the configuration?
# Rooms can perhaps only be added when placed, and even then not always ...
                        tl=t_tids,
                        tr=t_groups,
                        br=t_rooms,
                    )
                    tiles.append(tile)
                    if d >= 0:
                        grid.place_tile(tile_index, (d, p))
                        tile_list_hidden.append(True)
                    else:
                        tile_list_hidden.append(False)
            else:
                print("\nNO LESSONS:", a.tag)

        tile_list.setRowCount(len(tiledata))
        row = 0
        for tdata in tiledata:
            for col in range(4):
                twi = QTableWidgetItem(tdata[col])
                tile_list.setItem(row, col, twi)
            if tile_list_hidden[row]:
                tile_list.hideRow(row)
            row += 1
        tile_list.resizeColumnsToContents()
        tile_list.resizeRowsToContents()
        # Toggle the stretch on the last section here because of a
        # possible bug in Qt, where the stretch can be lost when
        # repopulating.
        hh = tile_list.horizontalHeader()
        hh.setStretchLastSection(False)
        hh.setStretchLastSection(True)

#TODO: Will need to consider activities which cover more than one class!
# Actually, there is one per tag ... or perhaps those details can be
# left to the lessons/chips?
# Maybe a subclass ClassActivity for class-specific data?
class Activity_:
    __slots__ = (
        "sid",
        "subject",
        "tag",
        "tids",
        "groups",
        "allgroups",
        "roomlists",
        "alltids",
    )

    def __init__(self, sid, subject, tag):
        self.sid = sid
        self.subject = subject
        self.tag = tag

#?
    def set_tids(self, tids):
        self.tids = tids

#?
    def set_groups(self, groups):
        self.groups = groups

    def set_all_groups(self, groups):
        self.allgroups = groups

    def set_all_rooms(self, roomlists):
        self.roomlists = roomlists

    def set_all_tids(self, tids):
        self.alltids = tids


def make_tile(
    grid,
    tag,
    duration,
    n_parts,
    n_all,
    offset,
    text,
    tl=None,
    tr=None,
    br=None,
    bl=None
):
    tile = grid.new_tile(
        tag,
        duration=duration,
        nmsg=n_parts,
        offset=offset,
        total=n_all,
        text=text
    )
    if tl:
        tile.set_corner(0, tl)
    if tr:
        tile.set_corner(1, tr)
    if br:
        tile.set_corner(2, br)
    if bl:
        tile.set_corner(3, bl)
    return tile


def simplify_room_lists(roomlists):
    """Simplify room lists, check for room conflicts."""
    # Collect single room "choices" and remove redundant entries
    singles = set()
    while True:
        extra = False
        singles1 = set()
        roomlists1 = []
        for rl in roomlists:
            rl1 = [r for r in rl if r not in singles]
            if rl1:
                if len(rl1) == 1:
                    if rl1[0] == '+':
                        if not extra:
                            roomlists1.append(rl1)
                            extra = True
                    else:
                        singles1.add(rl1[0])
                else:
                    roomlists1.append(rl1)
            else:
                raise ValueError
        if roomlists1 == roomlists:
            return [[s] for s in sorted(singles)] + roomlists
        singles.update(singles1)
        roomlists = roomlists1


def simplify_room_lists_(roomlists, klass, tag):
    """Simplify room lists, check for room conflicts."""
    # Collect single room "choices" and remove redundant entries
    singles = set()
    while True:
        extra = False
        singles1 = set()
        roomlists1 = []
        for rl in roomlists:
            rl1 = [r for r in rl if r not in singles]
            if rl1:
                if len(rl1) == 1:
                    if rl1[0] == '+':
                        if not extra:
                            roomlists1.append(rl1)
                            extra = True
                    else:
                        singles1.add(rl1[0])
                else:
                    roomlists1.append(rl1)
            else:
                SHOW_ERROR(
                    T["BLOCK_ROOM_CONFLICT"].format(
                        klass=klass,
                        sid=sid,
                        tag=tag,
                        rooms=repr(roomlists),
                    ),
                )
        if roomlists1 == roomlists:
            return [[s] for s in sorted(singles)] + roomlists
        singles.update(singles1)
        roomlists = roomlists1


class WeekGrid(GridPeriodsDays):
    def make_context_menu(self):
        self.context_menu = QMenu()
#TODO:
        Action = self.context_menu.addAction("Seek possible placements")
        Action.triggered.connect(self.seek_slots)

    def seek_slots(self):
        print("seek_slots:", self.context_tag)
        #tile = self.tiles[self.context_tag]


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':

### TESTING
#    from core.db_access import open_database
#    open_database()

#    grid = main(set(sys.path[1:]))

#    tt = Timetable(grid)
##    tt.show_class("09G")
#    tt.show_class("11G")
##    tt.show_class("12K")

#    grid.run_standalone()
#    quit(0)

### PROPER
    from ui.ui_base import run

    widget = TimetableEditor()
    widget.enter()

#TODO --
    widget.timetable.gather_info()
#    quit(0)

    widget.resize(1000, 550)
    run(widget)

