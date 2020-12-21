# -*- coding: utf-8 -*-
"""
gui/grade_editor.py

Last updated:  2020-12-21

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

### Labels, etc.
_TITLE = "WZ: Noten"
_PUPIL = "Schüler"
_STREAM = "Maßstab"
_ALL_PUPILS = "Gesamttabelle"
_NEW_REPORT = "Neues Zeugnis"

_SCHULJAHR = "Schuljahr:"
_TERM = "Anlass:"
_GROUP = "Klasse/Gruppe:"
_SAVE = "Änderungen speichern"
_TABLE_PDF = "Tabelle als PDF"
_REPORT_PDF = "Zeugnis(se) erstellen"
#####################################################


import sys, os, glob
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

from qtpy.QtWidgets import QApplication, QDialog, \
    QHBoxLayout, QVBoxLayout, QLabel, QPushButton

from gui.grid import GridView
from gui.grade_grid import GradeGrid
from gui.abitur_pupil_view import AbiPupilView
from gui.gui_support import VLine, KeySelect#, ZIcon
from core.base import Dates
from local.base_config import print_schoolyear, year_path
from local.grade_config import GradeBase

###

class GView(GridView):
    def set_changed(self, show):
        self.pbSave.setEnabled(show)

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
        self.gradeView = GView()
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

        cbox.addSpacing(30)
        self.gradeView.pbSave = QPushButton(_SAVE)
        cbox.addWidget(self.gradeView.pbSave)
        self.gradeView.pbSave.clicked.connect(self.save)

        cbox.addStretch(1)
        pbReport = QPushButton(_REPORT_PDF)
        cbox.addWidget(pbReport)
        pbReport.clicked.connect(self.make_reports)
        pbPdf = QPushButton(_TABLE_PDF)
        cbox.addWidget(pbPdf)
        pbPdf.clicked.connect(self.print_table)
        topbox.addLayout(cbox)

# after "showing"?
#        pbSmaller.setFixedWidth (pbSmaller.height ())
#        pbLarger.setFixedWidth (pbLarger.height ())

#
    def closeEvent(self, e):
        self.gradeView.clear()
        super().closeEvent(e)
#
    def init(self):
        years = [(y, print_schoolyear(y)) for y in Dates.get_years()]
        self.year_select.set_items(years)
#        self.gradeView.clear()
        self.year_select.trigger()
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
#        self.gradeView.clear()
        self.group_select.set_items(groups)
        self.group_select.trigger()
#
    def group_changed(self, group):
        # Needed to call <leaving> before (re)loading the grade table:
        self.gradeView.clear()
        self.group = group
#        self.pselect.setVisible(False)
        self.group_scene = GradeGrid(self.gradeView, self.schoolyear,
                self.group, self.term)
        self.gradeView.set_scene(self.group_scene)
        self.grade_scene = self.group_scene
        self.pupil_scene = None
        if self.term[0] == 'S':
            # Get list of existing reports for the group
            table_path = year_path(self.schoolyear,
                    GradeBase.table_path(group, 'S*'))
            date_list = [f.rsplit('_', 1)[1].split('.', 1)[0]
                    for f in glob.glob(table_path)]
            plist = [('', _NEW_REPORT)] + [('S' + d, d) for d in date_list]
        else:
            plist = [('', _ALL_PUPILS)] + self.grade_scene.pupils()
        self.pselect.set_items(plist)
#
    def pupil_changed(self, pid):
        """A new pupil has been selected: reset the grid accordingly.
        """
        self.pid = pid
        print("SELECT Pupil:", pid)
        if pid:
            if self.term == 'A':
                self.gradeView.clear()
                if not self.pupil_scene:
                    self.pupil_scene = AbiPupilView(self.gradeView,
                            self.schoolyear, self.group)
                    self.grade_scene = self.pupil_scene
                self.gradeView.set_scene(self.pupil_scene)
                self.pupil_scene.set_pupil(pid)
                return

#TODO
            else:
                pass

                self.gradeView.clear()
        else:
            self.group_changed(self.group)
        return
#
#?
    def update_calc(self):
        """Update all the calculated parts of the grid from the current
        grades.
        """
        for tag, val in self.calc.calculate().items():
            try:
                self.grade_scene.tagmap[tag].setText(val)
            except:
                pass
#                print("NO FIELD:", tag)
#
    def save(self):
        self.grade_scene.save_changes()
        self.grade_scene.clear_changes()
#
    def make_reports(self):
        """Generate the grade report(s).
        """
        print("TODO: make_reports")

#
    def print_table(self):
        """Output the table as pdf.
        """
        if self.grade_scene:
            self.grade_scene.to_pdf()


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

