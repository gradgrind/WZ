# -*- coding: utf-8 -*-
"""
ui/wz_main.py

Last updated:  2022-02-09

The timetable "main" window.


=+LICENCE=============================
Copyright 2022 Michael Towers

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
_TITLE = "WZ – Stundenplanung"

#####################################################

import sys, os, builtins

if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start
#TODO: Temporary redirection to use real data (there isn't any test data yet!)
#    start.setup(os.path.join(basedir, 'TESTDATA'))
    start.setup(os.path.join(basedir, 'DATA'))

    #TODO: IF I use this feature, this is probably the wrong path ...
    # Without the environment variable there is a disquieting error message.
#    os.environ['PYSIDE_DESIGNER_PLUGINS'] = this

    from qtpy.QtWidgets import QApplication#, QStyleFactory
    from qtpy.QtCore import QLocale, QTranslator, QLibraryInfo
    #print(QStyleFactory.keys())
    #QApplication.setStyle('windows')
    # Qt initialization
    app = QApplication([])
    # Set up language/locale for Qt
    LOCALE = QLocale(QLocale.German, QLocale.Germany)
    QLocale.setDefault(LOCALE)
    qtr = QTranslator()
    qtr.load("qt_" + LOCALE.name(),
            QLibraryInfo.location(QLibraryInfo.TranslationsPath))
    app.installTranslator(qtr)

from qtpy.QtWidgets import QGraphicsScene, QGraphicsRectItem, \
        QGraphicsSimpleTextItem, QGraphicsView
from qtpy.QtCore import Qt#, QSettings
from qtpy.QtGui import QIcon, QPen, QBrush, QColor, QPainter, QTransform

### +++++

# Sizes in points
_BOXWIDTH = 80
_BOXHEIGHT = 80
_SEPWIDTH = 10
_LINEWIDTH = 2
_TITLEHEIGHT = 20
_TITLEWIDTH = 40

BORDER_COLOUR = '6060d0'         # rrggbb
HEADER_COLOUR = 'b0b0b0'
CELL_HIGHLIGHT_COLOUR = 'a0a0ff' # rrggbb
#FONT_COLOUR = '442222'           # rrggbb
SELECT_COLOUR = 'ff0000'         # rrggbb

#TODO: these should be in a config file:
DAYS = ('Mo', 'Di', 'Mi', 'Do', 'Fr')
PERIODS = ('A', 'B', '1', '2', '3', '4', '5', '6', '7')
BREAKS = ('1', '3', '5')


#TODO: point to pixel conversions???

### -----

def main(args):
    font = app.font()
    #print("FONT:", font.pointSize())
    font.setPointSize(12)
    app.setFont(font)

    #from qtpy.QtGui import QFontInfo
    #qfi = QFontInfo(font)
    #print("FONT PIXELS / POINTS:", qfi.pixelSize(), qfi.pointSize())
    # Persistent Settings:
#    builtins.SETTINGS = QSettings(
#            QSettings.IniFormat, QSettings.UserScope, 'MT', 'WZ')
    #builtins.WINDOW = GridViewRescaling()
    #builtins.WINDOW = GridViewHFit()
    builtins.WINDOW = GridView()

    # Set up grid
    grid = GridPeriodsDays(DAYS, PERIODS, BREAKS)
    WINDOW.setScene(grid)

    # Scaling: only makes sense if using basic, unscaled GridView
    scale = WINDOW.pdpi / WINDOW.ldpi
    t = QTransform().scale(scale, scale)
    WINDOW.setTransform(t)

    app.setWindowIcon(QIcon(os.path.join(basedir, "wz-data", "icons", "tt.svg")))
    screen = app.primaryScreen()
    screensize = screen.availableSize()
    WINDOW.resize(int(screensize.width()*0.6), int(screensize.height()*0.6))
    WINDOW.show()

    t1 = grid.new_tile("T1", duration=1, nmsg=1, offset=1, total=4, text="De p1", colour="FFFF44")
    grid.place_tile("T1", (2, 3))
    t2 = grid.new_tile("T2", duration=2, nmsg=1, offset=0, total=4, text="tg B", colour="FF77E0")
    grid.place_tile("T2", (2, 3))
    sys.exit(app.exec())


class GridView(QGraphicsView):
    """This is the "view" widget for the grid.
    The actual grid is implemented as a "scene".
    """
    def __init__(self):
        super().__init__()
        # Change update mode: The default, MinimalViewportUpdate, seems
        # to cause artefacts to be left, i.e. it updates too little.
        # Also BoundingRectViewportUpdate seems not to be 100% effective.
        # self.setViewportUpdateMode(self.BoundingRectViewportUpdate)
        self.setViewportUpdateMode(self.FullViewportUpdate)
        # self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setRenderHints(QPainter.Antialiasing)
        # self.setRenderHints(QPainter.TextAntialiasing)
        self.ldpi = self.logicalDpiX()
        self.pdpi = self.physicalDpiX()
        #print("PDPI:", self.pdpi)
# Scaling the scene by pdpi/ldpi should display the correct size ...
        #        self.MM2PT = self.ldpi / 25.4
#        self.scene = QGraphicsScene()
#        self.setScene(self.scene)

        ### Set up sizes (globally)
        global BOXWIDTH, BOXHEIGHT, SEPWIDTH, LINEWIDTH, TITLEHEIGHT, TITLEWIDTH
        BOXWIDTH = self.pt2px(_BOXWIDTH)
        BOXHEIGHT = self.pt2px(_BOXHEIGHT)
        SEPWIDTH = self.pt2px(_SEPWIDTH)
        LINEWIDTH = self.pt2px(_LINEWIDTH)
        TITLEHEIGHT = self.pt2px(_TITLEHEIGHT)
        TITLEWIDTH = self.pt2px(_TITLEWIDTH)

    def pt2px(self, pt):
        px = self.ldpi * pt / 72.0
        #print(f"pt2px: {pt} -> {px} (LDPI: {self.ldpi})")
        return px

    def px2mm(self, px):
        return px * 25.4 / self.ldpi


class GridViewRescaling(GridView):
    """An QGraphicsView that automatically adjusts the scaling of its
    scene to fill the viewing window.
    """
    def __init__(self):
        super().__init__()
        # Disable the scrollbars when using this resizing scheme. They
        # should not appear anyway, but this might avoid problems.
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def resizeEvent(self, event):
        self.rescale()
        return super().resizeEvent(event)

    def rescale(self):
        #qrect = self._sceneRect
        qrect = self.scene().sceneRect()
        self.fitInView(qrect, Qt.KeepAspectRatio)


# Experimental!
class GridViewHFit(GridView):
    """A QGraphicsView that automatically adjusts the scaling of its
    scene to fill the width of the viewing window.
    """
    def __init__(self):
        super().__init__()
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Avoid problems at on/off transition:
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

    def resizeEvent(self, event):
        self.rescale()
        return super().resizeEvent(event)

    def rescale(self):
        #qrect = self._sceneRect
        qrect = self.scene().sceneRect()
        size = self.size()
        vsb = self.verticalScrollBar()
        w = size.width()
# This might be problematic at the point where the scrollbar appears or
# disappears ...
# Initially the scrollbar is reported as invisible, even when it is
# clearly visible, so the calculation is wrong.
        if vsb.isVisible():
            w -= vsb.size().width()
        scale = w / qrect.width()
        t = QTransform().scale(scale, scale)
        self.setTransform(t)
#        self.fitInView(qrect, Qt.KeepAspectRatio)


class GridPeriodsDays(QGraphicsScene):
    def __init__(self, days, periods, breaks):
        self.tiles = {}
        super().__init__()
        self.xslots = [0]    # x-coordinate of column left side
        self.yslots = [0]    # y-coordinate of row top side
        # Cell at top left-hand corner
        self.addItem(Cell(0, 0, TITLEWIDTH, TITLEHEIGHT, -1, -1))
        # Add column headers
        x = TITLEWIDTH
        icol = 0
        for col_header in periods:
            if col_header in breaks:
                x += SEPWIDTH
            self.xslots.append(x)
            cell = Cell(x, 0, BOXWIDTH, TITLEHEIGHT, -1, icol)
            cell.set_text(col_header)
            cell.set_background(HEADER_COLOUR)
            self.addItem(cell)
            icol += 1
            x += BOXWIDTH
        self.grid_width = x
        # Add row headers and rows
        self.cell_matrix = []
        irow = 0
        y = TITLEHEIGHT
        for row_header in days:
            day_list = []
            self.cell_matrix.append(day_list)
            self.yslots.append(y)
            # row header
            cell = Cell(0, y, TITLEWIDTH, BOXHEIGHT, irow, -1)
            cell.set_text(row_header)
            cell.set_background(HEADER_COLOUR)
            self.addItem(cell)
            # period cells
            for i in range(icol):
                cell = Cell(self.xslots[i + 1], y, BOXWIDTH, BOXHEIGHT, irow, i)
                day_list.append(cell)
                self.addItem(cell)
            irow += 1
            y += BOXHEIGHT
        self.grid_height = y
        self.select = QGraphicsRectItem(0, 0, BOXWIDTH, BOXHEIGHT)
        self.select.setPen(StyleCache.getPen(LINEWIDTH*2, SELECT_COLOUR))
        self.select.setZValue(20)
        self.select.hide()
        self.addItem(self.select)

#
    def get_cell(self, row, col):
        return self.cell_matrix[row][col]
#
    def mousePressEvent(self, event):
        point = event.scenePos()
        items = self.items(point)
        if items:
            if event.button() == Qt.LeftButton:
#TODO ...
                kbdmods = QApplication.keyboardModifiers()
                shift = " + SHIFT" if kbdmods & Qt.ShiftModifier else ""
                alt = " + ALT" if kbdmods & Qt.AltModifier else ""
                ctrl = " + CTRL" if kbdmods & Qt.ControlModifier else ""
                cell = None
                tiles = []
                item0 = None
                for item in items:
                    try:
                        cell = item.cell
                        item0 = item
                    except AttributeError:
                        tiles.append(item)
                for tile in tiles:
                    # Give all tiles at this point a chance to react, starting
                    # with the topmost. An item can break the chain by
                    # returning a false value.
                    try:
                        if not tile.leftclick():
                            return
                    except AttributeError:
                        pass
                if cell:
                    print (f"Cell – left press{shift}{ctrl}{alt} @ {item.cell}")
# Note that ctrl-click is for context menu on OSX ...
                    if shift:
                        self.place_tile("T2", cell)
                    if alt:
                        self.select_cell(cell)

    def contextMenuEvent(self, event):
        point = event.scenePos()
        items = self.items(point)
        if items:
            for item in items:
                # Give all items at this point a chance to react, starting
                # with the topmost. An item can break the chain by
                # returning a false value.
                try:
                    if not item.contextmenu():
                        return
                except AttributeError:
                    pass
                print (f"Cell – context menu @ {item.cell}")

    def new_tile(self, tag, duration, nmsg, offset, total, text, colour):
        t = Tile(duration, nmsg, offset, total, text, colour)
        self.addItem(t)
        self.tiles[tag] = t

    def place_tile(self, tag, cell):
        tile = self.tiles[tag]
        x = self.xslots[cell[0] + 1]    # first cell is header
        y = self.yslots[cell[1] + 1]    # first cell is header
        w = BOXWIDTH - LINEWIDTH #* 2
        if tile.duration > 1:
            w += self.xslots[cell[0] + tile.duration] - x
        tile.set_cell(x, y, w)

    def select_cell(self, cell):
        x = self.xslots[cell[0] + 1]    # first cell is header
        y = self.yslots[cell[1] + 1]    # first cell is header
        self.select.setPos(x, y)
        self.select.show()


class Tile(QGraphicsRectItem):
    def __init__(self, duration, nmsg, offset, total, text, colour):
        self.duration = duration
        self.height = BOXHEIGHT  * nmsg / total# - LINEWIDTH# * 2
        self.y = BOXHEIGHT * offset / total + LINEWIDTH/2
        super().__init__(
            LINEWIDTH/2,
            self.y,
            BOXWIDTH,
            self.height
        )
        self.setBrush(StyleCache.getBrush(colour))
        self.text_item = QGraphicsSimpleTextItem(self)
        self.set_text(text)
        self.hide()

    def set_text(self, text):
        self.text_item.setText(text)
        text_rect = self.text_item.boundingRect()
        rect = self.rect()
        self.text_width = text_rect.width()
        self.yshift = self.y + (rect.height() - text_rect.height()) / 2
        xshift = (rect.width() - self.text_width) / 2
        self.text_item.setPos(xshift, self.yshift)

    def set_cell(self, x, y, w):
        rect = self.rect()
        rect.setWidth(w)
        self.setRect(rect)
        self.setPos(x, y)
        self.text_item.setPos((w - self.text_width) / 2, self.yshift)
        self.show()



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
#
    def set_text(self, text):
        """Set a centred text item. Calling the function a second time
        updates the text.
        """
        try:
            item = self.text_item
        except AttributeError:
            item = QGraphicsSimpleTextItem(self)
            self.text_item = item
        item.setText(text)
        bdrect = item.boundingRect()
        #print("§§§", text, bdrect)
        wt = bdrect.width()
        ht = bdrect.height()
        rect = self.rect()
        xshift = (rect.width() - wt) / 2
        yshift = (rect.height() - ht) / 2
        item.setPos(xshift, yshift)

###

class Cell(Box):
    """This is a rectangle representing a single period slot. It is used
    to construct the basic timetable grid.
    It is a <Box> whose background colour is settable and which supports
    hover events.
    """
#TODO: highlighting by emphasizing the border:
#    selected = None

#    @classmethod
#    def setup(cls):
#        cls.nBrush = StyleCache.getBrush(None)
#        cls.hBrush = StyleCache.getBrush(CELL_HIGHLIGHT_COLOUR)
#        cls.nPen = StyleCache.getPen(LINEWIDTH + 2, BORDER_COLOUR)
#        cls.sPen = StyleCache.getPen(LINEWIDTH + 2, SELECT_COLOUR)

#    @classmethod
#    def select(cls, cell):
#        if cls.selected:
#            cls.selected.setPen(cls.nPen)
#            cls.selected.setZValue(0)
#            cls.selected = None
#        if cell:
#            cell.setPen(cls.sPen)
#            cell.setZValue(20)
#            cls.selected = cell

    def __init__(self, x, y, w, h, irow, icol):
        """Create a box at scene coordinates (x, y) with width w and
        height h. irow and icol are row and column indexes.
        """
        super().__init__(x, y, w, h, width=LINEWIDTH)
        self.x0 = x
        self.y0 = y
        self.cell = (icol, irow)
        self.setAcceptHoverEvents(True)
#        print ("Cell", icol, irow, x, y)

    def hoverEnterEvent(self, event):
        print("Enter", self.cell)

    def hoverLeaveEvent(self, event):
        print("Leave", self.cell)

    def set_background(self, colour):
        """Set the cell background colour.
        <colour> can be <None> ("no fill") or a colour in the form 'RRGGBB'.
        """
        self.setBrush(StyleCache.getBrush(colour))

###

#TODO
class Tile0(QGraphicsRectItem):
    """The graphical representation of a lesson.
    """
    margin = 3.0

    def __init__(self, grid, id_, text, division=1.0, duration=1, offset=0.0):
        super().__init__()
        self.duration = duration
        # TODO: division according to number of subgroups?
        self.grid = grid
        self.id_ = id_
        self.fullheight = self.grid.boxheight - self.margin*2
        self.height = self.fullheight * division
# If setting parent don't do the following line.
        grid.addItem(self)
        self.text = QGraphicsSimpleTextItem(text, self)
        bdrect = self.text.boundingRect()
        self.textw = bdrect.width()
        self.texty = (self.height - bdrect.height()) / 2

        self.setOffset(offset)

        self.setZValue(20)
        self.setBrush(QBrush(QColor('#d0f0f0f0')))
#        self.setVisible(False)
#        self.setAcceptHoverEvents (True)
        self.setFlag(self.ItemIsFocusable)

    def setOffset(self, offset):
        """Set the vertical offset of the tile in relation to the cell area.
        It is fractional: 0.0 <= <offset> < 1.0
        """
# Another option might be to use an integer (number of subgroups above
# this tile) ...
        self.offset = offset * self.fullheight
#
    def place(self, row, col):
        cell = self.grid.getCell(row, col)
        cell2 = self.grid.getCell(row, col + self.duration - 1) \
                if self.duration > 1 else cell
        xl = cell.x0
        xr = cell2.x0 + self.grid.boxwidth
        self.width = xr - xl - self.margin*2
        self.setRect(0, 0, self.width, self.height)
        xshift = (self.width - self.textw) / 2
        self.text.setPos(xshift, self.texty)
        self.setPos(cell.x0 + self.margin, cell.y0 + self.offset + self.margin)
#        self.setVisible(True)
#
# Mouse events should perhaps be received from the scene ...
#
# Are key presses at all relevant?
    def keyPressEvent(self, event):
        print("KEY:", event.key(), event.text())

    def hide(self):
        self.setVisible(False)

#?
    def contextMenuEvent(self, event):
        #        menu = QMenu ("Context Menu")
        menu = QMenu()
        Action = menu.addAction("I am a context Action")
        Action.triggered.connect(self.printName)

        menu.exec_(event.screenPos())
#?
    def printName(self):
        print("Action triggered from {}".format(self.id_))


###

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
            pen = QPen(QColor('#FF' + wc[1]))
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


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    args = set(sys.argv[1:])
    try:
        args.remove('--debug')
    except KeyError:
        def __debug(*msg):
            pass
    else:
        def __debug(*msg):
            print("DEBUG:::", *msg)
    builtins.DEBUG = __debug
    DEBUG("sys.argv:", sys.argv)

    main(set(sys.path[1:]))
