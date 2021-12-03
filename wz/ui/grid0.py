# -*- coding: utf-8 -*-
"""
ui/grid0.py

Last updated:  2021-12-03

Widget with tiles on grid layout (QGraphicsScene/QGraphicsView).

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

The coordinate system is such that rectangle borders are roughly
centred on the given coordinates. Regard a coordinate as a line without
width before the pixel which is actually drawn.
Given a coordinate x = 5:
    border = 1 => pixel 5
    border = 2 => pixels 4/5
    border = 3 => pixels 4/5/6
If a grid is drawn (separately from the tiles), it might be necessary
to adjust the coordinates of the tile so as not to paint over the grid.
Alternatively, putting the grid lines on top might be an easier solution.

"When rendering with a pen with an even number of pixels, the pixels will
be rendered symetrically around the mathematical defined points, while
rendering with a pen with an odd number of pixels, the spare pixel will
be rendered to the right and below the mathematical point.
"
"""

##### Configuration #####################
# ?
FONT_DEFAULT = "Droid Sans"
FONT_SIZE_DEFAULT = 11
FONT_COLOUR = "442222"  # rrggbb
GRID_COLOUR = "000088"  # rrggbb
# MARK_COLOUR = 'E00000'      # rrggbb

# Line width for borders
# UNDERLINE_WIDTH = 3
# BORDER_WIDTH = 1

SCENE_MARGIN = 10  # Margin around content in GraphicsView widgets
TITLE_MARGIN = 15  # Left & right title margin (points)
#####################

### Messages
_TILE_OUT_OF_BOUNDS = (
    "Kachel außerhalb Tabellenbereich:\n"
    " Zeile {row}, Höhe {rspan}, Spalte {col}, Breite {cspan}"
)
_NOTSTRING = "In <grid::Tile>: Zeichenkette erwartet: {val}"

#####################################################

from qtpy.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsRectItem,
    QGraphicsSimpleTextItem,
    QGraphicsLineItem,
)
from qtpy.QtGui import (
    QFont,
    QPen,
    QColor,
    QBrush,
    QTransform,
    QPainter,
    QPdfWriter,
    QPageLayout,
)
from qtpy.QtCore import Qt, QMarginsF, QRectF


class GridError(Exception):
    pass


### -----


