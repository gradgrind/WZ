"""
text/check_list.py

Last updated:  2022-03-24

For text reports:
    Build a check-list for the teachers: teacher -> class -> report subjects
    Build a check-list for the classes: class -> report subjects -> teachers


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

_NO_REPORTS = " *** {tname}: keine Zeugnisse"
_CLASS_SUBJECTS = "Klasse {klass}: {subject}"
_TEACHER = "Zeugnisfächer für „{tname}“"
_UNKNOWN_TID = "unbekanntes Lehrer-Kürzel: {tid}"
_CLASS_REPORTS = "Zeugnisfächer in Klasse {klass}"
_SUPPRESSED = "Lehrkraft ausgeschlossen: {tname}"

##############################################################

import sys, os
#from typing import Dict, List, Tuple, Optional, Set

if __name__ == "__main__":
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

#    start.setup(os.path.join(basedir, "TESTDATA"))
    start.setup(os.path.join(basedir, "DATA"))

### +++++

from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm

from core.courses import Subjects
from core.teachers import Teachers
from local.local_text import text_report_class

### -----


def teacher_class_subjects(block_tids=None):
    """For each teacher, collect the subjects for text reports (s)he
    gives in each class.
    If <block_tids> is supplied, it should be a set of teacher-ids which
    will be "blocked", i.e. not appear in the output.
    Build a list of "pages", one for each teacher, with a list of his/her
    classes and subjects.
    """
    if block_tids is None:
        block_tids = set()
    tmap = {}
    subjects = Subjects()
    for klass in subjects.classes():
        if not text_report_class(klass):
            continue
        sgmap = subjects.report_sgmap(klass, grades=False)
        for sid, gmap in sgmap.items():
            for sdata in gmap.values():
                for tid in sdata["TIDS"].split():
                    try:
                        kmap = tmap[tid]
                    except KeyError:
                        tmap[tid] = {klass: {sid}}
                    else:
                        try:
                            kmap[klass].add(sid)
                        except KeyError:
                            kmap[klass] = {sid}
    # Now build the output list
    tset = set(tmap)
    teachers = Teachers()
    tlist = []
    for tid in teachers.list_teachers():
        tname = teachers.name(tid)
        try:
            tset.remove(tid)
        except KeyError:
            if tid not in block_tids:
                REPORT("INFO", _NO_REPORTS.format(tname=tname))
            continue
        slist = []
        suppress = tid in block_tids
        if suppress:
            REPORT("INFO", _SUPPRESSED.format(tname=tname))
        else:
            tlist.append((_TEACHER.format(tname=tname), slist))
        kmap = tmap[tid]
        for klass, sids in kmap.items():
            for sid in sids:
                text = _CLASS_SUBJECTS.format(klass=klass,
                            subject=subjects.sid2name[sid])
                if suppress:
                    REPORT("OUT", text)
                else:
                    slist.append(text)
    for tid in tset:
        REPORT("WARNING", _UNKNOWN_TID.format(tid=tid))
    return tlist


def class_subjects_teachers(block_tids=None):
    """For each class, collect the text report subjects and the teachers
    who are responsible.
    If <block_tids> is supplied, it should be a set of teacher-ids which
    will be "blocked", i.e. not appear in the output.
    Build a list of "pages", one for each class, with a list of the subjects
    and the associated teachers – as text lines.
    """
    if block_tids is None:
        block_tids = set()
    subjects = Subjects()
    teachers = Teachers()
    clist = []
    for klass in subjects.classes():
        if not text_report_class(klass):
            continue
        sgmap = subjects.report_sgmap(klass, grades=False)
        smap = {}
        for sid, gmap in sgmap.items():
            for sdata in gmap.values():
                for tid in sdata["TIDS"].split():
                    if tid in block_tids:
                        continue
                    try:
                        smap[sid].add(tid)
                    except KeyError:
                        smap[sid] = {tid}
        # Now build the output list
        slist = []
        for sid, tlist in smap.items():
            for tid in tlist:
                slist.append(f"{subjects.sid2name[sid]}: {teachers.name(tid)}")
        clist.append((_CLASS_REPORTS.format(klass=klass), slist))
    return clist


BASE_MARGIN = 20 * mm
class PdfCreator:
    def add_page_number(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman', 12)
        page_number_text = "%d" % (doc.page)
        canvas.drawCentredString(
            18 * mm,
            18 * mm,
            page_number_text
        )
        canvas.restoreState()

    def build_pdf(self, pagelist, title, author):
        pdf_buffer = BytesIO()
        my_doc = SimpleDocTemplate(
            pdf_buffer,
            title=title,
            author=author,
            pagesize=A4,
            topMargin=BASE_MARGIN,
            leftMargin=BASE_MARGIN,
            rightMargin=BASE_MARGIN,
            bottomMargin=BASE_MARGIN
        )
        sample_style_sheet = getSampleStyleSheet()
        body_style = sample_style_sheet['BodyText']
        body_style.fontSize = 14
        body_style.leading = 20
        heading_style = sample_style_sheet['Heading1']
        heading_style.spaceAfter = 24
        #print("\n STYLES:", sample_style_sheet.list())

        flowables = []
        for teacher, subjects in pagelist:
            flowables.append(Paragraph(teacher, heading_style))
            for subject in subjects:
                flowables.append(Paragraph(subject, body_style))
            flowables.append(PageBreak())
        my_doc.build(
            flowables,
            onFirstPage=self.add_page_number,
            onLaterPages=self.add_page_number,
        )
        pdf_value = pdf_buffer.getvalue()
        pdf_buffer.close()
        return pdf_value


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    tlist = teacher_class_subjects({"IV", "ID"})
    pdf = PdfCreator()
    pdfbytes = pdf.build_pdf(tlist, title="Lehrer-Klassen-Fächer",
            author="FWS Bothfeld")
    odir = DATAPATH("REPORTS")
    os.makedirs(odir, exist_ok=True)
    pdffile = os.path.join(odir, "Lehrer-Klassen-Fächer.pdf")
    with open(pdffile, "wb") as fh:
        fh.write(pdfbytes)
        print("\nOUT:", pdffile)

    clist = class_subjects_teachers({"IV", "ID"})
    pdf = PdfCreator()
    pdfbytes = pdf.build_pdf(clist, title="Klassen-Fächer-Lehrer",
            author="FWS Bothfeld")
    #odir = DATAPATH("testing/tmp")
    #os.makedirs(odir, exist_ok=True)
    pdffile = os.path.join(odir, "Klassen-Fächer-Lehrer.pdf")
    with open(pdffile, "wb") as fh:
        fh.write(pdfbytes)
        print("\nOUT:", pdffile)
