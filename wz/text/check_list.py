"""
template_engine/template_sub.py

Last updated:  2022-02-02

Build a check-list for the teachers: teacher -> class -> report subjects


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

# So far just notes ...

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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm

from core.courses import Subjects
from core.teachers import Teachers

### -----

def get_teacher_class_subjects():
    """For each teacher, collect the subjects (s)he gives in each class.
    """
    subjects = Subjects()
#    print("SUBJECTS:", _subjects.sid2name)

#    print("\nINITIAL CLASSES:", _subjects.classes())

    tmap = {}
    for klass in subjects.classes():
        if klass >= "13":
            continue
        sgmap = subjects.report_sgmap(klass, grades=False)
        for sid, gmap in sgmap.items():
            for sdata in gmap.values():
                #print(f"Class {klass}, {subjects.sid2name[sid]}: {sdata['TIDS']}")
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
    return tmap


def teacher_class_subjects():
    """Build a document with a page for each teacher, listing classes
    and subjects for the text reports.
    """
    tmap = get_teacher_class_subjects()
    tset = set(tmap)
    teachers = Teachers()
    subjects = Subjects()
    tlist = []
    for tid in teachers.list_teachers():
        tname = teachers.name(tid)
        try:
            tset.remove(tid)
        except KeyError:
            print(f" *** {tname}: keine Zeugnisse")
            continue
        kmap = tmap[tid]
        slist = []
        for klass, sids in kmap.items():
            for sid in sids:
                slist.append(f"Klasse {klass}: {subjects.sid2name[sid]}")
        tlist.append((f"Zeugnisfächer für {tname}", slist))
    for tid in tset:
        print(f"!!! unbekanntes Lehrer-Kürzel: {tid}")
    return tlist


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

    def build_pdf(self, pagelist):
        pdf_buffer = BytesIO()
        my_doc = SimpleDocTemplate(
            pdf_buffer,
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
        #print("\n STYLES:", sample_style_sheet.list())

        flowables = []
        for teacher, subjects in pagelist:
            flowables.append(Paragraph(teacher, heading_style))
            flowables.append(Spacer(1, 24))
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



if __name__ == "__main__":
    tmap = get_teacher_class_subjects()
    for tid, kmap in tmap.items():
        print(f"\n*** {tid} ***")
        for klass, sids in kmap.items():
            print(" :::", klass, ":", sids)

    tlist = teacher_class_subjects()
    for t, slist in tlist:
        print("\n", t)
        for s in slist:
            print(s)

    pdf = PdfCreator()
    pdfbytes = pdf.build_pdf(tlist)

    odir = DATAPATH("testing/tmp")
    os.makedirs(odir, exist_ok=True)
    pdffile = os.path.join(odir, "pdf_test.pdf")
    with open(pdffile, "wb") as fh:
        fh.write(pdfbytes)
        print("\nOUT:", pdffile)



"""
Print Document (QTextDocument) to pdf
=====================================


int main(int argc, char *argv[]) {

   QApplication app(argc, argv);

   QString fileName = QFileDialog::getSaveFileName((QWidget* )0, "Export PDF", QString(), "*.pdf");
   if (QFileInfo(fileName).suffix().isEmpty()) { fileName.append(".pdf"); }

   QPrinter printer(QPrinter::PrinterResolution);
   printer.setOutputFormat(QPrinter::PdfFormat);
   printer.setPaperSize(QPrinter::A4);
   printer.setOutputFileName(fileName);

   QTextDocument doc;

doc.setHtml("
Hello, World!
\n

Lorem ipsum dolor sit amet, consectitur adipisci elit.
");

   doc.setPageSize(printer.pageRect().size()); // This is necessary if you want to hide the page number
   doc.print(&printer);

}
"""
