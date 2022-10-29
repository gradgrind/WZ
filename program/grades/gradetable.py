"""
grades/gradetable.py

Last updated:  2022-10-29

Access grade data, read and build grade tables.

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

#TODO ...

# Bear in mind that a pupil's groups can change during a school-year.
# Thus grade tables should probably be handled a bit separately from
# the normal database entries: retrospective changes could happen after,
# say, a group has been changed. Such volatile data should thus be
# stored along with the grade table. Non-volatile data can be taken from
# the normal database tables.

# How many grade tables should there be? Everything could be stored in
# in one table if there is an appropriate identifier column. Otherwise
# there could be a table per issue, class, whatever. If using a single
# table, there would need to be filters on at least issue and class,
# probably also group (or perhaps rather "stream"), at least for the
# higher classes.

###############################################################

import sys, os

if __name__ == "__main__":
    import locale

    print("LOCALE:", locale.setlocale(locale.LC_ALL, ""))
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

#    start.setup(os.path.join(basedir, "TESTDATA"))
#    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))

T = TRANSLATIONS("grades.gradetable")

### +++++

#? ...
from typing import Optional
import datetime

from core.base import class_group_split, Dates
from core.db_access import db_read_table, read_pairs
from core.basic_data import SHARED_DATA
from core.pupils import pupil_name, pupil_data
from core.report_courses import get_pupil_grade_matrix
from tables.spreadsheet import read_DataTable
from tables.matrix import KlassMatrix

class GradeTableError(Exception):
    pass

NO_GRADE = '/'

### -----

"""Grade tables.
pid, "term", grades (json?), extra fields:
1) composites?
2) calcs?
3) date of issue, other date(s), report type, qualification, etc. ...
The composites and calcs are not strictly necessary as they can always
be regenerated, however it might be practical to have them directly
available for the report generation.
At least some of the other fields will depend on class, term, report
type, etc., so perhaps there should be one field "extras"? (json?)
Or the fields are included in "grades"?
Separate field for "Bemerkungen"? "report-type"? ...

I could use the spreadsheet tables for input purposes. The question
would then be what to do when there is a conflict. The conflict could
be shown with an accept/reject dialog. Or all values could be
overwritten, or ...

