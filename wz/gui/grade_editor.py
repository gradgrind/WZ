# -*- coding: utf-8 -*-
"""
gui/grade_editor.py

Last updated:  2021-01-02

Editor for grades.

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
_SAVE_FAILED = "Speicherung der Änderungen ist fehlgeschlagen:\n  {msg}"
_MADE_REPORTS = "Notenzeugnisse erstellt"
_NO_REPORTS = "Keine Notenzeugnisse erstellt"
_NOT_INTERRUPTABLE = "+++ Der Prozess kann nicht unterbrochen werden +++"

### Labels, etc.
_EDIT_GRADES = "Noten verwalten"
_ALL_PUPILS = "Gesamttabelle"
_NEW_REPORT = "Neues Zeugnis"
_TERM = "Anlass:"
_GROUP = "Klasse/Gruppe:"
_SAVE = "Änderungen speichern"
_TABLE_XLSX = "Noteneingabe-Tabelle"
_TABLE_PDF = "Tabelle als PDF"
_REPORT_PDF = "Zeugnis(se) erstellen"
_TABLE_IN1 = "Notentabelle einlesen"
_TABLE_IN_DIR = "Notentabellen einlesen"
_FILESAVE = "Datei speichern"
_EXCEL_FILE = "Excel-Datei (*.xlsx)"

#####################################################

import sys, os, glob

from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, \
        QPushButton, QFileDialog

from core.base import Dates, ThreadFunction
from gui.grid import GridView
from gui.grade_grid import GradeGrid
from gui.abitur_pupil_view import AbiPupilView
from gui.gui_support import VLine, KeySelect, TabPage
from local.base_config import print_schoolyear, year_path
from local.grade_config import GradeBase
from grades.gradetable import FailedSave
from grades.makereports import GradeReports

###

class GView(GridView):
    def set_changed(self, show):
        self.pbSave.setEnabled(show)

###

class GradeEdit(TabPage):
    def __init__(self):
        super().__init__(_EDIT_GRADES)
        topbox = QHBoxLayout()
        self.vbox.addLayout(topbox)

        #*********** The "main" widget ***********
        self.gradeView = GView()
        self.grade_scene = None
        topbox.addWidget(self.gradeView)
        topbox.addWidget(VLine())

        cbox = QVBoxLayout()

        self.term_select = KeySelect(GradeBase.terms(), self.term_changed)
        cbox.addWidget(QLabel(_TERM))
        cbox.addWidget(self.term_select)

        ### Select group (might be just one entry ... perhaps even none)
        self.group_select = KeySelect(changed_callback = self.group_changed)
        cbox.addWidget(QLabel(_GROUP))
        cbox.addWidget(self.group_select)

        ### List of pupils
#TODO: not for term 1, 2?
        self.pselect = KeySelect(changed_callback = self.pupil_changed)
        cbox.addWidget(self.pselect)

        cbox.addSpacing(30)
        self.gradeView.pbSave = QPushButton(_SAVE)
        cbox.addWidget(self.gradeView.pbSave)
        self.gradeView.pbSave.clicked.connect(self.save)
        cbox.addStretch(1)
        pbTable = QPushButton(_TABLE_XLSX)
        cbox.addWidget(pbTable)
        pbTable.clicked.connect(self.make_table)
        cbox.addSpacing(10)
        pbTableIn1 = QPushButton(_TABLE_IN1)
        cbox.addWidget(pbTableIn1)
        pbTableIn1.clicked.connect(self.input_table)
        pbTableInDir = QPushButton(_TABLE_IN_DIR)
        cbox.addWidget(pbTableInDir)
        pbTableInDir.clicked.connect(self.input_tables)
        cbox.addSpacing(30)
        pbPdf = QPushButton(_TABLE_PDF)
        cbox.addWidget(pbPdf)
        pbPdf.clicked.connect(self.print_table)
        cbox.addSpacing(10)
        pbReport = QPushButton(_REPORT_PDF)
        cbox.addWidget(pbReport)
        pbReport.clicked.connect(self.make_reports)
        topbox.addLayout(cbox)
#
    def clear(self, force = False):
        """Check for changes in the current "scene", allowing these to
        be saved if desired, then clear the scene.
        """
        try:
            self.gradeView.clear(force)
        except FailedSave as e:
            REPORT(_SAVE_FAILED.format(msg = e))
            return False
        return True
#
    def enter(self):
        self.year_changed()
#
    def leave(self):
        self.clear()
        self.grade_scene = None
#
    def year_changed(self):
        if not self.clear():
            self.year_select.reset(ADMIN.schoolyear)
            return
        self.term_select.trigger()
#
    def term_changed(self, key):
        if not self.clear():
            self.term_select.reset(self.term)
            return
        self.term = key
        groups = [(grp, grp)
                for grp, rtype in GradeBase.term2group_rtype_list(key[0])]
        self.group_select.set_items(groups)
        self.group_select.trigger()
#
    def group_changed(self, group):
        if group:
            if not self.clear():
                self.group_select.reset(self.group)
                return
            self.group = group
            self.pid = ''
#        self.pselect.setVisible(False)
        if self.term[0] == 'S':
            self.term = self.pid if self.pid else 'S*'
            # Get list of existing reports for the group
            table_path = year_path(ADMIN.schoolyear,
                    GradeBase.table_path(self.group, 'S*'))
            date_list = sorted([f.rsplit('_', 1)[1].split('.', 1)[0]
                    for f in glob.glob(table_path)], reverse = True)
            if group and date_list:
                # Show next date
                today = Dates.today()
                for date in date_list:
                    if today > date:
                        break
                    # Select this date initially
                    self.pid = 'S' + latest
                    self.term = self.pid
            self.grade_scene = GradeGrid(self.gradeView, ADMIN.schoolyear,
                    self.group, self.term)
            plist = [('', _NEW_REPORT)] + [('S' + d, d) for d in date_list]
        else:
            self.grade_scene = GradeGrid(self.gradeView, ADMIN.schoolyear,
                    self.group, self.term)
            plist = [('', _ALL_PUPILS)] + self.grade_scene.pupils()
        self.pselect.set_items(plist)
        if self.pid:
            self.pselect.reset(self.pid)
        self.gradeView.set_scene(self.grade_scene)
#
    def pupil_changed(self, pid):
        """A new pupil has been selected: reset the grid accordingly.
        """
        if not self.clear():
            self.pselect.reset(self.pid)
            return
        self.pid = pid
        if pid:
            if self.term == 'A':
                self.grade_scene = AbiPupilView(self.gradeView,
                        ADMIN.schoolyear, self.group)
                self.gradeView.set_scene(self.grade_scene)
                self.grade_scene.set_pupil(pid)
                return
            if self.term[0] != 'S':
#TODO:
                REPORT("TODO: Change pupil %s" % pid)
                return
        self.group_changed(None)
#
    def save(self, force = True):
        if self.clear(force):    # no question dialog
            if self.term[0] == 'S':
                self.pid = self.grade_scene.grade_table.term
            self.group_changed(None)
#
    def make_table(self):
        """Generate input table for the grades.
        """
        self.save(force = False)
        gtable = self.grade_scene.grade_table
        qbytes = gtable.make_grade_table()
        dir0 = ADMIN._savedir or os.path.expanduser('~')
        filename = os.path.basename(GradeBase.table_path(
                gtable.group, gtable.term)) + '.xlsx'
        fpath = QFileDialog.getSaveFileName(self.gradeView, _FILESAVE,
                os.path.join(dir0, filename), _EXCEL_FILE)[0]
        if fpath:
            ADMIN.set_savedir(os.path.dirname(fpath))
            with open(fpath, 'wb') as fh:
                fh.write(bytes(qbytes))
#
    def input_table(self):
        """Import a single grade table, replacing the internal table.
        """
#TODO
        fn = ThreadFunction()
#        qp = ProgressMessages(fn)
        cc = REPORT('RUN', runme = fn)
        if cc:
            REPORT("ERROR: Interrupted")
        else:
            REPORT("INFO: Completed")
        print("TODO: input_table")

#
    def input_tables(self):
        """Import a folder of grade tables, replacing affected internal
        tables.
        """
#TODO
        REPORT("INFO: <input_tables> needs doing.")
        REPORT("WARN: <input_tables> is not yet implemented.")
        REPORT("ERROR: <input_tables> is still not yet implemented.")
        print("TODO: input_tables")

#
    def make_reports(self):
        """Generate the grade report(s).
        """
        self.save(force = False)
        greports = GradeReports(ADMIN.schoolyear, self.group, self.term)
        fn = _MakeReports(greports)
        files = REPORT('RUN', runme = fn)
        if files:
            REPORT("INFO: %s:\n  --> %s" % (_MADE_REPORTS,
                '\n  --> '.join(files)))
        else:
            REPORT("ERROR: %s" % _NO_REPORTS)
#
    def print_table(self):
        """Output the table as pdf.
        """
        self.save(force = False)
        if self.grade_scene:
            self.grade_scene.to_pdf()

###

class _MakeReports(ThreadFunction):
    def __init__(self, grade_reports):
        super().__init__()
        self._grade_reports = grade_reports

    def run(self):
        return self._grade_reports.makeReports()

    def terminate(self):
        self.message(_NOT_INTERRUPTABLE)
