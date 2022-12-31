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
    14, 8, 14,) + (18, 18, 14,)*4 + (
    14,) + (18, 14,)*4 + (14, 14,)*5 + (
    24, 14, 16,
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

TEXT_CELLS = (
    (0, 0, 14, "Abitur-Berechnungsbogen", {"cspan":4, "halign":"l"}),
    (0, 4, 14, "Freie Waldorfschule Hannover-Bothfeld", {"cspan":8, "halign":"r"}),
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

#        make_pdf = QPushButton(T["Export_PDF"])
        make_pdf = QPushButton("Export_PDF")
#        make_pdf.clicked.connect(self.pupil_data_table.export_pdf)
        vboxr.addWidget(make_pdf)

    def init_data(self):
        self.abiview.init(ROWS, COLS)


class AbiturGradeView(GridView):
    def setup(self, grade_table):
        pass



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
