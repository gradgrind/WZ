#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
timetable/tt_table.py

Last updated:  2021-07-22

Timetable grid ... testing


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

#TODO: Keep size fixed, but allow scaling (x 2 only?). This is to try to keep
# the grid lines, box edges, etc. look uniform.

# Configuration

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon, QPen, QColor, QBrush, QTransform
from PySide6.QtWidgets import QWidget, QToolTip, QLabel, \
        QHBoxLayout, QVBoxLayout, QMenu, QFrame, QComboBox, QListWidget, \
        QListWidgetItem, \
        QPushButton, QApplication, QGraphicsView, QGraphicsScene, \
        QGraphicsRectItem, QGraphicsSimpleTextItem
import os
BOXWIDTH = 80
BOXHEIGHT = 80
SEPWIDTH = 10
LINEWIDTH = 2
TITLEHEIGHT = 20
TITLEWIDTH = 40
BORDER_COLOUR = '000080'         # rrggbb
CELL_HIGHLIGHT_COLOUR = 'a0a0ff' # rrggbb
FONT_COLOUR = '442222'           # rrggbb
SELECT_COLOUR = 'f000f0'         # rrggbb


DAYS = ('Mo', 'Di', 'Mi', 'Do', 'Fr')

PERIODS = ('A', 'B', '-', '1', '2', '', '3', '4', '', '5', '6', '7')


###############################################################

class QHLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class QVLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)


class ListItem(QListWidgetItem):
    def __init__(self, text, tag=None):
        super().__init__(text)
        self.tag = tag

    def val(self):
        return self.text()


class Window(QWidget):
    def __init__(self, icondir):
        super().__init__()
        self.icondir = icondir
        self.initUI()

    def initUI(self):
        self.setWindowIcon(QIcon(os.path.join(self.icondir, 'icon.svg')))
        QToolTip.setFont(QFont('SansSerif', 10))

# TODO: Maybe this label (and any footnotes) should be in the graphics scene
# so that they are printable?
        self.gridtitle = QLabel("GRID TITLE")

        self.gridtitle.setAlignment(Qt.AlignCenter)
        self.gv = GView()
        self.gv.setToolTip('This shows the <b>timetable</b> for a class')
        gvbox = QVBoxLayout()
        gvbox.addWidget(self.gridtitle)
        gvbox.addWidget(self.gv)

        self.selectClass = QComboBox()
# TODO:
        self.selectClass.addItems(["class 9", "class 10", "class 11"])

        self.unallocated = QListWidget()
# TODO?
        self.unallocated.setFixedWidth(100)

        self.actionList = QListWidget()
# What difference does this make???:
        self.actionList.setSelectionMode(self.actionList.NoSelection)
        self.actionList.itemClicked.connect(self.action)

        for t in "Do 1", "Do 2", "Do 3":
            lwi = ListItem(t)
            self.actionList.addItem(lwi)
# TODO?
        self.actionList.setFixedWidth(100)

        btn = QPushButton('Button')
        btn.setToolTip('This is a <b>QPushButton</b> widget')
        btn.clicked.connect(QApplication.instance().quit)
#        btn.resize (btn.sizeHint ())

        cvbox = QVBoxLayout()
        cvbox.addWidget(self.selectClass)
        cvbox.addWidget(self.unallocated)
#        cvbox.addWidget (btn)
        cvbox.addWidget(self.actionList)

        hbox = QHBoxLayout(self)
        hbox.addLayout(gvbox)
        hbox.addWidget(QVLine())
        hbox.addLayout(cvbox)

        self.setWindowTitle('Grids')
        self.resize(1000, 600)
        self.show()

    def setGrid(self, grid):
        self.gv.setScene(grid)
        #self.gv.scale(1.5)
        #self.gv.scale(2)

    def action(self, listItem):
        print("Action", listItem.val())


class GView(QGraphicsView):
    """This is the "view" widget for the grid.
    The actual grid is implemented as a "scene".
    """
    def __init__(self):
        super().__init__()
        # Change update mode: The default, MinimalViewportUpdate, seems
        # to cause artefacts to be left, i.e. it updates too little.
        # Also BoundingRectViewportUpdate seems not to be 100% effective.
        #self.setViewportUpdateMode(self.BoundingRectViewportUpdate)
        self.setViewportUpdateMode(self.FullViewportUpdate)
        self.ldpi = self.logicalDpiX()
        if self.logicalDpiY() != self.ldpi:
            REPORT('WARNING', "LOGICAL DPI different for x and y")
        self.MM2PT = self.ldpi / 25.4
