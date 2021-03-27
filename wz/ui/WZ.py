# -*- coding: utf-8 -*-
"""
ui/WZ.py

Last updated:  2021-03-10

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


import sys, os, builtins, traceback, json
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

from qtpy.QtWidgets import QWidget, QDialog, QFrame, QStackedWidget, \
    QHBoxLayout, QVBoxLayout, QLabel, QTextEdit, \
    QPushButton, QButtonGroup
from qtpy.QtCore import Qt, QDateTime, QProcess, QTimer
from qtpy.QtGui import QMovie, QPixmap, QColor

from ui.ui_support import QuestionDialog, HLine, TabPage, KeySelect, \
        GuiError, openDialog, saveDialog

builtins.TABS = []
builtins.FUNCTIONS = {}
#TODO: first page ...
TABS.append(TabPage("Page 1"))
import ui.tab_subjects
import ui.tab_pupils_update
import ui.tab_pupil_editor
import ui.tab_grade_editor
#        self._addPage(TextReports())
import ui.tab_calendar
#        self._lbox.addStretch(1)
#import ui.tab_template_fields
#        self._addPage(FieldEdit())

####+++++++++++++++++++++++++++++++++++++++

sys.stdin.reconfigure(encoding='utf-8') # requires Python 3.7+
backend_instance = None
class _Backend(QDialog):
    """Manage communication with the "back-end". Provide a pop-up (modal
    dialog) to provide visual feedback to the user concerning the progress
    and success of the commands.
    This is a "singleton" class, i.e. only one instance may exist.

    For details of the communication protocol, see the description of
    class "_Main" in the "main" module of the back-end.

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
            SHOW_ERROR("BIG PROBLEM: <_Backend> instance exists already")
            self.terminate()
            quit(1)
        self.backend_queue = []
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
    def error_in(self):
        data = self.process.readAllStandardError()
        line = bytes(data).decode("utf8").rstrip()
        self.report('TRAP', 'BACKEND FAILED:\n' + line)
#
    def handle_in(self):
        while True:
            try:
                data = self.process.readLine()
            except:
                return
            line = bytes(data).decode("utf8").rstrip()
            if not line:
                return
#TODO ---
            print('>>>IN:', line, flush = True)
#TODO: The input lines should be logged?
            self.cb_lines.append(line)
            # A line has been received from the back-end.
            # Decode it and act upon it.
            try:
                self._callback = json.loads(line)
                cbfun = self._callback['__CALLBACK__']
            except:
                self.report('TRAP', '*** Invalid callback ***\n' + line)
                return
            self.do_callback(cbfun)
#
    def do_callback(self, function_name):
        try:
            function = FUNCTIONS[function_name]
        except KeyError:
            self.report('TRAP', 'Unknown callback: ' + function_name)
            return
        # deal with the parameters
        params = {}
        for p, v in self._callback.items():
            if p.startswith('_'):
                continue
            params[p] = v
        ### execute
        try:
            function(**params)
        except:
            log_msg = traceback.format_exc()
            self.report('TRAP', log_msg)
