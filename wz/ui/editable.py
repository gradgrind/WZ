# -*- coding: utf-8 -*-

"""
ui/editable.py

Last updated:  2021-11-01

An editable table widget using QTableWidget as base class. Only text
cells are handled.
Originally inspired by "TableWidget.py" from the "silx" project (www.silx.org),
thanks to P. Knobel, but it differs in several respects.

=+LICENCE=================================
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

=-LICENCE=================================
"""

#TODO
### Undo of multiple add/remove rows/columns as a block rather than
###     individual rows/columns?
### Ideally actions which in the present state don't do anything should
###     be disabled.
### An invisible QAction seems to imply it is also disabled.
### There is a signal on QItemSelectionModel:
###    selectionChanged(const QItemSelection &selected, const QItemSelection &deselected)

### Messages

#_TOO_MANY_ROWS = "Too many rows to insert"
_TOO_MANY_ROWS = "Einfügen nicht möglich – zu viele Zeilen"
#_TOO_MANY_COLUMNS = "Too many columns to insert"
_TOO_MANY_COLUMNS = "Einfügen nicht möglich – zu viele Spalten"
#_BAD_PASTE_RANGE = "Clipboard data dimensions incompatible with selected" \
#        " range"
_BAD_PASTE_RANGE = "Die Dimensionen der einzufügenden Daten sind nicht" \
        " kompatibel mit dem ausgewählten Bereich."
#_PASTE_PROTECTED = "Some data could not be inserted because of" \
#        " write-protected cells.
_PASTE_PROTECTED = "Zellen sind schreibgeschützt – einfügen nicht möglich"
#_CUTSELECTION = "Cut selection"
_CUTSELECTION = "Auswahl ausschneiden"
#_TTCUTSELECTION = "Cut selection, placing cell values in the clipboard."
_TTCUTSELECTION = "Auswahl ausschneiden und in die Zwischanablage kopieren."
#_COPYSELECTION = "Copy selection"
_COPYSELECTION = "Auswahl kopieren"
#_TTCOPYSELECTION = "Copy selected cells into the clipboard."
_TTCOPYSELECTION = "Ausgewählte Zellen in die Zwischanablage kopieren."
#_COPYFAIL = "No cells are selected"
_COPYFAIL = "Keine ausgewählten Zellen"
#_PASTE = "Paste"
_PASTE = "Einfügen"
#_TTPASTE = "Paste data." \
#         " The selected cell is the top-left corner of the paste area."
_TTPASTE = "Daten einfügen. Die ausgewählte Zelle ist oben links" \
        " im Bereich, der eingefügt wird."
#_INSERTROW = "Insert Row"
_INSERTROW = "Zeile einfügen"
#_TTINSERTROW = "Insert Row"
_TTINSERTROW = "Zeile einfügen nach der aktuellen Zeile"
#_DELETEROWS = "Delete Rows"
_DELETEROWS = "Zeilen löschen"
#_TTDELETEROWS = "Delete selected Rows"
_TTDELETEROWS = "ausgewählte Zeilen löschen"
#_DELETEROWSFAIL = "Deletion of the last row(s) is not permitted"
_DELETEROWSFAIL = "Das Löschen der letzten Zeile(n) ist nicht zulässig"
#_INSERTCOLUMN = "Insert Column"
_INSERTCOLUMN = "Spalte einfügen"
#_TTINSERTCOLUMN = "Insert Column"
_TTINSERTCOLUMN = "Spalte einfügen nach der aktuellen Spalte"
#_DELETECOLUMNS = "Delete Columns"
_DELETECOLUMNS = "Spalten löschen"
#_TTDELETECOLUMNS = "Delete selected Columns"
_TTDELETECOLUMNS = "ausgewählte Spalten löschen"
#_DELETECOLUMNSFAIL = "Deletion of the last column(s) is not permitted"
_DELETECOLUMNSFAIL = "Das Löschen der letzten Spalte(n) ist nicht zulässig"

########################################################################

from enum import Enum, auto

