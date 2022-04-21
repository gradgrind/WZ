"""
ui/editable.py

Last updated:  2022-04-21

An editable table widget using QTableWidget as base class. Only text
cells are handled.
Originally inspired by "TableWidget.py" from the "silx" project (www.silx.org),
thanks to P. Knobel, but it is now very different.

=+LICENCE=================================
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

=-LICENCE=================================
"""

#TODO: I might want to handle editing of non-editable items ...

### Messages

# _SELECT_ALL = "Select all"
_SELECT_ALL = "Alles auswählen"
# _TTSELECT_ALL = "Select all cells of the table"
_TTSELECT_ALL = "Ganze Tabelle auswählen"
# _UNSELECT = "Unselect"
_UNSELECT = "Auswahl zurücksetzen"
# _TTUNSELECT = "Clear the selection"
_TTUNSELECT = "keine Zellen sollen ausgewählt sein"
# _TOO_MANY_ROWS = "Too many rows to insert"
_TOO_MANY_ROWS = "Einfügen nicht möglich – zu viele Zeilen"
# _TOO_MANY_COLUMNS = "Too many columns to insert"
_TOO_MANY_COLUMNS = "Einfügen nicht möglich – zu viele Spalten"
# _BAD_PASTE_RANGE = "Clipboard data dimensions incompatible with selected" \
#        " range"
_BAD_PASTE_RANGE = (
    "Die Dimensionen der einzufügenden Daten sind nicht"
    " kompatibel mit dem ausgewählten Bereich."
)
# _PASTE_PROTECTED = "Some data could not be inserted because of" \
#        " write-protected cells.
_PASTE_PROTECTED = "Zellen sind schreibgeschützt – einfügen nicht möglich"
# _CUTSELECTION = "Cut selection"
_CUTSELECTION = "Auswahl ausschneiden"
# _TTCUTSELECTION = "Cut selection, placing cell values in the clipboard."
_TTCUTSELECTION = "Auswahl ausschneiden und in die Zwischanablage kopieren."
# _COPYSELECTION = "Copy selection"
_COPYSELECTION = "Auswahl kopieren"
# _TTCOPYSELECTION = "Copy selected cells into the clipboard."
_TTCOPYSELECTION = "Ausgewählte Zellen in die Zwischanablage kopieren."
# _COPYFAIL = "No cells are selected"
_COPYFAIL = "Keine ausgewählten Zellen"
# _PASTE = "Paste"
_PASTE = "Einfügen"
# _TTPASTE = "Paste data." \
#         " The selected cell is the top-left corner of the paste area."
_TTPASTE = (
    "Daten einfügen. Die ausgewählte Zelle ist oben links"
    " im Bereich, der eingefügt wird."
)
# _INSERTROW = "Insert Row(s)"
_INSERTROW = "Zeile(n) einfügen"
# _TTINSERTROW = "Insert Row(s)"
_TTINSERTROW = "Zeile(n) einfügen nach der aktuellen Zeile"
# _ROWOPFAIL = "No rows selected"
_ROWOPFAIL = "Keine Zeilen sind ausgewählt"
# _DELETEROWS = "Delete Row(s)"
_DELETEROWS = "Zeile(n) löschen"
# _TTDELETEROWS = "Delete selected Row(s)"
_TTDELETEROWS = "ausgewählte Zeilen löschen"
# _DELETEROWSFAIL = "Deleting all rows is not permitted"
_DELETEROWSFAIL = "Das Löschen aller Zeilen ist nicht zulässig"
# _INSERTCOLUMN = "Insert Column(s)"
_INSERTCOLUMN = "Spalte(n) einfügen"
# _TTINSERTCOLUMN = "Insert Column(s)"
_TTINSERTCOLUMN = "Spalte(n) einfügen nach der aktuellen Spalte"
# _DELETECOLUMNS = "Delete Column(s)"
_DELETECOLUMNS = "Spalte(n) löschen"
# _TTDELETECOLUMNS = "Delete selected Column(s)"
_TTDELETECOLUMNS = "Ausgewählte Spalte(n) löschen"
# _DELETECOLUMNSFAIL = "Deleting all columns is not permitted"
_DELETECOLUMNSFAIL = "Das Löschen aller Spalten ist nicht zulässig"
# _COLUMNOPFAIL = "No columns selected"
_COLUMNOPFAIL = "Keine Spalten sind ausgewählt"
# _UNDO = "Undo"
_UNDO = "Rückgängig"
# _TTUNDO = "Undo the last change"
_TTUNDO = "Die letzte Änderung rückgängig machen"
# _REDO = "Redo"
_REDO = "Wiederherstellen"
# _TTREDO = "Redo the last undone change"
_TTREDO = "Die letzte rückgängig gemachte Änderung wiederherstellen"
# _VALIDATION_ERROR = "Validation Error"
_VALIDATION_ERROR = "Ungültiger Wert"
# _WARNING = "Warning"
_WARNING = "Warnung"

