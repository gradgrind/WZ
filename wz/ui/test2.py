# -*- coding: utf-8 -*-

from qtpy.QtWidgets import QApplication, QMainWindow, QPushButton, \
        QTextEdit, QVBoxLayout, QHBoxLayout, QLabel, \
        QWidget, QProgressBar, QDialog, QFrame
from qtpy.QtCore import QProcess, QDateTime
from qtpy.QtGui import QColor
import sys, traceback

class RDialog(QDialog):
    def __init__(self):
        super().__init__()
        vbox = QVBoxLayout(self)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.colours = [QColor('#000000'), QColor('#ff0000'),
                QColor('#00ff00'), QColor('#0000ff')]
        self.count = 0
        vbox.addWidget(self.text)
        ## Button area
        vbox.addWidget(HLine())
        bbox = QHBoxLayout()
        vbox.addLayout(bbox)
        bbox.addStretch(1)
        self._cancel = QPushButton("Cancel")
#        self._cancel.hide()
        bbox.addWidget(self._cancel)
        self._cancel.clicked.connect(self.reject)
        self._ok = QPushButton("OK")
        self._ok.setDefault(True)
        bbox.addWidget(self._ok)
        self._ok.clicked.connect(self.accept)

        self.p = None

    def reject(self):
        if self.cmd_done:
            print("CLOSE")
            self.accept()
            return
        if QuestionDialog("INTERRUPT", "Really interrupt?"):
            self.p.kill()

    def command(self, msg):
        self.cmd = 0
        self.cmd_done = False
        self.text.clear()
        end_time = QDateTime.currentMSecsSinceEpoch() + 500
        if self.p is None:  # No process running.
            print("Executing process")
            self.p = QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
            self.p.setProcessChannelMode(QProcess.MergedChannels)
            self.p.readyRead.connect(self.handle_out)
            self.p.stateChanged.connect(self.handle_state)
            self.p.finished.connect(self.process_finished)  # Clean up once complete.
            self.p.start("python3", ['dummy_script2.py'])
        self.p.write(msg.encode('utf-8'))
        self._ok.setEnabled(False)
        self._cancel.show()
        while True:
#?
            if not self.p:
                quit()
            self.p.waitForReadyRead(100)
            if self.cmd_done:
                break
            if QDateTime.currentMSecsSinceEpoch() > end_time:
                # Switch to dialog
                self.exec_()
                break

    def handle_out(self):
#        data = self.p.readAll()
        while True:
            data = self.p.readLine()
            op = bytes(data).decode("utf8").rstrip()
            if not op:
                return
            print("+++", repr(op))
            if op.startswith('---'):
                # Command finished
                self._cancel.hide()
                self._ok.setEnabled(True)
                self.cmd_done = True
            elif op.startswith('>>>'):
                print(repr(op))
            else:
                self.text.setTextColor(self.colours[self.cmd % len(self.colours)])
                self.cmd += 1
                self.text.append(op)

    def handle_state(self, state):
        states = {
            QProcess.NotRunning: 'Not running',
            QProcess.Starting: 'Starting',
            QProcess.Running: 'Running',
        }
        state_name = states[state]
        print(f"State changed: {state_name}")

    def process_finished(self):
        print("Process finished.")
        self.p = None
        self._cancel.hide()
        self._ok.setEnabled(True)
        self.cmd_done = True


class HLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

def QuestionDialog(title, message):
    qd = QDialog()
    qd.setWindowTitle(title)
    vbox = QVBoxLayout(qd)
    vbox.addWidget(QLabel(message))
    vbox.addWidget(HLine())
    bbox = QHBoxLayout()
    vbox.addLayout(bbox)
    bbox.addStretch(1)
    cancel = QPushButton("No")
    cancel.clicked.connect(qd.reject)
    bbox.addWidget(cancel)
    ok = QPushButton("Yes")
    ok.clicked.connect(qd.accept)
    bbox.addWidget(ok)
    cancel.setDefault(True)
    return qd.exec_() == QDialog.Accepted


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

#TODO: In order to handle the close button, there must be a subclass of
# QDialog.
        self.dialog = RDialog()

        self.btn1 = QPushButton("Quickie")
        self.btn1.pressed.connect(self.quickie)
        self.btn2 = QPushButton("Longer")
        self.btn2.pressed.connect(self.longer)
        self.btn3 = QPushButton("Terminate")
        self.btn3.pressed.connect(self.terminate)

        l = QVBoxLayout()
        l.addWidget(self.btn1)
        l.addWidget(self.btn2)
        l.addWidget(self.btn3)

        w = QWidget()
        w.setLayout(l)

        self.setCentralWidget(w)

    def closeEvent(self, e):
#TODO: if a command is running this might make a mess of things?
        self.terminate()

    def quickie(self):
        print("command – quickie")
        self.dialog.command('COMMAND 1: öäüß€\n')

    def terminate(self):
        print("command – terminate")
        self.dialog.command('$\n')

    def longer(self):
        print("command – longer")
        self.dialog.command('!\n')


app = QApplication(sys.argv)

w = MainWindow()
w.show()

app.exec_()
