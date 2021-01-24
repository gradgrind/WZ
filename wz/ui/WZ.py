# -*- coding: utf-8 -*-
"""
ui/WZ.py

Last updated:  2021-01-24

Administration interface.


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
_SUBJECTS_CLASS = " ... Tabelle für Klasse {klass} aktualisiert"
_WARN_NO_CHANGES = "Keine Änderungen sind vorgemerkt"
_BAD_PUPIL_TABLE = "Schülerdaten fehlerhaft:\n  {path}"

### Labels, etc.
_TITLE = "WZ – Zeugnisverwaltung"

_FILEOPEN = "Datei öffnen"
_TABLE_FILE = "Tabellendatei (*.xlsx *.ods *.tsv)"

_UPDATE_PUPILS = "Schülerdaten aktualisieren"
_UPDATE_PUPILS_TEXT = "Die Schülerdaten können von einer Tabelle" \
        " aktualisiert werden.\nDiese Tabelle (xlsx oder ods) sollte" \
        " von der Schuldatenbank stammen."
_UPDATE_PUPILS_TABLE = "Tabellendatei wählen"
_DO_UPDATE = "Änderungen umsetzen"

_UPDATE_SUBJECTS = "Fachliste aktualisieren"
_UPDATE_SUBJECTS_TEXT = "Die Fachliste für eine Klasse kann von einer" \
        " Tabelle (xlsx oder ods) aktualisiert werden.\nDiese Tabelle" \
        " muss die entsprechende Struktur aufweisen."
_UPDATE_SUBJECTS_TABLE = "Tabellendatei wählen"

# Maximum display length (characters) of a pupil delta:
_DELTA_LEN_MAX = 80

#####################################################


import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

from qtpy.QtWidgets import QApplication, QWidget, QFrame, \
    QStackedWidget, QTreeWidget, QTreeWidgetItem, \
    QHBoxLayout, QVBoxLayout, QLabel, QTextEdit, \
    QPushButton, QButtonGroup, \
    QFileDialog
from qtpy.QtCore import Qt


#TODO

import os, platform, subprocess


def backend(command, *args, cwd = None, xpath = None, feedback = None):
    """Run an external program.
    Pass the command and the arguments as individual strings.
    The command must be either a full path or a command known in the
    run-time environment (PATH).
    Named parameters can be used to set:
     - cwd: working directory. If provided, change to this for the
       operation.
     - xpath: an additional PATH component (prefixed to PATH).
     - feedback: If provided, it should be a function. It will be called
         with each line of output as this becomes available.
    Return a tuple: (return-code, message).
    return-code: 0 -> ok, 1 -> fail, -1 -> command not available.
    If return-code >= 0, return the output as the message.
    If return-code = -1, return a message reporting the command.
    """
    # Note that using the <timeout> parameter will probably not work,
    # at least not as one might expect it to.
    params = {
        'stdin': subprocess.PIPE,
        'stdout': subprocess.PIPE,
        'stderr': subprocess.STDOUT,
        'universal_newlines': True,
        'bufsize': 1
    }
    my_env = os.environ.copy()
    if platform.system() == 'Windows':
        # Suppress the console
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        params['startupinfo'] = startupinfo
    if xpath:
        # Extend the PATH for the process
        my_env['PATH'] = xpath + os.pathsep + my_env['PATH']
        params['env'] = my_env
    if cwd:
        # Switch working directory for the process
        params['cwd'] = cwd

    cmd = [command] + list(args)
    try:
        if feedback:
            out = []
            with subprocess.Popen(cmd, bufsize=1, **params) as cp:
                for line in cp.stdout:
                    l = line.rstrip()
                    out.append(l)
                    feedback(l)
            msg = '\n'.join(out)

        else:
            cp = subprocess.run(cmd, **params)
            msg = cp.stdout

        return (0 if cp.returncode == 0 else 1, msg)

    except FileNotFoundError:
        return (-1, _COMMANDNOTPOSSIBLE.format(cmd=repr(cmd)))


class Backend:
    def __init__(self):
        pass


    def quit(self):
        print("TODO")
#???
        if not self.run('QUIT'):
            self.process.kill()

builtins.BACKEND = Backend()










# <core.base> must be the first WZ-import
from core.base import Dates
from gui.gui_support import HLine, KeySelect, TabPage
from gui.pupil_editor import PupilEdit
from gui.grade_editor import GradeEdit
from gui.text_reports import TextReports
from gui.calendar import Calendar
from gui.template_fields import FieldEdit
from local.base_config import print_schoolyear
from core.pupils import Pupils
from core.courses import Subjects

###

class Admin(QWidget):
    _savedir = None
    _loaddir = None
#
    @classmethod
    def set_savedir(cls, path):
        cls._savedir = path
#
    @classmethod
    def set_loaddir(cls, path):
        cls._loaddir = path
#
    def year(self):
        return self.year_select.selected()
#
    def __init__(self):
        super().__init__()
        self.setWindowTitle(_TITLE)
        topbox = QVBoxLayout(self)
        # ---------- Title Box ---------- #
        titlebox = QHBoxLayout()
        topbox.addLayout(titlebox)
        self.year_select = KeySelect(changed_callback = self.year_changed)
        titlebox.addWidget(self.year_select)
        titlebox.addStretch(1)
        topbox.addWidget(HLine())
        # ---------- Tab Box ---------- #
        self._ntabs = 0
        tabbox = QHBoxLayout()
        topbox.addLayout(tabbox)
        self._lbox = QVBoxLayout()
        tabbox.addLayout(self._lbox)
        self.selectPage = QButtonGroup()
        self._stack = QStackedWidget()
        self._stack.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        tabbox.addWidget(self._stack)

        page1 = TabPage("Page 1")
        self._addPage(page1)

        self._addPage(UpdateSubjects())
        self._addPage(UpdatePupils())
        self._addPage(PupilEdit())
        self._addPage(GradeEdit())
        self._addPage(TextReports())
        self._addPage(Calendar())
        self._lbox.addStretch(1)
        self._addPage(FieldEdit())

        self.selectPage.idToggled.connect(self._switchPage)
#
    def _addPage(self, tab):
        b = QPushButton(tab.name)
        b.setStyleSheet("QPushButton:checked {background-color: #ffd36b;}")
        b.setCheckable(True)
        if self._ntabs == 0:
            b.setChecked(True)
        self._lbox.addWidget(b)
        self.selectPage.addButton(b, self._ntabs)
        self._ntabs += 1
        self._stack.addWidget(tab)
#
    def _switchPage(self, i, checked):
        if checked:
            self._stack.setCurrentIndex(i)
            self._stack.widget(i).enter()
        else:
            self._stack.widget(i).leave()
#
    def closeEvent(self, e):
        tabpage = self._stack.currentWidget()
        if tabpage.clear() and BACKEND.quit():
            super().closeEvent(e)
#
    def init(self):
        years = [(y, print_schoolyear(y)) for y in Dates.get_years()]
        self.year_select.set_items(years)
        thisyear = Dates.get_schoolyear()
        chosenyear = self.year_select.selected()
        if chosenyear != thisyear and thisyear in years:
            self.year_select.reset(thisyear)
        self.year_select.trigger()
#
    def year_changed(self, schoolyear):
        tabpage = self._stack.currentWidget()
        if not tabpage.clear():
            self.year_select.reset(self.schoolyear)
            return
        self.schoolyear = schoolyear
        tabpage.year_changed()

##

class UpdateSubjects(TabPage):
    """Update the subjects list for a class from a table (ods or xlsx).
    """
    def __init__(self):
        super().__init__(_UPDATE_SUBJECTS)
        l = QLabel(_UPDATE_SUBJECTS_TEXT)
        l.setWordWrap(True)
        self.vbox.addWidget(l)
        p = QPushButton(_UPDATE_SUBJECTS_TABLE)
        self.vbox.addWidget(p)
        p.clicked.connect(self.update)
        self.output = QTextEdit()
        self.vbox.addWidget(self.output)
#
    def leave(self):
        """Called when the tab is deselected.
        """
        self.output.clear()
#
    def update(self):
        dir0 = ADMIN._loaddir or os.path.expanduser('~')
        fpath = QFileDialog.getOpenFileName(self, _FILEOPEN,
                dir0, _TABLE_FILE)[0]
        if not fpath:
            return
        ADMIN.set_loaddir(os.path.dirname(fpath))
        cc = BACKEND('UPDATE_SUBJECT_TABLE', FILEPATH = fpath)


        subjects = Subjects(ADMIN.year())
        srctable = subjects.read_source_table(fpath)
        opath = subjects.save_table(srctable)
        self.output.append(_SUBJECTS_CLASS.format(klass = srctable.klass))

##

class UpdatePupils(TabPage):
    """Handle updating of the class lists from the main school database.
    The entries to be changed are shown and may be deselected.
    """
    def __init__(self):
        super().__init__(_UPDATE_PUPILS)
        l = QLabel(_UPDATE_PUPILS_TEXT)
        l.setWordWrap(True)
        self.vbox.addWidget(l)
        p = QPushButton(_UPDATE_PUPILS_TABLE)
        self.vbox.addWidget(p)
        p.clicked.connect(self.update)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setWordWrap(True)
        self.vbox.addWidget(self.tree)
        self.pbdoit = QPushButton(_DO_UPDATE)
        self.pbdoit.clicked.connect(self.doit)
        self.vbox.addWidget(self.pbdoit)
        self.ptables = None
#
    def enter(self):
        """Called when the tab is selected.
        """
        self.pbdoit.setEnabled(False)
#
    def leave(self):
        """Called when the tab is deselected.
        """
        self.pupils = None
        self.ptables = None
        self._cleartree()
#
    def _cleartree(self):
        self.elements = None
        self.tree.clear()
#
    def update(self, review = False):
        self.enter()
        self.pupils = Pupils(ADMIN.year())
        if not review:
            dir0 = ADMIN._loaddir or os.path.expanduser('~')
            fpath = QFileDialog.getOpenFileName(self, _FILEOPEN,
                    dir0, _TABLE_FILE)[0]
            if not fpath:
                return
            ADMIN.set_loaddir(os.path.dirname(fpath))
            try:
                self.ptables = self.pupils.read_source_table(fpath)
            except:
                REPORT('ERROR', _BAD_PUPIL_TABLE.format(path = fpath))
                return
        _delta = self.pupils.compare_new_data(self.ptables)
        changes = False
        self.elements = []
        for k, dlist in _delta.items():
            items = []
            self.elements.append((k, items))
            if not dlist:
                continue
            changes = True
            parent = QTreeWidgetItem(self.tree)
            parent.setText(0, "Klasse {}".format(k))
            parent.setFlags(parent.flags() | Qt.ItemIsTristate
                    | Qt.ItemIsUserCheckable)
            for d in dlist:
                child = QTreeWidgetItem(parent)
                items.append((child, d))
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                op, pdata = d[0], d[1]
                name = pdata.name()
                if op == 'NEW':
                    text = 'Neu: %s' % name
                elif op == 'DELTA':
                    text = 'Ändern %s: %s' % (name, str(d[2]))
                    if len(text) > _DELTA_LEN_MAX:
                        child.setToolTip(0, '<p>' + text + '</p>')
                        text = text[:_DELTA_LEN_MAX - 4] + ' ...'
                elif op == 'REMOVE':
                    text = 'Entfernen: %s' % name
                else:
                    raise Bug("Unexpected operator: %s" % op)
                child.setText(0, text)
                child.setCheckState(0, Qt.Checked)
        if changes:
            self.pbdoit.setEnabled(True)
#
    def doit(self):
        changes = False
        # Filter the changes lists
        delta = {}
        for k, items in self.elements:
            dlist = []
            delta[k] = dlist
            for child, d in items:
                if child.checkState(0) == Qt.Checked:
                    dlist.append(d)
                    changes = True
        if changes:
            self.pupils.update_table(delta)
            ptables = self.ptables
            self._cleartree()
            self.update(True)
        else:
            REPORT('WARN', _WARN_NO_CHANGES)


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    import builtins

    from qtpy.QtWidgets import QApplication#, QStyleFactory
    from qtpy.QtCore import QLocale, QTranslator, QLibraryInfo, QSettings
    from qtpy.QtGui import QIcon

#    print(QStyleFactory.keys())
#    QApplication.setStyle('windows')

    from core.base import init
    app = QApplication([])
    if len(sys.argv) == 2:
        datadir = sys.argv[1]
    else:
        datadir = None
    init(datadir)
    # Persistent Settings:
    builtins.SETTINGS = QSettings(os.path.join(DATA, 'wz-settings'),
                QSettings.IniFormat)

    LOCALE = QLocale(QLocale.German, QLocale.Germany)
    QLocale.setDefault(LOCALE)
    qtr = QTranslator()
    qtr.load("qt_" + LOCALE.name(),
            QLibraryInfo.location(QLibraryInfo.TranslationsPath))
    app.installTranslator(qtr)

    admin = Admin()
    admin.setWindowIcon(QIcon(os.path.join('icons', 'WZ1.png')))
    builtins.ADMIN = admin
    admin.init()
    screen = app.primaryScreen()
    screensize = screen.availableSize()
    admin.resize(screensize.width()*0.8, screensize.height()*0.8)
    admin.show()
    sys.exit(app.exec_())

