# -*- coding: utf-8 -*-
"""
ui/grid2.py

Last updated:  2021-03-27

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
FONT_DEFAULT = 'Arial'
FONT_SIZE_DEFAULT = 11
FONT_COLOUR = '662222'

# Line width for borders
UNDERLINE_WIDTH = 3.0
BORDER_WIDTH = 1.0

NO_ITEM = '555555'  # colour for unused table cells

_DATE_POPUP = "Datum wählen"
_TEXT_POPUP = "Text eingeben"

#####################

### Messages
_TILE_OUT_OF_BOUNDS = ("Kachel außerhalb Tabellenbereich:\n"
        " Zeile {row}, Höhe {rspan}, Spalte {col}, Breite {cspan}")
_INVALIDLINEWIDTH = "Ungültige Strichbreite: {val}"
_NOTSTRING          = "In <grid::Tile>: Zeichenkette erwartet: {val}"
_TITLE_LOSE_CHANGES = "Ungespeicherte Änderungen"
_LOSE_CHANGES = "Sind Sie damit einverstanden, dass die Änderungen verloren gehen?"

### Dialog labels
_FILESAVE = "Datei speichern"
_PDF_FILE = "PDF-Datei (*.pdf)"

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
        if s0 and not scene and not s0.leave_ok():
            return False
        self.setScene(scene)
        if scene:
            # Set the view's scene area to a fixed size
            # (pop-ups could otherwise extend it)
            self.setSceneRect(scene._sceneRect)
        return True
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
                    return
#
    def set_changed(self, show):
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

class Gridbase(QGraphicsScene):
    _savedir = None
    @classmethod
    def set_savedir(cls, path):
        cls._savedir = path
#
    def __init__(self, gview, rowheights, columnwidths):
        """Set the grid size.
            <columnwidths>: a list of column widths (mm)
            <rowheights>: a list of row heights (mm)
        Rows and columns are 0-indexed.
        """
        super().__init__()
        self._gview = gview
        self._styles = {'*': CellStyle(FONT_DEFAULT, FONT_SIZE_DEFAULT,
                align = 'c', border = 1)
        }
        self.tagmap = {}        # {tag -> {Tile> instance}
        self.value0 = {}        # initial values (text) of cells
        self._changes_init()    # set of changed cells (tags)
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
# Allow a little margin? e.g.(-1.0, -1.0, x + 1.0, y + 1.0)
        self._sceneRect = QRectF(0.0, 0.0, x, y)
        # For popup editors
        self.editors = {
            'LINE': PopupLineEdit(self),
            'DATE': PopupDate(self),
            'TEXT': PopupTextEdit(self)
        }
        self._popup = None  # the "active" pop-up editor
#
    def changes(self):
        return list(self._changes)
#
    def change_values(self):
        return {tag: self.tagmap[tag].value() for tag in self.changes()}
#
    def _changes_init(self):
        self._changes = set()
        self._gview.set_changed(False)
#
    def changes_discard(self, tag):
        self._changes.discard(tag)
        if not self._changes:
            self._gview.set_changed(False)
#
    def changes_add(self, tag):
        if not self._changes:
            self._gview.set_changed(True)
        self._changes.add(tag)
#
    def leave_ok(self):
        """If there are unsaved changes, ask whether it is ok to lose
        them. Return <True> if ok to lose them (or if there aren't any
        changes), otherwise <False>.
        """
        if self._changes:
            return QuestionDialog(_TITLE_LOSE_CHANGES, _LOSE_CHANGES)
        return True
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
    def viewWH(self):
        """Return the width and height of the viewing area scaled to
        scene coordinates.
        This must query the graphics-view widget.
        """
        vp = self._gview.viewport()
        vw1 = vp.width()
        vh1 = vp.height()
        spoint = self._gview.mapToScene(vw1, vh1)
        return (spoint.x(), spoint.y())
#
    ### Methods dealing with cell editing
    def editCell(self, tile, x, y):
        editor = self.editors[tile.validation]
        if editor:
            editor.activate(tile, x, y)
#
    def addSelect(self, tag, valuelist):
        if tag in self.editors:
            raise GridError(_EDITOR_TAG_REUSED.format(tag = tag))
        self.editors[tag] = PopupTable(self, valuelist)
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


### ---------------
#
    def tile(self, row, col, text = None, cspan = 1, rspan = 1,
            style = None, validation = None, tag = None, label = None):
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
        t = Tile(self, tag, x, y, w, h, text, cell_style, validation, label)
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
        """Set the text in the given cell, not activating the
        cell-changed callback.
        """
        self.tagmap[tag].setText(text)
#
    def set_text_init(self, tag, text):
        """Reset the initial text in the given cell, not activating the
        cell-changed callback.
        """
        tile = self.tagmap[tag]
        tile.setText(text)
        self.value0[tag] = text
        # Clear "changed" highlighting
        if tile._style.colour_marked:
            # Only if the cell _can_ highlight "changed" ...
            tile.unmark()
            self.changes_discard(tag)
#
    def clear_changes(self):
        """Used after saving changes to clear markings.
        """
        for tag in self.changes():
            tile = self.tagmap[tag]
            self.value0[tag] = tile.value()
            self.changes_discard(tag)
            if tile._style.colour_marked:
                # Only if the cell _can_ highlight "changed" ...
                tile.unmark()
#
    def set_change_mark(self, tag, text):
        tile = self.tagmap[tag]
        if text == self.value0[tag]:
            self.changes_discard(tag)
            tile.unmark()
        else:
            self.changes_add(tag)
            tile.mark()
#
    def valueChanged(self, tag, text):
        """Cell-changed callback. This should be overridden if it is needed.
        The default code changes the text colour of a cell when the text
        differs from its initial value (a "changed" indicator).
        Also a set of "changed" cells is maintained.
        """
        self.set_change_mark(tag, text)
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
                pen = QPen()
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
    """
    def __init__(self, grid, tag, x, y, w, h, text, style, validation, label):
        self._style = style
        self._grid = grid
        self.tag = tag
        self.height0 = h
        self.width0 = w
        self.validation = validation
        self.label = label
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
        if text == None and not validation:
            self.textItem = None
        else:
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
        return 1.0 * self._grid._gview.MM2PT