########################################################################

from qtpy.QtWidgets import (
    QApplication,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)
from qtpy.QtCore import Qt, QPointF, QRectF, QSize
from qtpy.QtGui import QKeySequence
from qtpy.QtWidgets import QAction  # in Qt6 it is in QtGui


class Bug(Exception):
    pass


# Types of changes which are to be recorded by undo/redo function.
Change_CELL = 1
Change_BLOCK = 2
Change_ADD_ROW = 3
Change_DEL_ROW = 4
Change_ADD_COL = 5
Change_DEL_COL = 6
# For multiple row/column changes:
Change_GROUP = 7
Change_END_GROUP = 8
# As a starting number for extensions:
Change_X = 9

### -----


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
    rows = text.split("\n")
    # 'splitlines' can't be used as it loses trailing empty lines.
    table_data = []
    max_len = 0
    for row in rows:
        line = row.split("\t")
        l = len(line)
        if l > max_len:
            max_len = l
        table_data.append((line, l))
    result = []
    for line, l in table_data:
        if l < max_len:
            line += [""] * (max_len - l)
        result.append(line)
    return result


def table2tsv(table):
    """Represent a list of lists of strings (a "table") as a "tsv"
    (tab separated value) string.
    """
    return "\n".join(["\t".join(row) for row in table])


class RangeError(Exception):
    pass


class UndoRedo:
    def __init__(self, table):
        self.table = table
        self.blocked = False

    def mark0(self, clear):
        if clear:
            self.changes = []
            self.table.undoAction.setEnabled(False)
            self.table.redoAction.setEnabled(False)
            self.index = 0
        self.index0 = self.index

    def enable(self, en):
        self.mark0(True)
        self.enabled = en
        self.table.sep_undoredo.setVisible(en)
        self.table.undoAction.setVisible(en)
        self.table.redoAction.setVisible(en)
        self.table.undoAction.setEnabled(False)
        self.table.redoAction.setEnabled(False)

    def change(self, chtype, change):
        #print("CHANGE:", chtype, change, self.enabled, self.blocked)
        if self.enabled and not self.blocked:
            # print("CHANGE:", chtype, change)
            del self.changes[self.index :]
            self.changes.append((chtype, change))
            self.table.undoAction.setEnabled(True)
            self.index = len(self.changes)

    def undo(self):
        def do_undo():
            if chtype is Change_ADD_COL:
                self.table.removeColumn(change)
            elif chtype is Change_DEL_COL:
                self.table.insertColumn(change[0], data=change[1])
            elif chtype is Change_ADD_ROW:
                self.table.removeRow(change)
            elif chtype is Change_DEL_ROW:
                self.table.insertRow(change[0], data=change[1])
            elif chtype is Change_BLOCK:
                for _change in change:  # <change> is here a list
                    self.table.set_text(*_change[:3])
            elif chtype is Change_CELL:
                self.table.set_text(*change[:3])
            elif not self.table.undoredo_extension(True, chtype, change):
                raise Bug(f"Invalid Undo-change: {chtype}")

        if self.enabled and self.index > 0:
            self.blocked = True
            self.index -= 1
            chtype, change = self.changes[self.index]
            if chtype is Change_END_GROUP:
                while True:
                    self.index -= 1
                    chtype, change = self.changes[self.index]
                    if chtype is Change_GROUP:
                        break
                    do_undo()
            else:
                do_undo()
            self.blocked = False
            if self.index == 0:
                self.table.undoAction.setEnabled(False)
            self.table.redoAction.setEnabled(True)

    def redo(self):
        def do_redo():
            if chtype is Change_ADD_COL:
                self.table.insertColumn(change)
            elif chtype is Change_DEL_COL:
                self.table.removeColumn(change[0])
            elif chtype is Change_ADD_ROW:
                self.table.insertRow(change)
            elif chtype is Change_DEL_ROW:
                self.table.removeRow(change[0])
            elif chtype is Change_BLOCK:
                for _change in change:  # <change> is here a list
                    self.table.set_text(*_change[:2], _change[3])
            elif chtype is Change_CELL:
                self.table.set_text(*change[:2], change[3])
            elif not self.table.undoredo_extension(False, chtype, change):
                raise Bug(f"Invalid Redo-change: {chtype}")

        if self.enabled and self.index < len(self.changes):
            self.blocked = True
            chtype, change = self.changes[self.index]
            self.index += 1
            if chtype is Change_GROUP:
                while True:
                    chtype, change = self.changes[self.index]
                    self.index += 1
                    if chtype is Change_END_GROUP:
                        break
                    do_redo()
            else:
                do_redo()
            self.blocked = False
            if self.index == len(self.changes):
                self.table.redoAction.setEnabled(False)
            self.table.undoAction.setEnabled(True)


