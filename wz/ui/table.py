# -*- coding: utf-8 -*-

"""
gui/table.py

Last updated:  2021-10-07

A slight modification of "TableWidget.py" from the "silx" project
(www.silx.org), thanks to P. Knobel.

 - Adapted to run in this project (mostly tweaking of the imports).
 - Added German display texts.
 - Added check for text cells when copying to clip board (only text
  may be copied.
  - By default, cut/copy all cells is not enabled (if there are non-text
   cells it wouldn't work anyway).
  - Removed the TableView version.
  - Added "changed" handling (could be used for undo/redo, save-popup, etc.?)
  - Various other tweaks ...

Modifications Copyright (c) 2021 Michael Towers

Original Licence below.
"""

#TODO: Are non-text cells at all possible???!!!

# /*##########################################################################
#
# Copyright (c) 2004-2017 European Synchrotron Radiation Facility
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# ###########################################################################*/

"""This module provides a table widget handling cut, copy and paste for
multiple cell selections. These actions can be triggered using keyboard
shortcuts or through a context menu (right-click).

:class:`TableWidget` is a subclass of :class:`QTableWidget`, a table view
with a built-in standard data model. The added features are available as soon as
the widget is initialized.

The cut, copy and paste actions are implemented as QActions:

    - :class:`CopySelectedCellsAction` (*Ctrl+C*)
    - :class:`CopyAllCellsAction`
    - :class:`CutSelectedCellsAction` (*Ctrl+X*)
    - :class:`CutAllCellsAction`
    - :class:`PasteCellsAction` (*Ctrl+V*)

The copy actions are enabled by default. The cut and paste actions must be
explicitly enabled, by passing parameters ``cut=True, paste=True`` when
creating the widgets.
"""

__authors__ = ["P. Knobel"]
__license__ = "MIT"
__date__ = "03/07/2017"

#_PASTE1 = "Clipboard data dimensions incompatible with selected range"
_PASTE1 = "Die Dimensionen der einzufügenden Daten sind nicht kompatibel" \
        " mit dem selektierten Bereich."
#_PASTEFAIL = ("Some data could not be inserted,"
#        " due to out-of-range or write-protected cells.")
_PASTEFAIL = ("Aufgrund nicht verfügbarer Zellen konnten einige"
        " Daten nicht eingefügt werden")
#_CUTSELECTION = "Cut selection"
_CUTSELECTION = "Auswahl ausschneiden"
#_COPYSELECTION = "Copy selection"
_COPYSELECTION = "Auswahl kopieren"
#_TTCOPYSELECTION = "Copy selected cells into the clipboard."
_TTCOPYSELECTION = "Ausgewählte Zellen zur Zwischanablage kopieren."
#_COPYALL = "Copy all"
_COPYALL = "Alles kopieren"
#_TTCOPYALL = "Copy all cells into the clipboard."
_TTCOPYALL = "Alle Zellen zur Zwischanablage kopieren."
#_CUTALL = "Cut all"
_CUTALL = "Alles ausschneiden"
#_TTCUTALL = "Cut all cells into the clipboard."
_TTCUTALL = "Alle Zellen ausschneiden und zur Zwischanablage kopieren."
#_PASTE = "Paste"
_PASTE = "Einfügen"
#_TTPASTE = ("Paste data."
#         " The selected cell is the top-left corner of the paste area.")
_TTPASTE = ("Daten einfügen. Die selektierte Zelle ist oben links"
        " im Bereich, der eingefügt wird.")
#_COPYCELL = "Copy cell"
_COPYCELL = "Zelle kopieren"
#_TTCOPYCELL = "Copy cell content into the clipboard."
_TTCOPYCELL = "Zelleninhalt zur Zwischenablage kopieren."
#_NONTEXTCELL = "Can only copy selection with exclusively text cells."
_NONTEXTCELL = ("Um eine Auswahl zu kopieren, dürfen nur reine"
        " Text-Zellen enthalten sein.")
