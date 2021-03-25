# -*- coding: utf-8 -*-

"""
template_engine/template_sub.py

Last updated:  2021-03-25

Manage the substitution of "special" fields in an odt template.

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

The special substitution fields in a template start with '[[' and end
with ']]'. Between these delimiters there may be only ASCII-alphanumeric
characters, '_' and '.'.

There is always the danger that editing the templates (in LibreOffice)
can lead to the substitution fields being internally split up by styling
tags. This can generally be "repaired" by marking the edited field,
selecting "clear formatting" in the style selection pop-down (top left
of the window) and then reselecting the desired style. If that doesn't
help, it may be necessary to retype the field.
"""

### Messages:
_MISSING_PDFS = "pdf-Erstellung schlug fehl:\n  von {spath}\n  nach {dpath}"
_MISSING_PDF = "pdf-Erstellung schlug fehl: {fpath}"

### Paths:
_Grades_Single = 'Notenzeugnisse/Einzeln'
_Grades_Term = 'Notenzeugnisse/HJ%s'
_Grades_Abitur = 'Notenzeugnisse/Abitur'


import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

from io import BytesIO
import tempfile

from pikepdf import Pdf, Page

from core.run_extern import run_extern
from template_engine.simpleodt import OdtFields
from local.base_config import LIBREOFFICE


class TemplateError(Exception):
    pass

def merge_pdf(ifile_list, pad2sided = False):
    """Join the pdf-files in the input list <ifile_list> to produce a
    single pdf-file. The output is returned as a <bytes> object.
    The parameter <pad2sided> allows blank pages to be added
    when input files have an odd number of pages – to ensure that
    double-sided printing works properly.
    """
    pdf = Pdf.new()
    for ifile in ifile_list:
        src = Pdf.open(ifile)
        pdf.pages.extend(src.pages)
        if pad2sided and (len(src.pages) & 1):
            page = Page(src.pages[0])
            w = page.trimbox[2]
            h = page.trimbox[3]
            pdf.add_blank_page(page_size = (w, h))
    bstream = BytesIO()
    pdf.save(bstream)
    return bstream.getvalue()


def clean_dir(dpath):
    """Ensure the given folder exists and is empty.
    """
    if os.path.isdir(dpath):
        for f in os.listdir(dpath):
            os.remove(os.path.join(dpath, f))
    else:
        os.makedirs(dpath)


def libre_office(odt_list, pdf_dir):
    """Convert a list of odt-files to pdf-files.
    The input files are provided as a list of absolute paths,
    <pdf_dir> is the absolute path to the output folder.
    """
# Use LibreOffice to convert the odt-files to pdf-files.
# If using the appimage, the paths MUST be absolute, so I use absolute
# paths "on principle".
# I don't know whether the program blocks until the conversion is complete
# (some versions don't), so it might be good to check that all the
# expected files have been generated (with a timeout in case something
# goes wrong?).
# The old problem that libreoffice wouldn't work headless if another
# instance (e.g. desktop) was running seems to be no longer the case,
# at least on linux.
    def extern_out(line):
        REPORT('OUT', line)

    rc, msg = run_extern(LIBREOFFICE, '--headless',
            '--convert-to', 'pdf',
            '--outdir', pdf_dir,
            *odt_list,
            feedback = extern_out
        )

###

def open_odt(filepath):
    rc, msg = run_extern(LIBREOFFICE, filepath)

###

class Template:
    """Manage a template file.
    The method <make_pdf> takes a list of data (field-value mappings)
    for the pupils to be included and produces a pdf-file containing
    the reports for all the pupils.
    Each pupil must require the same template, that set when initializing
    the class instance.
    The method <all_keys> returns a <set> of all field names from the
    template.
    """
    def __init__(self, template_path, full_path = False):
        """<template_path> is the path to the template file.
        If <full_path> is true, the path is absolute;
        if false, the path is relative to the templates folder.
        The '.odt' ending is optional in <template_path> and will
        normally not be passed in.
        """
        self.template_path = (template_path if full_path
                else os.path.join(RESOURCES, 'templates',
                        *template_path.split('/')))
        if not self.template_path.endswith('.odt'):
            self.template_path += '.odt'
#
    def fields(self):
        """Return the fields as a list of pairs:
            [(tag, style or <None>), ...]
        If the tag is the only entry in a paragraph in the template file,
        the paragraph style should be returned as the second value. This
        indicates that a multi-line text may be substituted here.
        """
        return OdtFields.listUserFields(self.template_path)
#
    def all_keys(self):
        return {k for k,s in OdtFields.listUserFields(self.template_path)}
