"""
ui/grid_base.py

Last updated:  2022-11-20

Base functions for table-grids using the QGraphicsView framework.

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
be rendered symmetrically around the mathematically defined points, while
rendering with a pen with an odd number of pixels, the spare pixel will
be rendered to the right and below the mathematical point.
"

The grid area can be covered by boxes of predefined width and height.
I would suggest an optional box border of fixed width (but what does
"fixed width" mean here, e.g fixed pixels or fixed points/mm? As I am
aiming for a point/mm based specification, I would suggest the latter).
If there is no border there will be an empty gap – thus making the
geometry independent of the border. That would mean that "no border"
would need a transparent pen.
"""

##### Configuration #####################
GRID_COLOUR = "888800"  # rrggbb
SELECT_COLOUR = "2370ff"
FONT_SIZE_DEFAULT = 12
BORDER_WIDTH = 1
THICK_LINE_WIDTH = 3
SELECT_WIDTH = 3
SCENE_MARGIN = 10  # Margin around content in GraphicsView widgets
TITLE_MARGIN = 15  # Left & right title margin (points)


# ?
#FONT_DEFAULT = "Droid Sans"
FONT_COLOUR = "442222"  # rrggbb
# MARK_COLOUR = 'E00000'      # rrggbb


#####################

### Messages
_TILE_OUT_OF_BOUNDS = (
    "Kachel außerhalb Tabellenbereich:\n"
    " Zeile {row}, Höhe {rspan}, Spalte {col}, Breite {cspan}"
)
_NOTSTRING = "In <grid::Tile>: Zeichenkette erwartet: {val}"

#####################################################

from qtpy.QtWidgets import (
    QDialog,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsRectItem,
    QGraphicsSimpleTextItem,
    QGraphicsLineItem,
    QVBoxLayout,
    QLineEdit,
    QListWidget,
    QTableWidget,
    QTableWidgetItem,
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
    QPageSize,
)
from qtpy.QtCore import Qt, QMarginsF, QRectF, QPointF


class GridError(Exception):
    pass


### -----


class StyleCache:
    """Manage allocation of style resources using caches."""

    __fonts = {}  # cache for QFont items
    __brushes = {}  # cache for QBrush items
    __pens = {}  # cache for QPen items

    @classmethod
    def getPen(cls, width:int, colour:str="") -> QPen:
        """Manage a cache for pens of different width and colour.
        <width> should be a small integer.
        <colour> is a colour in the form 'RRGGBB'.
        """
        if width:
# A temporary bodge to allow a transparent border
            if colour is None:
                wc = (width, None)
            else:

                wc = (width, colour or GRID_COLOUR)
            try:
                return cls.__pens[wc]
            except KeyError:
                pass
# A temporary bodge to allow a transparent border
            if colour is None:
                pen = QPen(QColor("#00FFFFFF"))
            else:

                pen = QPen(QColor("#FF" + wc[1]))
            pen.setWidth(wc[0])
            cls.__pens[wc] = pen
            return pen
        else:
            try:
                return cls.__pens['*']
            except KeyError:
                pen = QPen()
                pen.setStyle(Qt.NoPen)
                cls.__pens['*'] = pen
                return pen

    @classmethod
    def getBrush(cls, colour:str="") -> QBrush:
        """Manage a cache for brushes of different colour.
        <colour> is a colour in the form 'RRGGBB'.
        """
        try:
            return cls.__brushes[colour or '*']
        except KeyError:
            pass
        if colour:
            brush = QBrush(QColor("#FF" + colour))
            cls.__brushes[colour] = brush
        else:
            brush = QBrush()    # no fill
            cls.__brushes['*'] = brush
        return brush

    @classmethod
    def getFont(
        cls,
        fontFamily:str="",
        fontSize:int=12,
        fontBold:bool=False,
        fontItalic:bool=False,
    ) -> QFont:
        """Manage a cache for fonts. The font parameters are passed as
        arguments.
        """
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


