# -*- coding: utf-8 -*-
"""
gui/abitur_grid.py

Last updated:  2021-01-05

Editor for Abitur results.


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

##### Configuration
_TITLE = "Abitur-Ergebnisse"

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


#####################################################


import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

from qtpy.QtWidgets import QApplication, QDialog, QStackedWidget, \
    QHBoxLayout, QVBoxLayout, QPushButton
#from qtpy.QtGui import QFont
#from qtpy.QtCore import Qt

from gui.grid import Grid, PopupDate, PopupTable
from gui.gui_support import VLine, KeySelect#, ZIcon
from grades.gradetable import GradeTable, Grades
from local.base_config import print_schoolyear#, year_path
from local.abitur_config import AbiCalc


class AbiturGrid(Grid):
    def styles(self):
        """Set up the styles used in the table view.
        """
        self.new_style('base', font = SCHOOL_DATA.FONT, size = 11)
        self.new_style('info', base = 'base', border = 0)
        self.new_style('infoL', base = 'info', align = 'l')
        self.new_style('label', base = 'infoL', highlight = 'b')

        self.new_style('title', font = SCHOOL_DATA.FONT, size = 12,
                align = 'l', border = 0, highlight = 'b')
        self.new_style('titleR', base = 'title', align = 'r')
        self.new_style('underline', base = 'base', border = 2)
        self.new_style('small', base = 'base', size = 10)
        self.new_style('v', base = 'small', align = 'm')
        self.new_style('h', base = 'small', border = 0)
        self.new_style('entry', base = 'base', highlight = ':2a6099',
                mark = 'E00000')
        self.new_style('resultL', base = 'title', border = 2)
        self.new_style('result', base = 'resultL', align = 'c')
        self.new_style('date', base = 'result', highlight = ':2a6099',
                mark = 'E00000')
#
    def __init__(self, callback_value_changed):
        super().__init__()
        self.callback_changed = callback_value_changed

        self.setTable(ROWS, COLUMNS)
        self.styles()
        ### Cell editors
#TODO: add '*' to list for "Nachprüfungen"
        edit_grade = PopupTable(self, VALID_GRADES)
        edit_date = PopupDate(self)

        ### Title area
        self.tile(0, 0, text = "Abitur-Berechnungsbogen", cspan = 4,
                style = 'title')
        self.tile(0, 4, text = SCHOOL_DATA.SCHOOL_NAME, cspan = 10,
                style = 'titleR')
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
                    validation = edit_grade, tag = "GRADE_%s" % istr)
            self.tile(row0 + 1, 4, text = '', style = 'entry',
                    validation = edit_grade, tag = "GRADE_%s_m" % istr)
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
                    validation = edit_grade, tag = "GRADE_%s" % istr)
            self.tile(row0, 6, text = '', style = 'base',
                    tag = "AVERAGE_%s" % istr)
            self.tile(row0, 7, text = "X", style = 'info')
            self.tile(row0, 8, text = "4", style = 'info')
            self.tile(row0, 9, text = '', style = 'underline',
                    tag = "SCALED_%s" % istr)

        ### Totals
        self.tile(11, 11, text = '', rspan = 11, style = 'base',
                    tag = "TOTAL_1-4")
        self.tile(24, 11, text = '', rspan = 7, style = 'base',
                    tag = "TOTAL_5-8")

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
                validation = edit_date, tag = "FERTIG_D")
#TODO: Do I want to display the date in local format? If so, I would need
# to adjust the popup editor ...
#
    def valueChanged(self, tag, text):
        """Called when a cell value is changed by the editor.
        """
        self.callback_changed(tag, text)


###########################################

class _GradeEdit(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(_TITLE)
        screen = QApplication.instance().primaryScreen()
#        ldpi = screen.logicalDotsPerInchY()
        screensize = screen.availableSize()
        self.resize(screensize.width()*0.8, screensize.height()*0.8)
#TODO: It might be more desirable to adjust to the scene size.

# Class select and separate stream select?
        topbox = QHBoxLayout(self)
#        self.gridtitle = QLabel ("GRID TITLE")
#        self.gridtitle.setAlignment (Qt.AlignCenter)

#*********** The "main" widget ***********
# This should perhaps be a QGraphicsView, whose scene can be set as required?
        self.grade_edit = QStackedWidget()
        topbox.addWidget(self.grade_edit)

        self.gradeView = AbiturGrid(self.cell_changed)
#        topbox.addWidget(self.gradeView)

        topbox.addWidget(VLine())

#        self.gradeView.setToolTip ('This shows the <b>grades</b> for a class')
#        bbox = QHBoxLayout()
#        pbSmaller = QPushButton(ZIcon('zoom-out'), '')
#        pbSmaller.clicked.connect(self.gradeView.scaleDn)
#        pbLarger = QPushButton(ZIcon('zoom-in'), '')
#        pbLarger.clicked.connect(self.gradeView.scaleUp)
#        bbox.addWidget(pbLarger)
#        bbox.addWidget(pbSmaller)

        cbox = QVBoxLayout()
#        cbox.addLayout(bbox)
#        self.yearSelect = KeySelect([(y, print_schoolyear(y))
#                for y in Dates.get_years()],
#                self.changedYear)
        self.term_select = KeySelect(Grades.terms(), self.term_changed)

        ### Select group (might be just one entry ...)
#TODO: classes
        self.group_select = KeySelect([('13', 'Klasse 13')],
                self.changedGroup)
        self.group_select

        ### List of pupils
        self.pselect = KeySelect(changed_callback = self.pupil_changed)
        self.pselect.setMaximumWidth(150)
#        cbox.addWidget(self.yearSelect)
        cbox.addWidget(self.term_select)
        cbox.addWidget(self.group_select)
        cbox.addWidget(self.pselect)
        cbox.addStretch(1)
        pbPdf = QPushButton('PDF')
        cbox.addWidget(pbPdf)
        pbPdf.clicked.connect(self.gradeView.toPdf)
        topbox.addLayout(cbox)
#        self.yearSelect.trigger()

# after "showing"?
#        pbSmaller.setFixedWidth (pbSmaller.height ())
#        pbLarger.setFixedWidth (pbLarger.height ())

    def changedGroup(self, group):
        pass

#    def changedYear(self, schoolyear):
#        print("Change Year:", schoolyear)
#        self.schoolyear = schoolyear
## clear main view?
#        self.categorySelect.trigger()


    def term_changed(self, key):
        print("Change Category:", key)
        if key == 'A':
            self.grade_edit.addWidget(self.gradeView)
##TODO: choices -> ???
##        categories = Grades.categories()
#
#
##        self.choices = GRADE_REPORT_CATEGORY[key]
#        self.pselect.clear()
#
#        if key == 'A':
#            # Abitur, examination results
#            pass
#        elif key == 'S':
#            # A non-scheduled report
#            pass
#        else:
#            ### A term report, select the pupil group.
#            # Get a list of (group, default-report-type) pairs for this term.
#            # (Note that this will fail for 'A' and 'S'.)
#            self.group_choices = term2group_rtype_list(key)
#
#            self.select.addItems([g for g, _ in self.group_choices])
## This doesn't initially select any entry


#    def set_table(self, fpath):
#        read_grade_table(fpath)

    def set_table(self, schoolyear, group, term):
        """Set the grade table to be used.
        """
        self.grade_table = GradeTable.group_table(schoolyear, group, term,
                ok_new = True)
        self.gradeView.tagmap['SCHOOLYEAR'].setText(
                print_schoolyear(self.grade_table.schoolyear))
        self.pselect.set_items([(pid, self.grade_table.name[pid])
                for pid, grades in self.grade_table.items()])

#        print("\n*** READING: %s.%s, class %s, teacher: %s" % (
#                self.grade_table.schoolyear, self.grade_table.term or '-',
#                self.grade_table.klass, self.grade_table.tid))
#        print("~~~ ISSUE_D: %s, GRADES_D: %s" % (self.grade_table.issue_d,
#                self.grade_table.grades_d))
#        print("~~~ Subjects:", self.grade_table.subjects)
#
#        for pid, grades in self.grade_table.items():
#            print("\n ::: %s (%s):" % (self.grade_table.name[pid],
#                    self.grade_table.stream[pid]), grades)


#TODO: Updating "database" ... (save button? ... or immediate update?)

    def pupil_changed(self, pid):
        """A new pupil has been selected: reset the grid accordingly.
        """
        self.pid = pid
        self.changes = set()    # set of changed cells
        # Set pupil's name (NAME) and completion date (FERTIG_D)
        name = self.grade_table.name[pid]
        self.gradeView.tagmap['NAME'].setText(name)
        self.calc = AbiCalc(self.grade_table, pid)
        # Set date of completion: if no value for pupil, use group date
        self.calc.set_editable_cell('FERTIG_D',
                self.calc.grade_map['*F_D'] or self.grade_table.grades_d)
        # Set subject names and grades
        for tag, val in self.calc.tags.items():
            self.gradeView.tagmap[tag].setText(val)
        self.update_calc()
#
    def update_calc(self):
        """Update all the calculated parts of the grid from the current
        grades.
        """
        for tag, val in self.calc.calculate().items():
            try:
                self.gradeView.tagmap[tag].setText(val)
            except:
                pass
#                print("NO FIELD:", tag)
#
    def cell_changed(self, tag, value):
        """Called when a cell is edited.
        """
        try:
            old = self.calc.tags0[tag]
        except KeyError:
            raise Bug("Unexpected cell change, %s: %s" % (tag, value))
        if value == old:
            self.changes.discard(tag)
            self.gradeView.tagmap[tag].mark(False)
        else:
            self.changes.add(tag)
            self.gradeView.tagmap[tag].mark(True)
        if tag.startswith('GRADE_'):
            self.calc.tags[tag] = value
            self.update_calc()
        elif tag == 'FERTIG_D':
            print("NEW DATE:", value)
        else:
            raise Bug("Invalid cell change, %s: %s" % (tag, value))
#
#TODO: This might need some tweaking ... unless the <GradeTable> is a
# subclass especially for Abitur.
    def save_changes(self):
        """Collect the fields to be saved and pass them to the
        <GradeTable> method.
        """
        full_grade_list = self.calc.get_all_grades()
        fertig_d = self.calc.tags['FERTIG_D']
#TODO: method <update_pupil>
        self.grade_table.update_pupil(self.pid, full_grade_list, fertig_d)


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    from core.base import init
    init()

    _year = '2016'

    import sys
    from qtpy.QtWidgets import QApplication#, QStyleFactory
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

