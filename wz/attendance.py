# -*- coding: utf-8 -*-
"""
attendance.py

Last updated:  2021-11-30

Gui editor for attendance tables.

=+LICENCE=================================
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

=-LICENCE=================================
"""

TITLE_HEIGHT = 25
ROWS0 = (25, 3)
ROWi0 = len(ROWS0)
ROWn = (25,)
COLS0 = (120, 3)
COLS = (120, 3) + (25,) * 31
COLi0 = len(COLS0)

#?
TCOLS = [f"{n:02d}" for n in range(1, 32)]

COLOUR_WEEKEND = "DDDDDD"
COLOUR_HOLIDAY = "00CC00"
COLOUR_NO_DAY = "99FFFF"

### Messages

_CLASS = "Klasse {klass}"
_SAVE_CLASS = "Daten speichern"
_PAGE = "Seite:"
#?
#_PROGRAM_NAME = "Attendance"
#_OPEN_TABLETYPE = "Tabellendatei"
#_INVALID_DATATABLE = "Ungültige DataTable: {path}\n ... {message}"

#_SAVE_AS_TSV = "Als tsv-Datei speichern?\n\n{path}"
#_UNSUPPORTED_SAVE = "Tabelle speichern – Dateityp '.{ending}'" " wird nicht unterstützt"

#_LOSE_CHANGES = "Es gibt ungespeicherte Änderungen.\n" "Wirklich schließen?"
#_LOSE_CHANGES_OPEN = (
#    "Es gibt ungespeicherte Änderungen.\n" "Neue Datei trotzdem öffnen?"
#)
#_SAVING_FORMAT = (
#    "Formatierungen werden möglicherweise verloren gehen:" "\n{path}\nÜberschreiben?"
#)


########################################################################

import sys, os, builtins, traceback, datetime

if __name__ == "__main__":
    import locale
    print("LOCALE:", locale.setlocale(locale.LC_ALL, ''))
    try:
        builtins.PROGRAM_DATA = os.environ["PROGRAM_DATA"]
    except KeyError:
        this = sys.path[0]
        basedir = os.path.dirname(this)
        builtins.PROGRAM_DATA = os.path.join(basedir, "wz-data")

from ui.ui_base import APP, run, openDialog, saveDialog, get_icon, \
        QWidget, QVBoxLayout, QDialog, QPushButton, QButtonGroup, Qt, \
        QToolBar, QAction, QKeySequence, KeySelector, QLabel, QFrame

# This seems to deactivate activate-on-single-click in filedialog
# (presumably elsewhere as well?)
APP.setStyleSheet("QAbstractItemView { activate-on-singleclick: 0; }")

from core.base import Dates
from core.pupils import Pupils
#from ui.grid0 import GridViewRescaling
from ui.grid0 import GridViewHFit

from ui.editable import EdiTableWidget
#?
from ui.grid0 import GraphicsSupport

### -----

CHOICE_ITEMS = (
    ("", "anwesend"),
    ("A", "ganztägig abwesend"),
    ("Ae", "ganztägig abwesend – entschuldigt"),
    ("T", "teils abwesend"),
    ("Te", "teils abwesend – entschuldigt"),
    ("V", "verspätet"),
    ("Ve", "verspätet – entschuldigt")
)
#TODO: There are more possibilities ... Praktikum, Ausland, beurlaubt?, ...

class Choice(QDialog):
    @classmethod
    def choice(cls, parent=None, x=None, y=None):
        dlg = cls(parent, x, y)
        dlg.exec()
        return dlg.entry

    def __init__(self, parent, x, y):
        super().__init__(parent)
        self.setWindowTitle("Abwesenheit")
        group = QButtonGroup(self)
        group.buttonClicked.connect(self.on_clicked)
        layout = QVBoxLayout(self)
        for k, v in CHOICE_ITEMS:
            label = f"{k}:" if k else "(leer):"
            p = QPushButton(f"{label:8} {v}")
            p.setStyleSheet("text-align:left;")
            p.entry = k
            layout.addWidget(p)
            group.addButton(p)

    def on_clicked(self, btn):
        print("§§§", btn.entry)
        self.entry = btn.entry
        self.accept()

    def reject(self):
        self.entry = None
        super().reject()


