# -*- coding: utf-8 -*-
"""
gui/grade_editor.py

Last updated:  2020-12-03

Editor for grades.


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


_TITLE = "WZ: Noten"
_PUPIL = "Schüler"
_STREAM = "Maßstab"

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

from gui.grid import Grid, CellStyle, PopupDate, PopupTable
from gui.gui_support import VLine, KeySelect#, ZIcon
from core.base import Dates
from grades.gradetable import GradeTable, Grades
from local.base_config import FONT, print_schoolyear, SCHOOL_NAME, year_path

## Measurements are in mm ##
COLUMNS = (35, 15, 15, 2) # + 8 * n ... further separators?
# The info values could need more space than just the 3rd column ...

# Specify widths of special columns explicitly:
COL_WIDTH = {
    ':D': 10,
    ':Dx': 10,
    '*ZA': 30,
    '*Q': 8,
    '*F_D': 20,
}

ROWS = (
#title
    12,
# info rows
    6, 6, 6, 6, 6, 6,
# header (tags)
    6, 2
) # + 6 * n

###

class GradeGrid(Grid):
#
    def styles(self):
        """Set up the styles used in the table view.
        """
        self.new_style('base', font = FONT, size = 11)
        self.new_style('title', font = FONT, size = 12, align = 'l',
                    border = 0, highlight = 'b')
        self.new_style('info', base = 'base', border = 0, align = 'l')
        self.new_style('underline', base = 'base', border = 2)
        self.new_style('titleR', base = 'title', align = 'r')
        self.new_style('small', base = 'base', size = 10)
        self.new_style('v', base = 'small', align = 'b')
        self.new_style('h', base = 'small', border = 0)
        self.new_style('entry', base = 'base', highlight = ':2a6099',
                mark = 'E00000')

    def set_table(self, schoolyear, group, term):
        """Set the grade table (a <GradeTable> instance) to be used.
        Set up the grid accordingly.
        """
        self.cell_callback = 'TODO'

        self.grade_table = GradeTable.group_table(schoolyear, group, term,
                ok_new = True)

#        print("$$$ pupils:", len(self.grade_table))
#        print("$$$ subjects:", self.grade_table.subjects) # real subjects

        # Get number of rows and columns from <grade_table>
        row_pids = len(ROWS)
        _ROWS = ROWS + (6,) * len(self.grade_table)
        col_sids = len(COLUMNS)
        _nsids = len(self.grade_table.subjects)
        _ncomps = len(self.grade_table.composites)
        _COLS = COLUMNS + (8,) * _nsids
        col_composites = len(_COLS) + 1
        if _ncomps:
            _COLS += (2,) + (8,) * _ncomps
        col_averages = len(_COLS) + 1
# The averages are only used in the grade editor ...
        averages = Grades.averages(group)
        if averages:
            _COLS += (2,)
            for x in averages:
                _COLS += (COL_WIDTH[x],)
        col_extras = len(_COLS) + 1
        if self.grade_table.extras:
            _COLS += (2,)
            for x in self.grade_table.extras:
                _COLS += (COL_WIDTH[x],)

        self.setTable(_ROWS, _COLS)
        self.styles()

        ### Cell editors
        # These are attached to the scene, so a new table (which starts
        # a new scene) begins with no cell editors.
        edit_grade = PopupTable(self, Grades.group_info(group, 'NotenWerte'))
        edit_date = PopupDate(self)
#TODO: add editors for extra fields

        ### Title area
        self.tile(0, 0, text = "Notentabelle", cspan = 2, style = 'title')
        self.tile(0, 4, text = SCHOOL_NAME, cspan = 10, style = 'titleR')
        ### General Info
        self.tile(1, 0, text = self.grade_table.SCHOOLYEAR, style = 'info')
        self.tile(1, 1, text = self.grade_table.schoolyear,
                cspan = 2, style = 'info')
        self.tile(2, 0, text = self.grade_table.GROUP, style = 'info')
        self.tile(2, 1, text = self.grade_table.group,
                cspan = 2, style = 'info')
        self.tile(3, 0, text = self.grade_table.TERM, style = 'info')
        self.tile(3, 1, text = Grades.term2text(self.grade_table.term),
                cspan = 2, style = 'info')
        # These are editable dates:
        self.tile(4, 0, text = self.grade_table.ISSUE_D, style = 'info')
        self.tile(4, 1, text = self.grade_table.issue_d,
                cspan = 2, style = 'info',
                validation = edit_date, tag = 'ISSUE_D')
        self.tile(5, 0, text = self.grade_table.GRADES_D, style = 'info')
        self.tile(5, 1, text = self.grade_table.grades_d,
                cspan = 2, style = 'info',
                validation = edit_date, tag = 'GRADES_D')

        # Subject lines
        self.tile(7, 0, text = _PUPIL, cspan = 2, style = 'small')
        self.tile(7, 2, text = _STREAM,  style = 'small')
        col = col_sids
        for sid, name in self.grade_table.subjects.items():
            self.tile(7, col, text = sid, style = 'small')
            self.tile(1, col, text = name, rspan = 6, style = 'v')
            col += 1

        col = col_composites
        for sid, name in self.grade_table.composites.items():
            self.tile(7, col, text = sid, style = 'small')
            self.tile(1, col, text = name, rspan = 6, style = 'v')
            col += 1

        col = col_averages
        for sid, name in averages.items():
            self.tile(7, col, text = sid, style = 'small')
            self.tile(1, col, text = name, rspan = 6, style = 'v')
            col += 1

        col = col_extras
        for sid, name in self.grade_table.extras.items():
            self.tile(7, col, text = sid, style = 'small')
            self.tile(1, col, text = name, rspan = 6, style = 'v')
            col += 1

#TODO: pupil lines


#
    def valueChanged(self, tag, text):
        """Called when a cell value is changed by the editor.
        """
        self.cell_callback(tag, text)
#
    def average(self, pid):
        """Calculate the average of all grades, including composites,
        but ignoring components and non-numerical grades.
        """
        asum = 0
        ai = 0
        grades = self.grade_table[pid]
        for sid in self.grade_table.subjects:
            if self.grade_table.sid2subject_data[sid].composite:
                # A component
                continue
            try:
                gi = grades.i_grade[sid]
            except KeyError:
                continue
            asum += gi
            ai += 1
        for sid in self.grade_table.composites:
            try:
                gi = grades.i_grade[sid]
            except KeyError:
                continue
            asum += gi
            ai += 1
        if ai:
            return Frac(asum, ai).round()
        else:
            return '–––'
#
    def average_dem(self, pid):
        """Special average for "Realschulabschluss": De-En_Ma only.
        """
        asum = 0
        ai = 0
        grades = self.grade_table[pid]
        for sid in ('De', 'En', 'Ma'):
            try:
                gi = grades.i_grade[sid]
            except KeyError:
                continue
            asum += gi
            ai += 1
        if ai:
            return Frac(asum, ai).round()
        else:
            return '–––'




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
        self.gradeView = GradeGrid()
        topbox.addWidget(self.gradeView)

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
        self.year_select = KeySelect(changed_callback = self.year_changed)
        self.term_select = KeySelect(Grades.terms(), self.term_changed)

        ### Select group (might be just one entry ... perhaps even none)
        self.group_select = KeySelect(changed_callback = self.group_changed)

        ### List of pupils – not for term 1, 2?
        self.pselect = KeySelect(changed_callback = self.pupil_changed)
        self.pselect.setMaximumWidth(150)
        cbox.addWidget(self.year_select)
        cbox.addWidget(self.term_select)
        cbox.addWidget(self.group_select)
        cbox.addWidget(self.pselect)
        cbox.addStretch(1)
        pbPdf = QPushButton('PDF')
        cbox.addWidget(pbPdf)
        pbPdf.clicked.connect(self.gradeView.toPdf)
        topbox.addLayout(cbox)
#        self.year_select.trigger()
#        self.term_select.trigger()

# after "showing"?
#        pbSmaller.setFixedWidth (pbSmaller.height ())
#        pbLarger.setFixedWidth (pbLarger.height ())

#TODO: at certain changes the scene should probably be cleared!
# Maybe at any change!

#
    def init(self):
        years = [(y, print_schoolyear(y)) for y in Dates.get_years()]
        self.year_select.set_items(years)
#        self.gradeView.clear()
#        self.year_select.trigger()
#
    def group_changed(self, group):
        print("Change Group:", group)
        self.group = group
        self.gradeView.set_table(self.schoolyear, self.group, self.term)
#
    def year_changed(self, schoolyear):
        print("Change Year:", schoolyear)
        self.schoolyear = schoolyear
#        self.gradeView.clear()
        self.term_select.trigger()
#
    def term_changed(self, key):
        self.term = key
        groups = [(grp, grp)
                for grp, rtype in Grades.term2group_rtype_list(key)]
        print("Change Category:", key, [grp[0] for grp in groups])
        self.gradeView.clear()
        self.group_select.set_items(groups)
#        self.group_select.trigger()






#        if key == 'A':
#            self.grade_edit.addWidget(self.gradeView)
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

    def set_table0(self, schoolyear, group, term):
        """Set the grade table to be used.
        <fpath> is the full path to the table file (see <GradeTable>).
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


#TODO: Updating database ... (save button? ... or immediate update?)

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
                self.calc.grade_map['X_FERTIG_D'] or self.grade_table.grades_d)
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
    ge.init()

#    ge.set_table(year_path(_year, 'NOTEN/Noten_13_A.xlsx'))
#    ge.set_table(os.path.join(DATA, 'testing', 'NOTEN', 'Noten_13_A.xlsx'))
#    ge.gradeView.set_table(_year, '12.R', '2')
    ge.exec_()

