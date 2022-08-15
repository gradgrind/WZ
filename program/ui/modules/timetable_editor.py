"""
ui/modules/timetable_editor.py

Last updated:  2022-08-15

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
from timetable.activities import Courses
from ui.ui_base import (
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
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
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.grid_view)
        vbox = QVBoxLayout()
        hbox.addLayout(vbox)
#TODO: T ...
        vbox.addWidget(QLabel("Klasse:"))
        self.list1 = QListWidget()
        # self.list1.setMinimumWidth(30)
        self.list1.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        vbox.addWidget(self.list1)
        self.list1.currentTextChanged.connect(self.change_class)
        self.list2 = QListWidget()
        self.list2.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        vbox.addWidget(self.list2)

        # Set up grid
        self.grid = self.grid_view.scene()

    def enter(self):
#TODO
        open_database()

        self.TT_CONFIG = MINION(DATAPATH("CONFIG/TIMETABLE"))
        days = get_days().key_list()
        periods = get_periods().key_list()
        breaks = self.TT_CONFIG["BREAKS_BEFORE_PERIODS"]
        self.grid = GridPeriodsDays(days, periods, breaks)
        self.grid_view.setScene(self.grid)

        self.timetable = Timetable(self.grid)

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


# ++++++++++++++ The widget implementation ++++++++++++++


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

class Timetable:
    def __init__(self, grid):
        self.grid = grid
        self.courses = Courses()
        # {block-tag -> [Sublesson, ... ]}
        self.tag2lessons = get_sublessons()     # not resetting cache
        self.subjects = get_subjects()

    def show_class(self, klass):
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
            activity = Activity(sid, name, tag)

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
                if info_.course.group:
                    allgroups.add(info_.course.group)
                if info_.rooms:
                    allroomlists_.append(info_.rooms)
            activity.set_all_tids(alltids)
            activity.set_all_rooms(
                simplify_room_lists(allroomlists_, klass, tag)
            )
            alist.append(activity)
# Sort lesson names?
        alist.sort(key=lambda a: a.subject)

        for a in alist:
            print("§§§", a.groups, a.tag, a.sid, a.subject, a.tids, a.alltids)
            print("         ", a.roomlists)
            lessons = self.tag2lessons.get(a.tag)
            if lessons:
                for l in lessons:
                    print("  +++", l)

# just testing ...

#    a2g = atoms2groups(divisions, group_map, with_divisions=True)
# Maybe better to try to discover which of the original divisions
# is relevant – but it might not be possible to be certain? Maybe in that
# case it wouldn't matter which was chosen!
# That would mean that a lesson can't be placed until all lessons sharing
# the slots are known. The algorithm could be rather complicated, but it
# should be able to prevent striping under certain circumstances.

                    chipdata = class_divisions(
                            a.groups,
                            group_map,
                            divisions
                        )
                    #print("    GROUPS:", chipdata.groups)
                    #print("    SET:", chipdata.basic_groups)
                    #print(f"    {chipdata.num}/{chipdata.den} @ {chipdata.offset}")

                    d, p = timeslot2index(l.TIME)
                    print("   ---", a.sid, d, p)
                    if d < 0:
                        continue
                    ltag = str(l.id)
                    tile = self.grid.new_tile(
                        ltag,
                        duration=l.LENGTH,
                        nmsg=chipdata.num,
                        offset=chipdata.offset,
                        total=chipdata.den,
                        text=a.sid
                    )
                    self.grid.place_tile(ltag, (d, p))


            else:
                print("NO LESSONS:", tag)


#TODO: Will need to consider activities which cover more than one class!
# Actually, there is one per tag ... or perhaps those details can be
# left to the lessons/chips?
class Activity:
    #TODO: __slots__
    def __init__(self, sid, subject, tag):
        self.sid = sid
        self.subject = subject
        self.tag = tag

    def set_tids(self, tids):
        self.tids = tids

    def set_groups(self, groups):
        self.groups = groups

    def set_all_rooms(self, roomlists):
        self.roomlists = roomlists

    def set_all_tids(self, tids):
        self.alltids = tids


def make_tile(grid):
# Need a tag (lesson-id?), duration, number of atoms, total number of atoms,
# offset???!!!, rooms, groups

    tile = grid.new_tile(tag, duration=1, nmsg=1, offset=0, total=2, text="Ta")
    tile.set_corner(0, "BMW")
    tile.set_corner(1, "A")
    tile.set_corner(2, "r10G")
    tile.set_corner(3, "?")

    grid.place_tile(tag, (3, 5))


def simplify_room_lists(roomlists, klass, tag):
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
    widget.resize(1000, 550)
    run(widget)

