# -*- coding: utf-8 -*-
"""
ui/pupil_grid.py

Last updated:  2021-02-12

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

### Messages
_TITLE_TABLE_CHANGE = "Änderungen speichern"
_TABLE_CHANGES = "Änderungen für {name} nicht gespeichert.\n" \
        "Sollen sie jetzt gespeichert werden?\n" \
        "Wenn nicht, dann gehen sie verloren."
_TITLE_REMOVE_PUPIL = "Schülerdaten löschen"
_REMOVE_PUPIL = "Wollen Sie wirklich {name} aus der Datenbank entfernen?"

#####################################################

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
        _ROWS = ROWS + (_HEIGHT_LINE,) * len(info['FIELDS'])
        super().__init__(pupil_view, _ROWS, COLUMNS)
        self.styles()

        ### Pop-up editor for SEX and STREAM fields
        self.addSelect('SEX', info['SEX'])
        self.addSelect('STREAM', info['STREAMS'])
        ### Non-editable fields
        noneditable = {'PID'}
        ### Title area
        self.tile(0, 0, text = '', cspan = 2, style = 'title', tag = 'title')
        ### field - value lines
        row = 1
        for field, tfield in info['FIELDS'].items():
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
        for field in self._info['FIELDS']:
            self.set_text_init(field, pdata.get(field) or '')
#
#TODO ...
    def leaving(self, force):
        """When setting a scene (or clearing one), or exiting the program
        (or dialog), this check for changed data should be made.
        """
        if self.changes() and (force or QuestionDialog(_TITLE_TABLE_CHANGE,
                _TABLE_CHANGES.format(name = self.pupil_data.name()))):
            self.save_changes()
#
    def save_changes(self):
        changes = self.change_values()
        self.pupils.modify_pupil(self.pupil_data, changes)
#
    def remove_pupil(self):
        if QuestionDialog(_TITLE_REMOVE_PUPIL,
                _REMOVE_PUPIL.format(name = self.pupil_data.name())):
            self.pupils.modify_pupil(self.pupil_data, {'CLASS': None})
#
#    def valueChanged(self, tag, text):
#        """Called when a cell value is changed by the editor.
#        """
#        super().valueChanged(tag, text)
#        ...