#_INSERTROW = "Insert Row"
_INSERTROW = "Zeile einfügen"
#_TTINSERTROW = "Insert Row"
_TTINSERTROW = "Zeile einfügen nach der aktuellen Zeile"
#_INSERT1 = "A single row must be selected to insert a new one"
_INSERT1 = "Um eine neue Zeile einzufügen, muss genau eine selektiert sein"
#_DELETEROWS = "Delete Rows"
_DELETEROWS = "Zeilen löschen"
#_TTDELETEROWS = "Delete selected Rows"
_TTDELETEROWS = "Selektierte Zeilen löschen"
#_INSERT1 = "A single row must be selected to insert a new one"
_DELETE1 = "Um Zeilen zu löschen, müssen sie eindeutig selektiert sein"
_NONCONTIGUOUS = "Selektierte Zellen sind nicht zusammenhängend"

import sys
from PySide6.QtWidgets import QApplication, \
        QTableView, QTableWidget, QMessageBox#, QMenu
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence

row_separator = '\n'
col_separator = '\t'


#TODO: Disallow multiple selections?

class InsertRowAction(QAction):
    """QAction to insert a row of cells.

    :param table: :class:`QTableView` to which this action belongs.
    """
    def __init__(self, table):
        if not isinstance(table, QTableView):
            raise ValueError('InsertRowAction must be initialised ' +
                             'with a QTableWidget.')
        super().__init__(table)
        self.setText(_INSERTROW)
        self.setToolTip(_TTINSERTROW)
# The tooltip is not shown in a popup menu ...
        self.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_I))
        self.setShortcutContext(Qt.WidgetShortcut)
        self.triggered.connect(self.insert_row)
        self.table = table

    def insert_row(self):
        """Insert an empty row below the current one.
        """
        selected = self.table.selectedRanges()
        if len(selected) == 1:
            # Just one selected block
            selrange = selected[0]
            i = selrange.bottomRow()
            if i == selrange.topRow():
                # Just one selected row (can be more than on cell)
                data_model = self.table.model()
                self.table.insertRow(i + 1)
                return True
        msgBox = QMessageBox(parent=self.table)
        msgBox.setText(_INSERT1)
        msgBox.exec()
        return False


class DeleteRowsAction(QAction):
    """QAction to delete rows of cells.

    :param table: :class:`QTableView` to which this action belongs.
    """
    def __init__(self, table):
        if not isinstance(table, QTableView):
            raise ValueError('DeleteRowsAction must be initialised ' +
                             'with a QTableWidget.')
        super().__init__(table)
        self.setText(_DELETEROWS)
        self.setToolTip(_TTDELETEROWS)
        self.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_R))
        self.setShortcutContext(Qt.WidgetShortcut)
        self.triggered.connect(self.delete_rows)
        self.table = table

    def delete_rows(self):
        """Delete the selected rows.
        """
        selected = self.table.selectedRanges()
        if len(selected) != 1:
            msgBox = QMessageBox(parent=self.table)
            msgBox.setText(_DELETE1)
            msgBox.exec()
            return False
        data_model = self.table.model()
        selrange = selected[0]
        i = selrange.topRow()
        n = selrange.bottomRow()
        while i <= n:
            self.table.removeRow(i)
            n -= 1
        return True