#
    def set_scene(self, scene):
        """Set the QGraphicsScene for this view. The size will be fixed
        to that of the initial <sceneRect> (to prevent it from being
        altered by pop-ups).
        <scene> may be <None>, to remove the current scene.
        """
        self.setScene(scene)
        if scene:
            self.setSceneRect(scene._sceneRect)
#
    def scale(self, n):
        """Set the scale of the view.
        """
        t = QTransform()
        t.scale(n, n)
        self.setTransform(t)


class ClassGrid (QGraphicsScene):
    @classmethod
    def setup(cls):
        cls.slots = []
        cls.xslots = []
        cls.xlines = []
        sepwidth = SEPWIDTH
        cls.linewidth = LINEWIDTH
        cls.titlewidth = TITLEWIDTH
        cls.titleheight = TITLEHEIGHT
        cls.boxwidth = BOXWIDTH
        cls.boxheight = BOXHEIGHT
        cls.days = DAYS
        x = cls.titlewidth
        for ctitle in PERIODS:
            cls.xlines.append(x)
            if ctitle in ('', '-'):
                x += sepwidth
            else:
                cls.slots.append(ctitle)
                cls.xslots.append(x)
                x += cls.boxwidth
        cls.width = x
        y = cls.titleheight
        cls.ydays = []
        for rtitle in cls.days:
            cls.ydays.append(y)
            y += cls.boxheight
        cls.height = y
        Cell.setup()

    def __init__(self):
        super().__init__()
        self.buildGrid()

#    def line (self, *args):
#        l = self.addLine (*args, self.pen)
#        l.setZValue (-20)
#        return l

    def buildGrid(self):
        self.rows = []
#        self.line (0, 0, 0, self.height)
#        for x in self.xlines:
#            self.line (x, 0, x, self.height)
#        self.line (self.width, 0, self.width, self.height)
        i = 0
        for ctitle in self.slots:
            x = self.xslots[i]
            self.addItem(TitleBox(x, 0, self.boxwidth,
                                  self.titleheight, ctitle))
#            self.drawtext (x, 0, self.boxwidth, self.titleheight, ctitle)
            i += 1

#        self.line (0, 0, self.width, 0)
        i = 0
        for rtitle in self.days:
            cols = []
            self.rows.append(cols)
            y = self.ydays[i]
#            self.line (0, y, self.width, y)
            # draw row title
            self.addItem(
                TitleBox(0, y, self.titlewidth, self.boxheight, rtitle))
#            self.drawtext (0, y, self.titlewidth, self.boxheight, rtitle)
            j = 0
            for ctitle in self.slots:
                print("CELL:", self.xslots[j], y, self.boxwidth,
                      self.boxheight)

                cell = Cell(self.xslots[j], y, self.boxwidth,
                            self.boxheight, rtitle, ctitle)
                self.addItem(cell)
                cols.append(cell)
                j += 1
            i += 1
#        self.line (0, self.height, self.width, self.height)

    def getCell(self, row, col):
        return self.rows[row][col]

    def drawtext(self, x0, y0, width, height, text):
        """Draw text centered in box. Used for row and column headers.
        """
        item = self.addSimpleText(text)
        bdrect = item.boundingRect()
        w = bdrect.width()
        h = bdrect.height()
        xshift = (width - w) / 2
        yshift = (height - h) / 2
        item.setPos(x0 + xshift, y0 + yshift)
        return item


