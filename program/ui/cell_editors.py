"""
ui/cell_editors.py

Last updated:  2022-12-24

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
    QApplication,
    QStyle,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QDialogButtonBox,
    QCalendarWidget,
    QLabel,
    QAbstractItemView,
)
from qtpy.QtCore import Qt, QDate, QSize

### -----


class CellEditorTable(QDialog):
    def __init__(self, items):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        vbox = QVBoxLayout(self)
        hbox = QHBoxLayout()
        vbox.addLayout(hbox)
        self.table = QTableWidget(self)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        hbox.addWidget(self.table)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()
        self.table.itemActivated.connect(self._select)
        self.table.itemClicked.connect(self._select)
        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Cancel
        )
        buttonBox.setOrientation(Qt.Orientation.Vertical)
        buttonBox.rejected.connect(self.reject)
        hbox.addWidget(buttonBox)
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
        self.val2item = {}
        for row in items:
            c = 0
            for val in row[0]:
                item = QTableWidgetItem(val)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
                )
                item.setFlags(
                    Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                )
                item._text = val
                self.table.setItem(r, c, item)
                self.val2item[val] = item
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
        if pos:
            self.move(pos)
        text0 = properties["VALUE"]
        try:
            self.table.setCurrentItem(self.val2item[text0])
        except KeyError:
            pass
        if self.exec():
            if self._value != text0:
                properties["VALUE"] = self._value
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
    def __init__(self, newline="\\n"):
        """Display a text editor widget with multiline capability.
        if <newline> is not empty, the stored value will have this
        string instead of a newline.
        """
        self.newline = newline
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
        text0 = properties["VALUE"]
        if self.newline:
            text0 = text0.replace(self.newline, "\n")
        self.textedit.setPlainText(text0)
        self.move(pos)
        if self.exec():
            text = self.textedit.toPlainText()
            if text != text0:
                if self.newline:
                    text = text.replace("\n", self.newline)
                properties["VALUE"] = text
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
        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        vbox.addWidget(buttonBox)

    def activate(self, pos, properties):
        text0 = properties["VALUE"]
        self.lineedit.setText(text0)
        self.move(pos)
        if self.exec():
            text = self.lineedit.text()
            if text != text0:
                properties["VALUE"] = text
                return True
        return False


class CellEditorCheckList(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        hbox = QHBoxLayout(self)
        self.listbox = ListWidget()
        self.listbox.setSpacing(5)
        self.listbox.setSelectionMode(QAbstractItemView.NoSelection)
        self.listbox.itemChanged.connect(self.item_changed)
        hbox.addWidget(self.listbox)
        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttonBox.setOrientation(Qt.Orientation.Vertical)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        hbox.addWidget(buttonBox)

    def set_list(self, items):
        self.listbox.clear()
        self.listbox.addItems(items)

    def item_changed(self, lwi:QListWidgetItem):
        """This should be overridden in a subclass if some action is
        required when an item is toggled.
        """
        pass

    def activate(self, pos, properties):
        set0 = self.to_set(properties["VALUE"])
        for n in range(self.listbox.count()):
            lwi = self.listbox.item(n)
            text = lwi.text()
            lwi.setCheckState(
                Qt.CheckState.Checked
                if text in set0
                else Qt.CheckState.Unchecked
            )
        self.move(pos)
        if self.exec():
            set1 = self.get_checked_item_set()
            if set1 != set0:
                properties["VALUE"] = self.from_set(set1)
                return True
        return False

    def to_set(self, val):
        return set(val.split())

    def from_set(self, val):
        return " ".join(sorted(val))

    def get_checked_item_set(self):
        cis = set()
        for n in range(self.listbox.count()):
            lwi = self.listbox.item(n)
            if lwi.checkState() == Qt.CheckState.Checked:
                cis.add(lwi.text())
        return cis


class CellEditorList(QDialog):
    def __init__(self, items, display_items=None, label=None):
        super().__init__()
        self.__items = items
        self.__display_items = display_items
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        vbox = QVBoxLayout(self)
        if label:
            label = QLabel(label)
            label.setWordWrap(True)
            vbox.addWidget(label)
        self.listbox = QListWidget(self)
        # TODO?
        #        self.setFixedWidth(60)
        if display_items:
            self.listbox.addItems(display_items)
        else:
            self.listbox.addItems(items)
        vbox.addWidget(self.listbox)
        self.listbox.itemClicked.connect(self.accept)
        self.listbox.itemActivated.connect(self.accept)
        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Cancel
        )
        #buttonBox.setOrientation(Qt.Orientation.Vertical)
        buttonBox.rejected.connect(self.reject)
        vbox.addWidget(buttonBox)

    def activate(self, pos, properties):
        text0 = properties["VALUE"]
        try:
            i = self.__items.index(text0)
        except ValueError:
            pass
        else:
            self.listbox.setCurrentRow(i)
        if pos:
            self.move(pos)
        if self.exec():
            i = self.listbox.currentRow()
            text = self.__items[i]
            if text != text0:
                properties["VALUE"] = text
                return True
        return False


#############################################################


class ListWidget(QListWidget):
    def sizeHint(self):
        s = QSize()
        s.setHeight(super().sizeHint().height())
        scrollbarwidth = (
            QApplication.instance()
            .style()
            .pixelMetric(QStyle.PM_ScrollBarExtent)
        )
        # The scroll-bar width alone is not quite enough ...
        s.setWidth(self.sizeHintForColumn(0) + scrollbarwidth + 5)
        # print("???", s, scrollbarwidth)
        return s


if __name__ == "__main__":
    import sys

    # Import all qt stuff
    from qtpy.QtCore import QPoint

    # print("STYLES:", QStyleFactory.keys())
    QApplication.setStyle("Fusion")
    APP = QApplication(sys.argv)

    # This seems to deactivate activate-on-single-click in filedialog
    # (presumably elsewhere as well?)
    APP.setStyleSheet("QAbstractItemView { activate-on-singleclick: 0; }")

    clist = CellEditorCheckList()
    clist.set_list(["A", "B", "R", "G", "I", "II", "III"])
    props = {"VALUE": 'G A'}
    print("?????", clist.activate(QPoint(100, 200), props))
    print("+++++", props)
    quit(0)
