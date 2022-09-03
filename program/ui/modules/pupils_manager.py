"""
ui/modules/pupils_manager.py

Last updated:  2022-09-02

Front-end for managing pupil data.


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

#TODO ...
_NAME = "Schüler"
_TITLE ="Schülerdaten verwalten"


### Messages

#####################################################

if __name__ == "__main__":
    import sys, os, builtins

    this = sys.path[0]
    appdir = os.path.dirname(os.path.dirname(this))
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start
    from ui.ui_base import StandalonePage as Page
    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    #    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))
else:
    from ui.ui_base import StackPage as Page


from ui.ui_base import QHBoxLayout, QVBoxLayout, QLabel, QPushButton, run
from ui.editable import EdiTableWidget


#from ui.ui_extra import QWidget, QLabel, QVBoxLayout, \
#        QTreeWidget, QTreeWidgetItem, Qt

### -----

def init():
    MAIN_WIDGET.add_tab(ManagePupils())


class ManagePupils(Page):
    name = _NAME
    title = _TITLE

    def __init__(self):
        super().__init__()
        hbox = QHBoxLayout(self)
        vboxl = QVBoxLayout()
        hbox.addLayout(vboxl)
        vboxr = QVBoxLayout()
        hbox.addLayout(vboxr)

        # Class info
        self.class_label = QLabel()
        vboxl.addWidget(self.class_label)
#TODO: Do I want this?
        self.modified_label = QLabel()
        vboxl.addWidget(self.modified_label)

        # The class data table
        self.pupil_data_table = EdiTableWidget()
        vboxl.addWidget(self.pupil_data_table)

        # Various "controls" in the panel on the right
        pb1 = QPushButton("Just testing")
        vboxr.addWidget(pb1)
        pb2 = QPushButton("Another button")
        vboxr.addWidget(pb2)
        vboxr.addStretch(1)
        for i in range(15):
            vboxr.addWidget(QPushButton(f"Button {i}"))

        def is_modified(self):
            """Return <True> if there are unsaved changes.
            """
#TODO: test whether there really are any changes?
            return True


if __name__ == "__main__":
    from ui.ui_base import run

    widget = ManagePupils()
    widget.class_label.setText("<b>Klasse 02G</b>")
    widget.modified_label.setText("zuletzt geändert: 2021-10-05_20:14")
# Actually this can be in the main code, using the fixed (translated)
# column headers ... need to set up the data area.
    widget.pupil_data_table.setup(colheaders = ["PID", "Name"],
            undo_redo = True, paste = True,
            on_changed = None)
    widget.resize(600, 400)
    run(widget)


#new?
#    widget = ManagePupils()
#    widget.enter()
#    widget.resize(1000, 550)
#    run(widget)
