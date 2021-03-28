# -*- coding: utf-8 -*-
"""
ui/gridbase.py

Last updated:  2021-03-28

Widget with editable tiles on grid layout (QGraphicsScene/QGraphicsView).

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

##### Configuration #####################
FONT_DEFAULT = 'Droid Sans'
FONT_SIZE_DEFAULT = 11
FONT_COLOUR = '442222'      # rrggbb
BORDER_COLOUR = '000088'    # rrggbb
MARK_COLOUR = 'E00000'      # rrggbb

# Line width for borders
UNDERLINE_WIDTH = 3.0
BORDER_WIDTH = 1.0

#####################

### Messages
_TILE_OUT_OF_BOUNDS = ("Kachel außerhalb Tabellenbereich:\n"
        " Zeile {row}, Höhe {rspan}, Spalte {col}, Breite {cspan}")
_NOTSTRING          = "In <grid::Tile>: Zeichenkette erwartet: {val}"

#####################################################

import sys, os, copy

from qtpy.QtWidgets import QLineEdit, QTextEdit, \
    QGraphicsView, QGraphicsScene, \
    QGraphicsRectItem, QGraphicsSimpleTextItem, QGraphicsLineItem, \
    QGraphicsProxyWidget, \
    QCalendarWidget, QVBoxLayout, QLabel, \
    QFileDialog, QDialog, QDialogButtonBox, \
    QTableWidget, QTableWidgetItem
from qtpy.QtGui import (QFont, QPen, QColor, QBrush, QTransform,
        QPainter, QPdfWriter, QPageLayout)
from qtpy.QtCore import QDate, Qt, QMarginsF, QRectF, QBuffer, QByteArray, \
        QLocale

class GridError(Exception):
    pass

###

class GridView(QGraphicsView):
    """This is the "view" widget for the grid.
    The actual grid is implemented as a "scene".
    """
    def __init__(self):
        self._scale = 1.0
        super ().__init__()
        # Change update mode: The default, MinimalViewportUpdate, seems
        # to cause artefacts to be left, i.e. it updates too little.
        #self.setViewportUpdateMode(self.SmartViewportUpdate)
        self.setViewportUpdateMode(self.BoundingRectViewportUpdate)
        self.ldpi = self.logicalDpiX()
        if self.logicalDpiY() != self.ldpi:
            REPORT('WARNING', "LOGICAL DPI different for x and y")
        self.MM2PT = self.ldpi / 25.4
#
    def set_scene(self, scene):
        """Set the QGraphicsScene for this view. The size will be fixed
        to that of the initial <sceneRect> (to prevent it from being
        altered by pop-ups).
        If <scene> is empty (<None>), the current scene will be removed
        if calling its method <leave_ok> returns a true value.
        The result is a <bool>, <True> if the operation was successfully
        completed.
        """
        s0 = self.scene()
#TODO: Looks like a bodge ...
        if s0:
            if not scene and not s0.leave_ok():
                return False
            s0.view(False)
        self.setScene(scene)
        if scene:
            # Set the view's scene area to a fixed size
            # (pop-ups could otherwise extend it)
            self.setSceneRect(scene._sceneRect)
            scene.view(True)
        return True
#
    def mousePressEvent(self, event):
        point = event.pos()
#        print("POS:", point, self.mapToGlobal(point), self.itemAt(point))
# The Tile may not be the top item.
        items = self.items(point)
        button = event.button()
        if items:
            for item in items:
                # Give all items at this point a chance to react, starting
                # with the topmost. An item can break the chain by
                # returning a false value.
                try:
                    if button == Qt.LeftButton:
                        if not item.leftclick():
                            return
                    elif button == Qt.RightButton:
                        if not item.rightclick():
                            return
                except AttributeError:
                    pass
#
    def set_changed(self, is_modified):
        """Called when there is a switch from "no changes" to "changes"
        or vice versa.
        """
        # Override this if something should happen!
        pass
#
    ### View scaling
    def scaleUp (self):
        self.scale(1)
#
    def scaleDn (self):
        self.scale(-1)
#
    def scale(self, delta):
        t = QTransform()
        self._scale += self._scale * delta / 10
        t.scale(self._scale, self._scale)
        self.setTransform(t)
    ### ---------------

###

class GridViewRescaling(GridView):
    """An QGraphicsView that automatically adjusts the scaling of its
    scene to fill the viewing window.
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

###

