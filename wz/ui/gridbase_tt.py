#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gridbase.py

Last updated:  2021-03-27

A spreadsheet-like grid as a background for laying out coordinate-based
box items, here called "Tiles".


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

# Changed positioning of Tiles: now done with self.offset.

#### Configuration

# Default settings
#BOXWIDTH = 80.0
#BOXHEIGHT = 80.0
LINEWIDTH = 3.0




###############################################################

import os
from qtpy.QtWidgets import (QWidget, QToolTip, QLabel,
    QHBoxLayout, QVBoxLayout, QMenu, QFrame, QComboBox, QListWidget,
    QListWidgetItem,
    QPushButton, QApplication, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsSimpleTextItem)
from qtpy.QtGui import QFont, QIcon, QPen, QColor, QBrush
from qtpy.QtCore import Qt


class GridbaseError(Exception):
    pass

###

class GView(QGraphicsView):
    """A QGraphicsView with click handler.
    """
#
    def mousePressEvent(self, event):
        point = event.pos()
#        print("POS:", point, self.mapToGlobal(point), self.itemAt(point))
# The Tile may not be the top item.
        items = self.items(point)
        if items:
            for item in items:
                try:
                    propagate = item.click(event)
                except AttributeError:
                    continue
                if not propagate:
                    break

###

