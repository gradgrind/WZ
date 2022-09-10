"""
grades/gradetable.py

Last updated:  2022-09-10

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


### Messages
_NO_INFO_FOR_GROUP = (
    "Klasse/Gruppe {group}: Notenzeugnisse sind nicht" " vorgesehen"
)
_TEMPLATE_HEADER_WRONG = "Fehler bei den Kopfzeilen der Vorlage:\n {path}"
_MISSING_KEY = "Eintrag fehlt in Konfigurationsdatei: {key}"
_GRADE_MISSING = "Leeres Notenfeld im Fach {sid}, Tabelle:\n  {path}"
_GRADE_CONFLICT = (
    "Widersprüchliche Noten für Schüler {pid} im Fach {sid}"
    "\n  {path1}\n  {path2}"
)
_TABLE_CLASS_MISMATCH = (
    "Falsche Klasse/Gruppe in Notentabelle:\n"
    "  erwartet '{group}' ... Datei:\n    {filepath}"
)
_TABLE_TERM_MISMATCH = (
    "Falscher 'Anlass' in Notentabelle:\n"
    "  erwartet '{term}' ... Datei:\n    {filepath}"
)
_TABLE_YEAR_MISMATCH = (
    "Falsches Schuljahr in Notentabelle:\n"
    "  erwartet '{year}' ... Datei:\n    {filepath}"
)
_BAD_DEPENDER = "Ungültiges Sonderfach-Kürzel: {sid}"
_BAD_WEIGHT = "Gewichtung des Faches ({sid}) muss eine Zahl sein: '{d}'"
_NULL_COMPOSITE = "'$' ist nicht gültig als Fach-Kürzel"
_BAD_COMPOSITE = "Ungültiges Fach-Kürzel: {sid}"
_EMPTY_COMPOSITE = "Sammelfach {sid} hat keine Komponenten"
_COMPOSITE_NOT_ALONE = (
    "Fach-Kürzel {sid}: Sammelfach ({comp}) darf"
    " nicht parallel zu anderen sein"
)
_COMPOSITE_COMPONENT = (
    "Sammelfach ({sid}) darf nicht Komponente eines"
    " anderen Sammelfaches ({comp}) sein"
)

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
from typing import Optional, Any
import datetime, fnmatch

#?
from core.base import class_group_split, Dates
from core.basic_data import get_classes, get_subjects_with_sorting, SHARED_DATA
from core.classes import atomic_maps
from core.pupils import pupils_in_group, pupil_name
from core.report_courses import get_class_subjects, get_pupil_grade_matrix
from tables.spreadsheet import read_DataTable
from tables.matrix import KlassMatrix

#? ...

#from core.base import Dates
#from core.courses import Subjects, NULL, UNCHOSEN
#from tables.spreadsheet import read_DataTable, filter_DataTable
#from local.local_grades import GradeBase, GradeConfigError


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

def get_grade_entry_tables():
    try:
        return SHARED_DATA["GRADE_ENTRY_TABLES"]
    except KeyError:
        pass
    data = MINION(DATAPATH("CONFIG/GRADE_ENTRY_TABLES"))
    group_data = []
    data["GROUP_DATA"] = group_data
    for key in list(data):
        if key.startswith("__"):
            val = data.pop(key)
            group_data.append((val.pop("GROUPS"), val))
    SHARED_DATA["GRADE_ENTRY_TABLES"] = data
    return data


def makeGradeTable(
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
    ### Get subject and pupil information
    subjects, pupils = get_pupil_grade_matrix(class_group, text_reports=False)

    ### Get information pertaining to the grade entry table.
    # Select the template, etc. on the basis of the group and "occasion".
    entry_tables_info = get_grade_entry_tables()
    group_data_count = 0
    group_data = None
    for glist, gdata in entry_tables_info["GROUP_DATA"]:
        # print(" ???", glist, gdata)
        group_data_exact = False
        for g in glist:
            if g == class_group:
                # Exact match – this has priority
                group_data_exact = True
                break
            if fnmatch.fnmatchcase(class_group, g):
                group_data_count += 1
                break
        else:
            # No match, seek further
            continue
        # Check <occasion>
        for o in gdata["OCCASION"]:
            if fnmatch.fnmatchcase(occasion, o):
                break
        else:
            # No match, seek further
            continue
        # Matched group and occasion
        group_data = gdata
        if group_data_exact:
            break
    else:
        if group_data_count != 1:
            if group_data_count == 0:
                raise GradeTableError(
                    T["NO_TEMPLATE_GROUP"].format(group=class_group)
                )
            raise GradeTableError(
                T["AMBIGUOUS_TEMPLATE_GROUP"].format(group=class_group)
            )

    ### Get template file
    template_path = RESOURCEPATH(group_data["TEMPLATE"])
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
    for f, t in entry_tables_info["INFO_FIELDS"]:
        info_transl[f] = t
    info: Dict[str, str] = {
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
    sdata: list
    for sdata in sorted(subjects.values()):
        sid = sdata[1]
#TODO: Should special subjects at all be present?
        if sid[0] == "$":
            # Skipping "special" subjects
            continue
        # Add subject
        col: int = table.nextcol()
        sidcol.append((sid, col))
        table.write(rowix[0], col, sid)
        table.write(rowix[1], col, sdata[2])
    # Enforce minimum number of columns
    while col < 18:
        col = table.nextcol()
        table.write(rowix[0], col, "")
    # Delete excess columns
    table.delEndCols(col + 1)

    ### Add pupils and grades
    for pdata, p_atoms, p_grade_tids in pupils:
        pid = pdata["PID"]
        pgrades: dict[str, str]
        try:
            pgrades = grades[pid]
        except:
            pgrades = {}
        row = table.nextrow()
        table.write(row, 0, pid)
        table.write(row, 1, pupil_name(pdata))
        table.write(row, 2, pdata["GROUPS"])
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


def get_group_info(
    group_info: dict[str, dict[str, Any]], group: str, key: str
) -> Any:
    """Read a value for a given group and key from a mapping with an
    "inheritance" mechanism.
    """
    while True:
        try:
            mapping: dict[str, Any] = group_info[group]
        except KeyError:
            raise GradeTableError(_NO_INFO_FOR_GROUP.format(group=group))
        try:
            return mapping[key]
        except KeyError:
            pass
        try:
            group = mapping["__INHERIT__"]
        except KeyError:
            raise GradeTableError(_MISSING_KEY.format(key=key))


def readGradeTableFile(filepath: str) -> tuple[
    dict[str, str], dict[str, dict[str, str]]
]:
    """Read the header info and pupils' grades from the given grade
    table (file).
    The "spreadsheet" module is used as backend so .ods, .xlsx and .tsv
    formats are possible. The filename may be passed without extension –
    <Spreadsheet> then looks for a file with a suitable extension.
    Return mappings for header-info and pupil-grades.
    """
    grade_entry_info = get_grade_entry_tables()
    header_map = {t: f for f, t in grade_entry_info["HEADERS"]}
    info_map = {t: f for f, t in grade_entry_info["INFO_FIELDS"]}
    datatable = read_DataTable(filepath)
    info = {
        (info_map.get(k) or k): v
        for k, v in datatable["__INFO__"].items()
    }
    ### Get the rows as mappings
    # fields = datatable["__FIELDS__"]
    # print("\nFIELDS:", fields)
    gdata: dict[str, dict[str, str]] = {}
    for pdata in datatable["__ROWS__"]:
        pinfo = [pdata.pop(h) for h in header_map]
        pid: str = pinfo[0]
        grades: dict[str, str] = {}
        if pid != "$":
            gdata[pid] = pdata
    return info, gdata



#####################################

class GradeTable:
    """Manage the grade data for one group in one "term" – corresponding
    to the contents of a single grade table.
    """

    def __init__(self, gradetable: dict):
        """Use the subject/course information to handle "composite" subjects
        and other special cases (e.g. averages).
        <gradetable> is a structure such as is return by the function
        <readGradeFile>.
        """
        info: Dict[str, str] = gradetable["__INFO__"]
        self.group = info["GROUP"]
        self.term = info["TERM"]
        self.grades_date = info["GRADES_D"]
        self.issue_date = info["ISSUE_D"]
        self.gradeBase = GradeBase(self.term, self.group)
        if info["SCHOOLYEAR"] != SCHOOLYEAR:
            raise GradeTableError(
                _TABLE_YEAR_MISMATCH.format(
                    year=SCHOOLYEAR, filepath=info["__FILEPATH__"]
                )
            )
        ### Get subjects for grade reports
        subjects = Subjects()
        # Check the subject names in the input file
        for sid, name in gradetable["__SUBJECT_NAMES__"].items():
            subjects.check_subject_name(sid, name)
        class_subjects: List[Tuple[str, str]]
        class_pupils: List[Tuple[str, str, str, dict]]
        self.class_subjects, class_pupils = subjects.filter_pupil_group(
            self.group, date=self.grades_date
        )
        # Do I really need to go through the subject lists for each pupil?
        # I suppose, in principle, the calculations could vary from pupil to
        # pupil. That would be unintended, but perhaps difficult to avoid as
        # an error-prone possibility ...
        self.pupils_grade_data = [
            PupilGradeData(
                gradeBase=self.gradeBase,
                pupilid=pid,
                pupilname=pname,
                pupilgroups=pgroups,
                subjectdata=sdata,
                grades=gradetable["__GRADEMAP__"][pid],
            )
            for pid, pname, pgroups, sdata in class_pupils
        ]


class PupilGradeData:
    """Manage the grades for a single pupil"""

    def __init__(
        self,
        #gradeBase: GradeBase,
        pupilid: str,
        pupilname: str,
        pupilgroups: str,
        subjectdata: dict[str, dict[str, str]],
        grades: dict[str, str],
    ):
        """Extract and process the subject data needed for grade reports.
        The dependencies of composite and calculated fields are determined.
        """
        self.gradeBase = gradeBase
        self.pid = pupilid
        self.name = pupilname
        self.groups = pupilgroups.split()
        self.grades = grades
        components: dict[str, list[tuple[str, int]]] = {}
        specials: set[str] = set()
        self.pupil_subjects: dict[str, dict[str, str]] = {}
        for sid, smap in subjectdata.items():
            psmap: dict[str, Any] = {
                "TIDS": smap["TIDS"],
                "GROUP": smap["GROUP"],
                "SGROUP": smap["SGROUP"],
            }
            self.pupil_subjects[sid] = psmap
            cmpst = smap["COMPOSITE"]
            dependers: list[str] = cmpst.split() if cmpst else []
            if dependers:
                for _d in dependers:
                    if _d[0] != "$":
                        # Entries must be COMPOSITE or CALC
                        raise GradeTableError(_BAD_DEPENDER.format(sid=_d))
                    # Split off weighting
                    try:
                        d, _w = _d.split("*", 1)
                    except ValueError:
                        d, w = _d, 1
                    else:
                        try:
                            w = int(_w)
                        except ValueError:
                            raise GradeTableError(
                                _BAD_WEIGHT.format(sid=sid, d=_d)
                            )
                    if len(d) > 1 and d[1] == "$":
                        # A CALC
                        try:
                            psmap["CALCS"].append(d)
                        except KeyError:
                            psmap["CALCS"] = [d]
                        # psmap["COMPOSITE"] = None
                    else:
                        # A COMPOSITE, possibly "$"
                        if sid[0] == "$":
                            # A composite may not be a component of another composite
                            raise GradeTableError(
                                _COMPOSITE_COMPONENT.format(sid=sid, comp=d)
                            )
                        if len(dependers) != 1:
                            # A composite must be the only entry
                            raise GradeTableError(
                                _COMPOSITE_NOT_ALONE.format(sid=sid, comp=d)
                            )
                        psmap["COMPOSITE"] = d
                    try:
                        components[d].append((sid, w))
                    except KeyError:
                        components[d] = [(sid, w)]
            if sid[0] == "$":
                if len(sid) == 1:
                    raise GradeTableError(_NULL_COMPOSITE)
                if sid[1] == "$":
                    # CALC item – should not have an entry in the subjects table
                    raise GradeTableError(_BAD_COMPOSITE.format(sid=sid))
                else:
                    # COMPOSITE item
                    specials.add(sid)
        self.calcs: Dict[str, List[Tuple[str, int]]] = {}
        self.composites: Dict[str, List[Tuple[str, int]]] = {}
        for c, clist in components.items():
            try:
                specials.remove(c)
            except KeyError:
                if c.startswith("$$"):
                    # CALC item
                    # The handler should be provided by "local" code.
                    self.calcs[c] = clist
            else:
                self.composites[c] = clist
        for c in specials:
            REPORT("WARNING", _EMPTY_COMPOSITE.format(sid=c))

    def calculate(self):
        """Perform the calculations demanded by the COMPOSITES and the
        CALCS.
        """
        ### Start with the COMPOSITES
        for csid, clist in self.composites.items():
            try:
                self.grades[csid] = self.gradeBase.composite_calc(
                    clist, self.grades
                )
            except GradeConfigError as e:
                REPORT("ERROR", f"{self.name}: {e}")
        ### Now the CALCS
        for csid, clist in self.calcs.items():
            try:
                self.grades[csid] = self.gradeBase.calc_calc(clist,
                        self.grades)
            except GradeConfigError as e:
                REPORT("ERROR", f"{self.name}: {e}")


#TODO
def collate_grade_tables(
    files: list[str],
    term: str,
    group: str,
) -> dict[str, dict[str, str]]:
    """Use <readGradeTableFile> to collect the grades from a set of grade
    tables – passed as <files>.
    Return the collated grades: {pid: {sid: grade}}.
    Only grades that have actually been given (i.e. no empty grades or
    grades for unchosen or unavailable subject) will be included.
    If a grade for a pupil/subject pair is given in multiple input tables,
    an exception will only be raised if the grades are different.
    """
    grades: dict[str, dict[str, str]] = {}
    # For error tracing, retain file containing first definition of a grade.
    fmap: dict[tuple[str, str], str] = {}  # {(pid, sid): filepath}
    for filepath in files:
        info, table = readGradeTableFile(filepath)
        if info["SCHOOLYEAR"] != SCHOOLYEAR:
            raise GradeTableError(
                _TABLE_YEAR_MISMATCH.format(
                    year=SCHOOLYEAR, filepath=info["__FILEPATH__"]
                )
            )
        if info["GROUP"] != group:
            raise GradeTableError(
                _TABLE_CLASS_MISMATCH.format(
                    group=group, path=info["__FILEPATH__"]
                )
            )
        if info["TERM"] != term:
            raise GradeTableError(
                _TABLE_TERM_MISMATCH.format(
                    term=term, path=info["__FILEPATH__"]
                )
            )
        newgrades = table["__GRADEMAP__"]
        # print("\n$$$", filepath)
        for pid, smap in newgrades.items():
            try:
                smap0 = grades[pid]
            except KeyError:
                smap0 = {}
                grades[pid] = smap0
            for s, g in smap.items():
                if g:
                    if g in (NULL, UNCHOSEN):
                        continue
                    g0 = smap0.get(s)
                    if g0:
                        if g0 != g:
                            raise GradeTableError(
                                _GRADE_CONFLICT.format(
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

    __cg = "12G.R"
    __cg = "11G"
#    __cg = "12G.G"

    tbytes = makeGradeTable("1. Halbjahr", __cg)

    tpath = DATAPATH(f"testing/tmp/GradeInput-{__cg}.xlsx")
    tdir = os.path.dirname(tpath)
    if not os.path.isdir(tdir):
        os.makedirs(tdir)
    with open(tpath, "wb") as _fh:
        _fh.write(tbytes)
    print(f"\nWROTE GRADE TABLE TO {tpath}\n")

    print("\n *************************************************\n")

    info, gdata = rawGradeTableFile(tpath)
    print("\nINFO:", info)
    for pid, pdata in gdata.items():
        print(f" --- {pid}:", pdata)

    quit(0)


    _filepath = DATAPATH(f"testing/Noten/NOTEN_1/Noten_{_group}_1")
    _gdata = readGradeFile(_filepath)
    for key, val in _gdata.items():
        print(f"\n** {key}: {repr(val)}")

    _tbytes = makeGradeTable(
        term="1", group=_group, grades=_gdata["__GRADEMAP__"]
    )
    #        ISSUE_D: Optional[str] = None,
    #        GRADES_D: Optional[str] = None)

    _tpath = DATAPATH(f"testing/tmp/GradeTable-{_group}.xlsx")
    _tdir = os.path.dirname(_tpath)
    if not os.path.isdir(_tdir):
        os.makedirs(_tdir)
    with open(_tpath, "wb") as _fh:
        _fh.write(_tbytes)
    print(f"\nWROTE GRADE TABLE TO {_tpath}\n")

    print("\n *************************************************\n")

    from glob import glob

    _files = glob(DATAPATH("testing/Noten/NOTEN_1_11.G/Noten_*"))
    _group = "11G.G"
    _term = "1. Halbjahr"
    _grades = collate_grade_tables(files=_files, term=_term, group=_group)
    print("COLLATED:")
    for pid, smap in _grades.items():
        print(f"\n -- {pid}::", smap)
    _tbytes = makeGradeTable(term=_term, group=_group, grades=_grades)
    #        ISSUE_D: Optional[str] = None,
    #        GRADES_D: Optional[str] = None)

    _tpath = DATAPATH(f"testing/tmp/GradeTable-{_group}.xlsx")
    # _tdir = os.path.dirname(_tpath)
    # if not os.path.isdir(_tdir):
    #    os.makedirs(_tdir)
    with open(_tpath, "wb") as _fh:
        _fh.write(_tbytes)
    print(f"\nWROTE GRADE TABLE TO {_tpath}\n")

    print("\n *************************************************\n")

    print("\n ... complete grade table")
    _cgtable = GradeTable(_gdata)
    for pgdata in _cgtable.pupils_grade_data:
        print("\n???X", pgdata.pid, pgdata.name)
        for sid, smap in pgdata.pupil_subjects.items():
            print(f"§§§ {sid}: {repr(smap)}")
        print("\n--- COMPOSITES:", pgdata.composites)
        print("\n--- CALCS:", pgdata.calcs)

        pgdata.calculate()
        print("\n--- GRADES:", pgdata.grades)
