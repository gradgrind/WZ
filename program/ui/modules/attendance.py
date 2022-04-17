"""
ui/modules/attendance.py

Last updated:  2021-12-21

Manage attendance tables.

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

The data stored in the files conmprises the following elements:
 - the last month of the school-year, YYYY-MM
 - the klass
 - a mapping of table entries: {
        pupil-id: {
            "__NAME__": pupil-name (short form),
            date ("yyyy-mm-dd"): entry,
            ... (further dates)
            "yyyy-mm-A": total number of A-entries (as string),
            "yyyy-mm-V": total number of V-entries (as string)
        },
        ...
    }
"""

_NAME = "Anwesenheit"
_TITLE ="Anwesenheitstabellen verwalten"

### Messages

#_WINDOW_TITLE = "Anwesenheit"
_PRINT_TITLE = "Anwesenheit"
_PROGRAM_NAME = "Anwesenheit"
_CLASS = "Klasse {klass}"
_OPEN_CLASS = "Datei öffnen"
_ATTENDANCE_FILE = "Anwesenheitsdaten"
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

HELP = """# Anwesenheitstabellen für einzelne Klassen pflegen

Eine Klasse hat für jeden Monat im aktuellen Schuljahr eine
Anwesenheitstabelle. Wochenenden werden anhand des Jahres berechnet
und Ferientage werden aus dem Schulkalender (eine Konfigurationsdatei)
geholt. Die Daten können sowohl „intern“ als auch „extern“ (als
xlsx-Datei) gespeichert werden.

Wenn eine externe Tabelle für eine Klasse, die schon interne Daten hat,
geöffnet wird, wird gewarnt, dass die internen Daten (beim Speichern)
überschrieben werden.

Auch Tabellen von nicht aktuellen Schuljahren können geöffnet werden,
aber nur zum Zwecke der Auswertung – sie können nicht wirklich sinnvoll
bearbeitet werden, da die Kalenderdaten fehlen.
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
MCOLn = (50,)
COLS = COLS0 + (25,) * 31
COLi0 = len(COLS0)

TCOLS = [f"{n:02d}" for n in range(1, 32)]

HEADER_BG = "FFFF80"
COLOUR_WEEKEND = "DDDDDD"
COLOUR_HOLIDAY = "00CC00"
COLOUR_NO_DAY = "99FFFF"

_FILE_TYPE = "*.xlsx"

########################################################################

import sys, os, builtins, traceback, datetime, calendar, json, tempfile

from pikepdf import Pdf, Page

if __name__ == "__main__":
    import locale
    print("LOCALE:", locale.setlocale(locale.LC_ALL, ''))
    this = sys.path[0]
    appdir = os.path.dirname(os.path.dirname(this))
    sys.path[0] = appdir
    try:
        builtins.PROGRAM_DATA = os.environ["PROGRAM_DATA"]
    except KeyError:
        basedir = os.path.dirname(appdir)
        builtins.PROGRAM_DATA = os.path.join(basedir, "wz-data")
    from ui.ui_base import StandalonePage as Page
    from core.base import start
#    start.setup(os.path.join(basedir, 'TESTDATA'))
    start.setup(os.path.join(basedir, 'DATA'))
else:
    from ui.ui_base import StackPage as Page

from ui.ui_base import APP, run, openDialog, saveDialog, get_icon, \
        QWidget, QVBoxLayout, QDialog, QPushButton, QButtonGroup, Qt, \
        QToolBar, QAction, QKeySequence, KeySelector, QLabel, QFrame, \
        QComboBox

# This seems to deactivate activate-on-single-click in filedialog
# (presumably elsewhere as well?)
APP.setStyleSheet("QAbstractItemView { activate-on-singleclick: 0; }")

from core.base import Dates
from core.pupils import Pupils

from ui.editable import EdiTableWidget
from ui.grid0 import GridViewRescaling as GridView
#from ui.grid0 import GridViewHFit as GridView
from ui.grid0 import GraphicsSupport

from template_engine.attendance import Table, pupil_list, \
        get_month_data, _ATTENDANCE, attendanceData, \
        attendanceTable, analyse_attendance

class AttendanceError(Exception):
    pass

### -----

def init():
    MAIN_WIDGET.add_tab(AttendanceEditor())



class AttendanceTables(Page):
    """Generate attendance tables for the current school-year.
    Existing tables can also be updated when pupil data changes in the
    pupil database.
    A summary of the data for the whole year can be printed.
    """
    name = _NAME
    title = _TITLE

    def __init__(self):
        super().__init__()
        self.month_data = get_month_data(CALENDAR)

#
    def generate_tables(self, klass):
        outfile = saveDialog(
            f"{_ATTENDANCE_FILE} ({_FILE_TYPE})",
            f"{_ATTENDANCE}_{SCHOOLYEAR}_{klass}.xlsx",
            _SAVE_CLASS
        )
        if outfile:

            pupilnames = pupil_list(Pupils(), klass)
#    pupilnames = [
#        ("001", "Fritz Blume"),
#        ("002", "Melanie Dreher"),
#        ("003", "Amelie Lennart"),
#        ...
#    ]
            table = Table()
            table.make_year(int(SCHOOLYEAR), klass,
                    pupilnames, {}, self.month_data)
#        outfile = DATAPATH(f"testing/tmp/Anwesenheit_{SCHOOLYEAR}_{klass}.xlsx")
            table.save(outfile)





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

# Wouldn't this need to be passed to the AttendanceEditor class?
    def cell_changed(self, r, c):
        if self._active:

            text = self.get_text(r, c)
#TODO
            print("$CHANGED$", r, c, text)
# Convert r, c to pid + date



class AttendanceEditor(Page):
#    def closeEvent(self, event):
#        if self.__modified:
#            if SHOW_CONFIRM(_LOSE_CHANGES):
#                event.accept()
#            else:
#                event.ignore()
#        else:
#            event.accept()

    name = _NAME
    title = _TITLE

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

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.toolbar = QToolBar()
        layout.addWidget(self.toolbar)
        # Class label
#        self.class_label = QLabel()
#?
#        self.class_label.setMinimumWidth(100)
#        self.class_label.setFrameStyle(QFrame.Box | QFrame.Raised)
#        self.class_label.setLineWidth(3)
#        self.class_label.setMidLineWidth(2)
#        self.toolbar.addWidget(self.class_label)

        # Class select
#        self.class_select = QComboBox()
#        self.class_select.currentTextChanged.connect(self.switch_class)
        self.class_select = KeySelector(changed_callback=self.switch_class)
        self.toolbar.addWidget(self.class_select)
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

#        self.dbinfo = DBinfo(data_base or "DATA")

#TODO
        self.set_current_file(None)
        self.modified(False)
        self.action_save_as.setEnabled(False)
#        if ofile:
#            self.open_file(ofile)
        self.schoolyear = SCHOOLYEAR
        classes = Pupils().classes()
        self.class_select.clear()
        print("§§§01")
#        self.class_select.addItems(classes)
        self.class_select.set_items([("", "–––")] + [(c, c) for c in classes])
        print("§§§02")
        self.month_data = get_month_data(CALENDAR)
        self.set_month_select(self.month_data)
        print("§§§03")

    def set_month_select(self, month_data):
        """Initialize the month selector.
        """
        self.month_map = {}
        months = []
        for md in month_data:
            mn = md[0]
            months.append((mn, md[2]))
            self.month_map[mn] = md

# The month should only be selectable when a class has been set, so the
# initialization of the combobox should be done as a result of setting
# a class.

# I am still not quite sure how to handle data from years other than the
# current one ... Perhaps just present a (printable?) summary page?

# When importing a file for the current year, warn that existing data
# may/will be replaced.

        #print("???MONTHS:", months)
        self.month_select.set_items(months)
        # If dealing with the current year, set the month for today
        today = Dates.today()
        print("§§§04")
        if Dates.check_schoolyear(self.schoolyear, today):
            self.month_select.reset(int(today.split('-')[1]))
        print("§§§05")

    def modified(self, mod):
        # print("MOD:", mod)
        self.__modified = mod
        self.action_save.setEnabled(mod)
        self.set_title(mod)

#?
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

# This is not fully thought through!
# It would probably be better to save automatically – say, periodically
# and when a page is changed (or else use a database ...).
# Each cell change can be made to register the change with a backing
# structure so that the displayed table doesn't actually need to be read.
    def read_table(self):
        pdata = []
        r = 0
        for row in self.table.read_all():
            pid, pname = self.pupilnames[r]
            data = {}
            pdata.append((pid, pname, data))
            r += 1
            d = 0
            for col in row:
                d += 1
                if col:
                    data[f] = col
            pass
#TODO
# Just save the dates, not A & V? – after all, these can be recreated.



    def switch_class(self, klass, pupildata=None):
        """Load the attendance data for the given class.
        """
        self.klass = klass
#        self.class_label.setText(_CLASS.format(klass=klass))
        pupils = Pupils().class_pupils(klass)
        row = 0
        self.pupilnames = []
        row_headers = []
        if not pupildata:
            pupildata = attendanceData(klass) or {}
        self.pupilmap = {}
        for pdata in pupils:
            pid, pname = pdata["PID"], pdata.name()
            self.pupilmap[pid] = pupildata.get(pid) or {}
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
# It seems pretty impossible to get the screen dimensions of the
# underlying table. So maybe the best way to proceed is to remember the
# window geometry from one run to another?
        self.month_select.trigger()
        self.action_save_as.setEnabled(True)
        return True

    def switch_month(self, month):
# Save old data? Not if doing updates on backing data?
        print(f"MONTH: {month:02}")
        for md in self.month_data:
            if md[0] == month:
                col_colour, dates = md[3:5]
                break
        else:
            raise Bug
        self.table._active = False
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
        self.table._active = True
        return True

#deprecated ...
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
        ofile = openDialog(f"{_ATTENDANCE_FILE} ({_FILE_TYPE})", _OPEN_CLASS)
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


############# old

    def _save_as_file(self):
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

    def _save_file(self):
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


_SUMMARY_TITLE = "Abwesenheiten und Verspätungen"
class AttendanceSummary(GridView):
    def __init__(self, infile):
        super().__init__()
        last_year_month, klass, pupildata = attendanceTable(infile)
        year_months, pupil_A, pupil_V = analyse_attendance(
                last_year_month, pupildata)
        months = [calendar.month_abbr[int(ym.split("-")[1])]
                for ym in year_months]

        headers = [""] * len(COLS0) + months + ["", "A", "V"]
        cols = COLS0 + MCOLn * len(months) + COLS0[-1:] + MCOLn * 2
        rows = ROWS0 + ROWn * len(pupildata)
        self.init(rows, cols, TITLE_HEIGHT)

        title_l = self.add_title(f"Klasse {klass}", halign="l")
        title = self.add_title(_SUMMARY_TITLE)
        year, mn = last_year_month.split("-")
        if mn != "12":
            lyear = str(int(year) - 1)
            year = CONFIG["PRINT_SCHOOLYEAR"].format(year1=lyear, year2=year)
        self.date = self.add_title(f"Schuljahr {year}", halign="r")

        i = 0
        for h in headers:
            if h:
                self.basic_tile(0, i, text=h, halign="c")
            i += 1

        i = 0
        row = ROWi0
        for pid, pdata in pupildata.items():
            pname = pdata["__NAME__"]
            self.basic_tile(row, 0, text=pname, halign="l")
            col = COLi0
#            print("+A+", pname, pupil_A[i])
#            print("+V+", pname, pupil_V[i])


            i += 1
            row += 1


def test_summary(infile):
    dlg = QDialog()
    layout = QVBoxLayout(dlg)
    grid = AttendanceSummary(infile)
    layout.addWidget(grid)
    dlg.exec()


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


#TODO
class DBinfo:
    """Refer to the WZ database to update calendar and pupil information,
    if possible.
    """
    def __init__(self, data_base):
        try:
            from core.base import start
        except:
            builtins.CALENDAR = None
            self.hols = None
            self.pupils = None
            return
        start.setup(os.path.join(basedir, data_base))
        self.hols = readHols(CALENDAR)
        try:
            from core.pupils import Pupils
            self.pupils = Pupils()
        except ImportError:
            self.pupils = None

    def get_classes(self):
        if self.pupils:
            return self.pupils.classes()
        return []


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

    ofile = None
    if len(sys.argv) == 2:
        _ofile = sys.argv[1]
        if os.path.isfile(_ofile) and _ofile.endswith(_FILE_TYPE):
            ofile = _ofile

    test_summary(DATAPATH(f"testing/{_ATTENDANCE}_test.xlsx"))

    MAIN_WIDGET = AttendanceEditor()
    MAIN_WIDGET.show()
    MAIN_WIDGET.resize(900, 700)
    run(MAIN_WIDGET)
    quit(0)




#    dbinfo = DBinfo("TESTDATA")
#    dbinfo = DBinfo()

#    from core.base import start
#TODO:
#    start.setup(os.path.join(basedir, "TESTDATA"))
#    start.setup(os.path.join(basedir, "DATA"))
#    print("§§§", CALENDAR)

    holidays = readHols(CALENDAR)
#    holidays = dbinfo.get_hols()
#    if holidays:
#        for d in sorted(holidays):
#            print (" ---", d, holidays[d])

#    print(calendar.day_name[1])
#    print(calendar.day_abbr[1])
#    print(calendar.month_name[1])
#    print(calendar.month_abbr[1])

#    edit = AttendanceEditor("TESTDATA")
    edit = AttendanceEditor()

    icon = get_icon("attendance")
    edit.setWindowIcon(icon)

#TODO ...
    edit.schoolyear = SCHOOLYEAR
    edit.set_month_select(CONFIG["SCHOOLYEAR_MONTH_1"], holidays)

#TODO: How to start with an empty table and no class?

    if ofile:
        pass

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