class CopySelectedCellsAction(QAction):
    """QAction to copy text from selected cells in a :class:`QTableWidget`
    into the clipboard.

    If multiple cells are selected, the copied text will be a concatenation
    of the texts in all selected cells, tabulated with tabulation and
    newline characters.

    If the cells are sparsely selected, the structure is preserved by
    representing the unselected cells as empty strings in between two
    tabulation characters.
    Beware of pasting this data because, depending
    on how the paste is implemented, the empty cells may cause data in the
    target table to be deleted, even though you didn't necessarily select the
    corresponding cell in the origin table.

    :param table: :class:`QTableView` to which this action belongs.
    """
    def __init__(self, table):
        if not isinstance(table, QTableView):
            raise ValueError('CopySelectedCellsAction must be initialised ' +
                             'with a QTableWidget.')
        super().__init__(table)
        self.setText(_COPYSELECTION)
        self.setToolTip(_TTCOPYSELECTION)
        self.setShortcut(QKeySequence.Copy)
        self.setShortcutContext(Qt.WidgetShortcut)
        self.triggered.connect(self.copyCellsToClipboard)
        self.table = table
        self.cut = False
        """:attr:`cut` can be set to True by classes inheriting this action,
        to do a cut action."""

    def copyCellsToClipboard(self):
        """Concatenate the text content of all selected cells into a string
        using tabulations and newlines to keep the table structure.
        Put this text into the clipboard.
        If the cells are not contiguous, fail.
        """
        selected_idx = self.table.selectedIndexes()
        if not selected_idx:
            return False
        #print("SELECTED:", selected_idx)
        selected_idx_tuples = [(idx.row(), idx.column()) for idx in selected_idx]

        selected_rows = [idx[0] for idx in selected_idx_tuples]
        row0, row1 = min(selected_rows), max(selected_rows)
        selected_columns = [idx[1] for idx in selected_idx_tuples]
        col0, col1 = min(selected_columns), max(selected_columns)
        nselblock = (row1 - row0 + 1) * (col1 - col0 + 1)
        if nselblock > len(selected_idx_tuples):
            # Selection not contiguous
            msgBox = QMessageBox(parent=self.table)
            msgBox.setText(_NONCONTIGUOUS)
            msgBox.exec()
            return False

        data_model = self.table.model()

        copied_text = ""
        for row in range(row0, row1 + 1):
            for col in range(col0, col1 + 1):
                index = data_model.index(row, col)
                cell_text = data_model.data(index)
                flags = data_model.flags(index)

                if (row, col) in selected_idx_tuples and cell_text is not None:
                    try:
                        copied_text += cell_text
                    except:
                        # Only works for text cells
                        msgBox = QMessageBox(parent=self.table)
                        msgBox.setText(_NONTEXTCELL)
                        msgBox.exec()
                        return False
                    if self.cut and (flags & Qt.ItemIsEditable):
                        data_model.setData(index, "")
                copied_text += col_separator
            # remove the right-most tabulation
            copied_text = copied_text[:-len(col_separator)]
            # add a newline
            copied_text += row_separator
        # remove final newline
        copied_text = copied_text[:-len(row_separator)]

        # put this text into clipboard
        qapp = QApplication.instance()
        qapp.clipboard().setText(copied_text)
        return True


class CopyAllCellsAction(QAction):
    """QAction to copy text from all cells in a :class:`QTableWidget`
    into the clipboard.

    The copied text will be a concatenation
    of the texts in all cells, tabulated with tabulation and
    newline characters.

    :param table: :class:`QTableView` to which this action belongs.
    """
    def __init__(self, table):
        if not isinstance(table, QTableView):
            raise ValueError('CopyAllCellsAction must be initialised ' +
                             'with a QTableWidget.')
        super().__init__(table)
        self.setText(_COPYALL)
        self.setToolTip(_TTCOPYALL)
        self.triggered.connect(self.copyCellsToClipboard)
        self.table = table
        self.cut = False

    def copyCellsToClipboard(self):
        """Concatenate the text content of all cells into a string
        using tabulations and newlines to keep the table structure.
        Put this text into the clipboard.
        """
        copied_text = self.table.getAllCells(self.cut)
        # put this text into clipboard
        qapp = QApplication.instance()
        qapp.clipboard().setText(copied_text)
        return True


class CutSelectedCellsAction(CopySelectedCellsAction):
    """QAction to cut text from selected cells in a :class:`QTableWidget`
    into the clipboard.

    The text is deleted from the original table widget
    (use :class:`CopySelectedCellsAction` to preserve the original data).

    If multiple cells are selected, the cut text will be a concatenation
    of the texts in all selected cells, tabulated with tabulation and
    newline characters.

    If the cells are sparsely selected, the structure is preserved by
    representing the unselected cells as empty strings in between two
    tabulation characters.
    Beware of pasting this data in another table widget, because depending
    on how the paste is implemented, the empty cells may cause data in the
    target table to be deleted, even though you didn't necessarily select the
    corresponding cell in the origin table.

    :param table: :class:`QTableView` to which this action belongs."""
    def __init__(self, table):
        super().__init__(table)
        self.setText(_CUTSELECTION)
        self.setShortcut(QKeySequence.Cut)
        self.setShortcutContext(Qt.WidgetShortcut)
        # cutting is already implemented in CopySelectedCellsAction (but
        # it is disabled), we just need to enable it
        self.cut = True


