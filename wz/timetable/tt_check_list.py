"""
timetable/tt_check_list.py

Last updated:  2022-02-19

For checking timetable entries:
    Build a check-list for the teachers: teacher -> class -> subjects/courses
? TODO:
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
#    start.setup(os.path.join(basedir, "DATA"))
    start.setup(os.path.join(basedir, "NEXT"))

### +++++

from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm

### -----

def teacher_class_subjects(teacher_subjects, block_tids=None):
    """For each teacher, present the subjects/courses together with
    groups, rooms etc.
    If <block_tids> is supplied, it should be a set of teacher-ids which
    will be "blocked", i.e. not appear in the output.
    Build a list of "pages", one for each teacher, with a list of his/her
    classes and subjects.
    """
    if block_tids is None:
        block_tids = set()
    tlist = []
    for tid, tname, clist in teacher_subjects:
        if tid in block_tids:
            REPORT("INFO", _SUPPRESSED.format(tname=tname))
            continue
        else:
            tlist.append((f"{tname} ({tid})", clist))

    pdf = PdfCreator()
    return pdf.build_pdf(tlist, title="Lehrer-Klassen-Fächer",
            author="FWS Bothfeld")


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
        class_style = sample_style_sheet['Heading2']
        class_style.spaceBefore = 25
        #print("\n STYLES:", sample_style_sheet.list())

        flowables = []
        for teacher, clist in pagelist:
            flowables.append(Paragraph(teacher, heading_style))
            for klass, slist in clist:
                flowables.append(Paragraph(klass, class_style))
                for subject in slist:
                    if subject:
                        flowables.append(Paragraph(subject, body_style))
                    else:
                        flowables.append(Spacer(1, 4 * mm))
            flowables.append(PageBreak())
        my_doc.build(
            flowables,
            onFirstPage=self.add_page_number,
            onLaterPages=self.add_page_number,
        )
        pdf_value = pdf_buffer.getvalue()
        pdf_buffer.close()
        return pdf_value
