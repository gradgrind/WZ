# -*- coding: utf-8 -*-
"""
ui/tab_grade_editor.py

Last updated:  2021-03-25

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
_NOT_INTERRUPTABLE = "+++ Der Prozess kann nicht unterbrochen werden +++"
_MUST_SAVE_CHANGES = "Die Änderungen müssen zuerst gespeichert werden."
_TITLE_TABLE_REPLACE = "Neue Tabelle speichern"
# Would need to be a bit different for individual pupils:
_TABLE_REPLACE = "Die neue Tabelle wird die alte ersetzen.\n" \
        "Soll sie jetzt gespeichert werden?"
_TABLE_OVERWRITE = "{n} Noten werden geändert. Übernehmen?"
_NOT_SAVED = "Änderungen nicht gespeichert"

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
_TAG_ENTER = "Geben Sie eine Bezeichnung für diesen Datensatz an.\n" \
        "Buchstaben, Ziffern, '~' und '-' sind zulässig, andere Zeichen" \
        " werden ersetzt."
_TABLE_FILE = "Tabellendatei (*.xlsx *.ods *.tsv)"

#####################################################

import os, glob

from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, \
        QPushButton, QFileDialog
from qtpy.QtCore import SIGNAL, QObject

from ui.grid import GridView
from ui.grade_grid import GradeGrid
from ui.abitur_pupil_view import AbiPupilView
from ui.ui_support import VLine, KeySelect, TabPage,openDialog, \
        QuestionDialog, dirDialog, LineDialog

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

        ### Select "term" (to which occasion the reports are to appear)
        ### That might be a term or semester, it might be a special
        ### unscheduled report, or a scheduled test (possibly no report)
        ### or something specific to the school form.
        self.term_select = KeySelect(changed_callback = self.term_changed)
        cbox.addWidget(QLabel(_TERM))
        cbox.addWidget(self.term_select)

        ### Select group (might be just one entry ... perhaps even none)
        self.group_select = KeySelect(changed_callback = self.group_changed)
        cbox.addWidget(QLabel(_GROUP))
        cbox.addWidget(self.group_select)

        ### Subselection: e.g. tags/dates/pupils
        self.subselect = KeySelect(changed_callback = self.sub_changed)
        cbox.addWidget(self.subselect)

        cbox.addSpacing(30)

        ### Save button (active when there are unsaved modifications)
        self.gradeView.pbSave = QPushButton(_SAVE)
        cbox.addWidget(self.gradeView.pbSave)
        self.gradeView.pbSave.clicked.connect(self.save)

        cbox.addStretch(1)

        ### Generate grade table (for inputting)
        pbTable = QPushButton(_TABLE_XLSX)
        pbTable.setToolTip(_TT_TABLE_XLSX)
        cbox.addWidget(pbTable)
        pbTable.clicked.connect(self.make_table)

        cbox.addSpacing(10)

        ### Import grade table (replace internal one)
        pbTableIn1 = QPushButton(_TABLE_IN1)
        pbTableIn1.setToolTip(_TT_TABLE_IN1)
        cbox.addWidget(pbTableIn1)
        pbTableIn1.clicked.connect(self.input_table)

        ### Import grade tables (adding to internal one)
        pbTableInDir = QPushButton(_TABLE_IN_DIR)
        pbTableInDir.setToolTip(_TT_TABLE_IN_DIR)
        cbox.addWidget(pbTableInDir)
        pbTableInDir.clicked.connect(self.input_tables)

        cbox.addSpacing(30)

        ### Produce a pdf of the grade table
        pbPdf = QPushButton(_TABLE_PDF)
        cbox.addWidget(pbPdf)
        pbPdf.clicked.connect(self.print_table)

        cbox.addSpacing(10)

        ### Produce the reports
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
    def SET_TERMS(self, terms, term):
        """CALLBACK: Supplies the terms as a list of "keys" (the display
        form must substitute '_' by ' ').
        Also the selected term is passed. Set the term selection widget
        and trigger a "change of term" signal.
        """
        try:
            ix = terms.index(term)
        except ValueError:
            ix = 0
        self.term_select.set_items([(t, t.replace('_', ' ')) for t in terms],
                index = ix)
        self.term_select.trigger()
        return True
#
    def term_changed(self, key):
        if not self.clear():
            return False
        BACKEND('GRADES_set_term', term = key)
        self.term = key
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
    def sub_changed(self, itemtag):
        # For real terms there is no subselect, so this method will not
        # be called.
        if not self.clear():
            return False
        if self.term == 'Abitur':
            # This is a special case ...
            # Switch to/from individual pupil display.
            # <itemtag> is the pid, empty to select the group.
            if itemtag:
                self.grade_scene = AbiPupilView(self.gradeView)
                self.gradeView.set_scene(self.grade_scene)
                BACKEND('ABITUR_set_pupil', pid = itemtag)
                return True
        BACKEND('GRADES_subselect', tag = itemtag)
        return True
#
    def SET_PUPILS_OR_TAGS(self, termx, group, select_list, pid_or_tag):
        self.subselect.set_items(select_list)
        if select_list:
            self.subselect.reset(pid_or_tag)
#?        self.subselect.trigger()
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
    def abitur_INIT_CELLS(self, data):
        self.grade_scene.init_cells(data)
#
    def abitur_SET_CELLS(self, data):
        self.grade_scene.set_cells(data)
#
    def save(self):
        self.grade_scene.save_data()
#
    def make_table(self):
        """Generate input table (xlsx) for the grades.
        """
        if self.grade_scene.changes():
            SHOW_WARNING(_MUST_SAVE_CHANGES)
            return
        BACKEND('GRADES_make_table')
#
    def input_table(self):
        """Import a single grade table, replacing the internal table.
        """
        fpath = openDialog(_TABLE_FILE)
        if fpath:
            if QuestionDialog(_TITLE_TABLE_REPLACE, _TABLE_REPLACE):
                BACKEND('GRADES_load_table', filepath = fpath)
                # On success, the table must be redisplayed
#
    def input_tables(self):
        """Import a folder of grade tables, collate the contents and
        update the internal table.
        Only non-empty cells in the imported tables are taken into
        consideration and only one imported table may supply the
        value for a given cell.
        The "information" fields are not affected.
        """
#TODO: At present only empty cells may be updated, but it may be better
# to allow grades to be updated (only by one of the input tables, though!).
# See gradetable.py: integrate_partial_data
        if not self.clear():
            return False
        dpath = dirDialog()
        if dpath:
            BACKEND('GRADES_update_table', dirpath = dpath)
            BACKEND('GRADES_save_new')
            # On success, the table must be redisplayed
#
    def QUESTION_UPDATE(self, n):
        if QuestionDialog(_TITLE_TABLE_REPLACE, _TABLE_OVERWRITE.format(
                n = n)):
            BACKEND('GRADES_save_new')
            # The table must be redisplayed
#
    def make_reports(self):
        """Generate the grade report(s).
        """
        if self.grade_scene.changes():
            SHOW_WARNING(_MUST_SAVE_CHANGES)
            return
        BACKEND('GRADES_make_reports')
#
    def print_table(self):
        """Output the table as pdf.
        """
        if self.grade_scene.changes():
            SHOW_WARNING(_MUST_SAVE_CHANGES)
            return
        BACKEND('GRADES_print_table')
#
    def PDF_NAME(self, filename):
        self.grade_scene.to_pdf(filename)
#
    def GET_TAG(self):
        tag = LineDialog(_TAG_ENTER)
        if tag:
            BACKEND('GRADES_save', tag = tag)
        else:
            SHOW_WARNING(_NOT_SAVED)

###

tab_grade_editor = GradeEdit()
TABS.append(tab_grade_editor)
FUNCTIONS['grades_SET_TERMS'] = tab_grade_editor.SET_TERMS
FUNCTIONS['grades_SET_GROUPS'] = tab_grade_editor.SET_GROUPS
FUNCTIONS['grades_SET_PUPILS_OR_TAGS'] = tab_grade_editor.SET_PUPILS_OR_TAGS
FUNCTIONS['grades_SET_GRADES'] = tab_grade_editor.SET_GRADES
FUNCTIONS['grades_SET_GRID'] = tab_grade_editor.SET_GRID
FUNCTIONS['grades_QUESTION_UPDATE'] = tab_grade_editor.QUESTION_UPDATE
FUNCTIONS['grades_PDF_NAME'] = tab_grade_editor.PDF_NAME
FUNCTIONS['grades_GET_TAG'] = tab_grade_editor.GET_TAG
FUNCTIONS['abitur_INIT_CELLS'] = tab_grade_editor.abitur_INIT_CELLS
FUNCTIONS['abitur_SET_CELLS'] = tab_grade_editor.abitur_SET_CELLS