class EdiTableWidget(QTableWidget):
    """This adds features to the standard table widget and makes a
    number of assumptions about the usage – specifically to provide a
    useful base for a table editor dealing with string data only.
    """

    def new_action(
        self, text=None, icontext=None, tooltip=None, shortcut=None, function=None
    ):
        action = QAction(self)
        if text:
            action.setText(text)
        if icontext:
            action.setIconText(icontext)
        # The tooltip is not shown in a popup (context) menu ...
        if tooltip:
            if shortcut:
                tooltip += f" – [{shortcut.toString()}]"
            action.setToolTip(tooltip)
        # action.setStatusTip(
        # action.setIcon(
        if shortcut:
            action.setShortcut(shortcut)
        #            action.setShortcutContext(Qt.WidgetShortcut)
        if function:
            action.triggered.connect(function)
        self.addAction(action)
        return action

    def context_menu_spacer(self):
        # self.sep_rowactions = QAction(self)
        sep = QAction(" ", self)
        sep.setSeparator(True)
        self.addAction(sep)
        return sep

    def __on_selection_state_change(self, sel):
        # print("SELECTION " + ("ON" if sel else "EMPTY"))
        pass

    def undoredo_extension(self, undo, chtype, change):
        """Allows external undo/redo operations to be handled.
        OVERRIDE to use.
        """
        return False

    def __init__(self, parent=None,
            align_centre = False,
            on_selection_state_change=None):
        super().__init__(parent=parent)
        self.setItemPrototype(ValidatingWidgetItem())
        self.setSelectionMode(self.ContiguousSelection)
        self.has_selection = False
        self.align_centre = align_centre
        self.on_selection_state_change = (
            on_selection_state_change
            if on_selection_state_change
            else self.__on_selection_state_change
        )
        self.__modified = False

        ### Actions
        # QAction to select all cells.
        # This seems to override the built-in shortcut, but only if the
        # table "has keyboard focus".
        self.select_all = self.new_action(
            text=_SELECT_ALL,
            tooltip=_TTSELECT_ALL,
            shortcut=QKeySequence(Qt.CTRL + Qt.Key_A),
            function=self.selectAll,
        )

        # QAction to clear the selection.
        self.unselect = self.new_action(
            text=_UNSELECT,
            tooltip=_TTUNSELECT,
            shortcut=QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_A),
            function=self.clearSelection,
        )

        self.context_menu_spacer()

        # QAction to copy selected cells to clipboard.
        self.copyCellsAction = self.new_action(
            text=_COPYSELECTION,
            tooltip=_TTCOPYSELECTION,
            shortcut=QKeySequence(Qt.CTRL + Qt.Key_C),
            function=self.copyCellsToClipboard,
        )

        # QAction to paste clipboard at selected cell(s).
        self.pasteCellsAction = self.new_action(
            text=_PASTE,
            tooltip=_TTPASTE,
            shortcut=QKeySequence(Qt.CTRL + Qt.Key_V),
            function=self.pasteCellFromClipboard,
        )

        # QAction to cut selected cells to clipboard.
        self.cutCellsAction = self.new_action(
            text=_CUTSELECTION,
            tooltip=_TTCUTSELECTION,
            shortcut=QKeySequence(Qt.CTRL + Qt.Key_X),
            function=self.cutCellsToClipboard,
        )

        self.sep_rowactions = self.context_menu_spacer()

        # QAction to insert a row or rows of cells.
        self.insertRowAction = self.new_action(
            text=_INSERTROW,
            tooltip=_TTINSERTROW,
            shortcut=QKeySequence(Qt.CTRL + Qt.Key_N),
            function=self.insert_row,
        )

        # QAction to delete a row or rows of cells.
        self.deleteRowsAction = self.new_action(
            text=_DELETEROWS,
            tooltip=_TTDELETEROWS,
            shortcut=QKeySequence(Qt.CTRL + Qt.Key_U),
            function=self.delete_rows,
        )

        self.sep_colactions = self.context_menu_spacer()

        # QAction to insert a column or columns of cells.
        self.insertColumnAction = self.new_action(
            text=_INSERTCOLUMN,
            tooltip=_TTINSERTCOLUMN,
            shortcut=QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_N),
            function=self.insert_column,
        )

        # QAction to delete a column or columns of cells.
        self.deleteColumnsAction = self.new_action(
            text=_DELETECOLUMNS,
            tooltip=_TTDELETECOLUMNS,
            shortcut=QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_U),
            function=self.delete_columns,
        )

        self.sep_undoredo = self.context_menu_spacer()

        # QAction to undo last change
        self.undoredo = UndoRedo(self)
        self.undoAction = self.new_action(
            text=_UNDO,
            tooltip=_TTUNDO,
            shortcut=QKeySequence(Qt.CTRL + Qt.Key_Z),
            function=self.undoredo.undo,
        )

        # QAction to redo last undone change
        self.redoAction = self.new_action(
            text=_REDO,
            tooltip=_TTREDO,
            shortcut=QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_Z),
            function=self.undoredo.redo,
        )

    def setup(
        self,
        colheaders=None,
        rowheaders=None,
        undo_redo=False,
        cut=False,
        paste=False,
        row_add_del=False,
        column_add_del=False,
        on_changed=None,
    ):
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
                raise Bug(
                    "Changing number of columns is not permitted"
                    " if column headers are provided"
                )
            self.setColumnCount(len(colheaders))
            self.setHorizontalHeaderLabels(colheaders)
        if rowheaders:
            if row_add_del:
                raise Bug(
                    "Changing number of rows is not permitted"
                    " if row headers are provided"
                )
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
        self.deleteRowsAction.setVisible(row_add_del)
        self.sep_colactions.setVisible(column_add_del)
        self.insertColumnAction.setVisible(column_add_del)
        self.deleteColumnsAction.setVisible(column_add_del)
        self.insertRowAction.setEnabled(False)
        self.deleteRowsAction.setEnabled(False)
        self.insertColumnAction.setEnabled(False)
        self.deleteColumnsAction.setEnabled(False)

        self.setContextMenuPolicy(Qt.ActionsContextMenu)

        self.set_change_report()
        self.cellChanged.connect(self.cell_changed)
        self.cellClicked.connect(self.cell_clicked)
        #        self.cellActivated.connect(self.newline_press)