class StyleCache:
    __pens = {}
    __brushes = {}

    @classmethod
    def getPen(cls, width, colour):
        """Manage a cache for pens of different width and colour.
        <width> should be a small integer.
        <colour> is a colour in the form 'RRGGBB'.
        """
        if width:
            wc = (width, colour)
            try:
                return cls.__pens[wc]
            except KeyError:
                pass
            pen = QPen('#FF' + wc[1])
            pen.setWidthF(wc[0])
            cls.__pens[wc] = pen
            return pen
        else:
            try:
                return cls.__pens['*']
            except KeyError:
                noPen = QPen()
                noPen.setStyle(Qt.NoPen)
                cls.__pens['*'] = noPen
                return noPen

    @classmethod
    def getBrush(cls, colour=None):
        """Manage a cache for brushes of different colour.
        <colour> is a colour in the form 'RRGGBB'.
        """
        try:
            return cls.__brushes[colour or '*']
        except KeyError:
            pass
        if colour:
            brush = QBrush(QColor('#FF' + colour))
            cls.__brushes[colour] = brush
        else:
            brush = QBrush()    # no fill
            cls.__brushes['*'] = brush
        return brush


class Box(QGraphicsRectItem):
    """A rectangle with adjustable borderwidth.
    The item's coordinate system starts at (0, 0), fixed by passing
    this origin to the <QGraphicsRectItem> constructor.
    The box is then moved to the desired location using <setPos>.
    """
    def __init__(self, x, y, w, h, width=None, colour=None):
        super().__init__(0, 0, w, h)
        self.setPos(x, y)
        self.setPen(StyleCache.getPen(width, colour or BORDER_COLOUR))


class TitleBox(Box):
    """A <Box> with centred text.
    """

    def __init__(self, x, y, w, h, text):
        """Draw text centered in box. Used for row and column headers.
        """
        super().__init__(x, y, w, h)
        item = QGraphicsSimpleTextItem(text, self)
        bdrect = item.boundingRect()
        wt = bdrect.width()
        ht = bdrect.height()
        xshift = (w - wt) / 2
        yshift = (h - ht) / 2
        item.setPos(xshift, yshift)


class Cell(Box):
    """This is a rectangle representing a single lesson slot.
    It is a <Box> which can be highlighted and which supports hover events.
    """
    selected = None

    @classmethod
    def setup(cls):
        cls.nBrush = StyleCache.getBrush(None)
        cls.hBrush = StyleCache.getBrush(CELL_HIGHLIGHT_COLOUR)
        cls.nPen = StyleCache.getPen(LINEWIDTH + 2, BORDER_COLOUR)
        cls.sPen = StyleCache.getPen(LINEWIDTH + 2, SELECT_COLOUR)

    @classmethod
    def select(cls, cell):
        if cls.selected:
            cls.selected.setPen(cls.nPen)
            cls.selected.setZValue(0)
            cls.selected = None
        if cell:
            cell.setPen(cls.sPen)
            cell.setZValue(20)
            cls.selected = cell

    def __init__(self, x, y, w, h, colh, rowh):
        super().__init__(x, y, w, h, width=LINEWIDTH)
        self.x0 = x
        self.y0 = y
        self.colh = colh
        self.rowh = rowh
        self.setAcceptHoverEvents(True)
#        print ("Cell", colh, rowh, x, y)

    def hoverEnterEvent(self, event):
        print("Enter", self.rowh, self.colh)

    def hoverLeaveEvent(self, event):
        print("Leave", self.rowh, self.colh)

    def highlight(self, on=True):
        self.setBrush(self.hBrush if on else self.nBrush)


class Tile (QGraphicsRectItem):
    """The graphical representation of a lesson.
    """
    margin = 3.0

    def __init__(self, grid, id_, text, division=1.0, duration=1, offset=0.0):
        # TODO: division according to number of subgroups?
        self.grid = grid
        self.id_ = id_
        self.fullheight = self.grid.boxheight - self.margin*2
        self.height = self.fullheight * division
        self.width = self.grid.boxwidth * duration - self.margin*2
        super().__init__(0, 0, self.width, self.height)
# If setting parent don't do the following line.
        grid.addItem(self)
        text = QGraphicsSimpleTextItem(text, self)
        bdrect = text.boundingRect()
        w = bdrect.width()
        h = bdrect.height()
        xshift = (self.width - w) / 2
        yshift = (self.height - h) / 2
        text.setPos(xshift, yshift)

        self.setOffset(offset)

        self.setZValue(20)
        self.setBrush(QBrush(QColor('#80f0f0f0')))
        self.setVisible(False)
