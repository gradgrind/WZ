"""
ui/abi_wani.py

Last updated:  2023-04-09

A "Page" for editing Abitur grades in a Waldorf school in Niedersachsen.

=+LICENCE=============================
Copyright 2023 Michael Towers

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

# A4 is roughly 842pt x 595pt – allow for margins of about 60pt
ABITUR_FORM = "ABITUR_FORM_WANI"

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
    start.setup(os.path.join(basedir, "DATA-2023"))
else:
    from ui.ui_base import StackPage as Page

T = TRANSLATIONS("ui.modules.abi")

### +++++

from core.base import class_group_split, Dates
from core.db_access import open_database, db_values
from core.basic_data import check_group
from core.pupils import pupil_name
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
    qdate2date,
)
# from ui.grid_base import GridViewAuto as GridView
from ui.grid_base import GridViewHFit as GridView
# from ui.grid_base import GridView
from ui.grid_base import StyleCache
from grades.grades_base import (
    GetGradeConfig,
    FullGradeTable,
    UpdatePupilGrades,
)

from ui.cell_editors import CellEditorTable, CellEditorDate

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


def date_printer(properties):
    """Display delegate for dates."""
    date = properties["VALUE"]
    if date:
        return Dates.print_date(date, CONFIG["DATEFORMAT"])
    else:
        return ""


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
        self.abiview.setup(self.cell_changed)
        vboxl.addWidget(self.abiview)
#        self.pupil_data_table.signal_modified.connect(self.updated)

        # Various "controls" in the panel on the right
#        grade_config = get_grade_config()
#        self.info_fields = dict(grade_config["INFO_FIELDS"])
        formbox = QFormLayout()
        vboxr.addLayout(formbox)
        self.group_selector = QComboBox()
        self.group_selector.currentTextChanged.connect(self.select_group)
        formbox.addRow(T["GROUP"], self.group_selector)

        # Date fields
#TODO
        firstday = QDate.fromString(
            CALENDAR["FIRST_DAY"], Qt.DateFormat.ISODate
        )
        lastday = QDate.fromString(CALENDAR["LAST_DAY"], Qt.DateFormat.ISODate)
        date_format = date2qt(CONFIG["DATEFORMAT"])

        self.modified_time = QLineEdit()
        self.modified_time.setReadOnly(True)
        formbox.addRow(T["MODIFIED_TIME"], self.modified_time)

        vboxr.addWidget(HLine())

        vboxr.addWidget(QLabel(T["Pupils"]))
        self.pupil_list = QListWidget()
        self.pupil_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.pupil_list.currentRowChanged.connect(self.select_pupil)
        vboxr.addWidget(self.pupil_list)

        #+++++++++ Show/Hide grid
        # Assumes grid not suppressed ...
        # def __grid_show(state):
        #    self.abiview.grid_group.setVisible(show_grid.isChecked())
        # show_grid = QCheckBox("SHOW_GRID")
        # show_grid.setCheckState(Qt.CheckState.Checked)
        # show_grid.stateChanged.connect(__grid_show)
        # vboxr.addWidget(show_grid)
        #---------

        vboxr.addSpacing(10)
        make_pdf = QPushButton(T["Export_PDF"])
        make_pdf.clicked.connect(self.to_pdf)
        vboxr.addWidget(make_pdf)
        vboxr.addSpacing(10)
        make_cert = QPushButton(T["Make_Certificate"])
        make_cert.clicked.connect(self.make_certificate)
        vboxr.addWidget(make_cert)

    def cell_changed(self, properties: dict):
        if not self.current_pid:
            return
        new_value = properties["VALUE"]
        grades = self.line_data[1]
        tag = properties["TAG"]
        # print("§§§ CHANGED:", tag, new_value)
        if (sid := grades["__SIDMAP__"].get(tag)):
            grades[sid] = new_value
        grades[tag] = new_value
        self.set_tile(tag, new_value)
        # Update this pupil's grades (etc.) in the database
        changes, timestamp = UpdatePupilGrades(
            self.grade_table, self.current_pid
        )
        # Display updates
        self.grade_table["MODIFIED"] = timestamp
        self.modified_time.setText(timestamp)
        for sid, g0 in changes:
            print(" ..", sid, g0, (g := grades[sid]))
            self.set_tile(sid, g)
        self.tilemap["NO_FHS"].setVisible(gdata["REPORT_TYPE"] == "Abi")


    def init_data(self):
        gcon = GetGradeConfig()
        grade_click_handler = CellEditorTable(gcon["&ABI_GRADES"])
        date_click_handler = CellEditorDate(empty_ok=True)
        self.suppress_callbacks = True
        self.group_selector.clear()
        self.pupil_list.clear()
        # Collect pupil groups with Abitur configuration
        abigroups = {}
        try:
            g = ""
            tag = ""
            for g, dlist in gcon["GROUP_DATA"].items():
                for tag, data in dlist:
                    if tag == "Abitur":
                        abigroups[g] = data
        except:
            REPORT("ERROR", T["GROUP_DATA_STRUCTURE"].format(g=g, tag=tag))
            return
        groups = []
        for g in abigroups:
            klass, group = class_group_split(g)
            if not check_group(klass, group):
                REPORT(
                    "ERROR",
                    T["BAD_ABI_GROUP_IN_CONFIG"].format(group=g),
                )
                continue
            groups.append(g)
        self.group_selector.addItems(sorted(groups))
#        self.group_selector.setCurrentText(self.class_group)  # no exception
        # Enable callbacks
        self.suppress_callbacks = False

        ## Set up grid cells
        self.tilemap = {}     # references to tagged tiles
        configpath = DATAPATH(f"CONFIG/{ABITUR_FORM}")
        config = MINION(configpath)
        ROWS = [int(i) for i in config["ROWS"]]
        COLS = [int(i) for i in config["COLS"]]
#--
        print("HEIGHT TOTAL =", sum(ROWS))
        print("WIDTH TOTAL =", sum(COLS))

        self.abiview.init(ROWS, COLS, suppress_grid=True)
        for configline in config["TEXT_CELLS"]:
            try:
                key, row, col, size, text, style = configline
            except ValueError:
                REPORT(
                    "ERROR",
                    T["BAD_CONFIGLINE"].format(
                        path=configpath,
                        data="\n".join(repr(x) for x in configline)
                    )
                )
            irow = int(row)
            icol = int(col)
            isize = int(size)
            # Convert boolean style values
            for k in ("bold", "rotate"):
                try:
                    if style.pop(k).upper() in ("1", "TRUE"):
                        style[k] = True
                except KeyError:
                    pass
            # Convert integer style values
            for k in ("cspan", "rspan", "border_width"):
                try:
                    style[k] = int(style.pop(k))
                except KeyError:
                    pass
            tile = self.abiview.add_text_item(irow, icol, isize, text, style)
            if key:
                self.tilemap[key] = tile
                if key[0] == "G":
                    tile.set_property("EDITOR", grade_click_handler)
                elif key.startswith("DATE_"):
                    tile.set_property("EDITOR", date_click_handler)
                    tile.set_property("DELEGATE", date_printer)
                tile.set_property("TAG", key)
        # print("§§§ --->", sorted(self.tilemap))
        self.set_tile("SCHOOLYEAR", CALENDAR["SCHOOLYEAR_PRINT"])
        self.select_group(self.group_selector.currentText())

    def select_group(self, group):
        if self.suppress_callbacks:
            print("Class change handling disabled:", group)
            return
        self.current_pid = None
        self.grade_table = FullGradeTable("Abitur", group, "")
        self.suppress_callbacks = True
        self.pupil_data_list = self.grade_table["PUPIL_LIST"]
        # [(pdata, grademap), ... ]
        # print("FIELDS", list(self.grade_table))
        self.modified_time.setText(self.grade_table["MODIFIED"])
        self.pupil_list.clear()
        for item in self.pupil_data_list:
            self.pupil_list.addItem(pupil_name(item[0]))
        self.suppress_callbacks = False
        # Select first (gui) list element ...
        self.pupil_list.setCurrentRow(0)

    def select_pupil(self, index):
        self.line_data = self.pupil_data_list[index]
        pdata, gdata = self.line_data
        self.current_pid = pdata["PID"]
        self.set_tile("PUPIL", pupil_name(pdata))
        for sid, g in gdata.items():
            print(" ..", sid, g)
            self.set_tile(sid, g)
        self.tilemap["NO_FHS"].setVisible(gdata["REPORT_TYPE"] == "Abi")

    def set_tile(self, key, value):
        try:
            tile = self.tilemap[key]
        except KeyError:
            return None
        # print("\n$$$", key, value)
        tile.set_text(value)
        return tile

    def read_tile(self, key):
        return self.tilemap[key].get_property("VALUE")

    def to_pdf(self):
        pdata = self.line_data[0]
        sortname = pdata["SORT_NAME"]
        fpath = SAVE_FILE(
            T["PDF_FILE"],
            T["pdf_filename"].format(name=sortname)
        )
        self.abiview.export_pdf(fpath)

    def make_certificate(self):
        print("TODO: make_certificate")


class AbiturGradeView(GridView):
    def setup(self, callback):
        self.callback_cell_changed = callback

    def add_text_item(self, row, col, size, text, style):
#?
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
        return tile

    def cell_modified(self, properties: dict):
        """Override base method in grid_base.GridView."""
        self.callback_cell_changed(properties)

    def export_pdf(self, fpath=None):
        if not fpath:
            fpath = SAVE_FILE(
                "pdf-Datei (*.pdf)",
#TODO: get pupil name, etc
                "ABITUR-ERGEBNIS" + ".pdf"
            )
            if not fpath:
                return
        if not fpath.endswith(".pdf"):
            fpath += ".pdf"
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        ## I guess the grid would normally not be shown (perhaps
        ## it would even be suppressed):
        # grid_shown = self.grid_group.isVisible()
        # self.grid_group.setVisible(False)
        self.to_pdf(fpath, can_rotate = True)
        # self.grid_group.setVisible(grid_shown)


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
            [   ["1+", "1", "1-"],  "sehr gut"      ],
            [   ["2+", "2", "2-"],  "gut"           ],
            [   ["3+", "3", "3-"],  "befriedigend"  ],
            [   ["4+", "4", "4-"],  "ausreichend"   ],
            [   ["5+", "5", "5-"],  "mangelhaft"    ],
            [   ["6"],              "ungenügend"    ],
            [   ["nt"],             "nicht teilgenommen"],
            [   ["t"],              "teilgenommen"  ],
            #[   ["ne"],             "nicht erteilt" ],
            [   ["nb"],             "kann nicht beurteilt werden"],
            [   ["*", NO_GRADE],    "––––––"        ],
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