class GridBase(QGraphicsScene):
    def __init__(self, gview, rowheights, columnwidths):
        """Set the grid size.
            <columnwidths>: a list of column widths (mm)
            <rowheights>: a list of row heights (mm)
        Rows and columns are 0-indexed.
        """
        super().__init__()
        self._gview = gview
        self._styles = {'*': CellStyle(FONT_DEFAULT, FONT_SIZE_DEFAULT,
                align = 'c', border = 1, mark = MARK_COLOUR)
        }
        self.tagmap = {}        # {tag -> {Tile> instance}
        self.xmarks = [0.0]
        x = 0.0
        for c in columnwidths:
            x += c * self._gview.MM2PT
            self.xmarks.append(x)
        self.ymarks = [0.0]
        y = 0.0
        for r in rowheights:
            y += r * self._gview.MM2PT
            self.ymarks.append(y)
#TODO: Allow a little margin? e.g.
        self._sceneRect = QRectF(-1.0, -1.0, x + 1.0, y + 1.0)
# ... or not:
#        self._sceneRect = QRectF(0.0, 0.0, x, y)
#
#    def style(self, name):
#        return self._styles[name]
#
    def new_style(self, name, base = None, **params):
        if base:
            style0 = self._styles[base]
            self._styles[name] = style0.copy(**params)
        else:
            self._styles[name] = CellStyle(params.pop('font', None),
                    params.pop('size', None), **params)
#
    def view(self, activate):
        """Called when the scene is (de)activated in the view.
        Override this if something should happen ...
        """
        pass
#
    def leave_ok(self):
        return True
#
    def ncols(self):
        return len(self.xmarks) - 1
#
    def nrows(self):
        return len(self.ymarks) - 1
#
    def screen_coordinates(self, x, y):
        """Return the screen coordinates of the given scene point.
        """
        viewp = self._gview.mapFromScene(x, y)
        return self._gview.mapToGlobal(viewp)
#
    def tile(self, row, col, text = None, cspan = 1, rspan = 1,
            style = None, tag = None):
        """Add a tile to the grid.
        If <tag> is not set, it will be set to '#row:col'.
        """
        # Check bounds
        if (row < 0 or col < 0
                or (row + rspan) >= len(self.ymarks)
                or (col + cspan) >= len(self.xmarks)):
            raise GridError(_TILE_OUT_OF_BOUNDS.format(
                row = row, col = col, cspan = cspan, rspan = rspan))
        x = self.xmarks[col]
        y = self.ymarks[row]
        w = self.xmarks[col + cspan] - x
        h = self.ymarks[row + rspan] - y
        if not tag:
            tag = '#%d:%d' % (row, col)
        cell_style = self._styles[style or '*']
        t = Tile(self, tag, x, y, w, h, text, cell_style)
        self.addItem(t)
        self.tagmap[tag] = t
        self.value0[tag] = text # initial value
        return t
#
    def text(self, tag):
        """Read the contents of the cell with given tag.
        """
        return self.tagmap[tag].value() or ''
#
    def set_text(self, tag, text):
        """Set the text in the given cell.
        """
        self.tagmap[tag].setText(text)
#
    ### pdf output
    def setPdfMargins(self, left = 15, top = 15, right = 15, bottom = 15):
        self._pdfmargins = (left, top, right, bottom)
        return self._pdfmargins
#
    def pdfMargins(self):
        try:
            return self._pdfmargins
        except AttributeError:
            return self.setPdfMargins()
#
    def to_pdf(self, filename = None):
        """Produce and save a pdf of the table.
        <filename> is a suggestion for the save dialog.
        The output orientation is selected according to the aspect ratio
        of the table. If the table is too big for the page area, it will
        be shrunk to fit.
        """
        qbytes = QByteArray()
        qbuf = QBuffer(qbytes)
        qbuf.open(qbuf.WriteOnly)
        printer = QPdfWriter(qbuf)
        printer.setPageSize(printer.A4)
        printer.setPageMargins(QMarginsF(*self.pdfMargins()),
                QPageLayout.Millimeter)
        sceneRect = self._sceneRect
        sw = sceneRect.width()
        sh = sceneRect.height()
        if sw > sh:
            printer.setPageOrientation(QPageLayout.Orientation.Landscape)
        pdf_dpmm = printer.resolution() / 25.4 # pdf resolution, dots per mm
        scene_dpmm = self._gview.MM2PT      # scene resolution, dots per mm
        natural_scale = pdf_dpmm / scene_dpmm
        page_layout = printer.pageLayout()
        pdf_rect = page_layout.paintRect(QPageLayout.Millimeter)
        swmm = sw / self._gview.MM2PT
        shmm = sh / self._gview.MM2PT
        painter = QPainter(printer)
        pdf_wmm = pdf_rect.width()
        pdf_hmm = pdf_rect.height()
        if swmm > pdf_wmm or shmm > pdf_hmm:
            # Shrink to fit page
            self.render(painter)
        else:
            # Scale resolution to keep size
            pdf_rect.setWidth(sw * natural_scale)
            pdf_rect.setHeight(sh * natural_scale)
            self.render(painter, pdf_rect)
        painter.end()
        qbuf.close()
        # Write resulting file
