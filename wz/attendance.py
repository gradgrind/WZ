# -*- coding: utf-8 -*-
"""
attendance.py

Last updated:  2021-12-04

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

For the current school year (as determined by the <SCHOOLYEAR> global –
a "builtin", initialized in core/base.py) the pupil data is extracted
from the pupil database. Thus, when a file is loaded, any changes in
the pupil database will be reflected in the attendance table.

It is also possible to start without a data file, but only for dates
within the current school year. This is necessary when beginning the
attendance table for a class.

The data files can also be used outside of their school year, but then
no changing of the basic paramaters is (easily) possible. To enable this
feature, the pupil list and calendar data must be saved in the data file.
"""

#TODO: Add facility to edit pupil list and calendar independently of
# the database? It might be confusing ...
# When started without a file, it should be possible to select a class
# from the WZ database. Only the current year is supported in this case(?).
# If no database is available, a file dialog can be presented, quitting
# if no file is selected – maybe with a message.
# It would also be possible to  open a file from the toolbar.
# When started with a file argument, this should be opened. If there is
# data for this year & class available (in the WZ database) that should
# be taken as the basis, the absence info from the file then being
# added to it.


TITLE_HEIGHT = 25
ROWS0 = (22, 3)
ROWi0 = len(ROWS0)
ROWn = (22,)
COLS0 = (150, 3)
COLS = COLS0 + (25,) * 31
COLi0 = len(COLS0)

TCOLS = [f"{n:02d}" for n in range(1, 32)]

HEADER_BG = "FFFF80"
COLOUR_WEEKEND = "DDDDDD"
COLOUR_HOLIDAY = "00CC00"
COLOUR_NO_DAY = "99FFFF"

_FILE_TYPE = "*.attendance"

### Messages

#_WINDOW_TITLE = "Abwesenheit"
_PRINT_TITLE = "Abwesenheiten"
_PROGRAM_NAME = "Abwesenheiten"
_CLASS = "Klasse {klass}"
_OPEN_CLASS = "Datei öffnen"
_ATTENDANCE_FILE = "Abwesenheitsdaten"
_SAVE_CLASS = "Datei speichern"
_SAVE_CLASS_AS = "Datei speichern unter"
_PAGE = "Seite:"
_PDF = "als PDF exportieren"
_PDF_FILE = "PDF-Datei"
_PDF_FILE_NAME = "Anwesenheit_{year}_{klass}.pdf"

_BAD_DATE = "Ungültiges Datum: {key}: {val}"
_BAD_RANGE = "Ungültiges Datumsbereich: {key}: {val}"
_DATE_NOT_IN_YEAR = "Datum liegt nicht im aktuellen Schuljahr: {key}: {val}"
_FILE_MISSING_FIELD = "Ungültige Datei: Feld '{field}' fehlt in \n {path}"
_FILE_TYPE_ERROR = "Ungültiger Dateityp: {path}"
#?
#_OPEN_TABLETYPE = "Tabellendatei"
#_INVALID_DATATABLE = "Ungültige DataTable: {path}\n ... {message}"

#_SAVE_AS_TSV = "Als tsv-Datei speichern?\n\n{path}"
#_UNSUPPORTED_SAVE = "Tabelle speichern – Dateityp '.{ending}'" " wird nicht unterstützt"

_LOSE_CHANGES = "Es gibt ungespeicherte Änderungen.\n" "Wirklich schließen?"
_LOSE_CHANGES_OPEN = (
    "Es gibt ungespeicherte Änderungen, die dann verloren werden.\n"
    "Neue Datei trotzdem öffnen?"
)
#_SAVING_FORMAT = (
#    "Formatierungen werden möglicherweise verloren gehen:" "\n{path}\nÜberschreiben?"
#)


########################################################################

import sys, os, builtins, traceback, datetime, calendar, json, tempfile

from pikepdf import Pdf, Page

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

from ui.editable import EdiTableWidget
from ui.grid0 import GridViewRescaling as GridView
#from ui.grid0 import GridViewHFit as GridView
from ui.grid0 import GraphicsSupport

class AttendanceError(Exception):
    pass

### -----

