"""
grades/gradetable.py

Last updated:  2022-01-07

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

#
_TITLE = "Notentabelle, erstellt {time}"

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

    start.setup(os.path.join(basedir, "TESTDATA"))
#    start.setup(os.path.join(basedir, 'DATA'))

### +++++


from typing import Dict, List, Optional, Any, Set, Tuple

import datetime

from core.base import Dates
from core.courses import Subjects, NULL, UNCHOSEN
from tables.spreadsheet import read_DataTable, filter_DataTable
from tables.matrix import KlassMatrix

# from local.base_config import DECIMAL_SEP, USE_XLSX, year_path
from local.local_grades import GradeBase

# from local.abitur_config import AbiCalc


class GradeTableError(Exception):
    pass


class FailedSave(Exception):
    pass


### -----


def get_with_default(
    mapping: Dict[str, Any], key: str, default: Dict[str, Any]
) -> Any:
    """Read a value from a "key -> value" mapping when default values
    are available in a second mapping.
    """
    try:
        return mapping[key]
    except KeyError:
        pass
    try:
        return default["__DEFAULT__"][key]
    except KeyError:
        pass
    raise GradeTableError(_MISSING_KEY.format(key=key))


def makeGradeTable(
    term: str,
    group: str,
    ISSUE_D: Optional[str] = None,
    GRADES_D: Optional[str] = None,
    grades: Optional[Dict[str, Dict[str, str]]] = None,
) -> bytes:
    """Build a basic pupil/subject table for grade input using a
    template appropriate for the given group.
    Existing grades can be included in the table by passing an appropriate
    structure as <grades>: {pid -> {sid -> grade}}
    """
    ### Get template file
    group_info = MINION(DATAPATH("CONFIG/GRADE_GROUP_INFO"))
    try:
        grade_info = group_info[group]
    except KeyError:
        raise GradeTableError(_NO_INFO_FOR_GROUP.format(group=group))
    template = get_with_default(grade_info, "GradeTableTemplate", group_info)
    template_path = RESOURCEPATH(f"templates/{template}.xlsx")
    table = KlassMatrix(template_path)

    ### Set title line
    table.setTitle(
        _TITLE.format(
            time=datetime.datetime.now().isoformat(sep=" ", timespec="minutes")
        )
    )
    ### Gather general info
    group_data: dict = MINION(DATAPATH("CONFIG/GRADE_DATA"))
    if not ISSUE_D:
        ISSUE_D = Dates.today()
    if not GRADES_D:
        GRADES_D = ISSUE_D
    info_transl: Dict[str, str] = {}
    info_item: dict
    for info_item in group_data["INFO_FIELDS"]:
        f = info_item["NAME"]
        t = info_item["DISPLAY_NAME"]
        info_transl[f] = t
    info: Dict[str, str] = {
        info_transl["SCHOOLYEAR"]: SCHOOLYEAR,
        info_transl["GROUP"]: group,
        # TODO:
        info_transl["TERM"]: term,
        info_transl["GRADES_D"]: GRADES_D,
        info_transl["ISSUE_D"]: ISSUE_D,
    }
    table.setInfo(info)

    ### Get subjects for grade reports
    subjects = Subjects()
    class_subjects: List[Tuple[str, str]]
    class_pupils: List[Tuple[str, str, dict]]
    class_subjects, class_pupils = subjects.filter_pupil_group(
        group, date=GRADES_D
    )

    ### Go through the template columns and check if they are needed:
    rowix: List[int] = table.header_rowindex  # indexes of header rows
    if len(rowix) != 2:
        raise GradeTableError(_TEMPLATE_HEADER_WRONG.format(path=template_path))
    sidcol: List[Tuple[str, int]] = []
    sid: str
    sname: str
    for sid, sname in class_subjects:
        if sid[0] == "$":
            # Skipping "special" subjects
            continue
        # Add subject
        col: int = table.nextcol()
        sidcol.append((sid, col))
        table.write(rowix[0], col, sid)
        table.write(rowix[1], col, sname)
    # Enforce minimum number of columns
    while col < 18:
        col = table.nextcol()
        table.write(rowix[0], col, "")
    # Delete excess columns
    table.delEndCols(col + 1)

    ### Add pupils
    for pid, pname, pgroups, sdata in class_pupils:
        try:
            pgrades = grades[pid]
        except:
            pgrades = {}
        row = table.nextrow()
        table.write(row, 0, pid)
        table.write(row, 1, pname)
        table.write(row, 2, pgroups)
        for sid, col in sidcol:
            if sid in sdata:
                # Get existing value
                g = pgrades.get(sid)
                if g:
                    table.write(row, col, g)
            else:
                table.write(row, col, "X", protect=True)
    # Delete excess rows
    row = table.nextrow()
    table.delEndRows(row)

    ### Save file
    table.protectSheet()
    return table.save_bytes()


def rawGradeTableFile(filepath: str) -> dict:
    """Read the header info and pupils' grades from the given grade
    table (file).
    The "spreadsheet" module is used as backend so .ods, .xlsx and .tsv
    formats are possible. The filename may be passed without extension –
    <Spreadsheet> then looks for a file with a suitable extension.
    Return a "DataTable" structure.
    """
    dbt = read_DataTable(filepath)
    return filter_DataTable(
        dbt, MINION(DATAPATH("CONFIG/GRADE_DATA")), matrix=True, extend=False
    )


def readGradeFile(filepath: str) -> Dict[str, Any]:
    dtable = rawGradeTableFile(filepath)
    subject_tags = dtable["__XFIELDS__"]
    #    print("info:", dtable["__INFO__"])
    #    print("subject_tags:", subject_tags)
    # Map pupil to grade-mapping
    gdata: Dict[str, Dict[str, str]] = {}
    for pdata in dtable["__ROWS__"]:
        pid: str = pdata["PID"]
        grades: Dict[str, str] = {}
        if pid == "$":
            dtable["__SUBJECT_NAMES__"] = grades
        else:
            gdata[pid] = grades
        for sid in subject_tags:
            g = pdata[sid]
            grades[sid] = g
    dtable["__GRADEMAP__"] = gdata
    return dtable


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
        self.issue_data = info["ISSUE_D"]
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
        class_pupils: List[Tuple[str, str, dict]]
        class_subjects, class_pupils = subjects.filter_pupil_group(
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
        gradeBase: GradeBase,
        pupilid: str,
        pupilname: str,
        pupilgroups: str,
        subjectdata: Dict[str, Dict[str, str]],
        grades: Dict[str, str],
    ):
        """Extract and process the subject data needed for grade reports.
        The dependencies of composite and calculated fields are determined.
        """
        self.gradeBase = gradeBase
        self.pid = pupilid
        self.name = pupilname
        self.groups = pupilgroups.split()
        self.grades = grades
        components: Dict[str, List[Tuple[str, int]]] = {}
        specials: Set[str] = set()
        self.pupil_subjects: Dict[str, Dict[str, str]] = {}
        for sid, smap in subjectdata.items():
            psmap = {
                "TIDS": smap["TIDS"],
                "GROUP": smap["GROUP"],
                "SGROUP": smap["SGROUP"],
            }
            self.pupil_subjects[sid] = psmap
            cmpst = smap["COMPOSITE"]
            dependers: List[str] = cmpst.split() if cmpst else []
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
            self.grades[csid] = self.gradeBase.composite_calc(
                clist, self.grades
            )
        ### Now the CALCS
        for csid, clist in self.calcs.items():
            self.grades[csid] = self.gradeBase.calc_calc(clist, self.grades)


def collate_grade_tables(
    files: List[str],
    term: str,
    group: str,
) -> Dict[str, Dict[str, str]]:
    """Use <readGradeFile> to collect the grades from a set of grade
    tables – passed as <files>.
    Return the collated grades: {pid: {sid: grade}}.
    Only grades that have actually been given (i.e. no empty grades or
    grades for unchosen or unavailable subject) will be included.
    If a grade for a pupil/subject pair is given in separate tables,
    an exception will only be raised if the grades are different.
    """
    grades: Dict[str, Dict[str, str]] = {}
    # For error tracing, retain file containing first definition of a grade.
    fmap: Dict[Tuple[str, str], str] = {}  # {(pid, sid): filepath}
    for filepath in files:
        table = readGradeFile(filepath)
        info = table["__INFO__"]
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
    _GRADE_DATA = MINION(DATAPATH("CONFIG/GRADE_DATA"))
    _group = "12G.R"
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