class GridView(QGraphicsView):
    """This is the "view" widget for the grid.
    The actual grid is implemented as a "scene".
    """

    def __init__(self):
        self._scale = 1.0
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
        #        self.pdpi = self.physicalDpiX()
        #        self.MM2PT = self.ldpi / 25.4
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

    def pt2px(self, pt):
        px = self.ldpi * pt / 72.0
        # print(f"pt2px: {pt} -> {px}")
        return px

    def px2mm(self, px):
        return px * 25.4 / self.ldpi

    def mousePressEvent(self, event):
        try:
            point = event.position().toPoint()
        except:
            point = event.pos()
        # print("POS:", point, self.mapToGlobal(point), self.itemAt(point))
        # The Tile may not be the top item.
        items = self.items(point)
        if items and event.button() == Qt.LeftButton:
            for item in items:
                # Give all items at this point a chance to react, starting
                # with the topmost. An item can break the chain by
                # returning a false value.
                try:
                    if not item.leftclick():
                        return
                except AttributeError:
                    pass

    def contextMenuEvent(self, event):
        try:
            point = event.position().toPoint()
        except:
            point = event.pos()
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

    ### View scaling
    def scaleUp(self):
        self.scale(1)

    def scaleDn(self):
        self.scale(-1)

    def scale(self, delta):
        t = QTransform()
        self._scale += self._scale * delta / 10
        t.scale(self._scale, self._scale)
        self.setTransform(t)

    ### ---------------

    def init(self, rowheights, columnwidths, titleheight=0):
        """Set the grid size.
            <columnwidths>: a list of column widths (points)
            <rowheights>: a list of row heights (points)
        Rows and columns are 0-indexed.
        The widths/heights include grid lines and other bounding boxes.
        """
        self.titleheight = self.pt2px(titleheight)
        self.scene.clear()
        self.xmarks = [0]
        xpt = 0
        x = 0
        for c in columnwidths:
            xpt += c
            c = self.pt2px(c)
            x += c
            self.xmarks.append(x)
        self.grid_width = x
        y = self.titleheight
        self.ymarks = [y]
        ypt = 0
        for r in rowheights:
            ypt += r
            r = self.pt2px(r)
            y += r
            self.ymarks.append(y)
        self.grid_height = y
        self.grid_xpt, self.grid_ypt = (xpt, ypt)

        # print("X:", self.xmarks)
        # print("Y:", self.ymarks)

        # Draw grid
        self.grid_pen = GraphicsSupport.getPen(1, GRID_COLOUR)
        for i in range(len(self.xmarks)):
            self.scene.addItem(GridLine(self, True, i))
        for i in range(len(self.ymarks)):
            self.scene.addItem(GridLine(self, False, i))

        # Allow a little margin
        margin = self.pt2px(SCENE_MARGIN)
        self._sceneRect = QRectF(
            -margin,
            -margin,
            self.grid_width + margin * 2,
            self.grid_height + margin * 2,
        )
        self.scene.setSceneRect(self._sceneRect)

    def add_title(self, text, halign="c"):
        textItem = QGraphicsSimpleTextItem()
        self.scene.addItem(textItem)
        font = QFont(GraphicsSupport.getFont())
        if halign == "c":
            font.setPointSizeF(font.pointSizeF() * 1.2)
        font.setBold(True)
        textItem.setFont(font)
        textItem.setText(text)
        bdrect = textItem.mapRectToParent(textItem.boundingRect())
        w = bdrect.width()
        h = bdrect.height()
        xshift = 0.0
        yshift = 0.0
        margin = self.pt2px(TITLE_MARGIN)
        if halign == "l":
            xshift += margin
        elif halign == "r":
            xshift += self.grid_width - margin - w
        else:
            xshift += (self.grid_width - w) / 2
        yshift += (self.titleheight - h) / 2
        textItem.setPos(xshift, yshift)
        return textItem

    def basic_tile(self, row, col, cspan=1, rspan=1, **kargs):
        """Add a basic tile to the grid, checking coordinates and
        converting row + col to x + y point-coordinates for the
        <Tile> class.
        """
        # Check bounds
        if (
            row < 0
            or col < 0
            or (row + rspan) >= len(self.ymarks)
            or (col + cspan) >= len(self.xmarks)
        ):
            raise GridError(
                _TILE_OUT_OF_BOUNDS.format(row=row, col=col, cspan=cspan, rspan=rspan)
            )
        x = self.xmarks[col] + 0.5
        y = self.ymarks[row] + 0.5
        w = self.xmarks[col + cspan] - x - 0.5
        h = self.ymarks[row + rspan] - y - 0.5
        t = Tile(self, x, y, w, h, **kargs)
        self.scene.addItem(t)
        return t

    ### pdf output
    def setPdfMargins(self, left=50, top=30, right=30, bottom=30):
        self._pdfmargins = (left, top, right, bottom)
        return self._pdfmargins

    def pdfMargins(self):
        try:
            return self._pdfmargins
        except AttributeError:
            return self.setPdfMargins()

    def to_pdf(self, filepath, landscape=False, can_rotate=True):
        """Produce and save a pdf of the table.
        The output orientation can be selected via the <landscape> parameter.
        If possible, the table will be printed full size. If that doesn't
        fit, and if it would fit better in the other orientation, the
        table will be rotated automatically – so long as <can_rotate> is
        true.
        If the table is still too big for the page, it will be shrunk to
        fit.
        To avoid too much complexity here, the automatic scaling of the
        <scene.render()> method is used. All sizes (points) are converted
        to "pixels" (using method <pt2px>), as that is what is needed for
        setting the scene rectangle. It ensures that the font size and
        grid size remain in a fairly constant relationship to each other.
        """
        # print(f"TABLE: {self.px2mm(self.grid_width)} X"
        #        f" {self.px2mm(self.grid_height)}")
        if not filepath.endswith(".pdf"):
            filepath += ".pdf"
        printer = QPdfWriter(filepath)
        printer.setPageSize(printer.A4)
        margins = self.pdfMargins()
        # print("margins:", margins)
        printer.setPageMargins(QMarginsF(*margins), QPageLayout.Point)
        page_layout = printer.pageLayout()
        pdf_rect = page_layout.paintRect(QPageLayout.Point)
        # print("?1a:", page_layout.pageSize().size(QPageSize.Point),
        #        printer.resolution())
        # print("?2a:", pdf_rect)

        # Convert the pdf print area (initially points) to "pixels"
        pdf_wpx = self.pt2px(pdf_rect.width())
        pdf_hpx = self.pt2px(pdf_rect.height())

        # Prepare the scene for printing – check size
        if self.grid_width > self.grid_height:
            if (not landscape) and (self.grid_width > pdf_wpx) and can_rotate:
                # The table is wider than the pdf area, so it would
                # benefit from rotating
                landscape = True
        elif self.grid_width < self.grid_height:
            if landscape and (self.grid_height > pdf_hpx) and can_rotate:
                # The table is taller than the pdf area, so it would
                # benefit from rotating
                landscape = False
        if landscape:
            printer.setPageOrientation(QPageLayout.Orientation.Landscape)
            # In landscape mode, rotate the given margins so that "left"
            # refers to the top margin.
            margins = margins[3:] + margins[:3]
            # print("margins:", margins)
            printer.setPageMargins(QMarginsF(*margins), QPageLayout.Point)
            page_layout = printer.pageLayout()
            pdf_rect = page_layout.paintRect(QPageLayout.Point)
            # print("?1b:", page_layout.pageSize().size(QPageSize.Point))
            # print("?2b:", pdf_rect)
            # Convert the pdf print area (initially points) to "pixels"
            pdf_wpx = self.pt2px(pdf_rect.width())
            pdf_hpx = self.pt2px(pdf_rect.height())

        # Render the table to pdf
        painter = QPainter()
        painter.begin(printer)
        if (self.grid_width < pdf_wpx) and (self.grid_height < pdf_hpx):
            # If both dimensions are smaller than the pdf area, expand the
            # scene rectangle to avoid the table being enlarged.
            self.scene.setSceneRect(0, 0, pdf_wpx, pdf_hpx)
            self.scene.render(painter)
            # print("SR1:", self.scene.sceneRect())
            self.scene.setSceneRect(self._sceneRect)
            # print("SR2:", self.scene.sceneRect())
        else:
            # print("SRX:", pdf_wpx, pdf_hpx)
            self.scene.render(painter)
            # print("SR:", self.scene.sceneRect())
        painter.end()
        return filepath


