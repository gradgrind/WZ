"""
ui/modules/year_manager.py

Last updated:  2023-03-17

Front-end for managing year data, migrations, etc.


=+LICENCE=============================
Copyright 2023 Michael Towers

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

if __name__ == "__main__":
    import sys, os

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

T = TRANSLATIONS("ui.modules.year_manager")

### +++++

from core.base import Dates, start
from core.db_access import (
    open_database,
    db_update_field,
    db_new_row,
    db_check_unique_entry,
    db_delete_rows,
    sql_insert_from_dict,
    migrate_db,
)
from core.basic_data import get_classes
from core.classes import build_group_data, atomic_maps
from core.pupils import (
    get_pupil_fields,
    get_pupils,
    pupil_data,
    pupil_name,
    migrate_pupils,
)
from local.local_pupils import get_sortname
from ui.ui_base import (
    # QtWidgets
    QWidget,
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFormLayout,
    QTableWidgetItem,
    QLineEdit,
    QDialogButtonBox,

    QTreeWidget,
    QTreeWidgetItem,
    # QtCore
    Qt,
    # Others
    KeySelector,
)

### -----


def init():
    MAIN_WIDGET.add_tab(ManageYears())


class ManageYears(Page):
    name = T["MODULE_NAME"]
    title = T["MODULE_TITLE"]

    def __init__(self):
        super().__init__()
        self.manager = YearManager()
        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.manager)

    def enter(self):
        open_database()
        self.manager.init_data()

    def is_modified(self):
        return self.manager.modified()


# ++++++++++++++ The widget implementation ++++++++++++++


class YearManager(QWidget):
    def __init__(self):
        super().__init__()
        vbox = QVBoxLayout(self)
        migrate = QPushButton(T["MIGRATE_DATA"])
        migrate.setToolTip(T["MIGRATE_TO_NEXT_YEAR"])
        migrate.clicked.connect(do_migration)
        vbox.addWidget(migrate)

    def modified(self):
        """Return <True> if there are unsaved changes."""
        return False  # All changes are done immediately

    def init_data(self):
        pass

def do_migration():
    migrated, leavers = migrate_pupils()
    keepers = migrate_leavers_dialog(leavers)
    for pid in keepers:
        pdata = leavers[pid]
        migrated[pdata["CLASS"]].append(pdata)
    sql_list = []
    for klass in sorted(migrated):
        pdlist = migrated[klass]
        # Get sql commands to insert pupil data
        for pdata in sorted(pdlist, key=lambda pd: pd["SORT_NAME"]):
            print("   ...", klass, pupil_name(pdata))
            sql_list.append(sql_insert_from_dict("PUPILS", pdata))
    # Folder for next year's data:
    new_folder = start.year_data_path(Dates.next_year())
    # Use a PROCESS pop-up to encapsulate the database migration
    PROCESS(
#TODO: Maybe include other migrations in the window?
        migrate_db,
        title=T["PROCESS_MIGRATE"].format(year=Dates.next_year()),
        path=new_folder,
        sql_extra=sql_list
    )
    # Perform basic conversion of calendar – it will still need manual
    # editing, but should at least enable "entry" into the new year.
    Dates.migrate_calendar()


def migrate_leavers_dialog(leavers):
    """Handle migration of pupils who would normally leave to the next
    school year.
    """
    dialog = QDialog()
    vbox = QVBoxLayout(dialog)
    vbox.addWidget(QLabel(T["SELECT_REPEATERS"]))
    tree = QTreeWidget()
    vbox.addWidget(tree)
    tree.setHeaderHidden(True)
    tree.setWordWrap(True)
    buttonBox = QDialogButtonBox(
        QDialogButtonBox.Ok | QDialogButtonBox.Cancel
    )
    buttonBox.accepted.connect(dialog.accept)
    buttonBox.rejected.connect(dialog.reject)
    vbox.addWidget(buttonBox)
    # Sort the leavers into classes
    classes = {}
    for pdata in leavers.values():
        klass = pdata["CLASS"]
        pid = pdata["PID"]
        name = pupil_name(pdata)
        val = (pid, name)
        try:
            classes[klass].append(val)
        except KeyError:
            classes[klass] = [val]
    # Populate the tree
    elements = []
    for klass, pid_name in classes.items():
        parent = QTreeWidgetItem(tree)
        parent.setText(0, T["CLASS_K"].format(klass=klass))
        parent.setFlags(parent.flags() | Qt.ItemFlag.ItemIsAutoTristate
                | Qt.ItemFlag.ItemIsUserCheckable)
        for pid, name in pid_name:
            child = QTreeWidgetItem(parent)
            elements.append((pid, child))
            child.setFlags(child.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            child.setText(0, name)
            child.setCheckState(0, Qt.CheckState.Unchecked)
    keeplist = []
    if dialog.exec():
        for pid, child in elements:
            # Filter the changes lists
            if child.checkState(0) == Qt.CheckState.Checked:
                keeplist.append(pid)
    return keeplist


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from ui.ui_base import run

    widget = ManageYears()
    widget.enter()
    widget.resize(1000, 550)
    run(widget)
