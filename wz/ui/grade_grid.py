# -*- coding: utf-8 -*-
"""
ui/grade_grid.py

Last updated:  2021-02-20

Manage the grid for the grade-editor.


=+LICENCE=============================
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

=-LICENCE========================================
"""

#TODO ...

### Display texts
_PUPIL = "Schüler"
_STREAM = "Maßstab"
_COMMENT = "Bemerkungen für {name}"

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
    '*B': 8,
}

ROWS = (
#title
    12,
# info rows
    6, 6, 6, 6, 6, 6,
# header (tags)
    6, _SEP_SIZE
) # + 6 * n

#####################################################

import os

from ui.grid import Grid
from ui.ui_support import QuestionDialog


class GradeGrid(Grid):
    """Present the grades for a group and term, allowing editing of the
    individual fields.
    """
    def __init__(self, grades_view, subject_data, grade_data):

        ### Pop-up "selection" editors
#? selects
        for sel_type, sel_values in selects:
            self.addSelect(sel_type, values)
#? ...
        main_sids = subject_data['main_sids']
        components = subject_data['components']
        composites = subject_data['composites']
        calcs = subject_data['calcs']
        extras = subject_data['extras']
        pupil_data = grade_data['pupil_data']
        self.UNCHOSEN = subject_data['UNCHOSEN']

        # Get number of rows and columns
        row_pids = len(ROWS)
        _ROWS = ROWS + (_HEIGHT_LINE,) * len(pupil_data)
        col_sids = len(COLUMNS)
        _COLS = COLUMNS + (_WIDTH_GRADE,) * len(main_sids)
        col_components = len(_COLS) + 1
        if components:
            _COLS += (_SEP_SIZE,) + (_WIDTH_GRADE,) * len(components)
        col_composites = len(_COLS) + 1
        if composites:
            _COLS += (_SEP_SIZE,) + \
                    (_WIDTH_GRADE,) * len(composites)
        col_calcs = len(_COLS) + 1
        if calcs:
            _COLS += (_SEP_SIZE,) + (_WIDTH_AVERAGE,) * len(calcs)
        col_extras = len(_COLS) + 1
        if extras:
            _COLS += (_SEP_SIZE,)
            for x in extras:
                _COLS += (COL_WIDTH[x],)

        super().__init__(grades_view, _ROWS, _COLS)
        self.styles()

        # horizontal separator (after headers)
        self.tile(row_pids - 1, 0, cspan = len(_COLS), style = 'padding')
        # vertical separators
        _clast = 0
        for col in (col_sids, col_components, col_composites,
                col_calcs, col_extras):
            if col == _clast or col >= len(_COLS):
                continue
            self.tile(1, col - 1, rspan = len(_ROWS) - 1, style = 'padding')

        ### Title area
        self.tile(0, 0, text = "Notentabelle", cspan = 2, style = 'title')
        self.tile(0, 4, text = ADMIN.school_data['SCHOOL_NAME'],
                cspan = 10, style = 'titleR')
        ### General Info
        line = 1
#? info
        for key, value in info:
            self.tile(line, 0, text = key, style = 'info')
            if key.endswith('_D'):
                # An editable date
                self.tile(line, 1, text = value, style = 'info_edit',
                cspan = 2, validation = 'DATE', tag = key)
            else:
                # Non-editable
                self.tile(line, 1, text = value, cspan = 2, style = 'info')
            line += 1
        ### Subject headers
        line += 1   # 7?
        rspan = line - 1
        self.tile(line, 0, text = _PUPIL, cspan = 2, style = 'small')
        self.tile(line, 2, text = _STREAM,  style = 'small')
        col = col_sids