class GridLine(QGraphicsLineItem):
    def __init__(self, view, vertical, index):
        self.index = index
        if vertical:
            self.w = 0
            self.h = view.grid_height - view.titleheight
            self.x = view.xmarks[index]
            self.y = view.titleheight
        else:
            self.w = view.grid_width
            self.h = 0
            self.x = 0
            self.y = view.ymarks[index]
        super().__init__(self.x, self.y, self.x + self.w, self.y + self.h)
        self.setPen(view.grid_pen)
        self.setZValue(-10)


# TODO: Additional functionality (moving grid lines?) can be added here ...
#        self.setAcceptHoverEvents(True)
#
#    def hoverEnterEvent(self, event):
#        print("Enter", "V" if self.h else "H", self.index)
#
#    def hoverLeaveEvent(self, event):
#        print("Leave", "V" if self.h else "H", self.index)
#
# Note that the hover events will also be captured if the line is hidden.


class GridViewRescaling(GridView):
    """An QGraphicsView that automatically adjusts the scaling of its
    scene to fill the viewing window.
    """

    def __init__(self):
        super().__init__()
        # Apparently it is a good idea to disable scrollbars when using
        # this resizing scheme. With this resizing scheme they would not
        # appear anyway, so this doesn't lose any features!
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def resizeEvent(self, event):
        self.rescale()
        return super().resizeEvent(event)

    def rescale(self, qrect=None):
        if qrect == None:
            qrect = self._sceneRect
        self.fitInView(qrect, Qt.KeepAspectRatio)


