from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import QEvent

app = QApplication([])
app.setQuitOnLastWindowClosed(False)

from pynput.keyboard import Key, Controller
keyboard = Controller()

def do_action():
    keyboard.press('≈')

def activated(reason):
    if reason == QSystemTrayIcon.Trigger:
        # left-clicked
        keyboard.press('⇒')

class MySysTrayIcon(QSystemTrayIcon):
    def event(self, e):
        if e.type() == QEvent.EnterEvent:
            self.showMessage("Watch out", "I'm a message!")
#            return True
        elif e.type() == QEvent.LeaveEvent:
            pass
#            return True
        return super().event(e)

# Create the icon
icon = QIcon("icon.png")

# Create the tray
tray = QSystemTrayIcon()
tray.setIcon(icon)
tray.setVisible(True)

tray.activated.connect(activated)
#tray.setToolTip("Type Special Characters")

# Create the menu
menu = QMenu()
action = QAction("A menu item")
action.triggered.connect(do_action)
menu.addAction(action)

# Add a Quit option to the menu.
quit_ = QAction("Quit")
quit_.triggered.connect(app.quit)
menu.addAction(quit_)

# Add the menu to the tray (right-clicked)
tray.setContextMenu(menu)

#tray.showMessage("Watch out", "I'm a message!")
app.exec_()
