# -*- coding: utf-8 -*-

"""
template_engine/coversheet.py

Last updated:  2023-04-29

Build the outer sheets (cover sheets) for the text reports.
User fields in template files are replaced by the report information.

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


import sys, os
if __name__ == "__main__":
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))

#T = TRANSLATIONS("template_engine.coversheet")

from zipfile import ZipFile, ZIP_DEFLATED

from core.base import Dates, wipe_folder_contents
from core.pupils import pupils_in_group, pupil_data
from core.basic_data import get_classes
from template_engine.template_sub import Template, merge_pdf


##### local stuff #####
COVER_DIR = "TEXT/MANTEL"
COVER_CLASS = f"{COVER_DIR}/Mantel_{{klass}}"
WHOLE_SCHOOL = "TEXT/Mantel_alle_Klassen.zip"

def filter_class(klass):
    return klass >= "13" or klass < "01"

def cover_template(klass):
    tp = 'Text/Mantel'
    if klass >= '12':
        tp += '-Abgang'
#    if klass[-1] == 'K':       # currently using the "normal" template
#        tp += '-Kleinklasse'
    return tp

def print_class(klass):
    """Return the class name as used in text reports.
    """
    return klass.lstrip('0').rstrip('G')

def print_schoolyear(schoolyear):
    """Convert a school-year (<str>) to the format used for output
    """
    return '%d – %s' % (int(schoolyear) - 1, schoolyear)
##### end local stuff #####


def for_class(klass, date):
    """Make cover sheets for all pupils of the given class.
    Join these to a single pdf.
        <date>: date of issue ('YYYY-MM-DD')
        <klass>: the class id
    Return the path to the resulting pdf-file.
    """
    pdlist = pupils_in_group(klass, date)
    template = Template(cover_template(klass))
    gmap0 = base_data(klass, date)
    gmaplist = []
    for pdata in pdlist:
        gmap = pupil_data_filter(pdata)
        gmap.update(gmap0)
        gmaplist.append(gmap)
    save_dir = DATAPATH(COVER_CLASS.format(klass=klass))
    pdfs = template.make_pdfs(
        gmaplist,
        save_dir,
        show_run_messages=1
    )
    pdf_path_list = [os.path.join(save_dir, pdf) for pdf in pdfs]
    # Join individual reports to a single file
    return join_pdfs(pdf_path_list, save_dir)


def join_pdfs(pdf_path_list, outfile):
    if not outfile.endswith(".pdf"):
        outfile += ".pdf"
    byte_array = merge_pdf(pdf_path_list, pad2sided=1)
    with open(outfile, "bw") as fout:
        fout.write(byte_array)
    return outfile


def base_data(klass, date):
    return {  ## data shared by all pupils in the group
        'A': '',    # 'Tage versäumt'
        'L': '',    # 'mal verspätet'
        'N': '',    # 'Blätter'
        'KK': 'Kleinklassenzweig\n' if klass[-1] == 'K' else '',
        'DATE_ISSUE': Dates.print_date(date, CONFIG["DATEFORMAT"]),
        'CL': print_class(klass),
        'SYEAR': print_schoolyear(SCHOOLYEAR)
    }


def pupil_data_filter(pdata):
    gmap = {}
    for k in pdata.keys():
        v = pdata[k]
        if v:
            if k.startswith('DATE_'):
                v = Dates.print_date(v, CONFIG["DATEFORMAT"])
        else:
            v = ''
        gmap[k] = v
    return gmap


def for_pupil(pid, date):
    """Make a single cover sheet, for the pupil with the given <pid>.
    An intermediate odt-file (with the same name) might also be
    produced. Return the path of the pdf-file.
    """
    pdata = pupil_data(pid)
    klass = pdata['CLASS']
    template = Template(cover_template(klass))
    gmap = pupil_data_filter(pdata)
    gmap.update(base_data(klass, date))
    gmaplist = [gmap]
    save_dir = DATAPATH(COVER_NAME.format(klass=klass))
    pdfs = template.make_pdfs(
        gmaplist,
        save_dir,
        show_run_messages=1
    )
    if pdfs:
        return os.path.join(save_dir, pdfs[0])
    return None


def for_school(date):
    """Produce cover sheets for whole school.
    They are done class-by-class, producing a single pdf for each
    class.
    The class pdfs are then zipped up to a single large archive.
    """
    # Clean out base folder
    wipe_folder_contents(DATAPATH(COVER_DIR))
    # Build class pdfs
    pdf_list = []
    for klass, name in get_classes().get_class_list():
        if filter_class(klass):
            continue
        REPORT("INFO", f"{klass}: {name}")
        pdf_list.append(pdf := for_class(klass, date))
        REPORT("INFO", f" ---> {pdf}")
    # Archive (zip) all class pdfs
    with ZipFile(
        DATAPATH(WHOLE_SCHOOL),
        'w',
        compression=ZIP_DEFLATED
    ) as zip:
       for pdf in pdf_list:
            zip.write(pdf, os.path.basename(pdf))


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    from core.db_access import open_database
    open_database()

    _date = '2023-07-05'

    PROCESS(
        for_school,
        date=_date
    )

    quit(0)

    PROCESS(
        for_class,
        klass="12K",
        date=_date
    )

    PROCESS(
        for_pupil,
        pid="3357",
        date=_date
    )