class AttendanceTable(EdiTableWidget):
    def activated(self, row, col):
        # This is called when a cell is left-clicked with Ctrl pressed
        # or when the (single) selected cell has "Return/Newline" pressed
        # together with Ctrl.
#        v = ListSelect("?", "???", options)
        item = self.item(row, col)
        if item.flags() & Qt.ItemIsEditable:
            v = Choice.choice(parent=self, x=None, y=None)
            if v is not None:
                self.set_text(row, col, v)


class AttendanceEditor(QWidget):
    def is_modified(self, changed):
        print("CHANGED:", changed)

    def new_action(self, icon, text, shortcut):
        action = QAction(self)
        if shortcut:
            text += f" – [{shortcut.toString()}]"
            action.setShortcut(shortcut)
        action.setText(text)
        action.setIcon(get_icon(icon))
        return action

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.toolbar = QToolBar()
        layout.addWidget(self.toolbar)
        # Class label
        self.class_label = QLabel()
        self.class_label.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.class_label.setLineWidth(3)
        self.class_label.setMidLineWidth(2)
        self.toolbar.addWidget(self.class_label)
        # Page (month)
        self.toolbar.addWidget(QLabel("   "))
        self.toolbar.addSeparator()
        self.toolbar.addWidget(QLabel("   "))
        month1 = Month(SCHOOLYEAR)
        months = []
        i = 12
        while True:
            months.append((month1.month, str(month1)))
            i -= 1
            if i == 0:
                break
            month1.increment()
        self.month_select = KeySelector(
            value_mapping=months,
            changed_callback=self.switch_month
        )
        self.toolbar.addWidget(QLabel(_PAGE))
        self.toolbar.addWidget(self.month_select)
        # File actions
        self.toolbar.addWidget(QLabel("   "))
        self.toolbar.addSeparator()
        self.toolbar.addWidget(QLabel("   "))
        self.action_save = self.new_action(
            "save", _SAVE_CLASS, QKeySequence(Qt.CTRL + Qt.Key_S)
        )
        self.action_save.triggered.connect(self.on_save)
        self.toolbar.addAction(self.action_save)



        self.table = AttendanceTable(self)
        layout.addWidget(self.table)
        self.table.horizontalHeader().setStyleSheet(
            "QHeaderView::section{"
            "background-color:#FFFF80;"
            "padding: 2px;"
            "border: 1px solid #808080;"
            "border-bottom: 2px solid #0000C0;"
            "}"
        )

    def setup(self, klass):
        """Load the attendance data for the given class.
        """
        self.class_label.setText(_CLASS.format(klass=klass))
        self.all_pupils = Pupils()
        self.pupils = self.all_pupils.class_pupils(klass)
        self.hols = readHols()

        row = 0
        trows = []

#TODO: Actually this should be the absence data for each pupil ...
        self.pupilmap = {}
        for pdata in self.pupils:
            pid, pname = pdata["PID"], pdata.name()
            self.pupilmap[pid] = {}
            trows.append(pname)
            row += 1

        self.table.setup(
            colheaders=TCOLS,
            rowheaders=trows,
            undo_redo=True,
            cut=True,
            paste=True,
            on_changed=self.is_modified,
        )

        self.table.resizeColumnsToContents()
# It seems pretty impossible to get the dimensions of the underlying table.
# So maybe the best way to proceed is to remember the window geometry
# from one run to another?

        self.month_select.trigger()

    def switch_month(self, month):
        _month = Month(SCHOOLYEAR, month)
#?
        col_colour = []
        dates = []
        for day in range(1, 32):
            try:
                date = datetime.date(_month.year(), month, day)
                dates.append(date.isoformat())
                if date.weekday() > 4:
                    # Weekend
