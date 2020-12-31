# -*- coding: utf-8 -*-
"""
gui/pupil_grid.py

Last updated:  2020-12-31

Manage the grid for the pupil-data editor.


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
_TABLE_CHANGES = "Änderungen für {name} nicht gespeichert.\n" \
        "Sollen sie jetzt gespeichert werden?\n" \
        "Wenn nicht, dann gehen sie verloren."

#####################################################

# To test this module, use it via admin.py

import os

from gui.grid import Grid
from gui.gui_support import QuestionDialog

from core.pupils import Pupils
from local.base_config import FONT, PupilsBase
from local.grade_config import STREAMS

## Measurements are in mm ##
_HEIGHT_LINE = 6
COLUMNS = (50, 80)
ROWS = (
#title
    12,
) # + _HEIGHT_LINE * n

###

class PupilGrid(Grid):
    """Present the data for a single pupil, allowing editing of the
    individual fields.
    """
    def __init__(self, pupil_view, schoolyear, klass, pid):
        self.pupils = Pupils(schoolyear)
        self.schoolyear = schoolyear
        self.klass = klass
        self.pid = pid
        self.pupil_data = self.pupils[pid]
        _ROWS = ROWS + (_HEIGHT_LINE,) * len(PupilsBase.FIELDS)
        super().__init__(pupil_view, _ROWS, COLUMNS)
        self.styles()

        ### Pop-up editor for SEX and STREAM fields
        self.addSelect('SEX', PupilsBase.SEX)
        self.addSelect('STREAM', STREAMS)
        ### Non-editable fields
        noneditable = {'PSORT'}
        ### Title area
#        self.tile(0, 0, text = "Notentabelle", cspan = 2, style = 'title')
#        self.tile(0, 4, text = SCHOOL_NAME, cspan = 10, style = 'titleR')
        ### field - value lines
        row = 1
        for field, tfield in PupilsBase.FIELDS.items():
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
            self.tile(row, 1, text = self.pupil_data[field],
                    style = vstyle, validation = validation,
                    tag = field)
            row += 1
#
    def styles(self):
        """Set up the styles used in the table view.
        """
        self.new_style('base', font = FONT, size = 11)
        self.new_style('key', base = 'base', align = 'l')
        self.new_style('fixed', base = 'key', highlight = ':808080')
        self.new_style('value', base = 'key',
                highlight = ':002562', mark = 'E00000')
#
    def leaving(self, force):
        """When setting a scene (or clearing one), or exiting the program
        (or dialog), this check for changed data should be made.
        """
        if self.changes() and (force or QuestionDialog(_TITLE_TABLE_CHANGE,
                _TABLE_CHANGES.format(name = self.pupil_data.name()))):
            self.save_changes()
#
    def save_changes(self):
        print("TODO:", self.change_values())
#TODO: need schoolyear and class – also old class if that has been changed!
# Maybe a change of class should be handled separately (a button in the
# panel)?

#
#    def valueChanged(self, tag, text):
#        """Called when a cell value is changed by the editor.
#        """
#        super().valueChanged(tag, text)
#        ...
