# -*- coding: utf-8 -*-
"""
gui/abitur_pupil_view.py

Last updated:  2020-12-22

Editor for Abitur results (single pupil).


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

### Messages
_TITLE_TABLE_CHANGE = "Änderungen speichern"
_TABLE_CHANGES = "Änderungen für {pupil} nicht gespeichert.\n" \
        "Sollen sie jetzt gespeichert werden?\n" \
        "Wenn nicht, dann gehen sie verloren."


#####################################################

# To test this module, use it via grade_editor.py (select "Anlass: Abitur")

from gui.grid import Grid
from gui.gui_support import QuestionDialog

from local.base_config import FONT, print_schoolyear, SCHOOL_NAME
from local.grade_config import NO_GRADE
from local.abitur_config import AbiCalc
from grades.gradetable import GradeTable

VALID_GRADES_X = VALID_GRADES + (NO_GRADE,)


class AbiPupilView(Grid):
    def styles(self):
        """Set up the styles used in the grid view.
        """
        self.new_style('base', font = FONT, size = 11)
        self.new_style('info', base = 'base', border = 0)
        self.new_style('infoL', base = 'info', align = 'l')
        self.new_style('label', base = 'infoL', highlight = 'b')

        self.new_style('title', font = FONT, size = 12, align = 'l',
                    border = 0, highlight = 'b')
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
    def __init__(self, grades_view, schoolyear, group):
        self.grade_table = GradeTable(schoolyear, group, 'A', ok_new = True)
        super().__init__(grades_view, ROWS, COLUMNS)
        self.styles()

        ### Cell editors
        self.addSelect('grade', VALID_GRADES)
        self.addSelect('xgrade', VALID_GRADES_X)

        ### Title area
        self.tile(0, 0, text = "Abitur-Berechnungsbogen", cspan = 4,
                style = 'title')
        self.tile(0, 4, text = SCHOOL_NAME, cspan = 10, style = 'titleR')
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
        Specific action is taken here only for grades, which can
        cause further changes in the table.
        References to other value changes will nevertheless be available
        via <self.changes()> (a list of tile-tags).
        """
        super().valueChanged(tag, text)
        if tag.startswith('GRADE_'):
            self.calc.set_editable_cell(tag, text)
            self.update_calc()
        elif tag == 'FERTIG_D':
            self.calc.set_editable_cell(tag, text)
        else:
            raise Bug("Invalid cell change, %s: %s" % (tag, text))
#
    def leaving(self, force):
        """When setting a scene (or clearing one), or exiting the program
        (or dialog), this check for changed data should be made.
        """
        if self.changes() and (force or QuestionDialog(_TITLE_TABLE_CHANGE,
                _TABLE_CHANGES.format(pupil = self.name))):
            self.save_changes()
#
    def set_pupil(self, pid):
        """A new pupil has been selected: reset the grid accordingly.
        """
        self.pid = pid
        self.clear_changes()
        self.changes_init()    # set of changed cells
        # Set pupil's name (NAME) and completion date (FERTIG_D)
        self.name = self.grade_table.name[pid]
        self.set_text('SCHOOLYEAR',
                print_schoolyear(self.grade_table.schoolyear))
        self.set_text('NAME', self.name)
        self.calc = AbiCalc(self.grade_table, pid)
        # Set date of completion: if no value for pupil, use group date
        self.calc.set_editable_cell('FERTIG_D',
                self.calc.grade_map['*F_D'] or self.grade_table.grades_d)
        # Set subject names and grades
        allvals = self.calc.all_values()
        for tag, val in allvals:
            if tag[0] != '*':
                self.set_text_init(tag, val)
        self.update_calc()
#
    def update_calc(self):
        """Update all the calculated parts of the grid from the current
        grades.
        """
        for tag, val in self.calc.calculate().items():
            try:
                self.set_text(tag, val)
            except:
                pass
#                print("NO FIELD:", tag)
#
    def save_changes(self):
        """Collect the fields to be saved and pass them to the
        <GradeTable> method.
        """
        if self.changes():
            pgtable = self.grade_table[self.pid]
            pgtable.set_grade('*F_D', self.calc.value('FERTIG_D'))
            for s, g in self.calc.get_all_grades():
                pgtable.set_grade(s, g)
#TODO: also '*ZA'?
            self.grade_table.save()


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    from core.base import init
    init('TESTDATA')

    _year = '2016'

    import sys
    from qtpy.QtWidgets import QApplication, QStyleFactory
    from qtpy.QtCore import QLocale, QTranslator, QLibraryInfo

#    print(QStyleFactory.keys())
#    QApplication.setStyle('windows')

    app = QApplication(sys.argv)
    LOCALE = QLocale(QLocale.German, QLocale.Germany)
    QLocale.setDefault(LOCALE)
    qtr = QTranslator()
    qtr.load("qt_" + LOCALE.name(),
            QLibraryInfo.location(QLibraryInfo.TranslationsPath))
    app.installTranslator(qtr)

    ge = _GradeEdit()
#    ge.set_table(year_path(_year, 'NOTEN/Noten_13_A.xlsx'))
#    ge.set_table(os.path.join(DATA, 'testing', 'NOTEN', 'Noten_13_A.xlsx'))
    ge.set_table(_year, '13', 'A')
    ge.exec_()

