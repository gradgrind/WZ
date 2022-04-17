# -*- coding: utf-8 -*-

"""
template_engine/coversheet.py

Last updated:  2021-05-22

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
# ---

import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)
# <core.base> must be the first WZ-import
from core.base import Dates

from core.pupils import PUPILS, sortkey
from template_engine.template_sub import Template
#from local.base_config import print_schoolyear, year_path
from local.base_config import sortkey, print_class
from local.text_config import cover_template, COVER_NAME, COVER_DIR


class CoverSheets:
    def __init__(self, schoolyear):
        """<schoolyear>: year in which school-year ends (int)
        """
        self.pupils = PUPILS(schoolyear)
#
    def for_class(self, klass, date):
        """
        <data>: date of issue ('YYYY-MM-DD')
        <klass>: a <Klass> instance for the school-class
        Return the path to the resulting pdf-file.
        """
        schoolyear = self.pupils.schoolyear
        pdlist = self.pupils.class_pupils(klass)
#        pdlist = self.pupils.classPupils(klass, date = date)
        template = Template(cover_template(klass))
        gmap0 = self.base_data(klass, date)
        gmaplist = []
        for pdata in pdlist:
            gmap = self.pupil_data(pdata)
            gmap.update(gmap0)
            gmaplist.append(gmap)
        # make_pdf: data_list, dir_name, working_dir, double_sided = False
        return template.make_pdf(gmaplist,
                COVER_NAME.format(klass = klass),
                year_path(schoolyear, COVER_DIR)
        )
#
    def for_pupil(self, pid, date, filepath = None):
        """Make a single cover sheet, for the pupil with the given <pid>.
        If <filepath> is supplied, the pdf will be saved there.
        An intermediate odt-file (with the same name) might also be
        produced. Return the path of the pdf-file.
        If no <filepath> is provided, return the contents (bytes) of the
        pdf-file.
        """
        pdata = self.pupils[pid]
        klass = pdata['CLASS']
        template = Template(cover_template(klass))
        gmap0 = self.base_data(klass, date)
        gmap = self.pupil_data(pdata)
        gmap.update(gmap0)
        return template.make1pdf(gmap, file_path = filepath)
#
    def base_data(self, klass, date):
        schoolyear = self.pupils.schoolyear
        return {  ## data shared by all pupils in the group
            'A': '',    # 'Tage versäumt'
            'L': '',    # 'mal verspätet'
            'N': '',    # 'Blätter'
            'KK': 'Kleinklassenzweig\n' if klass[-1] == 'K' else '',
            'ISSUE_D': Dates.print_date(date),  # 'Ausgabedatum'
            'CL': print_class(klass),
            'SYEAR': print_schoolyear(schoolyear)
        }
#
    def pupil_data(self, pdata):
        gmap = {}
        # Get pupil data
        for k in pdata.keys():
            v = pdata[k]
            if v:
                if k.endswith('_D'):
                    v = Dates.print_date(v)
            else:
                v = ''
            gmap[k] = v
        # Alphabetical name-tag
        gmap['PSORT'] = sortkey(pdata)
        # "tussenvoegsel" separator in last names ...
        gmap['LASTNAME'] = gmap['LASTNAME'].replace('|', ' ')
        return gmap
#
    def filename1(self, pid):
        """Suggest a file-name for the coversheet for the given pupil.
        """
        pdata = self.pupils[pid]
        return COVER_NAME.format(klass = '%s-%s' % (pdata['CLASS'],
                sortkey(pdata)))


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
