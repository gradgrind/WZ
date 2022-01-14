"""
ui/grade_grid.py

Last updated:  2022-01-14

Manage the grid for the grade-editor.


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

### Display texts
_GRUPPE = "Gruppe {group}"
_TERM = "{year}: {term}"
_ISSUE = "Ausgabedatum: {date}"

_PID = "Id"
_PNAME = "Schüler(in)"
_PGROUPS = "Gruppen"

## Measurements are in points ##
_SEP_SIZE = 3
_WIDTH_AVERAGE = 36
_HEIGHT_LINE = 18
_WIDTH_GRADE = 24
COLUMNS = (45, 105, 45, _SEP_SIZE) # + ...

ROWS = (
# header (tags)
    18, 100, _SEP_SIZE
) # + 18 * n

###############################################################

import sys, os

if __name__ == "__main__":
    import locale
    print("LOCALE:", locale.setlocale(locale.LC_ALL, ""))
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    start.setup(os.path.join(basedir, "TESTDATA"))
#    start.setup(os.path.join(basedir, 'DATA'))

### +++++

from typing import Dict, List, Optional, Any, Set, Tuple, Sequence

import os

from ui.grid0 import GridViewRescaling
from grades.gradetable import readGradeFile, GradeTable, PupilGradeData, \
        get_group_info
from local.local_grades import XCOL_WIDTH
from core.base import Dates

### -----

class GradeGrid(GridViewRescaling):
    """Present the grades for a group and term, allowing editing of the
    individual fields and completion of the extra fields steering
    report generation.
    A print version of the table can be prepared.
    """
    def set_table(self, gradetable:GradeTable) -> None:
        """<gradetable> contains all the basic grade information for the
        group.
        """
        self.gradetable:GradeTable = gradetable
        # Get number of rows and columns
        row_pids:int = len(ROWS)
        _ROWS: Sequence[int] = ROWS + \
                (_HEIGHT_LINE,) * len(gradetable.pupils_grade_data)
        # Divide the column data into categories
        print("SUBJECT:", gradetable.class_subjects)
        subjects: List[Tuple[str,str]] = []
        composites: List[Tuple[str,str]] = []
        sid:str
        sname:str
        for sid, sname in gradetable.class_subjects:
            if sid[0] == "$":
                composites.append((sid, sname))
            else:
                subjects.append((sid, sname))
        col_sids:int = len(COLUMNS)
        _COLS: Sequence[int] = COLUMNS + (_WIDTH_GRADE,) * len(subjects)
# Components could be coloured (on a per pupil basis)?
        col_composites: int = len(_COLS) + 1


        self.composite_set: Set[str] = set()
        self.calc_set: Set[str] = set()
        pgdata:PupilGradeData
        for pgdata in _cgtable.pupils_grade_data:
            for sid in pgdata.composites:
                self.composite_set.add(sid)
            for sid in pgdata.calcs:
                self.calc_set.add(sid)

        print("???1", self.composite_set)
        print("???2", self.calc_set)
        print("???3", composites)



# composites from the parsed data? ...

        if composites:
            _COLS += (_SEP_SIZE,) + (_WIDTH_GRADE,) * len(composites)
        col_calcs:int = len(_COLS) + 1
        if self.calc_set:
            _COLS += (_SEP_SIZE,) + (_WIDTH_AVERAGE,) * len(self.calc_set)

        # Additional fields in the grade table
        group_info = MINION(DATAPATH("CONFIG/GRADE_GROUP_INFO"))
        xfields = get_group_info(group_info, group=gradetable.group,
                key="GradeFields_X")
        col_extras:int = len(_COLS) + 1
        if xfields:
            _COLS += (_SEP_SIZE,)
            for x in xfields:
                _COLS += (XCOL_WIDTH[x[0]],)

        self.init(_ROWS, _COLS, titleheight=20)

        # Use the title line for the "INFO"
        self.add_title(_ISSUE.format(
                date=Dates.print_date(gradetable.issue_date)), halign="r")
        self.add_title(_GRUPPE.format(group=gradetable.group), halign="c")
        self.add_title(_TERM.format(year=CALENDAR["~SCHOOLYEAR_PRINT"],
                term=gradetable.term), halign="l")

#TODO: Do I really need the columns for sid & pid?
# Especially pid is questionable.
        # Add the column headers
        self.basic_tile(0, 0, text=_PID)
        self.basic_tile(0, 1, text=_PNAME)
        self.basic_tile(0, 2, text=_PGROUPS)

        # Build a mapping from sid to column
        self.sid2col: Dict[str,int] = {}
        # Basic subjects
        col = col_sids
        for sid, sname in subjects:
            self.sid2col[sid] = col
            self.basic_tile(0, col, text=sid)
            self.basic_tile(1, col, text=sname, rotate=True, valign="b")
            col += 1
        # Composite subjects
        col = col_composites
        for sid, sname in composites:
            if sid in self.composite_set:
                self.sid2col[sid] = col
                self.basic_tile(0, col, text=sid)
                self.basic_tile(1, col, text=sname, rotate=True, valign="b")
                col += 1
        # Calculated values
        col = col_calcs
        calcfields = get_group_info(group_info, group=gradetable.group,
                key="Calc")
        if calcfields:
            for x in calcfields:
                sid = x[0]
                self.sid2col[sid] = col
                self.basic_tile(0, col, text=sid)
                self.basic_tile(1, col, text=x[1], rotate=True, valign="b")
                col += 1
        # Additional (evaluation?) fields
        col = col_extras
        if xfields:
            for x in xfields:
                sid = x[0]
                self.sid2col[sid] = col
                self.basic_tile(0, col, text=sid)
                self.basic_tile(1, col, text=x[1], rotate=True, valign="b")
                col += 1

        # The pupil lines
        self.pid2row:Dict[str,int] = {}
        row:int = row_pids
        pgdata: PupilGradeData
        for pgdata in gradetable.pupils_grade_data:
            self.pid2row[pgdata.pid] = row
            self.basic_tile(row, 0, text=pgdata.pid)
            self.basic_tile(row, 1, text=pgdata.name, halign="l")
            self.basic_tile(row, 2, text=" ".join(pgdata.groups))
            pgdata.calculate()
            for sid, col in self.sid2col.items():
                g = pgdata.grades.get(sid) or ""
                self.basic_tile(row, col, text=g)
            row += 1



    def tile_left_clicked(self, tile):
#TODO: Handle cell editors
        print("POP UP EDITOR?:", tile.tag or "–––")
        return True

#    def tile_right_clicked(self, tile):
#        print("CONTEXT MENU:", tile.tag or "–––")
#        return True


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication([])

    #_GRADE_DATA = MINION(DATAPATH("CONFIG/GRADE_DATA"))
    _group = "12G.R"
    _filepath = DATAPATH(f"testing/Noten/NOTEN_1/Noten_{_group}_1")
    _gdata = readGradeFile(_filepath)
    _cgtable = GradeTable(_gdata)

    gridview = GradeGrid()
    gridview.set_table(_cgtable)
    gridview.resize(800, 600)
    gridview.show()
    app.exec()
