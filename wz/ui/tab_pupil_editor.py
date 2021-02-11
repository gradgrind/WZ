# -*- coding: utf-8 -*-
"""
ui/tab_pupil_editor.py

Last updated:  2021-02-11

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
#TODO

### Labels, etc.
_EDIT_PUPIL = "Schüler verwalten"
_CLASS = "Klasse:"
_NEW_PUPIL = "Neuer Schüler"
_REMOVE_PUPIL = "Schüler löschen"
_SAVE = "Änderungen speichern"

#####################################################

from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QPushButton

from ui.grid import GridView
from ui.pupil_grid import PupilGrid
from ui.ui_support import VLine, KeySelect, TabPage, GuiError

###

class GView(GridView):
    def set_changed(self, show):
        self.pbSave.setEnabled(show)

###

class PupilEdit(TabPage):
    def __init__(self):
        super().__init__(_EDIT_PUPIL)
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
        self.FIELDS = None
#
    def SET_INFO(self, fields, sex, streams):
        """<fields> is a list of field names:
            [[field1_internal_name, field1_local_name], ... ]
        """
        self.INFO = {
            'FIELDS': {field: name for field, name in fields},
            'SEX': sex,
            'STREAMS': streams
        }
        #print("INFO: ", self.INFO)
#
    def SET_CLASSES(self, classes, klass):
        """CALLBACK: Supplies the classes as a list: [class10, class9, ...]
        and the selected class. Set the class selection widget
        and trigger a "change of class" signal.
        """
#TODO: Is this the right place for this?
        self.pupil_scene = PupilGrid(self.pupilView, self.INFO)
#        self.pupilView.set_scene(self.pupil_scene)

        try:
            ix = classes.index(klass)
        except ValueError:
            ix = 0
        self.class_select.set_items([(c, c) for c in classes], index = ix)
        self.class_select.trigger()
        return True
#
    def SET_PUPILS(self, pupils, pid):
        """CALLBACK: Supplies the pupils as a list: [[pid, pname], ...]
        and the id of the selected pupil. Set the pupil selection widget
        and trigger a "change of pupil" signal.
        """
        self.pselect.set_items(pupils)
        try:
            self.pselect.reset(pid)
        except GuiError:
            pass
        self.pselect.trigger()
        return True
#
    def SET_PUPIL_DATA(self, data, name):
        self.pupil_scene.set_pupil(data, name)
        self.pupilView.set_scene(self.pupil_scene)
        return True
#
    def clear(self):
        """Check for changes in the current "scene", allowing these to
        be discarded if desired. If accepted (or no changes), clear the
        "scene" and return <True>, otherwise leave the display unaffected
        and return <False>.
        """
        return self.pupilView.set_scene(None)
#
    def enter(self):
        if not self.FIELDS:
            BACKEND('PUPIL_get_info')
        BACKEND('PUPIL_enter')
#
    def leave(self):
        if self.clear():
            # Drop the data structures associated with the pupil-data view
            self.pupil_scene = None
            return True
        else:
            return False
#
#TODO
    def year_changed(self):
        if not self.clear():
            return False
# I would need a second year to test this!


        self.pupil_scene = PupilGrid(self.pupilView, self.INFO)
        self.pupilView.set_scene(self.pupil_scene)
        self.class_select.set_items([(c, c)
                for c in self.pupil_scene.classes()])
        self.class_select.trigger()
        return True
#
    def class_changed(self, klass):
        if not self.clear():
            return False
        BACKEND('PUPIL_set_class', klass = klass)
        return True
#
    def pupil_changed(self, pid):
        """A new pupil has been selected: reset the grid accordingly.
        """
        if not self.clear():
            return False
        BACKEND('PUPIL_set_pupil', pid = pid)
        return True
#
#TODO ...
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

tab_pupil_editor = PupilEdit()
TABS.append(tab_pupil_editor)
FUNCTIONS['pupil_SET_INFO'] = tab_pupil_editor.SET_INFO
FUNCTIONS['pupil_SET_CLASSES'] = tab_pupil_editor.SET_CLASSES
FUNCTIONS['pupil_SET_PUPILS'] = tab_pupil_editor.SET_PUPILS
FUNCTIONS['pupil_SET_PUPIL_DATA'] = tab_pupil_editor.SET_PUPIL_DATA