#
    def make_pdf(self, data_list, dir_name, working_dir = None,
            double_sided = False):
        """From the supplied list of data mappings produce a pdf
        containing the concatenated individual reports.
        <dir_name> is the name of the folder containing all the output
        files. The pdf-file has the same name as this folder (but ending
        '.pdf').
        The resulting folder is built within <working_dir>, which will
        normally be a path within the data area for the school-year being
        processed. If it is not supplied, a temporary directory is created,
        which is removed automatically when the function completes.
        Note that the return value varies according to whether <working_dir>
        is provided:
            With <working_dir>: path to resulting pdf-file
            No <working_dir>: pdf-bytes
        """
        if working_dir:
            wdir = working_dir
            if not os.path.isdir(wdir):
                os.makedirs(wdir)
        else:
            wdirTD = tempfile.TemporaryDirectory()
            wdir = wdirTD.name
        odt_dir = os.path.join(wdir, dir_name)
        clean_dir(odt_dir)
        odt_list = []
        for datamap in data_list:
            _outfile = os.path.join(odt_dir, datamap['PSORT'] + '.odt')
            odtBytes, used, notsub = OdtFields.fillUserFields(
                    self.template_path, datamap)
#TODO: Do something with <used> and <notsub>?
            # Save the <bytes>
            with open(_outfile, 'bw') as fout:
                fout.write(odtBytes)
            odt_list.append(_outfile)

        pdf_dir = os.path.join(wdir, 'pdf')
        clean_dir(pdf_dir)

        libre_office(odt_list, pdf_dir)

        pdfs = os.listdir(pdf_dir)
        if len(pdfs) != len(odt_list):
            raise TemplateError(_MISSING_PDFS.format(spath = odt_dir,
                    dpath = pdf_dir))
# Maybe there's output from libreoffice somewhere?

        # Concatenate the pdf-files – possibly padding with empty pages –
        # to build the final result.
        # Get pad2sided from the template data (single-sided documents
        # should not be padded!).
        pdf_bytes = merge_pdf([os.path.join(pdf_dir, pdf)
                        for pdf in sorted(pdfs)],
                pad2sided = double_sided)
        # If a working folder is provided, store the result in it
        pdf_file = dir_name + '.pdf'
        if working_dir:
            pdf_path = os.path.join(wdir, pdf_file)
            with open(pdf_path, 'wb') as fout:
                    fout.write(pdf_bytes)
            clean_dir(pdf_dir)
            return pdf_path
        else:
            return pdf_bytes
#
    def make1pdf(self, datamap, show_only = False, file_path = None):
        """From the supplied data mapping produce a pdf of the
        corresponding report.
        1) <show_only> is false (default).
           The behaviour depends on whether <file_path> is supplied.
            (a) If <file_path> is empty, the resulting files are placed
                in a temporary folder, which is deleted on return. The
                pdf-file is returned as <bytes>.
            (b) <file_path> is the full path to the resulting pdf-file.
                Intermediate folders will be created, if necessary.
                The '.pdf' ending need not be supplied, it will be added
                automatically. Also the '.odt' file is produced (using
                the same file path, but with appropriate file suffix).
        2) <show_only> is true.
           In this case, <file_path> should be empty.
           The resulting file is shown in a viewer, at present only the
           odt-file is generated and shown in LibreOffice. The file is
           not saved anywhere (but could be within LibreOffice).
        """
        if file_path:
            if show_only:
                raise Bug("make1pdf: If <show_only> is true, no"
                        " <file_path> should be given")
            if file_path.endswith('.pdf'):
                # Remove pdf ending
                fpath = file_path.rsplit('.', 1)[0]
            else:
                fpath = file_path
            wdir = os.path.dirname(fpath)
            if not os.path.isdir(wdir):
                os.makedirs(wdir)
        else:
            # This can be to return the file-bytes, or for "show_only".
            wdirTD = tempfile.TemporaryDirectory()
            fpath = os.path.join(wdirTD.name, '_TMP_')
        _outfile = fpath + '.odt'
        odtBytes, used, notsub = OdtFields.fillUserFields(
                self.template_path, datamap)
#TODO: Do something with <used> and <notsub>?
        # Save the <bytes>
        with open(_outfile, 'bw') as fout:
            fout.write(odtBytes)
        if show_only:
            # Open in external viewer
            open_odt(_outfile)
            return None
        libre_office([_outfile], os.path.dirname(_outfile))
        pdf_file = fpath + '.pdf'
        if not os.path.isfile(pdf_file):
            raise TemplateError(_MISSING_PDF.format(fpath = pdf_file))
# Maybe there's output from libreoffice somewhere?
        if file_path:
            return pdf_file
        else:
            with open(pdf_file, 'rb') as fin:
                return fin.read()
