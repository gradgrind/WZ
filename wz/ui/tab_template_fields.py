# -*- coding: utf-8 -*-
"""
ui/tab_template_fields.py

Last updated:  2021-04-11

Show template fields, set values and process template.
This module is intended primarily for testing purposes.

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

## Measurements are in mm ##
_HEIGHT_LINE = 6
COLUMNS = (40, 60)
ROWS = (
#title
    12,
) # + _HEIGHT_LINE * n

### Messages
_TEMPLATES_TEXT = """## Dokument-Vorlagen

Hier können die ersetzbaren Felder der Dokument-Vorlagen angezeigt werden.
Werte können für die Felder eingegeben werden und die Dokumente können
so ausgefüllt ausgegeben werden.
"""

### Labels, etc.
_EDIT_FIELDS = "Vorlage ausfüllen"
_CLASS = "Klasse:"
_TEST_FIELDS = "Felder testen"
_GEN_ODT = "ODT erstellen"
_GEN_PDF = "PDF erstellen"
_CHOOSE_TEMPLATE = "Vorlage wählen"
_TEMPLATE_FILE = "LibreOffice Text-Vorlage (*.odt)"
_ODT_FILE = "LibreOffice Text-Dokument (*.odt)"
_PDF_FILE = "PDF-Dokument (*.pdf)"
_NULLEMPTY = "Null-Felder leer"
_NULLEMPTY_TIP = "Felder, für die keinen Wert gesetzt ist werden leer" \
        " dargestellt. Ansonsten bleibt die Feldmarke."
_SELECT_OR_BROWSE = "Datei wählen – oder suchen"
_BROWSE = "Suchen"
#_SAVE = "Änderungen Speichern"

#####################################################

import os

from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, \
        QPushButton, QCheckBox, QFileDialog, QSpacerItem, \
        QWidget, QTextEdit, QStackedWidget

from ui.grid import EditableGridView, Grid
from ui.ui_support import VLine, KeySelect, TabPage, GuiError, \
        TreeDialog, saveDialog

### +++++

NONE = ''

class StackedWidget_info(QTextEdit):
    def __init__(self, tab_widget):
        self._tab = tab_widget
        super().__init__()
        self.setReadOnly(True)
        self.setMarkdown(_TEMPLATES_TEXT)
#
    def is_modified(self):
        return False
#
    def changes(self):
        return False
#
    def activate(self):
        return
        for pb in ('TEMPLATE',):
            self._tab.enable(pb, True)
#
    def deactivate(self):
        return True

###

class StackedWidget_fill(EditableGridView):
    def __init__(self, tab_widget):
        self._tab = tab_widget
        super().__init__()
        self.fill_scene = None
#
    def is_modified(self):
        return False
#
#    def set_changed(self, show):
#        self._tab.enable('SAVE', show)
#
    def activate(self, title, fields, selects):
        self.fill_scene = FieldGrid(self, fields, selects)
        self.set_scene(self.fill_scene)
        for pb in ('ODT', 'PDF', 'TEST', 'NULLEMPTY'):
            self._tab.enable(pb, True)
        self.fill_scene.set_text_init('title', title)
        BACKEND('TEMPLATE_renew', klass = self._tab.klass,
                pid = self._tab.pid)
#
    def deactivate(self):
        self.fill_scene = None
        self.set_scene(None)
#
#    def save(self):
#        BACKEND('PUPILS_new_data', data = self.fill_scene.pupil_data)
#
    def renew(self, field_values):
        valmap = {}
        for f in self.fill_scene.values:
            valmap[f] = field_values[f]
        self.fill_scene.set_fields(valmap)
#
    def gen_doc(self, template):
        """If the "NULLEMPTY" checkbox is true, fields for which no
        value is supplied will be cleared. Otherwise the "tag" is left.
        """
        filename = self._tab.pid + '_' + os.path.basename(
                template).rsplit('.', 1)[0]
        fpath = saveDialog(_ODT_FILE, filename)
        if fpath:
            BACKEND('TEMPLATE_gen_doc', fields = self.fill_scene.values,
                    clear_empty = self._tab._widgets['NULLEMPTY'].isChecked(),
                    filepath = fpath)
#
    def gen_pdf(self, template):
        """If the "NULLEMPTY" checkbox is true, fields for which no
        value is supplied will be cleared. Otherwise the "tag" is left.
        """
        filename = self._tab.pid + '_' + os.path.basename(
                template).rsplit('.', 1)[0]
        fpath = saveDialog(_PDF_FILE, filename)
        if fpath:
            BACKEND('TEMPLATE_gen_pdf', fields = self.fill_scene.values,
                    clear_empty = self._tab._widgets['NULLEMPTY'].isChecked(),
                    filepath = fpath)

######################################################################

class FieldGrid(Grid):
    """Present the data for a template, allowing editing of the
    individual fields.
    There is special handling for certain pupil fields.
    """
    def __init__(self, view, fields, selects):
        """<view> is the QGraphicsView in which the grid is to be shown.
        <fields> is a list of [field, field name, "validation"] items.
        <selects> is a mapping containing selection lists.
        """
        _ROWS = ROWS + (_HEIGHT_LINE,) * len(fields)
        super().__init__(view, _ROWS, COLUMNS)
        self.styles()
        ### Title area
        self.tile(0, 0, text = '', cspan = 2, style = 'title', tag = 'title')
        ### field - value lines
        row = 1
        for field, slist in selects.items():
            self.addSelect(field, slist)
        self.values = {}
        for field, text, validation in fields:
            self.tile(row, 0, text = text, style = 'key')
            self.tile(row, 1, text = '',
                    style = 'value' if validation else 'fixed',
                    validation = validation, tag = field)
            self.values[field] = ''
            row += 1
#
    def styles(self):
        """Set up the styles used in the table view.
        """
        self.new_style('base', font = ADMIN.school_data['FONT'], size = 11)
        self.new_style('title', base = 'base', size = 12,
                align = 'c', border = 0, highlight = 'b')
        self.new_style('key', base = 'base', align = 'l')
        self.new_style('fixed', base = 'key', highlight = ':808080')
        self.new_style('value', base = 'key',
                highlight = ':002562', mark = 'E00000')
#
    def set_fields(self, mapping):
        for field, val in mapping.items():
            self.set_text_init(field, val)
            self.values[field] = val
#
    def value_changed(self, tile, val):
        """Called when a cell value is changed by the editor.
        """
#TODO: Pass it to the back-end ...
# The automatic processing, handling of dependencies, etc. must be done
# before anything new is displayed.
        super().value_changed(tile, val)
        if tile.tag in self.values:
            self.values[tile.tag] = val

###

class FieldEdit(TabPage):
    def __init__(self):
        super().__init__(_EDIT_FIELDS)
        self._widgets = {}
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
        # 1) Table for filling template fields
        _w = StackedWidget_fill(self)
        self.main.addWidget(_w)
        self._widgets['FILL'] = _w

        topbox.addWidget(VLine())

        cbox = QVBoxLayout()
        topbox.addLayout(cbox)
        cbox.addSpacerItem(QSpacerItem(180, 0))

        ### Select template
        choose_template = QPushButton(_CHOOSE_TEMPLATE)
        cbox.addWidget(choose_template)
        choose_template.clicked.connect(self.get_template)

        ### Select class
        self.class_select = KeySelect(changed_callback = self.class_changed)
        cbox.addWidget(QLabel(_CLASS))
        cbox.addWidget(self.class_select)

        ### List of pupils
        self.pselect = KeySelect(changed_callback = self.pupil_changed)
        cbox.addWidget(self.pselect)

        cbox.addStretch(1)

        ### Test template fields
        # (generate output file with all fields slightly changed)
        _w = QPushButton(_TEST_FIELDS)
        self._widgets['TEST'] = _w
        cbox.addWidget(_w)
        _w.clicked.connect(self.test_fields)

        cbox.addSpacing(30)

        ### Toggle "leave tags if value empty"
        _w = QCheckBox(_NULLEMPTY)
        self._widgets['NULLEMPTY'] = _w
        _w.setToolTip(_NULLEMPTY_TIP)
        _w.setChecked(False)
        cbox.addWidget(_w)

        ### Generate odt-file
        _w = QPushButton(_GEN_ODT)
        self._widgets['ODT'] = _w
        cbox.addWidget(_w)
        _w.clicked.connect(self.gen_doc)

        ### Generate pdf-file (and odt-file), without user-meta data.
        _w = QPushButton(_GEN_PDF)
        self._widgets['PDF'] = _w
        cbox.addWidget(_w)
        _w.clicked.connect(self.gen_pdf)
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
        for pb in ('NULLEMPTY', 'TEST', 'ODT', 'PDF'):
            self.enable(pb, False)
        new.activate(**params)
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
        self.template = None
        BACKEND('TEMPLATE_get_classes') # ... -> SET_CLASSES
#
    def leave(self):
        """Called when the tab is deselected.
        """
        self.main.currentWidget().deactivate()
#
    def is_modified(self):
        return self.main.currentWidget().is_modified()
#
    def SET_CLASSES(self, classes):
        self.class_select.set_items([('', '–––')] + [(c, c)
                for c in classes])
        self.class_changed(NONE)
#
    def class_changed(self, klass):
        self.klass = klass
        if klass:
            BACKEND('TEMPLATE_set_class', klass = klass) # ... -> SET_PUPILS
        else:
            self.SET_PUPILS(None)
        return True
#
    def SET_PUPILS(self, pupil_list):
        self.pselect.set_items(pupil_list)
        self.pupil_changed(NONE)
#
    def pupil_changed(self, pid):
        self.pid = pid
        if self.template:
            BACKEND('TEMPLATE_renew', klass = self.klass, pid = self.pid)
        return True
#
    def get_template(self):
        BACKEND('TEMPLATE_get_template_dir') # ... -> CHOOSE_TEMPLATE
#
    def CHOOSE_TEMPLATE(self, templates):
        cc = TreeDialog(_CHOOSE_TEMPLATE, _SELECT_OR_BROWSE,
                templates, button = _BROWSE)
        if not cc:
            return
        if cc[0]:
            fpath = os.path.join(cc[0], cc[1].split('::', 1)[0])
        else:
            # file dialog
            fpath = openDialog(_TEMPLATE_FILE)
            if not fpath:
                return
        BACKEND('TEMPLATE_set_template', template_path = fpath)
        # ... -> SET_FIELDS
#
    def SET_FIELDS(self, path, fields, selects):
        self.template = path
        title = self.template
        if len(title) > 42:
            title = '... ' + title[-40:]
        self.set_widget('FILL', title = title,
                fields = fields, selects = selects)
#
    def RENEW(self, field_values):
        self.main.currentWidget().renew(field_values)
#
    def gen_doc(self):
        self.main.currentWidget().gen_doc(self.template)
#
    def gen_pdf(self):
        self.main.currentWidget().gen_pdf(self.template)
#
    def test_fields(self):
        """Substitute all fields with {field} (to be easily visible)
        and display the result.
        """
        BACKEND('TEMPLATE_show')
#
#    def save(self):
#        self.main.currentWidget().save()


tab_template_fields = FieldEdit()
TABS.append(tab_template_fields)
FUNCTIONS['template_SET_CLASSES'] = tab_template_fields.SET_CLASSES
FUNCTIONS['template_SET_PUPILS'] = tab_template_fields.SET_PUPILS
FUNCTIONS['template_CHOOSE_TEMPLATE'] = tab_template_fields.CHOOSE_TEMPLATE
FUNCTIONS['template_SET_FIELDS'] = tab_template_fields.SET_FIELDS
FUNCTIONS['template_RENEW'] = tab_template_fields.RENEW
