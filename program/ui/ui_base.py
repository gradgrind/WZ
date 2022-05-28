"""
ui/ui_base.py

Last updated:  2022-05-28

Support stuff for the GUI: application initialization, dialogs, etc.


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

#####################################################

import sys, os, locale, builtins, traceback, glob

# TODO: PySide6 only?: If I use this feature, this is probably the wrong path ...
# Without the environment variable there is a disquieting error message.
#    os.environ['PYSIDE_DESIGNER_PLUGINS'] = this

# Import all qt stuff
from qtpy.QtWidgets import *
from qtpy.QtGui import *
from qtpy.QtCore import *
from qtpy.QtSql import *

APP = QApplication(sys.argv)
print("LOCALE:", locale.setlocale(locale.LC_ALL, ""))
path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
translator = QTranslator(APP)
if translator.load(QLocale.system(), "qtbase", "_", path):
    APP.installTranslator(translator)
# ?
SETTINGS = QSettings(QSettings.IniFormat, QSettings.UserScope, "MT", "WZ")

# This seems to deactivate activate-on-single-click in filedialog
# (presumably elsewhere as well?)
APP.setStyleSheet("QAbstractItemView { activate-on-singleclick: 0; }")

def run(window):
    window.show()
    sys.exit(APP.exec())


class GuiError(Exception):
    pass


T = TRANSLATIONS("ui.ui_base")

### -----


class HLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class VLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)


def get_icon(name):
    ilist = glob.glob(APPDATAPATH(f"icons/{name}.*"))
    return QIcon(ilist[0])


class StackPage(QWidget):
    """Base class for the page widgets ("tab" widgets) in the main "stack".
    Subclass this to add the required functionality.
    The actual visible widget is referenced by its name.
    """

    name = T["MODULE_NAME"]
    title = T["MODULE_TITLE"]

    def enter(self):
        """Called when a tab page is activated (selected) and when there
        is a change of year (which is treated as a reentry).
        """
        pass

    def leave(self):
        """Called to tidy up the data structures of the tab page, for
        example before leaving (deselecting) it.
        """
        pass

    def leave_ok(self):
        """If there are unsaved changes, ask whether it is ok to lose
        them. Return <True> if ok to lose them (or if there aren't any
        changes), otherwise <False>.
        """
        if self.is_modified():
            return LoseChangesDialog()
        return True

    def is_modified(self):
        """Return <True> if there are unsaved changes."""
        return False


class StandalonePage(StackPage):
    name = "StandalonePage"

    def closeEvent(self, event):
        if self.leave_ok():
            event.accept()
            #super().closeEvent(event)
        else:
            event.ignore()


class KeySelector(QComboBox):
    """A modified QComboBox:
    A selection widget for key-description pairs. The key is the
    actual selection item, but the description is displayed for
    human consumption.
    <value_mapping> is a list: ((key, display text), ...)
    To work with a callback, pass a function with a single parameter
    (the new key) as <changed_callback>. If this function does not
    return a true value, the selection will be reset to the last value.
    """

    def __init__(self, value_mapping=None, changed_callback=None):
        super().__init__()
        self._selected = None
        self._cb = changed_callback
        self.set_items(value_mapping)
        # Qt note: If connecting after adding the items, there seems
        # to be no signal; if before, then the first item is signalled.
        self.currentIndexChanged.connect(self._new)

    def selected(self, display=False):
        try:
            return self.value_mapping[self.currentIndex()][1 if display else 0]
        except IndexError:
            return None

    def _new(self, index):
        if self.value_mapping and self.changed_callback:
            key = self.value_mapping[index][0]
            if self.changed_callback(key):
                self._selected = index
            else:
                self.changed_callback = None
                self.setCurrentIndex(self._selected)
                self.changed_callback = self._cb

    def reset(self, key):
        self.changed_callback = None  # suppress callback
        i = 0
        for k, _ in self.value_mapping:
            if k == key:
                self.setCurrentIndex(i)
                self._selected = i
                break
            i += 1
        else:
            self.changed_callback = self._cb  # reenable callback
            raise GuiError(T["UNKNOWN_KEY"].format(key=key))
        self.changed_callback = self._cb  # reenable callback

    def trigger(self):
        self._new(self.currentIndex())

    def set_items(self, value_mapping, index=0):
        """Set / reset the items.
        <value_mapping> is a list: ((key, display text), ...)
        This will not cause a callback.
        """
        self.changed_callback = None  # suppress callback
        self.value_mapping = value_mapping
        self.clear()
        if value_mapping:
            self.addItems([text for _, text in value_mapping])
            self.setCurrentIndex(index)
            self._selected = index
        self.changed_callback = self._cb  # reenable callback


def YesOrNoDialog(message, title=None):
    qd = QDialog()
    qd.setWindowTitle(title or _YESORNO_TITLE)
    vbox = QVBoxLayout(qd)
    vbox.addWidget(QLabel(message))
    vbox.addWidget(HLine())
    bbox = QHBoxLayout()
    vbox.addLayout(bbox)
    bbox.addStretch(1)
    cancel = QPushButton(T["CANCEL"])
    cancel.clicked.connect(qd.reject)
    bbox.addWidget(cancel)
    ok = QPushButton(T["OK"])
    ok.clicked.connect(qd.accept)
    bbox.addWidget(ok)
    cancel.setDefault(True)
    return qd.exec_() == QDialog.Accepted


def LoseChangesDialog():
    return YesOrNoDialog(T["LOSE_CHANGES"], T["LOSE_CHANGES_TITLE"])


def LineDialog(message, text=None, title=None):
    td = QDialog()
    td.setWindowTitle(title or _INPUT_TITLE)
    vbox = QVBoxLayout(td)
    vbox.addWidget(QLabel(message))
    lineedit = QLineEdit(text or "")
    vbox.addWidget(lineedit)
    vbox.addWidget(HLine())
    bbox = QHBoxLayout()
    vbox.addLayout(bbox)
    bbox.addStretch(1)
    cancel = QPushButton(T["CANCEL"])
    cancel.clicked.connect(td.reject)
    bbox.addWidget(cancel)
    ok = QPushButton(T["OK"])
    ok.clicked.connect(td.accept)
    bbox.addWidget(ok)
    cancel.setDefault(True)
    if td.exec_() == QDialog.Accepted:
        return lineedit.text().strip()
    return None


def TextAreaDialog(message=None, text=None, title=None):
    td = QDialog()
    td.setWindowTitle(title or T["TEXTAREA_TITLE"])
    vbox = QVBoxLayout(td)
    if message:
        msg = QTextEdit(message)
        msg.setReadOnly(True)
        vbox.addWidget(msg)
    textedit = QTextEdit(text or "")
    vbox.addWidget(textedit)
    vbox.addWidget(HLine())
    bbox = QHBoxLayout()
    vbox.addLayout(bbox)
    bbox.addStretch(1)
    cancel = QPushButton(T["CANCEL"])
    cancel.clicked.connect(td.reject)
    bbox.addWidget(cancel)
    ok = QPushButton(T["OK"])
    ok.clicked.connect(td.accept)
    bbox.addWidget(ok)
    cancel.setDefault(True)
    if td.exec_() == QDialog.Accepted:
        return textedit.toPlainText().strip()
    return None


def ListSelect(title, message, data, button=None):
    """A simple list widget as selection dialog.
    <data> is a list of (key, display-text) pairs.
    Selection is by clicking or keyboard select and return.
    Can take additional buttons ...?
    """
    select = QDialog()
    select.setWindowTitle(title)

    def select_item(qlwi):
        if select.result == None:
            i = l.row(qlwi)
            select.result = data[i][0]
            select.accept()

    def xb_clicked():
        select.result = (None, button)
        select.accept()

    select.result = None
    layout = QVBoxLayout(select)
    layout.addWidget(QLabel(message))
    l = QListWidget()
    l.itemActivated.connect(select_item)
    l.itemClicked.connect(select_item)
    layout.addWidget(l)
    for k, d in data:
        l.addItem(d)
    select.resize(300, 400)
    # Now the buttons
    layout.addWidget(HLine())
    bbox = QHBoxLayout()
    layout.addLayout(bbox)
    bbox.addStretch(1)
    cancel = QPushButton(T["CANCEL"])
    cancel.setDefault(True)
    cancel.clicked.connect(select.reject)
    bbox.addWidget(cancel)
    if button:
        xb = QPushButton(button)
        xb.clicked.connect(xb_clicked)
        bbox.addWidget(xb)
    select.exec_()
    return select.result


def TreeDialog(title, message, data, button=None):
    """A simple two-level tree widget as selection dialog.
    Top level items may not be selected, they serve only as categories.
    Can take additional buttons ...?
    """
    select = QDialog()
    select.setWindowTitle(title)

    def select_item(qtwi, col):
        p = qtwi.parent()
        if p:
            select.result = (p.text(0), qtwi.text(0))
            select.accept()

    def xb_clicked():
        select.result = (None, button)
        select.accept()

    layout = QVBoxLayout(select)
    layout.addWidget(QLabel(message))
    tree = QTreeWidget()
    layout.addWidget(tree)
    tree.setColumnCount(1)
    tree.setHeaderHidden(True)
    tree.itemClicked.connect(select_item)
    for category, items in data:
        tline = QTreeWidgetItem(tree)
        tline.setText(0, category)
        for item in items:
            tatom = QTreeWidgetItem(tline)
            tatom.setText(0, item)
    tree.expandAll()
    select.resize(500, 300)
    select.result = None
    # Now the buttons
    layout.addWidget(HLine())
    bbox = QHBoxLayout()
    layout.addLayout(bbox)
    bbox.addStretch(1)
    cancel = QPushButton(T["CANCEL"])
    cancel.setDefault(True)
    cancel.clicked.connect(select.reject)
    bbox.addWidget(cancel)
    if button:
        xb = QPushButton(button)
        xb.clicked.connect(xb_clicked)
        bbox.addWidget(xb)
    select.exec_()
    return select.result


def TreeMultiSelect(title, message, data, checked=False):
    """A simple two-level tree widget as selection dialog.
    Top level items may not be selected, they serve only as categories.
    Any number of entries (atoms/leaves) may be selected.
    The data is supplied as a multilevel list:
        [[category1, [[val, display-val], ...]], [category2, ... ], ... ]
    """
    select = QDialog()
    select.setWindowTitle(title)
    layout = QVBoxLayout(select)
    layout.addWidget(QLabel(message))
    ### The tree widget
    elements = []
    tree = QTreeWidget()
    layout.addWidget(tree)
    # ?    tree.setColumnCount(1)
    tree.setHeaderHidden(True)
    # Enter the data
    for category, dataline in data:
        items = []
        elements.append((category, items))
        parent = QTreeWidgetItem(tree)
        parent.setText(0, category)
        parent.setFlags(parent.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
        for d in dataline:
            child = QTreeWidgetItem(parent)
            items.append((child, d))
            child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
            child.setText(0, d[1])
            child.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
    tree.expandAll()
    select.resize(500, 300)
    select.result = None
    ### Now the buttons
    layout.addWidget(HLine())
    bbox = QHBoxLayout()
    layout.addLayout(bbox)
    bbox.addStretch(1)
    cancel = QPushButton(T["CANCEL"])
    cancel.clicked.connect(select.reject)
    bbox.addWidget(cancel)
    ok = QPushButton(T["OK"])
    ok.setDefault(True)
    ok.clicked.connect(select.accept)
    bbox.addWidget(ok)
    if select.exec_() == QDialog.Accepted:
        categories = []
        for k, items in elements:
            # Filter the changes lists
            dlist = [d[0] for child, d in items if child.checkState(0) == Qt.Checked]
            categories.append((k, dlist))
        return categories
    else:
        return None


def _popupInfo(message):
    QMessageBox.information(None, T["INFO"], message)


def _popupWarn(message):
    QMessageBox.warning(None, T["WARNING"], message)


def _popupError(message):
    QMessageBox.critical(None, T["ERROR"], message)


def _popupConfirm(question):
    return (
        QMessageBox.question(
            None,
            T["CONFIRMATION"],
            question,
            buttons=QMessageBox.Ok | QMessageBox.Cancel,
            defaultButton=QMessageBox.Ok,
        )
        == QMessageBox.Ok
    )

builtins.SHOW_INFO = _popupInfo
builtins.SHOW_WARNING = _popupWarn
builtins.SHOW_ERROR = _popupError
builtins.SHOW_CONFIRM = _popupConfirm

### File/Folder Dialogs

def openDialog(filetype, title=None):
    dir0 = SETTINGS.value("LAST_LOAD_DIR") or os.path.expanduser("~")
    fpath = QFileDialog.getOpenFileName(None, title or _FILEOPEN, dir0, filetype)[0]
    if fpath:
        SETTINGS.setValue("LAST_LOAD_DIR", os.path.dirname(fpath))
    return fpath


def dirDialog(title=None):
    dir0 = SETTINGS.value("LAST_LOAD_DIR") or os.path.expanduser("~")
    dpath = QFileDialog.getExistingDirectory(
        None,
        title or T["DIROPEN"],
        dir0,
        QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
    )
    if dpath:
        SETTINGS.setValue("LAST_LOAD_DIR", dpath)
    return dpath


def saveDialog(filetype, filename, title=None):
    dir0 = SETTINGS.value("LAST_SAVE_DIR") or os.path.expanduser("~")
    fpath = QFileDialog.getSaveFileName(
        None, title or T["FILESAVE"], os.path.join(dir0, filename), filetype
    )[0]
    if fpath:
        SETTINGS.setValue("LAST_SAVE_DIR", os.path.dirname(fpath))
    return fpath


#TODO: deprecated, see <RowSelectTable>
#class TableViewRowSelect(QTableView):
#    """A QTableView with single row selection and restrictions on change
#    of selection.
#
#    In order to accept a change of row via the mouse, the "main" widget
#    (supplied as argument to the constructor) must have a "modified"
#    method returning false. If the result is true, a pop-up will ask
#    for confirmation.
#
#    This implementation avoids some very strange selection behaviour
#    in QTableView, which I assume to be a bug:
#    Programmatic switching of the selected row doesn't necessarily cause
#    the visible selection (blue background) to move, although the
#    current (selected) row does change. Clicking and moving (slightly
#    dragging) the mouse produce different responses.
#    """
#TODO: Note that when the selection is changed via the keyboard, the
# "modified" method is not called! However, in the intended use case,
# it is pretty unlikely that this will be a problem.
#
# By using a QTimer I think the normal selection-changed signal can be
# used, together with a memory of the currently active item ...
#
#    def __init__(self, main_widget):
#        super().__init__()
#        self.__modified = main_widget.modified
#        self.setSelectionMode(QTableView.SingleSelection)
#        self.setSelectionBehavior(QTableView.SelectRows)
#
#    def mousePressEvent(self, e):
#        index = self.indexAt(e.pos())
#        if index.isValid() and (
#            (not self.__modified()) or LoseChangesDialog()
#        ):
#            self.selectRow(index.row())
#
#    def mouseMoveEvent(self, e):
#        pass


