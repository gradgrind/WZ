# -*- coding: utf-8 -*-
"""
gui_support.py

Last updated:  2020-12-23

Support stuff for the GUI: dialogs, etc.


=+LICENCE=============================
Copyright 2019-2020 Michael Towers

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

import os, builtins

from qtpy.QtWidgets import (QApplication, QStyle,
        QHBoxLayout, QVBoxLayout,
        QLabel, QPushButton, QComboBox,
        QFrame, QTextEdit,
        QButtonGroup, QBoxLayout,
        QDialog, QCalendarWidget, QMessageBox,
        QProgressDialog,
        QTableWidget, QTableWidgetItem, QListWidgetItem)
from qtpy.QtGui import QIcon #, QFont
from qtpy.QtCore import Qt, QDate, QObject, Signal, Slot

### Messages
_UNKNOWN_KEY = "Ungültige Selektion: '{key}'"

# Dialog buttons, etc.
_CANCEL = "Abbrechen"
_ACCEPT = "Übernehmen"
_OK = "OK"
_SETALL = "Alle setzen"
_RESETALL = "Alle zurücksetzen"

_BUSY = "Fortschritt ..."

_DATE = "Datum"

_INFO_TITLE = "Information"
_WARN_TITLE = "Warnung"
_ERROR_TITLE = "Fehler"

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

def PopupInfo(title, message):
    _InfoDialog(title, message, QMessageBox.Information)
#
def PopupWarning(title, message):
    _InfoDialog(title, message, QMessageBox.Warning)
#
def PopupError(title, message):
    _InfoDialog(title, message, QMessageBox.Critical)
#
def _InfoDialog(title, message, mtype):
    mbox = QMessageBox(mtype, title, message,
            QMessageBox.NoButton)
    mbox.addButton(_OK, QMessageBox.AcceptRole)
    mbox.exec_()

###

def report(msg):
    """Pop-up reports, and logging ... (TODO!).
    """
#TODO: logging
    try:
        mtype, text = msg.split(':', 1)
    except:
        mtype = 'INFO'
        text = msg
    if not mtype:
#TODO: logging only
        print(msg)
        return
    if mtype == 'INFO':
        PopupInfo(_INFO_TITLE, text)
    elif mtype == 'WARN':
        PopupWarning(_WARN_TITLE, text)
    elif mtype == 'ERROR':
        PopupError(_ERROR_TITLE, text)
    else:
        PopupInfo(mtype, text)
builtins.REPORT = report
