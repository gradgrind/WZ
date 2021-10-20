# -*- coding: utf-8 -*-

"""
ui/editable.py

Last updated:  2021-10-20

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

### Messages

#_CLEARSELECTION = "Clear selection"
_CLEARSELECTION = "Auswahl aufheben"
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
#_TTCUTSELECTION = "Cut selection, placing cell values in the clipboard."
_TTCUTSELECTION = "Auswahl ausschneiden und in die Zwischanablage kopieren."
#_CUTSELECTION = "Cut selection"
_CUTSELECTION = "Auswahl ausschneiden"
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
#_INSERTROWFAIL = "One – and only one – row must be selected to insert" \
#        " a new one"
_INSERTROWFAIL = "Um eine neue Zeile einzufügen, muss genau eine" \
        " ausgewählt sein"
#_DELETEROWS = "Delete Rows"
_DELETEROWS = "Zeilen löschen"
#_TTDELETEROWS = "Delete selected Rows"
_TTDELETEROWS = "ausgewählte Zeilen löschen"
#_DELETEROWSFAIL = "No rows are selected"
_DELETEROWSFAIL = "Keine ausgewählten Zeilen"
#_INSERTCOLUMN = "Insert Column"
_INSERTCOLUMN = "Spalte einfügen"
#_TTINSERTCOLUMN = "Insert Column"
_TTINSERTCOLUMN = "Spalte einfügen nach der aktuellen Spalte"
#_INSERTCOLUMNFAIL = "One – and only one – column must be selected to" \
#        " insert a new one"
_INSERTCOLUMNFAIL = "Um eine neue Spalte einzufügen, muss genau eine" \
        " ausgewählt sein"
#_DELETECOLUMNS = "Delete Columns"
_DELETECOLUMNS = "Spalten löschen"
#_TTDELETECOLUMNS = "Delete selected Columns"
_TTDELETECOLUMNS = "ausgewählte Spalten löschen"
#_DELETECOLUMNSFAIL = "No columns are selected"
_DELETECOLUMNSFAIL = "Keine ausgewählten Spalten"
#_UNDO = "Undo"
_UNDO = "Rückgängig"
#_TTUNDO = "Undo last change"
_TTUNDO = "Letzte Änderung rückgängig machen"
#_REDO = "Redo"
_REDO = "Wiederherstellen"
#_TTREDO = "Redo"
_TTREDO = "Letzte Änderung wiederherstellen"

########################################################################

from PySide6.QtWidgets import QApplication, \
        QTableView, QTableWidget, QMessageBox, \
        QStyledItemDelegate, QStyleOptionViewItem
from PySide6.QtCore import Qt, QPointF, QRectF, QSize, Signal
from PySide6.QtGui import QAction, QKeySequence, QShortcut

### -----

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
        """
        selected = self.table.get_selection()
        if selected[0] and selected[4] == 1:
            self.table.insertRow(selected[1] + 1)
        else:
            msgBox = QMessageBox(parent = self.table)
            msgBox.setText(_INSERTROWFAIL)
            msgBox.exec()


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
        """
        selected = self.table.get_selection()
        if selected[0] and selected[3] == 1:
            self.table.insertColumn(selected[2] + 1)
        else:
            msgBox = QMessageBox(parent = self.table)
            msgBox.setText(_INSERTCOLUMNFAIL)
            msgBox.exec()


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
        """Delete the selected rows.
        """
        selected = self.table.get_selection()
        if selected[0]:
            r0 = selected[1]
            r = r0 + selected[4]
            while r > r0:
                r -= 1
                self.table.removeRow(r)
        else:
            msgBox = QMessageBox(parent = self.table)
            msgBox.setText(_DELETEROWSFAIL)
            msgBox.exec()


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
            c0 = selected[2]
            c = c0 + selected[3]
            while c > c0:
                c -= 1
                self.table.removeColumn(c)
        else:
            msgBox = QMessageBox(parent = self.table)
            msgBox.setText(_DELETECOLUMNSFAIL)
            msgBox.exec()


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

    def change(self, row, column, olddata, newdata):
        if self.enabled and not self.blocked:
            del(self.changes[self.index:])
            self.changes.append((row, column, olddata, newdata))
            self.index = len(self.changes)

    def undo(self):
        if self.enabled and self.index > 0:
            self.blocked = True
            self.index -= 1
            row, column, olddata, newdata = self.changes[self.index]
            if row < 0:
                # insert/delete column
                if olddata is None:
                    # undo "insert column"
                    self.table.removeColumn(column)
                else:
                    # undo "delete column"
                    self.table.insertColumn(column, data = olddata)
            elif column < 0:
                # insert/delete row
                if olddata is None:
                    # undo "insert row"
                    self.table.removeRow(row)
                else:
                    # undo "delete row"
                    self.table.insertRow(row, data = olddata)
            else:
                self.table.set_text(row, column, olddata)
            self.blocked = False
            self.table.set_modified(self.index != self.index0)

#TODO: not working
    def redo(self):
        if self.enabled and self.index < len(self.changes):
            self.blocked = True
            row, column, olddata, newdata = self.changes[self.index]
            self.index += 1
            if row < 0:
                # insert/delete column
                if olddata is None:
                    # redo "insert column"
                    self.table.insertColumn(column, data = olddata)
                else:
                    # redo "delete column"
                    self.table.removeColumn(column)
            elif column < 0:
                # insert/delete row
                if olddata is None:
                    # redo "insert row"
                    self.table.insertRow(row, data = olddata)
                else:
                    # redo "delete row"
                    self.table.removeRow(row)
            else:
                self.table.set_text(row, column, olddata)
            self.blocked = False
            self.table.set_modified(self.index != self.index0)


class EdiTableWidget(QTableWidget):
    modified = Signal(bool)
    #+
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


#TODO: Make <setup> specify the basic parameters of the table, but not
# the rows and columns – unless row- or column-headers are specified,
# then the one size or other should probably be fixed.

    def setup(self, rows, columns, colheaders = None, rowheaders = None,
            undo_redo = False, cut = False, paste = False,
            row_add_del = False, column_add_del = False):
        """Inizialize the table.
        Only the copy action is enabled by default.

        :param int rows: number of rows
        :param int columns: number of columns
        :param [str] colheaders: list of column headers
        :param [str] rowheaders: list of row headers
        :param bool undo_redo: Enable undo/redo actions
        :param bool cut: Enable cut action
        :param bool paste: Enable paste action
        :param bool row_add_del: Enable adding/deleting a table row
        :param bool col_add_del: Enable adding/deleting a table column
        :param fn on_changed: Callback(row, col, text) for changed cells
        """
        self.setRowCount(rows)
        self.setColumnCount(columns)
        self.clear()
        if colheaders:
            if len(colheaders) != columns:
                raise Bug("Wrong number of column headers")
            self.setHorizontalHeaderLabels(colheaders)
        if rowheaders:
            if len(rowheaders) != rows:
                raise Bug("Wrong number of row headers")
            self.setVerticalHeaderLabels(rowheaders)
        # Initially no data, set up the data table:
        self.table_data = [[''] * columns for r in range(rows)]
        # Enable desired actions
        self.reset_modified(clear = True)
        self.undoredo.enable(undo_redo)
        self.cutCellsAction.setVisible(cut)
        self.cutCellsAction.setEnabled(cut)
        self.pasteCellsAction.setVisible(paste)
        self.pasteCellsAction.setEnabled(paste)
        self.sep_rowactions.setVisible(row_add_del)
        self.insertRowAction.setVisible(row_add_del)
        self.insertRowAction.setEnabled(row_add_del)
        self.deleteRowsAction.setVisible(row_add_del)
        self.deleteRowsAction.setEnabled(row_add_del)
        self.sep_colactions.setVisible(column_add_del)
        self.insertColumnAction.setVisible(column_add_del)
        self.insertColumnAction.setEnabled(column_add_del)
        self.deleteColumnsAction.setVisible(column_add_del)
        self.deleteColumnsAction.setEnabled(column_add_del)
        #
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        #
        self.set_change_report()
        self.cellChanged.connect(self.cell_changed)
        self.cellClicked.connect(self.activated)
        self.cellActivated.connect(self.newline_press)

    def init_data(self, data):
        """Set the initial table data from a list of lists of strings.
        """
#TODO
        print("set_data: TBI")

    def init_sparse_data(self, rows, columns, data_list):
#TODO
        print("set_sparse_data: TBI")

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
            self.add_change(row, -1, None, newrow)
        else:
            if len(data) != ncols:
                raise Bug("insertRow: data length doesn't match table width")
            for column in range(ncols):
                self.set_text(row, column, data[column])

    def insertColumn(self, column, data = None):
        # Consistency check
        nrows = self.row_count()
        if len(self.table_data) != nrows:
            raise Bug("insertColumn: table height mismatch")
        for row in self.table_data:
            row.insert(column, '')
        super().insertColumn(column)
        if data is None:
            self.add_change(-1, column, None, [''] * self.row_count())
        else:
            if len(data) != nrows:
                raise Bug("insertColumn: data length doesn't match table height")
            for row in range(nrows):
                self.set_text(row, column, data[row])

    def removeRow(self, row):
        rowdata = self.table_data.pop(row)
        super().removeRow(row)
        self.add_change(row, -1, '\t'.join(rowdata), None)

    def removeColumn(self, column):
        coldata = [rowdata.pop(column) for rowdata in self.table_data]
        super().removeColumn(column)
        self.add_change(-1, column, '\t'.join(coldata), None)

    def cell_changed(self, row, col):
        """This is called automatically whenever a cell's content changes.
        It is not called when a row or column is inserted or deleted.
        """
        text = self._get_text(row, col)
        old = self.table_data[row][col]
        if old != text:
            self.table_data[row][col] = text
            self.add_change(row, col, old, text)
#            self.undoredo.add_change(row, col, old, text)

#TODO!
# Changes:
# - single cell
# - add line (empty)
# - add line with content? (could be useful for undo/redo)
# - remove line (with content)
# - remove line ignoring content? (could be useful for undo/redo)
# - cut/delete block
# - paste block
### The last two should be provided separately from individual cell
### changes to ease undo/redo of cut/paste.
### Changes as a result of undo/redo are not added to the undo/redo stack.
### There should be a modified callback (rather than a signal), perhaps
### associated directly with a flag. It will be handled a bit differently
### when undo/redo is enabled.
### Perhaps there should be a one-off setup method, which selects the
### enabled features. If it is better as a once-only setup, there could
### be a trap when it is called a second time. Note that, using methods
### actions() and removeAction() it would be possible to remove all the
### added actions on the table ... but disabling/enabling the desired
### ones might be better.
### Ideally actions which in the present state don't do anything should
### be disabled. Invisible seems to imply disabled.
### A separate init method would set the initial size and initial
### contents – without causing a modified callback.
### At present deleting a row/column also deletes the header, without
### retaining it for an undo operation. Also editing a header is not
### supported. If this remains so, it would be logical to only allow
### headers if insert/delete is not allowed.

### There is a signal on QItemSelectionModel:
###    selectionChanged(const QItemSelection &selected, const QItemSelection &deselected)


    def set_change_report(self, handler = None):
        if handler:
            self.add_change = handler
        else:
            self.add_change = self.add_change0

    def add_change0(self, row, column, olddata, newdata):
        """Add each change to a sort of stack for undo/redo support.
        Normally a single cell will be changed, but it is possible to
        insert or delete a whole row or column.
        To insert/delete a column, row is -1.
        To insert/delete a row, column is -1.
        Deleted rows/columns are supplied as tab-separated-value strings.
        """
        self.undoredo.change(row, column, olddata, newdata)
        self.set_modified(True)

#TODO
        print("CHANGE:", row, column, repr(olddata), repr(newdata))





    def activated(self, row, col):
        # This is called when a cell is left-clicked or when the (single)
        # selected cell has "Return/Newline" pressed.
        print("ACTIVATED:", row, col)

    def newline_press(self, row, col):
        #if self.get_selection()[0] == 1:
        if self.get_selection()[0] <= 1:
            self.activated(row, col)

#    def vheader_popup(self, point):
#        action = self.header_menu.exec(self.mapToGlobal(point))
#        if action:
#            i = self.verticalHeader().logicalIndexAt(point)
##            print("VHEADER:", i)
#            action.run(i)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and \
                QApplication.keyboardModifiers() & Qt.ControlModifier:
            self.clearSelection()
            self.setCurrentItem(None)
            return
        item = self.itemAt(event.position().toPoint())
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if self.state() != self.EditingState:
            key = event.key()
            if key == Qt.Key_Delete:
                if self.cut_selection() is None:
                    self.takeItem(self.currentRow(), self.currentColumn())
                return # in this case don't call base class method
        super().keyPressEvent(event)

    def cut_selection(self):
        """Cut the selected range, returning the contents as "tsv".
        The changed cells are reported as a single item, possibly a list.
        """
        def gather(*args):
            change_list.append(args)
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
#TODO?
        # Report changes as a list – only cells which actually changed
        if change_list:
            if len(change_list) == 1:
                self.add_change(*change_list[0])
            else:
                self.add_change(-1, -1, change_list, None)
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
        def gather(*args):
            change_list.append(args)
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
#TODO?
        # Report changes as a list – only cells which actually changed
        if change_list:
            if len(change_list) == 1:
                self.add_change(*change_list[0])
            else:
                self.add_change(-1, -1, change_list, None)

    def set_modified(self, mod):
        if mod != self.__modified:
            self.__modified = mod
            self.modified.emit(mod)

    def reset_modified(self, clear = False):
        """Reset the "starting point" for registering changes.
        This should be called when a table is saved, so that an
        unmodified state is reasserted. It can also be called after
        initializing the table data (e.g. from a file).
        If <clear> is true, the undo list is cleared (if there is one).
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
    def is_modified(mod):
        print("MODIFIED:", mod)

    cols = ["Column %02d" % n for n in range(10)]
    rows = ["Row %02d" % n for n in range(7)]
    tablewidget = EdiTableWidget()
    tablewidget.setup(len(rows), len(cols),
            colheaders = cols, rowheaders = rows,
            undo_redo = True, cut = True, paste = True,
            row_add_del = True, column_add_del = True)
    tablewidget.modified.connect(is_modified)

    tablewidget.setWindowTitle("TableWidget")

    tablewidget.setItemDelegateForRow(2, VerticalTextDelegate())

# Note that inserting and deleting rows will make a mess of the row
# headers set above

    r, c = 2, 3
    tablewidget.set_text(r, c, 'R%02d:C%02d' % (r, c))
    r, c = 1, 4
    tablewidget.set_text(r, c, 'R%02d:C%02d' % (r, c))

    tablewidget.resizeRowToContents(1)
    tablewidget.resizeRowToContents(2)
    tablewidget.resizeColumnToContents(3)

    tablewidget.reset_modified(True)

    tablewidget.resize(600, 400)
    tablewidget.show()
    app.exec()