from qtpy.QtWidgets import QApplication, \
        QTableView, QTableWidget, QMessageBox, \
        QStyledItemDelegate, QStyleOptionViewItem
from qtpy.QtCore import Qt, QPointF, QRectF, QSize
from qtpy.QtGui import QKeySequence
from qtpy.QtWidgets import QAction, QShortcut  # in Qt6 these are in QtGui

class Bug(Exception):
    pass

### -----

class Change(Enum):
    """Types of changes which are to be recorded by undo/redo function.
    """
    CELL = auto()
    BLOCK = auto()
    ADD_ROW = auto()
    DEL_ROW = auto()
    ADD_COL = auto()
    DEL_COL = auto()


class InsertRowAction(QAction):
    """QAction to insert a row of cells.
    """
    def __init__(self, table):
        super().__init__(table)
        self.setText(_INSERTROW)
        self.setToolTip(_TTINSERTROW)
# The tooltip is not shown in a popup menu ...
        self.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_N))
        self.setShortcutContext(Qt.WidgetShortcut)
        self.triggered.connect(self.insert_row)
        self.table = table

    def insert_row(self):
        """Insert an empty row below the current one.
        If multiple rows are selected, the same number will be added
        after the last selected row.
        """
        selected = self.table.get_selection()
        if selected[0]:
            h = selected[4]
            r = selected[1] + h
        else:
            h = 1
            r = self.table.currentRow() + 1
        while h > 0:
            self.table.insertRow(r)
            h -= 1


class InsertColumnAction(QAction):
    """QAction to insert a column of cells.
    """
    def __init__(self, table):
        super().__init__(table)
        self.setText(_INSERTCOLUMN)
        self.setToolTip(_TTINSERTCOLUMN)
# The tooltip is not shown in a popup menu ...
        self.setShortcut(QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_N))
        self.setShortcutContext(Qt.WidgetShortcut)
        self.triggered.connect(self.insert_column)
        self.table = table

    def insert_column(self):
        """Insert an empty column after the current one.
        If multiple columns are selected, the same number will be added
        after the last selected column.
        """
        selected = self.table.get_selection()
        if selected[0]:
            w = selected[3]
            c = selected[2] + w
        else:
            w = 1
            c = self.table.currentColumn() + 1
        while w > 0:
            self.table.insertColumn(c)
            w -= 1


class DeleteRowsAction(QAction):
    """QAction to delete rows of cells.
    """
    def __init__(self, table):
        super().__init__(table)
        self.setText(_DELETEROWS)
        self.setToolTip(_TTDELETEROWS)
        self.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_U))
        self.setShortcutContext(Qt.WidgetShortcut)
        self.triggered.connect(self.delete_rows)
        self.table = table

    def delete_rows(self):
        """Delete the selected rows or else the current row.
        """
        selected = self.table.get_selection()
        if selected[0]:
            n = selected[4]
            r0 = selected[1]
        else:
            n = 1
            r0 = self.table.currentRow()
            if r0 < 0:
                return
        if n == self.table.row_count():
            msgBox = QMessageBox(parent = self.table)
            msgBox.setText(_DELETEROWSFAIL)
            msgBox.exec()
        else:
            r = r0 + n
            while r > r0:
                r -= 1
                self.table.removeRow(r)


class DeleteColumnsAction(QAction):
    """QAction to delete columns of cells.
    """
    def __init__(self, table):
        super().__init__(table)
        self.setText(_DELETECOLUMNS)
        self.setToolTip(_TTDELETECOLUMNS)
        self.setShortcut(QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_U))
        self.setShortcutContext(Qt.WidgetShortcut)
        self.triggered.connect(self.delete_columns)
        self.table = table

    def delete_columns(self):
        """Delete the selected columns.
        """
        selected = self.table.get_selection()
        if selected[0]:
            n = selected[3]
            c0 = selected[2]
        else:
            n = 1
            c0 = self.table.currentColumn()
            if c0 < 0:
                return
        if n == self.table.column_count():
            msgBox = QMessageBox(parent = self.table)
            msgBox.setText(_DELETECOLUMNSFAIL)
            msgBox.exec()
        else:
            c = c0 + n
            while c > c0:
                c -= 1
                self.table.removeColumn(c)