class CutAllCellsAction(CopyAllCellsAction):
    """QAction to cut text from all cells in a :class:`QTableWidget`
    into the clipboard.

    The text is deleted from the original table widget
    (use :class:`CopyAllCellsAction` to preserve the original data).

    The cut text will be a concatenation
    of the texts in all cells, tabulated with tabulation and
    newline characters.

    :param table: :class:`QTableView` to which this action belongs."""
    def __init__(self, table):
        super().__init__(table)
        self.setText(_CUTALL)
        self.setToolTip(_TTCUTALL)
        self.cut = True


def _parseTextAsTable(text, col_separator=col_separator):
    """Parse text into list of lists (2D sequence).

    The input text must be tabulated using tabulation characters and
    newlines to separate columns and rows.

    :param text: text to be parsed
    :param record_separator: String, or single character, to be interpreted
        as a record/row separator.
    :param field_separator: String, or single character, to be interpreted
        as a field/column separator.
    :return: 2D sequence of strings, all rows having the same length
        (padded with '' if necessary).
    """
    rows = text.splitlines()
    table_data = []
    max_len = 0
    for row in rows:
        line = row.split(col_separator)
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


class RangeError(Exception):
    pass
#
class PasteCellsAction(QAction):
    """QAction to paste text from the clipboard into the table.

    If the text contains tabulations and newlines, they are interpreted
    as column and row separators.
    In such a case, the text is split into multiple texts to be pasted
    into multiple cells.

    If <skip_empty> is true and a cell content is an empty string in
    the pasted text, it is ignored: the destination cell's text will
    not be deleted.

    :param table: :class:`QTableView` to which this action belongs.
    """
    def __init__(self, table, skip_empty = False):
        if not isinstance(table, QTableView):
            raise ValueError('PasteCellsAction must be initialised ' +
                             'with a QTableWidget.')
        super().__init__(table)
        self.skip_empty = skip_empty
        self.table = table
        self.setText(_PASTE)
        self.setShortcut(QKeySequence.Paste)
        self.setShortcutContext(Qt.WidgetShortcut)
        self.setToolTip(_TTPASTE)
        self.triggered.connect(self.pasteCellFromClipboard)

    def pasteCellFromClipboard(self):
        """Paste text from clipboard into the table.

        :return: *True* in case of success, *False* if pasting data failed.
        """
        def do_paste(selected_row, selected_col):
            # paste table data into cells, using selected cell as origin
            for row_offset in range(len(table_data)):
                for col_offset in range(len(table_data[row_offset])):
                    target_row = selected_row + row_offset
                    target_col = selected_col + col_offset

                    if target_row >= data_model.rowCount() or\
                       target_col >= data_model.columnCount():
                        self.out_of_range_cells += 1
                        continue

                    index = data_model.index(target_row, target_col)
                    flags = data_model.flags(index)

                    # ignore empty strings?
                    if self.skip_empty and table_data[row_offset][col_offset] == "":
                        continue
                    if not flags & Qt.ItemIsEditable:
                        protected_cells += 1
                        continue
                    data_model.setData(index, table_data[row_offset][col_offset])

        qapp = QApplication.instance()
        clipboard_text = qapp.clipboard().text()
        table_data = _parseTextAsTable(clipboard_text)
        selected = self.table.selectedRanges()
        if len(selected) != 1:
            msgBox = QMessageBox(parent=self.table)
            msgBox.setText(_PASTE1)
            msgBox.exec()
            return False
        selrange = selected[0]
        irows = range(selrange.topRow(), selrange.bottomRow() + 1)
        icols = range(selrange.leftColumn(), selrange.rightColumn() + 1)
        data_model = self.table.model()
        protected_cells = 0
        self.out_of_range_cells = 0
        try:
            if len(table_data) == 1:
                # paste a single row
                if len(icols) == 1:
                    # ... to a single column
                    c = icols[0]
                    for r in irows:
                        do_paste(r, c)
                elif len(table_data[0]) == 1:
                    # paste a single cell
                    for r in irows:
                        for c in icols:
                            do_paste(r, c)
                else:
                    raise RangeError()
            elif len(table_data[0]) == 1:
                # paste a single column
                if len(irows) == 1:
                    # ... to a single row
                    r = irows[0]
                    for c in icols:
                        do_paste(r, c)
                else:
                    raise RangeError()
            elif len(irows) == 1 and len(icols) == 1:
                # paste to a single cell
                do_paste(irows[0], icols[0])
            else:
                raise RangeError()
        except RangeError:
            msgBox = QMessageBox(parent=self.table)
            msgBox.setText(_PASTE1)
            msgBox.exec()
            return False
        if protected_cells or self.out_of_range_cells:
            msgBox = QMessageBox(parent=self.table)
            msgBox.setText(_PASTEFAIL)
            msgBox.exec()
            return False
        return True