class Selection(QGraphicsRectItem):
    """A rectangle covering one or more cells.
    """
    def __init__(self, grid, parent=None):
        super().__init__(parent=parent)
        self.xmarks = grid.xmarks
        self.ymarks = grid.ymarks
        self.setPen(StyleCache.getPen(grid.pt2px(SELECT_WIDTH), SELECT_COLOUR))
        self.setZValue(20)
        grid.scene().addItem(self)
        self.clear()

    def clear(self):
        self.start_cellrc = (-1, -1)
        self.end_cellrc = (-1, -1)
        self.__range = (-1, -1, 0, 0)
        self.hide()

    def range(self):
        return self.__range

    def is_active(self):
        return self.isVisible()

    def set_pending(self, cellrc):
        """This is called on left-mouse-down. The actual selection only
        occurs after a small mouse movement.
        """
        self.start_cellrc = cellrc

    def is_primed(self):
        """Test whether a start cell is pending (or already set).
        """
        return self.start_cellrc[0] >= 0

    def set_end_cell(self, cellrc):
        if self.end_cellrc != cellrc:
            self.end_cellrc = cellrc
            self.expose()

    def expose(self):
        r0, c0 = self.start_cellrc
        r1, c1 = self.end_cellrc
        # Ensure that r0 <= r1 and c0 <= c1
        if r0 > r1:
            r0, r1 = r1, r0
        if c0 > c1:
            c0, c1 = c1, c0
        self.__range = (r0, c0, r1 - r0 + 1, c1 - c0 + 1)
        # Get the coordinate boundaries
        x0 = self.xmarks[c0]
        y0 = self.ymarks[r0]
        x1 = self.xmarks[c1 + 1]
        y1 = self.ymarks[r1 + 1]
        self.setRect(x0, y0, x1 - x0, y1 - y0)
        self.show()


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
        # self.pdpi = self.physicalDpiX()
        # self.MM2PT = self.ldpi / 25.4

    def pt2px(self, pt) -> int:
        px = int(self.ldpi * pt / 72.0 + 0.5)
        # print(f"pt2px: {pt} -> {px}")
        return px

    def px2mm(self, px):
        return px * 25.4 / self.ldpi

    def screen_coordinates(self, scene_pointf):
        """Return the screen coordinates of the given scene point.
        """
        viewp = self.mapFromScene(scene_pointf)
        return self.mapToGlobal(viewp)

    def mousePressEvent(self, event):
#Qt5
#        print("POS:", event.pos())
#        print("GLOBALPOS:", event.globalPos())
#        print("SCREENPOS:", event.screenPos())
#        print("WINDOWPOS:", event.windowPos())

#Qt6
#        print("POS:", event.position())
#        print("GLOBALPOS:", event.globalPosition())
#        print("SCENEPOS:", event.scenePosition())

        try:
            point = event.position().toPoint()  # Qt6
        except:
            point = event.pos()                 # Qt5
#
        print("§§????????", point)

        self.point0 = point
        self.select.clear()
#        self.end_cell = None
        # print("POS:", point, self.mapToGlobal(point), self.itemAt(point))
        # The sought <Tile> may not be the top item.
        items = self.items(point)
        if items and event.button() == Qt.LeftButton:
            # Only a grid cell is "selectable"
            for item in items:
                try:
                    self.select.set_pending(item.gridrc)
                    break # only take account of the first grid cell
                except AttributeError:
                    pass

    def mouseMoveEvent(self, event):
        # Only act if the selection has at least been "primed" – i.e.
        # if the left button is depressed.
        if not self.select.is_primed():
            return
        try:
            point = event.position().toPoint()
        except:
            point = event.pos()
        # print("MOVE TEST", point - self.point0)
        items = self.items(point)
        # Act only if the topmost selectable cell has changed
        for item in items:
            try:
                coords = item.gridrc
            except AttributeError:
                pass
            else:
                if self.select.is_active():
                    self.select.set_end_cell(coords)
                else:
                    delta = (point - self.point0).manhattanLength()
                    if delta > 1:
                        self.select.set_end_cell(coords)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        try:
            point = event.position().toPoint()
        except:
            point = event.pos()
        if self.select.is_active():
            print("§?§?§?§?§ SELECT ACTIVE:", self.select.range())
            return
        items = self.items(point)
        if items:
            for item in items:
                # Find the topmost <Tile> which responds to a click
                try:
                    click_handler = item.on_left_click
                except AttributeError:
                    continue
                point = self.screen_coordinates(item.scenePos())
                value = click_handler()
                if value is not None:
                    self.cell_modified(value)
                break

    def contextMenuEvent(self, event):
        try:
            pointf = event.position()   # Qt6
            point = pointf.toPoint()
        except:
            point = event.pos()         # Qt5
            pointf = QPointF(point)