#TODO: Summary page and Notices page

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
    def closeEvent(self, event):
        if self.__modified:
            if SHOW_CONFIRM(_LOSE_CHANGES):
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def is_modified(self):
        return self.__modified

    def new_action(self, icon, text, shortcut):
        action = QAction(self)
        if shortcut:
            text += f" – [{shortcut.toString()}]"
            action.setShortcut(shortcut)
        action.setText(text)
        action.setIcon(get_icon(icon))
        return action

    def __init__(self, ofile=None):
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
        self.month_select = KeySelector(changed_callback=self.switch_month)
        self.toolbar.addWidget(QLabel(_PAGE))
        self.toolbar.addWidget(self.month_select)
        # File actions
        self.toolbar.addWidget(QLabel("   "))
        self.toolbar.addSeparator()
        self.toolbar.addWidget(QLabel("   "))
        self.action_open = self.new_action(
            "open", _OPEN_CLASS, QKeySequence(Qt.CTRL + Qt.Key_O)
        )
        self.action_open.triggered.connect(self.get_file)
        self.toolbar.addAction(self.action_open)
        self.action_save = self.new_action(
            "save", _SAVE_CLASS, QKeySequence(Qt.CTRL + Qt.Key_S)
        )
        self.action_save.triggered.connect(self.on_save)
        self.toolbar.addAction(self.action_save)
        self.action_save_as = self.new_action(
            "saveas", _SAVE_CLASS_AS,
            QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_S)
        )
        self.action_save_as.triggered.connect(self.on_save_as)
        self.toolbar.addAction(self.action_save_as)
        # Printing
        self.action_print = self.new_action(
            "printpdf", _PDF,
            QKeySequence(Qt.CTRL + Qt.Key_P)
        )
        self.action_print.triggered.connect(self.on_print)
        self.toolbar.addAction(self.action_print)

        # The table
        self.table = AttendanceTable(self, align_centre=True)
        layout.addWidget(self.table)
        horizontalHeader = self.table.horizontalHeader()
        horizontalHeader.setMinimumSectionSize(-1)
        horizontalHeader.setStyleSheet(
            "QHeaderView::section{"
            f"background-color:#{HEADER_BG};"
            "padding: 3px;"
            "border: 1px solid #808080;"
            "border-bottom: 2px solid #0000C0;"
            "}"
        )
        #verticalHeader = self.table.verticalHeader()
        #verticalHeader.setMinimumSectionSize(150)

#TODO
        self.set_current_file(None)
        self.modified(False)
        self.action_save_as.setEnabled(False)
        if ofile:
            self.open_file(ofile)

    def set_month_select(self, month1, hols):
        """Initialize the calendar data for the current (<self.schoolyear>)
        year. <month1> is the first month of the school-year (range 1-12).
        """
        self.month1 = f"{int(month1):02}"
        months = []
        self.month_colours = {}
        month = self.month1
        while True:
            year = month2year(self.schoolyear, self.month1, month)
            col_colour = []
            dates = []
            for day in range(1, 32):
                try:
                    date = f"{year}-{month}-{day:02}"
                    dates.append(date)
                    if datetime.date.fromisoformat(date).weekday() > 4:
                        # Weekend
#TODO: What about school Saturdays?
                        col_colour.append(COLOUR_WEEKEND)
                    elif date in hols:
                        # Holiday weekday
                        col_colour.append(COLOUR_HOLIDAY)
                    else:
                        # A normal schoolday
                        col_colour.append(None)
                except ValueError:
                    # date out of range – grey out cell.
                    dates.append(None)
                    col_colour.append(COLOUR_NO_DAY)
            m = int(month)
            months.append((month, calendar.month_name[m]))
            self.month_colours[month] = (
                col_colour,
                dates
            )
            month = f"{(m % 12) + 1:02}"
            if month == self.month1:
                break
        self.month_select.set_items(months)
        # If dealing with the current year, set the month for today
        today = Dates.today()
        if Dates.check_schoolyear(self.schoolyear, today):
            self.month_select.reset(today.split('-')[1])


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
        ofile = openDialog(f"{_ATTENDANCE_FILE} ({_FILE_TYPE})", _OPEN_CLASS)
        if ofile:
            self.open_file(ofile)






    def setup(self, klass):
        """Load the attendance data for the given class.
        """
        self.klass = klass
        self.class_label.setText(_CLASS.format(klass=klass))
        self.all_pupils = Pupils()
        self.pupils = self.all_pupils.class_pupils(klass)

        row = 0
        self.pupilnames = []
        row_headers = []

#TODO: Actually this should be the absence data for each pupil ...
        self.pupilmap = {}
        for pdata in self.pupils:
            pid, pname = pdata["PID"], pdata.name()
            self.pupilmap[pid] = {}
            self.pupilnames.append((pid, pname))
            row_headers.append(pname)
            row += 1

        self.table.setup(
            colheaders=TCOLS,
            rowheaders=row_headers,
            undo_redo=True,
            cut=True,
            paste=True,
            on_changed=self.modified,
        )

        self.table.resizeColumnsToContents()
# It seems pretty impossible to get the dimensions of the underlying table.
# So maybe the best way to proceed is to remember the window geometry
# from one run to another?

        self.month_select.trigger()
        self.action_save_as.setEnabled(True)

    def switch_month(self, month):
        col_colour, dates = self.month_colours[month]