# Experimental!
class GridViewHFit(GridView):
    """An QGraphicsView that automatically adjusts the scaling of its
    scene to fill the width of the viewing window. If
    """

    def __init__(self):
        super().__init__()
        # Apparently it is a good idea to disable scrollbars when using
        # this resizing scheme. With this resizing scheme they would not
        # appear anyway, so this doesn't lose any features!
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
#        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def resizeEvent(self, event):
        self.rescale()
        return super().resizeEvent(event)

    def rescale(self, qrect=None):
        if qrect == None:
            qrect = self._sceneRect
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


class Tile(QGraphicsRectItem):
    """The graphical representation of a table cell.
    This cell can span rows and columns.
    It contains a simple text element. The cell has the peculiarity,
    however, that the text is shrunk automatically if it is too big to
    fit in the cell. This only works to a certain degree. If the text
    would become ridiculously small, only '###' is displayed.
    Both cell and text can be styled to a limited extent.
    """

    def __init__(self, grid, x, y, w, h, text="", tag=None, **style):
        self._grid = grid
        self.tag = tag
        self.height0 = h
        self.width0 = w
        super().__init__(0, 0, w, h)
        self.setFlag(self.ItemClipsChildrenToShape, True)
        self.setPos(x, y)
        self.style = {
            "bg": None,
            "font": None,
            "fg": FONT_COLOUR,
            "halign": "c",
            "valign": "m",
            "rotate": False,
        }
        self.style.update(style)
        self.halign = self.style["halign"]
        self.valign = self.style["valign"]
        self.rotation = self.style["rotate"]
        bg = self.style["bg"]
        if bg:
            self.set_background(bg)
        # Text
        self.textItem = QGraphicsSimpleTextItem(self)
        font = self.style["font"]
        if font:
            self.textItem.setFont(font)
        else:
            self.textItem.setFont(GraphicsSupport.getFont())
        self.setText(text)
        self.set_textcolour(self.style["fg"])
        # Border
        pen0 = GraphicsSupport.getPen(None)
        self.setPen(pen0)

    def set_background(self, colour):
        self.setBrush(GraphicsSupport.getBrush(colour))

    def set_textcolour(self, colour):
        self.textItem.setBrush(GraphicsSupport.getBrush(colour))

    def set_halign(self, halign):
        self.halign = halign

    def set_verticaltext(self, rot90=True):
        self.rotation = rot90
        self.setText(self.text)

    def margin(self):
        #        return 0.4 * self._grid._gview.MM2PT
        return self._grid.pt2px(2)

    def value(self):
        return self.text

    def setText(self, text):
        if type(text) != str:
            raise GridError(_NOTSTRING.format(val=repr(text)))
        self.text = text
        self.textItem.setText(text)
        self.textItem.setScale(1)
        w = self.textItem.boundingRect().width()
        h = self.textItem.boundingRect().height()
        margin = self.margin()
        if text:
            scale = 1
            maxw = self.width0 - margin * 2
            maxh = self.height0 - margin * 2
            if self.rotation:
                maxh -= margin * 4
                if w > maxh:
                    scale = maxh / w
                if h > maxw:
                    _scale = maxw / h
                    if _scale < scale:
                        scale = _scale
                if scale < 0.6:
                    self.textItem.setText("###")
                    scale = maxh / self.textItem.boundingRect().width()
                if scale < 1:
                    self.textItem.setScale(scale)
                trf = QTransform().rotate(-90)
                self.textItem.setTransform(trf)
            else:
                maxw -= margin * 4
                if w > maxw:
                    scale = maxw / w
                if h > maxh:
                    _scale = maxh / h
                    if _scale < scale:
                        scale = _scale
                if scale < 0.6:
                    self.textItem.setText("###")
                    scale = maxw / self.textItem.boundingRect().width()
                if scale < 1:
                    self.textItem.setScale(scale)
        # This print line can help find box size problems:
        #            print("BOX-SCALE: %5.3f (%s) *** w: %6.2f / %6.2f *** h: %6.2f / %6.2f"
        #                    % (scale, text, w, maxw, h, maxh))
        bdrect = self.textItem.mapRectToParent(self.textItem.boundingRect())
        yshift = -bdrect.top() if self.rotation else 0.0
        w = bdrect.width()
        h = bdrect.height()
        xshift = 0.0
        if self.halign == "l":
            xshift += margin
        elif self.halign == "r":
            xshift += self.width0 - margin - w
        else:
            xshift += (self.width0 - w) / 2
        if self.valign == "t":
            yshift += margin
        elif self.valign == "b":
            yshift += self.height0 - margin - h
        else:
            yshift += (self.height0 - h) / 2
        self.textItem.setPos(xshift, yshift)

    def leftclick(self):
        print("LEFT CLICK:", self.tag or "–––")
        return self._grid.tile_left_clicked(self)

    def contextmenu(self):
        print("CONTEXT MENU:", self.tag or "–––")
        return self._grid.tile_right_clicked(self)