#        self.cellDoubleClicked.connect(self.newline_press)
        self.cellDoubleClicked.connect(self.click2)

    def init0(self, rows, columns):
        """Set the initial number of rows and columns and check that
        this is not in conflict with headers, if these have been set.
        """
        self.reset_modified(clear=True)
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
        if rows:
            self.insertRowAction.setEnabled(True)
            self.deleteRowsAction.setEnabled(True)
            self.insertColumnAction.setEnabled(True)
            self.deleteColumnsAction.setEnabled(True)
        self.setFocus()

    def init_data(self, data):
        """Set the initial table data from a (complete) list of lists
        of strings.
        """

        def dummy(*args):  # Don't report data changes
            pass

        # +
        self.table_data0 = data
        rows = len(data)
        columns = len(data[0])
        self.init0(rows, columns)
        # Disable change reporting
        self.set_change_report(dummy)
        # Enter data
        for r in range(rows):
            for c in range(columns):
                val = data[r][c]
                # print("SET", r, c, repr(val))
                if isinstance(val, str):
                    item = ValidatingWidgetItem(val)
                    if self.align_centre:
                        item.setTextAlignment(Qt.AlignCenter)
                    self.setItem(r, c, item)
                else:
                    raise Bug("Only string data is accepted")
        # Enable change reporting
        self.set_change_report()

    def init_sparse_data(self, rows, columns, data_list):
        """Set the initial table data from a list of cell values.
        data_list is a list of tuples: [(row, column, value), ... ].
        All other cells are null strings.
        """
        data = [[""] * columns for r in range(rows)]
        # Enter data
        for r, c, val in data_list:
            data[r][c] = val
        self.init_data(data)

    def row_count(self):
        return self.model().rowCount()

    #    def rowCountChanged(self, oldCount, newCount):
    #        """Slot override.
    #        """
    #        super().rowCountChanged(oldCount, newCount)

    def col_count(self):
        return self.model().columnCount()

    #    def columnCountChanged(self, oldCount, newCount):
    #        """Slot override.
    #        """
    #        super().columnCountChanged(oldCount, newCount)

    def get_text(self, row, col):
        """Convenience method for reading a cell from the QTableWidget."""
        data_model = self.model()
        return data_model.data(data_model.index(row, col)) or ""

    def set_text(self, row, col, text):
        """Convenience method for writing a cell."""
        data_model = self.model()
        data_model.setData(data_model.index(row, col), text)

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
            c = left
            while c < c1:
                rowdata.append(self.get_text(top, c))
                c += 1
            top += 1
            rows.append(rowdata)
        return rows

    def set_validator(self, row, col, f_validate):
        """Set a validator on the cell at (row, col).
        This uses the <set_validator> method of the widget item
        (QTableWidgetItem) at the given position. A <ValidatingWidgetItem>
        provides this method.

        <f_validate> is a function taking just the value as argument.
        If this is valid, the function returns <None>. Otherwise it
        returns an error message.
        """
        self.item(row, col).set_validator(f_validate)

    def cell_changed(self, r, c):
        """Handle cell-value changed. The arguments are row and column.
        OVERRIDE to use.
        """
        pass
        #print("§§§", r, c, repr(self.get_text(r, c)))

    def cell_value_changed(self, r, c, value, v0):
        #print("§§§", r, c, value, v0, self.table_changes)
        if self.table_data0[r][c] == value:
            # == initial value
            self.table_changes.discard((r, c))
            if not self.table_changes:
                self.set_modified(False)
        else:
            # != initial value
            self.table_changes.add((r, c))
            self.set_modified(True)
        self.add_change(Change_CELL, (r, c, v0, value))

    def read_all(self):
        """Read all the table data.
        Return list of rows, each row is a list of cell values.
        """
        return self.read_block(0, 0, self.col_count(), self.row_count())

    def insert_row(self):
        """Insert an empty row below the currenty selected one(s).
        If multiple rows are selected, the same number of rows will be
        added after the last selected row.
        """
        selected = self.get_selection()
        if selected[0]:
            h = selected[4]
            r = selected[1] + h
        else:
            QMessageBox.warning(self, _WARNING, _ROWOPFAIL)
            return
        if h == 1:
            self.insertRow(r)
        else:
            self.add_change(Change_GROUP, None)
            while h > 0:
                self.insertRow(r)
                h -= 1
            self.add_change(Change_END_GROUP, None)

    def insertRow(self, row, data=None):  # override
        ncols = self.columnCount()
        super().insertRow(row)
        if data is None:
            self.add_change(Change_ADD_ROW, row)
            data = [""] * ncols
        else:
            # There should only be data when undoing, so no need to add
            # a "change".
            if len(data) != ncols:
                raise Bug("insertRow: data length doesn't match table width")
        self.paste_block(row, 0, [data])

    def insert_column(self):
        """Insert an empty column after the currently selected one(s).
        If multiple columns are selected, the same number of columns
        will be added after the last selected column.
        """
        selected = self.get_selection()
        if selected[0]:
            w = selected[3]
            c = selected[2] + w
        else:
            QMessageBox.warning(self, _WARNING, _COLUMNOPFAIL)
            return
        if w == 1:
            self.insertColumn(c)
        else:
            self.add_change(Change_GROUP, None)
            while w > 0:
                self.insertColumn(c)
                w -= 1
            self.add_change(Change_END_GROUP, None)

    def insertColumn(self, column, data=None):  # override
        # Consistency check
        nrows = self.row_count()
        super().insertColumn(column)
        if data is None:
            self.add_change(Change_ADD_COL, column)
            data = [""] * nrows
        else:
            # There should only be data when undoing, so no need to add
            # a "change".
            if len(data) != nrows:
                raise Bug("insertColumn: data length doesn't match table height")
            self.paste_block(0, column, [[data[row]] for row in range(nrows)])

    def delete_rows(self):
        """Delete the selected rows."""
        selected = self.get_selection()
        if selected[0]:
            n = selected[4]
            r0 = selected[1]
        else:
            QMessageBox.warning(self, _WARNING, _ROWOPFAIL)
            return
        if n == self.row_count():
            QMessageBox.warning(self, _WARNING, _DELETEROWSFAIL)
        elif n == 1:
            self.removeRow(r0)
        else:
            self.add_change(Change_GROUP, None)
            r = r0 + n
            while r > r0:
                r -= 1
                self.removeRow(r)
            self.add_change(Change_END_GROUP, None)

    def removeRow(self, row):  # override
        rowdata = [self.get_text(row, col) for col in range(self.columnCount())]
        super().removeRow(row)
        self.add_change(Change_DEL_ROW, (row, rowdata))

    def delete_columns(self):
        """Delete the selected columns."""
        selected = self.get_selection()
        if selected[0]:
            n = selected[3]
            c0 = selected[2]
        else:
            QMessageBox.warning(self, _WARNING, _COLUMNOPFAIL)
            return
        if n == self.columnCount():
            QMessageBox.warning(self, _WARNING, _DELETECOLUMNSFAIL)
        elif n == 1:
            self.removeColumn(c0)
        else:
            self.add_change(Change_GROUP, None)
            c = c0 + n
            while c > c0:
                c -= 1
                self.removeColumn(c)
            self.add_change(Change_END_GROUP, None)

    def removeColumn(self, column):  # override
        coldata = [self.get_text(row, column) for row in range(self.rowCount())]
        super().removeColumn(column)
        self.add_change(Change_DEL_COL, (column, coldata))

    def set_change_report(self, handler=None):
        if handler:
            self.add_change = handler
        else:
            self.add_change = self.undoredo.change

    def click2(self):
        """Double-click"""
        print("click2")
        self.editItem(self.currentItem())
