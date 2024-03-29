"""
ui/grid_base.py

Last updated:  2023-01-22

Base functions for table-grids using the QGraphicsView framework.

=+LICENCE=============================
Copyright 2023 Michael Towers

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
# FONT_DEFAULT = "Droid Sans"
FONT_DEFAULT = ""   # use system default
FONT_COLOUR = "442222"  # rrggbb

#####################################################

if __name__ == "__main__":
    import sys, os

    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)

    import core.base
#    from core.base import start
#    start.setup(os.path.join(basedir, "DATA-2023"))
#    start.setup(os.path.join(basedir, "TESTDATA"))

T = TRANSLATIONS("ui.grid_base")

### +++++

from tables.table_utilities import (
    TSV2Table,
    Table2TSV,
    ToRectangle,
    TableParser,
    PasteFit,
)
from ui.ui_base import (
    ## QtWidgets
    QApplication,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItemGroup,
    QGraphicsRectItem,
    QGraphicsSimpleTextItem,
    QGraphicsLineItem,
    QMenu,
    ## QtGui
    QFont,
    QPen,
    QColor,
    QBrush,
    QTransform,
    QPainter,
    QPdfWriter,
    QPageLayout,
    QPageSize,
    QKeySequence,
    QIcon,
    QAction,    # in QtWidgets in Qt5
    ## QtCore
    Qt,
    QMarginsF,
    QRectF,
    QPointF,
)

### -----

class StyleCache:
    """Manage allocation of style resources using caches."""

    __fonts = {}  # cache for QFont items
    __brushes = {}  # cache for QBrush items
    __pens = {}  # cache for QPen items

    @classmethod
    def getPen(cls, width: int, colour: str = "") -> QPen:
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
                return cls.__pens["*"]
            except KeyError:
                pen = QPen()
                pen.setStyle(Qt.NoPen)
                cls.__pens["*"] = pen
                return pen

    @classmethod
    def getBrush(cls, colour: str = "") -> QBrush:
        """Manage a cache for brushes of different colour.
        <colour> is a colour in the form 'RRGGBB'.
        """
        try:
            return cls.__brushes[colour or "*"]
        except KeyError:
            pass
        if colour:
            brush = QBrush(QColor("#FF" + colour))
            cls.__brushes[colour] = brush
        else:
            brush = QBrush()  # no fill
            cls.__brushes["*"] = brush
        return brush

    @classmethod
    def getFont(
        cls,
        fontFamily: str = FONT_DEFAULT,
        fontSize: int = FONT_SIZE_DEFAULT,
        fontBold: bool = False,
        fontItalic: bool = False,
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
    """A rectangle covering one or more cells."""

    def __init__(self, grid, parent=None):
        super().__init__(parent=parent)
        self.xmarks = grid.xmarks
        self.ymarks = grid.ymarks
        self.setPen(StyleCache.getPen(grid.pt2px(SELECT_WIDTH), SELECT_COLOUR))
        self.setZValue(20)
        grid.scene().addItem(self)
        self.clear()

    def on_context_menu(self):
        """Return false value to indicate that the selection context menu
        should be shown.
        This method will only be called when the selection is active
        (shown) and at the top of the item stack at the cursor position.
        """
        return False

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
        """Test whether a start cell is pending (or already set)."""
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
        # print("§§§§§1", self.ldpi)
        # print("§§§§§2", self.physicalDpiX())

        ## Add a context menu for the selection
        # Copy
        copyAct = QAction(parent=self)
        keyseq = QKeySequence(QKeySequence.StandardKey.Copy)
        copyAct.setText(T["Copy"])
        copyAct.setIcon(QIcon.fromTheme("copy"))
        copyAct.setShortcut(keyseq)
        copyAct.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)
        copyAct.triggered.connect(self.copysel)
        self.addAction(copyAct)
        # Paste
        pasteAct = QAction(parent=self)
        keyseq = QKeySequence(QKeySequence.StandardKey.Paste)
        pasteAct.setText(T["Paste"])
        pasteAct.setIcon(QIcon.fromTheme("paste"))
        pasteAct.setShortcut(keyseq)
        pasteAct.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)
        pasteAct.triggered.connect(self.pastesel)
        self.addAction(pasteAct)
        # Make menu for showing actions
        self.action_menu = QMenu()
        self.action_menu.addActions(self.actions())

    def pt2px(self, pt) -> int:
        px = int(self.ldpi * pt / 72.0 + 0.5)
        # print(f"pt2px: {pt} -> {px}")
        return px

    def px2mm(self, px):
        return px * 25.4 / self.ldpi

    def screen_coordinates(self, scene_pointf):
        """Return the screen coordinates of the given scene point."""
        viewp = self.mapFromScene(scene_pointf)
        return self.mapToGlobal(viewp)

#TODO???
#    def keyPressEvent(self, event):
#        print(f"%%% <{event.text()} | {event.key()}> %%%")
#        #event.ignore()
#        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        # Qt5
        #        print("POS:", event.pos())
        #        print("GLOBALPOS:", event.globalPos())
        #        print("SCREENPOS:", event.screenPos())
        #        print("WINDOWPOS:", event.windowPos())

        # Qt6
        #        print("POS:", event.position())
        #        print("GLOBALPOS:", event.globalPosition())
        #        print("SCENEPOS:", event.scenePosition())

        try:
            point = event.position().toPoint()  # Qt6
        except:
            point = event.pos()  # Qt5
        # print("§§????????", point)
        self.point0 = point
        if event.button() != Qt.LeftButton:
            return
        self.select.clear()
        #        self.end_cell = None
        # print("POS:", point, self.mapToGlobal(point), self.itemAt(point))
        # The sought <Tile> may not be the top item.
        items = self.items(point)
        if items and event.button() == Qt.LeftButton:
            # Only a grid cell is "selectable"
            for item in items:
                try:
                    self.select.set_pending(item.get_property("ROW_COL"))
                    break  # only take account of the first grid cell
                except (AttributeError, KeyError):
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
                coords = item.get_property("ROW_COL")
            except (AttributeError, KeyError):
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
            # print("§?§?§?§?§ SELECT ACTIVE:", self.select.range())
            return
        items = self.items(point)
        if items:
            for item in items:
                # Find the topmost <Tile> which responds to a click
                try:
                    click_handler = item.on_left_click
                except AttributeError:
                    continue
#                point = self.screen_coordinates(item.scenePos())
                value = click_handler()
                if value is not None:
                    self.cell_modified(value)
                break

    def contextMenuEvent(self, event):
        try:
            pointf = event.position()  # Qt6
            point = pointf.toPoint()
        except:
            point = event.pos()  # Qt5
            pointf = QPointF(point)
        items = self.items(point)
        clear = True
        if items:
            for item in items:
                # Find the topmost <Tile> which responds to the event
                # Under normal circumstances this should be the
                # selection, if this is active.
                try:
                    click_handler = item.on_context_menu
                except AttributeError:
                    continue
                clear = click_handler()
                if (not clear) and self.select.is_active():
                    # show context menu
                    self.action_menu.exec(self.mapToGlobal(point))
                break
        if clear:
            self.select.clear()

    def cell_modified(self, row_col):
        print("CELL MODIFIED:", row_col)

    ### View scaling
    def rescale(self):
        self._scale = 1.0
        self.scale(0)

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

    def init(self, rowheights, columnwidths, suppress_grid=False):
        """Set the grid size.
            <columnwidths>: a list of column widths (points)
            <rowheights>: a list of row heights (points)
        Rows and columns are 0-indexed.
        The widths/heights include grid lines and other bounding boxes.
        """
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
        y = 0
        self.ymarks = [y]
        ypt = 0
        for r in rowheights:
            ypt += r
            r = self.pt2px(r)
            y += r
            self.ymarks.append(y)
        self.grid_height = y
        self.grid_xpt, self.grid_ypt = (xpt, ypt)

        # Construct grid
        if suppress_grid:
            #?
            self.rows = None
            self.grid_group = None
        else:
            row_list = []
            self.rows = row_list
            self.grid_group = QGraphicsItemGroup()
            scene.addItem(self.grid_group)
            for rx in range(len(rowheights)):
                row = []
                for cx in range(len(columnwidths)):
                    gtile = self.grid_tile(
                        rx, cx,
                        border=GRID_COLOUR,
                        border_width=self.border_width,
                        grid_cell=True
                    )
                    row.append(gtile)
                    self.grid_group.addToGroup(gtile)
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

    def copysel(self):
        if self.select.is_active():
            self.do_copy(*self.select.range())
        else:
            SHOW_WARNING(T["COPY_NO_SELECTION"])

    def pastesel(self):
        if self.select.is_active():
            self.do_paste(*self.select.range())
        else:
            SHOW_WARNING(T["PASTE_NO_SELECTION"])

    def do_copy(self, row, col, nrows, ncols):
        """Copy the values of the selected cells (only the grid cells!)
        to the clipboard formatted as tab-separated-value.
        """
        rlist = [
            [
                self.get_cell((row + r, col + c)).get_property("VALUE")
                for c in range(ncols)
            ]
            for r in range(nrows)
        ]
        qapp = QApplication.instance()
        qapp.clipboard().setText(Table2TSV(rlist))

    def do_paste(self, row, col, nrows, ncols):
        """Paste the clipboard to the selected grid cells.
        The clipboard will be interpreted as a table.
        See <PasteFit> for details on dimension compatibility.
        """
        qapp = QApplication.instance()
        clipboard = qapp.clipboard()
        mimeData = clipboard.mimeData()
        if mimeData.hasHtml():
            table_data = TableParser(mimeData.html())
        elif mimeData.hasText():
            table_data = TSV2Table(mimeData.text())
        else:
            return
        if (n := ToRectangle(table_data)) > 0:
            SHOW_WARNING(T["PASTE_NOT_RECTANGULAR"].format(n=n))
        if PasteFit(table_data, nrows, ncols):
            for vals in table_data:
                self.write_to_row(row, col, vals)
                row += 1
        else:
            SHOW_ERROR(
                T["BAD_PASTE_RANGE"].format(
                    h0=len(table_data),
                    w0=len(table_data[0]),
                    h1=nrows,
                    w1=ncols
                )
            )

    def write_to_row(self, row, col, values):
        """Write a list of values to a position (<col>) in a given row.
        Override this if special behaviour, e.g. value-checking, is
        required.
        """
        for v in values:
            self.get_cell((row, col)).set_text(v)
            col += 1

    def grid_line_thick_h(self, row):
        return self.grid_line_h(row, self.thick_line_width)

    def grid_line_h(self, row, width=None, colour=GRID_COLOUR):
        # If supplied, width is in pixels
        try:
            y = self.ymarks[row]
        except KeyError:
            raise ValueError(T["BAD_ROW_LINE"].format(row=row))
        return self.line_h(y, width, colour)

    def line_h(self, y, width, colour):
        line = QGraphicsLineItem(self.xmarks[0], y, self.xmarks[-1], y)
        line.setPen(StyleCache.getPen(width or self.border_width, GRID_COLOUR))
        line.setZValue(10)
        self.scene().addItem(line)
        return line

    def grid_line_thick_v(self, col):
        return self.grid_line_v(col, self.thick_line_width)

    def grid_line_v(self, col, width=None, colour=GRID_COLOUR):
        # If supplied, width is in pixels
        try:
            x = self.xmarks[col]
        except KeyError:
            raise ValueError(T["BAD_COL_LINE"].format(col=col))
        line = QGraphicsLineItem(x, self.ymarks[0], x, self.ymarks[-1])
        line.setPen(StyleCache.getPen(width or self.border_width, GRID_COLOUR))
        line.setZValue(10)
        self.scene().addItem(line)
        return line

    def grid_tile(self, row, col, cspan=1, rspan=1, grid_cell=False, **kargs):
        """Add a basic tile to the grid, checking coordinates and
        converting row + col to x + y point-coordinates for the
        <Tile> constructor.
        """
        # Allow negative spans (= cells from left/bottom)
        if cspan < 0:
            span = len(self.xmarks) + cspan - col
            if span < 0:
                raise ValueError(
                    T["TILE_OUT_OF_BOUNDS"].format(
                        row=row, col=col, cspan=cspan, rspan=rspan
                    )
                )
            cspan = span or 1
        if rspan < 0:
            span = len(self.ymarks) + rspan - row
            if span < 0:
                raise ValueError(
                    T["TILE_OUT_OF_BOUNDS"].format(
                        row=row, col=col, cspan=cspan, rspan=rspan
                    )
                )
            rspan = span or 1
        # Check bounds
        if (
            row < 0
            or col < 0
            or (row + rspan) >= len(self.ymarks)
            or (col + cspan) >= len(self.xmarks)
        ):
            raise ValueError(
                T["TILE_OUT_OF_BOUNDS"].format(
                    row=row, col=col, cspan=cspan, rspan=rspan
                )
            )
        x = self.xmarks[col]
        y = self.ymarks[row]
        w = self.xmarks[col + cspan] - x
        h = self.ymarks[row + rspan] - y
        t = Tile(x, y, w, h, **kargs)
        if grid_cell:
            if rspan == 1 and cspan == 1:
                t.set_property("ROW_COL", (row, col))
            else:
                raise ValueError(T["GRID_CELL_RANGE"].format(row=row, col=col))
        self.scene().addItem(t)
        return t

    def get_cell(self, cellrc):
        return self.rows[cellrc[0]][cellrc[1]]

    ### pdf output

    def set_title(self, text, offset=0, halign="c", font_scale=None):
        """Place a text item above or below the grid area.
        Thus it may not be (fully) visible in the viewport.
        It is actually intended only for adding headers and footnotes
        to pdf exports.
        """
        if offset > 0:
            offset += self.grid_height
        textItem = QGraphicsSimpleTextItem(text)
        self.scene().addItem(textItem)
        font = QFont(StyleCache.getFont())
        if font_scale:
            font.setPointSizeF(font.pointSizeF() * font_scale)
        font.setBold(True)
        textItem.setFont(font)
        bdrect = textItem.mapRectToParent(textItem.boundingRect())
        w = bdrect.width()
        h = bdrect.height()
        margin = self.pt2px(TITLE_MARGIN)
        if halign == "l":
            x = margin
        elif halign == "r":
            x = self.grid_width - margin - w
        else:
            x = (self.grid_width - w) / 2
        textItem.setPos(x, offset - h/2)
        return textItem

    def delete_item(self, item):
        self.scene().removeItem(item)

    def setPdfMargins(self, left=50, top=30, right=30, bottom=30):
        self._pdfmargins = (left, top, right, bottom)
        return self._pdfmargins

    def pdfMargins(self):
        try:
            return self._pdfmargins
        except AttributeError:
            return self.setPdfMargins()

    def to_pdf(self, filepath, landscape=False, can_rotate=True,
        titleheight=0, footerheight=0
    ):
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

        h0 = self.pt2px(titleheight)
        h1 = self.pt2px(footerheight)
        scene_height = h0 + self.grid_height + h1

        # Prepare the scene for printing – check size
        if self.grid_width > scene_height:
            if (not landscape) and (self.grid_width > pdf_wpx) and can_rotate:
                # The table is wider than the pdf area, so it would
                # benefit from rotating
                landscape = True
        elif self.grid_width < scene_height:
            if landscape and (scene_height > pdf_hpx) and can_rotate:
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
        if (self.grid_width < pdf_wpx) and (scene_height < pdf_hpx):
            # If both dimensions are smaller than the pdf area, expand the
            # scene rectangle to avoid the table being enlarged.
            scene.setSceneRect(0, -h0, pdf_wpx, pdf_hpx)
        else:
            # Otherwise just add title and footer space
            scene.setSceneRect(0, -h0, self.grid_width, scene_height)
        scene.render(painter)
        # print("SR1:", scene.sceneRect())
        scene.setSceneRect(self._sceneRect)
        # print("SR2:", scene.sceneRect())
        painter.end()
        return filepath

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
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def resizeEvent(self, event):
        self.rescale()
        return super().resizeEvent(event)

    def rescale(self, qrect=None):
        if qrect == None:
            try:
                qrect = self._sceneRect
            except AttributeError:
                return  # The view hasn't been initialized yet
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
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

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
            if scale1 > 1.0:
                scale = 1.0
            else:
                scale = scale1
        elif scale > 1:
            scale = 1
        t = QTransform().scale(scale, scale)
        self.setTransform(t)


# Experimental!
class GridViewHFit(GridView):
    """An QGraphicsView that automatically adjusts the scaling of its
    scene to fill the width of the viewing window, up to a scale factor
    of 1.
    """

    def __init__(self):
        super().__init__()
        # Apparently it is a good idea to disable scrollbars when using
        # this resizing scheme. With this resizing scheme they would not
        # appear anyway, so this doesn't lose any features!
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # To avoid problematic situation at point where scroll-bar would
        # appear or disappear, force scrollbar on permanently.
        # TODO: On systems where this has no effect, the resulting
        # widget might be unstable – this needs testing.
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

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
        ## vsb = self.verticalScrollBar()
        ## if vsb.isVisible():
        ##     w -= vsb.size().width()
        scale = w / qrect.width()
        if scale > 1.0:
            scale = 1.0
        t = QTransform().scale(scale, scale)
        self.setTransform(t)


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
            "border_width": 1,
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
        pen0 = StyleCache.getPen(
            self.style["border_width"], self.style["border"]
        )
        self.setPen(pen0)

    def on_left_click(self):
        try:
            editor = self.__properties["EDITOR"]
        except KeyError:
            return None
        view = self.scene().views()[0]
        point = view.screen_coordinates(self.scenePos())
        if editor.activate(point, self.__properties):
            self.set_text(None)
            # Return the data needed for handling changes to this cell
            return self.__properties
        return None

    def on_context_menu(self):
        """This method will only be called when this item is at the top
        of the item stack at the cursor position.
        Return true value to indicate that the selection should be
        cleared. If a false value is returned, the selection context
        menu will be shown, if the selection is active.
        """
        try:
            handler = self.__properties["CONTEXT_MENU"]
        except KeyError:
            return True
        view = self.scene().views()[0]
        point = view.screen_coordinates(self.scenePos())
        handler(point, self.__properties)
        return True

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

    def set_text(self, value):
        if type(value) == str:
            self.__properties["VALUE"] = value
        elif value is not None:
            raise ValueError(T["NOT_STRING"].format(val=repr(value)))
        try:
            delegate = self.__properties["DELEGATE"]
        except KeyError:
            text = self.__properties["VALUE"]
        else:
            text = delegate(self.__properties)
        self.textItem.setText(text)
        self.textItem.setScale(1)
        tbr = self.textItem.boundingRect()
        w = tbr.width()
        h = tbr.height()
        margin = self.__properties.get("MARGIN") or 3
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
                if self.__properties.get("NO_SCALE"):
                    scale = 1
                elif scale < 1:
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
                if self.__properties.get("NO_SCALE"):
                    scale = 1
                elif scale < 1:
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


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    QIcon.setFallbackSearchPaths([os.path.join(basedir, "wz-data", "icons")])

    from ui.cell_editors import (
        CellEditorDate,
        CellEditorTable,
        CellEditorLine,
        CellEditorText,
    )
    rows = (100,) + (30,) * 12
    cols = (200, 50,) + (25,) * 14 + (40,) * 3

    app = QApplication([])
    # grid = GridViewRescaling()
    # grid = GridViewHFit()
    # grid = GridView()
    grid = GridViewAuto()

    # no_grid = True
    no_grid = False
    grid.init(rows, cols, suppress_grid=no_grid)

    grid.grid_line_thick_v(2)
    grid.grid_line_thick_h(1)

    if not no_grid:
        for c in range(2, len(cols)):
            grid.get_cell((0, c)).set_verticaltext()
        cell0 = grid.get_cell((0, 0))
        cell0.set_text("Not rotated")
        cell0.set_valign("m")
        cell1 = grid.get_cell((0, 2))
        cell1.set_text("Deutsch")
        cell1.set_valign("b")
        cell2 = grid.get_cell((0, 4))
        cell2.set_text("English")

        cell_1 = grid.get_cell((4, 3))
        cell_1.set_text("A long entry")
        cell_pid = grid.grid_tile(2, 0, text="left", halign="l")

        plain_line_editor = CellEditorLine()
        cell0.set_property("EDITOR", plain_line_editor)
        grade_editor_I = CellEditorTable(
            [
                [   ["1+", "1", "1-"],   "sehr gut"      ],
                [   ["2+", "2", "2-"],   "gut"           ],
                [   ["3+", "3", "3-"],   "befriedigend"  ],
                [   ["4+", "4", "4-"],   "ausreichend"   ],
                [   ["5+", "5", "5-"],   "mangelhaft"    ],
                [   ["6"],         "ungenügend"    ],
                [   ["nt"],        "nicht teilgenommen"],
                [   ["t"],         "teilgenommen"  ],
            #    [   ["ne"],        "nicht erteilt" ],
                [   ["nb"],        "kann nicht beurteilt werden"],
                [   ["*", "/"],       "––––––"        ],
            ]
        )
        text_editor = CellEditorText()
        #    grade_editor = CellEditorList(
        #cell_1.set_property("EDITOR", grade_editor_I)
        cell_1.set_property("EDITOR", text_editor)

        cell3 = grid.get_cell((6, 0))
        cell3.set_property("EDITOR", CellEditorDate())
        cell3.set_property("VALUE", "")
        cell3.set_text("")
        cell4 = grid.get_cell((7, 0))
        cell4.set_property("EDITOR", CellEditorDate(empty_ok=True))
        cell4.set_property("VALUE", "2022-12-01")
        cell4.set_text("2022-12-01")

    grid.grid_tile(3, 0, text="right", halign="r")
    grid.grid_tile(4, 0, text="top", valign="t", cspan=2, bg="ffffaa")
    grid.grid_tile(5, 0, text="bottom", valign="b")

    grid.resize(600, 400)
    grid.show()

    print("ymarks:", grid.ymarks)

    ###### TITLES & FOOTNOTES
    if True:
        titleheight = grid.pt2px(30)
        footerheight = grid.pt2px(30)
        t1 = grid.set_title(
            "Main Title",
            offset=-titleheight // 2,
            font_scale=1.2,
            halign="c",
        )
        h1 = grid.set_title(
            "A footnote",
            offset=footerheight // 2,
            halign="r",
        )

        for yl in 0, -titleheight, grid.grid_height, grid.grid_height + footerheight:
            line = grid.line_h(yl, width=grid.thick_line_width, colour="ff0000")

        # grid.scene().removeItem(t1)
        # grid.scene().removeItem(h1)
    ###### ------

    # grid.grid_group.hide()

    def export_to_pdf(can_rotate):
        basedir = os.path.dirname(appdir)
        tmpdir = os.path.join(basedir, "tmp")
        fpath = os.path.join(tmpdir, "grid1.pdf")
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        grid.to_pdf(
            fpath,
            can_rotate=can_rotate,
            titleheight=titleheight,
            footerheight=footerheight
        )
        print(f"Exported to {fpath}")

    export_to_pdf(can_rotate=True)

    app.exec()
