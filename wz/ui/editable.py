# -*- coding: utf-8 -*-

"""
ui/editable.py

Last updated:  2021-10-18

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
#_CUTSELECTION = "Cut selection"
_CUTSELECTION = "Auswahl ausschneiden"
#_COPYSELECTION = "Copy selection"
_COPYSELECTION = "Auswahl kopieren"
#_TTCOPYSELECTION = "Copy selected cells into the clipboard."
_TTCOPYSELECTION = "Ausgewählte Zellen zur Zwischanablage kopieren."
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

########################################################################

from PySide6.QtWidgets import QApplication, \
        QTableView, QTableWidget, QMessageBox, \
        QStyledItemDelegate, QStyleOptionViewItem
from PySide6.QtCore import Qt, QPointF, QRectF, QSize
from PySide6.QtGui import QAction, QKeySequence

### -----

class ClearSelectionAction(QAction):
    """QAction to clear the selection.
    """
    def __init__(self, table):
        super().__init__(table)
        self.setText(_CLEARSELECTION)
#        self.setToolTip(_TTCLEARSELECTION)
# The tooltip is not shown in a popup menu ...
        self.setShortcut(QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_A))
        self.setShortcutContext(Qt.WidgetShortcut)
        self.triggered.connect(self.clear_selection)
        self.table = table

    def clear_selection(self):
        """Clear the selection.
        """
        selected = self.table.get_selection()
        if selected[0]:
            self.table.clearSelection()
#?            self.table.setCurrentItem(None)


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
        self.cut = False    # can be overridden to perform a "cut" action

    def copyCellsToClipboard(self):
        """Concatenate the text content of all selected cells into a string
        using tabulations and newlines to keep the table structure.
        Put this text into the clipboard.
        """
        n, r0, c0, w, h = self.table.get_selection()
        if n:
            r = r0
            r1 = r0 + h
            c1 = c0 + w
            rows = []
            while r < r1:
                rowdata = []
                c = c0
                while c < c1:
#TODO: move some of this to the main widget?
# Ensure that cut changes are registered
                    celldata = self.table.get_text(r, c)
                    rowdata.append(celldata or '')
                    if self.cut and celldata:
                        self.table.set_text(r, c, '')
                    c += 1
                rows.append('\t'.join(rowdata))
                r += 1
            # put this data into clipboard
            qapp = QApplication.instance()
            qapp.clipboard().setText('\n'.join(rows))
        else:
            msgBox = QMessageBox(parent = self.table)
            msgBox.setText(_COPYFAIL)
            msgBox.exec()


class CutCellsAction(CopyCellsAction):
    """QAction to copy text from selected cells into the clipboard (see
    <CopyCellsAction>) and clear these cells in the table.
    """
    def __init__(self, table):
        super().__init__(table)
        self.setText(_CUTSELECTION)
        self.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_X))
        # cutting is already implemented in CopyCellsAction (but
        # it is disabled), we just need to enable it
        self.cut = True


def parseTextAsTable(text):
    """Parse text into list of lists.

    The input text must be tabulated using tabulation characters and
    newlines to separate columns and rows.

    The output lines are padded with '' values to ensure that all lines
    have the same length.
    """
    rows = text.splitlines()
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
        """
        nrows = self.table.row_count()
        ncols = self.table.column_count()
        #+
        def do_paste(selected_row, selected_col):
            # Paste table data into cells, using selected cell as origin.
            irows = len(table_data)
            # First check that the data to be pasted will fit into the table.
            if selected_row + irows > nrows:
                raise RangeError(_TOO_MANY_ROWS)
            # Using <parseTextAsTable> (see below) ensures that all rows
            # have the same length.
            icols = len(table_data[0])
            if selected_col + icols > ncols:
                raise RangeError(_TOO_MANY_COLUMNS)
            # Insert the new data
            for row_offset in range(irows):
                for col_offset in range(icols):
                    target_row = selected_row + row_offset
                    target_col = selected_col + col_offset
                    index = data_model.index(target_row, target_col)
                    if not (data_model.flags(index) & Qt.ItemIsEditable):
                        protected_cells += 1
                    else:
                        data_model.setData(index,
                                table_data[row_offset][col_offset])
        #-
        n, r0, c0, w, h = self.table.get_selection()
        if n == 0:
            msgBox = QMessageBox(parent = self.table)
            msgBox.setText(_COPYFAIL)
            msgBox.exec()
            return
        qapp = QApplication.instance()
        clipboard_text = qapp.clipboard().text()
        table_data = parseTextAsTable(clipboard_text)
        data_model = self.table.model()
        protected_cells = 0
        r1 = r0 + h
        c1 = c0 + w
        try:
            if len(table_data) == 1:    # paste a single row
                if w == 1:              # ... to a single column
                    r = r0
                    while r < r1:
                        do_paste(r, c0)
                        r += 1
                elif len(table_data[0]) == 1:   # paste a single cell
                    r = r0
                    while r < r1:
                        c = c0
                        while c < c1:
                            do_paste(r, c)
                            c += 1
                        r += 1
                else:
                    raise RangeError(_BAD_PASTE_RANGE)
            elif len(table_data[0]) == 1:   # paste a single column
                if h == 1:                  # ... to a single row
                    c = c0
                    while c < c1:
                        do_paste(r0, c)
                        c += 1
                else:
                    raise RangeError(_BAD_PASTE_RANGE)
            elif n == 1:                    # paste to a single cell
                do_paste(r0, c0)
            else:
                raise RangeError(_BAD_PASTE_RANGE)
        except RangeError as e:
            msgBox = QMessageBox(parent=self.table)
            msgBox.setText(str(e))
            msgBox.exec()
            return
        if protected_cells:
            msgBox = QMessageBox(parent = self.table)
            msgBox.setText(_PASTE_PROTECTED)
            msgBox.exec()


