# -*- coding: utf-8 -*-
"""
gui_support.py

Last updated:  2020-12-26

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

import os, builtins, traceback

from qtpy.QtWidgets import (QApplication, QStyle,
        QHBoxLayout, QVBoxLayout,
        QLabel, QPushButton, QComboBox,
        QFrame, QTextEdit,
        QButtonGroup, QBoxLayout,
        QDialog, QCalendarWidget, QMessageBox,
        QProgressBar,
        QTableWidget, QTableWidgetItem, QListWidgetItem)
from qtpy.QtGui import QIcon, QMovie, QPixmap#, QFont
from qtpy.QtCore import Qt, QDate, QObject, QThread, Signal, Slot

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
_RUN_TITLE = "in Bearbeitung ..."

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


############# Using threads for long-running tasks #############
# There is so much – sometimes conflicting – information on this theme
# that I'm not sure this approach is optimal, or even 100% correct ...

class WorkerT(QThread):
    _message = Signal(str)
#    _progress = Signal(str, int)

    def toBackground(self, op):
        if self.isRunning():
            raise Bug("Thread already in use")
        self._op = op
        op._message = self.message
        self.start()
#
    def run(self):
        # Run the code in a try-block because errors may not be handled
        # clearly.
        try:
            self.runResult = self._op.run()
        except RuntimeError as e:
            print ("?1")
            self.runResult = None
        except:
            tb = traceback.format_exc()
            print ("?2\n%s" % tb)
            self.runResult = None
        self._op = None
#
    def message(self, msg):
        self._message.emit(msg)
#
    @Slot()
    def _cancel(self):
        self._op.terminate()

###

class _Feedback(QDialog):
    """A modal dialog for reporting back to the user.
    It can simply present a piece of information, such as a warning or
    error message, or it can show the progress of a longer-running
    function (running in a separate thread).
...
    The "function" should actually be a class with a <run> method.
    There is a cancel-button which can try to terminate the running code.
    This can only work if the code is designed to allow this. This
    involves implementing a <terminate> method on the function-class.
    """
    _instance = None
    _report = Signal(str, str)
#
    @classmethod
    def fetch(cls):
        """This method is necessary because the class is instantiated
        only once, but this must wait until the QApplication has been
        started.
        """
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
#
    def __init__(self):
        super().__init__()
        self.resize(600, 400)
        #self.setWindowFlag(Qt.FramelessWindowHint)
        vbox = QVBoxLayout(self)

        # Header
        hbox = QHBoxLayout()
        vbox.addLayout(hbox)
        self._pixmap = QLabel()
        hbox.addWidget(self._pixmap)

        self._title = QLabel()
        #self._title.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self._title.setAlignment(Qt.AlignCenter)
        hbox.addWidget(self._title, 1)

#        self.prog = QProgressBar()
#        #self.prog.setMinimumWidth(100)
#        vbox.addWidget(self.prog)
#        self.prog.setRange(0,0)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        vbox.addWidget(self.text)

        vbox.addWidget(HLine())
        bbox = QHBoxLayout()
        vbox.addLayout(bbox)
        bbox.addStretch(1)
        self._cancel = QPushButton()
        self._cancel.clicked.connect(self.do_cancel)
        bbox.addWidget(self._cancel)
        self._report.connect(self.report)
        self.workerT = WorkerT()
        self.workerT._message.connect(self._output)
        self.workerT.finished.connect(self._done)
#        self.workerT._progress.connect(self._call)
#
    def closeEvent(self, e):
        """Clicking window-close should have the same effect as pressing
        the "Cancel" button.
        """
        e.ignore()
        self._cancel.click()
#
    def do_cancel(self):
        if self.workerT.isRunning():
            self.workerT._cancel()
        else:
            self.reject()
#
    def info(self, message, header = None):
        self._cancel.setText(_OK)
        self.setWindowTitle(_INFO_TITLE)
        self._title.setText("<h3>%s</h3>" % (header or _INFO_TITLE))
        self._pixmap.setPixmap(QPixmap('info.png'))
        self.text.setPlainText(message)
        self.exec_()
#
    def warn(self, message, header = None):
        self._cancel.setText(_OK)
        self.setWindowTitle(_WARN_TITLE)
        self._title.setText("<h3>%s</h3>" % (header or _WARN_TITLE))
        self._pixmap.setPixmap(QPixmap('warning.png'))
        self.text.setPlainText(message)
        self.exec_()
#
    def error(self, message, header = None):
        self._cancel.setText(_OK)
        self.setWindowTitle(_ERROR_TITLE)
        self._title.setText("<h3>%s</h3>" % (header or _ERROR_TITLE))
        self._pixmap.setPixmap(QPixmap('error.png'))
        self.text.setPlainText(message)
        self.exec_()
#
    def progress(self, fn, header):
        if self.workerT.isRunning():
            raise Bug("Background thread in use")
        self._cancel.setText(_CANCEL)
        self.setWindowTitle(_RUN_TITLE)
        self._title.setText("<h3>%s</h3>" % (header or _RUN_TITLE))
        self.text.clear()
        _m = QMovie('busy.gif')
        self._pixmap.setMovie(_m)
        _m.start()
        # Handle the function to be called
        self.workerT.toBackground(fn)
        self.exec_()
        return self.workerT.runResult
#
    @Slot()
    def report(self, mtype, msg):
        if mtype == 'INFO':
            if self.workerT.isRunning():
                self._output(msg)
            else:
                self.info(msg)
        elif mtype == 'WARN':
            if self.workerT.isRunning():
                self._output('%s: %s'(_WARN_TITLE.upper(), _msg))
            else:
                self.warn(msg)
        elif mtype == 'ERROR':
            if self.workerT.isRunning():
                self._output('%s: %s'(_ERROR_TITLE.upper(), _msg))
            else:
                self.error(msg)
        else:
            if mtype:
                msg = '?%s: %s' % ('' if mtype == '?' else mtype, msg)
            if self.workerT.isRunning():
                self._output(msg)
            else:
                print(msg)
#
    @Slot()
    def _done(self):
        #print("DONE!")
        self.reject()
#
    @Slot()
    def _output(self, msg):
        #print("output: " + msg)
        self.text.append(msg)
#
#    def _call (self, msg, percent):
#        print("$1:", percent, msg)

###

def report(msg, header = None, runme = None):
    """Pop-up reports, and logging ... (TODO!).
    """
#TODO: logging
    if msg == 'RUN':
        return _Feedback.fetch().progress(runme, header)
    try:
        mtype, text = msg.split(':', 1)
    except:
        mtype = '?'
        text = msg
    _Feedback.fetch()._report.emit(mtype, text)

#++++++++++++++++++++++++++++++++++++++++++
builtins.REPORT = report
