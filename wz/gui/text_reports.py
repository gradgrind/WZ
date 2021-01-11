# -*- coding: utf-8 -*-
"""
gui/text_reports.py

Last updated:  2021-01-09

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

### Messages
_MADE_COVERS = "Mantelbögen erstellt in:\n  {path}"

### Labels, etc.
_TEXT_REPORTS = "Waldorf-Zeugnisse"
#_SAVE = "Änderungen speichern"
_CLASS = "Klasse"
_FILESAVE = "Datei speichern"
#_COVER_FILE = "Mantelbogen (*.pdf)"
_ALL_PUPILS = "** Ganze Klasse **"
_COVERSHEETS = "Mantelbögen"
_MAKE_COVERS = "Mantelbögen erstellen"

#####################################################

import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)
# <core.base> must be the first WZ-import
import core.base as CORE

from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, \
        QPushButton, QTextEdit, QDateEdit
#from qtpy.QtGui import QTextOption
from qtpy.QtCore import QDate

from gui.gui_support import VLine, HLine, KeySelect, TabPage
from core.pupils import Pupils
#from local.base_config import year_path
from template_engine.coversheet import CoverSheets

###

class TextReports(TabPage):
    def __init__(self):
        super().__init__(_TEXT_REPORTS)
        topbox = QHBoxLayout()
        self.vbox.addLayout(topbox)

        #*********** The "main" widget ***********
        self.edit = QTextEdit()
        #self.edit.setLineWrapMode(self.edit.NoWrap)
        self.edit.setAcceptRichText(False)
        self.edit.setUndoRedoEnabled(True)
        topbox.addWidget(self.edit)
        topbox.addWidget(VLine())

        cbox = QVBoxLayout()
        topbox.addLayout(cbox)

        # Select class
        hbox1 = QHBoxLayout()
        cbox.addLayout(hbox1)
        hbox1.addWidget(QLabel(_CLASS))
        self.class_select = KeySelect(changed_callback = self.class_changed)
        hbox1.addWidget(self.class_select)

        self.pselect = KeySelect(changed_callback = self.pupil_changed)
        cbox.addWidget(self.pselect)

        cbox.addSpacing(30)
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
#TODO: check changes?
        cal = CORE.Dates.get_calendar(ADMIN.schoolyear)
        date = cal['LAST_DAY']
        self.date.setDate(QDate.fromString(date, 'yyyy-MM-dd'))
        self.pupils = Pupils(ADMIN.schoolyear)
        self.class_select.set_items([(c, c)
                for c in self.pupils.classes() if c < '13'])
        self.class_select.trigger()
#
    def save(self):
        header = CALENDER_HEADER.format(date = CORE.Dates.today())
        text = self.edit.toPlainText()
        try:
            text = text.split('#---', 1)[1]
            text = text.lstrip('-')
            text = text.lstrip()
        except:
            pass
        text = header + text

        with open(self.calendar_file, 'w', encoding = 'utf-8') as fh:
            fh.write(text)
        self.edit.setPlainText(text)    # clear undo/redo history
#
    def class_changed(self, klass):
#TODO: check changes?
        self.klass = klass
        self.pdlist = self.pupils.class_pupils(self.klass)
        plist = [('', _ALL_PUPILS)] + [(pdata['PID'], pdata.name())
                for pdata in self.pdlist]
        self.pselect.set_items(plist)
#?
#
    def pupil_changed(self, pid):
        raise Bug("TODO")
#
    def make_covers(self):
#TODO
        print("TODO: individual pupils")
        coversheets = CoverSheets(ADMIN.schoolyear)
        date = self.date.date().toString('yyyy-MM-dd')
        fn = _MakeCovers(coversheets, self.klass, date)
        files = REPORT('RUN', runme = fn)

###

class _MakeCovers(CORE.ThreadFunction):
    def __init__(self, coversheets, klass, date, pids = None):
        super().__init__()
        self._coversheets = coversheets
        self._klass = klass
        self._date = date
        self._pids = pids
#
    def run(self):
        fpath = self._coversheets.for_class(self._klass, self._date,
                self._pids)
        REPORT('INFO', _MADE_COVERS.format(path = fpath))
#
    def terminate(self):
        return False


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication
#    app = QApplication(['test', '-style=windows'])
    app = QApplication([])
    CORE.init()

    class ADMIN:
        schoolyear = '2016'
        _loaddir = None
        _savedir = None
        @classmethod
        def set_savedir(cls, path):
            cls._savedir = path
        @classmethod
        def set_loaddir(cls, path):
            cls._loaddir = path

    main = TextReports()
    main.enter()
    main.show()
    sys.exit(app.exec_())
