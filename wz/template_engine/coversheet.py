### python >= 3.7
# -*- coding: utf-8 -*-

"""
template_engine/coversheet.py

Last updated:  2021-01-07

Build the outer sheets (cover sheets) for the text reports.
User fields in template files are replaced by the report information.

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
_PUPILSNOTINCLASS   = "Schüler {pids} nicht in Klasse {klass}"
_NOPUPILS           = "Mantelbogen: keine Schüler"
_BADPID             = "Schüler {pid} nicht in Klasse {klass}"


import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)
# <core.base> must be the first WZ-import
from core.base import Dates

from core.pupils import Pupils
from template_engine.template_sub import Template, TemplateError
from local.base_config import print_schoolyear, print_class, year_path
from local.text_config import cover_template, COVER_NAME, COVER_DIR


class CoverSheets:
    def __init__(self, schoolyear):
        """<schoolyear>: year in which school-year ends (int)
        """
        self.pupils = Pupils(schoolyear)
#
    def for_class(self, klass, date, pids = None):
        """
        <data>: date of issue ('YYYY-MM-DD')
        <klass>: a <Klass> instance for the school-class
        <pids>: a list of pids (must all be in the given klass), only
            include pupils in this list.
            If not supplied, include the whole klass.
        Return the path to the resulting pdf-file.
        """
        schoolyear = self.pupils.schoolyear
        pdlist = self.pupils.class_pupils(klass)
#        pdlist = self.pupils.classPupils(klass, date = date)

        if pids:
            pall = pdlist
            pset = set(pids)
            pdlist = []
            for pdata in pall:
                try:
                    pset.remove(pdata['PID'])
                except KeyError:
                    continue
                pdlist.append(pdata)
            if pset:
                raise Bug(_PUPILSNOTINCLASS.format(pids = ', '.join(pset),
                        klass = klass))

        template = Template(cover_template(klass))
        gmap0 = {  ## data shared by all pupils in the group
            'A': '',    # 'Tage versäumt'
            'L': '',    # 'mal verspätet'
            'N': '',    # 'Blätter'
            'KK': 'Kleinklassenzweig\n' if klass[-1] == 'K' else '',
            'ISSUE_D': Dates.print_date(date),  # 'Ausgabedatum'
            'CL': print_class(klass),
            'SYEAR': print_schoolyear(schoolyear)
        }

        gmaplist = []
        for pdata in pdlist:
            gmap = gmap0.copy()
            # Get pupil data
            for k in pdata.keys():
                v = pdata[k]
                if v:
                    if k.endswith('_D'):
                        v = Dates.print_date(v)
                else:
                    v = ''
                gmap[k] = v
            gmaplist.append(gmap)

        # make_pdf: data_list, dir_name, working_dir, double_sided = False
        return template.make_pdf(gmaplist,
                COVER_NAME.format(klass = klass),
                year_path(schoolyear, COVER_DIR)
        )


#TODO
def makeOneSheet(schoolyear, date, klass, pupil):
    """
    <schoolyear>: year in which school-year ends (int)
    <data>: date of issue ('YYYY-MM-DD')
    <klass>: a <Klass> instance for the school-class
    <pupil>: a mapping with the necessary pupil information (at least a
    subset of <PupilData>).
    """
    template = getTextTemplate('Mantelbogen', klass)
    source = template.render(
            SCHOOLYEAR = printSchoolYear(schoolyear),
            DATE_D = date,
            todate = Dates.dateConv,
            pupils = [pupil],
            klass = klass
        )
    html = HTML (string=source,
            base_url=os.path.dirname (template.filename))
    pdfBytes = html.write_pdf(font_config=FontConfiguration())
    return pdfBytes


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    from core.base import init
    init()

    _year = '2016'
    _date = '2016-06-22'

    csheets = CoverSheets(_year)

    _klass = '12'
    fpath = csheets.for_class(_klass, _date)
    print(" -->", fpath)
