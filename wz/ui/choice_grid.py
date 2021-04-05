# -*- coding: utf-8 -*-
"""
ui/choice_grid.py

Last updated:  2021-04-05

Manage the grid for the puil-subject-choice-editor.


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

### Display texts
_PUPIL = "Schüler"
_STREAM = "Maßstab"

## Measurements are in mm ##
_SEP_SIZE = 1
_HEIGHT_LINE = 6
_WIDTH_TOGGLE = 8

COLUMNS = (35, 15, 15, _SEP_SIZE) # + ...

ROWS = (
#title
    12,
# info rows
    _HEIGHT_LINE, _HEIGHT_LINE, _HEIGHT_LINE, _HEIGHT_LINE,
    _HEIGHT_LINE, _HEIGHT_LINE,
# header (tags)
    _HEIGHT_LINE, _SEP_SIZE
) # + _HEIGHT_LINE * n

# Content of marked toggle-cells
MARK = 'X'

#####################################################

from qtpy.QtWidgets import QApplication
from qtpy.QtGui import QColor, QBrush
from qtpy.QtCore import Qt

from ui.gridbase import GridBase


class ToggleGrid(GridBase):
    """A grid of toggle-cells with column and row headers (potentially
    multi-row or multi-column respectively).
    Clicking on a cell will toggle its value. SHIFT-clicking marks a cell
    as the starting point of a rectangle. A further SHIFT-click marks
    the end-point of the rectangle and toggles all cells within the
    rectangle. The marking is removed.
    The mark can also be removed by clicking elsewhere (without SHIFT).
    """
    def __init__(self, gview, info, pupil_data, subjects):
        """<gview> is the "View" on which this "Scene" is to be presented.
        <info>: general information, [[key, value], ... ]
        <pupil_data>: A list of pupil lines, only non-taken subjects are
            included:
                [[pid, name, stream, [sid, ... ]], ... ]
        <subjects>: The list of subjects, possibly containing spacers:
                [[key, name], ... , null-value, [key, name], ... ]
        """
        # Set up grid: get number of rows and columns
        row_pids = len(ROWS)
        _ROWS = ROWS + (_HEIGHT_LINE,) * len(pupil_data)
        col_sids = len(COLUMNS)
        _COLS = list(COLUMNS)
        for s in subjects:
            _COLS.append(_WIDTH_TOGGLE if s else _SEP_SIZE)
        super().__init__(gview, _ROWS, _COLS)
        self.styles()
        # Horizontal separator (after headers)
        self.basic_tile(row_pids - 1, 0, tag = None, text = None,
                            style = 'padding', cspan = len(_COLS))
        # Vertical separator (before subjects)
        col = col_sids
        self.basic_tile(1, col_sids - 1, tag = None, text = None,
                            style = 'padding', rspan = len(_ROWS) - 1)
        ### Title area
        self.basic_tile(0, 0, tag = None, text = "Fächer(ab)wahl",
                style = 'title', cspan = 2)
        self.basic_tile(0, 4, tag = None,
                text = ADMIN.school_data['SCHOOL_NAME'],
                style = 'titleR', cspan = 10)
        ### General Info
        line = 1
        for key, value in info:
            self.basic_tile(line, 0, tag = None, text = key,
                    style = 'info')
            # Non-editable
            self.basic_tile(line, 1, tag = None, text = value,
                    style = 'info', cspan = 2)
            line += 1
        ### Subject headers
        line = 7
        rspan = line - 1
        self.basic_tile(line, 0, tag = None, text = _PUPIL,
                style = 'small', cspan = 2)
        self.basic_tile(line, 2, tag = None, text = _STREAM,
                style = 'small')
        col = col_sids
        self.sids = []
        for sid_name in subjects:
            if sid_name:
                sid, name = sid_name
                self.sids.append(sid)
                self.basic_tile(line, col, tag = None, text = sid,
                        style = 'small')
                self.basic_tile(1, col, tag = None, text = name,
                        style = 'v', rspan = rspan)
            else:
                # vertical spacer
                self.basic_tile(1, col, tag = None, text = None,
                        style = 'padding', rspan = len(_ROWS) - 1)
            col += 1
        ### Pupil lines
        row = row_pids
        # The array (list of lists) <self.toggles> is a simple matrix
        # of the toggle-tiles, omitting the skipped columns.
        self.toggles = []
        self.pids = []
        self.value0 = set() # Set of initially marked cells (x, y)
        y = 0
        for pid, pname, stream, choices_list in pupil_data:
            choices = set(choices_list)
            self.basic_tile(row, 0, tag = None, text = pname,
                    style = 'name', cspan = 2)
            self.basic_tile(row, 2, tag = None, text = stream,
                    style = 'small')
            col = col_sids
            x = 0
            _toggles = []
            for sid_name in subjects:
                if sid_name:
                    tag = (x, y)
                    if sid_name[0] in choices:
                        self.value0.add(tag)
                        val = MARK
                    else:
                        val = ''
                    tile = self.basic_tile(row, col, tag = (x, y),
                            text = val, style = 'toggle')
                    _toggles.append(tile)
                    x += 1
                col += 1
            self.pids.append(pid)
            self.toggles.append(_toggles)
            y += 1
            row += 1
        # Need a highlighted/selected QBrush for a toggle-cell
        self.mark_brush = QBrush(QColor('#60FFFF00'))
        self.no_mark = self.style('toggle').bgColour or QBrush(Qt.NoBrush)
        # Collect changed cell tags for signalling "table changed".
        self._changes = set()
#
    def styles(self):
        """Set up the styles used in the table view.
        """
        self.new_style('base', font = ADMIN.school_data['FONT'], size = 11)
        self.new_style('name', base = 'base', align = 'l')
        self.new_style('title', font = ADMIN.school_data['FONT'], size = 12,
                align = 'l', border = 0, highlight = 'b')
        self.new_style('info', base = 'base', border = 0, align = 'l')
        self.new_style('underline', base = 'base', border = 2)
        self.new_style('titleR', base = 'title', align = 'r')
        self.new_style('small', base = 'base', size = 10)
        self.new_style('v', base = 'small', align = 'b')
        self.new_style('toggle', base = 'base', highlight = ':002562',
                mark = 'E00000')
        self.new_style('padding', bg = '666666')
#
    def tile_left_clicked(self, tile):
        if isinstance(tile.tag, tuple):
            # toggle-tile
            kbdmods = QApplication.keyboardModifiers()
            if kbdmods & Qt.ShiftModifier:
                if self.toggle_start:
                    # toggle range
                    r0, c0 = self.toggle_start.tag
                    r1, c1 = tile.tag
                    r_range = range(r0, r1 + 1) if r1 >= r0 \
                            else range(r1, r0 + 1)
                    c_range = range(c0, c1 + 1) if c1 >= c0 \
                            else range(c1, c0 + 1)
                    for r in r_range:
                        for c in c_range:
                            t = self.toggles[r][c]
                            t.setText('' if t.value() else MARK)
                else:
                    self.toggle_start = tile
                    # highlight cell
                    tile.setBrush(self.mark_brush)
                    return False
            else:
                self.toggle(tile)
        if self.toggle_start:
            # remove highlight
            if self.toggle_start:
                self.toggle_start.setBrush(self.no_mark)
                self.toggle_start = None
        return False
#
    def toggle(self, tile):
        val = '' if tile.value() else MARK
        tile.setText(val)
        if val:
            if tile.tag in self.value0:
                self.changes_discard(tile.tag)
            else:
                self.changes_add(tile.tag)
        else:
            if tile.tag in self.value0:
                self.changes_add(tile.tag)
            else:
                self.changes_discard(tile.tag)
#
    def changes_discard(self, tag):
        if self._changes:
            self._changes.discard(tag)
            if not self._changes:
                self._gview.set_changed(False)
#
    def changes_add(self, tag):
        if not self._changes:
            self._gview.set_changed(True)
        self._changes.add(tag)
#
    def changes(self):
        return list(self._changes)
#
    def data(self):
        """Return choice data as a list of "non-chosen" subject lists.
            [(pid, [sid, ...]), ... ]
        Also pupils with empty lists are included.
        """
        clist = []
        y = 0
        for row in self.toggles:
            x = 0
            slist = []
            for sid in self.sids:
                if row[x].value():
                    slist.append(sid)
                x += 1
            clist.append((self.pids[y], slist))
            y += 1
        return clist