class EdiTableWidget(QTableWidget):
    def __init__(self, parent = None):
        super().__init__(parent = parent)
        self.setSelectionMode(self.ContiguousSelection)
        ### Actions
        self.copyCellsAction = CopyCellsAction(self)
        self.addAction(self.copyCellsAction)
        self.pasteCellsAction = PasteCellsAction(self)
        self.addAction(self.pasteCellsAction)
        self.cutCellsAction = CutCellsAction(self)
        self.addAction(self.cutCellsAction)
        self.clearSelectionAction = ClearSelectionAction(self)
        self.addAction(self.clearSelectionAction)

        #self.sep_rowactions = QAction(self)
#Qt bug?: Without the string, only one separator is shown.
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

    def setup(self, rows, columns, parent = None,
            cut = False, paste = False,
            row_add_del = False, column_add_del = False,
#?
            on_changed = None):
        """Inizialize the table.
        Only the copy action is enabled by default.

        :param int rows: number of rows
        :param int columns: number of columns
        :param QWidget parent: Parent
        :param bool cut: Enable cut action
        :param bool paste: Enable paste action
        :param bool row_add_del: Enable adding/deleting a table row
        :param bool col_add_del: Enable adding/deleting a table column
        :param fn on_changed: Callback(row, col, text) for changed cells
        """
        self.setRowCount(rows)
        self.setColumnCount(columns)
        self.clear()
        # Initially no data:
        self.table_data = [[''] * columns for r in range(rows)]
#?
        self.on_changed = on_changed
        # Enable desired actions
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
        self.cellChanged.connect(self.cell_changed)
        self.cellClicked.connect(self.activated)
        self.cellActivated.connect(self.newline_press)

    def row_count(self):
        return self.model().rowCount()

    def column_count(self):
        return self.model().columnCount()

    def get_text(self, row, col):
        data_model = self.model()
        return data_model.data(data_model.index(row, col))

#?
    def set_text(self, row, col, text):
        """To ensure that <self.table_data> is kept up-to-date, cells
        should only be written using this method.
        """
        old = self.table_data[row][col]
        if text != old:
            data_model = self.model()
            data_model.setData(data_model.index(row, col), text)

    def insertRow(self, row):
        newrow = [''] * self.column_count()
        self.table_data.insert(row, newrow)
        super().insertRow(row)
        self.add_change(row, -1, None, newrow)

    def insertColumn(self, column):
        for row in self.table_data:
            row.insert(column, '')
        super().insertColumn(column)
        self.add_change(-1, column, None, [''] * self.row_count())

    def removeRow(self, row):
        rowdata = self.table_data.pop(row)
        super().removeRow(row)
        self.add_change(row, -1, '\t'.join(rowdata), None)

    def removeColumn(self, column):
        coldata = [rowdata.pop(column) for rowdata in self.table_data]
        super().removeColumn(column)
        self.add_change(-1, column, '\t'.join(coldata), None)

    def cell_changed(self, row, col):
        text = self.item(row, col).text()
        old = self.table_data[row][col]
        if old != text:
            self.table_data[row][col] = text
            self.add_change(row, col, old, text)

    def add_change(self, row, column, olddata, newdata):
        """Add each change to a sort of stack for undo/redo support.
        Normally a single cell will be changed, but it is possible to
        insert or delete a whole row or column.
        To insert/delete a column, row is -1.
        To insert/delete a row, column is -1.
        Deleted rows/columns are supplied as tab-separated-value strings.
        """
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
                item = self.currentItem()
                if item:
                    item.setText('')
                return # in this case don't call base class method
        super().keyPressEvent(event)

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

    cols = ["Column %02d" % n for n in range(10)]
    rows = ["Row %02d" % n for n in range(7)]
    tablewidget = EdiTableWidget()
    tablewidget.setup(len(rows), len(cols),
            cut = True, paste = True,
            row_add_del = True, column_add_del = True)

    tablewidget.setWindowTitle("TableWidget")
    tablewidget.setHorizontalHeaderLabels(cols)
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

    tablewidget.setItemDelegateForRow(2, VerticalTextDelegate())
    tablewidget.resizeRowToContents(1)
    tablewidget.resizeRowToContents(2)
    tablewidget.resizeColumnToContents(3)

    tablewidget.resize(600, 400)
    tablewidget.show()
    app.exec()