#
    def value(self):
        return None if self.textItem == None else self._text
#
    def setText(self, text):
        if type(text) != str:
            raise GridError(_NOTSTRING.format(val = repr(text)))
        self._text = text
        self.textItem.setText(text)
        w = self.textItem.boundingRect().width()
        self.textItem.setScale(1)
        if text and self.validation == 'TEXT':
            # This cannot be rotated ...
            w = self.textItem.boundingRect().width()
            h = self.textItem.boundingRect().height()
            wscale = self.width0 / w
            hscale = self.height0 / h
            scale = hscale if hscale < wscale else wscale
            if scale < 0.6:
                self.textItem.setText('###')
                scale = self.width0 / self.textItem.boundingRect().width()
            if scale < 1.0:
                self.textItem.setScale(scale)
            bdrect = self.textItem.mapRectToParent(
                    self.textItem.boundingRect())
            yshift = 0.0
        elif self.rotation:
            maxh = self.height0 - self.margin() * 2
            if w > maxh:
                scale = maxh / w
                if scale < 0.6:
                    scale = 0.6
                self.textItem.setScale(scale)
            trf = QTransform().rotate(-90)
            self.textItem.setTransform(trf)
            bdrect = self.textItem.mapRectToParent(
                    self.textItem.boundingRect())
            yshift = - bdrect.top()
        else:
            maxw = self.width0 - self.margin() * 2
            if w > maxw:
                scale = maxw / w
                if scale < 0.6:
                    scale = 0.6
                self.textItem.setScale(scale)
            bdrect = self.textItem.mapRectToParent(
                    self.textItem.boundingRect())
            yshift = 0.0
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
    def click(self, event):
        if self.validation and event.button() == Qt.LeftButton:
#            point = event.scenePos ()
            point = self.pos()
            # Select type of popup and activate it
            self._grid.editCell(self, point.x(), point.y())
        return False
#
    def newValue(self, text):
        """Called with the new value. The tile should be updated and the
        callback invoked.
        """
        self.setText(text)
        self._grid.valueChanged(self.tag, text)

###

def PopupTable(grid, items, ncols = 3):
    if items:
        return _PopupTable(grid, items, ncols)
    return None
##
class _PopupTable(QDialog):
#TODO: Note the change: '' is no longer included automatically!!!
    def __init__(self, grid, items, ncols):
        self._grid = grid
        super().__init__()
        vbox = QVBoxLayout(self)
        self.table = QTableWidget(self)
        vbox.addWidget(self.table)
        self.setWindowTitle("?")
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
#
    def _select(self, item):
        if item._text != None:
            self._value = item._text
            self.accept()
#
    def activate(self, tile, x, y):
        # x and y are scene coordinates.
        self.move(self._grid.screen_coordinates(x, y))
        if self.exec_():
            tile.newValue(self._value)

###

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
                | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        vbox.addWidget(self.lbl)
        vbox.addWidget(buttonBox)
        self.setLayout(vbox)
        self.setWindowTitle(_DATE_POPUP)
