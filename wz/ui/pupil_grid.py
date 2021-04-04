# -*- coding: utf-8 -*-
"""
ui/pupil_grid.py

Last updated:  2021-04-02

Manage the grid for the pupil-data editor.

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

from ui.grid import Grid
from ui.ui_support import QuestionDialog

## Measurements are in mm ##
_HEIGHT_LINE = 6
COLUMNS = (40, 60)
ROWS = (
#title
    12,
) # + _HEIGHT_LINE * n

###

class PupilGrid(Grid):
    """Present the data for a single pupil, allowing editing of the
    individual fields.
    """
    def __init__(self, pupil_view, info):
        self._info = info
        _ROWS = ROWS + (_HEIGHT_LINE,) * len(info['fields'])
        super().__init__(pupil_view, _ROWS, COLUMNS)
        self.styles()

        ### Pop-up editor for SEX and STREAM fields
        self.addSelect('SEX', info['SEX'])
        self.addSelect('STREAM', list(info['STREAMS']))
        ### Non-editable fields
        noneditable = {'PID'}
        ### Title area
        self.tile(0, 0, text = '', cspan = 2, style = 'title', tag = 'title')
        ### field - value lines
        row = 1
        for field, tfield in info['fields']:
            self.tile(row, 0, text = tfield, style = 'key')
            vstyle = 'value'
            if field in noneditable:
                vstyle = 'fixed'
                validation = None
            elif field in self.editors:
                validation = field
            elif field.endswith('_D'):
                validation = 'DATE'
            else:
                validation = 'LINE'
            self.tile(row, 1, text = '', style = vstyle,
                    validation = validation, tag = field)
            row += 1
#
    def styles(self):
        """Set up the styles used in the table view.
        """
        font = ADMIN.school_data['FONT']
        self.new_style('base', font = font, size = 11)
        self.new_style('title', font = font, size = 12,
                align = 'c', border = 0, highlight = 'b')
        self.new_style('key', base = 'base', align = 'l')
        self.new_style('fixed', base = 'key', highlight = ':808080')
        self.new_style('value', base = 'key',
                highlight = ':002562', mark = 'E00000')
#
    def set_pupil(self, pdata, pname):
        self.pupil_data = pdata
        self.set_text('title', pname)
        for field, _ in self._info['fields']:
            self.set_text_init(field, pdata.get(field) or '')
#
    def value_changed(self, tile, text):
        """Called when a cell value is changed by the editor.
        """
        super().value_changed(tile, text)
        self.pupil_data[tile.tag] = text
