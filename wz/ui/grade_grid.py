# -*- coding: utf-8 -*-
"""
ui/grade_grid.py

Last updated:  2021-02-23

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
    def __init__(self, grades_view, info, main_sids, components,
            composites, calcs, extras, selects, pupil_data):
        """<grades_view> is the "View" on which this "Scene" is to be
        presented.
            <info>: general information, [[key, value, tag], ... ]
            <main_sids>, <components>, <composites>, <calcs>, <extras>:
                These are the subjects (and similar items) for the columns.
                They have the structure [[key, name], ... ]
            <selects>: Special "selection" entries for particular field
                editors, [[selection type, [value, ... ]], ... ]
            <pupil_data>: Alist of pupil lines,
                [[pid, name, stream, {sid: value, ... }], ... ]
        """
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
            for x, _ in extras:
                _COLS += (COL_WIDTH[x],)

        super().__init__(grades_view, _ROWS, _COLS)
        self.styles()

        # Pop-up "selection" editors
        for sel_type, sel_values in selects:
            self.addSelect(sel_type, sel_values)

        # horizontal separator (after headers)
        self.tile(row_pids - 1, 0, cspan = len(_COLS), style = 'padding')
        # vertical separators
        _clast = 0
        for col in (col_sids, col_components, col_composites,
                col_calcs, col_extras):
            if col == _clast or col >= len(_COLS):
                continue
            self.tile(1, col - 1, rspan = len(_ROWS) - 1, style = 'padding')

        # Title area
        self.tile(0, 0, text = "Notentabelle", cspan = 2, style = 'title')
        self.tile(0, 4, text = ADMIN.school_data['SCHOOL_NAME'],
                cspan = 10, style = 'titleR')
        # General Info
        line = 1
        for key, value, tag in info:
            self.tile(line, 0, text = key, style = 'info')
            if tag:
                # An editable field
                if tag.endswith('_D'):
                    vtype = 'DATE'
                else:
                    vtype = 'LINE'
                self.tile(line, 1, text = value, style = 'info_edit',
                        cspan = 2, validation = vtype, tag = tag)
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
        for sid, name in main_sids:
            self.tile(line, col, text = sid, style = 'small')
            self.tile(1, col, text = name, rspan = rspan, style = 'v')
            col += 1
        col = col_components
        for sid, name in components:
            self.tile(line, col, text = sid, style = 'small')
            self.tile(1, col, text = name, rspan = rspan, style = 'v')
            col += 1
        col = col_composites
        for sid, name in composites:
            self.tile(line, col, text = sid, style = 'small')
            self.tile(1, col, text = name, rspan = rspan, style = 'v')
            col += 1
        col = col_calcs
        for sid, name in calcs:
            self.tile(line, col, text = sid, style = 'small')
            self.tile(1, col, text = name, rspan = rspan, style = 'v')
            col += 1
        col = col_extras
        for sid, name in extras:
            self.tile(line, col, text = sid, style = 'small')
            self.tile(1, col, text = name, rspan = rspan, style = 'v')
            col += 1

        # Pupil lines
        row = row_pids
        for pid, pname, stream, grades in pupil_data:
            self.tile(row, 0, text = pname, cspan = 2, style = 'name')
            self.tile(row, 2, text = stream, style = 'small')
            col = col_sids
            for sid, _ in main_sids:
                self.tile(row, col, text = grades[sid],
                    style = 'entry',
                    validation = 'grade', tag = f'${pid}-{sid}')
                col += 1
            col = col_components
            for sid, _ in components:
                self.tile(row, col, text = grades[sid],
                    style = 'entry',
                    validation = 'grade', tag = f'${pid}-{sid}')
                col += 1
            col = col_composites
            for sid, _ in composites:
                self.tile(row, col, text = grades[sid], style = 'calc',
                        tag = f'${pid}-{sid}')
                col += 1
            if calcs:
                col = col_calcs
                for sid, _ in calcs:
                    self.tile(row, col, text = grades[sid], style = 'calc',
                            tag = f'${pid}-{sid}')
                    col += 1
            col = col_extras
            for sid, name in extras:
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
            BACKEND('GRADES_value_changed', pid = pid, sid = sid, val = text)
#
    def set_grades(self, vlist):
        for pid, sid, cgrade in vlist:
            ctag = f'${pid}-{sid}'
            self.set_text(ctag, cgrade)
            self.set_change_mark(ctag, cgrade)

