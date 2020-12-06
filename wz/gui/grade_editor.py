# -*- coding: utf-8 -*-
"""
gui/grade_editor.py

Last updated:  2020-12-06

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

_SCHULJAHR = "Schuljahr:"
_TERM = "Anlass:"
_GROUP = "Klasse/Gruppe:"
#####################################################


import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

from qtpy.QtWidgets import QApplication, QDialog, \
    QHBoxLayout, QVBoxLayout, QLabel, QPushButton

from gui.grade_grid import GradeGrid
from gui.gui_support import VLine, KeySelect#, ZIcon
from core.base import Dates
from local.base_config import print_schoolyear
from local.grade_config import GradeBase

###

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
        cbox.addWidget(QLabel(_SCHULJAHR))
        cbox.addWidget(self.year_select)

        self.term_select = KeySelect(GradeBase.terms(), self.term_changed)
        cbox.addWidget(QLabel(_TERM))
        cbox.addWidget(self.term_select)

        ### Select group (might be just one entry ... perhaps even none)
        self.group_select = KeySelect(changed_callback = self.group_changed)
        cbox.addWidget(QLabel(_GROUP))
        cbox.addWidget(self.group_select)

        ### List of pupils – not for term 1, 2?
        self.pselect = KeySelect(changed_callback = self.pupil_changed)
        self.pselect.setMaximumWidth(150)
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
        self.year_select.trigger()
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
                for grp, rtype in GradeBase.term2group_rtype_list(key[0])]
        print("Change Category:", key, [grp[0] for grp in groups])
        self.gradeView.clear()
        self.group_select.set_items(groups)
        self.group_select.trigger()






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

