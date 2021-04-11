# -*- coding: utf-8 -*-

"""
core/interface_template_fields.py - last updated 2021-04-11

Controller/dispatcher for the template-filler module.

==============================
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
"""

### Messages
_NO_SUBSTITUTIONS = "Keine Felder werden ersetzt: Keine Datei wird erstellt."
_DONE_ODT = "Neue Datei erstellt:\n  {fodt}"
_DONE_PDF = "Neue Dateien erstellt:\n  {fodt}\n  {fpdf}"
_DONE_SHOW = "Zwischendateien gelöscht"

################################################

import os

from core.base import Dates, DataError
from core.pupils import PUPILS
from local.base_config import PupilsBase, class_year, print_schoolyear, \
        print_class
from local.field_handlers import ManageHandlers, FieldMap, FieldHandlerError
from template_engine.template_sub import Template, TemplateError

### +++++

NONE = ''

class Template_Filler:
    template = None
#
    @staticmethod
    def get_classes():
        pupils = PUPILS(SCHOOLYEAR)
        class_list = pupils.classes()
        class_list.reverse()   # start with the highest classes
        CALLBACK('template_SET_CLASSES', classes = class_list)
        return True
#
    @staticmethod
    def set_class(klass):
        pupils = PUPILS(SCHOOLYEAR)
        plist = [('', '–––')] + [(pdata['PID'], pupils.name(pdata))
                for pdata in pupils.class_pupils(klass)]
        CALLBACK('template_SET_PUPILS', pupil_list = plist)
        return True
#
    @staticmethod
    def get_template_dir():
        """Fetch the path to a template file.
        The RESOURCES folder is searched to find suitable files.
        These have certain metadata fields set:
            'title': must start with 'WZ-template'
            'subject': short description
        This allows a somewhat documented list/tree of available templates
        to be shown.
        """
        startpath = os.path.join(RESOURCES, 'templates')
        data = []
        for (root, dirs, files) in os.walk(startpath):
            tfiles = []
            for f in files:
                if f.endswith('.odt'):
                    try:
                        t = Template(os.path.join(root, f), full_path = True)
                    except:
                        # Not a template file
                        continue
                    _meta = t.metadata()
                    try:
                        title = _meta['title']
                    except KeyError:
                        continue
                    if title.startswith('WZ-template'):
                        tfiles.append('%s:: %s' % (f, _meta['subject']))
            if tfiles:
                tfiles.sort()
                data.append((root, tfiles))
        data.sort()
        CALLBACK('template_CHOOSE_TEMPLATE', templates = data)
        return True
#
    @classmethod
    def set_template(cls, template_path):
        cls.template = Template(template_path, full_path = True)
        ### Get template fields: [(field, style or <None>), ...]
        fields_style = cls.template.fields()
        # The fields are in order of appearance in the template file,
        # keys may be present more than once!
        # The style is only present for fields which are alone within a
        # paragraph. This is a prerequisite for an entry with multiple
        # lines – if an entry has line-breaks but no style, the generator
        # will raise an Exception (TemplateError).
        ### Count number of appearances, reduce to single entries
        _fields = {}
        for f, s in fields_style:
            try:
                _fields[f] += 1
            except KeyError:
                _fields[f] = 1
        ### Get field information from the template file.
        # This tells us how to handle certain fields.
        # There can be "selections", for example, a list of permissible
        # values for a particular template field.
        try:
            handlers = ManageHandlers(cls.template.metadata().get('FIELD_INFO'))
            # Order the fields so that dependencies come before the fields
            # that need them:
            fields, deps = handlers.sort_dependencies(_fields)
            # One problem now is to distinguish between dependent fields
            # with only internal dependencies and those with (also)
            # external dependencies. The former are non-editable, for
            # the latter an editor must be provided.
            cls.field_map = FieldMap(handlers, {})
            field_info = []
            selects = {}  # collect used "selects" with python list values
            for field in fields:
                text, n = field, _fields[field]
                if n != 1:
                    text += f' (*{n})'
                sel = cls.field_map.selection(field)
                if sel == 'LINE':
                    validation = 'LINE'
                elif sel == 'DATE':
                    validation = 'DATE'
                elif sel == 'TEXT':
                    validation = 'TEXT'
                elif not sel:
                    # Field not writeable
                    validation = NONE
                else:
                    # It must be a selection list/map
                    validation, slist = sel
                    if validation not in selects:
                        selects[validation] = slist
                cls.field_map[field] = NONE
                field_info.append((field, text, validation))
            CALLBACK('template_SET_FIELDS', path = cls.template.template_path,
                    fields = field_info, selects = selects)
        except FieldHandlerError as e:
            REPORT('ERROR', str(e))
            return False
        return True
