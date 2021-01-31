# -*- coding: utf-8 -*-
"""
ui/WZ.py

Last updated:  2021-01-31

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

### Labels, etc.
_TITLE = "WZ – Zeugnisverwaltung"
_REPORT_TITLE = "WZ – Info"

# Dialog buttons, etc.
_CANCEL = "Abbrechen"
_OK = "OK"

_RUN_TITLE = "in Bearbeitung ..."
_INFO_TITLE = "Information"
_WARN_TITLE = "Warnung"
_ERROR_TITLE = "Fehler"
_UNEXPECTED_TITLE = "Unerwartetes Feedback"
_TRAP_TITLE = "Kritischer Fehler"
_INTERRUPT = "Abbrechen"
_INTERRUPT_QUESTION = "Wenn eine Zeit lang keine Fortschrittszeichen" \
        " erscheinen,\nkann es sein, dass ein unbekanntes Problem" \
        " vorliegt.\nIn diesem Fall ist es sinnvoll abzubrechen," \
        "\nobwohl möglicherweise Daten verloren gehen.\n" \
        "   Wollen Sie die Operation wirklich abbrechen?"
_INTERRUPTED = "*** ABGEBROCHEN ***"

INFO_TYPES = {    # message-type -> (message level, displayed type)
    'OUT': (0, '...'),
    'INFO': (1, ':::'),
    'WARN': (2, 'WARNUNG:'),
    'ERROR': (3, 'FEHLER:'),
    'UNEXPECTED': (4, '???:'),
    'TRAP': (5, 'KRITISCHER FEHLER:')
}

#####################################################


import sys, os, builtins, traceback
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    APPDIR = os.path.dirname(this)
    #print("&&&", APPDIR)
    sys.path[0] = APPDIR
    from qtpy.QtWidgets import QApplication#, QStyleFactory
#    print(QStyleFactory.keys())
#    QApplication.setStyle('windows')
    app = QApplication([])

from qtpy.QtWidgets import QWidget, QDialog, QFrame, \
    QStackedWidget, QTreeWidget, QTreeWidgetItem, \
    QHBoxLayout, QVBoxLayout, QLabel, QTextEdit, \
    QPushButton, QButtonGroup, \
    QFileDialog
from qtpy.QtCore import Qt, QDateTime, QProcess
from qtpy.QtGui import QMovie, QPixmap, QColor

from ui.ui_support import QuestionDialog, HLine, TabPage, KeySelect, \
        GuiError

builtins.TABS = []
builtins.FUNCTIONS = {}
#TODO: first page ...
TABS.append(TabPage("Page 1"))
import ui.tab_subjects
import ui.tab_pupils_update
#        self._addPage(PupilEdit())
#        self._addPage(GradeEdit())
#        self._addPage(TextReports())
#        self._addPage(Calendar())
#        self._lbox.addStretch(1)
#        self._addPage(FieldEdit())

####+++++++++++++++++++++++++++++++++++++++

sys.stdin.reconfigure(encoding='utf-8') # requires Python 3.7+
PARAGRAPH = '¶'
SPACE = '¬'
backend_instance = None
class _Backend(QDialog):
    """Manage communication with the "back-end". Provide a pop-up (modal
    dialog) to provide visual feedback to the user concerning the progress
    and success of the commands.
    This is a "singleton" class, i.e. only one instance may exist.
    Commands have the form:
            COMMAND parameter1:value1 parameter2:value ...
        In values:
            Spaces (' ') are represented by '¬', so '¬' should not be used
            in values.
            Newlines are represented by '¶', so the character '¶' should
            not be used in values.
    Feedback from the back-end is via messages. There are several types
    of message:
        '+++': Function completed successfully.
        '---': Function completed with errors.
        '>>>type message': A report. 'type' can be 'INFO', 'WARN', 'ERROR'
                or 'TRAP'. 'message' uses the same encoding as command
                parameter values (see above).
        '...text': Output from some subprogram (e.g. LibreOffice).
        ':::CALLBACK parameter1:value1 parameter2:value ...': A callback
                to the front-end, similar to the COMMAND to this handler.
    The messages '+++' and '---' are always the last messages sent in
    response to a COMMAND. No further COMMANDs are possible until one
    of these messages has been received.

    All communication is via 'utf-8' streams.
    """
    headers = [
        # index 0 should never be used:
        None,
        _INFO_TITLE,
        _WARN_TITLE,
        _ERROR_TITLE,
        _UNEXPECTED_TITLE,
        _TRAP_TITLE
    ]
#
    def __init__(self):
        if backend_instance:
            print("BIG PROBLEM: <_Backend> instance exists already")
            self.terminate()
            quit(1)
        super().__init__()
        self.process = None
        ### Set up the dialog window
        self.resize(600, 400)
        self.setWindowTitle(_REPORT_TITLE)
        #self.setWindowFlag(Qt.FramelessWindowHint)
        vbox = QVBoxLayout(self)
        ## Header
        hbox = QHBoxLayout()
        vbox.addLayout(hbox)
        self._pixmap = QLabel()
        hbox.addWidget(self._pixmap)
        self._title_label = QLabel()
        #self._title_label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self._title_label.setAlignment(Qt.AlignCenter)
        hbox.addWidget(self._title_label, 1)
        ## Text display widget
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        vbox.addWidget(self.text)
        ## Button area
        vbox.addWidget(HLine())
        bbox = QHBoxLayout()
        vbox.addLayout(bbox)
        bbox.addStretch(1)
        self._cancel = QPushButton(_CANCEL)
        self._cancel.clicked.connect(self.reject)
        bbox.addWidget(self._cancel)
        self._ok = QPushButton(_OK)
        self._ok.setDefault(True)
        self._ok.clicked.connect(self.accept)
        bbox.addWidget(self._ok)
        ## Icon area
        self._busy = QMovie(os.path.join('icons', 'busy.gif'))
        # index 0 should never be used:
        self._pixmaps = [
            None, #QPixmap(os.path.join('icons', 'other.png')),
            QPixmap(os.path.join('icons', 'info.png')),
            QPixmap(os.path.join('icons', 'warning.png')),
            QPixmap(os.path.join('icons', 'error.png')),
            QPixmap(os.path.join('icons', 'unexpected.png')),
            QPixmap(os.path.join('icons', 'critical.png')),
        ]
        self.colours = [QColor('#dd79c2'),
                QColor('#005900'), QColor('#ff8000'),
                QColor('#c90000'), QColor('#0019ff'), QColor('#8f00cc')]
#
    def encode(self, text):
        return PARAGRAPH.join(text.rstrip().replace(' ', SPACE).splitlines())
#
    def decode(self, text):
        return text.replace(SPACE, ' ').replace(PARAGRAPH, '\n')
#
    def handle_in(self):
        while True:
            data = self.process.readLine()
            line = bytes(data).decode("utf8").rstrip()
#TODO: The input lines should be logged?
            self.cb_lines.append(line)
            if not line:
                return
            # A line has been received from the back-end.
            # Decode it and act upon it.
            key = line[:3]
            line = line[3:].lstrip()
            if key == '+++':        # successful completion
                self.task_done(True)
            elif key == '---':      # unsuccessful completion
                self.task_done()
            elif key == '...':      # output from external subprocesses
                self.report('OUT', line)
            elif key == '>>>':      # REPORT
                self.report(*line.split(None, 1))
            elif key == ':::':      # callback
                self.do_callback(line)
            else:                   # unexpected output
                self.report('UNEXPECTED', line)
#
    def do_callback(self, line):
        ### decode
        plist = line.split()
        try:
            function_name = plist.pop(0)
            function = FUNCTIONS[function_name]
            # deal with the parameters
            params = {}
            for p in plist:
                key, val = p.split(':', 1)
                params[key] = self.decode(val)
        except:
            INFO('TRAP', 'Invalid callback:\n  %s' % line.rstrip())
            return
        ### execute
        try:
            function(**params)
        except:
            log_msg = traceback.format_exc()
            INFO('TRAP', log_msg)
#
#TODO: logging!
#
    def report(self, mtype, msg):
        # The QApplication must have been started before calling this.
        msglevel, msgtype = INFO_TYPES[mtype]
        if msglevel > self._level:
            self._level = msglevel
        self.text.setTextColor(self.colours[msglevel])
        msg1 = self.decode(msg)
        if msglevel == 0:
            self.text.append('%s %s' % (msgtype, msg1))
        else:
            self.text.append((
                    '+++++++++++++++++++++++++++++++++++++++++++\n'
                    '%s %s\n'
                    '-------------')
                    % (msgtype, msg1))
#
    def reject(self):
        if self._complete:
            super().reject()
        elif QuestionDialog(_INTERRUPT, _INTERRUPT_QUESTION):
            self.terminate()
#
    def command(self, fn, **parms):
        """Send a command to the back-end. Returned messages are passed
        to a modal dialog, which is only popped up after a short time-out.
        If the back-end command completes without displaying information
        before the time-out, the dialog will not be popped up at all.
        A busy icon/title will indicate in the modal dialog that the
        command is still running.
        """
        self.cb_lines = []  # remember all lines from back-end
        plist = ['%s:%s' % (key, self.encode(val))
                for key, val in parms.items()]
        msg = '%s %s\n' % (fn, ' '.join(plist))
        #print('!!!SEND:', msg, flush = True)
        if not self.process:
            # Start process
            self.process = QProcess()
            self.process.setProcessChannelMode(QProcess.MergedChannels)
            self.process.readyRead.connect(self.handle_in)
            #self.process.stateChanged.connect(self.handle_state)
            self.process.finished.connect(self.process_finished)
            exec_params = [os.path.join(APPDIR, 'core', 'main.py')]
            if DATADIR:
                exec_params.append(DATADIR)
            self.process.start(sys.executable, exec_params)
            self._complete = True
        if not self._complete:
            print("BIG PROBLEM: Program error, back-end not ready.\n"
                    "COMMAND: %s" % msg)
            self.terminate()
            quit(1)
        self.text.clear()
        end_time = QDateTime.currentMSecsSinceEpoch() + 500
        self.process.write(msg.encode('utf-8'))
        # Remember the highest-level message (none, info, warning, error, trap).
        self._level = 0
        self._complete = False  # set to <True> when the command finishes
        self._ok.setEnabled(False)
        self._cancel.show()
        self._active = False    # set to <True> when the pop-up is shown
        while True:
            if not self.process:
                print("BIG PROBLEM: Process failed ...")
                for l in self.cb_lines:
                    print(l)
                quit(1)
            self.process.waitForReadyRead(100)
            # The available input is read via a signal handler (<handle_in>),
            # not here.
            if self._complete and self._level == 0:
                # Completed with no significant messages to display
                break
            if QDateTime.currentMSecsSinceEpoch() > end_time:
                # Show modal dialog
                self.become_active()
                break
#
    def become_active(self):
        if self._complete:
            self.set_level()
        else:
            self._pixmap.setMovie(self._busy)
            self._title_label.setText("<h3>%s</h3>" % _RUN_TITLE)
            self._busy.start()
        # Show modal dialog
        self._active = True
        self.exec_()
        self._active = False
#
    def task_done(self, ok = False):
        """<ok> is true only when a '+++' is received from the back-end.
        """
#TODO: Do something with <ok>?
        if self._active:
            if self._level == 0:
                # End dialog automatically
                self.accept()
            else:
                self._busy.stop()
                self.set_level()
        self._complete = True
#
    def process_finished(self):
        if not self._complete:
            self.report('TRAP', _INTERRUPTED)
            self.task_done()
        self.process = None
#
    def set_level(self):
        # Adjust the header
        self._pixmap.setPixmap(self._pixmaps[self._level])
        self._title_label.setText("<h3>%s</h3>" % self.headers[self._level])
        self._cancel.hide()
        self._ok.setEnabled(True)
#
    def terminate(self):
        if self.process:
            self.process.kill()
            self.process.waitForFinished()

###

backend_instance = _Backend()
builtins.BACKEND = backend_instance.command
builtins.INFO = backend_instance.report

####---------------------------------------

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
        self.year_select.setMinimumWidth(150)
        titlebox.addWidget(self.year_select)
        titlebox.addStretch(1)
        self.tab_title = QLabel()
        titlebox.addWidget(self.tab_title)
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

        for tab in TABS:
            self._addPage(tab)
        self._lbox.addStretch(1)
#TODO: If all the tabs are in a list, this is not so easy to add after
# the stretch. Perhaps a "special" tab type for space/stretch?
#        self._addPage(FieldEdit())

        self.selectPage.idToggled.connect(self._switchPage)
        self._switchPage(0, True)   # Enter default tab
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
            tab = self._stack.widget(i)
            tab.enter()
            self.tab_title.setText('<b>%s</b>' % tab.name)
        else:
            self._stack.widget(i).leave()
#
    def closeEvent(self, e):
        tabpage = self._stack.currentWidget()
#TODO: Do I still use tabpage.clear() ?
        if tabpage.clear() and backend_instance.terminate():
            super().closeEvent(e)
#
    def init(self):
        BACKEND('BASE_get_years')
#
    def SET_YEARS(self, years, current):
        ylist = [y.split(':', 1) for y in years.split('|')]
        self.year_select.set_items(ylist)
        chosenyear = self.year_select.selected()
        if chosenyear != current:
            try:
                self.year_select.reset(current)
                chosenyear = current
            except GuiError:
                pass
        self.set_year(chosenyear)
#
    def year_changed(self, schoolyear):
        BACKEND('BASE_set_year', year = schoolyear)
        self.set_year(schoolyear)
#
    def set_year(self, schoolyear):
        tabpage = self._stack.currentWidget()
        if not tabpage.clear():
            self.year_select.reset(self.schoolyear)
            return
        self.schoolyear = schoolyear
        tabpage.year_changed()

builtins.ADMIN = Admin()
FUNCTIONS['base_SET_YEARS'] = ADMIN.SET_YEARS

#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    from qtpy.QtCore import QLocale, QTranslator, QLibraryInfo, \
            QTimer, QSettings
    from qtpy.QtGui import QIcon

#TODO: pass datadir to back-end, perhaps as command-line parameter!
# It might be possible to change the datadir from the gui.
# Could use SETTINGS...
    if len(sys.argv) == 2:
        DATADIR = sys.argv[1]
    else:
        DATADIR = None
#    init(datadir)
#    # Persistent Settings:
#    builtins.SETTINGS = QSettings(os.path.join(DATA, 'wz-settings'),
#                QSettings.IniFormat)

    LOCALE = QLocale(QLocale.German, QLocale.Germany)
    QLocale.setDefault(LOCALE)
    qtr = QTranslator()
    qtr.load("qt_" + LOCALE.name(),
            QLibraryInfo.location(QLibraryInfo.TranslationsPath))
    app.installTranslator(qtr)

    ADMIN.setWindowIcon(QIcon(os.path.join('icons', 'WZ1.png')))
    # Run this when the event loop has been entered:
    QTimer.singleShot(0, ADMIN.init)
    screen = app.primaryScreen()
    screensize = screen.availableSize()
    ADMIN.resize(screensize.width()*0.8, screensize.height()*0.8)
    ADMIN.show()
    sys.exit(app.exec_())