#        self.activated(self.currentRow(), self.currentColumn())

    def cell_clicked(self, row, col):
        """Ctrl-Click "activates" the cell."""
        if (
            QApplication.keyboardModifiers() & Qt.ControlModifier
        ) and self.get_selection()[0] == 1:
            self.activated(row, col)
#        self.editItem(self.item(row, col))

    def activated(self, row, col):
        # This is called when two conditions are fulfilled:
        #   1) the control button is pressed,
        #   2) a cell is left-clicked, or the (single) selected cell
        #      has "Return/Newline" pressed.
        # See 'activate-on-singleclick' below.
        print("ACTIVATED:", row, col)

#    def newline_press(self, row, col):
#        if self.get_selection()[0] == 1:
#            # if self.get_selection()[0] <= 1:
#            self.activated(row, col)

    @staticmethod
    def _get_point(event):
        # PySide2:
        return event.pos()
        # PySide6:
        return event.position().toPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clearSelection()
            self.setCurrentIndex(self.indexAt(self._get_point(event)))
            if QApplication.keyboardModifiers() & Qt.ControlModifier:
                return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if (
            event.button() == Qt.LeftButton
            and QApplication.keyboardModifiers() & Qt.ControlModifier
        ):
            if self.get_selection()[0] == 1:
                ix = self.indexAt(self._get_point(event))
                self.activated(ix.row(), ix.column())
                return
            else:
                self.clearSelection()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if self.state() != self.EditingState:
            key = event.key()
            if key == Qt.Key_Delete:
                if self.cut_selection() is None:
                    self.set_text(self.currentRow(), self.currentColumn(), "")
                return  # in this case don't call the base class method
            if key == Qt.Key_Return and self.get_selection()[0] == 1:
                if QApplication.keyboardModifiers() & Qt.ControlModifier:
                    self.activated(self.currentRow(), self.currentColumn())
                else:
                    self.editItem(self.currentItem())