#TODO?
        self.table.init_sparse_data(len(self.pupilmap), 31, [])
        row = 0
        for pid, pupil_data in self.pupilmap.items():
            col = 0
            for colour in col_colour:
#TODO: Move some of the details to editable.py?
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
        return True



    def save_file(self, filepath):
        """Save the holiday data, the pupil list and the attendance data
        to an "attendance" file, using json.
        """
        data = {
            "TYPE": "ATTENDANCE",
            "SCHOOLYEAR": self.schoolyear,
            "MONTH1": self.month1,
            "CLASS": self.klass,
            "HOLIDAYS": self.hols,
            "PUPILS": self.pupilnames,
            "DATA": self.pupilmap
        }
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(data, fh)





    def open_file(self, filepath):
        """Read in the attendance table (json) for a class from the
        given path.
        """
        def read_field(field):
            try:
                return data[field]
            except ValueError:
                raise AttendanceError(_FILE_MISSING_FIELD.format(
                        field=field, path=filepath))

        with open(filepath, 'rb') as fh:
            data = json.load(fh)
        if read_field("TYPE") != "ATTENDANCE":
            raise AttendanceError(_FILE_TYPE_ERROR.format(
                    path=filepath))
        self.schoolyear = read_field("SCHOOLYEAR")
        self.klass = read_field("CLASS")
        self.hols = read_field("HOLIDAYS")
        self.pupilnames = read_field("PUPILS")
        self.pupilmap = read_field("DATA")

        print("TODO – OPEN")
        return

        if self.schoolyear == SCHOOLYEAR:
            self.update()

#?
        self.set_current_file(filepath)
        self.open_table(datatable)
        self.action_save_as.setEnabled(True)
        self.saved = False
        self.modified(False)

    def on_open(self):
        if self.__modified and not SHOW_CONFIRM(_LOSE_CHANGES_OPEN):
            return
        ofile = openDialog(f"{_ATTENDANCE_FILE} (*.attendance)", _OPEN_CLASS)
        if ofile:
            self.open_file(ofile)

    def on_save(self):
        print("TODO – SAVE")

    def on_save_as(self):
        print("TODO – SAVE AS")

    def on_print(self):
        dialog = AttendancePrinter(
            self.schoolyear,
            self.month1,
            self.klass,
            self.pupilnames,
            self.pupilmap,
            self.month_colours
        )
        dialog.exec()


class AttendancePrinter(QDialog):
    def __init__(self, schoolyear, month1, klass,
            pupilnames, pupilmap, month_colours):
        self.schoolyear = schoolyear
        self.month1 = month1
        self.klass = klass
        super().__init__()
        layout = QVBoxLayout(self)
        self.pupilmap = pupilmap
        self.month_colours = month_colours
        self.grid = GridView()
        layout.addWidget(self.grid)

#???
        rows = ROWS0 + ROWn * len(pupilnames)
        self.grid.init(rows, COLS, TITLE_HEIGHT)
        col = COLi0
        for day in TCOLS:
            self.grid.basic_tile(0, col, text=day)
            col += 1
        row = ROWi0
        self.cells = []
        for pid, pname in pupilnames:
            rowcells = []
            self.cells.append(rowcells)
            self.grid.basic_tile(row, 0, text=pname, halign="l")
            col = COLi0
            for day in TCOLS:
                rowcells.append(self.grid.basic_tile(row, col))
                col += 1
            row += 1
        title_l = self.grid.add_title(f"Klasse {klass}", halign="l")
        title = self.grid.add_title(_PRINT_TITLE)
        self.date = self.grid.add_title("MONTH YEAR", halign="r")

#TODO ... ?
        self.pdfout()


    def set_month(self, month):
        col_colour, dates = self.month_colours[month]
        self.date.setText(f"{calendar.month_name[int(month)]}"
                f" {month2year(self.schoolyear, self.month1, month)}")
        # Build data array (of row-arrays)
        r = 0
        for pmap in self.pupilmap.values():
            rowcells = self.cells[r]
            for c in range(31):
                date = dates[c]
                colour = col_colour[c]
                if colour:
                    text = ""
                else:
                    text = pmap.get(date) or ""
                cell = rowcells[c]
                cell.setText(text)
                cell.set_background(colour)
            r += 1

    def pdfout(self):
        month = self.month1
        files = []
        with tempfile.TemporaryDirectory() as outdir:
            for i in range(12):
                self.set_month(month)
                fpath = os.path.join(outdir, f"file_{i:02}.pdf")
                self.grid.to_pdf(fpath, landscape=True, can_rotate=False)
                files.append(fpath)
                month = f"{(int(month) % 12) + 1:02}"
            filepath = saveDialog(
                f"{_PDF_FILE} (*.pdf)",
                _PDF_FILE_NAME.format(year=SCHOOLYEAR, klass=self.klass)
            )
            if filepath:
                if not filepath.endswith(".pdf"):
                    filepath += ".pdf"
                merge_pdf(files, filepath)