class CopyCellsAction(QAction):
    """QAction to copy text from selected cells into the clipboard.
    If no cell is selected, no action is taken.
    If multiple cells are selected, the copied text will be a concatenation
    of the texts in all selected cells, tabulated with tabulation and
    newline characters.
    """
    def __init__(self, table):
        super().__init__(table)
        self.setText(_COPYSELECTION)
        self.setToolTip(_TTCOPYSELECTION)
        self.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_C))
        self.setShortcutContext(Qt.WidgetShortcut)
        self.triggered.connect(self.copyCellsToClipboard)
        self.table = table

    def copyCellsToClipboard(self):
        """Concatenate the text content of all selected cells into a string
        using tabulations and newlines to keep the table structure.
        Put this text into the clipboard.
        """
        n, t, l, w, h = self.table.get_selection()
        if n:
            rows = self.table.read_block(t, l, w, h)
            # put this data into clipboard
            qapp = QApplication.instance()
            qapp.clipboard().setText(table2tsv(rows))
        else:
            msgBox = QMessageBox(parent = self.table)
            msgBox.setText(_COPYFAIL)
            msgBox.exec()


class CutCellsAction(QAction):
    """QAction to copy text from selected cells into the clipboard and
    clear these cells in the table. For undo/redo this should count as
    a single operation.
    """
    def __init__(self, table):
        super().__init__(table)
        self.setText(_CUTSELECTION)
        self.setToolTip(_TTCUTSELECTION)
        self.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_X))
        self.setShortcutContext(Qt.WidgetShortcut)
        self.triggered.connect(self.cutCellsToClipboard)
        self.table = table

    def cutCellsToClipboard(self):
        """Concatenate the text content of all selected cells into a string
        using tabulations and newlines to keep the table structure.
        Put this text into the clipboard. Clear the selected cells.
        """
        block = self.table.cut_selection()
        if block is None:
            msgBox = QMessageBox(parent = self.table)
            msgBox.setText(_COPYFAIL)
            msgBox.exec()
        else:
            # put this data into clipboard
            qapp = QApplication.instance()
            qapp.clipboard().setText(block)


def tsv2table(text):
    """Parse a "tsv" (tab separated value) string into a list of lists
    of strings (a "table").

    The input text is tabulated using tabulation characters to separate
    the fields of a row and newlines to separate columns.

    The output lines are padded with '' values to ensure that all lines
    have the same length.

    Note that only '\n' is acceptable as the newline character. Other
    special whitespace characters will be left untouched.
    """
    rows = text.split('\n')
    # 'splitlines' can't be used as it loses trailing empty lines.
    table_data = []
    max_len = 0
    for row in rows:
        line = row.split('\t')
        l = len(line)
        if l > max_len:
            max_len = l
        table_data.append((line, l))
    result = []
    for line, l in table_data:
        if l < max_len:
            line += ['']*(max_len - l)
        result.append(line)
    return result

def table2tsv(table):
    """Represent a list of lists of strings (a "table") as a "tsv"
    (tab separated value) string.
    """
    return '\n'.join(['\t'.join(row) for row in table])


class RangeError(Exception):
    pass