#                self.newline_press(self.currentRow(), self.currentColumn())
        super().keyPressEvent(event)

    def copyCellsToClipboard(self):
        """Concatenate the text content of all selected cells into a string
        using tabulations and newlines to keep the table structure.
        Put this text into the clipboard.
        """
        n, t, l, w, h = self.get_selection()
        if n:
            rows = self.read_block(t, l, w, h)
            # put this data into clipboard
            qapp = QApplication.instance()
            qapp.clipboard().setText(table2tsv(rows))
        else:
            QMessageBox.warning(self, _WARNING, _COPYFAIL)

    def cutCellsToClipboard(self):
        """Concatenate the text content of all selected cells into a string
        using tabulations and newlines to keep the table structure.
        Put this text into the clipboard. Clear the selected cells.
        """
        block = self.cut_selection()
        if block is None:
            QMessageBox.warning(self, _WARNING, _COPYFAIL)
        else:
            # put this data into clipboard
            qapp = QApplication.instance()
            qapp.clipboard().setText(block)

    def cut_selection(self):
        """Cut the selected range, returning the contents as "tsv".
        The changed cells are reported as a single item, possibly a list.
        """

        def gather(chtype, change):
            if chtype != Change_CELL:
                raise Bug("Cutting block should only cause cell changes")
            change_list.append(change)

        # +
        n, t, l, w, h = self.get_selection()
        if n == 0:
            return None
        if n == 1:
            text = self.get_text(t, l)
            if text:
                self.set_text(t, l, "")
            return text
        block = self.read_block(t, l, w, h)
        change_list = []
        self.set_change_report(gather)
        r1 = t + h
        c1 = l + w
        while t < r1:
            c = l
            while c < c1:
                self.set_text(t, c, "")
                c += 1
            t += 1
        self.set_change_report()
        # Report changes as a list – only cells which actually changed
        if change_list:
            if len(change_list) == 1:
                self.add_change(Change_CELL, change_list[0])
            else:
                self.add_change(Change_BLOCK, change_list)
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
        nrows = self.row_count()
        ncols = self.columnCount()
        n, r0, c0, w, h = self.get_selection()
        if n == 0:
            QMessageBox.warning(self, _WARNING, _COPYFAIL)
            return
        qapp = QApplication.instance()
        clipboard_text = qapp.clipboard().text().rstrip('\n')
        table_data = tsv2table(clipboard_text)
        protected_cells = 0
        ph = len(table_data)
        pw = len(table_data[0])
        try:
            if ph == 1:  # paste a single row
                if w == 1:  # ... to a single column
                    paste_data = table_data * h
                elif pw == 1:  # paste a single cell
                    row = table_data[0] * w
                    paste_data = [row] * h
                else:
                    raise RangeError(_BAD_PASTE_RANGE)
            elif pw == 1:  # paste a single column
                if h == 1:  # ... to a single row
                    paste_data = [row * w for row in table_data]
                else:
                    raise RangeError(_BAD_PASTE_RANGE)
            elif n == 1:  # paste to a single cell
                paste_data = table_data
            else:
                raise RangeError(_BAD_PASTE_RANGE)
            # Check that the data to be pasted will fit into the table.
            if r0 + ph > nrows:
                raise RangeError(_TOO_MANY_ROWS)
            if c0 + pw > ncols:
                raise RangeError(_TOO_MANY_COLUMNS)
        except RangeError as e:
            QMessageBox.warning(self, _WARNING, str(e))
            return
        if protected_cells:
            QMessageBox.warning(self, _WARNING, _PASTE_PROTECTED)
        # Do the pasting
        self.paste_block(r0, c0, paste_data)

    def paste_block(self, top, left, block):
        """The block must be a list of lists of strings."""

        def gather(chtype, change):
            if chtype != Change_CELL:
                raise Bug("Pasting block should only cause cell changes")
            change_list.append(change)

        # +
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
                self.add_change(Change_CELL, change_list[0])
            else:
                self.add_change(Change_BLOCK, change_list)

    def set_modified(self, mod):
        """Whenever a change away from the "initial" table data is made,
        this is called with <mod> true. When all changes are reverted,
        this is called with <mod> false.
        This method keeps the <self.__modified> flag up-to-date. When
        a change to that flag occurs here, the callback <self.on_changed>
        will be called with the new flag value.
        It is also possible to specify a new "initial" state: see the
        method <self.reset_modified>.
        """
        #print("§§§MOD", mod, self.__modified, self.on_changed)
        if mod != self.__modified:
            self.__modified = mod
            if self.on_changed:
                self.on_changed(mod)

    def reset_modified(self, clear=False):
        """Reset the "starting point" for registering changes.
        This should be called when a table is saved, so that an
        unmodified state is reasserted. It can also be called after
        initializing the table data (e.g. from a file).
        If <clear> is true, the undo list is cleared (if there is one).
        Otherwise the undo list is untouched, so that an undo operation
        can return to a state previous to the new initial state.
        """
        self.set_modified(False)
        self.table_changes = set()
        self.undoredo.mark0(clear)

    def is_modified(self):
        return self.__modified

    def selectionChanged(self, selected, deselected):
        """Override the slot. The parameters are <QItemSelection> items."""
        super().selectionChanged(selected, deselected)
        sel = bool(self.selectedRanges())
        if sel != self.has_selection:
            self.has_selection = sel
            self.on_selection_state_change(sel)
            # TODO: Enable/disable row/column actions? (also delete?)
            if sel:
                # Enable actions
                pass
            else:
                # Disable actions
                pass

    """
    def focusInEvent(self, event):
        self.focussed = True
        print("FOCUSSED TABLE")
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.focussed = False
        print("UNFOCUSSED TABLE")
        super().focusOutEvent(event)
    """


