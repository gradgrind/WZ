# -*- coding: utf-8 -*-
"""
ui/wz_main.py

Last updated:  2021-08-25

The timetable "main" window.


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
    os.environ['PYSIDE_DESIGNER_PLUGINS'] = this

    from PySide6.QtWidgets import QApplication#, QStyleFactory
    from PySide6.QtCore import QLocale, QTranslator, QLibraryInfo
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

from PySide6.QtWidgets import QGraphicsScene, QGraphicsRectItem, \
        QGraphicsSimpleTextItem
from PySide6.QtCore import Qt#, QSettings
from PySide6.QtGui import QIcon, QPen, QBrush, QColor#, QPixmap

from ui.ui_support import ui_load

### +++++

BOXWIDTH = 80
BOXHEIGHT = 80
SEPWIDTH = 10
LINEWIDTH = 2
TITLEHEIGHT = 20
TITLEWIDTH = 40
BORDER_COLOUR = '6060d0'         # rrggbb
HEADER_COLOUR = 'a0a0a0'
CELL_HIGHLIGHT_COLOUR = 'a0a0ff' # rrggbb
#FONT_COLOUR = '442222'           # rrggbb
SELECT_COLOUR = 'f000f0'         # rrggbb

#TODO: these should be in a config file:
DAYS = ('Mo', 'Di', 'Mi', 'Do', 'Fr')
PERIODS = ('A', 'B', '1', '2', '3', '4', '5', '6', '7')
BREAKS = ('1', '3', '5')

### -----

def main(args):
    # Persistent Settings:
#    builtins.SETTINGS = QSettings(
#            QSettings.IniFormat, QSettings.UserScope, 'MT', 'WZ')
    builtins.WINDOW = ui_load('timetable.ui')

    # Set up grid
    grid = GridPeriodsDays(DAYS, PERIODS, BREAKS)
    WINDOW.table_view.setScene(grid)

#    WINDOW.setWindowIcon(QIcon(":/icons/tt.svg")) # in ui file
    WINDOW.show()
    sys.exit(app.exec())


    return


## Alternive ui loader using generated python file:
# ../../venv/bin/pyside6-uic designer/timetable.ui > timetable_ui_test.py
# The path to the icon resources must be set up as ui.icons_rc ... which
# designer doesn't like. It looks like a BUG, so go with my patch for the
# ui-file loader (in ui_load).
def main2(args):
    from PySide6.QtWidgets import QMainWindow
    from ui.timetable_ui_test import Ui_MainWindow
    wmain = QMainWindow()
    builtins.WINDOW = Ui_MainWindow()
    WINDOW.setupUi(wmain)
    # Set up grid
    grid = GridPeriodsDays(DAYS, PERIODS, BREAKS)
    WINDOW.table_view.setScene(grid)

#    WINDOW.setWindowIcon(QIcon(":/icons/tt.svg")) # in ui file
    wmain.show()
    sys.exit(app.exec())


    # Determine data directory
#TODO: pass datadir to back-end, perhaps as command-line parameter!
# It might be possible to change the datadir from the gui.
# Could use SETTINGS...

#    SETTINGS.setValue('DATA', os.path.join(__basedir, 'DATA'))
#    print("$$$", SETTINGS.value('DATA'), SETTINGS.allKeys())

    try:
        args.remove('--test')
    except:
        testing = False
        datadir = SETTINGS.value('DATA') or ''
    else:
        testing = True
#TODO: This might be disabled or modified in a release version?
# The test data might be provided in a pristine archive, which can be
# unpacked to some work folder and registered there in settings?
        datadir = os.path.join(appdir, 'TESTDATA')

#TODO: If no DATADIR, get it from "settings".
# If none set, need to select one, or else load the test data, or
# start from scratch. Starting from scratch one would need to select
# a folder and immediately edit a calendar – perhaps the one from the
# test data could be taken as a starting point (changing to current
# year, as in migrate_year). Also other files can be "borrowed" from
# the test data. There should be a prompt to add pupils (can one do
# this manually when there are none present?).

    app.setWindowIcon(QIcon(os.path.join('icons', 'WZ1.png')))
    screen = app.primaryScreen()
    screensize = screen.availableSize()
    main_window.resize(screensize.width()*0.8, screensize.height()*0.8)
    main_window.show()
    sys.exit(app.exec())

###

class GridPeriodsDays(QGraphicsScene):
    def __init__(self, days, periods, breaks):
        super().__init__()
        xslots = [0]    # x-coordinate of column left side
        yslots = [0]    # y-coordinate of row top side
        # Cell at top left-hand corner
        self.addItem(Cell(0, 0, TITLEWIDTH, TITLEHEIGHT, -1, -1))
        # Add column headers
        x = TITLEWIDTH
        icol = 0
        for col_header in periods:
            if col_header in breaks:
                x += SEPWIDTH
            xslots.append(x)
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
            yslots.append(y)
            # row header
            cell = Cell(0, y, TITLEWIDTH, BOXHEIGHT, irow, -1)
            cell.set_text(row_header)
            cell.set_background(HEADER_COLOUR)
            self.addItem(cell)
            # period cells
            for i in range(icol):
                cell = Cell(xslots[i + 1], y, BOXWIDTH, BOXHEIGHT, irow, i)
                day_list.append(cell)
                self.addItem(cell)
            irow += 1
            y += BOXHEIGHT
        self.grid_height = y
#
    def get_cell(self, row, col):
        return self.cell_matrix[row][col]
#
    def mousePressEvent(self, event):
        point = event.scenePos()
        print("Scene PRESS:", point, self.items(point))
        kbdmods = QApplication.keyboardModifiers()
        if kbdmods & Qt.ShiftModifier:
            print("SHIFT")
        if kbdmods & Qt.ControlModifier:
            print("CTRL")

###

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
        self.icol = icol
        self.irow = irow
        self.setAcceptHoverEvents(True)
#        print ("Cell", icol, irow, x, y)

    def hoverEnterEvent(self, event):
        print("Enter", self.irow, self.icol)

    def hoverLeaveEvent(self, event):
        print("Leave", self.irow, self.icol)

    def set_background(self, colour):
        """Set the cell background colour.
        <colour> can be <None> ("no fill") or a colour in the form 'RRGGBB'.
        """
        self.setBrush(StyleCache.getBrush(colour))

###

#TODO
class Tile(QGraphicsRectItem):
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
