# -*- coding: utf-8 -*-
"""
ui/tab_pupils.py

Last updated:  2021-04-04

Pupil table management.


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

### Labels, etc.
_UPDATE_PUPILS = "Schülerdaten verwalten"
_UPDATE_PUPILS_TEXT = """## Keine Klasse (bzw. alle Klassen)

Auf dieser Seite gibt es zwei optionen:
 - Die gesamten Schülerdaten können als Tabellendatei (xlsx oder tsv)
gespeichert werden.
 - Die gesamten Schülerdaten können von einer externen Tabelle
aktualisiert werden.

Bei der Aktualisierung werden nur die Felder, die in der Tabellendatei
vorhanden sind, berücksichtigt. Alle anderen Felder in der Datenbank
bleiben unverändert. Zusätzliche Felder in der Eingabetabelle, die für
die Datenbank nicht relevant sind, werden ignoriert.

Die Änderungen zu den bestehenden Daten werden angezeigt. Anhand dieser
Baum-Anzeige können Sie wählen, welche dann tatsächlich umgesetzt werden.

## Klasse auswählen

Zuerst wird eine Tabelle mit den Daten von allen Schülern in der gewählten
Klasse angezeigt.

Diese Daten können auch geändert werden. Wenn Änderungen eingegeben werden,
werden sie nicht sofort gespeichert. Das Abspeichern muss durch
Anklicken der entsprechenden Schaltfläche ausgelöst werden.

Durch weitere Schaltflächen können Sie
 - einen neuen Schüler aufnehmen. Durch Anklicken dieser Schaltfläche
erscheint eine Tabelle, in die Sie die Daten des Schülers eingeben können.
 - einen Schüler aus der Datenbank entfernen.

*Achtung:* Normalerweise sollten Schüler nicht aus der Datenbank entfernt
werden, sondern durch ein Datum im Feld „Schulaustritt“ als „nicht
mehr vorhanden“ gekennzeichnet werden.

Es gibt auch die Möglichkeit die Daten dieser Klasse als Tabellendatei
zu speichern. Eine solche Tabelle kann auch eingelesen werden um die
Klassendaten aus einer externen Quelle zu aktualisieren.

## Schüler auswählen

Wenn ein Schüler im Menü unter dem Klassenmenü ausgewählt wird, werden
nur die Daten des gewählten Schülers angezeigt. Auch die Einträge in
dieser Tabelle können geändert werden. Für manche Felder (z.B. Datum)
gibt es hier angepasste Eingabe-Methoden.
"""
_DELTA_TEXT = """Die möglichen Änderungen werden als Baum dargestellt.
Indem Sie auf die entsprechenden Kontrollfelder klicken, können Sie
einzelne Änderungen (ab)wählen. Durch das Kontrollfeld einer Klasse
können alle Änderungen einer Klasse (ab)gewählt werden.

