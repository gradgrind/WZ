# -*- coding: utf-8 -*-
"""
ui/tab_text_reports.py

Last updated:  2021-04-06

Manage text reports

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

#TODO: only the cover sheets for a whole class have been implemented

### Labels, etc.
_TEXT_REPORTS = "Waldorf-Zeugnisse"
#_SAVE = "Änderungen speichern"
_CLASS = "Klasse"
#_FILESAVE = "Datei speichern"
#_COVER_FILE = "Mantelbogen (*.pdf)"
_ALL_CLASSES = "* Alle Klassen *"
_COVERSHEETS = "Mantelbögen"
_MAKE_COVERS = "Mantelbögen erstellen"
_SAVE_FILE = "pdf-Datei (*.pdf)"

#####################################################

from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, \
        QPushButton, QTextEdit, QDateEdit
#from qtpy.QtGui import QTextOption
from qtpy.QtCore import QDate

from ui.ui_support import VLine, HLine, KeySelect, TabPage, GuiError, \
        saveDialog

###

NONE = ''

class TextReports(TabPage):
    def __init__(self):
        self._widgets = {}
        super().__init__(_TEXT_REPORTS)
        topbox = QHBoxLayout()
        self.vbox.addLayout(topbox)

        #*********** The "main" widget ***********
        self.text = QTextEdit(self)
        topbox.addWidget(self.text)
        topbox.addWidget(VLine())
        cbox = QVBoxLayout()
        topbox.addLayout(cbox)

        ### Select class
        self.class_select = KeySelect(changed_callback = self.class_changed)
        self._widgets['C_CHOOSE'] = self.class_select
        cbox.addWidget(QLabel(_CLASS))
        cbox.addWidget(self.class_select)

        ### List of pupils
        self.pselect = KeySelect(changed_callback = self.pupil_changed)
        self._widgets['P_CHOOSE'] = self.pselect
        cbox.addWidget(self.pselect)

        ### Save (changed) data
        cbox.addStretch(1)

        ### Cover sheets
        cbox.addWidget(HLine())
        cbox.addWidget(QLabel('<b>%s</b>' % _COVERSHEETS))
        cbox.addSpacing(5)
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        cbox.addWidget(self.date)
        pbCover = QPushButton(_MAKE_COVERS)
        cbox.addWidget(pbCover)
        pbCover.clicked.connect(self.make_covers)
#
    def enter(self):
        self.klass = NONE
        self.pid = NONE
        BACKEND('TEXT_get_calendar')
#
    def SET_CALENDAR(self, calendar):
        self.calendar = calendar
        date = self.calendar['LAST_DAY']
        self.date.setDate(QDate.fromString(date, 'yyyy-MM-dd'))
#
    def SET_CLASSES(self, classes):
        """CALLBACK: Supplies the classes as a list: [class10, class9, ...]
        and the selected class. Set the class selection widget
        and trigger a "change of class" signal.
        """
        try:
            ix = classes.index(self.klass) + 1
        except ValueError:
            ix = 0
            self.klass = NONE
        self.class_select.set_items([('', _ALL_CLASSES)] +
                [(c, c) for c in classes if c < '13'], index = ix)
        self.class_changed(self.klass)
#
    def class_changed(self, klass):
        self.klass = klass
        if klass:
            BACKEND('TEXT_set_class', klass = klass)
        else:
            self.pselect.set_items(None)
            self.pid = NONE
        return True
#
    def SET_PUPILS(self, pupil_list):
        self.pselect.set_items(pupil_list)
        try:
            self.pselect.reset(self.pid)
        except GuiError:
            self.pid = NONE
#
    def pupil_changed(self, pid):
        self.pid = pid
        return True
#
    def make_covers(self):
        if self.pid:
            BACKEND('TEXT_covername', pid = self.pid)
        else:
            date = self.date.date().toString('yyyy-MM-dd')
            BACKEND('TEXT_make_covers', date = date, klass = self.klass)
#
    def MAKE_ONE_COVER(self, filename):
        fpath = saveDialog(_SAVE_FILE, filename)
        if fpath:
            date = self.date.date().toString('yyyy-MM-dd')
            BACKEND('TEXT_make_one_cover', pid = self.pid,
                    date = date, filepath = fpath)

tab_text_reports = TextReports()
TABS.append(tab_text_reports)
FUNCTIONS['text_SET_CALENDAR'] = tab_text_reports.SET_CALENDAR
FUNCTIONS['text_SET_CLASSES'] = tab_text_reports.SET_CLASSES
FUNCTIONS['text_SET_PUPILS'] = tab_text_reports.SET_PUPILS
FUNCTIONS['text_MAKE_ONE_COVER'] = tab_text_reports.MAKE_ONE_COVER