class CopySingleCellAction(QAction):
    """QAction to copy text from a single cell in a modified
    :class:`QTableWidget`.

    This action relies on the fact that the text in the last clicked cell
    are stored in :attr:`_last_cell_clicked` of the modified widget.

    In most cases, :class:`CopySelectedCellsAction` handles single cells,
    but if the selection mode of the widget has been set to NoSelection
    it is necessary to use this class instead.

    :param table: :class:`QTableView` to which this action belongs.
    """
    def __init__(self, table):
        if not isinstance(table, QTableView):
            raise ValueError('CopySingleCellAction must be initialised ' +
                             'with a QTableWidget.')
        super().__init__(table)
        self.setText(_COPYCELL)
        self.setToolTip(_TTCOPYCELL)
        self.triggered.connect(self.copyCellToClipboard)
        self.table = table

    def copyCellToClipboard(self):
        """
        """
        cell_text = self.table._text_last_cell_clicked
        if cell_text is None:
            return

        # put this text into clipboard
        qapp = QApplication.instance()
        qapp.clipboard().setText(cell_text)


class TableWidget(QTableWidget):
    """:class:`QTableWidget` with a context menu displaying actions, some
    of them optional:

        - :class:`InsertRowAction`
        - :class:`CopySelectedCellsAction`
        - :class:`CopyAllCellsAction`
        - :class:`CutSelectedCellsAction`
        - :class:`CutAllCellsAction`
        - :class:`PasteCellsAction`

    These actions interact with the clipboard and can be used to copy data
    to or from an external application, or another widget.

    The cut and paste actions are disabled by default, due to the risk of
    overwriting data (no *Undo* action is available).

    :param parent: Parent QWidget
    :param bool cut: Enable cut action
    :param bool paste: Enable paste action
    :param bool allCells: Enable copy(/cut) all cells
    :param fn on_changed: Callback(row, col, text) for changed cells
    """
    def setup(self, parent = None, cut = False, paste = False,
            allCells = False, row_add_del = False, on_changed = None):
        self.on_changed = on_changed
        self._text_last_cell_clicked = None
#
        if row_add_del:
#            self.header_menu = QMenu()
#            headers = self.verticalHeader()
#            insertRowAction = InsertRowAction(self)
#            self.header_menu.addAction(insertRowAction)
#            deleteRowsAction = DeleteRowsAction(self)
#            self.header_menu.addAction(deleteRowsAction)
##            headers.setContextMenuPolicy(Qt.ActionsContextMenu)
#            headers.setContextMenuPolicy(Qt.CustomContextMenu)
#            headers.customContextMenuRequested.connect(self.vheader_popup)

            insertRowAction = InsertRowAction(self)
            self.addAction(insertRowAction)
            deleteRowsAction = DeleteRowsAction(self)
            self.addAction(deleteRowsAction)
            sep = QAction(self)
            sep.setSeparator(True)
            self.addAction(sep)
#
        self.copySelectedCellsAction = CopySelectedCellsAction(self)
        self.copyAllCellsAction = None
        if allCells:
            self.copyAllCellsAction = CopyAllCellsAction(self)
            self.addAction(self.copyAllCellsAction)
        self.copySingleCellAction = None
        self.pasteCellsAction = None
        self.cutSelectedCellsAction = None
        self.cutAllCellsAction = None

        self.addAction(self.copySelectedCellsAction)
        if cut:
            self.cutSelectedCellsAction = CutSelectedCellsAction(self)
            self.addAction(self.cutSelectedCellsAction)
            if allCells:
                self.cutAllCellsAction = CutAllCellsAction(self)
                self.addAction(self.cutAllCellsAction)
        if paste:
            self.pasteCellsAction = PasteCellsAction(self)
            self.addAction(self.pasteCellsAction)
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
#
        self.cellChanged.connect(self.cell_changed)
        self.cellClicked.connect(self.activated)
        self.cellActivated.connect(self.activated)

    def get_text(self, row, col):
        data_model = self.model()
        return data_model.data(data_model.index(row, col))

    def set_text(self, row, col, text):
        data_model = self.model()
        data_model.setData(data_model.index(row, col), text)

    def cell_changed(self, row, col):
        if self.on_changed:
            self.on_changed(row, col, self.item(row, col).text())

    def activated(self, row, col):
        # This is called when a cell is left-clicked or when the selected
        # cell has "Enter" pressed. When multiple cells are selected,
        # the last selected one is activated.
        pass
        #print("ACTIVATED:", row, col)