class RowSelectTable(QTableView):
    """A QTableView with single row selection and the possibility to
    block selection changes when there is unsaved data.

    A callback function (<is_modified>) can be provided which is called
    when the current item changes. If this returns true, a dialog will
    pop up asking whether to ignore (i.e. lose) changes. If the
    dialog returns false, the item change will not be permitted.
    """
    def __init__(self, is_modified=None, name=None):
        super().__init__()
        self.__name = name
        self.__row = -1
        self.__modified = is_modified
        self.__callback = None
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

    def set_callback(self, row_changed):
        self.__callback = row_changed

    def __revert(self):
        self.selectRow(self.__row)

    def currentChanged(self, currentitem, olditem):
        super().currentChanged(currentitem, olditem)
        row = currentitem.row() # -1 => no current item
        #print(f"CURRENT CHANGED ({self.__name}):", olditem.row(), "-->", row)
        if olditem.row() == row:
            # Actually, this shouldn't be possible, but -1 -> -1 does
            # occur!
            return
        if self.__modified:
            if row == self.__row:
                self.__row = -1
                return
            if self.__modified():
                if self.__row >= 0:
                    raise Bug("Row change error")
                elif not LoseChangesDialog():
                    self.__row = olditem.row()
                    # The timer is necessary to avoid the selection and
                    # current item getting out of sync
                    QTimer.singleShot(0, self.__revert)
                    return
            self.__row = -1
        #print("  ... ACCEPTED")
        if self.__callback:
            self.__callback(row)


