# -*- coding: utf-8 -*-
"""
ui/ui_support.py

Last updated:  2021-10-13

Support stuff for the GUI: dialogs, etc.


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

### Messages
_UNKNOWN_KEY = "Ungültige Selektion: '{key}'"

### Dialog buttons, etc.
_CANCEL = "Abbrechen"
_OK = "OK"

_INPUT_TITLE = "Eingabe"
_YESORNO_TITLE = "Ja oder Nein?"
_TEXTAREA_TITLE = "Text eingeben"
_LOSE_CHANGES_TITLE = "Ungespeicherte Änderungen"
_LOSE_CHANGES = "Sind Sie damit einverstanden, dass die Änderungen verloren gehen?"

_INFO = "Mitteilung"
_WARNING = "Warnung"
_ERROR = "Fehler"

_FILEOPEN = "Datei öffnen"
_DIROPEN = "Ordner öffnen"
_FILESAVE = "Datei speichern"

#####################################################

import sys, os, builtins, traceback
from importlib import resources         # Python >= 3.7

from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, \
        QLabel, QPushButton, QComboBox, QFrame, QTextEdit, \
        QDialog, QTreeWidget, QTreeWidgetItem, QMessageBox, \
        QListWidget, QFileDialog, QLineEdit
from qtpy.QtGui import QMovie, QPixmap
from qtpy.QtCore import Qt, QObject, QFile, QIODevice
from qtpy.QtUiTools import QUiLoader

import ui.icons_rc
from ui.xwidgets import GViewResizing

### +++++

class GuiError(Exception):
    pass

### -----

def ui_load(filename):
    """Load a Qt Designer 'ui'-file.
    Folder 'ui/designer' must have an '__init__.py' file (which can be empty).
    """
#    with resources.path('ui.designer', filename) as path:
#        ui_file_name = str(path)
    ui_file_name = os.path.join(DATADIR, 'designer', filename)
    ui_file = QFile(ui_file_name)
    if not ui_file.open(QIODevice.ReadOnly):
        raise GuiError("BUG: Cannot open {}: {}".format(ui_file_name,
                ui_file.errorString()))
#    loader = QUiLoader()
    loader = UiLoader()
#    loader.clearPluginPaths()
#    print("§§§", loader.pluginPaths())
    ui = loader.load(ui_file, None)
    ui_file.close()
    if not ui:
        raise GuiError("BUG: " + loader.errorString())
    return ui

##Add custom widgets thus?
class UiLoader(QUiLoader):
    def createWidget(self, className, parent=None, name=""):
        print("UI:", className, name)
#        if name == 'table_view':
        if className == 'GViewResizing':
            return GViewResizing(parent=parent)
        if className == 'TableWidget':
            from ui.table import TableWidget
            return TableWidget(parent=parent)
        return super().createWidget(className, parent, name)

###

class StackPage:
    """Base class for the behaviour of the page widgets in the main "stack".
    Subclass this to add the required functionality.
    The actual visible widget is referenced by its name.
    """
    def __init__(self, widget_name):
        self.name = widget_name
        self.widget = getattr(WINDOW, widget_name)
#
    def enter(self):
        """Called when a tab page is activated (selected) and when there
        is a change of year (which is treated as a reentry).
        """
        pass
#
    def leave(self):
        """Called to tidy up the data structures of the tab page, for
        example before leaving (deselecting) it.
        """
        pass
#
    def leave_ok(self):
        """If there are unsaved changes, ask whether it is ok to lose
        them. Return <True> if ok to lose them (or if there aren't any
        changes), otherwise <False>.
        """
        if self.is_modified():
            return YesOrNoDialog(_LOSE_CHANGES, _LOSE_CHANGES_TITLE)
        return True
#
    def is_modified(self):
        """Return <True> if there are unsaved changes.
        """
        return False

###

class KeySelector:
    """Modifies the behaviour of an existing (pristine) QComboBox:
    A selection widget for key-description pairs. The key is the
    actual selection item, but the description is displayed for
    human consumption.
    <value_mapping> is a list: ((key, display text), ...)
    To work with a callback, pass a function with a single parameter
    (the new key) as <changed_callback>. If this function does not
    return a true value, the selection will be reset to the last value.
    """
    def __init__(self, widget_name,
            value_mapping = None, changed_callback = None):
        self.name = widget_name
        self.widget = getattr(WINDOW, widget_name)
        self._selected = None
        self._cb = changed_callback
        self.widget.set_items(value_mapping)
# Qt note: If connecting after adding the items, there seems
# to be no signal; if before, then the first item is signalled.
        self.widget.currentIndexChanged.connect(self._new)
#
    def selected(self, display = False):
        try:
            return self.value_mapping[self.widget.currentIndex()][
                    1 if display else 0]
        except:
            return None
#
    def _new(self, index):
        if self.value_mapping and self.changed_callback:
            key = self.value_mapping[index][0]
            if self.changed_callback(key):
                self._selected = index
            else:
                self.changed_callback = None
                self.widget.setCurrentIndex(self._selected)
                self.changed_callback = self._cb
#
    def reset(self, key):
        self.changed_callback = None        # suppress callback
        i = 0
        for k, _ in self.value_mapping:
            if k == key:
                self.widget.setCurrentIndex(i)
                self._selected = i
                break
            i += 1
        else:
            self.changed_callback = self._cb    # reenable callback
            raise GuiError(_UNKNOWN_KEY.format(key = key))
        self.changed_callback = self._cb    # reenable callback
#
    def trigger(self):
        self._new(self.widget.currentIndex())
#
    def set_items(self, value_mapping, index = 0):
        """Set / reset the items.
        <value_mapping> is a list: ((key, display text), ...)
        This will not cause a callback.
        """
        self.changed_callback = None        # suppress callback
        self.value_mapping = value_mapping
        self.widget.clear()
        if value_mapping:
            self.widget.addItems([text for _, text in value_mapping])
            self.widget.setCurrentIndex(index)
            self._selected = index
        self.changed_callback = self._cb    # reenable callback

###

def YesOrNoDialog(message, title = None):
    qd = QDialog()
    qd.setWindowTitle(title or _YESORNO_TITLE)
    vbox = QVBoxLayout(qd)
    vbox.addWidget(QLabel(message))
    vbox.addWidget(HLine())
    bbox = QHBoxLayout()
    vbox.addLayout(bbox)
    bbox.addStretch(1)
    cancel = QPushButton(_CANCEL)
    cancel.clicked.connect(qd.reject)
    bbox.addWidget(cancel)
    ok = QPushButton(_OK)
    ok.clicked.connect(qd.accept)
    bbox.addWidget(ok)
    cancel.setDefault(True)
    return qd.exec_() == QDialog.Accepted

###

def LineDialog(message, text = None, title = None):
    td = QDialog()
    td.setWindowTitle(title or _INPUT_TITLE)
    vbox = QVBoxLayout(td)
    vbox.addWidget(QLabel(message))
    lineedit = QLineEdit(text or '')
    vbox.addWidget(lineedit)
    vbox.addWidget(HLine())
    bbox = QHBoxLayout()
    vbox.addLayout(bbox)
    bbox.addStretch(1)
    cancel = QPushButton(_CANCEL)
    cancel.clicked.connect(td.reject)
    bbox.addWidget(cancel)
    ok = QPushButton(_OK)
    ok.clicked.connect(td.accept)
    bbox.addWidget(ok)
    cancel.setDefault(True)
    if td.exec_() == QDialog.Accepted:
        return lineedit.text().strip()
    return None

###

def TextAreaDialog(message = None, text = None, title = None):
    td = QDialog()
    td.setWindowTitle(title or _TEXTAREA_TITLE)
    vbox = QVBoxLayout(td)
    if message:
        msg = QTextEdit(message)
        msg.setReadOnly(True)
        vbox.addWidget(msg)
    textedit = QTextEdit(text or '')
    vbox.addWidget(textedit)
    vbox.addWidget(HLine())
    bbox = QHBoxLayout()
    vbox.addLayout(bbox)
    bbox.addStretch(1)
    cancel = QPushButton(_CANCEL)
    cancel.clicked.connect(td.reject)
    bbox.addWidget(cancel)
    ok = QPushButton(_OK)
    ok.clicked.connect(td.accept)
    bbox.addWidget(ok)
    cancel.setDefault(True)
    if td.exec_() == QDialog.Accepted:
        return textedit.toPlainText().strip()
    return None

###

def ListSelect(title, message, data, button = None):
    """A simple list widget as selection dialog.
    <data> is a list of (key, display-text) pairs.
    Selection is by clicking or keyboard select and return.
    Can take additional buttons ...?
    """
    select = QDialog()
    select.setWindowTitle(title)
#-
    def select_item(qlwi):
        if select.result == None:
            i = l.row(qlwi)
            select.result = data[i][0]
            select.accept()
#-
    def xb_clicked():
        select.result = (None, button)
        select.accept()
#-
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
    cancel = QPushButton(_CANCEL)
    cancel.setDefault(True)
    cancel.clicked.connect(select.reject)
    bbox.addWidget(cancel)
    if button:
        xb = QPushButton(button)
        xb.clicked.connect(xb_clicked)
        bbox.addWidget(xb)
    select.exec_()
    return select.result

###

def TreeDialog(title, message, data, button = None):
    """A simple two-level tree widget as selection dialog.
    Top level items may not be selected, they serve only as categories.
    Can take additional buttons ...?
    """
    select = QDialog()
    select.setWindowTitle(title)
#-
    def select_item(qtwi, col):
        p = qtwi.parent()
        if p:
            select.result = (p.text(0), qtwi.text(0))
            select.accept()
#-
    def xb_clicked():
        select.result = (None, button)
        select.accept()
#-
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
    cancel = QPushButton(_CANCEL)
    cancel.setDefault(True)
    cancel.clicked.connect(select.reject)
    bbox.addWidget(cancel)
    if button:
        xb = QPushButton(button)
        xb.clicked.connect(xb_clicked)
        bbox.addWidget(xb)
    select.exec_()
    return select.result

###

#TODO: tweak this to make it more readable ... (more spacing?)
def TreeMultiSelect(title, message, data, checked = False):
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
#?    tree.setColumnCount(1)
    tree.setHeaderHidden(True)
    # Enter the data
    for category, dataline in data:
        items = []
        elements.append((category, items))
        parent = QTreeWidgetItem(tree)
        parent.setText(0, category)
        parent.setFlags(parent.flags() | Qt.ItemIsTristate
                | Qt.ItemIsUserCheckable)
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
    cancel = QPushButton(_CANCEL)
    cancel.clicked.connect(select.reject)
    bbox.addWidget(cancel)
    ok = QPushButton(_OK)
    ok.setDefault(True)
    ok.clicked.connect(select.accept)
    bbox.addWidget(ok)
    if select.exec_() == QDialog.Accepted:
        categories = []
        for k, items in elements:
            # Filter the changes lists
            dlist = [d[0] for child, d in items
                    if child.checkState(0) == Qt.Checked]
            categories.append((k, dlist))
        return categories
    else:
        return None

###

def _popupInfo(message):
    QMessageBox.information(None, _INFO, message)
builtins.SHOW_INFO = _popupInfo
##
def _popupWarn(message):
    QMessageBox.warning(None, _WARNING, message)
builtins.SHOW_WARNING = _popupWarn
##
def _popupError(message):
     QMessageBox.critical(None, _ERROR, message)
builtins.SHOW_ERROR = _popupError

### File/Folder Dialogs

def openDialog(filetype, title = None):
    dir0 = SETTINGS.value('LAST_LOAD_DIR') or os.path.expanduser('~')
    fpath = QFileDialog.getOpenFileName(None, title or _FILEOPEN,
            dir0, filetype)[0]
    if fpath:
        SETTINGS.setValue('LAST_LOAD_DIR', os.path.dirname(fpath))
    return fpath
##
def dirDialog(title = None):
    dir0 = SETTINGS.value('LAST_LOAD_DIR') or os.path.expanduser('~')
    dpath = QFileDialog.getExistingDirectory(None, title or _DIROPEN, dir0,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
    if dpath:
        SETTINGS.setValue('LAST_LOAD_DIR', dpath)
    return dpath
##
def saveDialog(filetype, filename, title = None):
    dir0 = SETTINGS.value('LAST_SAVE_DIR') or os.path.expanduser('~')
    fpath = QFileDialog.getSaveFileName(None, title or _FILESAVE,
            os.path.join(dir0, filename), filetype)[0]
    if fpath:
        SETTINGS.setValue('LAST_SAVE_DIR', os.path.dirname(fpath))
    return fpath


############### Handle uncaught exceptions ###############
class UncaughtHook(QObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This registers the <exception_hook> method as hook with
        # the Python interpreter
        sys.excepthook = self.exception_hook
#
    def exception_hook(self, exc_type, exc_value, exc_traceback):
        """Function handling uncaught exceptions.
        It is triggered each time an uncaught exception occurs.
        """
        log_msg = '{val}\n\n$${emsg}'.format(
                val = exc_value, emsg = ''.join(traceback.format_exception(
                        exc_type, exc_value, exc_traceback)))
        # Show message
        SHOW_ERROR('*** TRAP ***\n' + log_msg)

# Create a global instance of <UncaughtHook> to register the hook
qt_exception_hook = UncaughtHook()
