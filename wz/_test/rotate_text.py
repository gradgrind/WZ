# -*- coding: utf-8 -*-
""" rotate_text.py
draw a rotated text with PySide's QPainter class
"""

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class MyWindow(QWidget):

    def __init__(self, text, degrees):
        # QWidget will be self
        QWidget.__init__(self)
        # setGeometry(x_pos, y_pos, width, height)
        # upper left corner coordinates (x_pos, y_pos)
        self.setGeometry(300, 100, 520, 520)
        self.setWindowTitle('Testing text rotation ...')
        self.text = text
        self.degrees = degrees

    def paintEvent(self, event):
        '''
        the method paintEvent() is called automatically
        the QPainter class does the low-level painting
        between its methods begin() and end()
        '''
        qp = QPainter()
        qp.begin(self)
        # set text color, default is black
        qp.setPen('red')
        # QFont(family, size)
        qp.setFont(QFont('Decorative', 12))
        # start text at point (x, y)
        x = 30
        y = 30
        qp.translate(x, y)
        qp.rotate(self.degrees)
        qp.drawText(0, 0, self.text)
        qp.end()


text = '''\
You pass an elementary school playground and the
children are all busy with their cellphones.
'''

# for command line replace [] with sys.argv
app = QApplication([])
# degrees of text rotation (clockwise)
degrees = 45
win = MyWindow(text, degrees)
win.show()
# run the application event loop
app.exec()

quit(0)
