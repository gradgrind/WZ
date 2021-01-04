# -*- coding: utf-8 -*-
"""
gui_support.py

Last updated:  2020-01-04

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

import sys, os, builtins, traceback

from qtpy.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, \
        QLabel, QPushButton, QComboBox, QFrame, QTextEdit, \
        QDialog#, QMessageBox, QProgressBar
from qtpy.QtGui import QMovie, QPixmap
from qtpy.QtCore import Qt, QObject, QThread, Signal, Slot, QCoreApplication

### Messages
_UNKNOWN_KEY = "Ungültige Selektion: '{key}'"

# Dialog buttons, etc.
_CANCEL = "Abbrechen"
_OK = "OK"

_INFO_TITLE = "Information"
_WARN_TITLE = "Warnung"
_ERROR_TITLE = "Fehler"
_TRAP_TITLE = "Kritischer Fehler"
_RUN_TITLE = "in Bearbeitung ..."
_DONE_TITLE = "... fertig!"
_OTHER_TITLE = "Rückmeldung"

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
        l = QLabel('<b>%s</b>' % name)
        l.setAlignment(Qt.AlignCenter)
        self.vbox.addWidget(l)
        self.vbox.addWidget(HLine())
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

MESSAGES = {
    'INFO': '$',
    'WARN': 'WARNUNG',
    'ERROR': 'FEHLER',
    'TRAP': 'KRITISCHER FEHLER'
}

class _Report(QDialog):
    """A modal dialog for reporting back to the user. It is a "singleton",
    i.e. only one instance may exist.
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
    _active = False
    _report = Signal(str)
#
    @classmethod
    def report(cls, mtype, msg = None, header = None, runme = None):
        # The first call must be in the main thread (which is no problem
        # as the worker thread can only be started by a call here).
        # The QApplication must have been started before calling this.
        mkey = MESSAGES.get(mtype)
        if not mkey:
            if msg:
                mkey = '???'
            else:
                mkey = '#'
                msg = mtype
        if cls._instance:
            if cls._active:
                if mtype == 'RUN':
                    raise Bug("Background thread within background thread")
                # If the dialog is active, pass reports directly
                # (via signal-slot) to the output window.
                # Note that the signal mechanism requires that
                # <cls._instance> be used here, not just <cls>.
                cls._instance._report.emit((
                        '+++++++++++++++++++++++++++++++++++++++++++\n'
                        '  ** %s **\n%s: %s\n'
                        '-------------------------------------------')
                        % (header or 'REPORT', mkey, msg or '–––'))
                return None
        else:
            cls._instance = cls()
        self = cls._instance
        # Reset the dialog (text, icon, etc.).
        # If 'RUN', mark as "active", start the background thread,
        # then exec_().
        self.text.clear()
        if mtype == 'RUN':
            self._ok.setEnabled(False)
            self._cancel.setVisible(runme.terminate())
            if self.workerT.isRunning():
                raise Bug("Background thread in use")
            self.setWindowTitle(_RUN_TITLE)
            self._title.setText("<h3>%s</h3>" % (header or _RUN_TITLE))
            self.busy = QMovie(os.path.join('icons', 'busy.gif'))
            self._pixmap.setMovie(self.busy)
            self.busy.start()
            # Handle the function to be called
            cls._active = True
            self.workerT.toBackground(runme)
            self.exec_()
            cls._active = False
            return self.workerT.runResult
        if mtype == 'INFO':
            self.setWindowTitle(_INFO_TITLE)
            self._title.setText("<h3>%s</h3>" % (header or _INFO_TITLE))
            self._pixmap.setPixmap(QPixmap(os.path.join('icons', 'info.png')))
            self.text.setPlainText(msg)
        elif mtype == 'WARN':
            self.setWindowTitle(_WARN_TITLE)
            self._title.setText("<h3>%s</h3>" % (header or _WARN_TITLE))
            self._pixmap.setPixmap(QPixmap(os.path.join('icons', 'warning.png')))
            self.text.setPlainText(msg)
        elif mtype == 'ERROR':
            self.setWindowTitle(_ERROR_TITLE)
            self._title.setText("<h3>%s</h3>" % (header or _ERROR_TITLE))
            self._pixmap.setPixmap(QPixmap(os.path.join('icons', 'error.png')))
            self.text.setPlainText(msg)
        elif mtype == 'TRAP':
            self.setWindowTitle(_TRAP_TITLE)
            self._title.setText("<h3>%s</h3>" % (header or _TRAP_TITLE))
            self._pixmap.setPixmap(QPixmap(os.path.join('icons', 'error.png')))
            self.text.setPlainText(msg)
        else:
            self.setWindowTitle(_OTHER_TITLE)
            self._title.setText("<h3>%s</h3>" % (header or _OTHER_TITLE))
            self._pixmap.setPixmap(QPixmap(os.path.join('icons', 'other.png')))
            self.text.setPlainText('%s: %s' % (mkey, msg))
        self.exec_()
        return None
#
    def __init__(self):
        if self._instance:
            raise Bug("Report dialog exists already")
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
        self._cancel = QPushButton(_CANCEL)
        self._cancel.hide()
        bbox.addWidget(self._cancel)
        self._ok = QPushButton(_OK)
        self._ok.setDefault(True)
        bbox.addWidget(self._ok)

        self.workerT = WorkerT()
        self.workerT._message.connect(self._output)
        self.workerT.finished.connect(self.thread_done)
        self._cancel.clicked.connect(self.workerT._cancel)
        self._cancel.clicked.connect(self.hide_cancel)
        self._ok.clicked.connect(self.accept)
        self._report.connect(self._output)
#
    @Slot()
    def _output(self, msg):
        #print("output: " + msg)
        self.text.append(msg)
#
    def hide_cancel(self):
        """The cancel button was pressed. This is only relevant in
        "RUN" dialogs.
        There is a separate connection to the worker (see <__init__>).
        """
        self._cancel.hide()
#
    @Slot()
    def thread_done(self):
        self._cancel.hide()
        self._ok.setEnabled(True)
        # Adjust the header
        self._title.setText("<h3>%s</h3>" % _DONE_TITLE)
        self.busy.stop()
#
    def accept(self):
        #print("ACCEPT")
        super().accept()
#
    def reject(self):
        #print("REJECT")
        if self._cancel.isVisible():
            self._cancel.clicked.emit()
        if self._ok.isEnabled():
            super().reject()

#++++++++++++++++++++++++++++++++++++++++++
builtins.REPORT = _Report.report
#++++++++++++++++++++++++++++++++++++++++++

# Handle uncaught exceptions
class UncaughtHook(QObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This registers the <exception_hook> method as hook with
        # the Python interpreter
        sys.excepthook = self.exception_hook
#
    def exception_hook(self, exc_type, exc_value, exc_traceback):
        """Function handling uncaught exceptions.
        It is triggered each time an uncaught exception occurs.
        """
        log_msg = '{val}$${emsg}'.format(
                val = exc_value, emsg = ''.join(traceback.format_exception(
                        exc_type, exc_value, exc_traceback)))
        # Show message
        REPORT('TRAP', log_msg)

# Create a global instance of <UncaughtHook> to register the hook
qt_exception_hook = UncaughtHook()