class GraphicsSupport:
    """Support functions for the grid."""

    __fonts = {}  # cache for QFont items
    __brushes = {}  # cache for QBrush items
    __pens = {}  # cache for QPen items

    @classmethod
    def getFont(
        cls,
        fontFamily=FONT_DEFAULT,
        fontSize=FONT_SIZE_DEFAULT,
        fontBold=False,
        fontItalic=False,
    ):
        ftag = (fontFamily, fontSize, fontBold, fontItalic)
        try:
            return cls.__fonts[ftag]
        except KeyError:
            pass
        font = QFont()
        if fontFamily:
            font.setFamily(fontFamily)
        if fontSize:
            font.setPointSizeF(fontSize)
        if fontBold:
            font.setBold(True)
        if fontItalic:
            font.setItalic(True)
        cls.__fonts[ftag] = font
        return font

    @classmethod
    def getPen(cls, width, colour=None):
        """Manage a cache for pens of different width and colour."""
        if width:
            wc = (width, colour or GRID_COLOUR)
            try:
                return cls.__pens[wc]
            except KeyError:
                pass
            pen = QPen(QColor("#FF" + wc[1]))
            pen.setWidthF(wc[0])
            cls.__pens[wc] = pen
            return pen
        else:
            try:
                return cls.__pens[None]
            except KeyError:
                pen = QPen()
                pen.setStyle(Qt.NoPen)
                cls.__pens[None] = pen
                return pen

    @classmethod
    def getBrush(cls, colour=None):
        """Manage a cache for brushes of different colour.
        <colour> is a colour in the form 'RRGGBB'.
        """
        try:
            return cls.__brushes[colour]
        except KeyError:
            pass
        if colour:
            brush = QBrush(QColor("#FF" + (colour)))
        else:
            brush = QBrush()
        cls.__brushes[colour] = brush
        return brush


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    rows = (100, 6, 25, 25, 25, 25, 25)
    cols = (80, 30, 25, 60, 25, 25, 350)

    from qtpy.QtWidgets import QApplication

    app = QApplication([])
    #    grid = GridViewRescaling()
    grid = GridView()
    titleheight = 25
    grid.init(rows, cols, titleheight)

    t1 = grid.basic_tile(3, 0, text="Two Merged Cells", cspan=2, bg="ffff80")
    grid.basic_tile(5, 3, text="I am")
    grid.basic_tile(
        0,
        2,
        text="Rotated",
        rotate=True,
        font=GraphicsSupport.getFont("Serif", fontBold=True, fontItalic=False),
    )
    if titleheight:
        title = grid.add_title("Centre Title")
        title_l = grid.add_title("Left Title", halign="l")
        title_r = grid.add_title("Right Title", halign="r")

    grid.resize(600, 400)
    grid.show()

    # Enable package import if running as module
    import sys, os

    # print(sys.path)
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    from core.base import start

    basedir = os.path.dirname(appdir)
    start.setup(os.path.join(basedir, "TESTDATA"))

    fpath = os.path.join(os.path.expanduser("~"), "test.pdf")
    fpath = DATAPATH("testing/tmp/grid0.pdf")
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    grid.to_pdf(fpath)
    #    grid.to_pdf(fpath, can_rotate = False)

    app.exec()