'''
# This is just for testing purposes. The approach using <ValidatingWidgetItem>
# looks more promising.
class MyDelegate(QStyledItemDelegate):
    """Intercept data changes in the delegate.
    """
    def setModelData(self, editor, model, index):
        col = index.column()
        row = index.row()
        n = editor.metaObject().userProperty().name()
        if not n:
            raise Bug("No user property name")
            # In source for QStyledItemDelegate::setModelData:
            #n = d->editorFactory()->valuePropertyName(
            #model->data(index, Qt::EditRole).userType());
        if n:
            print("setModelData", n, type(n), "->", editor.property(n))
            val = editor.property(n)
            if val != 'x':
                super().setModelData(editor, model, index)
            else:
                QMessageBox.warning(editor, _WARNING,
                        f"{_VALIDATION_ERROR} "
                        f"@({row}, {col}): {val}")
'''


class ValidatingWidgetItem(QTableWidgetItem):
    def __init__(self, value=""):
        self.set_validator(None)
        super().__init__(value)

    def set_validator(self, validate):
        self.__validate = validate

    def clone(self):
        return ValidatingWidgetItem()

    def setData(self, role, value):
        if role == Qt.EditRole:
            if self.__validate:
                v = self.__validate(value)
                if v:
                    QMessageBox.warning(
                        self.tableWidget(),
                        _WARNING,
                        f"{_VALIDATION_ERROR} "
                        f"@({self.row()}, {self.column()}): {value}",
                    )
                    return
            v0 = self.data(role)
            if v0 == value:
                return
            tw = self.tableWidget()
            if tw:
                r, c = self.row(), self.column()
                #print(f"CHANGED @({r}, {c}): {v0} -> {value}")
                tw.cell_value_changed(r, c, value, v0)
        super().setData(role, value)


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


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    app = QApplication([])
    # This seems to deactivate activate-on-single-click
    # (presumably elsewhere as well?)
    #    app.setStyleSheet("QAbstractItemView { activate-on-singleclick: 0; }")
    def is_modified1(mod):
        print("MODIFIED1:", mod)

    def is_modified2(mod):
        print("MODIFIED2:", mod)

    def validate(value):
        if value == "v":
            return "invalid value"
        return None

    cols = ["Column %02d" % n for n in range(10)]
    rows = ["Row %02d" % n for n in range(7)]
    tablewidget = EdiTableWidget(align_centre=True)