#    def vheader_popup(self, point):
#        action = self.header_menu.exec(self.mapToGlobal(point))
#        if action:
#            i = self.verticalHeader().logicalIndexAt(point)
##            print("VHEADER:", i)
#            action.run(i)

    def mousePressEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        if item is not None:
            self._text_last_cell_clicked = item.text()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if self.state() != self.EditingState:
            if event.key() == Qt.Key_Delete:
                item = self.currentItem()
                if item:
                    item.setText('')
                return
        # any other key was pressed, inform base class
        super().keyPressEvent(event)

    def setSelectionMode(self, mode):
        """Overloaded from QTableWidget to disable cut/copy selection
        actions in case mode is NoSelection

        :param mode:
        :return:
        """
        if mode == QTableView.NoSelection:
            self.copySelectedCellsAction.setVisible(False)
            self.copySelectedCellsAction.setEnabled(False)
            if self.cutSelectedCellsAction is not None:
                self.cutSelectedCellsAction.setVisible(False)
                self.cutSelectedCellsAction.setEnabled(False)
            if self.copySingleCellAction is None:
                self.copySingleCellAction = CopySingleCellAction(self)
                self.insertAction(self.copySelectedCellsAction,  # before first action
                                  self.copySingleCellAction)
            self.copySingleCellAction.setVisible(True)
            self.copySingleCellAction.setEnabled(True)
        else:
            self.copySelectedCellsAction.setVisible(True)
            self.copySelectedCellsAction.setEnabled(True)
            if self.cutSelectedCellsAction is not None:
                self.cutSelectedCellsAction.setVisible(True)
                self.cutSelectedCellsAction.setEnabled(True)
            if self.copySingleCellAction is not None:
                self.copySingleCellAction.setVisible(False)
                self.copySingleCellAction.setEnabled(False)
        super().setSelectionMode(mode)

    def getAllCells(self, cut = False):
        """Concatenate the text content of all cells into a string
        using tabulations and newlines to keep the table structure.
        If <cut> is true, the cells will be emptied if they are editable.
        """
        data_model = self.model()
        copied_text = ""
        for row in range(data_model.rowCount()):
            for col in range(data_model.columnCount()):
                index = data_model.index(row, col)
                cell_text = data_model.data(index)
                if cell_text:
                    copied_text += cell_text
                    if cut and (data_model.flags(index) & Qt.ItemIsEditable):
                        data_model.setData(index, "")
                copied_text += col_separator
            # remove the right-most tabulation
            copied_text = copied_text[:-len(col_separator)]
            # add a newline
            copied_text += row_separator
        # remove final newline
        return copied_text[:-len(row_separator)]



if __name__ == "__main__":
    app = QApplication([])

    tablewidget = TableWidget()
    tablewidget.setup(row_add_del = True, cut = True, paste = True)
    tablewidget.setSelectionMode(QTableView.ExtendedSelection)
    tablewidget.setWindowTitle("TableWidget")
    cols = ["Column %02d" % n for n in range(10)]
    tablewidget.setColumnCount(len(cols))
    tablewidget.setHorizontalHeaderLabels(cols)
    rows = ["Row %02d" % n for n in range(7)]
    tablewidget.setRowCount(len(rows))
    tablewidget.setVerticalHeaderLabels(rows)

# Note that inserting and deleting rows will make a mess of the row
# headers set above

    r, c = 2, 3
    tablewidget.set_text(r, c, 'R%02d:C%02d' % (r, c))
    print("???", tablewidget.get_text(r, c))
    r, c = 1, 4
    tablewidget.set_text(r, c, 'R%02d:C%02d' % (r, c))
    print("???", tablewidget.get_text(r, c))
    print("???", tablewidget.get_text(0, 0))

    tablewidget.resize(600, 400)
    tablewidget.show()
    app.exec()