#TODO: If within active selection, call it on this somehow?
# Otherwise clear selection?
        if self.select.is_active():
            print("§§????", pointf, self.select.rect())
            if self.select.contains(pointf):
                print("§§CONTAINED")
            else:
                self.select.clear()
#?

        items = self.items(point)
        if items:
            for item in items:
                # Find the topmost <Tile> which responds to the event
                try:
                    click_handler = item.on_context_menu
                except AttributeError:
                    continue
                click_handler()
                break


    def cell_modified(self, row, col):
        print("CELL MODIFIED:", row, col)

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
        self.border_width = self.pt2px(BORDER_WIDTH)
        self.thick_line_width = self.pt2px(THICK_LINE_WIDTH)
        scene = QGraphicsScene()
        self.setScene(scene)
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

        # Construct grid
        row_list = []
        self.rows = row_list
        for rx in range(len(rowheights)):
            row = []
            for cx in range(len(columnwidths)):
                row.append(
                    self.grid_tile(
                        rx, cx,
                        border=GRID_COLOUR,
                        grid_cell=True
                    )
                )
            row_list.append(row)

        # Allow a little margin
        margin = self.pt2px(SCENE_MARGIN)
        self._sceneRect = QRectF(
            -margin,
            -margin,
            self.grid_width + margin * 2,
            self.grid_height + margin * 2,
        )
        scene.setSceneRect(self._sceneRect)

        # Add a "selection" rectangle to the scene
        self.select = Selection(self)

    def add_title(self, text, halign="c"):
        textItem = QGraphicsSimpleTextItem()
        self.scene().addItem(textItem)
        font = QFont(StyleCache.getFont())
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

    def grid_line_thick_h(self, row):
        try:
            y = self.ymarks[row]
        except:
#TODO
            raise
        line = QGraphicsLineItem(self.xmarks[0], y, self.xmarks[-1], y)
        line.setPen(StyleCache.getPen(self.thick_line_width, GRID_COLOUR))
        line.setZValue(10)
        self.scene().addItem(line)

    def grid_line_thick_v(self, col):
        try:
            x = self.xmarks[col]
        except:
#TODO
            raise
        line = QGraphicsLineItem(x, self.ymarks[0], x, self.ymarks[-1])
        line.setPen(StyleCache.getPen(self.thick_line_width, GRID_COLOUR))
        line.setZValue(10)
        self.scene().addItem(line)

    def grid_tile(self,
        row,
        col,
        cspan=1,
        rspan=1,
        grid_cell=False,
        **kargs
    ):
        """Add a basic tile to the grid, checking coordinates and
        converting row + col to x + y point-coordinates for the
        <Tile> constructor.
        """
        # Check bounds
        if (
            row < 0
            or col < 0
            or (row + rspan) >= len(self.ymarks)
            or (col + cspan) >= len(self.xmarks)
        ):
#TODO
            raise GridError(
                _TILE_OUT_OF_BOUNDS.format(row=row, col=col, cspan=cspan, rspan=rspan)
            )

        x = self.xmarks[col]
        y = self.ymarks[row]
        w = self.xmarks[col + cspan] - x
        h = self.ymarks[row + rspan] - y
        t = Tile(x, y, w, h, **kargs)
        if grid_cell:
            if rspan == 1 and cspan == 1:
                t.gridrc = (row, col)
            else:
#TODO
                raise GridError("Raster-Kachel in Zeile {row}, Spalte {col} darf nicht andere Zellen überdecken".format(row=row, col=col))

        self.scene().addItem(t)
        return t

    def get_cell(self, cellrc):
        return self.rows[cellrc[0]][cellrc[1]]