Some fields will normally apply to a whole group (e.g. date of issue or
date of "Notenkonferenz"), but may – in special cases – deviate for
individual pupils. This is a bit of a tricky one if the grade data in
the database is purely pupil-term-based.
One possibility might be to have the group value in a config file (or
special config-table in the db). It would act as default if no value
is set in the pupil record. In that case the value in a spreadsheet
table would be irrelevant (only for information), maybe even superfluous.
"""

def get_grade_config():
    try:
        return SHARED_DATA["GRADE_CONFIG"]
    except KeyError:
        pass
    data = MINION(DATAPATH("CONFIG/GRADE_CONFIG"))
    SHARED_DATA["GRADE_CONFIG"] = data
    return data


def get_group_data(occasion: str, class_group: str):
    """Get information pertaining to the grade table for the given
    group and "occasion".
    """
    grade_info = get_grade_config()
    oinfo = grade_info["OCCASIONS"]
    for o, odata in oinfo:
        if o == occasion:
            break
    else:
        raise Bug(f'Invalid grade "occasion": {occasion}')
    try:
        return odata[class_group]
    except KeyError:
        raise GradeTableError(
            T["INVALID_OCCASION_GROUP"].format(
                occasion=o, group=class_group
            )
        )


#TODO: Construct whatever is needed for a full grade table.
# The parameters should come from the class/group in the record (if there
# is one). However, as the search is done based on a class/group, it
# must be the same one as in the search criterion. The pupils in this
# class/group could be different from the current members.

# Use:
# REPORT_TYPE
# ?LEVEL: [Maßstab [Gym RS HS]]
# ?Q12:   [Versetzung [X ""]]
# COMPOSITE: [Ku]
# AVERAGE: [(D  "Φ alle Fächer") (Ddem  "Φ De-En-Ma")]
# MULTIPLE: ["Klausur 1" "Klausur 2" "Klausur 3"]
#
# Consider also:
# __INDIVIDUAL__: True

# Some of these entries are "expected", with built-in handlers.
# Those starting with '?' are choices (from the given value list), but
# they are not "expected".
# COMPOSITE refers to a subject in the COURSES table (without teachers
# and lessons). It generates an average of the grades in those subjects
# (sids) which include the sid in their REPORT field. These "component"
# subjects will need special handling when building the reports (to
# ensure that they don't get "counted" twice).

# I could have a collection of handler functions/methods for the built-in
# key words, others could be handled by plug-ins? Those starting with '?'
# would have a special handler. The question is, though, how much of that
# needs to be handled here, and how much in the editor. Maybe the
# primary handling of the details should be in the editor. It might be
# enough here to simply read the fields from the database.

# When making a table/editor for an occasion+group I would need
#  - the identifier stuff: pupil-id, pupil-name, pupil-groups(?);
#  - the subjects (separating out composites and components?);
#  - (possibly the components);
#  - (possibly the composites);
#  - averages, etc.
#  - evaluation fields, report type, ...
# Each column would have an appropriate "item delegate", for example
# a grade choice, or read-only for calculated cells.
# Setting a background colour on the columns might help.

# Note that special text-report fields (subject, signatories) and special
# grade-report fields (composite, calculated fields) are set in the
# course editor. The course editor is independent of particular report
# "occasions", so these fields must also be independently specified for
# a class/group. If groups are involved it might make sense to first
# look for class specifications, which can then be extended (or even
# overriden?) by group specifications.

'''
# see also the example in test-itemdelegates.py
class ComboDelegate(QItemDelegate):
    """
    A delegate to add QComboBox in every cell of the given column
    """

    def __init__(self, parent):
        super(ComboDelegate, self).__init__(parent)
        self.parent = parent

    def createEditor(self, parent, option, index):
        combobox = QComboBox(parent)
        version_list = []
        for item in index.data():
            if item not in version_list:
                version_list.append(item)

        combobox.addItems(version_list)
        combobox.currentTextChanged.connect(lambda value: self.currentIndexChanged(index, value))
        return combobox

    def setEditorData(self, editor, index):
        value = index.data()
        if value:
            maxval = len(value)
            editor.setCurrentIndex(maxval - 1)
'''

#TODO
def grade_table_info(occasion: str, class_group: str, instance: str = ""):
    ### Get subject, pupil and group report-information
    subjects, pupils = get_pupil_grade_matrix(
        class_group, text_reports=False
    )
    group_data = get_group_data(occasion, class_group)
    # print("??????", group_data)
    klass, group = class_group_split(class_group)
    try:
        __extra_info = get_grade_config()["GRADE_FIELDS_EXTRA"][klass]
    except KeyError:
        composites = {}
        composite_references = {}
        averages = {}
    else:
        try:
            __clist = __extra_info["COMPOSITE"]
        except KeyError:
            __clist = []
        try:
            __alist = __extra_info["CALCULATE"]
        except KeyError:
            __alist = []
        try:
            __ginfo = __extra_info[group]
        except KeyError:
            pass
        else:
            try:
                __clist += __ginfo["COMPOSITE"]
            except KeyError:
                pass
            try:
                __alist += __ginfo["CALCULATE"]
            except KeyError:
                pass

        composites = {}
        composite_references = {}
        for k, fn in __clist:
            composites[k] = fn
            composite_references[k] = 0

#        composites = {k: fn for k, fn in __clist}
        averages = {k: (n, fn) for k, n, fn in __alist}
    header_list = []
    for sdata in sorted(subjects.values()):
        # print("§§§§§§§§", sdata)
        # Subjects counting towards composites need some sort of reference
        # to their target – so that a change can trigger a recalculation.
        sid = sdata[1]
        sname = sdata[2]
        zgroup = sdata[3]
        composite = sdata[4]
        # sdata[5] is the text-report custom settings, which are
        # not relevant  here.
        value = {"SID": sid, "NAME": sname, "GROUP":zgroup}
        try:
            value["FUNCTION"] = composites.pop(sid)
            value["TYPE"] = "COMPOSITE"
        except KeyError:
            value["TYPE"] = "SUBJECT"
        if composite:
            if composite == "---":
                value["TARGET"] = ""
            else:
                try:
                    composite_references[composite] += 1
                    value["TARGET"] = composite
                except KeyError:
                    # This composite is not configured, ignore it.
                    pass
        header_list.append(value)
    # Check usage and declaration of composites
    for c, n in composite_references.items():
        if n == 0:
            # No references, which suggests the composite should not be
            # defined ...
            if c not in composites:
                REPORT(
                    "ERROR",
                    T["COMPOSITE_NO_REFERENCE"].format(
                        group=class_group,
                        composite=c
                    )
                )
        else:
            # Referenced, so it must be defined ...
            if c in composites:
                REPORT(
                    "ERROR",
                    T["COMPOSITE_UNDECLARED"].format(
                        group=class_group,
                        composite=c
                    )
                )
    result = {"SUBJECTS": header_list}
    # Now all the extra fields
#TODO: Should they be added to the subjects?
    extra_list = []
    result["EXTRAS"] = extra_list
    for k, v in averages.items():
        extra_list.append(
            {
                "SID": k,
                "NAME": v[0],
                "TYPE": "CALCULATE",
                "FUNCTION": v[1]
            }
        )
    for k, v in group_data.items():
        if k[0] == '?':
            extra_list.append(
                {
                    "SID": k[1:],
                    "NAME": v[0],
                    "TYPE": "CHOICE",
                    "VALUES": v[1]
                }
            )
    report_types = group_data.get("REPORT_TYPES")
    if report_types:
        extra_list.append(
            {
                "SID": "REPORT_TYPE",
                "NAME": T["REPORT_TYPE"],
                "TYPE": "CHOICE_MAP",
                "VALUES": report_types
            }
        )
    extra_list.append(
        {
            "SID": "REMARKS",
            "NAME": T["REMARKS"],
            "TYPE": "TEXT"
        }
    )

    result["GRADES"] = group_data["GRADES"]
    result["GRADE_ENTRY"] = group_data["GRADE_ENTRY"]

    pupil_map = {}
    result["PUPILS"] = pupil_map
    for pdata, p_atoms, p_grade_tids in pupils:
        pupil_map[pdata["PID"]] = (pdata, p_grade_tids)

    return result


def read_stored_grades(occasion: str, class_group: str, instance: str = ""):
    fields = [
        # "OCCASION",
        # "CLASS_GROUP",
        # "INSTANCE",
        "PID",
        "LEVEL",    # The level might have changed, so this field is relevant
        "GRADE_MAP"
    ]
    flist, rlist = db_read_table(
        "GRADES",
        fields,
        OCCASION=occasion,
        CLASS_GROUP=class_group,
        INSTANCE=instance
    )
    plist = []
    for row in rlist:
        pid = row["PID"]
        pdata = pupil_data(pid) # this mapping is not cached => it is mutable
        # Substitute the pupil fields which could differ in the grade data
        pdata["CLASS"] = class_group_split(class_group)[0]
        pdata["LEVEL"] = row["LEVEL"]
        # Get grade (etc.) info as mapping
        grade_map = read_pairs(row["GRADE_MAP"])
        plist.append((pdata, grade_map))
    return plist

#TODO
    # If there is a result, use the pupils in the list rather than
    # the pupils from <pupils>, in case there have been changes.
    # There should be an option in the GUI to reload the data, which
    # would use the "current" pupil list (in <pupils>), but take
    # any available data about grades from this database list.
    # Additional pupil data needed for the reports would need to come
    # from the "PUPILS" table. For those in <pupils>, it is already
    # available, others must be read individually.

    # It is not impossible that some other information about a pupil
    # changes during a year (not just the groups). The most
    # straightforward approach might be to forbid editing/regeneration
    # of old reports after their date of issue – or at lest to warn
    # strongly against it. A separate possibility to edit old data
    # might be useful. However, consider a possible need to correct
    # old data when a mistake is found only later. To preserve all
    # the old data which might be needed to print a report, it would
    # need to be stored with the grade data.

#        return {
#            "HEADERS": header_list,
#            "PUPILS": pupil_map,
#            "GRADES": grade_map
#        }

def make_grade_table(
    occasion: str,
    class_group: str,
    DATE_ISSUE: str = "",
    DATE_GRADES: str = "",
    grades: Optional[dict[str, dict[str, str]]] = None,
) -> bytes:
    """Build a basic pupil/subject table for grade input using a
    template appropriate for the given group.
    Existing grades can be included in the table by passing an appropriate
    structure as <grades>: {pid -> {sid -> grade}}
    """
    ### Get subject, pupil and group information
    gtinfo = grade_table_info(occasion, class_group)
    subjects = gtinfo["SUBJECTS"]
    pupils = gtinfo["PUPILS"]

    ### Get template file
    template_path = RESOURCEPATH(gtinfo["GRADE_ENTRY"])
    table = KlassMatrix(template_path)

    ### Set title line
    table.setTitle(
        T["TITLE"].format(
            time=datetime.datetime.now().isoformat(sep=" ", timespec="minutes")
        )
    )

    ### Gather general info
    if not DATE_ISSUE:
        DATE_ISSUE = Dates.today()
    if not DATE_GRADES:
        DATE_GRADES = DATE_ISSUE
    info_transl: dict[str, str] = {}
    info_item: dict
    grade_info = get_grade_config()
    for f, t in grade_info["INFO_FIELDS"]:
        info_transl[f] = t
    info: dict[str, str] = {
        info_transl["SCHOOLYEAR"]: SCHOOLYEAR,
        info_transl["CLASS_GROUP"]: class_group,
        info_transl["OCCASION"]: occasion,
        info_transl["DATE_GRADES"]: DATE_GRADES,
        info_transl["DATE_ISSUE"]: DATE_ISSUE,
    }
    table.setInfo(info)

    ### Go through the template columns and check if they are needed:
    rowix: list[int] = table.header_rowindex  # indexes of header rows
    if len(rowix) != 2:
        raise GradeTableError(
            T["TEMPLATE_HEADER_WRONG"].format(path=template_path)
        )
    sidcol: list[tuple[str, int]] = []
    sid: str
    sdata: dict
    for sdata in subjects:
        if sdata["TYPE"] != "SUBJECT":
            continue
        sid = sdata["SID"]
        # Add subject
        col: int = table.nextcol()
        sidcol.append((sid, col))
        table.write(rowix[0], col, sid)
        table.write(rowix[1], col, sdata["NAME"])
    # Enforce minimum number of columns
    while col < 18:
        col = table.nextcol()
        table.write(rowix[0], col, "")
    # Delete excess columns
    table.delEndCols(col + 1)

    ### Add pupils and grades
#    for pdata, p_atoms, p_grade_tids in pupils:
#        pid = pdata["PID"]
    for pid, pinfo in pupils.items():
        pdata, p_grade_tids = pinfo
        pgrades: dict[str, str]
        try:
            pgrades = grades[pid]
        except:
            pgrades = {}
        row = table.nextrow()
        table.write(row, 0, pid)
        table.write(row, 1, pupil_name(pdata))
        table.write(row, 2, pdata["LEVEL"])
        for sid, col in sidcol:
            if p_grade_tids.get(sid):
                if (g := pgrades.get(sid)):
                    table.write(row, col, g)
            else:
                table.write(row, col, NO_GRADE, protect=True)
    # Delete excess rows
    row = table.nextrow()
    table.delEndRows(row)

    ### Save file
    table.protectSheet()
    return table.save_bytes()


def read_grade_table_file(filepath: str) -> tuple[
    dict[str, str], dict[str, dict[str, str]]
]:
    """Read the header info and pupils' grades from the given grade
    table (file).
    <read_DataTable> in the "spreadsheet" module is used as backend, so
    .ods, .xlsx and .tsv formats are possible. The filename may be
    passed without extension – <Spreadsheet> then looks for a file with
    a suitable extension.
    Return mapping for pupil-grades. Include header info as special
    entry.
    """
    grade_config = get_grade_config()
    header_map = {t: f for f, t in grade_config["HEADERS"]}
    info_map = {t: f for f, t in grade_config["INFO_FIELDS"]}
    datatable = read_DataTable(filepath)
    info = {
        (info_map.get(k) or k): v
        for k, v in datatable["__INFO__"].items()
    }
    ### Get the rows as mappings
    # fields = datatable["__FIELDS__"]
    # print("\nFIELDS:", fields)
    gdata: dict[str, dict[str, str]] = {"__INFO__": info}
    group_data = get_group_data(info["OCCASION"], info["CLASS_GROUP"])
    valid_grades = set(group_data["GRADES"])
    for pdata in datatable["__ROWS__"]:
        pinfo = [pdata.pop(h) for h in header_map]
        pid: str = pinfo[0]
        if pid != "$":
            gdata[pid] = pdata
            # Check validity of grades
            for k, v in pdata.items():
                if v and v not in valid_grades:
                    REPORT(
                        "ERROR",
                        T["INVALID_GRADE"].format(
                            filepath=info["__FILEPATH__"],
                            pupil=pinfo[1],
                            sid=k,
                            grade=v
                        )
                    )
                    pdata[k] = ""
    return gdata


def collate_grade_tables(
    files: list[str],
    occasion: str,
    group: str,
) -> dict[str, dict[str, str]]:
    """Use <read_grade_table_file> to collect the grades from a set of grade
    tables – passed as <files>.
    Return the collated grades: {pid: {sid: grade}}.
    Only grades that have actually been given (i.e. no empty grades or
    grades for unchosen or unavailable subject) will be included.
    If a grade for a pupil/subject pair is given in multiple input tables,
    an exception will be raised if the grades are different.
    """
    grades: dict[str, dict[str, str]] = {}
    # For error tracing, retain file containing first definition of a grade.
    fmap: dict[tuple[str, str], str] = {}  # {(pid, sid): filepath}
    for filepath in files:
        table = read_grade_table_file(filepath)
        info = table.pop("__INFO__")
        if info["SCHOOLYEAR"] != SCHOOLYEAR:
            raise GradeTableError(
                T["TABLE_YEAR_MISMATCH"].format(
                    year=SCHOOLYEAR, filepath=info["__FILEPATH__"]
                )
            )
        if info["CLASS_GROUP"] != group:
            raise GradeTableError(
                T["TABLE_CLASS_MISMATCH"].format(
                    group=group, path=info["__FILEPATH__"]
                )
            )
        if info["OCCASION"] != occasion:
            raise GradeTableError(
                T["TABLE_TERM_MISMATCH"].format(
                    term=occasion, path=info["__FILEPATH__"]
                )
            )
        # print("\n$$$", filepath)
        for pid, smap in table.items():
            try:
                smap0 = grades[pid]
            except KeyError:
                smap0 = {}
                grades[pid] = smap0
            for s, g in smap.items():
                if g:
                    if (not g) or g == NO_GRADE:
                        continue
                    g0 = smap0.get(s)
                    if g0:
                        if g0 != g:
                            raise GradeTableError(
                                T["GRADE_CONFLICT"].format(
                                    pid=pid,
                                    sid=s,
                                    path1=fmap[(pid, s)],
                                    path2=filepath,
                                )
                            )
                    else:
                        smap0[s] = g
                        fmap[(pid, s)] = filepath
    return grades


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from core.db_access import open_database
    open_database()

    for __cg in ("13", "11G", "12G.G", "12G.R"):
#    for __cg in ("11G", "12G.G", "12G.R"):
        tbytes = make_grade_table("1. Halbjahr", __cg)
        tpath = DATAPATH(f"testing/tmp/GradeInput-{__cg}.xlsx")
        tdir = os.path.dirname(tpath)
        if not os.path.isdir(tdir):
            os.makedirs(tdir)
        with open(tpath, "wb") as _fh:
            _fh.write(tbytes)
        print(f"\nWROTE GRADE TABLE TO {tpath}\n")

    print("\n *************************************************\n")

    gdata = read_grade_table_file(tpath)
    for pid, pdata in gdata.items():
        print(f"\n --- {pid}:", pdata)

    print("\nCOLLATING ...")
    from glob import glob
    gtable = collate_grade_tables(
        glob(os.path.join(tdir, "test?.xlsx")), "1. Halbjahr", "11G"
    )
    for p, pdata in gtable.items():
        print("\n ***", p, pdata)

    print("\n *************************************************\n")

    gtinfo = grade_table_info("2. Halbjahr", "12G.R")
    print("\n*** SUBJECTS")
    for val in gtinfo["SUBJECTS"]:
        print("    ---", val)
    print("\n*** EXTRA COLUMNS")
    for val in gtinfo["EXTRAS"]:
        print("    ---", val)
    print("\n*** GRADES", gtinfo["GRADES"])
    print("\n*** PUPILS")
    for pid, pinfo in gtinfo["PUPILS"].items():
        pdata, p_grade_tids = pinfo
        print(f'\n +++ {pdata}')
        print(" .........", p_grade_tids)

    print("\n*** STORED GRADES")
    stored_grades = read_stored_grades("2. Halbjahr", "12G.R")
