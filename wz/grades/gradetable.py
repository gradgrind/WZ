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

### Grade table "info" items
_SCHOOLYEAR = "Schuljahr"
_GROUP = "Klasse/Gruppe"
_TERM = "Anlass"
_ISSUE_D = "Ausgabedatum"  # or 'Ausstellungsdatum'?
_GRADES_D = "Notendatum"

### Messages
_NO_INFO_FOR_GROUP = (
    "Klasse/Gruppe {group}: Notenzeugnisse sind nicht" " vorgesehen"
)
_TEMPLATE_HEADER_WRONG = "Fehler bei den Kopfzeilen der Vorlage:\n {path}"
_MISSING_KEY = "Eintrag fehlt in Konfigurationsdatei: {key}"
_GRADE_MISSING = "Leeres Notenfeld im Fach {sid}, Tabelle:\n  {path}"

_TABLE_CLASS_MISMATCH = "Falsche Klasse/Gruppe in Notentabelle:\n  {filepath}"
_TABLE_TERM_MISMATCH = 'Falscher "Anlass" in Notentabelle:\n  {filepath}'
_TABLE_YEAR_MISMATCH = "Falsches Schuljahr in Notentabelle:\n  {filepath}"
_PIDS_NOT_IN_GROUP = "Schüler nicht in Gruppe {group}: {pids}"
_WARN_EXTRA_PUPIL = (
    "Unerwarteter Schüler ({name}) in" " Notentabelle:\n  {tfile}"
)
_WARN_EXTRA_SUBJECT = "Unerwartetes Fach ({sid}) in" " Notentabelle:\n  {tfile}"
_ERROR_OVERWRITE = (
    "Neue Note für {name} im Fach {sid} mehrmals"
    " vorhanden:\n  {tfile1}\n  {tfile2}"
)
_BAD_GRADE = "Ungültige Note im Fach {sid}: {g}"
_NO_DATE = "Kein Ausgabedatum angegeben"
_DATE_EXISTS = "Ausgabedatum existiert schon"
_BAD_DEPENDER = "Ungültiges Sonderfach-Kürzel: {sid}"
_BAD_WEIGHT = "Gewichtung des Faches ({sid}) muss eine Zahl sein: '{d}'"
_NULL_COMPOSITE = "'$' ist nicht gültig als Fach-Kürzel"
_BAD_COMPOSITE = "Ungültiges Fach-Kürzel: {sid}"
_MISSING_COMPOSITE = "Fach-Kürzel {sid} hat keinen Eintrag"
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
from fractions import Fraction
from collections import namedtuple

from core.base import Dates
from core.pupils import Pupils
from core.courses import Subjects, NULL, UNCHOSEN
from tables.spreadsheet import (
    Spreadsheet,
    TableError,
    read_DataTable,
    filter_DataTable,
    make_DataTable,
)
from tables.matrix import KlassMatrix

# from local.base_config import DECIMAL_SEP, USE_XLSX, year_path
# from local.local_grades import GradeBase, UNCHOSEN, NO_GRADE

# from local.abitur_config import AbiCalc


class GradeTableError(Exception):
    pass


class FailedSave(Exception):
    pass


NO_GRADE = '*'

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