class PasteCellsAction(QAction):
    """QAction to paste text from the clipboard into the table.

    If the text contains tabulations and newlines, they are interpreted
    as column and row separators.
    In such a case, the text is split into multiple texts to be pasted
    into multiple cells.
    """
    def __init__(self, table):
        super().__init__(table)
        self.table = table
        self.setText(_PASTE)
        self.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_V))
        self.setShortcutContext(Qt.WidgetShortcut)
        self.setToolTip(_TTPASTE)
        self.triggered.connect(self.pasteCellFromClipboard)

    def pasteCellFromClipboard(self):
        """Paste text from clipboard into the table.

        Pasting to more than one selected cell is possible if the data
        to be pasted has "compatible" dimensions:
            A single cell can be pasted to any block.
            A single row of cells can be pasted to a single column of cells.
            A single column of cells can be pasted to a single row of cells.
            Otherwise a block of cells can only be pasted to a single cell.

        If the block to be pasted would affect cells outside the grid,
        the pasting will fail.
        """
        nrows = self.table.row_count()
        ncols = self.table.column_count()
        n, r0, c0, w, h = self.table.get_selection()
        if n == 0:
            msgBox = QMessageBox(parent = self.table)
            msgBox.setText(_COPYFAIL)
            msgBox.exec()
            return
        qapp = QApplication.instance()
        clipboard_text = qapp.clipboard().text()
        table_data = tsv2table(clipboard_text)
        data_model = self.table.model()
        protected_cells = 0
        ph = len(table_data)
        pw = len(table_data[0])
        try:
            if ph == 1:                 # paste a single row
                if w == 1:              # ... to a single column
                    paste_data = table_data * h
                elif pw == 1:           # paste a single cell
                    row = table_data[0] * w
                    paste_data = [row] * h
                else:
                    raise RangeError(_BAD_PASTE_RANGE)
            elif pw == 1:               # paste a single column
                if h == 1:              # ... to a single row
                    paste_data = [row * w for row in table_data]
                else:
                    raise RangeError(_BAD_PASTE_RANGE)
            elif n == 1:                    # paste to a single cell
                paste_data = table_data
            else:
                raise RangeError(_BAD_PASTE_RANGE)
            # Check that the data to be pasted will fit into the table.
            if r0 + ph > nrows:
                raise RangeError(_TOO_MANY_ROWS)
            if c0 + pw > ncols:
                raise RangeError(_TOO_MANY_COLUMNS)
        except RangeError as e:
            msgBox = QMessageBox(parent=self.table)
            msgBox.setText(str(e))
            msgBox.exec()
            return
        if protected_cells:
            msgBox = QMessageBox(parent = self.table)
            msgBox.setText(_PASTE_PROTECTED)
            msgBox.exec()
        # Do the pasting
        self.table.paste_block(r0, c0, paste_data)


class UndoRedo:
    def __init__(self, table):
        self.table = table
        self.blocked = False

    def mark0(self, clear):
        if clear:
            self.changes = []
            self.index = 0
        self.index0 = self.index

    def enable(self, en):
        self.mark0(True)
        self.enabled = en

    def change(self, chtype, change):
        if self.enabled:
            if not self.blocked:
                #print("CHANGE:", chtype, change)
                del(self.changes[self.index:])
                self.changes.append((chtype, change))
                self.index = len(self.changes)
                self.table.set_modified(True)
        else:
            self.table.set_modified(True)

    def undo(self):
        if self.enabled and self.index > 0:
            self.blocked = True
            self.index -= 1
            chtype, change = self.changes[self.index]
            if chtype is Change.ADD_COL:
                self.table.removeColumn(change)
            elif chtype is Change.DEL_COL:
                self.table.insertColumn(change[0], data = change[1])
            elif chtype is Change.ADD_ROW:
                self.table.removeRow(change)
            elif chtype is Change.DEL_ROW:
                self.table.insertRow(change[0], data = change[1])
            elif chtype is Change.BLOCK:
                for _change in change:  # <change> is here a list
                    self.table.set_text(*_change[:3])
            elif chtype is Change.CELL:
                self.table.set_text(*change[:3])
            self.blocked = False
            self.table.set_modified(self.index != self.index0)

    def redo(self):
        if self.enabled and self.index < len(self.changes):
            self.blocked = True
            chtype, change = self.changes[self.index]
            self.index += 1
            if chtype is Change.ADD_COL:
                self.table.insertColumn(change)
            elif chtype is Change.DEL_COL:
                self.table.removeColumn(change[0])
            elif chtype is Change.ADD_ROW:
                self.table.insertRow(change)
            elif chtype is Change.DEL_ROW:
                self.table.removeRow(change[0])
            elif chtype is Change.BLOCK:
                for _change in change:  # <change> is here a list
                    self.table.set_text(*_change[:2], _change[3])
            elif chtype is Change.CELL:
                self.table.set_text(*change[:2], change[3])
            self.blocked = False
            self.table.set_modified(self.index != self.index0)