#
    def make_doc(self, datamap):
        """From the supplied data mapping produce a text document (odt)
        of the corresponding report, returning the file content as <bytes>.
        """
        odtBytes, used, notsub = OdtFields.fillUserFields(
                self.template_path, datamap)
#TODO: Do something with <used> and <notsub>?
        return odtBytes


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    from core.base import init
    init()

    sdict0 = {
        'SCHOOL': 'Freie Michaelschule',
        'SCHOOLBIG': 'FREIE MICHAELSCHULE',
        'CLASS': '11',              # ?
        'CYEAR': '11',              # ?
        'schoolyear': '2020',
        'SCHOOLYEAR': '2019 – 2020',
        'ZEUGNIS': 'ZEUGNIS',
        'Zeugnis': 'Zeugnis',
        'LEVEL': 'Maßstab Gymnasium',   # Sek I, not Abschluss
        'issue_d': '2020-07-15',    # for file names ...
        'ISSUE_D': '15.07.2020',    # always
        'GRADES_D': '06.07.2020',   # Versetzung only (Zeugnis 11.Gym, 12.Gym)
        'COMMENT': '',
        'NOCOMMENT': '––––––––––',
        'GS': '',                   # Abgang only
        'GSVERMERK': '',            # Abgang SekI only

# Pupil data
        'POB': 'Hannover',
        'DOB_D': '12.02.2002',
        'ENTRY_D': '01.08.2009',
        'FIRSTNAMES': 'Elena Susanne',
        'LASTNAME': 'Blender',
        'PSORT': 'Blender_Elena',
        'EXIT_D': '15.07.2020',     # Abschluss / Abgang only

        'S.V.01': 'Deutsch', 'G.V.01': 'sehr gut',
        'S.V.02': 'Englisch', 'G.V.02': 'gut',
        'S.V.03': 'Französisch', 'G.V.03': 'befriedigend',
        'S.V.04': 'Kunst', 'G.V.04': 'gut',
        'S.V.05': 'Musik', 'G.V.05': 'gut',
        'S.V.06': 'Geschichte', 'G.V.06': 'gut',
        'S.V.07': 'Sozialkunde', 'G.V.07': 'befriedigend',
        'S.V.08': 'Religion', 'G.V.08': 'gut',
        'S.V.09': 'Mathematik', 'G.V.09': 'befriedigend',
        'S.V.10': 'Biologie', 'G.V.10': 'sehr gut',
        'S.V.11': 'Chemie', 'G.V.11': 'gut',
        'S.V.12': 'Physik', 'G.V.12': 'mangelhaft',
        'S.V.13': 'Sport', 'G.V.13': 'gut',
        'S.V.14': '––––––––––', 'G.V.14': '––––––––––',
        'S.V.15': '––––––––––', 'G.V.15': '––––––––––',
        'S.V.16': '––––––––––', 'G.V.16': '––––––––––',

        'S.K.01': 'Eurythmie', 'G.K.01': 'sehr gut',
        'S.K.02': 'Buchbinden', 'G.K.02': 'gut',
        'S.K.03': 'Kunstgeschichte', 'G.K.03': '––––––',
        'S.K.04': '––––––––––', 'G.K.04': '––––––––––',
        'S.K.05': '––––––––––', 'G.K.05': '––––––––––',
        'S.K.06': '––––––––––', 'G.K.06': '––––––––––',
        'S.K.07': '––––––––––', 'G.K.07': '––––––––––',
        'S.K.08': '––––––––––', 'G.K.08': '––––––––––',
    }

#    t = Template('Noten/SekI')
#    t = Template('Noten/Fachhochschulreife')
    t = Template('Noten/SekII-13-Abgang')
    t.FILES_PATH = 'GRADE_REPORTS'
    print("\nKeys:", sorted(t.all_keys()))

#    t.make1pdf(sdict0, show_only = True)

    quit(0)

    wdir = os.path.join(DATA, 'testing', 'tmp')
    file_name = '%s_%s' % (sdict0['PSORT'], sdict0['issue_d'])
    fpath = t.make_pdf1(sdict0, file_name, wdir)
#    pdf_bytes = t.make_pdf1(sdict0, file_name)
#    fpath = os.path.join(wdir, file_name) + '.pdf'
#    with open(fpath, 'wb') as fout:
#        fout.write(pdf_bytes)

    print("\nGenerated", fpath)

    sdict1 = sdict0.copy()
    sdict1['PSORT'] = 'Blender_Eleni'
    sdict1['FIRSTNAMES'] = 'Eleni Marie'
    dir_name = '11_2'
    print("\nGenerated", t.make_pdf([sdict0, sdict1], dir_name, wdir))
