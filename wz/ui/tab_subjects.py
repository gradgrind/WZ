# -*- coding: utf-8 -*-
"""
ui/tab_subjects.py

Last updated:  2021-04-05

Subject table management.


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

#TODO: Class subject table editor

### Labels, etc.
_CLASS = "Klasse:"
_NO_CLASS = "–––"
_MANAGE_SUBJECTS = "Fächer verwalten"
_MANAGE_SUBJECTS_TEXT = """## Fachliste aktualisieren
Die Fachliste für eine Klasse kann von einer Tabelle (xlsx, ods or tsv)
aktualisiert werden. Diese Tabelle muss die entsprechende Struktur
aufweisen.

## Fächerwahl
Es ist möglich – aber nicht immer notwendig – für eine Klasse eine
Tabelle anzulegen, die angibt, dass bestimmte Schüler am Unterricht in
bestimmten Fächern **nicht** teilnehmen. Diese Tabelle kann hier
bearbeitet werden.

Die Fächerwahl-Tabelle für eine Klasse kann als xlsx-Datei "exportiert"
werden. Eine solche Tabelle kann auch "importiert" werden, um die
Daten für diese Klasse von einer externen Quelle zu aktualisieren.
"""
_UPDATE_SUBJECTS_TABLE = "Fachtabelle laden"
_MAKE_CHOICE_TABLE = "Fach-Wahl-Tabelle erstellen"
_UPDATE_CHOICE_TABLE = "Fach-Wahl-Tabelle laden"
_SELECT_CLASS_TITLE = "Klasse wählen"
_SELECT_CLASS = "Klicken Sie auf die Klasse, für die eine" \
        " Fächerwahltabelle erstellt werden soll."
_EDIT_CHOICES = "Fächerwahl bearbeiten"
_SUBJECT_CHOICE_FILE = 'Fachwahl_{klass}.xlsx'
_TABLE_FILE = "Tabellendatei (*.xlsx *.ods *.tsv)"
_EXCEL_FILE = "Excel-Tabelle (*.xlsx)"
_SAVE = "Änderungen Speichern"

#####################################################

from qtpy.QtWidgets import QLabel, QTextEdit, QHBoxLayout, QVBoxLayout, \
        QPushButton, QStackedWidget

from ui.ui_support import TabPage, VLine, ListSelect, openDialog, \
        HLine, saveDialog, KeySelect
from ui.choice_grid import ToggleGrid
from ui.gridbase import GridView

### ++++++

class StackedWidget_info(QTextEdit):
    def __init__(self, tab_widget):
        self._tab = tab_widget
        super().__init__()
        self.setReadOnly(True)
        self.setMarkdown(_MANAGE_SUBJECTS_TEXT)
#
    def is_modified(self):
        return False
#
    def changes(self):
        return False
#
    def activate(self):
        for pb in ('NEW_TABLE', 'C_CHOOSE'):
            self._tab.enable(pb, True)
#
    def deactivate(self):
        return True

###

class StackedWidget_choices(GridView):
    def __init__(self, tab_widget):
        self._tab = tab_widget
        super().__init__()
        self.choices_scene = None
#
    def is_modified(self):
        return bool(self.choices_scene.changes())
#
    def set_changed(self, show):
        self._tab.enable('SAVE', show)
#
    def activate(self, info, pupil_data, subjects):
        self.choices_scene = ToggleGrid(self, info, pupil_data, subjects)
        self.set_scene(self.choices_scene)
        for pb in ('MAKE_CHOICE_TABLE', 'UPDATE_CHOICE_TABLE', 'C_CHOOSE'):
            self._tab.enable(pb, True)
#
    def deactivate(self):
        self.choices_scene = None
        self.set_scene(None)
#
    def save(self):
        BACKEND('SUBJECT_save_choices', klass = self._tab.klass,
                data = self.choices_scene.data())

###

class Subjects(TabPage):
    """Update (import) the subjects list for a class from a table (ods
    or xlsx).
    Export (xlsx) and import (ods or xlsx) the "choice" table for a class.
    """
    def __init__(self):
        self._widgets = {}
        super().__init__(_MANAGE_SUBJECTS)
        topbox = QHBoxLayout()
        self.vbox.addLayout(topbox)

        #*********** The "main" widget ***********
        self.main = QStackedWidget()
        topbox.addWidget(self.main)
        ### The stacked widgets:
        # 0) Text describing the available functions
        _w = StackedWidget_info(self)
        self.main.addWidget(_w)
        self._widgets['INFO'] = _w
        # 1) Custom editor-table for subject choices
        _w = StackedWidget_choices(self)
        self.main.addWidget(_w)
        self._widgets['CHOICES'] = _w

        topbox.addWidget(VLine())
        cbox = QVBoxLayout()
        topbox.addLayout(cbox)

        ### Select class
        self.class_select = KeySelect(changed_callback = self.class_changed)
        self._widgets['C_CHOOSE'] = self.class_select
        cbox.addWidget(QLabel(_CLASS))
        cbox.addWidget(self.class_select)

        ### Import new subject table
        _w = QPushButton(_UPDATE_SUBJECTS_TABLE)
        self._widgets['NEW_TABLE'] = _w
        cbox.addWidget(_w)
        _w.clicked.connect(self.update_subjects)

        cbox.addSpacing(30)

        ### Manage choices
        cbox.addWidget(HLine())
        cbox.addSpacing(5)

        _w = QPushButton(_EDIT_CHOICES)
        self._widgets['EDIT_CHOICES'] = _w
        cbox.addWidget(_w)
        _w.clicked.connect(self.edit_choices)

        cbox.addSpacing(30)

        _w = QPushButton(_MAKE_CHOICE_TABLE)
        self._widgets['MAKE_CHOICE_TABLE'] = _w
        cbox.addWidget(_w)
        _w.clicked.connect(self.choice_table)

        cbox.addSpacing(5)

        _w = QPushButton(_UPDATE_CHOICE_TABLE)
        self._widgets['UPDATE_CHOICE_TABLE'] = _w
        cbox.addWidget(_w)
        _w.clicked.connect(self.update_choices)

        cbox.addStretch(1)

        ### Save (changed) data
        _w = QPushButton(_SAVE)
        self._widgets['SAVE'] = _w
        cbox.addWidget(_w)
        _w.clicked.connect(self.save)
#
    def set_widget(self, tag, **params):
        """Select the widget to be displayed in the "main" stack.
        """
        current = self.main.currentWidget()
        if current:
            current.deactivate()
        new = self._widgets[tag]
        self.main.setCurrentWidget(new)
        # Allow each function group to decide which buttons are enabled
        for pb in ('NEW_TABLE', 'EDIT_CHOICES', 'MAKE_CHOICE_TABLE',
                'UPDATE_CHOICE_TABLE', 'C_CHOOSE', 'SAVE'):
            self.enable(pb, False)
        new.activate(**params)
#
    def is_modified(self):
        return self.main.currentWidget().is_modified()
#
    def enable(self, tag, on):
        """Enable or disable the widget with given tag.
        """
        self._widgets[tag].setEnabled(on)
#
    def enter(self):
        """Called when the tab is selected.
        """
        self.klass = None
        BACKEND('SUBJECT_get_classes')   # -> SET_CLASSES(...)
#
    def year_change_ok(self):
        return self.leave_ok()
#
    def SET_CLASSES(self, classes):
        """CALLBACK: Supplies the classes as a list.
        Set the class selection widget and trigger a "change of class"
        signal.
        """
        classes.reverse()
        ix = 0
        for c, _ in classes:
            ix += 1
            if c == self.klass:
                break
        else:
            ix = 0
            self.klass = None
        self.class_select.set_items([('', _NO_CLASS)] + classes, index = ix)
        self.class_changed(self.klass, force = True)
#
    def class_changed(self, klass, force = False):
        """Manual selection of a class (including the 'empty' class,
        meaning "no particular class").
        """
        if force or self.leave_ok():
            self.klass = klass
            if klass:
                self.edit_choices()
            else:
                self.set_widget('INFO')
            return True
        return False
#
    def leave(self):
        """Called when the tab is deselected.
        """
        self.main.currentWidget().deactivate()
        return True
#
    def update_subjects(self):
        fpath = openDialog(_TABLE_FILE)
        if not fpath:
            return
        BACKEND('SUBJECT_table_update', filepath = fpath)
#
    def edit_choices(self):
        BACKEND('SUBJECT_edit_choices', klass = self.klass)
#
    def EDIT_CHOICES(self, info, pupil_data, subjects):
        self.set_widget('CHOICES', info = info, pupil_data = pupil_data,
                subjects = subjects)
#
    def update_choices(self):
        fpath = openDialog(_TABLE_FILE)
        if not fpath:
            return
        BACKEND('SUBJECT_update_choice_table', filepath = fpath)
#
    def choice_table(self):
        fpath = saveDialog(_EXCEL_FILE,
                _SUBJECT_CHOICE_FILE.format(klass = self.klass))
        if fpath:
            BACKEND('SUBJECT_make_choice_table', klass = self.klass,
                    filepath = fpath)
#
    def save(self):
        self.main.currentWidget().save()


tab_subjects = Subjects()
TABS.append(tab_subjects)
FUNCTIONS['subjects_SET_CLASSES'] = tab_subjects.SET_CLASSES
FUNCTIONS['subjects_EDIT_CHOICES'] = tab_subjects.EDIT_CHOICES