#        QFileDialog.saveFileContent(qbytes, filename or 'grid.pdf')
        dir0 = self._savedir or os.path.expanduser('~')
        if filename:
            if not filename.endswith('.pdf'):
                filename += '.pdf'
        else:
            filename = 'grid.pdf'
        fpath = QFileDialog.getSaveFileName(self._gview, _FILESAVE,
                           os.path.join(dir0, filename), _PDF_FILE)[0]
        if fpath:
            self.set_savedir(os.path.dirname(fpath))
            with open(fpath, 'wb') as fh:
                fh.write(bytes(qbytes))

    def to_pdf2(self, filepath):
        # just a sketch ... needs stuff from above, too ...
        printer = QPdfWriter(filepath)
        logicalDPIX = printer.logicalDpiX() # int
        PointsPerInch = 72
        painter = QPainter()
        painter.begin(printer)
        t = QTransform()
        scaling = logicalDPIX / PointsPerInch # float, 16.6
        t.scale(scaling, scaling)
        # do drawing with painter
        painter.end()
        painter.setTransform(t)

###

class CellStyle:
    """Handle various aspects of cell styling.
    Also manage caches for fonts, pens and brushes.
    """
    _fonts = {}
    _brushes = {}
    _pens = {}
#
    @classmethod
    def getFont(cls, fontFamily, fontSize, fontBold, fontItalic):
        ftag = (fontFamily, fontSize, fontBold, fontItalic)
        try:
            return cls._fonts[ftag]
        except:
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
        cls._fonts[ftag] = font
        return font
#
    @classmethod
    def getPen(cls, width):
        """Manage a cache for pens of different width.
        """
        if width:
            try:
                return cls._pens[width]
            except AttributeError:
                cls._pens = {}
            except KeyError:
                pen = QPen('#FF' + BORDER_COLOUR)
                pen.setWidthF(width)
                cls._pens[width] = pen
                return pen
        else:
            try:
                return cls._noPen
            except AttributeError:
                cls._noPen = QPen()
                cls._noPen.setStyle(Qt.NoPen)
                return cls._noPen
#
    @classmethod
    def getBrush(cls, colour):
        """Manage a cache for brushes of different colour.
        <colour> is a colour in the form 'RRGGBB'.
        """
        try:
            return cls._brushes[colour or FONT_COLOUR]
        except:
            pass
        brush = QBrush(QColor('#FF' + (colour or FONT_COLOUR)))
        cls._brushes[colour] = brush
        return brush
#
    def __init__(self, font, size, align = 'c', highlight = None,
            bg = None, border = 1, mark = None):
        """
        <font> is the name of the font (<None> => default, not recommended,
            unless the cell is to contain no text).
        <size> is the size of the font (<None> => default, not recommended,
            unless the cell is to contain no text).
        <align> is the horizontal (l, c or r) OR vertical (b, m, t) alignment.
            Vertical alignment is for rotated text (-90° only).
        <highlight> can set bold, italic and font colour: 'bi:RRGGBB'. All bits
            are optional, but the colon must be present if a colour is given.
        <bg> can set the background colour ('RRGGBB').
        <border>: Only three border types are supported here:
            0: none
            1: all sides
            2: (thicker) underline
        <mark> is a colour ('RRGGBB') which can be selected as an
        "alternative" font colour.
        """
        # Font
        self.setFont(font, size, highlight)
        self.colour_marked = mark
        # Alignment
        self.setAlign(align)
        # Background colour
        self.bgColour = self.getBrush(bg) if bg else None
        # Border
        self.border = border
#
    def setFont(self, font, size, highlight):
        self._font, self._size, self._highlight = font, size, highlight
        try:
            emph, clr = highlight.split(':')
        except:
            emph, clr = highlight or '', None
        self.fontColour = self.getBrush(clr)
        self.font = self.getFont(font, size, 'b' in emph, 'i' in emph)
#
    def setAlign(self, align):
        if align in 'bmt':
            # Vertical
            self.alignment = ('c', align, True)
        else:
            self.alignment = (align, 'm', False)
