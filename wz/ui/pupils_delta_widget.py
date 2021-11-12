# -*- coding: utf-8 -*-
"""
ui/pupils_delta_widget.py

Last updated:  2021-10-30

Gui widget for comparing class data with a newer version from an
external source.


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

_DELTA_TEXT = """Die möglichen Änderungen werden als Baum dargestellt.
Indem Sie auf die entsprechenden Kontrollfelder klicken, können Sie
einzelne Änderungen (ab)wählen. Durch das Kontrollfeld einer Klasse
können alle Änderungen einer Klasse (ab)gewählt werden.
"""
_CLASS_K = "Klasse {klass}"
_NEW_NAME = "Neu: {name}"
_CHANGE = "Ändern {name}: {fields}"
_REMOVE_NAME = "Entfernen: {name}"

# Maximum display length (characters) of a pupil delta:
_DELTA_LEN_MAX = 80

#####################################################

if __name__ == '__main__':
    # Enable package import if running as module
    import sys, os
    #print(sys.path)
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)
    from ui.ui_extra import StandalonePage as Page
else:
    from ui.ui_extra import StackPage as Page

from ui.ui_extra import QWidget, QLabel, QVBoxLayout, \
        QTreeWidget, QTreeWidgetItem, Qt

# Types of change which can be recorded
NEW = 1     # data: the pupil-data mapping
REMOVE = 2  # data: the pupil-data mapping to be removed
DELTA = 3   # data: the (original) pupil-data maping, a list of changes:
            #           [(field name, new value), ... ]

### -----

class PupilsDeltaWidget(QWidget):
    def __init__(self):
        super().__init__()
        vbox = QVBoxLayout(self)
        vbox.addWidget(QLabel(_DELTA_TEXT))
        self.tree = QTreeWidget()
        vbox.addWidget(self.tree)
        self.tree.setHeaderHidden(True)
        self.tree.setWordWrap(True)
        self.changes = None
        self.elements = None

    def activate(self):
        self.tree.clear()
        self.elements = []
        self.error = False

    def deactivate(self):
        self.tree.clear()
        self.elements = None

    def add_changes(self, klass, delta):
        """Add elements (changes) for the given class.
        <delta> is a list of differences as generated by the method
        <compare_update> of a <Pupils> instance.
        """
        items = []
        self.elements.append((klass, items))
        parent = QTreeWidgetItem(self.tree)
        parent.setText(0, _CLASS_K.format(klass = klass))
        parent.setFlags(parent.flags() | Qt.ItemIsAutoTristate
                | Qt.ItemIsUserCheckable)
        for d in delta:
            child = QTreeWidgetItem(parent)
            items.append((child, d))
            child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
            op, pdata = d[0], d[1]
            name = f"{pdata['FIRSTNAME']} {pdata['LASTNAME']}"
            if op == NEW:
                text = _NEW_NAME.format(name = name)
            elif op == DELTA:
                text = _CHANGE.format(name = name,
                        fields = "; ".join([f"{k} → {v}" for k, v in d[2]]))
                if len(text) > _DELTA_LEN_MAX:
                    child.setToolTip(0, f"<p>{text}</p>")
                    text = f"{text[:_DELTA_LEN_MAX - 4]} ..."
            elif op == REMOVE:
                text = _REMOVE_NAME.format(name = name)
            else:
                raise Bug("Unexpected pupil-delta operator: %s" % op)
            child.setText(0, text)
            child.setCheckState(0, Qt.Checked)

    def get_data(self):
        """Return the filtered data, as a mapping {class: delta},
        delta having the same format as supplied to <add_changes>.
        """
        data = {}
        for k, items in self.elements:
            # Filter the changes lists
            dlist = [d for child, d in items
                    if child.checkState(0) == Qt.Checked]
            if dlist:
                data[k] = dlist
        return data


if __name__ == "__main__":
    from ui.ui_extra import run, QHBoxLayout, QTextEdit, QPushButton, \
            QTextOption

    class MyPage(Page):
        def is_modified(self):
            """Return <True> if there are unsaved changes.
            """
#TODO: test whether there really are any changes?
            return True


    test_data = {
        '01G': [
            (NEW, {'FIRSTNAME': 'Fritz', 'LASTNAME': 'Müller'}),
            (DELTA, {'FIRSTNAME': 'Lisa', 'LASTNAME': 'Schmidt'},
                    (('FIELD1', 'New data'), ('FIELD2', 'Changed'))),
        ],
        '02G': [
            (REMOVE, {'FIRSTNAME': 'Melanie', 'LASTNAME': 'Weiß'}),
        ],
    }

    def show_data():
        data = deltawidget.get_data()
        text.clear()
        for klass, items in data.items():
            text.append(f"{klass}:")
            for item in items:
                text.append(f"    {repr(item)}")

    widget = MyPage()
    layout = QVBoxLayout(widget)
    deltawidget = PupilsDeltaWidget()
    layout.addWidget(deltawidget)
    box = QHBoxLayout()
    layout.addLayout(box)
    pb = QPushButton("Get Data")
    box.addWidget(pb)
    text = QTextEdit()
    text.setReadOnly(True)
    text.setWordWrapMode(QTextOption.NoWrap)
    box.addWidget(text)
    pb.clicked.connect(show_data)

    deltawidget.activate()
    for klass, kdata in test_data.items():
        deltawidget.add_changes(klass, kdata)

#TODO: Add a button to print the data ...

    widget.resize(600, 400)
    run(widget)