class EdiTableWidget(QTableWidget):
    def __init__(self, parent = None):
        super().__init__(parent = parent)
        self.setSelectionMode(self.ContiguousSelection)

        ### Extra shortcuts
        # Ctrl-A selects all cells (built-in shortcut in Qt)
        # Ctrl-Shift-A should cancel selection
        unselect = QShortcut(QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_A),
                self)
        unselect.activated.connect(self.clearSelection)

        # Undo (Ctrl-Z) and redo (Ctrl-Y)
        self.undoredo = UndoRedo(self)
        undo = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Z), self)
        undo.activated.connect(self.undoredo.undo)
        redo = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Y), self)
        redo.activated.connect(self.undoredo.redo)

        ### Actions
        self.copyCellsAction = CopyCellsAction(self)
        self.addAction(self.copyCellsAction)
        self.pasteCellsAction = PasteCellsAction(self)
        self.addAction(self.pasteCellsAction)
        self.cutCellsAction = CutCellsAction(self)
        self.addAction(self.cutCellsAction)

        #self.sep_rowactions = QAction(self)
        self.sep_rowactions = QAction(" ", self)
        self.sep_rowactions.setSeparator(True)
        self.addAction(self.sep_rowactions)

        self.insertRowAction = InsertRowAction(self)
        self.addAction(self.insertRowAction)
        self.deleteRowsAction = DeleteRowsAction(self)
        self.addAction(self.deleteRowsAction)

        #self.sep_colactions = QAction(self)
        self.sep_colactions = QAction(" ", self)
        self.sep_colactions.setSeparator(True)
        self.addAction(self.sep_colactions)

        self.insertColumnAction = InsertColumnAction(self)
        self.addAction(self.insertColumnAction)
        self.deleteColumnsAction = DeleteColumnsAction(self)
        self.addAction(self.deleteColumnsAction)

    def setup(self, colheaders = None, rowheaders = None,
            undo_redo = False, cut = False, paste = False,
            row_add_del = False, column_add_del = False,
            on_changed = None):
        """Inizialize the table.
        Only the copy action is enabled by default.
        If column headers are provided, adding/deleting columns is forbidden.
        If row headers are provided, adding/deleting rows is forbidden.

        :param [str] colheaders: list of column headers
        :param [str] rowheaders: list of row headers
        :param bool undo_redo: Enable undo/redo actions
        :param bool cut: Enable cut action
        :param bool paste: Enable paste action
        :param bool row_add_del: Enable adding/deleting a table row
        :param bool col_add_del: Enable adding/deleting a table column
        :param fn on_changed: Callback(bool) indicating change of
                "modified" status
        """
        self.on_changed = on_changed
        self.colheaders = colheaders
        self.rowheaders = rowheaders
        if colheaders:
            if column_add_del:
                raise Bug("Changing number of columns is not permitted"
                        " if column headers are provided")
            self.setColumnCount(len(colheaders))
            self.setHorizontalHeaderLabels(colheaders)
        if rowheaders:
            if row_add_del:
                raise Bug("Changing number of rows is not permitted"
                        " if row headers are provided")
            self.setRowCount(len(rowheaders))
            self.setVerticalHeaderLabels(rowheaders)
        # Enable desired actions
        self.undoredo.enable(undo_redo)

        self.cutCellsAction.setVisible(cut)
#        self.cutCellsAction.setEnabled(cut)
        self.pasteCellsAction.setVisible(paste)
#        self.pasteCellsAction.setEnabled(paste)
        self.sep_rowactions.setVisible(row_add_del)
        self.insertRowAction.setVisible(row_add_del)
