# -*- coding: utf-8 -*-
"""
gui/grade_grid.py

Last updated:  2020-12-09

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
_TITLE_TABLE_CHANGE = "Änderungen speichern"
# Would need to be a bit different for individual pupils:
_TABLE_CHANGES = "Änderungen für Klasse/Gruppe {group}, {term}" \
        " im Jahr {year} nicht gespeichert.\n" \
        "Sollen sie jetzt gespeichert werden?\n" \
        "Wenn nicht, dann gehen sie verloren."

### Display texts
_PUPIL = "Schüler"
_STREAM = "Maßstab"

#####################################################

# To test this module, use it via grade_editor.py

from gui.grid import Grid
from gui.gui_support import QuestionDialog

from grades.gradetable import GradeTable, Grades, Frac
from local.base_config import FONT, SCHOOL_NAME
from local.grade_config import UNCHOSEN

## Measurements are in mm ##
_SEP_SIZE = 1
_WIDTH_AVERAGE = 12
_HEIGHT_LINE = 6
_WIDTH_GRADE = 8
COLUMNS = (35, 15, 15, _SEP_SIZE) # + ...

# Specify widths of special columns explicitly:
COL_WIDTH = {
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
    6, _SEP_SIZE
) # + 6 * n

###

class GradeGrid(Grid):
    def __init__(self, grades_view, schoolyear, group, term):
        """Set the grade table (a <GradeTable> instance) to be used.
        Set up the grid accordingly.
        """
        self.grade_table = GradeTable.group_table(schoolyear, group, term,
                ok_new = True)

#        print("$$$ pupils:", len(self.grade_table))
#        print("$$$ subjects:", self.grade_table.subjects) # real subjects

        # Get number of rows and columns from <grade_table>
        row_pids = len(ROWS)
        _ROWS = ROWS + (_HEIGHT_LINE,) * len(self.grade_table)
        col_sids = len(COLUMNS)
        # Separate out "component" subjects
        main_sids = {}
        components = {}
        for sid, name in self.grade_table.subjects.items():
            if sid in self.grade_table.components:
                components[sid] = name
            else:
                main_sids[sid] = name
        _COLS = COLUMNS + (_WIDTH_GRADE,) * len(main_sids)
        col_components = len(_COLS) + 1
        if components:
            _COLS += (_SEP_SIZE,) + (_WIDTH_GRADE,) * len(components)
        col_composites = len(_COLS) + 1
        if self.grade_table.composites:
            _COLS += (_SEP_SIZE,) + \
                    (_WIDTH_GRADE,) * len(self.grade_table.composites)
        col_averages = len(_COLS) + 1
# The averages are only used in the grade editor ...
        self.averages = Grades.averages(group)
        if self.averages:
            _COLS += (_SEP_SIZE,) + (_WIDTH_AVERAGE,) * len(self.averages)
        col_extras = len(_COLS) + 1
        if self.grade_table.extras:
            _COLS += (_SEP_SIZE,)
            for x in self.grade_table.extras:
                _COLS += (COL_WIDTH[x],)

        super().__init__(grades_view, _ROWS, _COLS)
        self.styles()

        self.tile(row_pids - 1, 0, cspan = len(_COLS), style = 'padding')
        for col in (col_sids, col_components, col_composites,
                col_averages, col_extras):
            self.tile(1, col - 1, rspan = len(_ROWS) - 1, style = 'padding')

        ### Pop-up editor for grades
        self.addSelect('grade', Grades.group_info(group, 'NotenWerte'))

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
                validation = 'DATE', tag = 'ISSUE_D')
        self.tile(5, 0, text = self.grade_table.GRADES_D, style = 'info')
        self.tile(5, 1, text = self.grade_table.grades_d,
                cspan = 2, style = 'info_edit',
                validation = 'DATE', tag = 'GRADES_D')

        # Subject lines
        self.tile(7, 0, text = _PUPIL, cspan = 2, style = 'small')
        self.tile(7, 2, text = _STREAM,  style = 'small')
        col = col_sids
        for sid, name in main_sids.items():
            self.tile(7, col, text = sid, style = 'small')
            self.tile(1, col, text = name, rspan = 6, style = 'v')
            col += 1
        col = col_components
        for sid, name in components.items():
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
            if sid == '*ZA':
                _ZA_vals = Grades.group_info(group, f'*ZA/{term}')
                self.addSelect(sid, _ZA_vals)
                ZA_default = _ZA_vals[0] if _ZA_vals else ''
#            elif sid.endswith('_D'):
#                'DATE'
            elif sid == '*Q':
                self.addSelect(sid, Grades.group_info(group, '*Q'))
            col += 1

        # Pupil lines
        row = row_pids
        for pid, grades in self.grade_table.items():
            self.tile(row, 0, text = self.grade_table.name[pid],
                    cspan = 2, style = 'name')
            self.tile(row, 2, text = grades.stream,
                    style = 'small')
            col = col_sids
            for sid in main_sids:
                self.tile(row, col, text = grades.get(sid, UNCHOSEN),
                    style = 'entry',
                    validation = 'grade', tag = f'${pid}-{sid}')
                col += 1
            col = col_components
            for sid in components:
                self.tile(row, col, text = grades.get(sid, UNCHOSEN),
                    style = 'entry',
                    validation = 'grade', tag = f'${pid}-{sid}')
                col += 1
            col = col_composites
            for sid in self.grade_table.composites:
                self.tile(row, col, text = grades[sid], style = 'calc',
                        tag = f'${pid}-{sid}')
                col += 1
            if self.averages:
                col = col_averages
                for sid in self.averages:
                    self.tile(row, col, text = '?', style = 'calc',
                            tag = f'${pid}-{sid}')
                    col += 1
                self.calc_averages(pid)
            col = col_extras
            for sid, name in self.grade_table.extras.items():
                _tag = f'${pid}-{sid}'
                _val = grades[sid]
                self.tile(row, col, text = _val, style = 'entry',
                        validation = 'DATE' if sid.endswith('_D') else sid,
                        tag = _tag)
                # Default values if empty?
                if (not _val) and sid == '*ZA':
                    self.set_text(_tag, ZA_default)
                    self.valueChanged(_tag, ZA_default)
                col += 1
            row += 1
#
    def styles(self):
        """Set up the styles used in the table view.
        """
        self.new_style('base', font = FONT, size = 11)
        self.new_style('calc', base = 'base', highlight = ':006000')
        self.new_style('name', base = 'base', align = 'l')
        self.new_style('title', font = FONT, size = 12, align = 'l',
                    border = 0, highlight = 'b')
        self.new_style('info', base = 'base', border = 0, align = 'l')
        self.new_style('underline', base = 'base', border = 2)
        self.new_style('titleR', base = 'title', align = 'r')
        self.new_style('small', base = 'base', size = 10)
        self.new_style('v', base = 'small', align = 'b')
        self.new_style('h', base = 'small', border = 0)
        self.new_style('entry', base = 'base', highlight = ':002562',
                mark = 'E00000')
        self.new_style('info_edit', base = 'info', align = 'l',
                highlight = ':002562', mark = 'E00000')
        self.new_style('padding', bg = '666666')
#
    def leaving(self):
        """When setting a scene (or clearing one), or exiting the program
        (or dialog), this check for changed data should be made.
        """
        if self.changes and QuestionDialog(_TITLE_TABLE_CHANGE,
                _TABLE_CHANGES.format(year = self.grade_table.schoolyear,
                        term = Grades.term2text(self.grade_table.term),
                        group = self.grade_table.group)):
            self.grade_table.save()
        self.changes = None
#
    def pupils(self):
        """Return an ordered mapping of pupils: {pid -> name}.
        """
        return [(pid, name) for pid, name in self.grade_table.name.items()]
#
    def valueChanged(self, tag, text):
        """Called when a cell value is changed by the editor.
        Specific action is taken here only for real grades, which can
        cause further changes in the table.
        References to other value changes will nevertheless be available
        in <self.changes> (a set of tile-tags).
        """
        super().valueChanged(tag, text)
        if tag.startswith('$'):
            # Averages should not be handled, but have no "validation"
            # so they won't land here at all.
            pid, sid = tag[1:].split('-')
            grades = self.grade_table[pid]
            # Update the grade, includes special handling for numbers
            grades.set_grade(sid, text)
            if sid in self.grade_table.extras:
                return
            # If it is a component, recalculate the composite
            if sid in self.grade_table.components:
                csid = self.grade_table.sid2subject_data[sid].composite
                if csid == UNCHOSEN:
                    return
                grades.composite_calc(
                        self.grade_table.sid2subject_data[csid])
                ctag = f'${pid}-{csid}'
                cgrade = grades[csid]
                self.set_text(ctag, cgrade)
                self.set_change_mark(ctag, cgrade)
            # Recalculate the averages
            self.calc_averages(pid)
#TODO: Other changes: where to save the new values?
#
    def calc_averages(self, pid):
        for sid in self.averages:
            tag = f'${pid}-{sid}'
            if sid == ':D':
                self.set_text(tag, self.average(pid))
            elif sid == ':Dx':
                self.set_text(tag, self.average_dem(pid))
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
            gi = grades.i_grade[sid]
            if gi >= 0:
                asum += gi
                ai += 1
        for sid in self.grade_table.composites:
            gi = grades.i_grade[sid]
            if gi >= 0:
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
            gi = grades.i_grade[sid]
            if gi >= 0:
                asum += gi
                ai += 1
        if ai:
            return Frac(asum, ai).round(2)
        else:
            return '–––'