#        self.setWindowFlags(Qt.SplashScreen)
#
    def activate(self, tile, x, y):
        # Set date
        self.tile = tile
        date = tile.value()
        self.cal.setSelectedDate(QDate.fromString(date, 'yyyy-MM-dd')
                if date else QDate.currentDate())
        self.newDate(self.cal.selectedDate())
        self.move(self._grid.screen_coordinates(x, y))
        if self.exec_():
            self.tile.newValue(self.date)
#
    def newDate(self, date):
        self.lbl.setText(QLocale().toString(date))
        self.date = date.toString('yyyy-MM-dd')

###

class PopupTextEdit(QDialog):
    def __init__(self, grid):
        self._grid = grid
        super().__init__()
        vbox = QVBoxLayout(self)
        self.textedit = QTextEdit(self)
        self.textedit.setTabChangesFocus(True)
        vbox.addWidget(self.textedit)
        self.lbl = QLabel(self)
        vbox.addWidget(self.lbl)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok
                | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        vbox.addWidget(buttonBox)
        self.setWindowTitle(_TEXT_POPUP)
#
    def activate(self, tile, x, y):
        self.lbl.setText(tile.label)
        text = tile.value()
        self.textedit.setPlainText(text)
        self.move(self._grid.screen_coordinates(x, y))
        if self.exec_():
            text = self.textedit.toPlainText()
            if text:
                text = '\n'.join([l.rstrip() for l in text.splitlines()])
            tile.newValue(text)

###

class PopupLineEdit(QDialog):
    def __init__(self, grid):
        self._grid = grid
        super().__init__()
        vbox = QVBoxLayout(self)
        self.lineedit = QLineEdit(self)
        vbox.addWidget(self.lineedit)
        self.lineedit.returnPressed.connect(self.accept)
#
    def activate(self, tile, x, y):
        self.setWindowTitle(tile.label)
        w = tile.width0
        if w < 50.0:
            w = 50.0
        self.lineedit.setFixedWidth(w)
        self.lineedit.setText(tile.value() or '')
        self.move(self._grid.screen_coordinates(x, y))
        if self.exec_():
            text = self.lineedit.text()
            tile.newValue(text)


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication, QDialog, QHBoxLayout, \
            QPushButton, QMessageBox
    from qtpy.QtCore import QLocale, QTranslator, QLibraryInfo

    def function():
        QMessageBox.information(window, "Message", "Ouch!")

    app = QApplication(sys.argv)
    LOCALE = QLocale(QLocale.German, QLocale.Germany)
    QLocale.setDefault(LOCALE)
    qtr = QTranslator()
    qtr.load("qt_" + LOCALE.name(),
            QLibraryInfo.location(QLibraryInfo.TranslationsPath))
    app.installTranslator(qtr)

    window = QDialog()
    gview = GridView()

    topbox = QHBoxLayout(window)
    topbox.addWidget(gview)

    pb = QPushButton('–')
    pb.clicked.connect(function)
    topbox.addWidget(pb)

    # Add some data
    rows = (10, 2, 6, 6, 6, 6, 6)
    cols = (25, 10, 8, 20, 8, 8, 25)
    cols = (25, 10, 8, 20, 8, 8, 15)
    grid = Gridbase(gview, rows, cols)

    grid.new_style('title', font = 'Serif', size = 12,
            align = 'c', border = 2)

    # Title
    t = grid.tile(0, 0, cspan = len(cols), text = "Table Testing",
                style = 'title')
    t.setToolTip ('This is the <b>title</b> of the table')

    grid.addSelect('SGRADE', ('1', '2', '3', '4', '5', '6',
            'nb', 'nt', '*', '/'))

    grid.tile(2, 0, tag = 'd1', text = "2020-08-10", validation = 'DATE')
    grid.tile(2, 6, tag = 'd2', text = "2020-09-02", validation = 'DATE')
    grid.tile(4, 3, tag = 'd3', text = "2020-02-09", validation = 'DATE')
    grid.tile(4, 0, cspan = 3, rspan = 3, tag = 'd4',
            text = "Text\nwith\nmultiple lines.", validation = 'TEXT')
    grid.tile(6, 6, tag = 'd5', text = "More than\none line.", validation = 'TEXT')

    grid.tile(5, 4, tag = 'g1', text = "4", validation = 'SGRADE')
    grid.tile(3, 2, tag = 'g2', validation = 'SGRADE')

    grid.tile(3, 0, cspan = 2, tag = 't1', validation = 'LINE', text = "Text")
    grid.tile(4, 5, tag = 't2', validation = 'LINE', text = "X")

    gview.set_scene(grid)
    window.resize(600, 400)
    window.exec_()