#
#TODO: logging!
#
    def report(self, mtype, msg):
        # The QApplication must have been started before calling this.
        msglevel, msgtype = INFO_TYPES[mtype]
        if msglevel > self._level:
            self._level = msglevel
        self.text.setTextColor(self.colours[msglevel])
        if msglevel == 0:
            self.text.append('%s %s' % (msgtype, msg))
        else:
            self.text.append((
                    '+++++++++++++++++++++++++++++++++++++++++++\n'
                    '%s %s\n'
                    '-------------')
                    % (msgtype, msg))
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
        New commands can arise via callbacks while one command is still
        running. These are placed in a queue and executed one after the
        other.
        """
        if not self.process:
            # Start process
            self.process = QProcess()
            # It is probably better to have separate channels, so that
            # back-end failures can be reported properly:
            #self.process.setProcessChannelMode(QProcess.MergedChannels)
            #self.process.readyRead.connect(self.handle_in)
            self.process.readyReadStandardOutput.connect(self.handle_in)
            self.process.readyReadStandardError.connect(self.error_in)
            self.process.finished.connect(self.process_finished)
            exec_params = [os.path.join(APPDIR, 'core', 'main.py')]
            if DATADIR:
                exec_params.append(DATADIR)
            self.process.start(sys.executable, exec_params)
            self._complete = True       # completion set by back-end
            # Flag used to wait for end of previous command:
            self.cmd_running = False
        if self.cmd_running:
            self.backend_queue.append((fn, parms))
#TODO ---
            print("$$$queue:",  self.backend_queue)
            return
        self.cmd_running = True
        while True:
            # Loop through queued commands
            self.cb_lines = []  # remember all lines from back-end
            parms['__NAME__'] = fn
            msg = json.dumps(parms, ensure_ascii = False) + '\n'
#TODO ---
            print('!!!SEND:', msg, flush = True)
            self.text.clear()
            end_time = QDateTime.currentMSecsSinceEpoch() + 500
            self.process.write(msg.encode('utf-8'))
            # Remember the highest-level message (none, info, warning,
            # error, trap).
            self._level = 0
            self._complete = False  # set to <True> when the command finishes
            self._ok.setEnabled(False)
            self._cancel.show()
            self._active = False    # set to <True> when the pop-up is shown
            while True:
                # Loop to handle input from back-end until display-info
                # pop-up is shown (when something "important" to report
                # is available – or until the delay-timeout is reached).
                self.cmd_running = True
                if self.process:
                    self.process.waitForReadyRead(100)
                else:
                    SHOW_ERROR("BIG PROBLEM: Process failed ...\n"
                            + '\n'.join(self.cb_lines))
                    return
                # The available input is read via a signal handler
                # (<handle_in>), not here.
                # Check whether/when to pop up the dialog:
                if self._level > 0 or \
                        QDateTime.currentMSecsSinceEpoch() > end_time:
                    # Show modal dialog
                    self.become_active()
                    # The pop-up can be cancelled before the back-end
                    # is finished:
                    while not self._complete:
                        self.process.waitForReadyRead(100)
                    break
                elif self._complete:
                    # The back-end can complete quickly without anything
                    # to report.
                    break
            # Handle queued command
            if self.backend_queue:
                fn, parms = self.backend_queue.pop(0)
            else:
                break
        self.cmd_running = False    # present command finished
#
    def become_active(self):
        if self._complete:
            if self._level == 0:
                return
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
    def task_done(self, cc):
        """A back-end function has completed.
        """
        if cc != 'OK':
            self.backend_queue = []
            self.report('ERROR', cc)
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
            self.task_done('OK')
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
#
    def read_dialog(self, filetype, callback):
        """Put up a file-open dialog and call a back-end function with
        the selected filepath. If the action is cancelled, the back-end
        function is not called.
            <filetype>: E.g. "Tabellendatei (*.xlsx *.ods *.tsv)"
            <callback>: Name of back-end function to call with filepath.
        """
        fpath = openDialog(filetype)
        if fpath:
            self.command(callback, filepath = fpath)
#
    def save_dialog(self, filetype, filename, callback):
        """Put up a file-save dialog and call a back-end function with
        the selected filepath. If the action is cancelled, the back-end
        function is not called.
            <filetype>: E.g. "Tabellendatei (*.xlsx *.ods *.tsv)"
            <filename>: Initial name of file.
            <callback>: Name of back-end function to call with filepath.
        """
        fpath = saveDialog(filetype, filename)
        if fpath:
            self.command(callback, filepath = fpath)
###

backend_instance = _Backend()
builtins.BACKEND = backend_instance.command
FUNCTIONS['*DONE*'] = backend_instance.task_done
FUNCTIONS['*REPORT*'] = backend_instance.report
# For other message pop-ups, see <SHOW_INFO>, <SHOW_WARNING> and
# <SHOW_ERROR> in module "ui_support".
FUNCTIONS['*READ_FILE*'] = backend_instance.read_dialog
FUNCTIONS['*SAVE_FILE*'] = backend_instance.save_dialog

####---------------------------------------

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
        if tab:
            b = TabButton(tab.name, self)
            self.tab_buttons.append(b)
            self._lbox.addWidget(b)
            self._stack.addWidget(tab)
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
            if tab0.leave():
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
    def clear(self):
        w = self._stack.currentWidget()
        if w:
            return w.leave()
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
        tab_title = QLabel()
        titlebox.addWidget(tab_title)
        titlebox.addStretch(1)
        topbox.addWidget(HLine())
        # ---------- Tab Box ---------- #
        self.tab_widget = TabWidget(tab_title)
        topbox.addWidget(self.tab_widget)

        for tab in TABS:
            self.tab_widget.add_page(tab)
        self.tab_widget.add_page(None)

        self.tab_widget.select(0)   # Enter default tab
#
    def closeEvent(self, e):
        if self.tab_widget.clear():
            backend_instance.terminate()
            e.accept()
        else:
            e.ignore()
#
    def init(self):
        BACKEND('BASE_get_school_data')
        BACKEND('BASE_get_years')
#
    def SET_SCHOOL_DATA(self, data):
        self.school_data = data
#TODO ---
        print('SCHOOL_DATA', self.school_data, flush = True)
#
    def SET_YEARS(self, years, current):
        self.year_select.set_items(years)
        chosenyear = self.year_select.selected()
        if chosenyear != current:
            self.year_select.reset(current)
#
    def YEAR_CHANGED(self):
        tabpage = self.tab_widget.current_page()
        tabpage.enter()
#
    def year_changed(self, schoolyear):
        tabpage = self.tab_widget.current_page()
        if tabpage.year_change_ok():
            BACKEND('BASE_set_year', year = schoolyear)
            return True
        return False
#
    def current_year(self):
        return self.year_select.selected()
#
#    def set_year(self, year):
#        self.year_select.reset(year)
#        self.year_select.trigger()

builtins.ADMIN = Admin()
FUNCTIONS['base_SET_YEARS'] = ADMIN.SET_YEARS
FUNCTIONS['base_SET_SCHOOL_DATA'] = ADMIN.SET_SCHOOL_DATA
FUNCTIONS['base_YEAR_CHANGED'] = ADMIN.YEAR_CHANGED

#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    from qtpy.QtCore import QLocale, QTranslator, QLibraryInfo, QSettings
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

    app.setWindowIcon(QIcon(os.path.join('icons', 'WZ1.png')))
    # Run this when the event loop has been entered:
    QTimer.singleShot(10, ADMIN.init)
    screen = app.primaryScreen()
    screensize = screen.availableSize()
    ADMIN.resize(screensize.width()*0.8, screensize.height()*0.8)
    ADMIN.show()
    sys.exit(app.exec_())