class FormLineEdit(QLineEdit):
    """A specialized line editor for use in the editor form for a
    "RowSelectTable" table view.

    The constructor receives the name of the field and a function which
    is to be called when the selected value is changed. This function
    takes the field name and a boolean (value != initial value, set by
    the "setText" method).
    The extra parameter "width_hint" allows the default width of the
    widget to be set; in particular this allows narrower widgets.
    """

    def __init__(self, field, modified, parent=None, width_hint=None):
        self.width_hint = width_hint
        super().__init__(parent)
        self.__modified = modified
        self.__field = field
        self.text0 = None
        self.textEdited.connect(self.text_edited)

    def setText(self, text):
        super().setText(text)
        self.text0 = text

    def text_edited(self, text):
        self.__modified(self.__field, text != self.text0)

    def sizeHint(self):
        sh = super().sizeHint()
        if self.width_hint and sh.isValid():
            return QSize(self.width_hint, sh.height())
        return sh


#deprecated?
class FormComboBox(QComboBox):
    """A specialized combobox for use in the editor form for a
    "RowSelectTable" table view. This combobox is used for editing
    foreign key fields by offering the available values to choose from.

    The constructor receives the name of the field and a function which
    is to be called when the selected value is changed. This function
    takes the field name and a boolean (value != initial value, set by
    the "setText" method).

    Also the "setup" method must be called to initialize the contents.
    """

    def __init__(self, field, modified, parent=None):
        super().__init__(parent)
        self.__modified = modified
        self.__field = field
        self.text0 = None
        self.currentIndexChanged.connect(self.change_index)

    def setup(self, key_value):
        """Set up the indexes required for the table's item delegate
        and the combobox (<editwidget>).

        The argument is a list [(key, value), ... ].
        """
        self.keylist = []
        self.key2i = {}
        self.clear()
        i = 0
        self.callback_enabled = False
        for k, v in key_value:
            self.key2i[k] = i
            self.keylist.append(k)
            self.addItem(v)
            i += 1
        self.callback_enabled = True

    def text(self):
        """Return the current "key"."""
        return self.keylist[self.currentIndex()]

    def setText(self, text):
        """<text> is the "key"."""
        if text:
            try:
                i = self.key2i[text]
            except KeyError:
                raise Bug(
                    f"Unknown key for editor field {self.__field}: '{text}'"
                )
            self.text0 = text
            self.setCurrentIndex(i)
        else:
            self.text0 = self.keylist[0]
            self.setCurrentIndex(0)

    def change_index(self, i):
        if self.callback_enabled:
            self.__modified(self.__field, self.keylist[i] != self.text0)


class ForeignKeyItemDelegate(QStyledItemDelegate):
    """An "item delegate" for displaying referenced values in
    foreign key fields. The mapping to the display values is supplied
    as a parameter, a list: [(key, value), ... ].
    """

    def __init__(self, key_value, parent=None):
        super().__init__(parent)
        self.key2value = dict(key_value)

    def displayText(self, key, locale):
        return self.key2value[key]


############### Handle uncaught exceptions ###############
class UncaughtHook(QObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This registers the <exception_hook> method as hook with
        # the Python interpreter
        sys.excepthook = self.exception_hook

    def exception_hook(self, exc_type, exc_value, exc_traceback):
        """Function handling uncaught exceptions.
        It is triggered each time an uncaught exception occurs.
        """
        log_msg = "{val}\n\n$${emsg}".format(
            val=exc_value,
            emsg="".join(
                traceback.format_exception(exc_type, exc_value, exc_traceback)
            ),
        )
        # Show message
        SHOW_ERROR("*** TRAP ***\n" + log_msg)


# Create a global instance of <UncaughtHook> to register the hook
qt_exception_hook = UncaughtHook()
