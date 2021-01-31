# -*- coding: utf-8 -*-

from qtpy.QtWidgets import QApplication, QMainWindow, QPushButton, \
        QPlainTextEdit, QVBoxLayout, QWidget, QProgressBar, QDialog
from qtpy.QtCore import QProcess, QTimer
import sys
import re

# A regular expression, to extract the % complete.
progress_re = re.compile("Total complete: (\d+)%")

def simple_percent_parser(output):
    """
    Matches lines using the progress_re regex,
    returning a single integer for the % progress.
    """
    m = progress_re.search(output)
    if m:
        pc_complete = m.group(1)
        return int(pc_complete)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.popup = False
        self.dialog = QDialog()
        vbox = QVBoxLayout(self.dialog)
        self.dialog_text = QPlainTextEdit()
        self.dialog_text.setReadOnly(True)
        vbox.addWidget(self.dialog_text)

        self.p = None

        self.btn = QPushButton("Start")
        self.btn.pressed.connect(self.start_process)
        self.btn2 = QPushButton("Command")
        self.btn2.pressed.connect(self.command)
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)

        l = QVBoxLayout()
        l.addWidget(self.btn)
        l.addWidget(self.btn2)
        l.addWidget(self.progress)
        l.addWidget(self.text)

        w = QWidget()
        w.setLayout(l)

        self.setCentralWidget(w)

    def message(self, s):
        if self.popup:
            if s.startswith('XXX'):
                self.dialog.accept()
                self.popup = False
            else:
                self.dialog_text.appendPlainText(s)
                return
        self.text.appendPlainText(s)

    def start_process(self):
        if self.p is None:  # No process running.
            self.message("Executing process")
            self.p = QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
#self.p.setProcessChannelMode(QProcess.MergedChannels)
#self.p.readyRead.connect(self.handle_out)
# ... self.p.readAll()
            self.p.readyReadStandardOutput.connect(self.handle_stdout)
            self.p.readyReadStandardError.connect(self.handle_stderr)
            self.p.stateChanged.connect(self.handle_state)
            self.p.finished.connect(self.process_finished)  # Clean up once complete.
            self.p.start("python3", ['dummy_script.py'])

    def command(self):
        print("command")
#        self.p.write('COMMAND 1: öäüß€\n'.encode('utf-8'))
        self.p.write('!\n'.encode('utf-8'))
#This is a brilliant solution, but it doesn't do what it "should" – it
# doesn't block input to the main window!
# The hiding seems to cancel the modality, and the showing doesn't start it
# again.
#        QTimer.singleShot(10, self.popup_hide)
#        QTimer.singleShot(2000, self.popup_show)

        if self.p.waitForReadyRead(200):
            # If it is an info (etc.) message, pop up and show it.
            # Otherwise execute it ...
        else:
            # no response (or error)
            # --> dialog





            self.popup = True
            self.dialog_text.clear()
            self.dialog.exec_()
# Would input polling up to the show time be possible?
# Selectively handle events?
# What about leaving the modal window up to the individual function?
# But one would still need to block further actions until the response is
# available ... As QProcess is rather signal-slot based, that might be
# easier with python's subprocess?


    def popup_hide(self):
        if self.popup:
            self.dialog.setVisible(False)

    def popup_show(self):
        print("SHOW")
        if self.popup:
            self.dialog.setVisible(True)

    def handle_stderr(self):
        data = self.p.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        # Extract progress if it is in the data.
        progress = simple_percent_parser(stderr)
        if progress:
            self.progress.setValue(progress)
        self.message(stderr)

    def handle_stdout(self):
        data = self.p.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        self.message(stdout)

    def handle_state(self, state):
        states = {
            QProcess.NotRunning: 'Not running',
            QProcess.Starting: 'Starting',
            QProcess.Running: 'Running',
        }
        state_name = states[state]
        self.message(f"State changed: {state_name}")

    def process_finished(self):
        self.message("Process finished.")
        self.p = None


app = QApplication(sys.argv)

w = MainWindow()
w.show()

app.exec_()
