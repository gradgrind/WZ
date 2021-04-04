# -*- coding: utf-8 -*-
"""
ui/grid.py

Last updated:  2021-04-04

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
NO_ITEM = '555555'  # colour for unused table cells, rrggbb

#####################################################

import sys, os, copy
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

from qtpy.QtWidgets import QLineEdit, QTextEdit, \
    QCalendarWidget, QVBoxLayout, QLabel, QDialog, QDialogButtonBox, \
    QTableWidget, QTableWidgetItem
from qtpy.QtCore import QDate, Qt, QMarginsF, QRectF, QBuffer, QByteArray, \
        QLocale

from ui.gridbase import CellStyle, GridView, GridBase

### ++++++

class EditableGridView(GridView):
    def is_modified(self):
        return bool(self.scene().changes())
#
    def set_changed(self, mods):
        """Called when there is a switch between 'no-changes' and 'changes'
        (mods = True) or the reverse (mods = False) in the managed scene.
        Override if needed.
        """
        pass
#
    def set_scene(self, scene):
        """Set or clear the managed scene.
        This clears the 'changes' state of the exited scene and
        initializes that of the entered scene.
        """
        s0 = self.scene()
        if s0:
            s0.view(False)
        super().set_scene(scene)
        if scene:
            scene.view(True)

###

class Grid(GridBase):
    def __init__(self, gview, rowheights, columnwidths):
        super().__init__(gview, rowheights, columnwidths)
        self.value0 = {}        # initial values (text) of cells
        # For popup editors
        self.editors = {
            'LINE': PopupLineEdit(self),
            'DATE': PopupDate(self),
            'TEXT': PopupTextEdit(self)
        }
        self._changes = None
#
    def view(self, activate = True):
        """Called when the scene is (de)activated in the view.
        """
        if activate:
            self._changes = set()
            self._gview.set_changed(False)
        else:
            self._changes = None
#
    def changes(self):
        return list(self._changes)
#
    def change_values(self):
        return {tag: self.tagmap[tag].value() for tag in self.changes()}
#
    def changes_discard(self, tag):
        if self._changes:
            self._changes.discard(tag)
            if not self._changes:
                self._gview.set_changed(False)
#
    def changes_add(self, tag):
        if not self._changes:
            self._gview.set_changed(True)
        self._changes.add(tag)
#
    ### Methods dealing with cell editing
    def tile_left_clicked(self, tile):
        if tile.validation:
            # Select type of popup and activate it
            editor = self.editors[tile.validation]
            if editor:
                point = tile.pos()
                editor.activate(tile, point.x(), point.y())
        return False
#
    def addSelect(self, tag, valuelist):
        if tag in self.editors:
            raise GridError(_EDITOR_TAG_REUSED.format(tag = tag))
        self.editors[tag] = PopupTable(self, valuelist)
#
    def tile(self, row, col, **kargs):
        """Add a tile to the grid. Adds the attribute <value0> to the
        base implementation.
        """
        validation = kargs.pop('validation', None)
        t = super().tile(row, col, **kargs)
        t.validation = validation
        self.value0[t.tag] = t.value()  # initial value
        return t
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
            # Only needed if the cell _can_ highlight "modified" ...
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
                # Only needed if the cell _can_ highlight "modified" ...
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
    def value_changed(self, tile, text):
        """Cell-changed callback. This should be overridden if it is needed.
        The default code changes the text colour of a cell when the text
        differs from its initial value (a "changed" indicator).
        Also a set of "changed" cells is maintained.
        """
        self.set_change_mark(tile.tag, text)
        tile.setText(text)

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
        self.setWindowTitle(tile.tag)
        # x and y are scene coordinates.
        self.move(self._grid.screen_coordinates(x, y))
        if self.exec_():
            self._grid.value_changed(tile, self._value)

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
#
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
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok
                | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        vbox.addWidget(buttonBox)
#
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
        self.setWindowTitle(tile.tag)
        w = tile.width0
        if w < 50.0:
            w = 50.0
        self.lineedit.setFixedWidth(w)
        self.lineedit.setText(tile.value() or '')
        self.move(self._grid.screen_coordinates(x, y))
        if self.exec_():
            self._grid.value_changed(tile, self.lineedit.text())


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication, QHBoxLayout, \
            QPushButton, QMessageBox
    from qtpy.QtCore import QTranslator, QLibraryInfo

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
    grid = Grid(gview, rows, cols)

    grid.new_style('title', font = 'Serif', size = 12,
            align = 'c', border = 2)
    grid.new_style('90', base = '*', align = 'b')

    # Title
    t = grid.tile(0, 0, cspan = len(cols), text = "Table Testing",
                style = 'title')
    t.setToolTip ('This is the <b>title</b> of the table')

    grid.addSelect('SGRADE', ('1', '2', '3', '4', '5', '6',
            'nb', 'nt', '*', '/', ''))

    grid.tile(2, 0, tag = 'd1', text = "2020-08-10", validation = 'DATE')
    grid.tile(2, 6, rspan = 3, tag = 'd2', text = "2020-09-02",
            style = '90', validation = 'DATE')
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
