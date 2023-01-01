"""
ui/abi_wani.py

Last updated:  2022-12-31

A widget for editing Abitur grades in a Waldorf school in Niedersachsen.

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

ROWS = (
    20, 8, 16, 22, 16, 34,
    14, 7, 14,) + (18, 18, 14,)*4 + (
    14,) + (18, 14,)*4 + (14, 14,)*5 + (
    24, 14, 18,
)
print("A4 is roughly 842pt x 595pt – allow for margins of about 60pt")
print("HEIGHT TOTAL =", sum(ROWS))
COLS = (
    39, 31, 80, 39, 41, 11, 54, 18, 18, 18, 40, 8, 50,
    # 9, 28
)
print("WIDTH TOTAL =", sum(COLS))

# row, col, 0 (default) or font-size,
#  HOW DOES FONT SETTING WORK? grid_base has some constants which are
# not used, and it is generally unclear ...
# cspan=1, rspan=1, grid_cell=False,
# text="", style options
# style_opts:
#    "bg": None,
#    "font": None,
#    "fg": None,#FONT_COLOUR,
#    "halign": "c",
#    "valign": "m",
#    "rotate": False,
#    "border": None,#GRID_COLOUR,
#    "border_width": 1,

FONT1 = 11
FONT_TITLE = 14
FONT_SUBTITLE = 12
#TODO: Maybe rather colour the backgrounds?
COLOUR_PUPIL_DATA = "A800C8"
COLOUR_GRADES = "0000B0"
COLOUR_CALCULATED = "05A5A0"

TEXT_CELLS = (
    (   0, 0, FONT_TITLE, "Abitur-Berechnungsbogen",
        {"bold": True, "cspan":4, "halign":"l", "border_width":0}
    ),
    (   2, 6, FONT_SUBTITLE, "Schuljahr:",
        {"bold": True, "cspan":3, "halign":"r", "border_width":0}
    ),
    (   4, 0, FONT_SUBTITLE, "Name:",
        {"bold": True, "halign":"l", "border_width":0}
    ),
    (   6, 1, FONT1, "Fach", {"cspan": 2, "border_width":0}   ),
    (   6, 3, FONT1, "Kurspunkte", {"cspan": 2, "border_width":0}   ),
    (   6, 6, FONT1, "Mittelwert", {"border_width":0}   ),
    (   6, 10, FONT1, "Berechnungspunkte", {"cspan": 3, "border_width":0}   ),
    (   8, 12, FONT1, "Fach 1 – 4", {}   ),
    (   21, 12, FONT1, "Fach 5 – 8", {}   ),
    (   9, 0, FONT1, "erhöhtes Anforderungsniveau", {"rspan": 8, "rotate":True}   ),
    (   18, 0, FONT1, "grundlegendes Anforderungsniveau", {"rspan": 11, "rotate":True}   ),
    (   9, 1, FONT1, "1", {"rspan": 2}   ),
    (   12, 1, FONT1, "2", {"rspan": 2}   ),
    (   15, 1, FONT1, "3", {"rspan": 2}   ),
    (   18, 1, FONT1, "4", {"rspan": 2}   ),
    (   22, 1, FONT1, "5", {}   ),
    (   24, 1, FONT1, "6", {}   ),
    (   26, 1, FONT1, "7", {}   ),
    (   28, 1, FONT1, "8", {}   ),
    (   9, 3, FONT1, "schr.", {}   ),
    (   10, 3, FONT1, "mündl.", {}   ),
    (   12, 3, FONT1, "schr.", {}   ),
    (   13, 3, FONT1, "mündl.", {}   ),
    (   15, 3, FONT1, "schr.", {}   ),
    (   16, 3, FONT1, "mündl.", {}   ),
    (   18, 3, FONT1, "schr.", {}   ),
    (   19, 3, FONT1, "mündl.", {}   ),
    (   22, 3, FONT1, "mündl.", {}   ),
    (   24, 3, FONT1, "mündl.", {}   ),
    (   26, 3, FONT1, "2. Hj.", {}   ),
    (   28, 3, FONT1, "2. Hj.", {}   ),
    (   9, 7, FONT1, "x", {"rspan": 2, "border_width":0}   ),
    (   9, 8, FONT1, "12", {"rspan": 2, "border_width":0}   ),
    (   9, 9, FONT1, "=", {"rspan": 2, "border_width":0}   ),
    (   12, 7, FONT1, "x", {"rspan": 2, "border_width":0}   ),
    (   12, 8, FONT1, "12", {"rspan": 2, "border_width":0}   ),
    (   12, 9, FONT1, "=", {"rspan": 2, "border_width":0}   ),
    (   15, 7, FONT1, "x", {"rspan": 2, "border_width":0}   ),
    (   15, 8, FONT1, "12", {"rspan": 2, "border_width":0}   ),
    (   15, 9, FONT1, "=", {"rspan": 2, "border_width":0}   ),
    (   18, 7, FONT1, "x", {"rspan": 2, "border_width":0}   ),
    (   18, 8, FONT1, "8", {"rspan": 2, "border_width":0}   ),
    (   18, 9, FONT1, "=", {"rspan": 2, "border_width":0}   ),
    (   22, 7, FONT1, "x", {"border_width":0}   ),
    (   22, 8, FONT1, "4", {"border_width":0}   ),
    (   22, 9, FONT1, "=", {"border_width":0}   ),
    (   24, 7, FONT1, "x", {"border_width":0}   ),
    (   24, 8, FONT1, "4", {"border_width":0}   ),
    (   24, 9, FONT1, "=", {"border_width":0}   ),
    (   26, 7, FONT1, "x", {"border_width":0}   ),
    (   26, 8, FONT1, "4", {"border_width":0}   ),
    (   26, 9, FONT1, "=", {"border_width":0}   ),
    (   28, 7, FONT1, "x", {"border_width":0}   ),
    (   28, 8, FONT1, "4", {"border_width":0}   ),
    (   28, 9, FONT1, "=", {"border_width":0}   ),
    (   30, 2, FONT1, "Alle > 0P.:", {"halign":"l", "cspan":7, "border_width":0}   ),
    (   32, 2, FONT1, "Fach 1 – 4, mindestens 2mal ≥ 5P.:", {"halign":"l", "cspan":7, "border_width":0}   ),
    (   34, 2, FONT1, "Fach 5 – 8, mindestens 2mal ≥ 5P.:", {"halign":"l", "cspan":7, "border_width":0}   ),
    (   36, 2, FONT1, "Fach 1 – 4 ≥ 220:", {"halign":"l", "cspan":7, "border_width":0}   ),
    (   38, 2, FONT1, "Fach 5 – 8 ≥ 80:", {"halign":"l", "cspan":7, "border_width":0}   ),
    (   40, 2, FONT_SUBTITLE, "Summe:",
        {"bold": True, "halign":"r", "border_width":0}
    ),
    (   40, 6, FONT_SUBTITLE, "Note:",
        {"bold": True, "halign":"r", "cspan":3, "border_width":0}
    ),
    (   42, 6, FONT_SUBTITLE, "Datum:",
        {"bold": True, "halign":"r", "cspan":3, "border_width":0}
    ),

# School/Pupil details
    (   0, 4, FONT_TITLE, "Freie Michaelschule",
        {"bold": True, "cspan":-1, "halign":"r", "border_width":0}
    ),
    (   2, 9, FONT_SUBTITLE, "2022 – 2023",
        {"bold": True, "cspan":-1, "fg":COLOUR_PUPIL_DATA, "border_width":0}
    ),
    (   4, 2, FONT_SUBTITLE, "Michaela Musterfrau",
        {"bold": True, "cspan":-1, "halign":"l", "fg":COLOUR_PUPIL_DATA, "border_width":0}
    ),

# Subjects
    (   9, 2, FONT1, "Deutsch", {"rspan": 2, "fg":COLOUR_PUPIL_DATA}   ),
    (   12, 2, FONT1, "Englisch", {"rspan": 2, "fg":COLOUR_PUPIL_DATA}   ),
    (   15, 2, FONT1, "Geschichte", {"rspan": 2, "fg":COLOUR_PUPIL_DATA}   ),
    (   18, 2, FONT1, "Mathematik", {"rspan": 2, "fg":COLOUR_PUPIL_DATA}   ),
    (   22, 2, FONT1, "Biologie", {"fg":COLOUR_PUPIL_DATA}   ),
    (   24, 2, FONT1, "Französisch", {"fg":COLOUR_PUPIL_DATA}   ),
    (   26, 2, FONT1, "Musik", {"fg":COLOUR_PUPIL_DATA}   ),
    (   28, 2, FONT1, "Sport", {"fg":COLOUR_PUPIL_DATA}   ),

# Grades ...
    (   9, 4, FONT1, "10", {"fg":COLOUR_GRADES}   ),
    (   10, 4, FONT1, "*", {"fg":COLOUR_GRADES}   ),
    (   12, 4, FONT1, "05", {"fg":COLOUR_GRADES}   ),
    (   13, 4, FONT1, "12", {"fg":COLOUR_GRADES}   ),
    (   15, 4, FONT1, "08", {"fg":COLOUR_GRADES}   ),
    (   16, 4, FONT1, "13", {"fg":COLOUR_GRADES}   ),
    (   18, 4, FONT1, "08", {"fg":COLOUR_GRADES}   ),
    (   19, 4, FONT1, "*", {"fg":COLOUR_GRADES}   ),
    (   22, 4, FONT1, "09", {"fg":COLOUR_GRADES}   ),
    (   24, 4, FONT1, "07", {"fg":COLOUR_GRADES}   ),
    (   26, 4, FONT1, "12", {"fg":COLOUR_GRADES}   ),
    (   28, 4, FONT1, "14", {"fg":COLOUR_GRADES}   ),
    (   42, 10, FONT_SUBTITLE, "20.6.2020",
        {"bold": True, "cspan":-1, "fg":COLOUR_GRADES}
    ),

# Calculated fields ...
    (   9, 6, FONT1, "10", {"rspan":2, "fg":COLOUR_CALCULATED}   ),
    (   12, 6, FONT1, "8,5", {"rspan":2, "fg":COLOUR_CALCULATED}   ),
    (   15, 6, FONT1, "10,5", {"rspan":2, "fg":COLOUR_CALCULATED}   ),
    (   18, 6, FONT1, "8", {"rspan":2, "fg":COLOUR_CALCULATED}   ),
    (   22, 6, FONT1, "9", {"fg":COLOUR_CALCULATED}   ),
    (   24, 6, FONT1, "7", {"fg":COLOUR_CALCULATED}   ),
    (   26, 6, FONT1, "12", {"fg":COLOUR_CALCULATED}   ),
    (   28, 6, FONT1, "14", {"fg":COLOUR_CALCULATED}   ),
    (   9, 10, FONT1, "120", {"rspan":2, "fg":COLOUR_CALCULATED}   ),
    (   12, 10, FONT1, "102", {"rspan":2, "fg":COLOUR_CALCULATED}   ),
    (   15, 10, FONT1, "126", {"rspan":2, "fg":COLOUR_CALCULATED}   ),
    (   18, 10, FONT1, "64", {"rspan":2, "fg":COLOUR_CALCULATED}   ),
    (   22, 10, FONT1, "36", {"fg":COLOUR_CALCULATED}   ),
    (   24, 10, FONT1, "28", {"fg":COLOUR_CALCULATED}   ),
    (   26, 10, FONT1, "48", {"fg":COLOUR_CALCULATED}   ),
    (   28, 10, FONT1, "56", {"fg":COLOUR_CALCULATED}   ),

    (   9, 12, FONT1, "412", {"rspan":11, "fg":COLOUR_CALCULATED}   ),
    (   22, 12, FONT1, "168", {"rspan":7, "fg":COLOUR_CALCULATED}   ),

    (   30, 10, FONT1, "Ja", {"fg":COLOUR_CALCULATED}   ),
    (   32, 10, FONT1, "Ja", {"fg":COLOUR_CALCULATED}   ),
    (   34, 10, FONT1, "Ja", {"fg":COLOUR_CALCULATED}   ),
    (   36, 10, FONT1, "Ja", {"fg":COLOUR_CALCULATED}   ),
    (   38, 10, FONT1, "Ja", {"fg":COLOUR_CALCULATED}   ),

    (   40, 3, FONT_SUBTITLE, "580",
        {"bold": True, "cspan":2, "border_width":0, "fg":COLOUR_CALCULATED}
    ),
    (   40, 10, FONT_SUBTITLE, "2,4",
        {"bold": True, "cspan":-1, "border_width":0, "fg":COLOUR_CALCULATED}
    ),
)

########################################################################

if __name__ == "__main__":
    import sys, os

    this = sys.path[0]
    appdir = os.path.dirname(os.path.dirname(this))
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start
    from ui.ui_base import StandalonePage as Page

    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    #    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))
else:
    from ui.ui_base import StackPage as Page

T = TRANSLATIONS("ui.modules.abi_wani")

### +++++

from core.db_access import open_database, db_values
from ui.ui_base import (
    QWidget,
    QLabel,
    QFormLayout,
    QLineEdit,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QComboBox,
    QDateEdit,
    QListWidget,
    QAbstractItemView,
    QCheckBox,
    # QtCore
    Qt,
    QDate,
    # Other
    run,
    HLine,
    date2qt,
)
# from ui.grid_base import GridViewAuto as GridView
from ui.grid_base import GridViewHFit as GridView
# from ui.grid_base import GridView
from ui.grid_base import StyleCache

### -----


def init():
    MAIN_WIDGET.add_tab(Abitur())


class Abitur(Page):
    name = T["MODULE_NAME"]
    title = T["MODULE_TITLE"]

    def __init__(self):
        super().__init__()
        self.manager = AbiturManager()
        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.manager)

    def enter(self):
        open_database()
        self.manager.init_data()

    def is_modified(self):
        """Return <True> if there are unsaved changes.
        This module always saves changes immediately.
        """
        return False


# ++++++++++++++ The widget implementation ++++++++++++++

class AbiturManager(QWidget):
    def __init__(self):
        super().__init__()
        hbox = QHBoxLayout(self)
        vboxl = QVBoxLayout()
        hbox.addLayout(vboxl)
        vboxr = QVBoxLayout()
        hbox.addLayout(vboxr)
        hbox.setStretchFactor(vboxl, 1)

        # The class data table
        self.abiview = AbiturGradeView()
        vboxl.addWidget(self.abiview)
#        self.pupil_data_table.signal_modified.connect(self.updated)

        # Various "controls" in the panel on the right
#        grade_config = get_grade_config()
#        self.info_fields = dict(grade_config["INFO_FIELDS"])
        formbox = QFormLayout()
        vboxr.addLayout(formbox)
        self.class_selector = QComboBox()
#        self.class_selector.currentTextChanged.connect(self.changed_class)
        formbox.addRow("CLASS_GROUP", self.class_selector)

        # Date fields
        firstday = QDate.fromString(
            CALENDAR["FIRST_DAY"], Qt.DateFormat.ISODate
        )
        lastday = QDate.fromString(CALENDAR["LAST_DAY"], Qt.DateFormat.ISODate)
        date_format = date2qt(CONFIG["DATEFORMAT"])
        self.grade_date = QDateEdit()
        self.grade_date.setMinimumDate(firstday)
        self.grade_date.setMaximumDate(lastday)
        self.grade_date.setCalendarPopup(True)
        self.grade_date.setDisplayFormat(date_format)
        formbox.addRow("DATE_GRADES", self.grade_date)
#        self.grade_date.dateChanged.connect(self.grade_date_changed)
        self.modified_time = QLineEdit()
        self.modified_time.setReadOnly(True)
        formbox.addRow("MODIFIED", self.modified_time)

        vboxr.addWidget(HLine())

#        vboxr.addWidget(QLabel(T["Pupils"]))
        vboxr.addWidget(QLabel("Pupils"))
        self.pupil_list = QListWidget()
        self.pupil_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        vboxr.addWidget(self.pupil_list)

#+++++++++ Show grid
        def __grid_show(state):
            self.abiview.grid_group.setVisible(show_grid.isChecked())
        show_grid = QCheckBox("SHOW_GRID")
        show_grid.setCheckState(Qt.CheckState.Checked)
        show_grid.stateChanged.connect(__grid_show)
        vboxr.addWidget(show_grid)
#---------

#        make_pdf = QPushButton(T["Export_PDF"])
        make_pdf = QPushButton("Export_PDF")
#        make_pdf.clicked.connect(self.pupil_data_table.export_pdf)
        vboxr.addWidget(make_pdf)

    def init_data(self):
        self.abiview.init(ROWS, COLS)
        for row, col, size, text, style in TEXT_CELLS:
            self.abiview.add_text_item(row, col, size, text, style)


class AbiturGradeView(GridView):
    def setup(self, grade_table):
        pass

    def add_text_item(self, row, col, size, text, style):
        if "bg" not in style:
            style["bg"] = "ffffff"
        try:
            bold = style.pop("bold")
        except KeyError:
            bold = False
        style["font"] = StyleCache.getFont(fontSize=size, fontBold=bold)
        tile = self.grid_tile(row, col, **style)
        tile.set_property("MARGIN", 1)
#?
        tile.set_property("NO_SCALE", True)
        tile.set_text(text)


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    widget = Abitur()
    widget.enter()

    widget.resize(1000, 500)
    run(widget)

    quit(0)



    from qtpy.QtWidgets import QApplication

    app = QApplication([])
    # grid = GridViewRescaling()
    # grid = GridViewHFit() # buggy ...
    # grid = GridView()
    grid = GridViewAuto()
    grid.init(rows, cols)

    grid.grid_line_thick_v(2)
    grid.grid_line_thick_h(1)

    cell0 = grid.get_cell((0, 0))
    cell0.set_text("Not rotated")
    cell0.set_valign("m")
    cell1 = grid.get_cell((0, 2))
    cell1.set_text("Deutsch")
    cell1.set_verticaltext()
    cell1.set_valign("b")
    cell2 = grid.get_cell((0, 4))
    cell2.set_text("English")
    cell2.set_verticaltext()

    cell_1 = grid.get_cell((4, 3))
    cell_1.set_text("A long entry")
    cell_pid = grid.grid_tile(2, 0, text="left", halign="l")
    grid.grid_tile(3, 0, text="right", halign="r")
    grid.grid_tile(4, 0, text="top", valign="t", cspan=2, bg="ffffaa")
    grid.grid_tile(5, 0, text="bottom", valign="b")

    plain_line_editor = CellEditorLine().activate
    cell0.set_property("EDITOR", plain_line_editor)
    grade_editor_I = CellEditorTable(
        [
            [   ["1+", "1", "1-"],   "sehr gut"      ],
            [   ["2+", "2", "2-"],   "gut"           ],
            [   ["3+", "3", "3-"],   "befriedigend"  ],
            [   ["4+", "4", "4-"],   "ausreichend"   ],
            [   ["5+", "5", "5-"],   "mangelhaft"    ],
            [   ["6"],         "ungenügend"    ],
            [   ["nt"],        "nicht teilgenommen"],
            [   ["t"],         "teilgenommen"  ],
        #    [   ["ne"],        "nicht erteilt" ],
            [   ["nb"],        "kann nicht beurteilt werden"],
            [   ["*", "/"],       "––––––"        ],
        ]
    ).activate
    text_editor = CellEditorText().activate
    #    grade_editor = CellEditorList(
    #cell_1.set_property("EDITOR", grade_editor_I)
    cell_1.set_property("EDITOR", text_editor)

    cell3 = grid.get_cell((6, 0))
    cell3.set_property("EDITOR", CellEditorDate().activate)
    cell3.set_property("VALUE", "")
    cell3.set_text("")
    cell4 = grid.get_cell((7, 0))
    cell4.set_property("EDITOR", CellEditorDate(empty_ok=True).activate)
    cell4.set_property("VALUE", "2022-12-01")
    cell4.set_text("2022-12-01")
    grid.resize(600, 400)
    grid.show()

    # Enable package import if running as module
    import sys, os

    # print(sys.path)
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    from core.base import start

    basedir = os.path.dirname(appdir)
    start.setup(os.path.join(basedir, "TESTDATA"))

    fpath = DATAPATH("testing/tmp/grid1.pdf")
    os.makedirs(os.path.dirname(fpath), exist_ok=True)

    titleheight = grid.pt2px(30)
    titlemiddle = grid.pt2px(15)
    footerheight = grid.pt2px(30)
    footermiddle = grid.pt2px(15)

    print("$1", grid.ymarks)

    for yl in 0, -titleheight, grid.grid_height, grid.grid_height + footerheight:
        line = QGraphicsLineItem(0, yl, grid.grid_width, yl)
        line.setPen(StyleCache.getPen(grid.thick_line_width, "ff0000"))
        line.setZValue(10)
        grid.scene().addItem(line)

    t1 = grid.set_title("Main Title", offset=titlemiddle, font_scale=1.2)
    h1 = grid.set_title("A footnote", halign="r",
        y0=grid.grid_height + footerheight, offset=footermiddle
    )

    grid.to_pdf(fpath, titleheight=titleheight, footerheight=footerheight)
    # grid.to_pdf(fpath, can_rotate = False, titleheight=titleheight, footerheight=footerheight)

    #grid.scene().removeItem(t1)
    #grid.scene().removeItem(h1)
    #grid.grid_group.hide()

    app.exec()
