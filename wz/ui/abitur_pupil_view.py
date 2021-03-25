# -*- coding: utf-8 -*-
"""
ui/abitur_pupil_view.py

Last updated:  2021-03-23

Editor for Abitur results (single pupil).


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

#TODO: Do I want/need to display the FHS-criteria and points?
# Perhaps as pop-up?

##### Configuration
## Measurements are in mm ##
COLUMNS = (14, 14, 25, 14, 14, 4, 20, 6, 6, 14, 3, 18, 3, 11)
ROWS = (
    6, 3, 6, 3, 4, 5, 4, 10, 5, 1,
    # Written subjects:
    5, 6, 6, 5, 6, 6, 5, 6, 6, 5, 6, 6,
    # Other subjects:
    5, 5, 6, 5, 6, 5, 6, 5, 6,
    # Results:
    5, 5, 3, 5, 3, 5, 3, 5, 3, 5, 5, 6, 5, 6
)

VALID_GRADES = (
    '15', '14', '13',
    '12', '11', '10',
    '09', '08', '07',
    '06', '05', '04',
    '03', '02', '01',
    '00'
)
VALID_GRADES_X = VALID_GRADES + ('*',)  # "Nachprüfungen" are optional

### Messages
#_TITLE_TABLE_CHANGE = "Änderungen speichern"
#_TABLE_CHANGES = "Änderungen für {pupil} nicht gespeichert.\n" \
#        "Sollen sie jetzt gespeichert werden?\n" \
#        "Wenn nicht, dann gehen sie verloren."


#####################################################

from ui.grid import Grid
from ui.ui_support import QuestionDialog


class AbiPupilView(Grid):
    def styles(self):
        """Set up the styles used in the grid view.
        """
        self.new_style('base', font = ADMIN.school_data['FONT'], size = 11)
        self.new_style('info', base = 'base', border = 0)
        self.new_style('infoL', base = 'info', align = 'l')
        self.new_style('label', base = 'infoL', highlight = 'b')

        self.new_style('title', font = ADMIN.school_data['FONT'], size = 12,
                align = 'l', border = 0, highlight = 'b')
        self.new_style('titleR', base = 'title', align = 'r')
        self.new_style('underline', base = 'base', border = 2)
        self.new_style('small', base = 'base', size = 10)
        self.new_style('v', base = 'small', align = 'm')
        self.new_style('h', base = 'small', border = 0)
        self.new_style('entry', base = 'base', highlight = ':002562',
                mark = 'E00000')
        self.new_style('resultL', base = 'title', border = 2)
        self.new_style('result', base = 'resultL', align = 'c')
        self.new_style('date', base = 'result', highlight = ':002562',
                mark = 'E00000')
#
    def __init__(self, grades_view):
        super().__init__(grades_view, ROWS, COLUMNS)
        self.styles()

        ### Cell editors
        self.addSelect('grade', VALID_GRADES)
        self.addSelect('xgrade', VALID_GRADES_X)

        ### Title area
        self.tile(0, 0, text = "Abitur-Berechnungsbogen", cspan = 4,
                style = 'title')
        self.tile(0, 4, text = ADMIN.school_data['SCHOOL_NAME'],
                cspan = 10, style = 'titleR')
        self.tile(2, 7, text = "Schuljahr:", cspan = 3, style = 'titleR')
        self.tile(2, 10, text = '', cspan = 4, style = 'title',
                tag = 'SCHOOLYEAR')
        self.tile(3, 0, cspan = 14, style = 'underline')

        ### Pupil's name
        self.tile(5, 0, cspan = 2, text = "Name:", style = 'label')
        self.tile(5, 2, cspan = 12, text = '', style = 'label',
                tag = 'NAME')
        self.tile(6, 0, cspan = 14, style = 'underline')

        ### Grade area headers
        self.tile(8, 2, text = "Fach", style = 'h')
        self.tile(8, 3, text = "Kurspunkte", cspan = 2, style = 'h')
        self.tile(8, 6, text = "Mittelwert", style = 'h')
        self.tile(8, 9, text = "Berechnungspunkte", cspan = 3,
                style = 'h')

        self.tile(10, 11, text = "Fach 1-4", style = 'small')
        self.tile(11, 0, text = "Erhöhtes Anforderungsniveau",
                rspan = 8, style = 'v')
        self.tile(23, 11, text = "Fach 5-8", style = 'small')
        self.tile(20, 0, text = "Grundlegendes Anforderungsniveau",
                rspan = 11, style = 'v')

        ### Subject entries
        # With written exams
        for i in (1, 2, 3, 4):
            istr = str(i)
            row0 = 8 + i*3
            self.tile(row0, 1, rspan = 2, text = istr, style = 'base')
            self.tile(row0, 2, rspan = 2, text = '', style = 'base',
                    tag = "SUBJECT_%s" % istr)
            self.tile(row0, 3, text = "schr.", style = 'small')
            self.tile(row0 + 1, 3, text = "mündl.", style = 'small')
            self.tile(row0, 4, text = '', style = 'entry',
                    validation = 'grade', tag = "GRADE_%s" % istr)
            self.tile(row0 + 1, 4, text = '', style = 'entry',
                    validation = 'xgrade', tag = "GRADE_%s_m" % istr)
            self.tile(row0, 6, rspan = 2, text = '', style = 'base',
                    tag = "AVERAGE_%s" % istr)
            self.tile(row0, 7, rspan = 2, text = "X", style = 'info')
            self.tile(row0, 8, rspan = 2, text = "12" if i < 4 else "8",
                    style = 'info')
            self.tile(row0, 9, rspan = 2, text = '', style = 'underline',
                    tag = "SCALED_%s" % istr)

        # Without written exams
        for i in (5, 6, 7, 8):
            istr = str(i)
            row0 = 14 + i*2
            self.tile(row0, 1, text = istr, style = 'base')
            self.tile(row0, 2, text = '', style = 'base',
                    tag = "SUBJECT_%s" % istr)
            self.tile(row0, 3, text = "mündl." if i < 7 else "2. Hj.",
                    style = 'small')
            self.tile(row0, 4, text = "04", style = 'entry',
                    validation = 'grade', tag = "GRADE_%s" % istr)
            self.tile(row0, 6, text = '', style = 'base',
                    tag = "AVERAGE_%s" % istr)
            self.tile(row0, 7, text = "X", style = 'info')
            self.tile(row0, 8, text = "4", style = 'info')
            self.tile(row0, 9, text = '', style = 'underline',
                    tag = "SCALED_%s" % istr)

        ### Totals
        self.tile(11, 11, text = '', rspan = 11, style = 'base',
                    tag = "s1_4")
        self.tile(24, 11, text = '', rspan = 7, style = 'base',
                    tag = "s5_8")

        ### Evaluation
        i = 0
        for text in (
                "Alle >0:",
                "Fach 1 – 4, mindestens 2mal ≥ 5P.:",
                "Fach 5 – 8, mindestens 2mal ≥ 5P.:",
                "Fach 1 – 4 ≥ 220:",
                "Fach 5 – 8 ≥ 80:"
                ):
            row = 32 + i*2
            i += 1
            self.tile(row, 2, text = text, cspan = 6, style = 'infoL')
            self.tile(row, 9, text = '', style = 'base',
                tag = "JA_%d" % i)

        ### Final result
        self.tile(42, 2, text = "Summe:", style = 'resultL')
        self.tile(42, 3, text = '', cspan = 2, style = 'result',
                tag = "SUM")
        self.tile(42, 8, text = "Endnote:", cspan = 2, style = 'resultL')
        self.tile(42, 10, text = '', cspan = 4, style = 'result',
                tag = "FINAL_GRADE")

        self.tile(44, 8, text = "Datum:", cspan = 2, style = 'resultL')
        self.tile(44, 10, text = '', cspan = 4, style = 'date',
                validation = 'DATE', tag = "FERTIG_D")
#TODO: Do I want to display the date in local format? If so, I would need
# to adjust the popup editor ...
#
    def valueChanged(self, tag, text):
        """Called when a cell value is changed by the editor.
        """
        super().valueChanged(tag, text)
        BACKEND('ABITUR_set_value', tag = tag, val = text)
#TODO:???
#        self.set_change_mark(tag, text)

#
#    def leaving(self, force):
#        """When setting a scene (or clearing one), or exiting the program
#        (or dialog), this check for changed data should be made.
#        """
#        if self.changes() and (force or QuestionDialog(_TITLE_TABLE_CHANGE,
#                _TABLE_CHANGES.format(pupil = self.name))):
#            self.save_changes()
#
#    def set_pupil(self, pid):
#        """A new pupil has been selected: reset the grid accordingly.
#        """
#        self.clear_changes()
#        self._changes_init()    # set of changed cells
#        BACKEND('ABITUR_set_pupil', pid = pid)
#
    def set_cells(self, data):
        for tag, val in data:
            try:
                self.set_text(tag, val)
            except KeyError:
                pass
#
    def init_cells(self, data):
        for tag, val in data:
            self.set_text_init(tag, val)
#
    def save_data(self):
        BACKEND('ABITUR_save_current')
        # -> redisplay of term/group/subselect
