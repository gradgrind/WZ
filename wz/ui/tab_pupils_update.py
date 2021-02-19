# -*- coding: utf-8 -*-
"""
ui/tab_pupils_update.py

Last updated:  2021-02-19

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
        " aktualisiert werden.\nDiese Tabelle (xlsx oder ods) sollte" \
        " von der Schuldatenbank stammen."
_UPDATE_PUPILS_TABLE = "Tabellendatei wählen"
_DO_UPDATE = "Änderungen umsetzen"

_FILEOPEN = "Datei öffnen"
_TABLE_FILE = "Tabellendatei (*.xlsx *.ods *.tsv)"

# Maximum display length (characters) of a pupil delta:
_DELTA_LEN_MAX = 80

#####################################################

import os
from qtpy.QtWidgets import QLabel, QTreeWidget, QTreeWidgetItem, \
        QPushButton
from qtpy.QtCore import Qt
from ui.ui_support import TabPage, openDialog

##

class UpdatePupils(TabPage):
    """Handle updating of the class lists from the main school database.
    The entries to be changed are shown and may be deselected.
    """
    def __init__(self):
        super().__init__(_UPDATE_PUPILS)
        l = QLabel(_UPDATE_PUPILS_TEXT)
        l.setWordWrap(True)
        self.vbox.addWidget(l)
        p = QPushButton(_UPDATE_PUPILS_TABLE)
        self.vbox.addWidget(p)
        p.clicked.connect(self.update)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setWordWrap(True)
        self.vbox.addWidget(self.tree)
        self.pbdoit = QPushButton(_DO_UPDATE)
        self.pbdoit.clicked.connect(self.doit)
        self.vbox.addWidget(self.pbdoit)
        self.ptables = None
#
    def enter(self):
        """Called when the tab is selected.
        """
        self.pbdoit.setEnabled(False)
#
    def leave(self):
        """Called when the tab is deselected.
        """
        self.pupils = None
        self.ptables = None
        self._cleartree()
        return True
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
