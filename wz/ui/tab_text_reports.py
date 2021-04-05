# -*- coding: utf-8 -*-
"""
ui/tab_text_reports.py

Last updated:  2021-04-04

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
#TODO ... fixing up – still much old code

#TODO: only the cover sheets for a whole class have been implemented

### Messages
_MADE_COVERS = "Mantelbögen erstellt in:\n  {path}"

### Labels, etc.
_TEXT_REPORTS = "Waldorf-Zeugnisse"
#_SAVE = "Änderungen speichern"
_CLASS = "Klasse"
_FILESAVE = "Datei speichern"
#_COVER_FILE = "Mantelbogen (*.pdf)"
_ALL_CLASSES = "* Alle Klassen *"
_ALL_PUPILS = "* Ganze Klasse *"
_COVERSHEETS = "Mantelbögen"
_MAKE_COVERS = "Mantelbögen erstellen"

#####################################################

from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, \
        QPushButton, QTextEdit, QDateEdit
#from qtpy.QtGui import QTextOption
from qtpy.QtCore import QDate

from ui.ui_support import VLine, HLine, KeySelect, TabPage

###

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
        self.year_changed()
#
    def leave(self):
        pass
#        self.check_saved()      # see calendar.py
#
    def year_changed(self):
        BACKEND('TEXT_get_calendar')
#
    def SET_CALENDAR(self, calendar):
        self.calendar = calendar
        date = self.calendar['LAST_DAY']
        self.date.setDate(QDate.fromString(date, 'yyyy-MM-dd'))
#
    def SET_CLASSES(self, classes, klass):
        """CALLBACK: Supplies the classes as a list: [class10, class9, ...]
        and the selected class. Set the class selection widget
        and trigger a "change of class" signal.
        """
        try:
            ix = classes.index(klass) + 1
        except ValueError:
            ix = 0
        self.class_select.set_items([('', _ALL_CLASSES)] +
                [(c, c) for c in classes if c < '13'], index = ix)
        self.class_select.trigger()
#
    def class_changed(self, klass):
        BACKEND('TEXT_set_class', klass = klass)
#
    def SET_CLASS(self, klass, pupil_list):
#TODO: check changes?
        self.klass = klass
        self.pselect.set_items(pupil_list)
#?
#
    def pupil_changed(self, pid):
        raise Bug("TODO")
#
    def make_covers(self):
        date = self.date.date().toString('yyyy-MM-dd')
        BACKEND('TEXT_make_covers', date = date)


        return



#TODO
        print("TODO: individual pupils")
        coversheets = CoverSheets(ADMIN.schoolyear)
        date = self.date.date().toString('yyyy-MM-dd')
        fn = _MakeCovers(coversheets, self.klass, date)
        files = REPORT('RUN', runme = fn)



tab_text_reports = TextReports()
TABS.append(tab_text_reports)
#FUNCTIONS['text_SET_CLASS'] = tab_text_reports.SET_CLASS
FUNCTIONS['text_SET_CALENDAR'] = tab_text_reports.SET_CALENDAR