# What about school Saturdays?
                    col_colour.append(COLOUR_WEEKEND)
                elif date in self.hols:
                    # Holiday weekday
                    col_colour.append(COLOUR_HOLIDAY)
                else:
                    # A normal schoolday
                    col_colour.append(None)
            except ValueError:
                # date out of range – grey out cell.
                col_colour.append(COLOUR_NO_DAY)


#TODO
        self.table.init_sparse_data(len(self.pupilmap), 31, [])
        row = 0
        for pid, pupil_data in self.pupilmap.items():
            col = 0
            for colour in col_colour:
                item = self.table.item(row, col)
                if colour:
                    item.setFlags(item.flags() & ~ Qt.ItemIsEditable)
                    item.setBackground(GraphicsSupport.getBrush(colour))
                else:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    item.setBackground(GraphicsSupport.getBrush())
                    text = pupil_data.get(dates[col])
                    if text:
                        self.table.set_text(row, col, text)
                col += 1
            row += 1

    def on_save(self):
        print("TODO – SAVE")




class AttendancePrinter(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
#        self.grid = GridViewRescaling()
        self.grid = GridViewHFit()
        layout.addWidget(self.grid)

    def setup(self, klass):
        """Load the attendance data for the given class.
        """
        self.all_pupils = Pupils()
        self.pupils = self.all_pupils.class_pupils(klass)
        rows = ROWS0 + ROWn * len(self.pupils)
        self.grid.init(rows, COLS, TITLE_HEIGHT)
        col = COLi0
        for day in range(1, 32):
            self.grid.basic_tile(0, col, text=str(day))
            col += 1
        row = ROWi0
        pupilmap = {}
        for pdata in self.pupils:
            pid, pname = pdata["PID"], pdata.name()
            pupilmap[pid] = row
            self.grid.basic_tile(row, 0, text=pname, halign="l")
            row += 1


        self.grid.add_title("This is the title", halign="l")

#        self.set_current_file(None)
#        self.modified(False)
#        self.action_save_as.setEnabled(False)
        return int(self.grid.grid_width), int(self.grid.grid_height)



# For a large class this will probably lead to a scaling, which might
# be the best way to deal with printing, but possibly not for editing
# on screen – a vertical scrollbar might be useful here, i.e. yet
# another grid variant that only scales on the width ...
# However, then I would lose the title lines. Do I really want to
# implement a fixed header? ... how?!
# An alternative might be a sort of paged table on screen (at least for
# editing, if not also for printing). That could be done using a row of
# toggle buttons to select the page.
# Could it be that a standard table editor would be better suited for
# the screen part? I could still use the above for printing to one page.

#TODO: Use the pupil db to get the pupils, according to class.
# The attendance data could be a mapping for each pupil-id to a mapping
# of date -> info.
    def open_file(self, filepath):
        pupils = (
            ("0006", "Henry King"),
            ("1001", "Catherine d'Aragon"),
            ("1002", "Anne Boleyn"),
        )

        rows = ROWS0
        row0 = len(rows)
        rows += (25,) * len(pupils)
        cols = COLS0
        col0 = len(cols)
        cols += (25,) * 31
        self.grid.init(rows, cols, 25)

        col = col0
        for day in range(1, 32):
            self.grid.basic_tile(0, col, text=str(day))
            col += 1
        row = row0
        pupilmap = {}
        for pupil in pupils:
            pupilmap[pupil[0]] = row
            self.grid.basic_tile(row, 0, text=pupil[1], halign="l")
            row += 1


        self.grid.add_title("This is the title", halign="l")

#        self.set_current_file(None)
#        self.modified(False)
#        self.action_save_as.setEnabled(False)
        return int(self.grid.grid_width), int(self.grid.grid_height)

    def closeEvent(self, event):
        return

        w = APP.focusWidget()
        if w and isinstance(w, QLineEdit) and w.isModified():
            # Editing cell
            if SHOW_CONFIRM(_EDITING_CELL):
                event.accept()
            else:
                event.ignore()
        elif self.__modified:
            if SHOW_CONFIRM(_LOSE_CHANGES):
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def modified(self, mod):
        # print("MOD:", mod)
        self.__modified = mod
        self.action_save.setEnabled(mod)
        self.set_title(mod)

    def set_title(self, changed):
        x = " *" if changed else ""
        title = (
            f"{_PROGRAM_NAME} – {self.filename}{x}" if self.filename \
                    else _PROGRAM_NAME
        )
        self.setWindowTitle(title)

    def set_current_file(self, path):
        self.current_file = path
        self.filename = os.path.basename(path) if path else None

    def get_file(self):
        if self.__modified and not SHOW_CONFIRM(_LOSE_CHANGES_OPEN):
            return
        filetypes = " ".join(["*." + fte for fte in Spreadsheet.filetype_endings()])
        ofile = openDialog(f"{_OPEN_TABLETYPE} ({filetypes})", OPEN_FILE)
        if ofile:
            self.open_file(ofile)

    def _open_file(self, filepath):
        """Read in a DataTable from the given path."""
        try:
            datatable = read_DataTable(filepath)
        except TableError as e:
            SHOW_ERROR(_INVALID_DATATABLE.format(path=str(filepath), message=str(e)))
            return
        except:
            SHOW_ERROR(
                f"BUG while reading {str(filepath)}:\n" f" ... {traceback.format_exc()}"
            )
            return
        self.set_current_file(filepath)
        self.open_table(datatable)
        self.action_save_as.setEnabled(True)
        self.saved = False
        self.modified(False)

    def save_as_file(self):
        endings = make_DataTable_filetypes()
        ftypes = " ".join(["*." + e for e in endings])
        filepath = saveDialog(
            f"{_OPEN_TABLETYPE} ({ftypes})", self.current_file, SAVE_FILE
        )
        if filepath:
            fpath, ending = filepath.rsplit(".", 1)
            if ending in endings:
                data = self.get_data()
                fbytes = make_DataTable(data, ending, __MODIFIED__=Dates.timestamp())
                with open(filepath, "wb") as fh:
                    fh.write(fbytes)
                self.current_file = filepath
                self.reset_modified()
            else:
                SHOW_ERROR(_UNSUPPORTED_SAVE.format(ending=ending))

    def save_file(self):
        fpath, ending = self.current_file.rsplit(".", 1)
        if ending == "tsv":
            filepath = self.current_file
        else:
            if ending in read_DataTable_filetypes():
                filepath = fpath + ".tsv"
            else:
                filepath = self.current_file + ".tsv"
            if not SHOW_CONFIRM(_SAVE_AS_TSV.format(path=filepath)):
                self.save_as_file()
                return
        data = self.get_data()
        tsvbytes = make_DataTable(data, "tsv", __MODIFIED__=Dates.timestamp())
        with open(filepath, "wb") as fh:
            fh.write(tsvbytes)
        self.current_file = filepath
        self.reset_modified()


def readHols():
    """Return a <set> of <datetime.date> instances for all holidays in
    the calendar file for the current year. The dates are initially in
    isoformat (YYYY-MM-DD).
    """
    deltaday = datetime.timedelta(days = 1)
    hols = set()
    for k, v in CALENDAR.items():
        if k[0] == '_':
            if type(v) == str:
                # single date
                hols.add(datetime.date.fromisoformat(v))
            else:
                d1, d2 = map(datetime.date.fromisoformat, v)
                if d1 >= d2:
                    raise AttendanceError(_BAD_RANGE.format(
                            key = k, val = v))
                while True:
                    hols.add(d1)
                    d1 += deltaday
                    if d1 > d2:
                        break
    return hols


#TODO
# Perhaps on failure the choice pop-up (with an appropriate message)
# would be better. Would that be possible?
def validate(value):
    """Validate an entry against the CHOICE_ITEMS list.
    Return <None> if it passes, otherwise an error message.
    """
    if value == "v":
        return "invalid value"
    return None


class Month:
    """Manage information, especially names for the months of the school year.
    The calendar year is adjusted to the month of the school year.
    """
    def __init__(self, schoolyear, num=None):
        self.SCHOOLYEAR_MONTH_1 = int(CONFIG["SCHOOLYEAR_MONTH_1"])
        self.month1 = self.boundmonth(num or self.SCHOOLYEAR_MONTH_1)
        self.schoolyear = schoolyear
        self.month = self.month1

    def month(self):
        """Return the index of the month, in the range 1 to 12.
        """
        return self.month

    def __str__(self):
        return calendar.month_name[self.month]

    def tag(self):
        return calendar.month_abbr[self.month]

    @staticmethod
    def boundmonth(m):
        return ((m-1) % 12) + 1

    def year(self):
        return (int(self.schoolyear) if (self.month < self.SCHOOLYEAR_MONTH_1
                    or self.SCHOOLYEAR_MONTH_1 == 1)
                else (int(self.schoolyear) - 1))

    def increment(self, delta = 1):
        self.month = self.boundmonth(self.month + delta)

    def last_tag(self):
        return calendar.month_abbr[self.boundmonth(self.month1 - 1) - 1]

# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    # Enable package import if running as module
    # print(sys.path)
    this = sys.path[0]
    basedir = os.path.dirname(this)
#    sys.path[0] = appdir
    from core.base import start
#TODO:
#    start.setup(os.path.join(basedir, "TESTDATA"))
    start.setup(os.path.join(basedir, "DATA"))
    print("§§§", CALENDAR)

    for d in sorted(readHols()):
        print (" ---", d.isoformat())

    import calendar
    print(calendar.day_name[1])
    print(calendar.day_abbr[1])
    print(calendar.month_name[1])
    print(calendar.month_abbr[1])

    edit = AttendanceEditor()
    icon = get_icon("attendance")
    edit.setWindowIcon(icon)
    edit.setup("12G")
    edit.show()
    edit.resize(900, 700)
    run(edit)
    quit(0)


# To use as a printer, I don't need the view, just the scene?
    prt = AttendancePrinter()
    icon = get_icon("attendance")
    prt.setWindowIcon(icon)

#    x, y = edit.open_file(None)
    x, y = prt.setup("12G")

# This may well not be the best approach to resizing. By using
# GridViewRescaling it shows the whole table ...
# The trouble with allowing scrollbars is that I haven't built fixed
# headers into the table widget.
    geometry = APP.primaryScreen().availableGeometry()
    max_x = int(geometry.width() * 0.9)
    max_y = int(geometry.height() * 0.9)
    if x + 50 > max_x or y + 50 > max_y:
        prt.resize(max_x, max_y)
    else:
        prt.resize(x + 50, y + 50)
    prt.show()
    prt.resize(int(geometry.width() * 0.7), int(geometry.height() * 0.7))
    run(prt)
    quit(0)


    # print("???", sys.argv)
    if len(sys.argv) == 2:
        edit.open_file(sys.argv[1])


#        if ofile:
#            self.open_file(ofile)

    grid.resize(600, 400)
    grid.show()


    fpath = os.path.join(os.path.expanduser("~"), "test.pdf")
    fpath = DATAPATH("testing/tmp/grid0.pdf")
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    grid.to_pdf(fpath)
    #    grid.to_pdf(fpath, can_rotate = False)



    # Window dimensions
    #    geometry = edit.screen().availableGeometry()
    #    edit.setFixedSize(geometry.width() * 0.7, geometry.height() * 0.7)
    #    #edit.resize(800, 600)
    geometry = APP.primaryScreen().availableGeometry()
    edit.resize(int(geometry.width() * 0.7), int(geometry.height() * 0.7))
    run(edit)

