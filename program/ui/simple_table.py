"""
ui/simple_table.py

Last updated:  2023-01-22

A fairly simple table widget, which supports (single) range selection.
Cell editing is possible using external pop-up editors.


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
"""

import sys, os

if __name__ == "__main__":
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))

T = TRANSLATIONS("ui.simple_table")

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
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QAction,
    # QMenu,
    ## QtGui
    QKeySequence,
    ## QtCore
    Qt,
    QPoint,
)

### -----

class TableWidget(QTableWidget):
    def __init__(self, parent=None, edit_handler=None):
        self.edit_handler = edit_handler
        super().__init__(parent=parent)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ContiguousSelection)
        # The editing support built into <QTableWidget> is not used.
        # Event handlers determine when a selection should be laid on or
        # adjusted – or else when to call an external editor supplied as
        # a function via the <edit_handler> paramater.

        # Change stylesheet to make the current and selected cells more visible
        self.setStyleSheet(
            """QTableView {
               selection-background-color: #f0e0ff;
               selection-color: black;
            }
            QTableView::item:focus {
                selection-background-color: #d0ffff;
            }
            """
        )
        self.cellClicked.connect(self.clicked)
        self.cellPressed.connect(self.pressed)
        self.cellEntered.connect(self.entered)
        self.click_pending = False

    def keyPressEvent(self, e):
        e.accept()
        key = e.key()
        if key == Qt.Key_Return:
            self.open_editor(self.currentRow(), self.currentColumn())
        else:
            super().keyPressEvent(e)

    def clicked(self, r, c):
        if self.click_pending:
            self.open_editor(r, c)

    def open_editor(self, r, c):
        if self.edit_handler:
            x = self.columnViewportPosition(c)
            y = self.rowViewportPosition(r)
            pos = self.mapToGlobal(QPoint(x, y))
            # print("CLICKED", r, c, pos)
            val = self.edit_handler(r, c, pos)
            if val != None:
                self.write_cell(r, c, val)

    def pressed(self, r, c):
        km = QApplication.instance().queryKeyboardModifiers()
        self.click_pending = km == Qt.KeyboardModifier.NoModifier

    def entered(self, r, c):
        # print("ENTERED", r, c)
        self.click_pending = False

    def get_selection(self):
        """Return the selected cell range:
            (number of rows, top row, number of columns, top column)
        If no cells are selected, all elements are 0.
        """
        try:
            sel_range = self.selectedRanges()[0]
        except IndexError:
            return (0, 0, 0, 0)
        r0 = sel_range.topRow()
        c0 = sel_range.leftColumn()
        nrows = sel_range.bottomRow() - r0 + 1
        ncols = sel_range.rightColumn() - c0 + 1
        return (nrows, r0, ncols, c0)

    ##### Actions: copy/paste

    def add_actions(self):
        # self.selection_menu = QMenu(self)
        action = QAction(T["COPY_SELECTION"], parent=self)
        action.setShortcut(QKeySequence.Copy)
        action.setShortcutVisibleInContextMenu(True)
        action.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)
        action.triggered.connect(self.read_from_selection)
        self.addAction(action)
        # self.selection_menu.addAction(action)
        action = QAction(T["PASTE_SELECTION"], parent=self)
        action.setShortcut(QKeySequence.Paste)
        action.setShortcutVisibleInContextMenu(True)
        action.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)
        action.triggered.connect(self.write_to_selection)
        self.addAction(action)
        # self.selection_menu.addAction(action)
        # Enable context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

    def read_cell(self, r, c):
        """Return the value in the given cell.
        Override this if the cell values are not the same as the
        displayed values.
        """
        return self.item(r, c).text()

    def write_cell(self, r, c, value):
        """Write the given value to the given cell.
        Override this if there is an underlying data store.
        """
        self.item(r, c).setText(value)

    def write_cells_to_row(self, r, c, row):
        """Write a list of values to cells in row <r> starting at
        column <c>.
        This can be overridden if there is an underlying data store
        which can perform the writing more efficiently.
        """
        for val in row:
            self.write_cell(r, c, val)
            c += 1

    def read_from_selection(self):
        """Copy the values from the selected cells to the clipboard,
        in tab-separated-value format.
        """
        nrows, r0, ncols, c0 = self.get_selection()
        if not nrows:
            SHOW_WARNING(T["NO_SELECTION"])
            return None
        rows = []
        i = 0
        while i < nrows:
            j = 0
            row = []
            while j < ncols:
                row.append(self.read_cell(r0 + i, c0 + j))
                j += 1
            rows.append(row)
            i += 1
        # Put this data into clipboard
        QApplication.instance().clipboard().setText(Table2TSV(rows))

    def write_to_selection(self):
        """Paste the clipboard to the selected grid cells.
        The clipboard will be interpreted as a table.
        See <PasteFit> for details on dimension compatibility.
        """
        nrows, r0, ncols, c0 = self.get_selection()
        if not nrows:
            SHOW_WARNING(T["NO_SELECTION"])
            return
        clipboard = QApplication.instance().clipboard()
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
            for i in range(nrows):  # iterate over selected rows
                self.write_cells_to_row(r0 + i, c0, table_data[i])
        else:
            SHOW_ERROR(
                T["BAD_PASTE_RANGE"].format(
                    h0=len(table_data),
                    w0=len(table_data[0]),
                    h1=nrows,
                    w1=ncols
                )
            )


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from ui.ui_base import run
    from ui.cell_editors import CellEditorLine

    line_editor = CellEditorLine().activate
    def cell_editor(r, c, pos):
        props = {"VALUE": widget.read_cell(r, c)}
        if line_editor(pos, props):
            return props["VALUE"]
        else:
            return None

    widget = TableWidget(edit_handler=cell_editor)
    widget.add_actions()
    width = 6
    height = 10
    widget.setColumnCount(width)
    widget.setRowCount(height)
    for r in range(height):
        for c in range(width):
            widget.setItem(r, c, QTableWidgetItem())
    widget.resize(600, 550)
    run(widget)
