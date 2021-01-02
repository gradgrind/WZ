# -*- coding: utf-8 -*-
"""
gui/grade_editor.py

Last updated:  2021-01-02

Editor for pupil data.

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
from gui.gui_support import VLine, KeySelect, TabPage, GuiError

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
        self.pupil_scene = None
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
        self.pupil_scene = None
#
    def year_changed(self):
        if not self.clear():
            return False
        self.pupil_scene = PupilGrid(self.pupilView, ADMIN.schoolyear)
        self.pupilView.set_scene(self.pupil_scene)
        self.class_select.set_items([(c, c)
                for c in self.pupil_scene.classes()])
        self.class_select.trigger()
        return True
#
    def class_changed(self, klass, pid = None):
        # If <pid> is supplied there are no unsaved changes.
        if (not pid) and (not self.clear()):
            self.class_select.reset(self.pupil_scene.klass)
            return
        if self.pupil_scene:
            self.pupilView.set_scene(self.pupil_scene)
        pdlist = self.pupil_scene.set_class(klass)
        self.pselect.set_items([(pdata['PID'], pdata.name())
                for pdata in pdlist])
        try:
            self.pselect.reset(pid)
        except GuiError:
            pid = pdlist[0]['PID']
        self.pupil_scene.set_pupil(pid)
#
    def pupil_changed(self, pid):
        """A new pupil has been selected: reset the grid accordingly.
        """
        if not self.clear():
            self.pselect.reset(self.pupil_scene.pid)
            return
        if self.pupil_scene:
            self.pupilView.set_scene(self.pupil_scene)
        self.pupil_scene.set_pupil(pid)
#
    def new_pupil(self):
        if not self.clear():
            return
        if self.pupil_scene:
            self.pupilView.set_scene(self.pupil_scene)
        self.pupil_scene.set_pupil(None)
#
    def remove_pupil(self):
        self.pupil_scene.remove_pupil()
        # Pass dummy argument to suppress "changed" dialog.
        self.class_changed(self.pupil_scene.klass, 'DUMMY')
#
    def save(self, force = True):
        self.pupil_scene.save_changes()
        klass = self.pupil_scene.pupil_data['CLASS']
        pid = self.pupil_scene.pupil_data['PID']
        self.class_changed(klass, pid)
