# -*- coding: utf-8 -*-

"""
core/interface_template_fields.py - last updated 2021-04-08

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
        # lines. A field-name ending '_T' is intended to allow multiple
        # lines, so in this case a check will be made for the style.
        # Reduce to one entry per field, collect number of each field.
        fields = {}         # {field-name -> number of occurrences}
        for field, fstyle in fields_style:
            if field.endswith('_T'):
                if not style:
                    REPORT('ERROR', _BAD_MULTILINE.format(field = field))
                    return False
            try:
                fields[field] += 1
            except KeyError:
                fields[field] = 1
        ### Get "selections", lists of permissible values for certain
        # template fields. These are in the template as space-separated
        # lists. Perform the substitution '_' -> ' ' on the values.
        selects = cls.template.user_info()  # {key -> value (spaced list)}
        slist = {}  # collect used "selects" with python list values
        ### Allocate "editors" (via <validation> parameter) for the fields
        field_info = []
        for field, n in fields.items():
            text = field
            if n > 1:
                text += ' (*%d)' % n
            if field.endswith('_D'):
                validation = 'DATE'
            elif field.endswith('_T'):
                validation = 'TEXT'
            elif field in selects:  # Special pop-up editor
                slist[field] = [s.replace('_', ' ') for s in
                        selects[field].split()]
                validation = field
            else:
                validation = 'LINE'
            field_info.append((field, text, validation))
        CALLBACK('template_SET_FIELDS', path = cls.template.template_path,
                fields = field_info, selects = slist)
        return True
#
    @staticmethod
    def renew(klass, pid):
#TODO: part -> local?
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
            field_values.update(PUPILS(SCHOOLYEAR)[pid])
        CALLBACK('template_RENEW', field_values = field_values)
        return True
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
