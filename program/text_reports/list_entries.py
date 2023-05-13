"""
text_reports/list_entries.py

Last updated:  2023-04-29

Present list of reports to be written for teachers and classes.

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

if __name__ == "__main__":
    # Enable package import if running as module
    import sys, os

    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    # start.setup(os.path.join(basedir, "TESTDATA"))
    start.setup(os.path.join(basedir, "DATA-2023"))

#T = TRANSLATIONS("text_reports.list_entries")

### +++++

from tables.pdf_table import PdfCreator, Paragraph, getSampleStyleSheet
from core.basic_data import (
    get_classes,
    get_teachers,
    get_subjects,
)
from core.report_courses import get_class_subjects

### -----


def collect_text_report_data() -> tuple[dict,dict]:
    """Gather the data for class and teacher report lists from the
    database.
    Return a mapping for each.
    """
    classes = get_classes()
    subjects = get_subjects()
    teachers = get_teachers()
    teacher_map = {}
    class_map = {}
    for cid, _ in classes.get_class_list():
        cmap = {}
        for rsdata in get_class_subjects(cid):
            #print("  ---", rsdata)
            s = rsdata.text_report_subject or subjects.map(rsdata.sid)
            t = rsdata.text_report_authors or teachers.name(rsdata.tid)
            if rsdata.report:
                # handle entries for class_map
                try:
                    cmap[s].add(t)
                except KeyError:
                    cmap[s] = {t}

                # handle entries for teacher_map
                try:
                    tdata = teacher_map[rsdata.tid]
                except KeyError:
                    tcdata = {}
                    teacher_map[rsdata.tid] = (tdata := {cid: tcdata})
                else:
                    try:
                        tcdata = tdata[cid]
                    except KeyError:
                        tdata[cid] = (tcdata := {})
                tcdata[s] = rsdata.text_report_authors

        if cmap:
            class_map[cid] = cmap
    return class_map, teacher_map


def class_list(class_map):
    """Print the report data for the classes to standard output."""
    classes = get_classes()
    for cid, cname in classes.get_class_list():
        try:
            cdata = class_map[cid]
        except KeyError:
            continue
        print("\n ******************", cname)
        for s in sorted(cdata):
            for t in sorted(cdata[s]):
                print(f"  +++ {s} : {t}")


def pdf_classes(class_map):
    """Return a pdf table (as byte array) with the report data for the
    classes.
    """
    classes = get_classes()
    classes_list = []
    for cid, cname in classes.get_class_list():
        try:
            cdata = class_map[cid]
        except KeyError:
            continue
        clist = []
        for s in sorted(cdata):
            for t in sorted(cdata[s]):
                clist.append(("", s, "", t))
        clist.append("")
        classes_list.append((cname, [('', clist)]))
    pdf = PdfCreator()
    headers = ["", "Fach", "", "Lehrkraft"]
    colwidths = (20, 70, 10, 70)
    return pdf.build_pdf(
        classes_list,
        title="Zeugnisliste_Klassen",
        author=CONFIG["SCHOOL_NAME"],
        headers=headers,
        colwidths=colwidths,
        #        do_landscape=True
    )


def teacher_list(teacher_map):
    """Print the report data for the classes to standard output."""
    classes = get_classes()
    teachers = get_teachers()
    for tid in teachers.list_teachers():
        try:
            tdata = teacher_map[tid]
        except KeyError:
            continue
        print("\n ******************", teachers.name(tid))
        for cid, cname in classes.get_class_list():
            try:
                tcdata = tdata[cid]
            except KeyError:
                continue
            print("  +++", cname)

            for s in sorted(tcdata):
                tx = tcdata[s]
                if tx:
                    print("      ---", s, "|", tx)
                else:
                    print("      ---", s)


def pdf_teachers(teacher_map):
    """Return a pdf table (as byte array) with the report data for the
    teachers.
    """
    classes = get_classes()
    teachers = get_teachers()
    teachers_list = []

#???
    styl = getSampleStyleSheet()["Normal"]
#    styl.wordWrap = 'CJK'


    for tid in teachers.list_teachers():
        try:
            tdata = teacher_map[tid]
        except KeyError:
            continue
        tlist = []
        for cid, cname in classes.get_class_list():
            try:
                tcdata = tdata[cid]
            except KeyError:
                continue
            for s in sorted(tcdata):
                tx = tcdata[s]
                tlist.append((cname, s, tx))
        tlist.append("")
        teachers_list.append((teachers.name(tid), [('', tlist)]))
    pdf = PdfCreator()
    headers = ["Klasse", "Fach", "(abweichende Unterschrift)"]
    colwidths = (50, 50, 60)
    return pdf.build_pdf(
        teachers_list,
        title="Zeugnisliste_Lehrer",
        author=CONFIG["SCHOOL_NAME"],
        headers=headers,
        colwidths=colwidths,
        #        do_landscape=True
    )


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from core.db_access import open_database
    from ui.ui_base import saveDialog

    open_database()

    def action():
        cm, tm = collect_text_report_data()

        class_list(cm)

        pdfbytes = pdf_classes(cm)
        filepath = saveDialog("pdf-Datei (*.pdf)", "Zeugnisliste_Klassen")
        if filepath and os.path.isabs(filepath):
            if not filepath.endswith(".pdf"):
                filepath += ".pdf"
            with open(filepath, "wb") as fh:
                fh.write(pdfbytes)
            print("  --->", filepath)

        teacher_list(tm)
        pdfbytes = pdf_teachers(tm)
        filepath = saveDialog("pdf-Datei (*.pdf)", "Zeugnisliste_Lehrer")
        if filepath and os.path.isabs(filepath):
            if not filepath.endswith(".pdf"):
                filepath += ".pdf"
            with open(filepath, "wb") as fh:
                fh.write(pdfbytes)
            print("  --->", filepath)



    PROCESS(
        action, "Print report lists for classes and teachers"
    )
