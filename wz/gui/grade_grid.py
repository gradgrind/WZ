# -*- coding: utf-8 -*-
"""
gui/grade_grid.py

Last updated:  2020-12-05

Manage the grid for the grade-editor.


=+LICENCE=============================
Copyright 2020 Michael Towers

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

### Messages


### Display texts
_PUPIL = "Schüler"
_STREAM = "Maßstab"

#####################################################

# To test this module, use it via grade_editor.py

from gui.grid import Grid, CellStyle, PopupDate, PopupTable

from grades.gradetable import GradeTable, Grades, Frac
from local.base_config import FONT, SCHOOL_NAME
from local.grade_config import UNCHOSEN

## Measurements are in mm ##
COLUMNS = (35, 15, 15, 2) # + 8 * n ... further separators?
# The info values could need more space than just the 3rd column ...

# Specify widths of special columns explicitly:
COL_WIDTH = {
    ':D': 10,
    ':Dx': 10,
    '*ZA': 30,
    '*Q': 8,
    '*F_D': 20,
}

ROWS = (
#title
    12,
# info rows
    6, 6, 6, 6, 6, 6,
# header (tags)
    6, 2
) # + 6 * n

###

class GradeGrid(Grid):
#
    def styles(self):
        """Set up the styles used in the table view.
        """
        self.new_style('base', font = FONT, size = 11)
        self.new_style('name', base = 'base', align = 'l')
        self.new_style('title', font = FONT, size = 12, align = 'l',
                    border = 0, highlight = 'b')
        self.new_style('info', base = 'base', border = 0, align = 'l')
        self.new_style('underline', base = 'base', border = 2)
        self.new_style('titleR', base = 'title', align = 'r')
        self.new_style('small', base = 'base', size = 10)
        self.new_style('v', base = 'small', align = 'b')
        self.new_style('h', base = 'small', border = 0)
        self.new_style('entry', base = 'base', highlight = ':2a6099',
                mark = 'E00000')
        self.new_style('info_edit', base = 'info', align = 'l',
                highlight = ':2a6099', mark = 'E00000')
        self.new_style('padding', bg = '666666')
#
    def set_table(self, schoolyear, group, term):
        """Set the grade table (a <GradeTable> instance) to be used.
        Set up the grid accordingly.
        """
        self.cell_callback = 'TODO'

        self.grade_table = GradeTable.group_table(schoolyear, group, term,
                ok_new = True)

#        print("$$$ pupils:", len(self.grade_table))
#        print("$$$ subjects:", self.grade_table.subjects) # real subjects

        # Get number of rows and columns from <grade_table>
        row_pids = len(ROWS)
        _ROWS = ROWS + (6,) * len(self.grade_table)
        col_sids = len(COLUMNS)
        _nsids = len(self.grade_table.subjects)
        _ncomps = len(self.grade_table.composites)
        _COLS = COLUMNS + (8,) * _nsids
        col_composites = len(_COLS) + 1
        if _ncomps:
            _COLS += (2,) + (8,) * _ncomps
        col_averages = len(_COLS) + 1
# The averages are only used in the grade editor ...
        self.averages = Grades.averages(group)
        if self.averages:
            _COLS += (2,)
            for x in self.averages:
                _COLS += (COL_WIDTH[x],)
        col_extras = len(_COLS) + 1
        if self.grade_table.extras:
            _COLS += (2,)
            for x in self.grade_table.extras:
                _COLS += (COL_WIDTH[x],)

        self.setTable(_ROWS, _COLS)
        self.styles()

        self.tile(row_pids - 1, 0, cspan = len(_COLS), style = 'padding')
        for col in col_sids, col_composites, col_averages, col_extras:
            self.tile(1, col - 1, rspan = len(_ROWS) - 1, style = 'padding')

        ### Cell editors
        # These are attached to the scene, so a new table (which starts
        # a new scene) begins with no cell editors.
        edit_grade = PopupTable(self, Grades.group_info(group, 'NotenWerte'))
        edit_date = PopupDate(self)
#TODO: add editors for extra fields

        ### Title area
        self.tile(0, 0, text = "Notentabelle", cspan = 2, style = 'title')
        self.tile(0, 4, text = SCHOOL_NAME, cspan = 10, style = 'titleR')
        ### General Info
        self.tile(1, 0, text = self.grade_table.SCHOOLYEAR, style = 'info')
        self.tile(1, 1, text = self.grade_table.schoolyear,
                cspan = 2, style = 'info')
        self.tile(2, 0, text = self.grade_table.GROUP, style = 'info')
        self.tile(2, 1, text = self.grade_table.group,
                cspan = 2, style = 'info')
        self.tile(3, 0, text = self.grade_table.TERM, style = 'info')
        self.tile(3, 1, text = Grades.term2text(self.grade_table.term),
                cspan = 2, style = 'info')
        # These are editable dates:
        self.tile(4, 0, text = self.grade_table.ISSUE_D, style = 'info')
        self.tile(4, 1, text = self.grade_table.issue_d,
                cspan = 2, style = 'info_edit',
                validation = edit_date, tag = 'ISSUE_D')
        self.tile(5, 0, text = self.grade_table.GRADES_D, style = 'info')
        self.tile(5, 1, text = self.grade_table.grades_d,
                cspan = 2, style = 'info_edit',
                validation = edit_date, tag = 'GRADES_D')

        # Subject lines
        self.tile(7, 0, text = _PUPIL, cspan = 2, style = 'small')
        self.tile(7, 2, text = _STREAM,  style = 'small')
        col = col_sids
        for sid, name in self.grade_table.subjects.items():
            self.tile(7, col, text = sid, style = 'small')
            self.tile(1, col, text = name, rspan = 6, style = 'v')
            col += 1

        col = col_composites
        for sid, name in self.grade_table.composites.items():
            self.tile(7, col, text = sid, style = 'small')
            self.tile(1, col, text = name, rspan = 6, style = 'v')
            col += 1

        col = col_averages
        for sid, name in self.averages.items():
            self.tile(7, col, text = sid, style = 'small')
            self.tile(1, col, text = name, rspan = 6, style = 'v')
            col += 1

        col = col_extras
        for sid, name in self.grade_table.extras.items():
            self.tile(7, col, text = sid, style = 'small')
            self.tile(1, col, text = name, rspan = 6, style = 'v')
            col += 1

#TODO: pupil lines
        row = row_pids
        for pid, grades in self.grade_table.items():
            self.tile(row, 0, text = self.grade_table.name[pid],
                    cspan = 2, style = 'name')
            self.tile(row, 2, text = grades.stream,
                    style = 'small')
            col = col_sids
            for sid in self.grade_table.subjects:
                self.tile(row, col, text = grades.get(sid, UNCHOSEN),
                    style = 'entry',
                    validation = edit_grade, tag = f'#{pid}-{sid}')
                col += 1
            col = col_composites
            for sid in self.grade_table.composites:
                self.tile(row, col, text = grades[sid], style = 'base',
                        tag = f'#{pid}-{sid}')
                col += 1
            if self.averages:
                col = col_averages
                for sid in self.averages:
                    self.tile(row, col, text = '?', style = 'base',
                            tag = f'#{pid}-{sid}')
                    col += 1
                self.calc_averages(pid)
            col = col_extras
            for sid, name in self.grade_table.extras.items():
                self.tile(row, col, text = grades[sid], style = 'entry',
                        tag = f'#{pid}-{sid}')
                col += 1
            row += 1



#
    def valueChanged(self, tag, text):
        """Called when a cell value is changed by the editor.
        """
        self.cell_callback(tag, text)
#
    def calc_averages(self, pid):
        for sid in self.averages:
            tag = f'#{pid}-{sid}'
            tile = self.tagmap[tag]
            if sid == ':D':
                tile.setText(self.average(pid))
            elif sid == ':Dx':
                tile.setText(self.average_dem(pid))
#
    def average(self, pid):
        """Calculate the average of all grades, including composites,
        but ignoring components and non-numerical grades.
        """
        asum = 0
        ai = 0
        grades = self.grade_table[pid]
        for sid in self.grade_table.subjects:
            if self.grade_table.sid2subject_data[sid].composite:
                # A component
                continue
            try:
                gi = grades.i_grade[sid]
            except KeyError:
                continue
            asum += gi
            ai += 1
        for sid in self.grade_table.composites:
            try:
                gi = grades.i_grade[sid]
            except KeyError:
                continue
            asum += gi
            ai += 1
        if ai:
            return Frac(asum, ai).round(2)
        else:
            return '–––'
#
    def average_dem(self, pid):
        """Special average for "Realschulabschluss": De-En_Ma only.
        """
        asum = 0
        ai = 0
        grades = self.grade_table[pid]
        for sid in ('De', 'En', 'Ma'):
            try:
                gi = grades.i_grade[sid]
            except KeyError:
                continue
            asum += gi
            ai += 1
        if ai:
            return Frac(asum, ai).round(2)
        else:
            return '–––'
