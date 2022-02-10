# -*- coding: utf-8 -*-
"""
ui/colourgrid.py

Last updated:  2022-02-0

Widget with tiles on grid layout (QGraphicsScene/QGraphicsView).
Used to display a grid of distinct colours – preferring light colours.

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
be rendered symetrically around the mathematical defined points, while
rendering with a pen with an odd number of pixels, the spare pixel will
be rendered to the right and below the mathematical point.
"
"""

##### Configuration #####################
# ?
FONT_DEFAULT = "Droid Sans"
FONT_SIZE_DEFAULT = 12
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
    QDialog,
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

    def tile_left_clicked(self, tile):
        print("LEFT CLICK:", tile.tag or "–––")
        return True

    def tile_right_clicked(self, tile):
        print("CONTEXT MENU:", tile.tag or "–––")
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

    def __init__(self, grid, x, y, w, h, text="", tag="", **style):
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
        return self._grid.pt2px(1.5)

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
        return self._grid.tile_left_clicked(self)

    def contextmenu(self):
        return self._grid.tile_right_clicked(self)

#################################################
### The pop-up editors

def PopupTable(grid, items, ncols = 3):
    if items:
        return _PopupTable(grid, items, ncols)
    return None


class _PopupTable(QDialog):
#TODO: Note the change: '' is no longer included automatically!!!
    def __init__(self, grid, items, ncols):
        self._grid = grid
        super().__init__()
        vbox = QVBoxLayout(self)
        self.table = QTableWidget(self)
        vbox.addWidget(self.table)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()
        self.table.itemActivated.connect(self._select)
        self.table.itemClicked.connect(self._select)
        # Enter the data
        nrows = (len(items) + 2) // ncols
        self.table.setColumnCount(ncols)
        self.table.setRowCount(nrows)
        i = 0
        for row in range(nrows):
            for col in range(ncols):
                try:
                    text = items[i]
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignHCenter)
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    item._text = text
                except IndexError:
                    item = QTableWidgetItem('')
                    item.setBackground(CellStyle.getBrush(NO_ITEM))
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
        for c in range(ncols):
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

    def activate(self, tile, x, y):
        self.setWindowTitle(tile.tag)
        # x and y are scene coordinates.
        self.move(self._grid.screen_coordinates(x, y))
        if self.exec_():
            self._grid.value_changed(tile, self._value)


class PopupDate(QDialog):
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
        self.setWindowTitle(tile.tag)
        # Set date
        tile = tile
        date = tile.value()
        self.cal.setSelectedDate(QDate.fromString(date, 'yyyy-MM-dd')
                if date else QDate.currentDate())
        self.newDate(self.cal.selectedDate())
        self.move(self._grid.screen_coordinates(x, y))
        if self.exec_():
            tile.setText(self.date)
            self._grid.value_changed(tile, self.date)

    def newDate(self, date):
        self.lbl.setText(QLocale().toString(date))
        self.date = date.toString('yyyy-MM-dd')


class PopupTextEdit(QDialog):
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
        self.setWindowTitle(tile.tag)
        text = tile.value()
        self.textedit.setPlainText(text)
        self.move(self._grid.screen_coordinates(x, y))
        if self.exec_():
            text = self.textedit.toPlainText()
            if text:
                text = '\n'.join([l.rstrip() for l in text.splitlines()])
            self._grid.value_changed(tile, text)


class PopupLineEdit(QDialog):
    def __init__(self, grid):
        self._grid = grid
        super().__init__()
        vbox = QVBoxLayout(self)
        self.lineedit = QLineEdit(self)
        vbox.addWidget(self.lineedit)
        self.lineedit.returnPressed.connect(self.accept)

    def activate(self, tile, x, y):
        self.setWindowTitle(tile.tag)
        w = tile.width0
        if w < 50.0:
            w = 50.0
        self.lineedit.setFixedWidth(w)
        self.lineedit.setText(tile.value() or '')
        self.move(self._grid.screen_coordinates(x, y))
        if self.exec_():
            self._grid.value_changed(tile, self.lineedit.text())

#################################################

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


import colorsys

def HSVToRGB(h, s, v):
    (r, g, b) = colorsys.hsv_to_rgb(h, s, v)
    return f"{int(255*r):02x}{int(255*g):02x}{int(255*b):02x}"

def getDistinctColors(c, r):
    huePartition = 1.0 / c
    satPartition = 7 / 8 / r
    clist = []
    for hue in range(c):
        rlist = []
        clist.append(rlist)
        h = huePartition * hue
        for sat in range(r):
            s = satPartition * sat + 1/8
            rlist.append(HSVToRGB(h, s, 1.0))
    return clist


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    app = QApplication([])
    import sys, os
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)

    with open(os.path.join(basedir, "wz-data", "COLOURS")) as fh:
        lines = fh.read().split()
    colours = []
    for l in lines:
        c = l.lstrip('#')
        if c:
            colours.append(c)
    grid0 = GridViewRescaling()
    #grid0 = GridView()
    titleheight = 25
    cols = (50,)*10
    rows = (50,)*((len(colours)+9) // 10)
    grid0.init(rows, cols, titleheight)
    grid0.add_title("Colour Palette 1")
    for r in range(len(rows)):
        for c in range(10):
            try:
                colour = colours.pop()
            except IndexError:
                colour = ""
            grid0.basic_tile(r, c, bg=colour, text=colour)

    grid0.resize(800, 600)
    grid0.show()

    huex = (0, 16, 32, 48, 64, 88, 112, 134, 144, 160, 176, 192, 208, 230)
    satx = (0.2, 0.3, 0.4, 0.5, 0.7)
    cols = (50,)*len(huex)
    rows = (50,)*len(satx)

    grid = GridViewRescaling()
    #grid = GridView()
    titleheight = 25
    grid.init(rows, cols, titleheight)
    grid.add_title("Colour Palette 2")
    cn = len(huex)
    rn = len(satx)
#    clist = getDistinctColors(cn, rn)
    for c in range(cn):
        hue = huex[c]/256
        for r in range(rn):
            sat = satx[r]
            colour = HSVToRGB(hue, sat, 1.0)
            grid.basic_tile(r, c, bg=colour, text=colour)

    grid.resize(800, 600)
    grid.show()
    app.exec()