#
    def copy(self, font = None, size = None, align = None,
            highlight = None, mark = None, bg = None, border = None):
        """Make a copy of this style, but with changes specified by the
        parameters.
        Note that a change to a 'None' parameter value is not possible.
        """
        newstyle = copy.copy(self)
        if font or size or highlight:
            newstyle.setFont(font or self._font,
                    size or self._size, highlight or self._highlight)
        if mark:
            newstyle.colour_marked = mark
        if align:
            newstyle.setAlign(align)
        if bg:
            newstyle.bgColour = self.getBrush(bg)
        if border != None:
            newstyle.border = border
        return newstyle

###

class Tile(QGraphicsRectItem):
    """The graphical representation of a table cell.
    This cell can span rows and columns.
    It contains a simple text element.
    Both cell and text can be styled to a limited extent (see <CellStyle>).
    """
    def __init__(self, grid, tag, x, y, w, h, text, style):
        self._style = style
        self._grid = grid
        self.tag = tag
        self.height0 = h
        self.width0 = w
        super().__init__(0, 0, w, h)
        self.setFlag(self.ItemClipsChildrenToShape, True)
        self.setPos(x, y)

        # Background colour
        if style.bgColour != None:
            self.setBrush(style.bgColour)

        # Border
        if style.border == 1:
            # Set the pen for the rectangle boundary
            pen0 = CellStyle.getPen(BORDER_WIDTH)
        else:
            # No border for the rectangle
            pen0 = CellStyle.getPen(None)
            if style.border != 0:
                # Thick underline
                line = QGraphicsLineItem(self)
                line.setPen(CellStyle.getPen(UNDERLINE_WIDTH))
                line.setLine(0, h, w, h)
        self.setPen(pen0)

        # Alignment and rotation
        self.halign, self.valign, self.rotation = style.alignment
        # Text
        self.textItem = QGraphicsSimpleTextItem(self)
        self.textItem.setFont(style.font)
        self.textItem.setBrush(style.fontColour)
        self.setText(text or '')
#
    def mark(self):
        if self._style.colour_marked:
            self.textItem.setBrush(self._style.getBrush(self._style.colour_marked))
#
    def unmark(self):
        self.textItem.setBrush(self._style.fontColour)
#
    def margin(self):
        return 0.4 * self._grid._gview.MM2PT
#
    def value(self):
        return self._text
#
    def setText(self, text):
        if type(text) != str:
            raise GridError(_NOTSTRING.format(val = repr(text)))
        self._text = text
        self.textItem.setText(text)
        self.textItem.setScale(1)
        w = self.textItem.boundingRect().width()
        h = self.textItem.boundingRect().height()
        if text:
            scale = 1
            maxw = self.width0 - self.margin() * 2
            maxh = self.height0 - self.margin() * 2
            if self.rotation:
                maxh -= self.margin() * 4
                if w > maxh:
                    scale = maxh / w
                if h > maxw:
                    _scale = maxw / h
                    if _scale < scale:
                        scale = _scale
                if scale < 0.6:
                    self.textItem.setText('###')
                    scale = (maxh /
                            self.textItem.boundingRect().width())
                if scale < 1:
                    self.textItem.setScale(scale)
                trf = QTransform().rotate(-90)
                self.textItem.setTransform(trf)
            else:
                maxw -= self.margin() * 4
                if w > maxw:
                    scale = maxw / w
                if h > maxh:
                    _scale = maxh / h
                    if _scale < scale:
                        scale = _scale
                if scale < 0.6:
                    self.textItem.setText('###')
                    scale = (maxw /
                            self.textItem.boundingRect().width())
                if scale < 1:
                    self.textItem.setScale(scale)
#TODO-
            print("    -->", scale, text, w, h, maxw, maxh)
        bdrect = self.textItem.mapRectToParent(
                self.textItem.boundingRect())
        yshift = - bdrect.top() if self.rotation else 0.0
        w = bdrect.width()
        h = bdrect.height()
        xshift = 0.0
        if self.halign == 'l':
            xshift += self.margin()
        elif self.halign == 'r':
            xshift += self.width0 - self.margin() - w
        else:
            xshift += (self.width0 - w) / 2
        if self.valign == 't':
            yshift += self.margin()
        elif self.valign == 'b':
            yshift += self.height0 - self.margin() - h
        else:
            yshift += (self.height0 - h) / 2
        self.textItem.setPos(xshift, yshift)
#
    def leftclick(self):
        return self._grid.tile_left_clicked(self)
#
    def rightclick(self):
        return self._grid.tile_right_clicked(self)


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#
#TODO ...