#        self.insertRowAction.setEnabled(row_add_del)
        self.deleteRowsAction.setVisible(row_add_del)
#        self.deleteRowsAction.setEnabled(row_add_del)
        self.sep_colactions.setVisible(column_add_del)
        self.insertColumnAction.setVisible(column_add_del)
#        self.insertColumnAction.setEnabled(column_add_del)
        self.deleteColumnsAction.setVisible(column_add_del)
#        self.deleteColumnsAction.setEnabled(column_add_del)
        #
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        #
        self.set_change_report()
        self.cellChanged.connect(self.cell_changed)
        self.cellClicked.connect(self.activated)
        self.cellActivated.connect(self.newline_press)

    def init0(self, rows, columns):
        """Set the initial number of rows and columns and check that
        this is not in conflict with headers, if these have been set.
        """
        self.reset_modified(clear = True)
        self.clearContents()
        if self.colheaders:
            if columns != len(self.colheaders):
                raise Bug("Number of columns doesn't match header list")
        else:
            self.setColumnCount(columns)
        if self.rowheaders:
            if rows != len(self.rowheaders):
                raise Bug("Number of rows doesn't match header list")
        else:
            self.setRowCount(rows)

    def init_data(self, data):
        """Set the initial table data from a (complete) list of lists
        of strings.
        """
        def dummy(*args):   # Don't report data changes
            pass
        #+
        rows = len(data)
        columns = len(data[0])
        self.init0(rows, columns)
        # Disable change reporting
        self.set_change_report(dummy)
        # Enter data
        self.table_data = []
        data_model = self.model()
        for r in range(rows):
            self.table_data.append([''] * columns)
            for c in range(columns):
                val = data[r][c]
                #print("SET", r, c, repr(val))
                if isinstance(val, str):
                    if val:
                        data_model.setData(data_model.index(r, c), val)
                else:
                    raise Bug("Only string data is accepted")
        # Enable change reporting
        self.set_change_report()

    def init_sparse_data(self, rows, columns, data_list):
        """Set the initial table data from a list of cell values.
        data_list is a list of tuples: [(row, column, value), ... ].
        All other cells are left empty.
        """
        def dummy(*args):   # Don't report data changes
            pass
        #+
        self.init0(rows, columns)
        # Disable change reporting
        self.set_change_report(dummy)
        # Enter data
        self.table_data = [[''] * columns for r in range(rows)]
        data_model = self.model()
        for r, c, val in data_list:
            if isinstance(val, str):
                if val:
                    data_model.setData(data_model.index(r, c), val)
            else:
                raise Bug("Only string data is accepted")
        # Enable change reporting
        self.set_change_report()

    def row_count(self):
        return self.model().rowCount()

    def column_count(self):
        return self.model().columnCount()

    def _get_text(self, row, col):
        """Convenience method for reading a cell from the QTableWidget.
        """
        data_model = self.model()
        return data_model.data(data_model.index(row, col)) or ''

    def set_text(self, row, col, text):
        """Convenience method for writing a cell, first to the QTableWidget,
        then – indirectly – to <self.table_data>.
        """
        old = self.table_data[row][col]
        if text != old:
            data_model = self.model()
            data_model.setData(data_model.index(row, col), text)
            # This will also (via method <cell_changed>) update <table_data>

    def read_block(self, top, left, width, height):
        """Read a block of data from the table.
        Return list of rows, each row is a list of cell values.
        """
        if width == 0 or height == 0:
            raise Bug("Can't read block with no dimensions")
        r1 = top + height
        c1 = left + width
        rows = []
        while top < r1:
            rowdata = []
            row = self.table_data[top]
            c = left
            while c < c1:
                rowdata.append(row[c])
                c += 1
            top += 1
            rows.append(rowdata)
        return rows

    def insertRow(self, row, data = None):
        # Consistency check
        ncols = self.column_count()
        l = 0 if not self.table_data else len(self.table_data[0])
        if l != ncols:
            raise Bug("insertRow: table width mismatch")
        newrow = [''] * ncols
        self.table_data.insert(row, newrow)
        super().insertRow(row)
        if data is None:
            self.add_change(Change.ADD_ROW, row)
        else:
            # There should only be data when undoing
            if len(data) != ncols:
                raise Bug("insertRow: data length doesn't match table width")
            self.paste_block(row, 0, [data])

    def insertColumn(self, column, data = None):
        # Consistency check
        nrows = self.row_count()
        if len(self.table_data) != nrows:
            raise Bug("insertColumn: table height mismatch")
        for row in self.table_data:
            row.insert(column, '')
        super().insertColumn(column)
        if data is None:
            self.add_change(Change.ADD_COL, column)
        else:
            # There should only be data when undoing
            if len(data) != nrows:
                raise Bug("insertColumn: data length doesn't match table height")
            self.paste_block(0, column, [[data[row]] for row in range(nrows)])

    def removeRow(self, row):
        rowdata = self.table_data.pop(row)
        super().removeRow(row)
        self.add_change(Change.DEL_ROW, (row, rowdata))

    def removeColumn(self, column):
        coldata = [rowdata.pop(column) for rowdata in self.table_data]
        super().removeColumn(column)
        self.add_change(Change.DEL_COL, (column, coldata))

    def cell_changed(self, row, col):
        """This is called automatically whenever a cell's content changes.
        It is not called when a row or column is inserted or deleted.
        """
        text = self._get_text(row, col)
        old = self.table_data[row][col]
        if old != text:
            self.table_data[row][col] = text
            self.add_change(Change.CELL, (row, col, old, text))

    def set_change_report(self, handler = None):
        if handler:
            self.add_change = handler
        else:
            self.add_change = self.undoredo.change

    def activated(self, row, col):
        # This is called when a cell is left-clicked or when the (single)
        # selected cell has "Return/Newline" pressed.
        print("ACTIVATED:", row, col)

    def newline_press(self, row, col):
        #if self.get_selection()[0] == 1:
        if self.get_selection()[0] <= 1:
            self.activated(row, col)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and \
                QApplication.keyboardModifiers() & Qt.ControlModifier:
            self.clearSelection()
            self.setCurrentItem(None)
            return