#        self.setAcceptHoverEvents (True)
        self.setFlag(self.ItemIsFocusable)

    def setOffset(self, offset):
        """Set the vertical offset of the tile in relation to the cell area.
        It is fractional: 0.0 <= <offset> < 1.0
        """
# Another option might be to use an integer (number of subgroups above
# this tile) ...
        self.offset = offset * self.fullheight

    def place(self, row, col):
#TODO: If placing a multi-period lesson over a break is to be possible,
# it would probably make sense to (re)set the dimensions according to
# the positions of the underlying cells – or leave out visual marking of
# breaks so that all offsets are the same.
        cell = self.grid.getCell(row, col)
        self.setPos(cell.x0 + self.margin, cell.y0 + self.offset + self.margin)
        self.setVisible(True)

    def mousePressEvent(self, event):
        print("Pressed on", self.id_)
        kbdmods = QApplication.keyboardModifiers()
        if kbdmods & Qt.ShiftModifier:
            print("SHIFT")
        if kbdmods & Qt.ControlModifier:
            print("CTRL")

# May want to wait for the release – and check that it is on the same tile?
# Then ignore should probably not be called?
#        event.ignore ()
#        super ().mousePressEvent (event)

# Release only causes a signal when the grabber is set  (press event accepted),
# but the mouse may then be somewhere else ...
    def mouseReleaseEvent(self, event):
        point = event.scenePos()
        ipoint = event.pos()
        x = ipoint.x()
        y = ipoint.y()
#        print ("Released", self.id_, event.button (), point, ipoint)
        print("Released", self.id_, x, y, point.x(), point.y())
        event.ignore()
        if event.button == Qt.MouseButton.LeftButton:
            self.setFocus()
        # button can be Qt.MouseButton.RightButton or Qt.MouseButton.LeftButton
# event.pos () returns the coordinates relative to this item, so if these
# are not within width&height the release was outside the tile.
        if x >= 0 and y >= 0 and x < self.width and y < self.height:
            print("IN ITSELF", x, y)
# This seems a bit more complicated!
        dt = self.deviceTransform(self.grid.views()[0].viewportTransform())
        this = self.grid.itemAt(point, dt)
        if this == self:
            print("DO IT")
# DO IT doesn't work over the text.

    def keyPressEvent(self, event):
        print("KEY:", event.key(), event.text())

    def hide(self):
        self.setVisible(False)

    def hoverEnterEvent(self, event):
        print("+EnterTile", self.id_)
# These seem unnecessary ... apparently, ignore does nothing the parent
# just updates.
#        event.ignore ()
#        super ().hoverEnterEvent (event)

    def hoverLeaveEvent(self, event):
        print("+LeaveTile", self.id_)
# These seem unnecessary ... apparently, ignore does nothing the parent
# just updates.
#        event.ignore ()
#        super ().hoverEnterEvent (event)


#    def contextMenuEvent (self, event):
#        print ("CONTEXT MENU")
#        event.accept ()

    def contextMenuEvent(self, event):
        #        menu = QMenu ("Context Menu")
        menu = QMenu()
        Action = menu.addAction("I am a context Action")
        Action.triggered.connect(self.printName)

        menu.exec_(event.screenPos())

    def printName(self):
        print("Action triggered from {}".format(self.id_))


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    ClassGrid.setup()
    grid = ClassGrid()
    window = Window(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 'icons'))
    window.setGrid(grid)
    #select = CellSelect ()

    t1 = Tile(grid, 1, "F1 AB", 0.3)
    t1.place(2, 4)
    t1a = Tile(grid, 4, "Fx XY", 0.6, offset=0.4)
    t1a.place(2, 4)
    t2 = Tile(grid, 2, "F2 BC", 0.5, offset=0.5)
    #t2.setOffset (0.5)

    t2.place(3, 4)
    t3 = Tile(grid, 3, "F3 DE", 1, duration=2)
    #    select.place (3, 4)
    #    t1.hide ()
    t3.place(0, 0)
    t4 = Tile(grid, 3, "F4 PQ", 1, duration=2)
    t4.place(2, 1)

    Cell.select(grid.getCell(2, 4))
    grid.getCell(3, 4).highlight()
    grid.getCell(1, 6).highlight()

    # TODO: How to associate the Items with the appropriate grid?

    sys.exit(app.exec())
