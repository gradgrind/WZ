# -*- coding: utf-8 -*-
"""
gui/template_fields.py

Last updated:  2021-01-16

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

### Messages
_DONE_PDF = "Neue Dateien erstellt:\n  {fodt}\n  {fpdf}"
_DONE_SHOW = "Zwischendateien gelöscht"

### Labels, etc.
_EDIT_FIELDS = "Vorlage ausfüllen"
_CLASS = "Klasse:"
_TEST_FIELDS = "Felder testen"
_GEN_ODT = "ODT erstellen"
_GEN_PDF = "PDF erstellen"
_CHOOSE_TEMPLATE = "Vorlage wählen"
_FILEOPEN = "Datei öffnen"
_FILESAVE = "Datei speichern"
_TEMPLATE_FILE = "LibreOffice Text-Vorlage (*.odt)"
_ODT_FILE = "LibreOffice Text-Dokument (*.odt)"
_PDF_FILE = "PDF-Dokument (*.pdf)"
_NULLEMPTY = "Null-Felder leer"
_NULLEMPTY_TIP = "Felder, für die keinen Wert gesetzt ist werden leer" \
        " dargestellt. Ansonsten bleibt die Feldmarke."
_SELECT_OR_BROWSE = "Datei wählen – oder suchen"
_BROWSE = "Suchen"

#####################################################

import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)
    from qtpy.QtWidgets import QApplication
#    app = QApplication(['test', '-style=windows'])
    app = QApplication([])
# <core.base> must be the first WZ-import
import core.base as CORE

from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, \
        QPushButton, QCheckBox, QFileDialog, QSpacerItem

from gui.grid import GridView, Grid
from gui.gui_support import VLine, KeySelect, TabPage, GuiError, TreeDialog

from core.pupils import Pupils, NullPupilData
from local.base_config import PupilsBase, class_year, print_schoolyear, \
        print_class
from local.grade_config import STREAMS
from template_engine.template_sub import Template, TemplateError
from template_engine.simpleodt import metadata

###

class GView(GridView):
    pass

###

## Measurements are in mm ##
_HEIGHT_LINE = 6
COLUMNS = (40, 60)
ROWS = (
#title
    12,
) # + _HEIGHT_LINE * n

###

class FieldGrid(Grid):
    """Present the data for a template, allowing editing of the
    individual fields.
    There is special handling for certain pupil fields.
    """
    def __init__(self, view, template):
        """<view> is the QGraphicsView in which the grid is to be shown.
        <template> is a <Template> instance.
        """
        # Get template fields: [(field, style or <None>), ...]
        fields_style = template.fields()
        # The fields are in order of appearance in the template file,
        # keys may be present more than once!
        # The style is only present for fields which are alone within a
        # paragraph. It indicates that multiple lines are possible, so
        # normally a multi-line editor will be provided.
        # Reduce to one entry per field, collect number of each field.
        self.fields = {}    # {field-name -> number of occurrences}
        multiline = {}      # {field-name -> <bool>}
        for field, fstyle in fields_style:
            try:
                self.fields[field] += 1
                if not fstyle:
                    # all occurrences must allow multi-line values
                    multiline[field] = False
            except KeyError:
                self.fields[field] = 1
                multiline[field] = bool(fstyle)
        _ROWS = ROWS + (_HEIGHT_LINE,) * len(self.fields)
        super().__init__(view, _ROWS, COLUMNS)
        self.styles()
        ### Non-editable fields
        noneditable = {'PSORT'}
        ### Title area
        self.tile(0, 0, text = '', cspan = 2, style = 'title', tag = 'title')
        ### field - value lines
        row = 1
        for field, n in self.fields.items():
            text = field
            if n > 1:
                text += ' (*%d)' % n
            self.tile(row, 0, text = text, style = 'key')
            vstyle = 'value'
            if field in noneditable:
                vstyle = 'fixed'
                validation = None
            elif field in self.editors:
                validation = field
            elif field.endswith('_D'):
                validation = 'DATE'
            else:
                if field == 'SEX':          # Special pop-up editor
                    validation = 'SEX'
                    self.addSelect('SEX', PupilsBase.SEX)
                elif field == 'STREAM':
                    validation = 'STREAM'   # Special pop-up editor
                    self.addSelect('STREAM', STREAMS)
                elif multiline[field]:
                    validation = 'TEXT'
                else:
                    validation = 'LINE'
            self.tile(row, 1, text = '', style = vstyle,
                    validation = validation, tag = field)
            row += 1
#
    def styles(self):
        """Set up the styles used in the table view.
        """
        self.new_style('base', font = SCHOOL_DATA.FONT, size = 11)
        self.new_style('title', font = SCHOOL_DATA.FONT, size = 12,
                align = 'c', border = 0, highlight = 'b')
        self.new_style('key', base = 'base', align = 'l')
        self.new_style('fixed', base = 'key', highlight = ':808080')
        self.new_style('value', base = 'key',
                highlight = ':002562', mark = 'E00000')
#
    def set_fields(self, mapping):
        for field in self.fields:
            self.set_text_init(field, mapping.get(field) or '')
#
    def valueChanged(self, tag, text):
        """Called when a cell value is changed by the editor.
        """
        super().valueChanged(tag, text)
        if tag in self.values:
            self.values[tag] = text

###

class FieldEdit(TabPage):
    def __init__(self):
        super().__init__(_EDIT_FIELDS)
        topbox = QHBoxLayout()
        self.vbox.addLayout(topbox)

        #*********** The "main" widget ***********
        self.fieldView = GView()
        self.field_scene = None
        topbox.addWidget(self.fieldView)
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

        cbox.addSpacing(30)
        cbox.addStretch(1)

        testfields = QPushButton(_TEST_FIELDS)
        cbox.addWidget(testfields)
        testfields.clicked.connect(self.test_fields)
        cbox.addSpacing(30)
        self.nullempty = QCheckBox(_NULLEMPTY)
        self.nullempty.setToolTip(_NULLEMPTY_TIP)
        self.nullempty.setChecked(False)
        cbox.addWidget(self.nullempty)
        odtgen = QPushButton(_GEN_ODT)
        cbox.addWidget(odtgen)
        odtgen.clicked.connect(self.gen_doc)
        pdfgen = QPushButton(_GEN_PDF)
        cbox.addWidget(pdfgen)
        pdfgen.clicked.connect(self.gen_pdf)
#
    def enter(self):
        self.year_changed()
#
    def leave(self):
        pass
#
    def year_changed(self):
        self.pupils = Pupils(ADMIN.schoolyear)
        self.class_select.set_items([('', '–––')] + [(c, c)
                for c in self.pupils.classes()])
        self.class_select.trigger()
#
    def class_changed(self, klass):
        self.klass = klass
        if klass:
            self.pdlist = self.pupils.class_pupils(klass)
            self.pselect.set_items([('', '–––')] + [(pdata['PID'],
                    pdata.name())   for pdata in self.pdlist])
        else:
            self.pselect.clear()
            self.pid = None
            self.pdata = None
        self.pselect.trigger()
#
    def pupil_changed(self, pid):
        """A new pupil has been selected: reset the grid accordingly.
        """
        self.pid = pid
        if pid:
            # Replace pupil data
            self.pdata = self.pdlist.pid2pdata(pid)
        else:
            # Clear pupil data
            self.pdata = {'CLASS': self.klass}
        if not self.clear():
            self.pselect.reset(self.pupil_scene.pid)
            return
        if self.field_scene:
            self.renew()
#
    def get_template(self):
        data = []
        for (root, dirs, files) in os.walk(os.path.join(RESOURCES,
                'templates')):
            tfiles = []
            for f in files:
                if f.endswith('.odt'):
                    title, subject = metadata(os.path.join(root, f))
                    if title and title.startswith('WZ-template'):
                        tfiles.append('%s:: %s' % (f, subject))
            if tfiles:
                tfiles.sort()
                data.append((root, tfiles))
        data.sort()
        cc = TreeDialog(_CHOOSE_TEMPLATE, _SELECT_OR_BROWSE,
                data, button = _BROWSE)
        if not cc:
            return
        if cc[0]:
            fpath = os.path.join(cc[0], cc[1].split('::', 1)[0])
        else:
            # file dialog – start at template folder
            dir0 = os.path.join(RESOURCES, 'templates')
            fpath = QFileDialog.getOpenFileName(self, _FILEOPEN,
                    dir0, _TEMPLATE_FILE)[0]
            if not fpath:
                return
        self.template = Template(fpath, full_path = True)
        self.field_scene = FieldGrid(self.fieldView, self.template)
        self.fieldView.set_scene(self.field_scene)
        title = fpath
        if len(title) > 42:
            title = '... ' + title[-40:]
        self.field_scene.set_text_init('title', title)
        self.renew()
#
    def renew(self):
        ### Initial fields
        _sy = ADMIN.schoolyear
        _syL = print_schoolyear(_sy)
        _cl = print_class(self.klass) if self.klass else ''
        self.field_values = {
            'schoolyear': _sy,
            'SCHOOLYEAR': _syL,
            'SYEAR': _syL,
            'CL': _cl,
            'CYEAR': class_year(self.klass) if self.klass else '',
            'SCHOOL': SCHOOL_DATA.SCHOOL_NAME,
            'SCHOOLBIG': SCHOOL_DATA.SCHOOL_NAME.upper()
        }
        # Add pupil data
        if self.pdata:
            self.field_values.update(self.pdata)
        self.field_scene.set_fields(self.field_values)
#
    def test_fields(self):
        """Substitute all fields with *<field>* (to be easily visible)
        and display the result.
        """
        # Run as background thread because of potential delay.
        all_fields = {f: '*%s*' % f for f in self.field_scene.fields}
        fn = _MakePdf(self.template, all_fields)
        REPORT('RUN', runme = fn)
#
    def gen_doc(self):
        """If the "nullempty" checkbox is true, fields for which no
        value is supplied will be cleared. Otherwise the "tag" is left.
        """
        if self.nullempty.isChecked():
            all_fields = {f: self.field_values.get(f, '')
                    for f in self.field_scene.fields}
            odtBytes = self.template.make_doc(all_fields)
        else:
            odtBytes = self.template.make_doc(self.field_values)
        dir0 = ADMIN._savedir or os.path.expanduser('~')
        try:
            filename = self.pdata.name() + '_'
        except:
            filename = '_'
        filename += os.path.basename(self.template.template_path).rsplit(
                '.', 1)[0]
        fpath = QFileDialog.getSaveFileName(self.fieldView, _FILESAVE,
                os.path.join(dir0, filename), _ODT_FILE)[0]
        if fpath:
            ADMIN.set_savedir(os.path.dirname(fpath))
            if not fpath.endswith('.odt'):
                fpath += '.odt'
            with open(fpath, 'wb') as fh:
                fh.write(odtBytes)
#
    def gen_pdf(self):
        """If the "nullempty" checkbox is true, fields for which no
        value is supplied will be cleared. Otherwise the "tag" is left.
        """
        # Run as background thread because of potential delay.
        dir0 = ADMIN._savedir or os.path.expanduser('~')
        try:
            filename = self.pdata.name() + '_'
        except:
            filename = '_'
        filename += os.path.basename(self.template.template_path).rsplit(
                '.', 1)[0]
        fpath = QFileDialog.getSaveFileName(self.fieldView, _FILESAVE,
                os.path.join(dir0, filename), _PDF_FILE)[0]
        if fpath:
            ADMIN.set_savedir(os.path.dirname(fpath))
            if not fpath.endswith('.pdf'):
                fpath += '.pdf'
        else:
            return
        if self.nullempty.isChecked():
            all_fields = {self.field_values.get(f, '')
                    for f in self.field_scene.fields}
        else:
            all_fields = self.field_values
        fn = _MakePdf(self.template, all_fields, fpath)
        REPORT('RUN', runme = fn)

###

class _MakePdf(CORE.ThreadFunction):
    def __init__(self, template, all_fields, filepath = None):
        super().__init__()
        self._template = template
        self._fields = all_fields
        self._filepath = filepath
        self._show_only = not filepath
#
    def run(self):
        cc = self._template.make1pdf(self._fields,
                show_only = self._show_only, file_path = self._filepath)
        if cc:
            REPORT('INFO', _DONE_PDF.format(fpdf = cc,
                    fodt = cc.rsplit('.', 1)[0] + '.odt'))
        else:
            REPORT('INFO', _DONE_SHOW)
#
    def terminate(self):
        return False


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    CORE.init()

    class ADMIN:
        schoolyear = '2016'
        _loaddir = None
        _savedir = None
        @classmethod
        def set_savedir(cls, path):
            cls._savedir = path
        @classmethod
        def set_loaddir(cls, path):
            cls._loaddir = path

    main = FieldEdit()
    main.enter()
    main.show()
    main.resize(700, 400)
    sys.exit(app.exec_())