Um die Änderungen auszuführen, klicken Sie auf die Schaltfläche „Speichern“.
"""

_DELTA_QUIT = "Abbrechen"
_CLASS = "Klasse:"
_SAVE = "Änderungen Speichern"
_NEW_PUPIL = "Neuer Schüler"
_REMOVE_PUPIL = "Schüler entfernen"
_EXPORT = "Tabelle exportieren"
_IMPORT = "Tabelle importieren"
_ALL_CLASSES = "* Alle Klassen *"
_ALL_PUPILS = "* Ganze Klasse *"
_ENTER_PID_TITLE = "Neue Schülerkennung"
_ENTER_PID = "Wählen Sie eine neue,\neindeutige Schülerkennung"
_REMOVE_TITLE = "Schülerdaten löschen"
_REMOVE = "Wollen Sie wirklich {name} aus der Datenbank entfernen?"
_REMOVE_PID = "Wollen Sie wirklich Schüler {pid} aus der Datenbank entfernen?"
_NO_CHANGES = "Fertig?"
_WARN_NO_CHANGES = "Sie haben keine Änderungen gewählt.\n" \
        "Wollen Sie diese Ansicht verlassen?"

_FILEOPEN = "Datei öffnen"
_TABLE_FILE = "Tabellendatei (*.xlsx *.ods *.tsv)"
_SAVE_TABLE_FILE = "Tabellendatei (*.xlsx *.tsv)"
_TABLE_FILE_NAME = "Schuelerdaten_{klass}"
_FULL_TABLE_FILE_NAME = "Schuelerdaten"

# Maximum display length (characters) of a pupil delta:
_DELTA_LEN_MAX = 80

#####################################################

import os
from qtpy.QtWidgets import QStackedWidget, QLabel, QTreeWidget, \
        QTreeWidgetItem, QPushButton, QHBoxLayout, QVBoxLayout, \
        QWidget, QInputDialog, QTextEdit
from qtpy.QtCore import Qt
from ui.ui_support import TabPage, openDialog, VLine, KeySelect, \
        QuestionDialog, GuiError, saveDialog
from ui.table import TableWidget
from ui.grid import GridView
from ui.pupil_grid import PupilGrid

### +++++

class StackedWidget_info(QTextEdit):
    def __init__(self, tab_widget):
        self._tab = tab_widget
        super().__init__()
        self.setReadOnly(True)
        self.setMarkdown(_UPDATE_PUPILS_TEXT)
#
    def is_modified(self):
        return False
#
    def changes(self):
        return False
#
    def activate(self):
        for pb in ('EXPORT', 'IMPORT', 'C_CHOOSE'):
            self._tab.enable(pb, True)
#
    def deactivate(self):
        return True

###

class StackedWidget_class(QWidget):
    def __init__(self, tab_widget):
        self._tab = tab_widget
        super().__init__()
        vbox = QVBoxLayout(self)
        self.table = TableWidget(paste = True, on_changed = self.val_changed)
        vbox.addWidget(self.table)
        self._changes = None
        self._row = -1
        self.table.itemSelectionChanged.connect(self.selection_changed)
#
    def selection_changed(self):
        """Selection changes are used to enable and disable the "remove
        pupil data" button.
        """
        tsr = self.table.selectedRanges()
        if len(tsr) == 1:
            tsr1 = tsr[0]
            if tsr1.rowCount() == 1:
                self._row = tsr1.topRow()
                self._tab.enable('REMOVE', True)
                return
        self._tab.enable('REMOVE', False)
        self._row = -1
#
    def is_modified(self):
        return bool(self._changes)
#
    def activate(self, fields, pupil_list):
        for pb in ('EXPORT', 'IMPORT', 'ADD', 'C_CHOOSE', 'P_CHOOSE'):
            self._tab.enable(pb, True)
        # Translated headers:
        self.flist, tlist = [], []
        for f, t in fields:
            if f == 'PID':
                tpid = t
                continue
            self.flist.append(f)
            tlist.append(t)
        self.table.setColumnCount(len(self.flist))
        self.table.setRowCount(len(pupil_list))
        self.table.setHorizontalHeaderLabels(tlist)
        # Use the pupil-ids as row headers
        self.pidlist = [pdata['PID'] for pdata in pupil_list]
        self.table.setVerticalHeaderLabels(self.pidlist)
        self.rows = []
        for pdata in pupil_list:
            r = len(self.rows)
            cols = []
            for f in self.flist:
                val = pdata.get(f) or ''
                self.table.set_text(r, len(cols), val)
                cols.append(val)
            self.rows.append(cols)
#?
        self.table.resizeColumnsToContents()
        self._changes = set()
#
    def deactivate(self):
        self.table.clear()
        self._changes = None
        self.pidlist = None
        self.rows = None
        self.flist = None
#
    def val_changed(self, row, col, text):
        if self._changes == None:  # table not active
            return
        tag = f'{row:02}:{col:02}'
        old = self.rows[row][col]
        if text == old:
            self._changes.discard(tag)
        else:
            self._changes.add(tag)
        self._tab.enable('SAVE', self.is_modified())
#
    def remove_pupil(self):
        pid = self.pidlist[self._row]
        if QuestionDialog(_REMOVE_TITLE,
                _REMOVE_PID.format(pid = pid)):
            BACKEND('PUPILS_remove', pid = pid)
#
    def save(self):
        """Update pupils with modified fields.
        """
        data = []
        rows = {int(tag.split(':', 1)[0]) for tag in self._changes}
        for row in rows:
            pdata = {'PID': self.pidlist[row]}
            col = 0
            for f in self.flist:
                pdata[f] = self.table.get_text(row, col)
                col += 1
            data.append(pdata)
        #for pdata in data:
        #    print("§§§", pdata)
        BACKEND('PUPILS_new_table_data', data = data)

###

class StackedWidget_delta(QWidget):
    def __init__(self, tab_widget):
        self._tab = tab_widget
        super().__init__()
        vbox = QVBoxLayout(self)
        hbox = QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.addWidget(QLabel(_DELTA_TEXT))
        hbox.addWidget(VLine())
        qb = QPushButton(_DELTA_QUIT)
        hbox.addWidget(qb)
        qb.clicked.connect(self.done)
        self.tree = QTreeWidget()
        vbox.addWidget(self.tree)
        self.tree.setHeaderHidden(True)
        self.tree.setWordWrap(True)
        self.changes = None
        self.elements = None
        FUNCTIONS['pupils_DELTA'] = self.DELTA
        FUNCTIONS['pupils_DELTA_COMPLETE'] = self.DELTA_COMPLETE
#
    def is_modified(self):
        raise BUG("This method should not be called")
#
    def activate(self):
        self.tree.clear()
        self.elements = []
        self.error = False
#
    def deactivate(self):
        self.tree.clear()
        self.elements = None
#
    def DELTA(self, klass, delta):
        """Add elements (changes) for the given class.
        """
        if self.error:
            return
        items = []
        self.elements.append((klass, items))
        parent = QTreeWidgetItem(self.tree)
        parent.setText(0, "Klasse {}".format(klass))
        parent.setFlags(parent.flags() | Qt.ItemIsTristate
                | Qt.ItemIsUserCheckable)
        for d in delta:
            child = QTreeWidgetItem(parent)
            items.append((child, d))
            child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
            op, pdata = d[0], d[1]
            name = pdata['FIRSTNAME'] + ' ' + pdata['LASTNAME']
            if op == 'NEW':
                text = 'Neu: %s' % name
            elif op == 'DELTA':
                text = 'Ändern %s: %s' % (name, str(d[2]))
                if len(text) > _DELTA_LEN_MAX:
                    child.setToolTip(0, '<p>' + text + '</p>')
                    text = text[:_DELTA_LEN_MAX - 4] + ' ...'
            elif op == 'REMOVE':
                text = 'Entfernen: %s' % name
            else:
                SHOW_ERROR("Unexpected pupil-delta operator: %s" % op)
                self.error = True
                return
            child.setText(0, text)
            child.setCheckState(0, Qt.Checked)
#
    def DELTA_COMPLETE(self):
        if self.error:
            BACKEND('PUPILS_get_classes', reset = '')
        else:
            self._tab.enable('SAVE', True)
#
    def save(self):
        """Perform the selected changes.
        Transmit the change info class-for-class, so that the data chunks
        don't get too big.
        """
        changes = False
        for k, items in self.elements:
            # Filter the changes lists
            dlist = [d for child, d in items
                    if child.checkState(0) == Qt.Checked]
            if dlist:
                changes = True
                BACKEND('PUPILS_class_update', klass = k,
                        delta_list = dlist)
        if changes:
            # Now perform the actual update
            BACKEND('PUPILS_table_update')
        elif QuestionDialog(_NO_CHANGES, _WARN_NO_CHANGES):
            self.done()
#
    def done(self):
        BACKEND('PUPILS_get_classes', reset = '')

###

class StackedWidget_pupil(GridView):
    def __init__(self, tab_widget):
        self._tab = tab_widget
        super().__init__()
        self.pupil_scene = None
#
    def is_modified(self):
        return bool(self.pupil_scene.changes())
#
    def set_changed(self, show):
        self._tab.enable('SAVE', show)
#
    def activate(self, pdata, name, exists):
        self.pupil_scene = PupilGrid(self, self._tab.INFO)
        self.pupil_scene.set_pupil(pdata, name)
        self.set_scene(self.pupil_scene)
        self.pupil_scene.view()
        for pb in ('ADD', 'REMOVE', 'C_CHOOSE'):
            self._tab.enable(pb, True)
        self._tab.enable('P_CHOOSE', exists)
        self.exists = exists
#
    def deactivate(self):
        self.pupil_scene = None
        self.set_scene(None)
#
    def remove_pupil(self):
        if QuestionDialog(_REMOVE_TITLE,
                _REMOVE.format(name = self.pupil_scene.text('title'))):
            if self.exists:
                BACKEND('PUPILS_remove',
                        pid = self.pupil_scene.pupil_data['PID'])
            else:
                BACKEND('PUPILS_get_classes', reset = '')
#
    def save(self):
        BACKEND('PUPILS_new_data', data = self.pupil_scene.pupil_data)

###

class ManagePupils(TabPage):
    """Manage the pupil data on an individual basis, or else via tables
    for a class or even the whole school (e.g. when the data is to be
    synchronized with a master database).
    For class/school editing, the entries to be changed are shown and
    may be deselected.
    """
    def __init__(self):
        super().__init__(_UPDATE_PUPILS)
        self._widgets = {}
        self.INFO = None        # set on entry
        topbox = QHBoxLayout()
        self.vbox.addLayout(topbox)

        #*********** The "main" widget ***********
        self.main = QStackedWidget()
        topbox.addWidget(self.main)
        ### The stacked widgets:
        # 0) Text describing the available functions
        _w = StackedWidget_info(self)
        self.main.addWidget(_w)
        self._widgets['INFO'] = _w
        # 1) Table with data for all pupils in a class
        _w = StackedWidget_class(self)
        self.main.addWidget(_w)
        self._widgets['CLASS'] = _w
        # 2) Tree showing pending changes (update from table)
        _w = StackedWidget_delta(self)
        self.main.addWidget(_w)
        self._widgets['DELTA'] = _w
        # 3) Custom editor-table for individual pupil-data
        _w = StackedWidget_pupil(self)
        self.main.addWidget(_w)
        self._widgets['PUPIL'] = _w

        topbox.addWidget(VLine())
        cbox = QVBoxLayout()
        topbox.addLayout(cbox)

        ### Select class
        self.class_select = KeySelect(changed_callback = self.class_changed)
        self._widgets['C_CHOOSE'] = self.class_select
        cbox.addWidget(QLabel(_CLASS))
        cbox.addWidget(self.class_select)


        ### List of pupils
        self.pselect = KeySelect(changed_callback = self.pupil_changed)
        self._widgets['P_CHOOSE'] = self.pselect
        cbox.addWidget(self.pselect)

        cbox.addSpacing(30)

        ### Save (changed) data
        _w = QPushButton(_SAVE)
        self._widgets['SAVE'] = _w
        cbox.addWidget(_w)
        _w.clicked.connect(self.save)

        cbox.addSpacing(30)

        ### Add a new pupil, or delete the entry for an existing pupil
        _w = QPushButton(_NEW_PUPIL)
        self._widgets['ADD'] = _w
        cbox.addWidget(_w)
        _w.clicked.connect(self.new_pupil)
        cbox.addSpacing(10)
        _w = QPushButton(_REMOVE_PUPIL)
        self._widgets['REMOVE'] = _w
        cbox.addWidget(_w)
        _w.clicked.connect(self.remove_pupil)

        cbox.addStretch(1)

        ### Export the current class table (or complete table)
        _w = QPushButton(_EXPORT)
        self._widgets['EXPORT'] = _w
        cbox.addWidget(_w)
        _w.clicked.connect(self.export)

        cbox.addSpacing(30)

        ### Import table (class or whole school)
        _w = QPushButton(_IMPORT)
        self._widgets['IMPORT'] = _w
        cbox.addWidget(_w)
        _w.clicked.connect(self.update)
#
    def set_widget(self, tag, **params):
        """Select the widget to be displayed in the "main" stack.
        """
        current = self.main.currentWidget()
        if current:
            current.deactivate()
        new = self._widgets[tag]
        self.main.setCurrentWidget(new)
        # Allow each function group to decide which buttons are enabled
        for pb in ('SAVE', 'ADD', 'REMOVE', 'EXPORT', 'IMPORT',
                'P_CHOOSE', 'C_CHOOSE'):
            self.enable(pb, False)
        new.activate(**params)
#
    def is_modified(self):
        return self.main.currentWidget().is_modified()
#
    def enable(self, tag, on):
        """Enable or disable the widget with given tag.
        """
        self._widgets[tag].setEnabled(on)
#
    def enter(self):
        """Called when the tab is selected.
        """
        self.set_widget('INFO')
        BACKEND('PUPILS_get_info')   # -> SET_INFO(...)
#
    def SET_INFO(self, **params):
        """CALLBACK: set up basic info for pupils.
        Expected parameters:
            <fields> is a list of field names:
                [[field1_internal_name, field1_local_name], ... ]
            <sex> and <streams> are lists of possible values.
        """
        self.INFO = params
        #print("INFO: ", self.INFO)
        BACKEND('PUPILS_get_classes')   # -> SET_CLASSES(..., '')
        #
#
    def year_change_ok(self):
        return self.leave_ok()
#
    def leave(self):
        """Called when the tab is deselected.
        """
        self.main.currentWidget().deactivate()
        return True
#
    def SET_CLASSES(self, classes, klass):
        """CALLBACK: Supplies the classes as a list: [class10, class9, ...]
        and the selected class. Set the class selection widget
        and trigger a "change of class" signal.
        """
        self.set_widget('INFO')
        try:
            ix = classes.index(klass) + 1
        except ValueError:
            ix = 0
        self.class_select.set_items([('', _ALL_CLASSES)] +
                [(c, c) for c in classes], index = ix)
        self.class_select.trigger()
#
    def class_changed(self, klass):
        """Manual selection of a class (including the 'empty' class,
        meaning "no class" or "all classes", according to usage ...).
        """
        if self.leave_ok():
            self.leave()
            BACKEND('PUPILS_set_class', klass = klass)  # -> SET_PUPILS(...)
            return True
        return False
#
    def SET_PUPILS(self, pupils, pid):
        """CALLBACK: Supplies the pupils as a list of (pid, name) pairs.
        <pid> is the id of the selected pupil (it may be invalid).
        Set the pupil selection widget and trigger a "change of pupil"
        signal.
        """
        self.pselect.set_items([('', _ALL_PUPILS)] + pupils)
        try:
            self.pselect.reset(pid)
        except GuiError:
            pass
        BACKEND('PUPILS_set_pupil', pid = pid)
#
    def pupil_changed(self, pid):
        """A new pupil has been selected: reset the grid accordingly.
        """
        if not self.leave_ok():
            return False
        BACKEND('PUPILS_set_pupil', pid = pid)
        return True
#
    def SET_INFO_VIEW(self):
        """Show info page.
        """
        self.set_widget('INFO')
#
    def SET_CLASS_VIEW(self, pdata_list):
        """Show class editor.
        """
        self.set_widget('CLASS', fields = self.INFO['fields'],
                pupil_list = pdata_list)
#
    def SET_PUPIL_VIEW(self, pdata, name, exists = True):
        self.set_widget('PUPIL', pdata = pdata, name = name, exists = exists)
#
    def new_pupil(self):
        if not self.leave_ok():
            return
        # First enter pid (which is not editable).
        # The back-end call is necessary to get a pid suggestion (as
        # well as the rest of the "dummy" data).
        BACKEND('PUPILS_new_pupil')
#
    def NEW_PUPIL(self, data, ask_pid = None):
        if ask_pid:
            etext = data.get('__ERROR__')
            mtext = _ENTER_PID
            if etext:
                mtext = etext + '\n\n' + mtext
            pid, ok = QInputDialog.getText(self, _ENTER_PID_TITLE,
                    mtext, text = ask_pid)
            if ok:
                if pid != ask_pid:
                    # Need to check validity of the pid
                    BACKEND('PUPILS_new_pupil', pid = pid)
                    return
            else:
                return
        self.SET_PUPIL_VIEW(data, _NEW_PUPIL, exists = False)
#
    def save(self):
        self.main.currentWidget().save()
#
    def remove_pupil(self):
        self.main.currentWidget().remove_pupil()
#
    def export(self):
        if not self.leave_ok():
            return
        klass = self.class_select.selected()
        fpath = saveDialog(_SAVE_TABLE_FILE,
                _TABLE_FILE_NAME.format(klass = klass) if klass
                else _FULL_TABLE_FILE_NAME)
        if fpath:
            BACKEND('PUPILS_export_data', filepath = fpath, klass = klass)
#
    def update(self):
        if self.leave_ok():
            fpath = openDialog(_TABLE_FILE)
            if fpath:
                # Ask for the changes
                BACKEND('PUPILS_table_delta', filepath = fpath)
#
    def DELTA_START(self):
        self.set_widget('DELTA')


tab_pupils = ManagePupils()
TABS.append(tab_pupils)
FUNCTIONS['pupils_SET_INFO'] = tab_pupils.SET_INFO
FUNCTIONS['pupils_SET_CLASSES'] = tab_pupils.SET_CLASSES
FUNCTIONS['pupils_SET_PUPILS'] = tab_pupils.SET_PUPILS
FUNCTIONS['pupils_SET_CLASS_VIEW'] = tab_pupils.SET_CLASS_VIEW
FUNCTIONS['pupils_SET_PUPIL_VIEW'] = tab_pupils.SET_PUPIL_VIEW
FUNCTIONS['pupils_SET_INFO_VIEW'] = tab_pupils.SET_INFO_VIEW
FUNCTIONS['pupils_NEW_PUPIL'] = tab_pupils.NEW_PUPIL
FUNCTIONS['pupils_DELTA_START'] = tab_pupils.DELTA_START
