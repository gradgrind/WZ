# -*- coding: utf-8 -*-
"""
gui/grade_editor.py

Last updated:  2020-12-31

Editor for pupil data.


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

#TODO ...

### Messages
_SAVE_FAILED = "Speicherung der Änderungen ist fehlgeschlagen:\n  {msg}"

### Labels, etc.
_EDIT_PUPIL = "Schüler verwalten"
_CLASS = "Klasse:"
_NEW_PUPIL = "Neuer Schüler"
_REMOVE_PUPIL = "Schüler löschen"



_PUPIL = "Schüler"
_STREAM = "Maßstab"
_ALL_PUPILS = "Gesamttabelle"
_NEW_REPORT = "Neues Zeugnis"

_SCHULJAHR = "Schuljahr:"
_TERM = "Anlass:"
_GROUP = "Klasse/Gruppe:"
_SAVE = "Änderungen speichern"
_TABLE_XLSX = "Noteneingabe-Tabelle"
_TABLE_PDF = "Tabelle als PDF"
_REPORT_PDF = "Zeugnis(se) erstellen"
_TABLE_IN1 = "Notentabelle einlesen"
_TABLE_IN_DIR = "Notentabellen einlesen"
_FILESAVE = "Datei speichern"

#####################################################


from qtpy.QtWidgets import QApplication, QWidget, \
    QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFileDialog

from core.pupils import Pupils
from gui.grid import GridView
from gui.pupil_grid import PupilGrid
from gui.gui_support import VLine, KeySelect, TabPage

###

class GView(GridView):
    def set_changed(self, show):
        self.pbSave.setEnabled(show)

###

class PupilEdit(TabPage):
    def __init__(self):
        super().__init__(_EDIT_PUPIL)
#        self.resize(w, h)
#TODO: It might be desirable to adjust to the scene size?

        topbox = QHBoxLayout()
        self.vbox.addLayout(topbox)

        #*********** The "main" widget ***********
        self.pupilView = GView()
        topbox.addWidget(self.pupilView)
        topbox.addWidget(VLine())

        cbox = QVBoxLayout()

        ### Select class
        self.class_select = KeySelect(changed_callback = self.class_changed)
        cbox.addWidget(QLabel(_CLASS))
        cbox.addWidget(self.class_select)

        ### List of pupils
        self.pselect = KeySelect(changed_callback = self.pupil_changed)
#        self.pselect.setMaximumWidth(150)
        cbox.addWidget(self.pselect)

        cbox.addSpacing(30)
        self.pupilView.pbSave = QPushButton(_SAVE)
        cbox.addWidget(self.pupilView.pbSave)
        self.pupilView.pbSave.clicked.connect(self.save)
        cbox.addStretch(1)
        pnew = QPushButton(_NEW_PUPIL)
        cbox.addWidget(pnew)
        pnew.clicked.connect(self.new_pupil)
        cbox.addSpacing(10)
        pdel = QPushButton(_REMOVE_PUPIL)
        cbox.addWidget(pdel)
        pdel.clicked.connect(self.remove_pupil)
        topbox.addLayout(cbox)
#
    def closeEvent(self, e):
        if self.clear():
            super().closeEvent(e)
#
    def clear(self, force = False):
        """Check for changes in the current "scene", allowing these to
        be saved if desired (or if <force> is true), then clear the scene.
        """
        try:
            self.pupilView.clear(force)
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
#
    def year_changed(self):
        if not self.clear():
            return False
        self.schoolyear = ADMIN.schoolyear
        self.pupils = Pupils(self.schoolyear)
        classes = self.pupils.classes()
        self.class_select.set_items([(c, c) for c in classes])
        self.class_select.trigger()
        return True
#
    def class_changed(self, klass):
#TODO
        if klass:
            if not self.clear():
                self.class_select.reset(self.klass)
                return
            self.klass = klass
            self.pid = ''
        else:
            raise Exception("TODO")

        pdlist = self.pupils.class_pupils(self.klass)
        plist = [(pdata['PID'], pdata.name()) for pdata in pdlist]
        self.pid = pdlist[0]['PID']
        self.pselect.set_items(plist)
        self.pupil_scene = PupilGrid(self.pupilView, self.schoolyear,
                self.klass, self.pid)
#        if self.pid:
#            self.pselect.reset(self.pid)
        self.pupilView.set_scene(self.pupil_scene)
#
    def pupil_changed(self, pid):
        """A new pupil has been selected: reset the grid accordingly.
        """
#TODO
        if not self.clear():
            self.pselect.reset(self.pid)
            return
        self.pid = pid
        if pid:
            if self.term == 'A':
                self.grade_scene = AbiPupilView(self.gradeView,
                        self.schoolyear, self.group)
                self.gradeView.set_scene(self.grade_scene)
                self.grade_scene.set_pupil(pid)
                return
            if self.term[0] != 'S':
#TODO:
                REPORT("TODO: Change pupil %s" % pid)
                return
        self.group_changed(None)
#
    def new_pupil(self):
        print("TODO: new_pupil")
#
    def remove_pupil(self):
        print("TODO: remove_pupil")
#
    def save(self, force = True):
        if self.clear(force):    # no question dialog
            if self.term[0] == 'S':
                self.pid = self.grade_scene.grade_table.term
            self.group_changed(None)