#TODO?
#PySide6:        item = self.itemAt(event.position().toPoint())
        item = self.itemAt(event.pos())

        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if self.state() != self.EditingState:
            key = event.key()
            if key == Qt.Key_Delete:
                if self.cut_selection() is None:
                    self.takeItem(self.currentRow(), self.currentColumn())
                return # in this case don't call the base class method
        super().keyPressEvent(event)

    def cut_selection(self):
        """Cut the selected range, returning the contents as "tsv".
        The changed cells are reported as a single item, possibly a list.
        """
        def gather(chtype, change):
            if chtype != Change.CELL:
                raise Bug("Cutting block should only cause cell changes")
            change_list.append(change)
        #+
        n, t, l, w, h = self.get_selection()
        if n == 0:
            return None
        if n == 1:
            item = self.takeItem(t, l)
            if item:
                return item.text()
            return ''
        block = self.read_block(t, l, w, h)
        change_list = []
        self.set_change_report(gather)
        r1 = t + h
        c1 = l + w
        while t < r1:
            c = l
            while c < c1:
                self.takeItem(t, c)
                c += 1
            t += 1
        self.set_change_report()
        # Report changes as a list – only cells which actually changed
        if change_list:
            if len(change_list) == 1:
                self.add_change(Change.CELL, change_list[0])
            else:
                self.add_change(Change.BLOCK, change_list)
        return table2tsv(block)

    def get_selection(self):
        """Return the current selection:
            (number of cells, top row, left column, width, height)
        """
        selected = self.selectedRanges()
        if len(selected) > 1:
            raise Bug("Multiple selection is not supported")
        if not selected:
            return (0, -1, -1, 0, 0)
        selrange = selected[0]
        l = selrange.leftColumn()
        w = selrange.rightColumn() - l + 1
        t = selrange.topRow()
        h = selrange.bottomRow() - t + 1
        return (w * h, t, l, w, h)

    def paste_block(self, top, left, block):
        """The block must be a list of lists of strings.
        """
        def gather(chtype, change):
            if chtype != Change.CELL:
                raise Bug("Pasting block should only cause cell changes")
            change_list.append(change)
        #+
        change_list = []
        self.set_change_report(gather)
        for row in block:
            c = left
            for cell in row:
                self.set_text(top, c, cell)
                c += 1
            top += 1
        self.set_change_report()
        # Report changes as a list – only cells which actually changed
        if change_list:
            if len(change_list) == 1:
                self.add_change(Change.CELL, change_list[0])
            else:
                self.add_change(Change.BLOCK, change_list)

    def set_modified(self, mod):
        """Whenever a change away from the "initial" table data is made,
        this is called with <mod> true. When undo/redo is enabled, it is
        also possible to return to the initial data state. In that case
        <mod> is false.
        This method keeps the <self.__modified> flag up-to-date. When
        a change to that flag occurs here, the callback <self.on_changed>
        will be called with the new flag value.
        It is also possible to specify a new "initial" state: see the
        method <self.reset_modified>.
        """
        if mod != self.__modified:
            self.__modified = mod
            if self.on_changed:
                self.on_changed(mod)

    def reset_modified(self, clear = False):
        """Reset the "starting point" for registering changes.
        This should be called when a table is saved, so that an
        unmodified state is reasserted. It can also be called after
        initializing the table data (e.g. from a file).
        If <clear> is true, the undo list is cleared (if there is one).
        Otherwise the undo list is untouched, so that an undo operation
        can return to a state previous to the new initial state.
        """
        self.__modified = False
        self.undoredo.mark0(clear)