#TODO
    def tile_right_clicked(self, tile):
        try:
            cmen = tile.get_property("CONTEXT_MENU")
        except KeyError:
            print("NO CONTEXT MENU")
            return True
        print("CONTEXT MENU:", cmen)
        return True

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
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
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
        scene = self.scene()
        if (self.grid_width < pdf_wpx) and (self.grid_height < pdf_hpx):
            # If both dimensions are smaller than the pdf area, expand the
            # scene rectangle to avoid the table being enlarged.
            scene.setSceneRect(0, 0, pdf_wpx, pdf_hpx)
            scene.render(painter)
            # print("SR1:", scene.sceneRect())
            scene.setSceneRect(self._sceneRect)
            # print("SR2:", scene.sceneRect())
        else:
            # print("SRX:", pdf_wpx, pdf_hpx)
            scene.render(painter)
            # print("SR:", scene.sceneRect())
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


class GridViewAuto(GridView):
    """An QGraphicsView that automatically adjusts the scaling of its
    scene to fill the viewing window, up to max. scale factor 1.
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
            try:
                qrect = self._sceneRect
            except AttributeError:
                return  # The view hasn't been initialized yet
        size = self.viewport().size()
        w = size.width()
        scale = w / qrect.width()
        h = size.height()
        scale1 = h / qrect.height()
        if scale1 < scale:
            if scale1 > 1:
                scale = 1
            else:
                scale = scale1
        elif scale > 1:
            scale = 1
        t = QTransform().scale(scale, scale)
        self.setTransform(t)


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
    would become too small, only '###' is displayed.
    Both cell and text can be styled to a limited extent.
    """

    def __init__(self, x, y, w, h, text="", **style):
        self.__properties = {}
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
            "border": GRID_COLOUR,
        }
        self.style.update(style)
        self.halign = self.style["halign"]
        self.valign = self.style["valign"]
        self.rotated = self.style["rotate"]
        bg = self.style["bg"]
        if bg:
            self.set_background(bg)
        # Text
        self.textItem = QGraphicsSimpleTextItem(self)
        font = self.style["font"]
        if font:
            self.textItem.setFont(font)
        else:
            self.textItem.setFont(StyleCache.getFont())
        self.set_text(text)
        self.set_textcolour(self.style["fg"])
        # Border
        pen0 = StyleCache.getPen(grid.border_width, self.style["border"])
        self.setPen(pen0)

    def on_left_click(self):
        try:
            editor = self.__properties["EDITOR"]
        except KeyError:
            return None
        view = self.scene().views()[0]
        point = view.screen_coordinates(self.scenePos())
        if editor(point, self.__properties):
            self.set_text(None)
            # Return the data needed for handling changes to this cell
            return self.__properties.get("CHANGED")
        return None

    def on_context_menu(self):
        try:
            handler = self.__properties["CONTEXT_MENU"]
        except KeyError:
            return
        view = self.scene().views()[0]
        point = view.screen_coordinates(self.scenePos())
        handler(point, self.__properties)

    def set_property(self, key, value):
        self.__properties[key] = value

    def get_property(self, key):
        try:
            return self.__properties[key]
        except KeyError:
            raise KeyError(f"TILE_NO_PROPERTY: {key}")

    def set_background(self, colour):
        self.setBrush(StyleCache.getBrush(colour))

    def set_textcolour(self, colour):
        self.textItem.setBrush(StyleCache.getBrush(colour))

    def set_halign(self, halign):
        self.halign = halign
        self.set_text(None)

    def set_valign(self, valign):
        self.valign = valign
        self.set_text(None)

    def set_verticaltext(self, rot90=True):
        self.rotated = rot90
        self.set_text(None)

    def set_text(self, text):
        if text is None:
            text = self.__properties["TEXT"]
        elif type(text) == str:
            self.__properties["TEXT"] = text
        else:
