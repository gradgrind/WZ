# -*- coding: utf-8 -*-
"""
ui/tab_grade_editor.py

Last updated:  2021-02-22

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

#TODO ...


### Messages
_MADE_REPORTS = "Notenzeugnisse erstellt"
_NO_REPORTS = "Keine Notenzeugnisse erstellt"
_NOT_INTERRUPTABLE = "+++ Der Prozess kann nicht unterbrochen werden +++"

_TITLE_TABLE_REPLACE = "Neue Tabelle speichern"
# Would need to be a bit different for individual pupils:
_TABLE_REPLACE = "Die neue Tabelle wird die alte ersetzen.\n" \
        "Soll sie jetzt gespeichert werden?"
_NO_GRADE_FILES = "Keine Tabellen zur Aktualisierung"
_BAD_GRADE_FILE = "Ungültige Tabellendatei:\n  {fpath}"
_UPDATED_GRADES = "Notentabelle aktualisiert: {n} Quelldatei(en)"
_GRADE_TABLE_MISMATCH = "{error}:\n  Jahr: {year}, Gruppe: {group}," \
        " Anlass: {term}"

### Labels, etc.
_EDIT_GRADES = "Noten verwalten"
_TERM = "Anlass:"
_GROUP = "Klasse/Gruppe:"
_SAVE = "Änderungen speichern"
_TABLE_XLSX = "Noteneingabe-Tabelle\nerstellen"
_TT_TABLE_XLSX = "Tabelle der unterrichteten Fächer als xlsx-Datei erstellen"
_TABLE_PDF = "Tabelle als PDF"
_REPORT_PDF = "Zeugnis(se) erstellen"
_TABLE_IN1 = "Notentabelle ersetzen,\n externe einlesen"
_TT_TABLE_IN1 = "Ersetze die Notentabelle durch die gewählte Datei" \
        " (xlsx, ods, tsv)"
_TABLE_IN_DIR = "Noten aktualisieren,\n von externem Ordner"
_TT_TABLE_IN_DIR = "Aktualisiere die Notentabelle von den Dateien" \
        " (xlsx, ods, tsv) im gewählten Ordner"
_FILESAVE = "Datei speichern"
_FILEOPEN = "Datei öffnen"
_DIROPEN = "Ordner öffnen"
_EXCEL_FILE = "Excel-Datei (*.xlsx)"
_TABLE_FILE = "Tabellendatei (*.xlsx *.ods *.tsv)"

#####################################################

import os, glob

from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, \
        QPushButton, QFileDialog
from qtpy.QtCore import SIGNAL, QObject

from ui.grid import GridView
from ui.grade_grid import GradeGrid
from ui.abitur_pupil_view import AbiPupilView
from ui.ui_support import VLine, KeySelect, TabPage, QuestionDialog

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

        self.term_select = KeySelect(changed_callback = self.term_changed)
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
        # Special connection, see <self.save>
        QObject.connect(self.gradeView.pbSave, SIGNAL('clicked()'), self.save)
        cbox.addStretch(1)
        pbTable = QPushButton(_TABLE_XLSX)
        pbTable.setToolTip(_TT_TABLE_XLSX)
        cbox.addWidget(pbTable)
        pbTable.clicked.connect(self.make_table)
        cbox.addSpacing(10)
        pbTableIn1 = QPushButton(_TABLE_IN1)
        pbTableIn1.setToolTip(_TT_TABLE_IN1)
        cbox.addWidget(pbTableIn1)
        pbTableIn1.clicked.connect(self.input_table)
        pbTableInDir = QPushButton(_TABLE_IN_DIR)
        pbTableInDir.setToolTip(_TT_TABLE_IN_DIR)
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
    def clear(self):
        """Check for changes in the current "scene", allowing these to
        be discarded if desired. If accepted (or no changes), clear the
        "scene" and return <True>, otherwise leave the display unaffected
        and return <False>.
        """
        return self.gradeView.set_scene(None)
#
    def year_change_ok(self):
        return self.clear()
#

#TODO: On entering / year change / ... a whole train of events needs to
# be set in motion.

#TODO
    def enter(self):
        BACKEND('GRADES_init')
#
    def leave(self):
        if self.clear():
            # Drop the data structures associated with the grade view
            self.grade_scene = None
            return True
        else:
            return False
#
#    def year_changed(self):
#        if not self.clear():
#            self.year_select.reset(ADMIN.schoolyear)
#            return
#        self.term_select.trigger()
#
    def SET_TERMS(self, terms, term):
        """CALLBACK: Supplies the terms as a list of pairs:
            [[key1, term1], [key2, term2], ...]
        Also the selected term is passed. Set the term selection widget
        and trigger a "change of term" signal.
        """
        ix = 0
        for t, tdisp in terms:
            if term == t:
                break
            ix += 1
        self.term_select.set_items(terms, index = ix)
        self.term_select.trigger()
        return True
#
    def term_changed(self, key):
        if not self.clear():
            return False
        BACKEND('GRADES_set_term', term = key)
#?        self.term = key
        return True
#
#TODO: group to set?
    def SET_GROUPS(self, groups):
        glist = [(grp, grp) for grp in groups]
        self.group_select.set_items(glist)
        self.group_select.trigger()
#
    def group_changed(self, group):
        if not self.clear():
            return False
        BACKEND('GRADES_set_group', group = group)
        return True
#
    def SET_PUPILS(self, termx, group, pid_name_list, pid):
        self.pselect.set_items(pid_name_list)
        self.pselect.reset(pid)
#?        self.pselect.trigger()
#
    def SET_GRID(self, **parms):
        self.grade_scene = GradeGrid(self.gradeView, **parms)
        self.gradeView.set_scene(self.grade_scene)
#
    def SET_GRADES(self, grades):
        """<grades> is a list: [[pid, sid, val], ... ]
        """
        self.grade_scene.set_grades(grades)
#
    def pupil_changed(self, pid):
        """A new pupil has been selected: reset the grid accordingly.
        """
        if not self.clear():
            return False
        self.pid = pid
        if pid:
            if self.term == 'A':
                self.grade_scene = AbiPupilView(self.gradeView,
                        ADMIN.schoolyear, self.group)
                self.gradeView.set_scene(self.grade_scene)
                self.grade_scene.set_pupil(pid)
                return
            if self.term[0] not in ('S', 'T'):
#TODO:
                REPORT("TODO: Change pupil %s" % pid)
                return
        self.group_changed(None)
#
# Must connect to this specifying signal with no argument:
#  QObject.connect(button, SIGNAL('clicked()'), self.save)
    def save(self, force = True):
        if self.clear(force):    # no question dialog
            if self.term[0] in ('S', 'T'):
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
        self.clear()
        dir0 = ADMIN._loaddir or os.path.expanduser('~')
        fpath = QFileDialog.getOpenFileName(self.gradeView, _FILEOPEN,
                dir0, _TABLE_FILE)[0]
        if fpath:
            ADMIN.set_loaddir(os.path.dirname(fpath))
            gtable = GradeTableFile(ADMIN.schoolyear, fpath)
            # Check that it matches the currently selected group/term
            try:
                self.grade_scene.grade_table.check_group_term(gtable)
                # ... only returns if ok
            except GradeTableError as e:
                REPORT('ERROR', _GRADE_TABLE_MISMATCH.format(error = e,
                        year = gtable.schoolyear, group = gtable.group,
                        term = gtable.term))
            else:
                if QuestionDialog(_TITLE_TABLE_REPLACE, _TABLE_REPLACE):
                        gtable.save()       # save table
        # Redisplay table
        self.grade_scene = GradeGrid(self.gradeView, ADMIN.schoolyear,
                self.group, self.term)
        self.gradeView.set_scene(self.grade_scene)
#
    def input_tables(self):
        """Import a folder of grade tables, collate the contents and
        update the internal table.
        Only non-empty cells in the imported tables are taken into
        consideration and only one imported table may supply the
        value for a given cell.
        The "information" fields are not affected.
        """
        self.clear()
        dir0 = ADMIN._loaddir or os.path.expanduser('~')
        dpath = QFileDialog.getExistingDirectory(self.gradeView,
                _DIROPEN, dir0,
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if dpath:
            ADMIN.set_loaddir(dpath)
            # Reload grade table, in case changes were not saved
            grade_table = GradeTable(ADMIN.schoolyear, self.group,
                    self.term, ok_new = True)
            fn = _UpdateGrades(grade_table, dpath)
            cc = REPORT('RUN', runme = fn)
        # Redisplay table
        self.grade_scene = GradeGrid(self.gradeView, ADMIN.schoolyear,
                self.group, self.term)
        self.gradeView.set_scene(self.grade_scene)
#
    def make_reports(self):
        """Generate the grade report(s).
        """
        self.save(force = False)
        greports = GradeReports(ADMIN.schoolyear, self.group, self.term)
        fn = _MakeReports(greports)
        files = REPORT('RUN', runme = fn)
#
    def print_table(self):
        """Output the table as pdf.
        """
        self.save(force = False)
        if self.grade_scene:
            self.grade_scene.to_pdf()

###

class _MakeReports:#(ThreadFunction):
    def __init__(self, grade_reports):
        super().__init__()
        self._grade_reports = grade_reports
#
    def run(self):
        files = self._grade_reports.makeReports()
        if files:
            REPORT('INFO', "%s:\n  --> %s" % (_MADE_REPORTS,
                '\n  --> '.join(files)))
        else:
            REPORT('ERROR', _NO_REPORTS)
#
    def terminate(self):
        return False

###

class _UpdateGrades:#(ThreadFunction):
    def __init__(self, grade_table, dpath):
        super().__init__()
        self.grade_table = grade_table
        self.dpath = dpath
#
    def run(self):
        self._cc = 0
        gtables = []
        for f in os.listdir(self.dpath):
            self.message("FILE: %s" % f)
            if self._cc:
                return -1
            fpath = os.path.join(self.dpath, f)
            try:
                gtable = GradeTableFile(ADMIN.schoolyear, fpath,
                        full_table = False)
            except:
                REPORT('WARN', _BAD_GRADE_FILE.format(fpath = fpath))
            else:
                # Check that it matches the currently selected group/term
                try:
                    self.grade_table.check_group_term(gtable)
                    # ... only returns if ok
                except GradeTableError as e:
                    REPORT('ERROR', _GRADE_TABLE_MISMATCH.format(error = e,
                            year = gtable.schoolyear, group = gtable.group,
                            term = gtable.term))
                gtables.append(gtable)
        if gtables:
            self.grade_table.integrate_partial_data(*gtables)
            REPORT('INFO', _UPDATED_GRADES.format(n = len(gtables)))
            return len(gtables)
        else:
            REPORT('WARN', _NO_GRADE_FILES)
            return 0


tab_grade_editor = GradeEdit()
TABS.append(tab_grade_editor)
FUNCTIONS['grades_SET_TERMS'] = tab_grade_editor.SET_TERMS
FUNCTIONS['grades_SET_GROUPS'] = tab_grade_editor.SET_GROUPS
FUNCTIONS['grades_SET_PUPILS'] = tab_grade_editor.SET_PUPILS
FUNCTIONS['grades_SET_GRADES'] = tab_grade_editor.SET_GRADES
FUNCTIONS['grades_SET_GRID'] = tab_grade_editor.SET_GRID
