# -*- coding: utf-8 -*-
"""
ui/ui_support.py

Last updated:  2021-01-31

Support stuff for the GUI: dialogs, etc.


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

import sys, os, builtins, traceback

from qtpy.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, \
        QLabel, QPushButton, QComboBox, QFrame, QTextEdit, \
        QDialog, QTreeWidget, QTreeWidgetItem#, QMessageBox, QProgressBar
from qtpy.QtGui import QMovie, QPixmap
from qtpy.QtCore import Qt, QObject, QThread, Signal, Slot, QCoreApplication

### Messages
_UNKNOWN_KEY = "Ungültige Selektion: '{key}'"

# Dialog buttons, etc.
_CANCEL = "Abbrechen"
_OK = "OK"

###

class GuiError(Exception):
    pass

###

class HLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

###

class VLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)

###

class BoldLabel(QLabel):
    def __init__(self, text):
        super().__init__('<b>' + text + '</b>')

###

class KeySelect(QComboBox):
    def __init__(self, value_mapping = None, changed_callback = None):
        """A selection widget for key-description pairs. The key is the
        actual selection item, but the description is displayed for
        human consumption.
        <value_mapping> is a list: ((key, display text), ...)
        To work with a callback, pass a function with a single parameter
        (the new key) as <changed_callback>. If this function does not
        return a true value, the selection will be reset to the last value.
        """
        super().__init__()
        self._cb = changed_callback
        self.set_items(value_mapping)
# Qt note: If connecting after adding the items, there seems
# to be no signal; if before, then the first item is signalled.
        self.currentIndexChanged.connect(self._new)
#
    def selected(self):
        try:
            return self.value_mapping[self.currentIndex()][0]
        except:
            return None
#
    def _new(self, index):
        if self.value_mapping and self.changed_callback:
            key = self.value_mapping[index][0]
            self.changed_callback(key)
#
    def reset(self, key):
        self.changed_callback = None        # suppress callback
        i = 0
        for k, _ in self.value_mapping:
            if k == key:
                self.setCurrentIndex(i)
                break
            i += 1
        else:
            self.changed_callback = self._cb    # reenable callback
            raise GuiError(_UNKNOWN_KEY.format(key = key))
        self.changed_callback = self._cb    # reenable callback
#
    def trigger(self):
        self._new(self.currentIndex())
#
    def set_items(self, value_mapping, index = 0):
        """Set / reset the items.
        <value_mapping> is a list: ((key, display text), ...)
        This will not cause a callback.
        """
        self.changed_callback = None        # suppress callback
        self.value_mapping = value_mapping
        self.clear()
        if value_mapping:
            self.addItems([text for _, text in value_mapping])
            self.setCurrentIndex(index)
        self.changed_callback = self._cb    # reenable callback

###

def QuestionDialog(title, message):
    qd = QDialog()
    qd.setWindowTitle(title)
    vbox = QVBoxLayout(qd)
    vbox.addWidget(QLabel(message))
    vbox.addWidget(HLine())
    bbox = QHBoxLayout()
    vbox.addLayout(bbox)
    bbox.addStretch(1)
    cancel = QPushButton(_CANCEL)
    cancel.clicked.connect(qd.reject)
    bbox.addWidget(cancel)
    ok = QPushButton(_OK)
    ok.clicked.connect(qd.accept)
    bbox.addWidget(ok)
    cancel.setDefault(True)
    return qd.exec_() == QDialog.Accepted

###

def TextDialog(title, text):
    td = QDialog()
    td.setWindowTitle(title)
    vbox = QVBoxLayout(td)
    textedit = QTextEdit(text)
    vbox.addWidget(textedit)
    vbox.addWidget(HLine())
    bbox = QHBoxLayout()
    vbox.addLayout(bbox)
    bbox.addStretch(1)
    cancel = QPushButton(_CANCEL)
    cancel.clicked.connect(td.reject)
    bbox.addWidget(cancel)
    ok = QPushButton(_OK)
    ok.clicked.connect(td.accept)
    bbox.addWidget(ok)
    cancel.setDefault(True)
    if td.exec_() == QDialog.Accepted:
        return textedit.toPlainText()
    return None

###

class TabPage(QWidget):
    """Base class for widgets to be used as a tab page in the admin gui.
    Subclass this to add the required functionality.
    """
    def __init__(self, name):
        super().__init__()
#        self.setMaximumWidth(800)
        self.setMinimumWidth(600)
        self.vbox = QVBoxLayout(self)
        self.name = name
#        l = QLabel('<b>%s</b>' % name)
#        l.setAlignment(Qt.AlignCenter)
#        self.vbox.addWidget(l)
#        self.vbox.addWidget(HLine())
#        self.vbox.addStretch(1)
#
    def enter(self):
        pass
#
    def leave(self):
        pass
#
    def clear(self):
        return True
#
    def year_changed(self):
        pass

###

def TreeDialog(title, message, data, button = None):
    """A simple two-level tree widget as selection dialog.
    Top level items may not be selected, they serve only as categories.
    Can take additional buttons ...?
    """
    select = QDialog()
    select.setWindowTitle(title)
#-
    def select_item(qtwi, col):
        p = qtwi.parent()
        if p:
            select.result = (p.text(0), qtwi.text(0))
            select.accept()
#-
    def xb_clicked():
        select.result = (None, button)
        select.accept()
#-
    layout = QVBoxLayout(select)
    layout.addWidget(QLabel(message))
    tree = QTreeWidget()
    layout.addWidget(tree)
    tree.setColumnCount(1)
    tree.setHeaderHidden(True)
    tree.itemClicked.connect(select_item)
    for category, items in data:
        tline = QTreeWidgetItem(tree)
        tline.setText(0, category)
        for item in items:
            tatom = QTreeWidgetItem(tline)
            tatom.setText(0, item)
    tree.expandAll()
    select.resize(500, 300)
    select.result = None
    # Now the buttons
    layout.addWidget(HLine())
    bbox = QHBoxLayout()
    layout.addLayout(bbox)
    bbox.addStretch(1)
    cancel = QPushButton(_CANCEL)
    cancel.setDefault(True)
    cancel.clicked.connect(select.reject)
    bbox.addWidget(cancel)
    if button:
        xb = QPushButton(button)
        xb.clicked.connect(xb_clicked)
        bbox.addWidget(xb)
    select.exec_()
    return select.result


#def PopupInfo(title, message):
#    _InfoDialog(title, message, QMessageBox.Information)
##
#def PopupWarning(title, message):
#    _InfoDialog(title, message, QMessageBox.Warning)
##
#def PopupError(title, message):
#    _InfoDialog(title, message, QMessageBox.Critical)
##
#def _InfoDialog(title, message, mtype):
#    mbox = QMessageBox(mtype, title, message,
#            QMessageBox.NoButton)
#    mbox.addButton(_OK, QMessageBox.AcceptRole)
#    mbox.exec_()