#
    @classmethod
    def renew(cls, klass, pid):
#TODO: part -> local?
# Some of this can be done by template transforms ...
        ### Initial fields
        year = SCHOOLYEAR
        _syL = print_schoolyear(year)
        field_values = {
            'schoolyear': year,
            'SCHOOLYEAR': _syL,
            'SYEAR': _syL,
            'SCHOOL': SCHOOL_DATA['SCHOOL_NAME'],
            'SCHOOLBIG': SCHOOL_DATA['SCHOOL_NAME'].upper()
        }
        if klass:
            field_values['CL'] = print_class(klass)
            field_values['CLASS'] = print_class(klass)
            field_values['CYEAR'] = class_year(klass)
        if pid:
            # This could (perhaps ...) change CLASS
            field_values.update(PUPILS(SCHOOLYEAR)[pid])

#TODO: transforms ...
        _fields = {}
        for f in cls.field_map:
            try:
                cls.field_map[f] = field_values[f]
            except KeyError:
                pass
            val = cls.field_map.exec_(f, force = True)
            _fields[f] = val


        CALLBACK('template_RENEW', field_values = _fields)
        return True

#TODO: handle changes

#
    @staticmethod
    def all_fields(fields, clear_empty):
        fmap = {}
        for f, v in fields.items():
            if v or clear_empty:
                if f.endswith('_D'):
                    try:
                        v = Dates.print_date(v)
                    except DataError:
                        pass
                fmap[f] = v
        try:
            fmap['LASTNAME'] = fmap['LASTNAME'].replace('|', ' ')
        except:
            pass
        return fmap
#
    @classmethod
    def gen_doc(cls, fields, clear_empty, filepath):
        fieldmap = cls.all_fields(fields, clear_empty)
        if not fieldmap:
            REPORT('WARN', _NO_SUBSTITUTIONS)
            return False
        odtBytes = cls.template.make_doc(fieldmap)
        if not filepath.endswith('.odt'):
            filepath += '.odt'
        with open(filepath, 'wb') as fh:
            fh.write(odtBytes)
        REPORT('INFO', _DONE_ODT.format(fodt = filepath))
        return True
#
    @classmethod
    def gen_pdf(cls, fields, clear_empty, filepath):
        fieldmap = cls.all_fields(fields, clear_empty)
        cc = cls.template.make1pdf(fieldmap, file_path = filepath)
        if cc:
            REPORT('INFO', _DONE_PDF.format(fpdf = cc,
                    fodt = cc.rsplit('.', 1)[0] + '.odt'))
            return True
        else:
            return False
#
    @classmethod
    def show(cls):
        cls.template.show({})
        return True


FUNCTIONS['TEMPLATE_get_classes'] = Template_Filler.get_classes
FUNCTIONS['TEMPLATE_set_class'] = Template_Filler.set_class
FUNCTIONS['TEMPLATE_get_template_dir'] = Template_Filler.get_template_dir
FUNCTIONS['TEMPLATE_set_template'] = Template_Filler.set_template
FUNCTIONS['TEMPLATE_renew'] = Template_Filler.renew
FUNCTIONS['TEMPLATE_gen_doc'] = Template_Filler.gen_doc
FUNCTIONS['TEMPLATE_gen_pdf'] = Template_Filler.gen_pdf
FUNCTIONS['TEMPLATE_show'] = Template_Filler.show
