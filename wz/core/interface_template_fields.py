# -*- coding: utf-8 -*-

"""
core/interface_template_fields.py - last updated 2021-04-06

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

#TODO ...

### Messages

### Labels, etc.
_ALL_PUPILS = "* Ganze Klasse *"

import os

from core.pupils import PUPILS, NullPupilData
from local.base_config import PupilsBase, class_year, print_schoolyear, \
        print_class
from template_engine.template_sub import Template, TemplateError
from template_engine.simpleodt import metadata


###

NONE = ''

class Template_Filler:
    template = None

    @staticmethod
    def get_classes():
        pupils = PUPILS(SCHOOLYEAR)
        class_list = pupils.classes()
        class_list.reverse()   # start with the highest classes
        CALLBACK('template_SET_CLASSES', classes = class_list)
        return True

    @staticmethod
    def get_template_dir():
        CALLBACK('template_CHOOSE_TEMPLATE', startpath = os.path.join(
                RESOURCES, 'templates'))
        return True

###

    @classmethod
    def set_template(cls, template_path):
        cls.template = Template(template_path, full_path = True)



        # Get template fields: [(field, style or <None>), ...]
        fields_style = cls.template.fields()
        # The fields are in order of appearance in the template file,
        # keys may be present more than once!
        # The style is only present for fields which are alone within a
        # paragraph. It indicates that multiple lines are possible, so
        # normally a multi-line editor will be provided.
        # Reduce to one entry per field, collect number of each field.
        fields = {}         # {field-name -> number of occurrences}
        multiline = {}      # {field-name -> <bool>}
        for field, fstyle in fields_style:
            try:
                fields[field] += 1
                if not fstyle:
                    # all occurrences must allow multi-line values
                    multiline[field] = False
            except KeyError:
                fields[field] = 1
                multiline[field] = bool(fstyle)

        for field, n in fields.items():
            text = field
            if n > 1:
                text += ' (*%d)' % n
            vstyle = 'value'
            if field in noneditable:
                vstyle = 'fixed'
                validation = None
            elif field.endswith('_D'):
                validation = 'DATE'
            elif field in selects:  # Special pop-up editor
                validation = field
                self.addSelect(field, selects[field])
            elif multiline[field]:
                validation = 'TEXT'
            else:
                validation = 'LINE'



    @classmethod
    def make_pdf(cls):
        cc = cls._template.make1pdf(cls._fields,
                show_only = cls._show_only, file_path = cls._filepath)
        if cc:
            REPORT('INFO', _DONE_PDF.format(fpdf = cc,
                    fodt = cc.rsplit('.', 1)[0] + '.odt'))
        else:
            REPORT('INFO', _DONE_SHOW)




def set_class(klass):
    pupils = PUPILS(SCHOOLYEAR)
    plist = [('', _ALL_PUPILS)] + [(pdata['PID'], pupils.name(pdata))
            for pdata in pupils.class_pupils(klass)]
    CALLBACK('text_SET_PUPILS', pupil_list = plist)
    return True

###

def make_covers(date, klass):
    coversheets = CoverSheets(SCHOOLYEAR)
    fpath = coversheets.for_class(klass, date)
    REPORT('INFO', _MADE_COVERS.format(path = fpath))
    return True
#
def covername(pid):
    coversheets = CoverSheets(SCHOOLYEAR)
    CALLBACK('text_MAKE_ONE_COVER', filename = coversheets.filename1(pid))
    return True
#
def make_one_cover(pid, date, filepath):
    coversheets = CoverSheets(SCHOOLYEAR)
    pdfbytes = coversheets.for_pupil(pid, date)
    with open(filepath, 'wb') as fh:
        fh.write(pdfbytes)
    REPORT('INFO', _MADE_ONE_COVER.format(path = filepath))
    return True


FUNCTIONS['TEMPLATE_get_classes'] = Template_Filler.get_classes
FUNCTIONS['TEMPLATE_get_start_dir'] = Template_Filler.get_template_dir