class _AttendancePrinter(QDialog):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.grid = GridViewRescaling()
#        self.grid = GridViewHFit()
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
            SHOW_ERROR(_INVALID_DATATABLE.format(path=str(filepath),
                    message=str(e)))
            return
        except:
            SHOW_ERROR(
                f"BUG while reading {str(filepath)}:\n" \
                        f" ... {traceback.format_exc()}"
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
            f"{_OPEN_TABLETYPE} ({ftypes})",
            self.current_file,
            SAVE_FILE
        )
        if filepath:
            fpath, ending = filepath.rsplit(".", 1)
            if ending in endings:
                data = self.get_data()
                fbytes = make_DataTable(
                    data,
                    ending,
                    __MODIFIED__=Dates.timestamp()
                )
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


def readHols(calendar):
    """Return a set of dates for all holidays in the calendar file for
    the current year. The dates are in isoformat (YYYY-MM-DD).
    Also weekends are marked.
    The information is returned as a mapping {date: tag}
    """
    schoolyear = Dates.calendar_year(calendar)
    deltaday = datetime.timedelta(days = 1)
    hols = {}
    for k, v in calendar.items():
        if k[0] == '_':
            if type(v) == str:
                # single date
                try:
                    d = datetime.date.fromisoformat(v)
                except ValueError:
                    raise AttendanceError(_BAD_DATE.format(
                            key=k, val=v))
                if not Dates.check_schoolyear(schoolyear, d=v):
                    raise AttendanceError(_DATE_NOT_IN_YEAR.format(
                            key=k, val=v))
                hols[v] = k
            else:
                d1, d2 = map(datetime.date.fromisoformat, v)
                if d1 >= d2:
                    raise AttendanceError(_BAD_RANGE.format(
                            key=k, val=v))
                while True:
                    hols[d1.isoformat()] = k
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
        self.month0 = self.boundmonth(num or self.SCHOOLYEAR_MONTH_1)
        self.schoolyear = schoolyear
        self.month = self.month0

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
        return calendar.month_abbr[self.boundmonth(self.month0 - 1) - 1]

    def column_colours(self, hols):
        col_colour = []
        dates = []
        year = self.year()
        for day in range(1, 32):
            try:
                date = f"{year}-{self.month:02}-{day:02}"
                dates.append(date)
                if datetime.date.fromisoformat(date).weekday() > 4:
                    # Weekend
# What about school Saturdays?
                    col_colour.append(COLOUR_WEEKEND)
                elif date in hols:
                    # Holiday weekday
                    col_colour.append(COLOUR_HOLIDAY)
                else:
                    # A normal schoolday
                    col_colour.append(None)
            except ValueError:
                # date out of range – grey out cell.
                dates.append(None)
                col_colour.append(COLOUR_NO_DAY)
        return col_colour, dates

def Update():
    """Refer to the WZ database to update calendar and pupil information,
    if possible.
    """
    pass


def merge_pdf(ifile_list, filepath, pad2sided = False):
    """Join the pdf-files in the input list <ifile_list> to produce a
    single pdf-file, saved at <filepath>.
    The parameter <pad2sided> allows blank pages to be added
    when input files have an odd number of pages – to ensure that
    double-sided printing works properly.
    """
    pdf = Pdf.new()
    for ifile in ifile_list:
        src = Pdf.open(ifile)
        pdf.pages.extend(src.pages)
        if pad2sided and (len(src.pages) & 1):
            page = Page(src.pages[0])
            w = page.trimbox[2]
            h = page.trimbox[3]
            pdf.add_blank_page(page_size = (w, h))
    pdf.save(filepath)


def month2year(schoolyear, month1, month):
    """Return the year of month <month>. <month1> is the first month in
    the school-year. All values are strings, months always have two digits.
    """
    return schoolyear if (month < month1 or month1 == "01") \
            else f"{int(schoolyear) - 1:02}"


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

    holidays = readHols(CALENDAR)
    for d in sorted(holidays):
        print (" ---", d, holidays[d])

    print(calendar.day_name[1])
    print(calendar.day_abbr[1])
    print(calendar.month_name[1])
    print(calendar.month_abbr[1])

    edit = AttendanceEditor()
    icon = get_icon("attendance")
    edit.setWindowIcon(icon)

    edit.schoolyear = SCHOOLYEAR
    edit.set_month_select(CONFIG["SCHOOLYEAR_MONTH_1"], holidays)

#TODO: How to start with an empty table and no class?

    from core.pupils import Pupils
    edit.setup("11G")
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