class GViewResizing(GView):
    """An automatcally-resizing QGraphicsView ...
    """
    def __init__(self):
        super().__init__()
        # Apparently it is a good idea to disable scrollbars when using
        # this resizing scheme. With this resizing scheme they would not
        # appear anyway, so this doesn't lose any features!
        self.setHorizontalScrollBarPolicy (Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy (Qt.ScrollBarAlwaysOff)

    def resizeEvent(self, event):
        self.resize()
        return super().resizeEvent(event)

    def resize(self, qrect=None):
        if qrect == None:
            qrect = self.sceneRect()
        self.fitInView(qrect, Qt.KeepAspectRatio)



class Gridbase(QGraphicsScene):
#    def __init__(self):
#        super().__init__()
#
    def set_grid(self, rows, cols, linewidth = None, draw_grid = False):
        self.clear()
        def gridline(pos, length, vertical = True):
            if vertical:
                l = self.addLine(pos, 0.0, pos, length, pen0)
                self.addLine(pos, 0.0, pos, length, pen1)
            else:
                l = self.addLine(0.0, pos, length, pos, pen0)
                self.addLine(0.0, pos, length, pos, pen1)
            l.setZValue(-20)
        #
        self.line_width = LINEWIDTH if linewidth == None else linewidth
        self.row_widths = rows
        self.col_widths = cols
        self.rows_y = []
        self.cols_x = []
        y = 0.0
        for rh in rows:
            self.rows_y.append(y)
            y += rh
        self.y_end = y
        x = 0.0
        for cw in cols:
            self.cols_x.append(x)
            x += cw
        self.x_end = x
        if draw_grid:
            pen0 = QPen()
            pen0.setWidth(self.line_width)
            pen0.setColor(QColor('#ff8000')) # rrggbb
            pen1 = QPen()
            pen1.setColor(QColor('#ff000000')) # aarrggbb
            for y in self.rows_y:
                gridline(y, self.x_end, vertical = False)
            gridline(self.y_end, self.x_end, vertical = False)
            for x in self.cols_x:
                gridline(x, self.y_end)
            gridline(self.x_end, self.y_end)
#
    def box_dimensions(self, row, col, width = 1, height = 1):
        """Get the position and size of the box covering the given cell(s).
        Return a tuple: (x-top-left, y-top-left, width, height).
        """
        x0 = self.cols_x[col]
        y0 = self.rows_y[row]
        col2 = col + width
        if col2 >= len(self.cols_x):
            if col2 > len(self.cols_x):
                raise GridbaseError("Right overflow: column = %d" % col2)
            x1 = self.x_end
        else:
            x1 = self.cols_x[col2]
        row2 = row + height
        if row2 >= len(self.rows_y):
            if row2 > len(self.rows_y):
                raise GridbaseError("Bottom overflow: row = %d" % row2)
            y1 = self.y_end
        else:
            y1 = self.rows_y[row2]
        return (x0, y0, x1 - x0, y1 - y0)
#
    def new_tile(self, row, col, width = 1, height = 1, text = None):
        return Cell(self, row, col, width, height, text)
#
#    def getCell (self, row, col):
#        return self.rows [row] [col]


    def drawtext (self, x0, y0, width, height, text):
        """Draw text centered in box. Used for row and column headers.
        """
        item = self.addSimpleText (text)
        bdrect = item.boundingRect ()
        w = bdrect.width ()
        h = bdrect.height ()
        xshift = (width - w) / 2
        yshift = (height - h) / 2
        item.setPos (x0 + xshift, y0 + yshift)
        return item


class Box(QGraphicsRectItem):
    """A rectangle with adjustable borderwidth.
    The item's coordinate system starts at (0, 0), fixed by passing
    this origin to the <QGraphicsRectItem> constructor.
    The box is then moved to the desired location using <setPos>.
    """
    @classmethod
    def setup (cls, linewidth):
        # Set the linewidth of the border.
        cls.pen0 = QPen ()
        cls.pen0.setWidth (linewidth)
        #cls.pen0.setColor (QColor ('#e8e800')) or QColor ('#ffe8e800')

    def __init__ (self, x, y, w, h):
        super().__init__(0, 0, w, h)
        self.setPos(x, y)
#        self.setPen (self.pen0)


class Cell(Box):
    """This is a rectangle representing a single grid cell.
    It is a <Box> which can be selected by raising it and changing its
    border (only one cell may be selected).
    It can also be highlighted by changing the background and it
    supports hover events.
    """
    nPen = None
    selected = None

    @classmethod
    def setup (cls):
        cls.nBrush = QBrush()
        cls.hBrush = QBrush(QColor('#e0ffff80'))
        cls.nPen = QPen()
        cls.hPen = QPen()
        cls.hPen.setColor(QColor('#00ff00'))
        cls.hPen.setWidth(3)

    @classmethod
    def select(cls, cell):
        if cls.selected:
            cls.selected.setPen(cls.nPen)
            cls.selected.setZValue(0)
            cls.selected = None
        if cell:
            cell.setPen(cls.hPen)
            cell.setZValue(20)
            cls.selected = cell

    def __init__(self, grid, row, col, width, height, text = None):
        if not self.nPen:
            self.setup()
        self.dims = grid.box_dimensions(row, col, width, height)
        super().__init__(*self.dims)
        self.row = row
        self.col = col
        self.width = width
        self.height = height
        self.setAcceptHoverEvents(True)
        grid.addItem(self)
        if text != None:
            self.draw_text(text)
#
    def hoverEnterEvent(self, event):
        print ("Enter", self.row, self.col)
        QToolTip.showText(event.screenPos(), "Hi there!", view)
        # ... the last argument must be a QWidget
#
    def hoverLeaveEvent(self, event):
        print ("Leave", self.row, self.col)
#
    def highlight(self, on = True):
        self.setBrush(self.hBrush if on else self.nBrush)
#
    def draw_text(self, text):
        """Draw text centered in box.
        """
        self.text_item = grid.addSimpleText(text)
        bdrect = self.text_item.boundingRect ()
        w = bdrect.width()
        h = bdrect.height()
        x0, y0, w0, h0 = self.dims
        xshift = (w0 - w) / 2
        yshift = (h0 - h) / 2
        self.text_item.setPos(x0 + xshift, y0 + yshift)
        self.text_item.setZValue(22)
#
    def click(self, event):
        b = event.button()
        if b == Qt.LeftButton:
            bt = "LEFT"
        elif b == Qt.RightButton:
            bt = "RIGHT"
        else:
            return True
        print("CLICKED!", bt)
        return False

###

class Tile (QGraphicsRectItem):
    """The graphical representation of a lesson.
    """
    margin = 3.0

    def __init__ (self, grid, id_, text, division=1.0, duration=1, offset=0.0):
#TODO: division according to number of subgroups?
        self.grid = grid
        self.id_ = id_
        self.fullheight = Grid.boxheight - self.margin*2
        self.height = self.fullheight * division
        self.width = Grid.boxwidth * duration - self.margin*2
        super().__init__(0, 0, self.width, self.height)
# If setting parent don't do the following line.
        grid.addItem (self)
        text = QGraphicsSimpleTextItem (text, self)
        bdrect = text.boundingRect ()
        w = bdrect.width ()
        h = bdrect.height ()
        xshift = (self.width - w) / 2
        yshift = (self.height - h) / 2
        text.setPos (xshift, yshift)

        self.setOffset (offset)

        self.setZValue (20)
        self.setBrush (QBrush (QColor ('#80f0f0f0')))
        self.setVisible (False)
#        self.setAcceptHoverEvents (True)
        self.setFlag (self.ItemIsFocusable)


    def setOffset (self, offset):
        """Set the vertical offset of the tile in relation to the cell area.
        It is fractional: 0.0 <= <offset> < 1.0
        """
# Another option might be to use an integer (number of subgroups above
# this tile) ...
        self.offset = offset * self.fullheight


    def place (self, row, col):
        cell = self.grid.getCell (row, col)
        self.setPos (cell.x0 + self.margin, cell.y0 + self.offset + self.margin)
        self.setVisible (True)


    def mousePressEvent (self, event):
        print ("Pressed on", self.id_)
# May want to wait for the release – and check that it is on the same tile?
# Then ignore should probably not be called?
#        event.ignore ()
#        super ().mousePressEvent (event)

# Release only causes a signal when the grabber is set  (press event accepted),
# but the mouse may then be somewhere else ...
    def mouseReleaseEvent (self, event):
        point = event.scenePos ()
        ipoint = event.pos ()
        x = ipoint.x ()
        y = ipoint.y ()
#        print ("Released", self.id_, event.button (), point, ipoint)
        print ("Released", self.id_, x, y, point.x (), point.y ())
        event.ignore ()
        if event.button == Qt.MouseButton.LeftButton:
            self.setFocus ()
        #button can be Qt.MouseButton.RightButton or Qt.MouseButton.LeftButton
# event.pos () returns the coordinates relative to this item, so if these
# are not within width&height the release was outside the tile.
        if x >= 0 and y >= 0 and x < self.width and y < self.height:
            print ("IN ITSELF", x, y)
# This seems a bit more complicated!
        dt = self.deviceTransform(self.grid.views () [0].viewportTransform())
        this = self.grid.itemAt (point, dt)
        if this == self:
            print ("DO IT")
# DO IT doesn't work over the text.

    def keyPressEvent (self, event):
        print ("KEY:", event.key (), event.text ())

    def hide (self):
        self.setVisible (False)

    def hoverEnterEvent (self, event):
        print ("+EnterTile", self.id_)
## These seem unnecessary ... apparently, ignore does nothing the parent just updates.
#        event.ignore ()
#        super ().hoverEnterEvent (event)

    def hoverLeaveEvent(self, event):
        print ("+LeaveTile", self.id_)
## These seem unnecessary ... apparently, ignore does nothing the parent just updates.
#        event.ignore ()
#        super ().hoverEnterEvent (event)


#    def contextMenuEvent (self, event):
#        print ("CONTEXT MENU")
#        event.accept ()

    def contextMenuEvent(self, event):
#        menu = QMenu ("Context Menu")
        menu = QMenu ()
        Action = menu.addAction("I am a context Action")
        Action.triggered.connect(self.printName)

        menu.exec_(event.screenPos())

    def printName(self):
        print ("Action triggered from {}".format (self.id_))






    def old(self):
        gvbox = QVBoxLayout ()
        gvbox.addWidget (self.gridtitle)
        gvbox.addWidget (self.gv)


        self.selectClass = QComboBox ()
#TODO:
        self.selectClass.addItems (["class 9", "class 10", "class 11"])

        self.unallocated = QListWidget ()
#TODO?
        self.unallocated.setFixedWidth (100)

        self.actionList = QListWidget ()
# What difference does this make???:
        self.actionList.setSelectionMode (self.actionList.NoSelection)
        self.actionList.itemClicked.connect (self.action)

        for t in "Do 1", "Do 2", "Do 3":
            lwi = ListItem (t)
            self.actionList.addItem (lwi)
#TODO?
        self.actionList.setFixedWidth (100)

        btn = QPushButton ('Button')
        btn.setToolTip ('This is a <b>QPushButton</b> widget')
        btn.clicked.connect (QApplication.instance ().quit)
#        btn.resize (btn.sizeHint ())

        cvbox = QVBoxLayout ()
        cvbox.addWidget (self.selectClass)
        cvbox.addWidget (self.unallocated)
#        cvbox.addWidget (btn)
        cvbox.addWidget (self.actionList)

        hbox = QHBoxLayout (self)
        hbox.addLayout (gvbox)
        hbox.addWidget (QVLine ())
        hbox.addLayout (cvbox)

        self.setWindowTitle ('Grids')
        self.resize (800, 400)
        self.show ()

    def setGrid (self, grid):
        self.gv.setScene (grid)
        self.gv.resize ()


    def action (self, listItem):
        print ("Action", listItem.val ())








if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

#    view = GView()
    view = GView()
    grid = Gridbase()
    icondir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
            'icons')
    view.setScene(grid)
    grid.set_grid(
        rows = [30.0, 30.0, 30.0, 30.0, 30.0],
        cols = [45.0, 45.0, 45.0, 45.0],
        draw_grid = True
    )

#    print("1, 2, 2, 3:", grid.box_dimensions(1, 2, 2, 3))
#    print("1, 2, 2, 4:", grid.box_dimensions(1, 2, 2, 4))
#    print("3, 1, 2, 3:", grid.box_dimensions(3, 1, 2, 3))

    cell = grid.new_tile(1, 2, 2, 3, text = "Hello, world!")
    cell.select(cell)
    cell.highlight(True)

    view.show()
    sys.exit(app.exec_())
