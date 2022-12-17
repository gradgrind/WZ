"""
ui/modules/pupils_manager.py

Last updated:  2022-12-17

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

T = TRANSLATIONS("ui.modules.pupils_manager")

### +++++

from core.db_access import (
    open_database,
    db_update_field,
    db_new_row,
    db_check_unique_entry,
    db_delete_rows,
)
from core.basic_data import get_classes
from core.classes import build_group_data, atomic_maps
from core.pupils import get_pupil_fields, get_pupils, pupil_data, pupil_name
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
    # QtCore
    Qt,
    # Others
    KeySelector,
)
from ui.simple_table import TableWidget
from ui.cell_editors import (
    CellEditorLine,
    CellEditorDate,
    CellEditorTable,
    CellEditorCheckList,
    CellEditorList,
)

### -----


def init():
    MAIN_WIDGET.add_tab(ManagePupils())


class ManagePupils(Page):
    name = T["MODULE_NAME"]
    title = T["MODULE_TITLE"]

    def __init__(self):
        super().__init__()
        self.pupil_manager = PupilManager()
        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.pupil_manager)

    def enter(self):
        open_database()
        self.pupil_manager.init_data()

    def is_modified(self):
        return self.pupil_manager.modified()


# ++++++++++++++ The widget implementation ++++++++++++++


class PupilManager(QWidget):
    def __init__(self):
        super().__init__()
        hbox = QHBoxLayout(self)
        vboxl = QVBoxLayout()
        hbox.addLayout(vboxl)
        vboxr = QVBoxLayout()
        hbox.addLayout(vboxr)
        hbox.setStretchFactor(vboxl, 1)

        # The class data table, etc.
        self.pupil_table = TableWidget(edit_handler=self.edit_cell)
        vboxl.addWidget(self.pupil_table)

        # Various "controls" in the panel on the right
        formbox = QFormLayout()
        vboxr.addLayout(formbox)
        self.class_selector = KeySelector(changed_callback=self.changed_class)
        formbox.addRow(T["CLASS"], self.class_selector)
        del_pupil = QPushButton(T["REMOVE_PUPIL"])
        del_pupil.clicked.connect(self.remove_pupil)
        vboxr.addWidget(del_pupil)
        change_class = QPushButton(T["CHANGE_CLASS"])
        change_class.clicked.connect(self.do_class_change)
        vboxr.addWidget(change_class)
        add_pupil = QPushButton(T["NEW_PUPIL"])
        add_pupil.clicked.connect(self.new_pupil)
        vboxr.addWidget(add_pupil)

    def modified(self):
        """Return <True> if there are unsaved changes."""
        return False  # All changes are done immediately

    def init_data(self):
        self.pupil_fields_map = get_pupil_fields()
        self.pupil_table.setColumnCount(len(self.pupil_fields_map))
        classes = get_classes()
        class_list = classes.get_class_list()
        self.field_editors = []
        headers = []
        self.field_list = []
        for f, vec in self.pupil_fields_map.items():
            self.field_list.append(f)
            headers.append(vec[0])
            e = vec[1]
            if e == "CLASS_CHOICE":
                editor = None
            elif e == "PID":
                editor = CellEditorPid().activate
            elif e == "SORT_NAME":
                editor = CellEditorSortName().activate
            elif e == "GROUPS":
                self.group_editor = CellEditorGroups(classes)
                editor = self.group_editor.activate
            elif e == "LINE":
                editor = CellEditorLine().activate
            elif e == "DATE_OR_EMPTY":
                editor = CellEditorDate(empty_ok=True).activate
            elif e == "DATE":
                editor = CellEditorDate(empty_ok=False).activate
            elif e == "CHOICE":
                vlist = [[[v], ""] for v in vec[2]]
                editor = CellEditorTable(vlist).activate
            elif e == "CHOICE_MAP":
                vlist = [[[v], text] for v, text in vec[2]]
                editor = CellEditorTable(vlist).activate
            else:
                # TODO?
                editor = None
            self.field_editors.append(editor)
        self.pupil_table.setHorizontalHeaderLabels(headers)
        self.class_selector.set_items(class_list)
        self.choose_class = CellEditorList(
            *map(list, zip(*class_list)),
            label=f'<p style="color:#a00000;">{T["CLASS_WARNING"]}</p>',
        ).activate
        self.class_selector.trigger()

    def changed_class(self, klass):
        self.pupil_list = get_pupils(klass, use_cache=False)
        self.pupil_table.setRowCount(len(self.pupil_list))
        row = 0
        for pdata in self.pupil_list:
            col = 0
            for f in self.pupil_fields_map:
                self.pupil_table.setItem(row, col, QTableWidgetItem(pdata[f]))
                col += 1
            row += 1
        # hHd = self.pupil_table.horizontalHeader()
        self.pupil_table.resizeColumnsToContents()
        # hHd.setStretchLastSection(True)
        self.group_editor.set_class(klass)
        self.klass = klass
        return True  # confirm acceptance to the <KeySelector>.

    def edit_cell(self, r, c, pos):
        pdata = self.pupil_list[r]
        field = self.field_list[c]
        properties = {
            "ROW_DATA": pdata,
            "VALUE": pdata[field],
        }
        editor = self.field_editors[c]
        if editor and editor(pos, properties):
            print("====>", properties)
            # Update db and display
            val = properties["VALUE"]
            pid = pdata["PID"]
            if not db_update_field("PUPILS", field, val, PID=pid):
                raise Bug(
                    f"PUPILS: update of {field} to {val} for {pid} failed"
                )
            pdata[field] = val
            # TODO: What about a "delegate", to show a display version of the value?
            return val
        return None

    # The CLASS field is not editable. To move a pupil to a different
    # class there is a special button. After such a change there needs
    # to be a redisplay, because the pupil will disappear from its old class.

    # Some field handlers are specific to certain schools/situations, so
    # the handler should be specified in a config file.
    # Some special handlers are required for certain fields – these are
    # defined separately from the more general handlers.

    def new_pupil(self):
        """Add a dummy pupil to the class and redisplay the pupils."""
        field_data = CONFIG["DUMMY_PUPIL"]
        db_new_row("PUPILS", CLASS=self.klass, **dict(field_data))
        # Redisplay pupil list
        self.changed_class(self.klass)

    def do_class_change(self):
        # Get table selection
        try:
            sel_range = self.pupil_table.selectedRanges()[0]
        except IndexError:
            # print("§§§§§ NO SELECETED PUPIL")
            return
        val = {"VALUE": self.klass}
        if self.choose_class(None, val):
            pid_list = [
                self.pupil_list[row]["PID"]
                for row in range(sel_range.topRow(), sel_range.bottomRow() + 1)
            ]
            k = val["VALUE"]
            for pid in pid_list:
                if not db_update_field("PUPILS", "CLASS", k, PID=pid):
                    raise Bug(
                        f"PUPILS: update of CLASS to {k} for {pid} failed"
                    )
            # Redisplay pupil list
            self.changed_class(self.klass)

    def remove_pupil(self):
        # Get table selection
        try:
            sel_range = self.pupil_table.selectedRanges()[0]
        except IndexError:
            # print("§§§§§ NO SELECETED PUPIL")
            return
        pdata_list = [
            self.pupil_list[row]
            for row in range(sel_range.topRow(), sel_range.bottomRow() + 1)
        ]

        if SHOW_CONFIRM(
            T["CONFIRM_DELETE_PUPILS"].format(
                pnames="\n  ".join(
                    [""] + [pupil_name(pdata) for pdata in pdata_list]
                )
            )
        ):
            db_delete_rows("PUPILS", PID=[pdata["PID"] for pdata in pdata_list])
            # Redisplay pupil list
            self.changed_class(self.klass)


####################################################
### Specialized cell editors for the pupil table ###
####################################################


class CellEditorPid(QDialog):
    """For correcting a pupil-id or creating a new one. This should
    normally be handled automatically, a manual change being generally
    undesirable.
    """

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        vbox = QVBoxLayout(self)
        label = QLabel(f'<p style="color:#a00000;">{T["PID_WARNING"]}</p>')
        label.setWordWrap(True)
        vbox.addWidget(label)
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
            # A new pupil-id may not be null ...
            if text:
                if text != text0:
                    # ... and may not be in use
                    if pupil_data(text, allow_none=True):
                        SHOW_ERROR(T["PID_EXISTS"].format(pid=text))
                    else:
                        properties["VALUE"] = text
                        return True
            else:
                SHOW_ERROR(T["NULL_PID"])
        return False


class CellEditorSortName(QDialog):
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
        if text0:
            self.lineedit.setText(text0)
        else:
            # Generate a default sorting name
            self.lineedit.setText(get_sortname(properties["ROW_DATA"]))
        self.move(pos)
        if self.exec():
            text = self.lineedit.text()
            if not text:
                text = get_sortname(properties["ROW_DATA"])
            if text != text0:
                # Check that it is unique
                if db_check_unique_entry("PUPILS", SORT_NAME=text):
                    SHOW_ERROR(T["SORT_NAME_EXISTS"])
                else:
                    properties["VALUE"] = text
                    return True
        return False


class CellEditorGroups(CellEditorCheckList):
    """The groups field is a somewhat optional field – the program
    doesn't necessarily need any group information. However, membership
    of certain groups may be important, e.g. if it affects the grading.
    Only compatible groups may be checked simultaneously.
    """

    def __init__(self, classes):
        self.__classes = classes
        super().__init__()

    def set_class(self, klass):
        divisions = self.__classes[klass].divisions
        gdata = build_group_data(divisions)
        self.__g2atoms = {
            g: set(atoms)
            for g, atoms in atomic_maps(
                gdata["MINIMAL_SUBGROUPS"], list(gdata["GROUP_MAP"])
            ).items()
            if g and "." not in g
        }
        # print("\n ... Atoms:", self.__g2atoms)
        self.set_list(self.__g2atoms)

    def item_changed(self, lwi):
        """Check compatibility of groups every time a group is added."""
        if lwi.checkState() == Qt.CheckState.Checked:
            gset = self.get_checked_item_set()
            isct = set.intersection(*[self.__g2atoms[g] for g in gset])
            if not isct:
                lwi.setCheckState(Qt.CheckState.Unchecked)


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from ui.ui_base import run

    widget = ManagePupils()
    widget.enter()
    widget.resize(1000, 550)
    run(widget)
