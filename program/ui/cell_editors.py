"""
ui/cell_editors.py

Last updated:  2022-12-04

Pop-up editors for table grids.

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
"""

from qtpy.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QListWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QDialogButtonBox,
    QCalendarWidget,
    QLabel
)
from qtpy.QtCore import Qt, QDate

### -----


class CellEditorTable(QDialog):
    def __init__(self, items):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        vbox = QVBoxLayout(self)
        self.table = QTableWidget(self)
        vbox.addWidget(self.table)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()
        self.table.itemActivated.connect(self._select)
        self.table.itemClicked.connect(self._select)
        # Enter the data
        coln = 0
        extracol = 0
        for row in items:
            l = len(row[0])
            if l > coln:
                coln = l
            if row[1]:
                extracol = 1
        nrows = len(items)
        self.table.setColumnCount(coln + extracol)
        self.table.setRowCount(nrows)
        r = 0
        for row in items:
            c = 0
            for val in row[0]:
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignHCenter)
                item.setFlags(
                    Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                )
                item._text = val
                self.table.setItem(r, c, item)
                c += 1
            comment = row[1]
            if comment:
                item = QTableWidgetItem(comment)
                item.setFlags(Qt.ItemFlag.NoItemFlags)
#                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(r, coln, item)
                item._text = None
            r += 1
        # This is all about fitting to contents, first the table,
        # then the window
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        h = 0
        for r in range(nrows):
            h += self.table.rowHeight(r)
        w = 0
        for c in range(coln + extracol):
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

    def activate(self, pos, properties):
        self.move(pos)
        text0 = properties["TEXT"]
        if self.exec():
            if self._value != text0:
                properties["TEXT"] = self._value
                return True
        return False


class CellEditorDate(QDialog):
    def __init__(self, empty_ok=False):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        vbox = QVBoxLayout(self)
        self.cal = QCalendarWidget(self)
        self.cal.setGridVisible(True)
        self.cal.clicked[QDate].connect(self.new_date)
        vbox.addWidget(self.cal)
        self.lbl = QLabel(self)
        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel
            | QDialogButtonBox.Reset
        )
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        buttonBox.button(QDialogButtonBox.Reset).clicked.connect(self.reset)
        vbox.addWidget(self.lbl)
        vbox.addWidget(buttonBox)
        self.setLayout(vbox)
        buttonBox.button(QDialogButtonBox.Reset).setEnabled(empty_ok)

    def activate(self, pos, properties):
        date0 = properties["VALUE"]
        self.cal.setSelectedDate(
            QDate.fromString(date0, "yyyy-MM-dd")
            if date0
            else QDate.currentDate()
        )
        self.new_date(self.cal.selectedDate())
        self.move(pos)
        if self.exec():
            if self.date != date0:
                properties["VALUE"] = self.date
                properties["TEXT"] = self.lbl.text()
                return True
        return False

    def new_date(self, qdate):
        self.date = qdate.toString(Qt.DateFormat.ISODate)
        self.lbl.setText(self.date)

    def reset(self):
        self.date = ""
        self.lbl.setText("")
        self.accept()


class CellEditorText(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        vbox = QVBoxLayout(self)
        self.textedit = QTextEdit(self)
        self.textedit.setTabChangesFocus(True)
        vbox.addWidget(self.textedit)
        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        vbox.addWidget(buttonBox)

    def activate(self, pos, properties):
        text0 = properties["TEXT"]
        self.textedit.setPlainText(text0)
        self.move(pos)
        if self.exec():
            text = self.textedit.toPlainText()
            if text != text0:
                properties["TEXT"] = text
                return True
        return False


class CellEditorLine(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        vbox = QVBoxLayout(self)
        self.lineedit = QLineEdit(self)
        vbox.addWidget(self.lineedit)
        self.lineedit.returnPressed.connect(self.accept)

    def activate(self, pos, properties):
        text0 = properties["TEXT"]
        self.lineedit.setText(text0)
        self.move(pos)
        if self.exec():
            text = self.lineedit.text()
            if text != text0:
                properties["TEXT"] = text
                return True
        return False


# TODO
class CellEditorList(QDialog):
    def __init__(self, items, display_items=None):
        super().__init__()
        self.__items = items
        self.__display_items = display_items
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        vbox = QVBoxLayout(self)
        self.listbox = QListWidget(self)
        # TODO
        #        self.setFixedWidth(60)
        if display_items:
            self.listbox.addItems(display_items)
        else:
            self.listbox.addItems(items)
        # Width?
        vbox.addWidget(self.listbox)
        self.listbox.itemClicked.connect(self.accept)

    def activate(self, pos, properties):
        text0 = properties["TEXT"]
        try:
            i = self.__items.index(text0)
        except ValueError:
            pass
        else:
            self.listbox.setCurrentRow(i)
        self.move(pos)
        if self.exec():
            # TODO: especially for the case when display items are used
            i = self.listbox.currentRow()
            text = self.__items[i]
            if text != text0:
                properties["TEXT"] = text
                return True
        return False