class VerticalTextDelegate(QStyledItemDelegate):
    """A <QStyledItemDelegate> for vertical text. It can be set on a
    row or column (or the whole table), not on single cells.
    """
    def paint(self, painter, option, index):
        optionCopy = QStyleOptionViewItem(option)
        rectCenter = QPointF(QRectF(option.rect).center())
        painter.save()
        painter.translate(rectCenter.x(), rectCenter.y())
        painter.rotate(-90.0)
        painter.translate(-rectCenter.x(), -rectCenter.y())
        optionCopy.rect = painter.worldTransform().mapRect(option.rect)

        # Call the base class implementation
        super().paint(painter, optionCopy, index)

        painter.restore()

    def sizeHint(self, option, index):
        val = QSize(super().sizeHint(option, index))
        return QSize(val.height(), val.width())


if __name__ == "__main__":
    app = QApplication([])
    def is_modified1(mod):
        print("MODIFIED1:", mod)
    def is_modified2(mod):
        print("MODIFIED2:", mod)

    cols = ["Column %02d" % n for n in range(10)]
    rows = ["Row %02d" % n for n in range(7)]
    tablewidget = EdiTableWidget()
    tablewidget.setup(colheaders = cols, rowheaders = rows,
            on_changed = is_modified1)

    tablewidget.setWindowTitle("EdiTableWidget")

    tablewidget.setItemDelegateForRow(2, VerticalTextDelegate())

    sparse_data = []
    r, c = 2, 3
    sparse_data.append((r, c, 'R%02d:C%02d' % (r, c)))
    r, c = 1, 4
    sparse_data.append((r, c, 'R%02d:C%02d' % (r, c)))
    tablewidget.init_sparse_data(len(rows), len(cols), sparse_data)

    tablewidget.resizeRowToContents(1)
    tablewidget.resizeRowToContents(2)
    tablewidget.resizeColumnToContents(3)
    tablewidget.resize(600, 400)
    tablewidget.show()

    tw2 = EdiTableWidget()
    tw2.setup(undo_redo = True, cut = True, paste = True,
            row_add_del = True, column_add_del = True,
            on_changed = is_modified2)
    tw2.init_data([["1", "2", "3", "4"], [""] * 4])
    tw2.resize(400, 300)
    tw2.show()

    app.exec()