#    tablewidget.installEventFilter(tablewidget)
    tablewidget.setup(colheaders=cols, rowheaders=rows, on_changed=is_modified1)

    tablewidget.setWindowTitle("EdiTableWidget")

    # setItemDelegate doesn't take ownership of the custom delegates,
    # so I retain references (otherwise there will be a segfault).
    idel1 = VerticalTextDelegate()
    #    idel2 = MyDelegate()
    tablewidget.setItemDelegateForRow(2, idel1)
    #    tablewidget.setItemDelegateForRow(1, idel2)

    sparse_data = []
    r, c = 2, 3
    sparse_data.append((r, c, "R%02d:C%02d" % (r, c)))
    r, c = 1, 4
    sparse_data.append((r, c, "R%02d:C%02d" % (r, c)))
    tablewidget.init_sparse_data(len(rows), len(cols), sparse_data)

    tablewidget.resizeRowToContents(1)
    tablewidget.resizeRowToContents(2)
    tablewidget.resizeColumnToContents(3)
    tablewidget.resize(600, 400)
    tablewidget.show()

    tw2 = EdiTableWidget()
    tw2.setup(
        undo_redo=True,
        cut=True,
        paste=True,
        row_add_del=True,
        column_add_del=True,
        on_changed=is_modified2,
    )
    tw2.init_data([["1", "2", "3", "4"], [""] * 4])
    tw2.set_validator(1, 0, validate)
    tw2.resize(400, 300)
    tw2.show()

    app.exec()
