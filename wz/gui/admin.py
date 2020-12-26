# -*- coding: utf-8 -*-
"""
gui/admin.py

Last updated:  2020-12-26

Administration interface.


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

### Messages

### Labels, etc.
_TITLE = "WZ - Administration"

#####################################################


import sys, os, glob
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

from qtpy.QtWidgets import QApplication, QDialog, QWidget, \
    QStackedWidget, QTreeWidget, QTreeWidgetItem, \
    QHBoxLayout, QVBoxLayout, QLabel, \
    QPushButton, QRadioButton, QButtonGroup, \
    QFileDialog
from qtpy.QtCore import Qt

# <core.base> must be the first WZ-import
from core.base import Dates
from gui.gui_support import VLine, HLine, KeySelect
from local.base_config import print_schoolyear, year_path
from core.pupils import Pupils

###

class Admin(QDialog):
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
    def __init__(self):
        super().__init__()
        self.setWindowTitle(_TITLE)
        topbox = QVBoxLayout(self)
        self._ntabs = 0
        tabbox = QHBoxLayout()
        topbox.addLayout(tabbox)
        self._lbox = QVBoxLayout()
        tabbox.addLayout(self._lbox)
        self.selectPage = QButtonGroup()
        self._stack = QStackedWidget()
        tabbox.addWidget(self._stack)

        start_page = TabPage("Start Page")
        self._stack.addWidget(start_page)
        page1 = TabPage("Page 1")
        self._addPage(page1)
        page2 = TabPage("A longer tab name")
        self._addPage(page2)

        self.selectPage.idToggled.connect(self._switchPage)

#
    def _addPage(self, tab):
        self._ntabs += 1
        b = QRadioButton(tab.name)
        self._lbox.addWidget(b)
        self.selectPage.addButton(b, self._ntabs)
        self._stack.addWidget(tab)
#
    def _switchPage(self, i, checked):
        if checked:
            self._stack.setCurrentIndex(i)
#
#    def closeEvent(self, e):
#        if self.clear():
#            super().closeEvent(e)
#
    def init(self):
        years = [(y, print_schoolyear(y)) for y in Dates.get_years()]
        self.year_select.set_items(years)
        self.year_select.trigger()
#
    def year_changed(self, schoolyear):
        if not self.clear():
            self.year_select.reset(self.schoolyear)
            return
        print("Change Year:", schoolyear)
        self.schoolyear = schoolyear
        self.term_select.trigger()
#
    def save(self, force = True):
        if self.clear(force):    # no question dialog
            if self.term[0] == 'S':
                self.pid = self.grade_scene.grade_table.term
            self.group_changed(None)

###

class TabPage(QWidget):
    def __init__(self, name):
        super().__init__()
        self.vbox = QVBoxLayout(self)
        self.name = name
        l = QLabel('<b>%s</b>' % name)
        l.setAlignment(Qt.AlignCenter)
        self.vbox.addWidget(l)
        self.vbox.addWidget(HLine())
        self.vbox.addStretch(1)


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#


def main():
    app     = QApplication(sys.argv)
    tree    = QTreeWidget()
    headerItem  = QTreeWidgetItem()
    item    = QTreeWidgetItem()

    for i in range(3):
        parent = QTreeWidgetItem(tree)
        parent.setText(0, "Parent {}".format(i))
        parent.setFlags(parent.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
        for x in range(5):
            child = QTreeWidgetItem(parent)
            child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
            child.setText(0, "Child {}".format(x))
            child.setCheckState(0, Qt.Unchecked)
    tree.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
#    main()
#    quit(0)

    from core.base import init
    init('DATA')

    _year = '2021'

    import sys
    from qtpy.QtWidgets import QApplication, QStyleFactory
    from qtpy.QtCore import QLocale, QTranslator, QLibraryInfo

#    print(QStyleFactory.keys())
#    QApplication.setStyle('windows')

    app = QApplication(sys.argv)
    LOCALE = QLocale(QLocale.German, QLocale.Germany)
    QLocale.setDefault(LOCALE)
    qtr = QTranslator()
    qtr.load("qt_" + LOCALE.name(),
            QLibraryInfo.location(QLibraryInfo.TranslationsPath))
    app.installTranslator(qtr)

    admin = Admin()
#    admin.init()
    admin.exec_()

