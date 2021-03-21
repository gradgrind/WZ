# -*- coding: utf-8 -*-
"""
ui/tab_pupils_update.py

Last updated:  2021-03-21

Pupil table management: update from master table.


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
_WARN_NO_CHANGES = "Keine Änderungen sind vorgemerkt"

### Labels, etc.
_UPDATE_PUPILS = "Schülerdaten aktualisieren"
_UPDATE_PUPILS_TEXT = "Die Schülerdaten können von einer Tabelle" \
        " aktualisiert werden." \
        "\nEs gibt zuerst die Möglichkeit, die Daten einer Klasse in" \
        " Tabellenform direkt hier zu bearbeiten." \
        "\nEine Tabelle kann aber auch exportiert werden (als xlsx-Datei)." \
        " Diese Tabelle kann dann extern bearbeitet und wieder" \
        " importiert werden (als xlsx-, ods- oder tsv-Datei)." \
        "\nEs ist auch möglich eine Tabelle für die ganze Schule zu" \
        " exportieren und importieren. Die importierte Tabelle kann" \
        " auch von einer externen Schuldatenbank stammen und muss nicht" \
        " alle Felder haben – fehlende Felder werden unverändert bleiben."
_UPDATE_PUPILS_TABLE = "Tabellendatei wählen"
_DO_UPDATE = "Änderungen umsetzen"
_CLASS = "Klasse:"
_SAVE = "Änderungen Speichern"
_EXPORT = "Tabelle exportieren"
_IMPORT = "Tabelle importieren"
_ALL_CLASSES = "* Alle Klassen *"
_TITLE_LOSE_CHANGES = "Ungespeicherte Änderungen"
_LOSE_CHANGES = "Sind Sie damit einverstanden, dass die Änderungen verloren gehen?"

_FILEOPEN = "Datei öffnen"
_TABLE_FILE = "Tabellendatei (*.xlsx *.ods *.tsv)"

# Maximum display length (characters) of a pupil delta:
_DELTA_LEN_MAX = 80

#####################################################

import os
from qtpy.QtWidgets import QStackedWidget, QLabel, QTreeWidget, \
        QTreeWidgetItem, QPushButton, QHBoxLayout, QVBoxLayout
from qtpy.QtCore import Qt
from ui.ui_support import TabPage, openDialog, VLine, KeySelect, \
        QuestionDialog
from ui.table import TableWidget

##

class UpdatePupils(TabPage):
    """Handle updating of the class lists from the main school database.
    The entries to be changed are shown and may be deselected.
    """
    def __init__(self):
        super().__init__(_UPDATE_PUPILS)
        topbox = QHBoxLayout()
        self.vbox.addLayout(topbox)

        #*********** The "main" widget ***********
        self.main = QStackedWidget()
        # Description of the functions available:
        l = QLabel(_UPDATE_PUPILS_TEXT)
        l.setWordWrap(True)
        self.main.addWidget(l)
        self.table = TableWidget(paste = True,
                on_changed = self.cell_changed) # for class table
        self.main.addWidget(self.table)
        self.tree = QTreeWidget()               # for "complete update"
        self.main.addWidget(self.tree)

        topbox.addWidget(self.main)
        topbox.addWidget(VLine())
        cbox = QVBoxLayout()
        topbox.addLayout(cbox)

        ### Select class
        self.class_select = KeySelect(changed_callback = self.class_changed)
        cbox.addWidget(QLabel(_CLASS))
        cbox.addWidget(self.class_select)

        ### Save (changed) table
        cbox.addSpacing(30)
        self.pbSave = QPushButton(_SAVE)
        cbox.addWidget(self.pbSave)
        self.pbSave.clicked.connect(self.save)

        ### Export the current class table (or complete table)
        cbox.addSpacing(30)
        self.pbExport = QPushButton(_EXPORT)
        cbox.addWidget(self.pbExport)
        self.pbExport.clicked.connect(self.export)

        ### Import table (class or whole school)
        cbox.addStretch(1)
        cbox.addWidget(QLabel(_IMPORT))
        p = QPushButton(_UPDATE_PUPILS_TABLE)
        cbox.addWidget(p)
        p.clicked.connect(self.update)
        self.tree.setHeaderHidden(True)
        self.tree.setWordWrap(True)
        self.pbdoit = QPushButton(_DO_UPDATE)
        self.pbdoit.clicked.connect(self.doit)
        cbox.addWidget(self.pbdoit)

        self.table_changes = None
#
    def enter(self):
        """Called when the tab is selected.
        """
        self.main.setCurrentIndex(0)    # select description page
        self.pbSave.setEnabled(False)
        self.pbdoit.setEnabled(False)
        BACKEND('PUPILS_get_classes')
#
    def year_change_ok(self):
        return self.check_switch()
#
    def SET_CLASSES(self, classes):
        """CALLBACK: Supplies the classes as a list: [class10, class9, ...].
        Set the class selection widget.
        """
        self.class_select.set_items([('', _ALL_CLASSES)] +
                [(c, c) for c in classes])
#
    def leave(self):
        """Called when the tab is deselected.
        """
        return self.check_switch()
#
    def check_switch(self):
        """If there are unsaved changes, ask whether it is ok to lose them.
        If there are no changes, or "ok to lose changes" was selected,
        clear the data structures and return <True>.
        If "don't lose changes" was selected, don't touch anything and
        return <False>.
        """
        if self.table_changes and not QuestionDialog(
                _TITLE_LOSE_CHANGES, _LOSE_CHANGES):
            return False
        self._cleartree()
        self.table.clear()
        self.table_changes = None
        return True
#
    def class_changed(self, klass):
        if not self.check_switch():
            return False
        if klass:
            self.klass = klass
            # Show table editor page
            self.main.setCurrentIndex(1)
            # Enter pupil data in table
            BACKEND('PUPILS_get_data', klass = klass)
        else:
            self.klass = None
            # Show description page
            self.main.setCurrentIndex(0)
        return True
#
    def SET_CLASS(self, fields, pupil_list):
        # Translated headers:
        tpid = fields.pop('PID')
        self.flist, tlist = [], []
        for f, t in fields.items():
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
        self.table_changes = set()
#
    def cell_changed(self, row, col, text):
        if self.table_changes == None:
            return
        tag = f'{row:02}:{col:02}'
        old = self.rows[row][col]
        if text == old:
            self.table_changes.discard(tag)
        else:
            self.table_changes.add(tag)
        self.pbSave.setEnabled(bool(self.table_changes))
#
    def save(self):
#TODO
        print("§§§ SAVE")
#
    def export(self):
#TODO
        print("§§§ EXPORT")
#
    def _cleartree(self):
        self.elements = None
        self.tree.clear()
#
    def update(self, review = False):
        self.enter()
        self._cleartree()
        self.changes = False
        self.elements = []
        if review:
            BACKEND('PUPIL_table_delta2')
        else:
            fpath = openDialog(_TABLE_FILE)
            if not fpath:
                return
            # Ask for the changes
            BACKEND('PUPIL_table_delta', filepath = fpath)
#
    def DELTA(self, klass, delta):
        items = []
        self.elements.append((klass, items))
        if not delta:
            return
        self.changes = True
        self.error = False
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
                INFO('TRAP', "Unexpected pupil-delta operator: %s" % op)
                self.error = True
                return
            child.setText(0, text)
            child.setCheckState(0, Qt.Checked)
#
    def DELTA_COMPLETE(self):
        if self.error:
            self._cleartree()
        elif self.changes:
            self.pbdoit.setEnabled(True)
#
    def doit(self):
# Transmit the change info class-for-class, so that the data chunks
# don't get too big.
        changes = False
        for k, items in self.elements:
            # Filter the changes lists
            dlist = [d for child, d in items
                    if child.checkState(0) == Qt.Checked]
            if dlist:
                changes = True
                BACKEND('PUPIL_class_update', klass = k,
                        delta_list = dlist)
        if changes:
            # Now perform the actual update
            BACKEND('PUPIL_table_update')
            self.update(True)
        else:
            SHOW_WARNING(_WARN_NO_CHANGES)


tab_pupils_update = UpdatePupils()
TABS.append(tab_pupils_update)
FUNCTIONS['pupil_DELTA'] = tab_pupils_update.DELTA
FUNCTIONS['pupil_DELTA_COMPLETE'] = tab_pupils_update.DELTA_COMPLETE
FUNCTIONS['pupils_SET_CLASSES'] = tab_pupils_update.SET_CLASSES
FUNCTIONS['pupils_SET_CLASS'] = tab_pupils_update.SET_CLASS
