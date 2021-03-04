# -*- coding: utf-8 -*-
"""
ui/grade_grid_single.py

Last updated:  2021-03-02

Manage the grid for the grade-editor (single pupil).


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

### Messages

### Display texts
_STREAM = "Maßstab"
_COMMENT = "Bemerkungen für {name}"

## Measurements are in mm ##
_HEIGHT_LINE = 6
COLUMNS = (40, 60)
ROWS = (
#title
    12, _HEIGHT_LINE,
) # + _HEIGHT_LINE * n

#####################################################

from gui.grid import Grid


class GradeGrid1(Grid):
    """Present the grade data for a single pupil, allowing editing of the
    individual fields.
    There is special handling for certain fields.
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
        <pupil_data>: [pid, name, stream, {sid: value, ... }]
        """
        _ROWS = ROWS + (_HEIGHT_LINE,) * (len(info) + len(main_sids)
                + len(components) + len(composites)
                + len(calcs) + len(extras))
        super().__init__(view, _ROWS, COLUMNS)
        self.styles()
        # Pop-up "selection" editors
#        self.addSelect('grade', grade_list)
#        self.addSelect('stream', stream_list)
#TODO: Maybe the above are included in <selects>?
        for sel_type, sel_values in selects:
            self.addSelect(sel_type, sel_values)



selects
group
stream_list
subjects
pupil_data

# Where is the stream editable? Here? In the group view? Only in the
# pupil editor?
# Changing a stream could (in principle) cause a change of group – and
# indeed that does sometimes happen. This should normally not be done
# when there are already grades. It might occasionally be necessary,
# though.

# Also interesting – though not really relevant for single pupils – is
# the question of pupil changes (+/-) that take place after the (term)
# table has been started. Could a term table take primary pupil data from
# the pupils table and the subjects table, retrieving grades (as far as
# possible) from the grade table? That is probably the best. Then it
# should be no problem to restrict group changes to the pupil editor.
# Of course this would require some attention from the administrator,
# in case grades need changing, but that is hard to automate anyway.
# Actually that could also count for single reports. But editing of
# older grades – say first term when we are now in the second – could be
# very tricky. It probably shouldn't be done! The alternative is to allow
# updating of pupils and subjects only for the current term (which would
# need defining – perhaps by setting a date (normally "today"? – but
# perhaps tweakable for testing purposes???).

        pid, pname, stream, grades = pupil_data
        ### Title area
        self.tile(0, 0, text = 'Gruppe %s: %s' % (group, pupil_name),
                cspan = 2, style = 'title')#, tag = 'title')
        ### field - value lines
        self.tile(1, 0, text = _STREAM, style = 'key')
        self.tile(1, 1, text = stream, style = 'value',
                validation = 'stream', tag = 'STREAM')
# dates, etc? ("info")
# If this is just an alternative view onto a group, the dates are not
# editable. But if it is a special report, only the date-of-issue would
# be required (editable) and maybe some sort of tag?
#?
        row = 2
        for sid, name in main_sids:
            self.tile(row, 0, text = name, style = 'key')
            self.tile(row, 1, text = grades[sid], style = 'value',
                    validation = 'grade', tag = f'${pid}-{sid}')
            row += 1
        for sid, name in components:
            self.tile(row, 0, text = name, style = 'key')
            self.tile(row, 1, text = grades[sid], style = 'value',
                    validation = 'grade', tag = f'${pid}-{sid}')
            row += 1
        for sid, name in composites:
            self.tile(row, 0, text = name, style = 'key')
            self.tile(row, 1, text = grades[sid], style = 'calc',
                    tag = f'${pid}-{sid}')
            row += 1
        for sid, name in calcs:
            self.tile(row, 0, text = name, style = 'key')
            self.tile(row, 1, text = grades[sid], style = 'calc',
                    tag = f'${pid}-{sid}')
            row += 1
        for sid, name in extras:
            self.tile(row, 0, text = name, style = 'key')
            _tag = f'${pid}-{sid}'
            _val = grades[sid]
            _label = None
            if sid.endswith('_D'):
                validation = 'DATE'
            elif sid == '*B':
                validation = 'TEXT'
                _label = _COMMENT.format(name = pname)
            else:
#TODO: manage these validations!
                validation = sid
            self.tile(row, 1, text = _val, style = 'value',
                    validation = validation, tag = _tag, label = _label)
            row += 1
#
    def styles(self):
        """Set up the styles used in the table view.
        """
        self.new_style('base', font = SCHOOL_DATA.FONT, size = 11)
        self.new_style('title', font = SCHOOL_DATA.FONT, size = 12,
                align = 'c', border = 0, highlight = 'b')
        self.new_style('key', base = 'base', align = 'l')
        self.new_style('fixed', base = 'key', highlight = ':808080')
        self.new_style('calc', base = 'key', highlight = ':4080C0')
        self.new_style('value', base = 'key',
                highlight = ':002562', mark = 'E00000')
#
    def set_fields(self, mapping):
        for field in self.fields:
            self.set_text_init(field, mapping.get(field) or '')
#
    def valueChanged(self, tag, text):
        """Called when a cell value is changed by the editor.
        """
        super().valueChanged(tag, text)
        if tag in self.values:
            self.values[tag] = text
# call to backend?