#TODO
            raise GridError(_NOTSTRING.format(val=repr(text)))
        self.textItem.setText(text)
        self.textItem.setScale(1)
        tbr = self.textItem.boundingRect()
        w = tbr.width()
        h = tbr.height()
        margin = h / 5
        scale = 1
        yshift = 0
        if text:
            maxw = self.width0 - margin * 2
            maxh = self.height0 - margin * 2
            if self.rotated:
                if w > maxh:
                    scale = maxh / w
                if h > maxw:
                    _scale = maxw / h
                    if _scale < scale:
                        scale = _scale
                if scale < 0.6:
                    self.textItem.setText("###")
                    tbr = self.textItem.boundingRect()
                    w = tbr.width()
                    h = tbr.height()
                    scale = maxh / w
                if scale < 1:
                    self.textItem.setScale(scale)
                self.textItem.setRotation(-90)
                __h = h
                h = w * scale
                w = __h * scale
                yshift = h
            else:
                if w > maxw:
                    scale = maxw / w
                if h > maxh:
                    _scale = maxh / h
                    if _scale < scale:
                        scale = _scale
                if scale < 0.6:
                    self.textItem.setText("###")
                    tbr = self.textItem.boundingRect()
                    w = tbr.width()
                    h = tbr.height()
                    scale = maxw / w
                if scale < 1:
                    self.textItem.setScale(scale)
                h = h * scale
                w = w * scale
        if self.halign == "l":
            xshift = margin
        elif self.halign == "r":
            xshift = self.width0 - margin - w
        else:
            xshift = (self.width0 - w) / 2
        if self.valign == "t":
            yshift += margin
        elif self.valign == "b":
            yshift += self.height0 - margin - h
        else:
            yshift += self.height0 - (self.height0 + h) / 2
        self.textItem.setPos(xshift, yshift)


#################################################
### The pop-up editors

#TODO
class CellEditorTable(QDialog):
    def __init__(self, items, ncols=None):
        coln = ncols or 1
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        vbox = QVBoxLayout(self)
        self.table = QTableWidget(self)
        vbox.addWidget(self.table)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()
        self.table.itemActivated.connect(self._select)
        self.table.itemClicked.connect(self._select)
        # Enter the data
        nrows = (len(items) + 2) // coln
        self.table.setColumnCount(coln)
        self.table.setRowCount(nrows)
        i = 0
        for row in range(nrows):
            for col in range(coln):
                try:
                    text = items[i]
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignHCenter)
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    item._text = text
                except IndexError:
                    item = QTableWidgetItem('')
                    item.setBackground(StyleCache.getBrush(''))
                    item.setFlags(Qt.NoItemFlags)
                    item._text = None
                self.table.setItem(row, col, item)
                i += 1
        # This is all about fitting to contents, first the table,
        # then the window
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        h = 0
        for r in range(nrows):
            h += self.table.rowHeight(r)
        w = 0
        for c in range(coln):
            w += self.table.columnWidth(c)
        _cm = self.table.contentsMargins()
        h += _cm.top() + _cm.bottom()
        w += _cm.left() + _cm.right()
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setFixedSize(w, h)
        self.resize(0, 0)

    def _select(self, item):
        if item._text != None:
            self._value = item._text
            self.accept()

    def activate(self, pos, properties):
#        self.setWindowTitle(tile.tag)
        self.move(pos)
        text0 = properties["TEXT"]
        if self.exec():
            if self._value != text0:
                properties["TEXT"] = self._value
                return True
        return False

#TODO
class CellEditorDate(QDialog):
    def __init__(self, grid):
        self._grid = grid
        super().__init__()
        vbox = QVBoxLayout(self)
        self.cal = QCalendarWidget(self)
        self.cal.setGridVisible(True)
        self.cal.clicked[QDate].connect(self.newDate)
        vbox.addWidget(self.cal)
        self.lbl = QLabel(self)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok
                | QDialogButtonBox.Cancel | QDialogButtonBox.Reset)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        buttonBox.button(QDialogButtonBox.Reset).clicked.connect(self.reset)
        vbox.addWidget(self.lbl)
        vbox.addWidget(buttonBox)
        self.setLayout(vbox)

    def reset(self):
        self.date = ''
        self.accept()

    def activate(self, tile, x, y):
#        self.setWindowTitle(tile.tag)
        # Set date
        tile = tile
        date = tile.value()
        self.cal.setSelectedDate(QDate.fromString(date, 'yyyy-MM-dd')
                if date else QDate.currentDate())
        self.newDate(self.cal.selectedDate())
        self.move(self._grid.screen_coordinates(x, y))
        if self.exec_():
            tile.set_text(self.date)
            self._grid.value_changed(tile, self.date)

    def newDate(self, date):
        self.lbl.setText(QLocale().toString(date))
        self.date = date.toString('yyyy-MM-dd')

