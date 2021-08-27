# -*- coding: utf-8 -*-
"""
ui/wz_main.py

Last updated:  2021-08-24

The "main" window.


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

### Labels, etc.
_TITLE = "WZ – Zeugnisverwaltung"

#####################################################

from importlib import import_module
import sys, os, builtins
os.environ['PYSIDE_DESIGNER_PLUGINS'] = '.'

from PySide6.QtWidgets import QApplication#, QStyleFactory
#print(QStyleFactory.keys())
#QApplication.setStyle('windows')

from PySide6.QtWidgets import QWidget, QDialog, QFrame, QStackedWidget, \
    QHBoxLayout, QVBoxLayout, QLabel, QTextEdit, \
    QPushButton
from PySide6.QtCore import QLocale, QTranslator, QLibraryInfo, QSettings, \
        QTimer
from PySide6.QtGui import QIcon

from ui.ui_support import ui_load, dirDialog
#from ui.wz_communicate import Backend
from ui.wz_dispatch import Dispatch

### -----

# Qt initialization
app = QApplication([])
# Set up language/locale for Qt
LOCALE = QLocale(QLocale.German, QLocale.Germany)
QLocale.setDefault(LOCALE)
qtr = QTranslator()
qtr.load("qt_" + LOCALE.name(),
        QLibraryInfo.location(QLibraryInfo.TranslationsPath))
app.installTranslator(qtr)

### +++++

def main(args, appdir):#, modules):
    # Persistent Settings:
    builtins.SETTINGS = QSettings(
            QSettings.IniFormat, QSettings.UserScope, 'MT', 'WZ')


    dispatcher = Dispatch()
    dispatcher.display()

    return




    # Include selected modules
    builtins.TABS = []
    builtins.FUNCTIONS = {}
    for m in modules:
        DEBUG("Adding ui module", m)
        import_module('ui_modules.' + m)
    DEBUG("FUNCTIONS:", FUNCTIONS)

    # Start communication with the back-end
    Backend()


    # Determine data directory
#TODO: pass datadir to back-end, perhaps as command-line parameter!
# It might be possible to change the datadir from the gui.
# Could use SETTINGS...

#    SETTINGS.setValue('DATA', os.path.join(__basedir, 'DATA'))
#    print("$$$", SETTINGS.value('DATA'), SETTINGS.allKeys())

    try:
        args.remove('--test')
    except:
        testing = False
        datadir = SETTINGS.value('DATA') or ''
    else:
        testing = True
#TODO: This might be disabled or modified in a release version?
# The test data might be provided in a pristine archive, which can be
# unpacked to some work folder and registered there in settings?
        datadir = os.path.join(appdir, 'TESTDATA')

#TODO: If no DATADIR, get it from "settings".
# If none set, need to select one, or else load the test data, or
# start from scratch. Starting from scratch one would need to select
# a folder and immediately edit a calendar – perhaps the one from the
# test data could be taken as a starting point (changing to current
# year, as in migrate_year). Also other files can be "borrowed" from
# the test data. There should be a prompt to add pupils (can one do
# this manually when there are none present?).

    main_window = MainWindow(datadir)

    app.setWindowIcon(QIcon(os.path.join('icons', 'WZ1.png')))
    screen = app.primaryScreen()
    screensize = screen.availableSize()
    main_window.resize(screensize.width()*0.8, screensize.height()*0.8)
    main_window.show()
    sys.exit(app.exec_())

###

#TODO: There would need to be an explanatory dialog before showing the
# directory chooser ...
def dialog_schooldata():
    d = dirDialog('Select Data Folder')
    DEBUG("Set data folder:", d)
    return d

###

class MainWindow(QWidget):
    def __init__(self, datadir):
        """Note that some of the initialization is done after a short
        delay: <init> is called using a single-shot timer.
        """
        self.__datadir = datadir
        super().__init__()
        self.setWindowTitle(_TITLE)
        topbox = QVBoxLayout(self)
        # ---------- Title Box ---------- #
        titlebox = QHBoxLayout()
        topbox.addLayout(titlebox)
        self.year_term = QLabel()
        titlebox.addWidget(self.year_term)
        titlebox.addStretch(1)
        tab_title = QLabel()
        titlebox.addWidget(tab_title)
        titlebox.addStretch(1)
        topbox.addWidget(HLine())
        # ---------- Tab Box ---------- #
        self.tab_widget = TabWidget(tab_title)
        topbox.addWidget(self.tab_widget)
        for tab in TABS:
            self.tab_widget.add_page(tab)
        # Run the <init> method when the event loop has been entered:
        QTimer.singleShot(10, self.init)
#
    def init(self):
        # <self.__datadir> is only used here
        if not self.__datadir:
            self.__datadir = dialog_schooldata()
            if not self.__datadir:
                app.exit(1)
        BACKEND('BASE_set_datadir', datadir = self.__datadir)
        # --> <self.SET_DATADIR>

#        BACKEND('BASE_get_school_data')
#        BACKEND('BASE_get_years')
#
    def closeEvent(self, e):
#        DEBUG("CLOSING CONTROL")
        if self.tab_widget.check_unsaved():
            backend_instance.terminate()
            e.accept()
        else:
            e.ignore()
#
    def SET_DATADIR(self, schooldata):
        """CALLBACK: If <schooldata> is null/false (<NONE>), a new data
        folder must be selected.
        Otherwise <schooldata> contains the information needed to set up
        the main window.
        """
        if not schooldata:
            self.__datadir = NONE
            self.init()
            return
#TODO:
        print("#TODO: Set up window\n", schooldata)
#?
    def GET_DATADIR(self):
        """CALLBACK: No valid data folder is set.
        Either choose an existing one or start a fresh one.
        """
        dpath = dirDialog()
        if not dpath:
#TODO ...
            pass
        # Get calendar file
#CONFIG isn't there yet!
        cpath = os.path.join(dpath, CONFIG)
        # Load in editor. If missing, load migrated test file.
#
    def SET_SCHOOL_DATA(self, data):
        self.school_data = data
#TODO ---
        print('SCHOOL_DATA', self.school_data, flush = True)
#
#TODO
    def SET_YEARS(self, years, current):
        self.year_term.setText("<strong>2015 – 2016; 1. Halbjahr</strong>")
        self.tab_widget.select(TAB0)   # Enter default tab
#
    def year_changed(self, schoolyear):
        tabpage = self.tab_widget.current_page()
        if tabpage.year_change_ok():
            BACKEND('BASE_set_year', year = schoolyear) # ... -> YEAR_CHANGED
            return True
        return False
#
    def YEAR_CHANGED(self):
        tabpage = self.tab_widget.current_page()
        tabpage.enter()
#
    def current_year(self):
        return self.year_select.selected()
#
#    def set_year(self, year):
#        self.year_select.reset(year)
#        self.year_select.trigger()

    @classmethod
    def setup(cls, datadir):
        """Call this once to start the application.
        <datadir> is the full path to the data folder. If it is empty or
        otherwise invalid, a dialog window will deal with setting it up.
        """
        builtins.ADMIN = cls(datadir)
        FUNCTIONS['base_SET_YEAR'] = ADMIN.SET_YEAR
#        FUNCTIONS['base_SET_YEARS'] = ADMIN.SET_YEARS
        FUNCTIONS['base_SET_SCHOOL_DATA'] = ADMIN.SET_SCHOOL_DATA
#        FUNCTIONS['base_YEAR_CHANGED'] = ADMIN.YEAR_CHANGED

###

class TabWidget(QWidget):
    def __init__(self, title_label):
        self.title_label = title_label
        super().__init__()
        tabbox = QHBoxLayout(self)
        self._lbox = QVBoxLayout()
        tabbox.addLayout(self._lbox)
        self._stack = QStackedWidget()
        self._stack.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        tabbox.addWidget(self._stack)
        self.tab_buttons = []
        self.index = -1
#
    def add_page(self, tab):
        try:
            i = int(tab)
        except TypeError:
            b = TabButton(tab.name, self)
            self.tab_buttons.append(b)
            self._lbox.addWidget(b)
            self._stack.addWidget(tab)
        else:
            if i:
                self._lbox.addSpacing(i)
            else:
                self._lbox.addStretch(1)
#
    def select(self, index):
        i0 = self._stack.currentIndex()
        if i0 == index:
            # No change
            self.tab_buttons[i0].setChecked(True)
            return
        elif i0 >= 0:
            # Check that the old tab can be left
            tab0 = self._stack.widget(i0)
            if tab0.leave_ok():
                tab0.leave()
                # Deselect old button
                self.tab_buttons[i0].setChecked(False)
            else:
                # Deselect new button
                self.tab_buttons[index].setChecked(False)
                return
        # Select new button
        self.tab_buttons[index].setChecked(True)
        # Enter new tab
        self._stack.setCurrentIndex(index)
        tab = self._stack.widget(index)
        tab.enter()
        if self.title_label:
            self.title_label.setText('<b>%s</b>' % tab.name)
#
    def check_unsaved(self):
        """Called when a "quit program" request is received.
        Check for unsaved data, asking for confirmation if there is
        some. Return <True> if it is ok to continue (quit).
        """
        w = self._stack.currentWidget()
        if w:
            return w.leave_ok()
        return True
#
    def current_page(self):
        return self._stack.currentWidget()
##
class TabButton(QPushButton):
    """A custom class to provide special buttons for the tab switches.
    """
    _stylesheet = "QPushButton:checked {background-color: #ffd36b;}"
#
    def __init__(self, label, tab_widget):
        super().__init__(label)
        self.tab_widget = tab_widget
        self.index = len(tab_widget.tab_buttons)
        self.setStyleSheet(self._stylesheet)
        self.setCheckable(True)
        self.clicked.connect(self._selected)
#
    def _selected(self):
        self.tab_widget.select(self.index)