#? main_sids.items() ...
        for sid, name in main_sids.items():
            self.tile(line, col, text = sid, style = 'small')
            self.tile(1, col, text = name, rspan = rspan, style = 'v')
            col += 1
        col = col_components
        for sid, name in components.items():
            self.tile(line, col, text = sid, style = 'small')
            self.tile(1, col, text = name, rspan = rspan, style = 'v')
            col += 1
        col = col_composites
        for sid, name in composites.items():
            self.tile(line, col, text = sid, style = 'small')
            self.tile(1, col, text = name, rspan = rspan, style = 'v')
            col += 1
        col = col_calcs
        for sid, name in calcs.items():
            self.tile(line, col, text = sid, style = 'small')
            self.tile(1, col, text = name, rspan = rspan, style = 'v')
            col += 1
        col = col_extras
        for sid, name in extras.items():
            self.tile(line, col, text = sid, style = 'small')
            self.tile(1, col, text = name, rspan = rspan, style = 'v')
            col += 1

        # Pupil lines
        row = row_pids
        for pid, pname, stream, grades in pupil_data:
            self.tile(row, 0, text = pname, cspan = 2, style = 'name')
            self.tile(row, 2, text = stream, style = 'small')
            col = col_sids
            for sid in main_sids:
                self.tile(row, col, text = grades.get(sid, self.UNCHOSEN),
                    style = 'entry',
                    validation = 'grade', tag = f'${pid}-{sid}')
                col += 1
            col = col_components
            for sid in components:
                self.tile(row, col, text = grades.get(sid, self.UNCHOSEN),
                    style = 'entry',
                    validation = 'grade', tag = f'${pid}-{sid}')
                col += 1
            col = col_composites
            for sid in composites:
                self.tile(row, col, text = grades[sid], style = 'calc',
                        tag = f'${pid}-{sid}')
                col += 1
            if calcs:
                col = col_calcs
                for sid in calcs:
                    self.tile(row, col, text = '?', style = 'calc',
                            tag = f'${pid}-{sid}')
                    col += 1
#? Maybe back-end handles this before sending data?
                self.calc_tags(pid)

            col = col_extras
            for sid, name in extras.items():
                _tag = f'${pid}-{sid}'
                _val = grades[sid]
                _label = None
                if sid.endswith('_D'):
                    validation = 'DATE'
                elif sid == '*B':
                    validation = 'TEXT'
                    _label = _COMMENT.format(name = pname)
                else:
                    validation = sid
                self.tile(row, col, text = _val, style = 'entry',
                        validation = validation, tag = _tag, label = _label)
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
        self.new_style('base', font = ADMIN.school_data['FONT'], size = 11)
        self.new_style('calc', base = 'base', highlight = ':006000')
        self.new_style('name', base = 'base', align = 'l')
        self.new_style('title', font = ADMIN.school_data['FONT'], size = 12,
                align = 'l', border = 0, highlight = 'b')
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
    def to_pdf(self):
#TODO
        fname = os.path.basename(Grades.table_path(
                self.grade_table.group, self.grade_table.term))
        super().to_pdf(fname)
#
#?
#    def pupils(self):
#        """Return an ordered mapping of pupils: {pid -> name}.
#        """
#        return [(pid, name) for pid, name in self.grade_table.name.items()]
#
    def valueChanged(self, tag, text):
        """Called when a cell value is changed by the editor.
        Specific action is taken here only for real grades, which can
        cause further changes in the table.
        References to other value changes will nevertheless be available
        via <self.changes()> (a list of tile-tags).
        """
        super().valueChanged(tag, text)
        if tag.startswith('$'):
            # Averages should not be handled, but have no "validation"
            # so they won't land here at all.
            pid, sid = tag[1:].split('-')

# -> back-end

            grades = self.grade_table[pid]
            # Update the grade, includes special handling for numbers
            grades.set_grade(sid, text)
            if sid in self.grade_table.extras:
                return
            # If it is a component, recalculate the composite
            if sid in self.grade_table.components:
                csid = self.grade_table.sid2subject_data[sid].composite
                if csid == self.UNCHOSEN:
                    return
                grades.composite_calc(
                        self.grade_table.sid2subject_data[csid])
                ctag = f'${pid}-{csid}'
                cgrade = grades[csid]
                self.set_text(ctag, cgrade)
                self.set_change_mark(ctag, cgrade)
            # Recalculate the averages, etc.
            self.calc_tags(pid)
#TODO: Other changes: where to save the new values?
#
# -> back-end
    def calc_tags(self, pid):
        for sid, val in self.grade_table.recalc(pid):
            self.set_text(f'${pid}-{sid}', val)