#TODO
class CellEditorText(QDialog):
    def __init__(self, grid):
        self._grid = grid
        super().__init__()
        vbox = QVBoxLayout(self)
        self.textedit = QTextEdit(self)
        self.textedit.setTabChangesFocus(True)
        vbox.addWidget(self.textedit)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok
                | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        vbox.addWidget(buttonBox)

    def activate(self, tile, x, y):
#        self.setWindowTitle(tile.tag)
        text = tile.value()
        self.textedit.setPlainText(text)
        self.move(self._grid.screen_coordinates(x, y))
        if self.exec_():
            text = self.textedit.toPlainText()
            if text:
                text = '\n'.join([l.rstrip() for l in text.splitlines()])
            self._grid.value_changed(tile, text)


class CellEditorLine(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        vbox = QVBoxLayout(self)
        self.lineedit = QLineEdit(self)
        vbox.addWidget(self.lineedit)
        self.lineedit.returnPressed.connect(self.accept)

    def activate(self, pos, properties):
#        self.setWindowTitle(tile.tag)
        text0 = properties["TEXT"]
        self.lineedit.setText(text0)
        self.move(pos)
        if self.exec():
            text = self.lineedit.text()
            if text != text0:
                properties["TEXT"] = text
                return True
        return False

#TODO
class CellEditorList(QDialog):
    def __init__(self, items, display_items=None):
        super().__init__()
        self.__items = items
        self.__display_items = display_items
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        vbox = QVBoxLayout(self)
        self.listbox = QListWidget(self)
#TODO
#        self.setFixedWidth(60)
        if display_items:
            self.listbox.addItems(display_items)
        else:
            self.listbox.addItems(items)
#Width?
        vbox.addWidget(self.listbox)
        self.listbox.itemClicked.connect(self.accept)

    def activate(self, pos, properties):
#        self.setWindowTitle(tile.tag)
        text0 = properties["TEXT"]
        try:
            i = self.__items.index(text0)
        except ValueError:
            pass
        else:
            self.listbox.setCurrentRow(i)
        self.move(pos)
        if self.exec():
#TODO: especially for the case when display items are used
            i = self.listbox.currentRow()
            text = self.__items[i]
            if text != text0:
                properties["TEXT"] = text
                return True
        return False


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    rows = (100, 30, 30, 30, 30, 30, 30, 30)
    cols = (200, 50, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 40, 40, 40)

    from qtpy.QtWidgets import QApplication

    app = QApplication([])
    #grid = GridViewRescaling()
    #grid = GridViewHFit() # buggy ...
    #grid = GridView()
    grid = GridViewAuto()
    titleheight = 25
    grid.init(rows, cols, titleheight)

    grid.grid_line_thick_v(2)
    grid.grid_line_thick_h(1)

    cell0 = grid.get_cell((0, 0))
    cell0.set_text("Not rotated")
    cell0.set_valign('m')
    cell1 = grid.get_cell((0, 2))
    cell1.set_text('Deutsch')
    cell1.set_verticaltext()
    cell1.set_valign('b')
    cell2 = grid.get_cell((0, 4))
    cell2.set_text("English")
    cell2.set_verticaltext()

    cell_1 = grid.grid_tile(4, 3, text="A long entry")
    grid.grid_tile(2, 0, text="left", halign='l')
    grid.grid_tile(3, 0, text="right", halign='r')
    grid.grid_tile(4, 0, text="top", valign='t', cspan=2, bg= "ffffaa")
    grid.grid_tile(5, 0, text="bottom", valign='b')

    if titleheight > 0:
        title = grid.add_title("Centre Title")
        title_l = grid.add_title("Left Title", halign="l")
        title_r = grid.add_title("Right Title", halign="r")

#TODO:
    plain_line_editor = CellEditorLine().activate
    cell0.set_property("EDITOR", plain_line_editor)
#    grade_editor = CellEditorList(
    grade_editor = CellEditorTable(
        (   "1+", "1", "1-",
            "2+", "2", "2-",
            "3+", "3", "3-",
            "4+", "4", "4-",
            "5+", "5", "5-",
            "6", "nt", "nb",
            "*", "/", ""
        ), 3
    ).activate
    cell_1.set_property("EDITOR", grade_editor)

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