# Where to put the file?
def makeGradeTable(
    term: str,
    group: str,
    ISSUE_D: Optional[str] = None,
    GRADES_D: Optional[str] = None,
) -> bytes:
    """Build a basic pupil/subject table for grade input using a
        template appropriate for the given group.

    #TODO: Also possible to include the existing grades?
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
        row = table.nextrow()
        table.write(row, 0, pid)
        table.write(row, 1, pname)
        table.write(row, 2, pgroups)
        for sid, col in sidcol:
            if sid in sdata:
                # TODO: Get existing value ...
                g = ""
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


def readGradeFile(filepath: str, check_complete: bool = False) -> Dict[str,Any]:
    dtable = rawGradeTableFile(filepath)
    subject_tags = dtable["__XFIELDS__"]
    #    print("info:", dtable["__INFO__"])
    #    print("subject_tags:", subject_tags)
    # Map pupil to grade-mapping, skipping empty, NULL and UNCHOSEN entries
    # TODO: That may not be the optimal policy – it might be helpful to recognize
    # subjects for which there is no grade when there should be one (empty grade)?
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
            if (not g) and check_complete:
                REPORT("WARNING", _GRADE_MISSING.format(sid=sid,
                        path=filepath))
#            if g and g not in (NULL, UNCHOSEN):
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
        if info["SCHOOLYEAR"] != SCHOOLYEAR:
            raise GradeTableError(
                _TABLE_YEAR_MISMATCH.format(filepath=info["__FILEPATH__"])
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
                pupilid=pid,
                pupilname=pname,
                pupilgroups=pgroups,
                subjectdata=sdata,
                grades=gradetable["__GRADEMAP__"][pid],
            )
            for pid, pname, pgroups, sdata in class_pupils
        ]


class PupilGradeData:
    """Manage the grades for a single pupil
    """
    def __init__(
        self,
        pupilid: str,
        pupilname: str,
        pupilgroups: str,
        subjectdata: Dict[str, Dict[str, str]],
        grades: Dict[str, str],
    ):
        """Extract and process the subject data needed for grade reports.
        The dependencies of composite and calculated fields are determined.
        """
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
                            raise GradeTableError(_BAD_WEIGHT.format(
                                    sid=sid, d=_d))
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
        #print("\n§§§calcs:", self.calcs)
        #print("\n§§§composites:", self.composites)

    def calculate(self):
        """Perform the calculations demanded by the COMPOSITES and the
        CALCS.
        """
        ### Start with the COMPOSITES
        for csid, clist in self.composites.items():
            self.grades[csid] = self.composite_calc(clist)
            #print("\n???", self.name, csid, self.grades[csid])
        ### Now the CALCS
        for csid, clist in self.calcs.items():
            self.grades[csid] = self.calc_calc(clist)
            #print("\n???", self.name, csid, self.grades[csid])


# TODO: local?
    def composite_calc(self, clist):
        """Recalculate a composite grade.
        The (weighted) average of the components will be calculated,
        if possible.
        If there are no numeric grades, choose NO_GRADE, unless all
        components are UNCHOSEN (in which case also the composite will
        be UNCHOSEN).
        """
#TODO: Distinguish UNCHOSEN and NULL?
        asum = 0
        ai = 0
        non_grade = UNCHOSEN
        for csid, weight in clist:
# Can the entry be missing?
            g = self.grades[csid]
            if g:
                try:
                    gi = int(g.rstrip("+-"))
                except ValueError:
                    if g not in (UNCHOSEN, NULL):
                        non_grade = NO_GRADE
                    continue
                ai += weight
                asum += gi * weight
            else:
                non_grade = NO_GRADE
        if ai:
            g = Frac(asum, ai).round()
            return g
#TODO: return g.zfill(2) if self.sekII else g.zfill(1)
            return self.grade_format(g)
        else:
            return non_grade


# TODO: local?
    def calc_calc(self, clist):
        """Recalculate a CALC value.
        The (weighted) average of the components will be calculated,
        if possible.
        """
        asum = 0
        ai = 0
        for csid, weight in clist:
# Can the entry be missing?
            g = self.grades[csid]
            if g:
                try:
                    gi = int(g.rstrip("+-"))
                except ValueError:
                    continue
                ai += weight
                asum += gi * weight
        if ai:
            g = Frac(asum, ai).round(2)
            return g
        else:
            return "–––"


class Frac(Fraction):
    """A <Fraction> subclass with custom <truncate> and <round> methods
    returning strings.
    """

    def truncate(self, decimal_places: int = 0) -> str:
        if not decimal_places:
            return str(int(self))
        v = int(self * 10 ** decimal_places)
        # Ensure there are enough leading zeroes
        sval = f"{v:0{decimal_places + 1}d}"
        return (
            sval[:-decimal_places]
            + CONFIG["DECIMAL_SEP"]
            + sval[-decimal_places:]
        )

    def round(self, decimal_places: int = 0) -> str:
        f = Fraction(1, 2) if self >= 0 else Fraction(-1, 2)
        if not decimal_places:
            return str(int(self + f))
        v = int(self * 10 ** decimal_places + f)
        # Ensure there are enough leading zeroes
        sval = f"{v:0{decimal_places + 1}d}"
        return (
            sval[:-decimal_places]
            + CONFIG["DECIMAL_SEP"]
            + sval[-decimal_places:]
        )


########################################################################
# Without base class???
# class Grades(GradeBase):
class Grades:
    """A <Grades> instance manages the set of grades in the database for
    a pupil and "term".
    """

    def __init__(self, group, stream, grades):
        super().__init__(group, stream)
        for sid, g in grades.items():
            self.set_grade(sid, g)

    #
    def filter_grade(self, sid, g):
        """Return the possibly filtered grade <g> for the subject <sid>.
        Integer values are stored additionally in the mapping
        <self.i_grade> – only for subjects with numerical grades, others
        are set to -1.
        """
        if sid[0] == "*":
            # An "extra" field
            return g or ""
        # There can be normal, empty, non-numeric and badly-formed grades
        gi = -1  # integer value
        if g:
            if g in self.valid_grades:
                # Separate out numeric grades, ignoring '+' and '-'.
                # This can also be used for the Abitur scale, though the
                # stripping is superfluous.
                try:
                    gi = int(g.rstrip("+-"))
                except ValueError:
                    pass
            else:
                REPORT("ERROR", _BAD_GRADE.format(sid=sid, g=g))
                g = ""
        else:
            g = ""  # ensure that the grade is a <str>
        self.i_grade[sid] = gi
        return g

    #
    def set_grade(self, sid, grade):
        """Update a single grade."""
        self[sid] = self.filter_grade(sid, grade)

    #
    def composite_calc(self, sdata):
        """Recalculate a composite grade.
        <sdata> is the subject-data for the composite, the (weighted)
        average of the components will be calculated, if possible.
        If there are no numeric grades, choose NO_GRADE, unless all
        components are UNCHOSEN (in which case also the composite will
        be UNCHOSEN).
        """
        asum = 0
        ai = 0
        non_grade = UNCHOSEN
        for csid, weight in sdata.composite:
            gi = self.i_grade[csid]
            if gi >= 0:
                ai += weight
                asum += gi * weight
            elif self[csid] != UNCHOSEN:
                non_grade = NO_GRADE
        if ai:
            g = Frac(asum, ai).round()
            self[sdata.sid] = self.grade_format(g)
            self.i_grade[sdata.sid] = int(g)
        else:
            self[sdata.sid] = non_grade


###


class _GradeTable(dict):
    """Manage the grade data for a term (etc.) and group.
    <term> need not actually be a "school term", though it may well be.
    It is used rather to specify the "occasion" determining the issue
    of the reports.
    For each possible, valid combination of "term" and group there is
    a grade table (pupil-subject, plus some general information).
    The class instance is a mapping: {pid -> <Grades> instance}. The
    stream is available in the <Grades> instance.
    Additional information is available as attributes:
        <group>: school-class/group, as specified in
                <GradeBase.REPORT_GROUPS>
        <term>: a string representing a valid "term" (school-term, etc.)
        <schoolyear>: school-year
        <issue_d>: date of issue
        <grades_d>: date of grade finalization
        <sid2subject_data>: {sid -> subject_data} also for "special" sids
        <subjects>: {sid -> subject-name}   (just "real" sids)
        <composites>: {sid -> subject-name} ("composite" sids)
        <components>: set of "component" sids
        <extra>: {sid/tag -> text name} ("extra" data, treated as grade)
        <name>: {pid -> (short) name}
    """

    SCHOOLYEAR = _SCHOOLYEAR
    GROUP = _GROUP
    TERM = _TERM
    ISSUE_D = _ISSUE_D
    GRADES_D = _GRADES_D
    #
    def __init__(self, schoolyear):
        super().__init__()
        self.schoolyear = schoolyear
        self.group = None
        self.term = None
        self.issue_d = None
        self.grades_d = None
        self.sid2subject_data = None
        self.subjects = None
        self.composites = None
        self.extras = None
        self.name = {}
        self.calcs = None
        self.abicalc = None

    #
    def _readtable(self, dbtable, sid2col):
        """Read the grades from a table with column-mapping <sid2col>."""
        for row in dbtable:
            pid = row[0]
            if pid and pid != "$":
                gmap = {sid: row[col] for sid, col in sid2col}
                self.name[pid] = row[1]
                # stream = row[2]
                grades = Grades(self.group, row[2], self._include_grades(gmap))
                self[pid] = grades
                for comp in self.composites:
                    grades.composite_calc(self.sid2subject_data[comp])
                if self.term == "A":
                    grades.abicalc = AbiCalc(self, pid)

    #
    def _new_group_table(self, pids):
        """Initialize an empty table for <self.group> and <self.term>.
        If <pids> is not null, only include these pupils.
        """
        ## Initialize the dates (issue at end of term, or end of year)
        if self.term[0] in ("S", "T"):
            # ... unless it is a special table
            date = "*"
        else:
            calendar = Dates.get_calendar(self.schoolyear)
            try:
                date = calendar["TERM_%d" % (int(self.term) + 1)]
            except:
                date = calendar["LAST_DAY"]
            else:
                # Previous day, ensure that it is a weekday
                td = datetime.timedelta(days=1)
                d = datetime.date.fromisoformat(date)
                while True:
                    d -= td
                    if d.weekday() < 5:
                        date = d.isoformat()
                        break
        self.issue_d = date
        self.grades_d = "*"

        ## Pupil information
        # Pupil data, select pupils
        pupils = Pupils(self.schoolyear)
        pidset = set(pids) if pids else None
        for pdata in pupils.group2pupils(self.group, date=date):
            pid = pdata["PID"]
            if pids:
                try:
                    pidset.remove(pid)
                except KeyError:
                    continue
            self.name[pid] = pdata.name()
            # Set grades (all empty)
            grades = Grades(
                self.group, pdata["STREAM"], self._include_grades({})
            )
            self[pid] = grades
            for comp in self.composites:
                grades.composite_calc(self.sid2subject_data[comp])
            if self.term == "A":
                grades.abicalc = AbiCalc(self, pid)
        if pidset:
            raise GradeTableError(
                _PIDS_NOT_IN_GROUP.format(
                    group=self.group, pids=", ".join(pidset)
                )
            )

    #
    def _set_group_term(self, group, term):
        """Set the subjects and extra pupil-data fields for the given
        group and term.
        """
        self.group = group
        self.term = term
        # Get subjects
        subjects = Subjects(self.schoolyear)
        self.sid2subject_data = {}  # {sid -> subject_data}
        self.subjects = {}  # name-mapping just for "real" subjects
        self.composites = {}  # name-mapping for composite sids
        self.components = set()  # set of "component" sids
        for gs in subjects.grade_subjects(group):
            sid = gs.sid
            self.sid2subject_data[sid] = gs
            if term[0] == "T":
                # Only include if in 'T' group
                if "T" not in gs.report_groups:
                    continue
            if gs.tids:
                # "real" (taught) subject
                self.subjects[sid] = gs.name
                if gs.composite:
                    self.components.add(sid)
            else:
                # "composite" subject
                self.composites[sid] = gs.name
        # name-mapping for "extra" sid-fields:
        self.extras = Grades.xgradefields(group, term)
        # additional info fields, which are calculated from the other data
        self.calcs = Grades.calc_fields(group, term)
        if term == "A":
            # Modify for Abitur
            AbiCalc.subjects(self)

    #
    def _include_grades(self, gmap):
        """Return a grade mapping.
        Include grades for all subjects and extra entries.
        Initial values are taken from the mapping <gmap>: {sid -> grade}.
        The expected entries are set previously in method <_set_group_term>.
        """
        grades = {}
        for sid in self.subjects:
            grades[sid] = gmap.get(sid) or ""
        for comp in self.composites:
            grades[comp] = gmap.get(comp) or ""
        for xsid in self.extras:
            grades[xsid] = gmap.get(xsid) or ""
        return grades

    #
    def make_grade_table(self, title: str = None):
        """Build a basic pupil/subject table for grade input.
        The field names will be localized.
        It will contain the existing grades. To get an empty table,
        initialize the <GradeTable> instance using method <new_group_table>.
        """
        ### Get template file
        #        group_info = MINION(DATAPATH("CONFIG/GRADE_GROUPS"))

        template = GradeBase.group_info(self.group, "NotentabelleVorlage")
        template_path = os.path.join(
            RESOURCES, "templates", *template.split("/")
        )
        table = KlassMatrix(template_path)

        ### Set title line
        dt = datetime.datetime.now()
        table.setTitle(
            _TITLE.format(time=dt.isoformat(sep=" ", timespec="minutes"))
        )

        ### Translate and enter general info
        info = (
            ("SCHOOLYEAR", SCHOOLYEAR),
            (_GROUP, group),
            (_TERM, GradeBase.term2text(self.term)),
            (_GRADES_D, self.grades_d),
            (_ISSUE_D, self.issue_d),
        )
        table.setInfo(info)
        ### Go through the template columns and check if they are needed:
        sidcol = []
        col = 0
        rowix = table.row0()  # index of header row
        for sid, sname in self.subjects.items():
            # Add subject
            col = table.nextcol()
            sidcol.append((sid, col))
            table.write(rowix, col, sid)
            table.write(rowix + 1, col, sname)
        # Enforce minimum number of columns
        while col < 18:
            col = table.nextcol()
            table.write(rowix, col, "")
        # Delete excess columns
        table.delEndCols(col + 1)
        ### Add pupils
        for pid, gmap in self.items():
            row = table.nextrow()
            table.write(row, 0, pid)
            table.write(row, 1, self.name[pid])
            table.write(row, 2, gmap.stream)
            for sid, col in sidcol:
                g = gmap.get(sid)
                if g:
                    table.write(row, col, g)
        # Delete excess rows
        row = table.nextrow()
        table.delEndRows(row)
        ### Save file
        table.protectSheet()
        return table.save()

    #
    def save(self, changes=None):
        """Save the data to the "database".
        <changes> is a mapping: {tag -> value}
        """
        try:
            grades_d = changes["GRADES_D"]
        except:
            grades_d = self.grades_d
        try:
            issue_d = changes["ISSUE_D"]
        except:
            issue_d = self.issue_d
        fields = ["PID", "PUPIL", "STREAM"]
        for sid in self.subjects:
            fields.append(sid)
        # for comp in self.composites:
        #    fields.append(comp)
        for xsid in self.extras:
            fields.append(xsid)
        # The calculated fields are not saved.
        # Get line data
        dlist = []
        for pid, grades in self.items():
            dmap = {
                "PID": pid,
                "PUPIL": self.name[pid],
                "STREAM": grades.stream,
            }
            dmap.update(grades)
            dlist.append(dmap)
        suffix = ".xlsx" if USE_XLSX else ".tsv"
        # Get file path and write file
        table_path = year_path(
            self.schoolyear, GradeBase.table_path(self.group, self.term)
        )
        if self.term[0] in ("S", "T"):
            # TODO: check validity of date?
            if issue_d == "*":
                raise FailedSave(_NO_DATE)
            if self.term[1:] != issue_d:
                # Date-of-issue – and thus also "term" – changed
                new_term = self.term[0] + issue_d
                table_path_new = year_path(
                    self.schoolyear, GradeBase.table_path(self.group, new_term)
                )
                if os.path.isfile(table_path_new + suffix):
                    raise FailedSave(_DATE_EXISTS)
                xfile = table_path + suffix
                if os.path.isfile(xfile):
                    os.remove(xfile)
                self.term = new_term
                table_path = table_path_new
        info = (
            ("SCHOOLYEAR", self.schoolyear),
            ("GROUP", self.group),
            ("TERM", self.term),
            ("GRADES_D", grades_d),
            ("ISSUE_D", issue_d),
        )
        # "Title"
        dt = datetime.datetime.now().isoformat(sep=" ", timespec="minutes")
        bstream = make_db_table(dt, fields, dlist, info=info)  # "title"
        tpdir = os.path.dirname(table_path)
        os.makedirs(tpdir, exist_ok=True)
        tfile = table_path + suffix
        with open(tfile, "wb") as fh:
            fh.write(bstream)
        return tfile

    #
    def recalc(self, pid):
        """Calculate the values for the "Calc" fields.
        Return a list: [(sid, val), ... ]
        """
        svlist = []
        for sid in self.calcs:
            if sid == ".D":
                svlist.append((sid, self.average(pid)))
            elif sid == ".Dx":
                svlist.append((sid, self.average_dem(pid)))
            elif sid == ".Q":
                try:
                    _ac = self[pid].abicalc
                except AttributeError:
                    pass
                else:
                    _amap = _ac.calculate()
                    svlist.append((sid, _amap["REPORT_TYPE"]))
        return svlist

    #
    def average(self, pid):
        """Calculate the average of all grades, including composites,
        but ignoring components and non-numerical grades.
        """
        asum = 0
        ai = 0
        grades = self[pid]
        for sid in self.subjects:
            if self.sid2subject_data[sid].composite:
                # A component
                continue
            gi = grades.i_grade[sid]
            if gi >= 0:
                asum += gi
                ai += 1
        for sid in self.composites:
            gi = grades.i_grade[sid]
            if gi >= 0:
                asum += gi
                ai += 1
        if ai:
            return Frac(asum, ai).round(2)
        else:
            return "–––"

    #
    def average_dem(self, pid):
        """Special average for "Realschulabschluss": De-En_Ma only."""
        asum = 0
        ai = 0
        grades = self[pid]
        for sid in ("De", "En", "Ma"):
            gi = grades.i_grade[sid]
            if gi >= 0:
                asum += gi
                ai += 1
        if ai:
            return Frac(asum, ai).round(2)
        else:
            return "–––"


def calculateGrades(gradetable: dict) -> None:
    """Add the calculated fields (subject tag '$...') to the grade data.
    Initially only the calculation of averages is supported – with
    various rounding choices.
    Further calculations may be added as "local" extensions for handling
    specific subject tags.
    """
    # todo
    pass


# ? I alread have rawGradeTableFile to read a raw table.
class GradeTableFile(_GradeTable):
    def __init__(self, schoolyear, filepath, full_table=True):
        """Read the header info and pupils' grades from the given table file.
        The "spreadsheet" module is used as backend so .ods, .xlsx and .tsv
        formats are possible. The filename may be passed without extension –
        <Spreadsheet> then looks for a file with a suitable extension.
        <Spreadsheet> also supports in-memory binary streams (io.BytesIO)
        with attribute 'filename' (so that the type-extension can be read).
        The <info> mapping of the table should contain the keys:
            'SCHOOLYEAR', 'GROUP', 'TERM', 'ISSUE_D', 'GRADES_D'
        If <full_table> is true, all grade information will be included,
        including calculations where appropriate. Otherwise, only the
        non-empty cells from the source table will be included.
        """
        super().__init__(schoolyear)
        #        ss = Spreadsheet(filepath)
        #        self.filepath = ss.filepath
        #        dbt = ss.dbTable()
        dbt = read_DataTable(filepath)
        dbt = filter_DataTable(
            dbt,
            MINION(DATAPATH("CONFIG/GRADE_DATA")),
            matrix=True,
            extend=False,
        )
        # print("????", dbt)
        return

        # ?
        info = {row[0]: row[1] for row in dbt.info if row[0]}
        self.issue_d = info.get(_ISSUE_D)
        self.grades_d = info.get(_GRADES_D)
        self._set_group_term(
            info.get(_GROUP), GradeBase.text2term(info.get(_TERM), self.issue_d)
        )
        year = info.get(_SCHOOLYEAR)
        if year != str(self.schoolyear):
            raise GradeTableError(
                _TABLE_YEAR_MISMATCH.format(filepath=filepath)
            )
        sid2col = []
        col = 0
        for f in dbt.fieldnames():
            if col > 2:
                if f[0] != "$":
                    # This should be a subject tag
                    if f in self.subjects or f in self.extras:
                        sid2col.append((f, col))
                    else:
                        REPORT(
                            "WARNING",
                            _WARN_EXTRA_SUBJECT.format(
                                sid=f, tfile=self.filepath
                            ),
                        )
            col += 1
        if full_table:
            self._readtable(dbt, sid2col)
        else:
            # Only include non-empty cells from the source table
            for row in dbt:
                pid = row[0]
                if pid and pid != "$":
                    gmap = {}
                    for sid, col in sid2col:
                        val = row[col]
                        if val:
                            gmap[sid] = val
                    self.name[pid] = row[1]
                    self[pid] = gmap


gtable_info = namedtuple(
    "gtable_info", ("schoolyear", "group", "term", "filepath")
)


class NewGradeTable(_GradeTable):
    """An empty grade table."""

    def __init__(self, schoolyear, group, term, pids=None):
        """If <pids> is supplied it should be a list of pupil ids: only
        these pupils will be included in the new table.
        """
        super().__init__(schoolyear)
        self._set_group_term(group, term)
        self._new_group_table(pids)


###


class __GradeTable(_GradeTable):
    def __init__(self, schoolyear, group, term, ok_new=False):
        """If <ok_new> is true, a new table may be created, otherwise
        the table must already exist.
        """
        super().__init__(schoolyear)
        self._set_group_term(group, term)
        # Get file path
        table_path = year_path(schoolyear, GradeBase.table_path(group, term))
        try:
            # Read the "internal" table for this group/term
            ss = Spreadsheet(table_path)
        except TableError:
            # File doesn't exist
            if not ok_new:
                raise
            self._new_group_table(None)
            return

        dbt = ss.dbTable()
        info = {row[0]: row[1] for row in dbt.info if row[0]}
        gtable = gtable_info(
            info.get("SCHOOLYEAR"),
            info.get("GROUP"),
            info.get("TERM"),
            table_path,
        )
        self.check_group_term(gtable)
        self.issue_d = info.get("ISSUE_D")
        self.grades_d = info.get("GRADES_D")
        sid2col = []
        col = 0
        for f in dbt.fieldnames():
            if col > 2:
                if f[0] != "$":
                    # This should be a subject tag
                    sid2col.append((f, col))
            col += 1
        self._readtable(dbt, sid2col)

    #
    def check_group_term(self, gtable):
        """Check that year, group and term in <gtable> match those of
        the current instance.
        """
        if gtable.schoolyear != self.schoolyear:
            raise GradeTableError(
                _TABLE_YEAR_MISMATCH.format(filepath=gtable.filepath)
            )
        if gtable.group != self.group:
            raise GradeTableError(
                _TABLE_CLASS_MISMATCH.format(filepath=gtable.filepath)
            )
        if gtable.term != self.term:
            raise GradeTableError(
                _TABLE_TERM_MISMATCH.format(filepath=gtable.filepath)
            )

    #
    def integrate_partial_data(self, *gtables):
        """Include the data from the given (partial) tables.
        - Only non-empty source table fields will be used for updating.
        - Check validity of pupils and subjects (warn if mismatch).
        - Only update empty fields (warn if there are attempts to overwrite).
        """
        tfiles = {}  # {pid:sid -> table file} (keep track of sources)
        for gtable in gtables:
            # Check year, group, term
            self.check_group_term(gtable)
            for pid, grades in gtable.items():
                try:
                    pgrades = self[pid]
                except KeyError:
                    REPORT(
                        "WARNING",
                        _WARN_EXTRA_PUPIL.format(
                            name=gtable.name[pid], tfile=gtable.filepath
                        ),
                    )
                    continue
                for sid, g in grades.items():
                    g0 = pgrades[sid]
                    key = "%s:%s" % (pid, sid)
                    tfile1 = tfiles.get(key)
                    tfile2 = gtable.filepath
                    tfiles[key] = tfile2
                    if g != g0:
                        if (not g0) and tfile1:
                            REPORT(
                                "ERROR",
                                _ERROR_OVERWRITE.format(
                                    sid=sid,
                                    name=gtable.name[pid],
                                    tfile1=tfile1,
                                    tfile2=tfile2,
                                ),
                            )
                            continue  # don't update
                        pgrades[sid] = g
        # A "recalc" should not be necessary if the grade file is
        # reloaded after saving – which is the expected usage.
        # Otherwise the calculations should probably be redone:
        # for pid in self:
        #    self.recalc(pid)
        self.save()


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    _GRADE_DATA = MINION(DATAPATH("CONFIG/GRADE_DATA"))
    _filepath = DATAPATH("testing/Noten/NOTEN_1/Noten_12G.G_1")
    _filepath = DATAPATH("testing/Noten/NOTEN_1/Noten_12G.R_1")
    _gdata = readGradeFile(_filepath, check_complete=True)
    for key, val in _gdata.items():
        print(f"\n** {key}: {repr(val)}")
    print("\n ... complete grade table")
    _cgtable = GradeTable(_gdata)
    for pgdata in _cgtable.pupils_grade_data:
        print("\n???X", pgdata.pid, pgdata.name)
        for sid, smap in pgdata.pupil_subjects.items():
            print(f"§§§ {sid}: {repr(smap)}")
        print("\n--- COMPOSITES:", pgdata.composites)
        print("\n--- CALCS:", pgdata.calcs)
        print("\n--- GRADES:", pgdata.grades)

        pgdata.calculate()
    #    _gdata = read_DataTable(_filepath)
    #    _gdata = filter_DataTable(_gdata, _GRADE_DATA, matrix=True, extend=False)
    quit(0)

    _group = "12G.G"
    #    _group = "12G.R"
    #    _group = "10G"
    _tbytes = makeGradeTable(term="1", group=_group)
    #        ISSUE_D: Optional[str] = None,
    #        GRADES_D: Optional[str] = None)

    _tpath = DATAPATH(f"testing/tmp/GradeTable-{_group}.xlsx")
    _tdir = os.path.dirname(_tpath)
    if not os.path.isdir(_tdir):
        os.makedirs(_tdir)
    with open(_tpath, "wb") as _fh:
        _fh.write(_tbytes)
    print(f"\nWROTE GRADE TABLE TO {_tpath}\n")

    _fr = Frac(123456, 10000)
    print(f"Truncate {_fr.round(5)}: {_fr.truncate(2)}")
    print(f"Round {_fr.round(5)}: {_fr.round(2)}")

    quit(0)

    if True:
        #    if False:
        _filepath = DATAPATH("testing/Noten/NOTEN_A/Noten_13_A")
        _gtable = GradeTableFile(SCHOOLYEAR, _filepath)
        print("SUBJECTS:", _gtable.subjects)
        print("GROUP:", _gtable.group)
        print("TERM:", _gtable.term)
        print("YEAR:", _gtable.schoolyear)
        print("ISSUE_D:", _gtable.issue_d)
        print("GRADES_D:", _gtable.grades_d)
        print("NAMES:", _gtable.name)
        print("COMPOSITES:", _gtable.composites)
        print("COMPONENTS:", _gtable.components)
        print("EXTRAS:", _gtable.extras)
        print("CALCS:", _gtable.calcs)
        for _pid, _gdata in _gtable.items():
            print("???", _pid, _gdata.stream, _gdata)

    if True:
        #    if False:
        _group = "12.G"
        _term = "2"
        print("\n\nGRADE TABLE for %s, term %s" % (_group, _term))
        _gtable = GradeTable(_schoolyear, _group, _term, ok_new=True)
        print("SUBJECTS:", _gtable.subjects)
        print("GROUP:", _gtable.group)
        print("TERM:", _gtable.term)
        print("YEAR:", _gtable.schoolyear)
        print("ISSUE_D:", _gtable.issue_d)
        print("GRADES_D:", _gtable.grades_d)
        print("NAMES:", _gtable.name)
        for _pid, _gdata in _gtable.items():
            print("???", _pid, _gdata.stream, _gdata)

    if True:
        #    if False:
        _group = "11.G"
        _term = "S2016-03-01"
        print("\n\nGRADE TABLE for %s, term %s" % (_group, _term))
        _gtable = GradeTable(_schoolyear, _group, _term, ok_new=True)
        print("SUBJECTS:", _gtable.subjects)
        print("GROUP:", _gtable.group)
        print("TERM:", _gtable.term)
        print("YEAR:", _gtable.schoolyear)
        print("ISSUE_D:", _gtable.issue_d)
        print("GRADES_D:", _gtable.grades_d)
        print("NAMES:", _gtable.name)
        for _pid, _gdata in _gtable.items():
            print("???", _pid, _gdata.stream, _gdata)
        print("INTERNAL: -->", _gtable.save())

    quit(0)

    if True:
        # Read all existing test tables into the internal form
        #    if False:
        odir = os.path.join(DATA, "testing", "tmp")
        os.makedirs(odir, exist_ok=True)
        from glob import glob

        _filepath = os.path.join(DATA, "testing", "NOTEN", "NOTEN_*", "Noten_*")
        for f in sorted(glob(_filepath)):
            _gtable = GradeTableFile(_schoolyear, f)
            print("READ", f)
            fname = os.path.basename(f)
            xlsx_bytes = _gtable.make_grade_table()
            tfile = os.path.join(odir, fname.rsplit(".", 1)[0] + ".xlsx")
            with open(tfile, "wb") as fh:
                fh.write(xlsx_bytes)
                print("OUT:", tfile)
            print("INTERNAL: -->", _gtable.save())
