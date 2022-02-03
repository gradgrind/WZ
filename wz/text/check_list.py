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

from core.courses import Subjects

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
    teachers = Teachers()
    ### Build html
    document = []
    #???
    for tdata in teachers:
        tid = tdata["TID"]
        tname = tdata["NAME"]
# Should I maybe use a similar approach to pupil names? That is separate
# first name and last name, with a "|" in case of a "tussenvoegsel"?


    #TODO
    for tid, kmap in tmap.items():
        document.append(f"<h3>({tid})</h3>")
        for klass, sids in kmap.items():
            print(" :::", klass, ":", sids)



if __name__ == "__main__":
    tmap = get_teacher_class_subjects()
    for tid, kmap in tmap.items():
        print(f"\n*** {tid} ***")
        for klass, sids in kmap.items():
            print(" :::", klass, ":", sids)


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
