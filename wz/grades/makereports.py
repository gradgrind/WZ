"""
grades/makereports.py

Last updated:  2022-01-23

Generate the grade reports for a given group and "term".
Fields in template files are replaced by the report information.

In the templates there are grouped and numbered slots for subject names
and the corresponding grades.

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

# TODO: Sonderzeugnisse

# TODO: Maybe also "Sozialverhalten" und "Arbeitsverhalten"
# TODO: Praktika? e.g.
#       Vermessungspraktikum:   10 Tage
#       Sozialpraktikum:        3 Wochen
# TODO: Maybe component courses (& eurythmy?) merely as "teilgenommen"?

_REPORT_TYPE_FIELD = "*ZA"

## Messages
_INVALID_SUBJECT_KEY = "Ungültiges Fach-Feld in Vorlage: {key}"
_BAD_GRADE = "Ungültige Note ({grade}) im Fach {sid}"
_NO_GRADE = "Keine Note im Fach {sid}"
_NO_SUBJECT_GROUP = "Fach {sid}: Fach-Gruppe {group} nicht in Vorlage"

_NOT_COMPLETE = "Daten für {pupil} unvollständig"
_NO_REPORT_TYPE = "Kein Zeugnistyp für Schüler {pids}"
_MULTI_GRADE_GROUPS = "Fach {sbj} passt zu mehr als eine Fach-Gruppe"
#_NO_GRADE = "Schüler {pname}: keine Note im Fach {sbj}"
_UNEXPECTED_GRADE_GROUP = (
    "Ungültiger Fachgruppe ({tag}) in Vorlage:\n" "  {tpath}"
)
_NO_SLOT = (
    "Kein Platz mehr für Fach mit Kürzel {sid} in Fachgruppe {tag}."
    " Bisher: {done}"
)
_BAD_REPORT_TYPE = "Ungültiger Zeugnistyp: '{rtype}'"

###############################################################

import sys, os
from typing import List, Dict, Set, Tuple

if __name__ == "__main__":
    # Enable package import if running as module
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

from typing import Dict, List  # , Optional, Any, Set, Tuple

from core.base import Dates, class_group_split
from core.pupils import Pupils
from core.courses import Subjects, UNCHOSEN, NULL

# from local.base_config import year_path, \
#        print_schoolyear, LINEBREAK
from local.local_grades import class_year

# from local.grade_config import UNCHOSEN, MISSING_GRADE, NO_GRADE, UNGRADED, \
#        GradeConfigError, NO_SUBJECT
# from local.grade_template import info_extend
from template_engine.template_sub import Template, TemplateError
from grades.gradetable import readGradeFile, GradeTable  # , GradeTableError


class GradeReports:
    """Generate the grade reports for a group of pupils based on the
    information provided in a <GradeTable> instance.
    The group must be a valid grade-report group (which can be a class
    name or a class name with a group tag, e.g. '12.G') – the valid
    groups are specified (possibly dependant on the term) in the
    GRADE_GROUP_INFO configuration file.
    """

    def __init__(self, gradetable: GradeTable):
        self.grade_table = gradetable
        # TODO: type of dict?
        self.gmap0: Dict[str, str] = {
            ## data shared by all pupils in the group
            "GROUP": self.grade_table.group,
            "TERM": self.grade_table.term,
            "CYEAR": class_year(self.grade_table.group),
            "issue_d": self.grade_table.issue_date,  # for file-names
            "ISSUE_D": Dates.print_date(
                self.grade_table.issue_date, trap=False
            ),
            "GRADES_D": Dates.print_date(
                self.grade_table.grades_date, trap=False
            ),
            "SCHOOL": CONFIG["SCHOOL_NAME"],
            "SCHOOLBIG": CONFIG["SCHOOL_NAME"].upper(),
            "schoolyear": SCHOOLYEAR,
            "SCHOOLYEAR": CALENDAR["~SCHOOLYEAR_PRINT"],
        }

    #
    def makeReports(self):
        """The resulting pdfs will be combined into a single pdf-file for
        each report type. If the reports are double-sided, empty pages
        can be added as necessary.
        Return a list of file-paths for the report-type pdf-files.
        """
        group_info = MINION(DATAPATH("CONFIG/GRADE_GROUP_INFO"))
        # template = get_group_info(group_info, group, "GradeTableTemplate")

        greport_type = {}
        no_report_type = []
        for pupilGradeData in self.grade_table.pupils_grade_data:

            # ?            # <forGroupTerm> accepts only valid grade-groups.
            if self.grade_table.term == "A":
                rtype = grades.abicalc.calculate()["REPORT_TYPE"]
                if not rtype:
                    REPORT(
                        "ERROR",
                        _NOT_COMPLETE.format(pupil=self.grade_table.name[pid]),
                    )
            else:
                # Split group according to report type
                rtype = grades.get(_REPORT_TYPE_FIELD, "-")
            if rtype:
                try:
                    greport_type[rtype].append(pid)
                except KeyError:
                    greport_type[rtype] = [pid]
            else:
                no_report_type.append(pid)

        if no_report_type:
            raise GradeTableError(
                _NO_REPORT_TYPE.format(pids=", ".join(no_report_type))
            )

        ### Build reports for each report-type separately
        fplist = []
        for rtype, pid_list in greport_type.items():
            if rtype == "-":
                continue  # Skip these pupils
            _tg = self.prepare_report_data(rtype, pid_list)
            if _tg:
                template, gmaplist = _tg
                # make_pdf: data_list, dir_name, working_dir, double_sided
                fplist.append(
                    template.make_pdf(
                        gmaplist,
                        grades.report_name(
                            group=self.grade_table.group,
                            term=self.grade_table.term,
                            rtype=rtype,
                        ),
                        year_path(
                            self.grade_table.schoolyear,
                            grades.REPORT_DIR.format(
                                term=self.grade_table.term
                            ),
                        ),
                        double_sided=grades.double_sided(
                            self.grade_table.group, rtype
                        ),
                    )
                )
        return fplist

    #
    def prepare_report_data(self, rtype, pid_list):
        """Prepare the slot-mappings for report generation.
        Return a tuple: (template object, list of slot-mappings).
        """
        ### Pupil data
        pupils = Pupils(self.grade_table.schoolyear)
        # The individual pupil data can be fetched using pupils[pid].
        # Fetching the whole class may not be good enough, as it is vaguely
        # possible that a pupil has changed class.
        # The subject data is available at <self.grade_table.subjects>
        # and <self.sid2subject_data>.
        ### Grade report template
        try:
            template_tag = Grades.report_template(self.grade_table.group, rtype)
        except GradeConfigError:
            REPORT("ERROR", _BAD_REPORT_TYPE.format(rtype=rtype))
            return None
        gTemplate = Template(template_tag)
        ### Build the data mappings and generate the reports
        gmaplist = []
        for pid in pid_list:
            gmap = self.gmap0.copy()
            # Get pupil data
            pdata = pupils[pid]
            # could just do gmap[k] = pdata[k] or '' and later substitute all dates?
            for k in pdata.keys():
                v = pdata[k]
                if v:
                    if k.endswith("_D"):
                        v = Dates.print_date(v)
                else:
                    v = ""
                gmap[k] = v
            grades = self.grade_table[pid]
            # Grade parameters
            gmap["STREAM"] = grades.stream
            gmap["SekII"] = grades.sekII
            comment = grades.pop("*B", "")
            if comment:
                comment = comment.replace(LINEBREAK, "\n")
            gmap["COMMENT"] = comment

            ## Process the grades themselves ...
            if self.grade_table.term == "A":
                showgrades = {
                    k: UNGRADED if v == NO_GRADE else v
                    for k, v in grades.abicalc.tags.items()
                }
                gmap.update(showgrades)
                gmap.update(grades.abicalc.calculate())
            else:
                # Sort into grade groups
                grade_map = self.sort_grade_keys(
                    pdata.name(), grades, gTemplate
                )
                gmap.update(grade_map)
                gmap["REPORT_TYPE"] = rtype

            ## Add template and "local" stuff
            info_extend(gmap)
            gmaplist.append(gmap)

        return (gTemplate, gmaplist)

    #
    def sort_grade_keys(self, name, grades, template):
        """Allocate the subjects and grades to the appropriate slots in the
        template.
        Return a {slot: grade-entry} mapping.
        <grades> is the <Grades> instance,
        <template> is a <Template> (or subclass) instance.
        """
        _grp2indexes = group_grades(template.all_keys())
        for rg in grades.group_info(self.grade_table.group, "Nullgruppen"):
            _grp2indexes[rg] = None
        sbj_grades = _grp2indexes[None]  # "direct" grade slots
        gmap = {}  # for the result
        for sid, grade in grades.items():
            # Get the print representation of the grade
            if sid[0] == "*":
                gmap[sid] = grade
                continue
            g = grades.print_grade(grade)
            if sbj_grades:
                try:
                    sbj_grades.remove(sdata.sid)
                except KeyError:
                    pass
                else:
                    # grade-only entry
                    gmap["G.%s" % sdata.sid] = g or UNGRADED
                    continue
            if grade == UNCHOSEN:
                continue
            # Get the subject data
            sdata = self.grade_table.sid2subject_data[sid]
            if g == MISSING_GRADE:
                REPORT("WARN", _NO_GRADE.format(pname=name, sbj=sdata.name))
            if not g:
                # Subject "not chosen", no report entry
                continue
            done = False
            for rg in sdata.report_groups:
                # Get an index
                try:
                    ilist = _grp2indexes[rg]
                except KeyError:
                    continue
                if done:
                    raise GradeConfigError(_MULTI_GRADE_GROUPS.format(sbj=sbj))
                done = True
                if ilist == None:
                    # Suppress subject/grade
                    continue
                try:
                    i = ilist.pop()
                except IndexError as e:
                    # No indexes left
                    raise TemplateError(
                        _NO_SLOT.format(tag=rg, sid=sdata.sid, done=repr(gmap))
                    ) from e
                gmap["G.%s.%s" % (rg, i)] = g
                # For the name, strip possible extra bits, after '|':
                gmap["S.%s.%s" % (rg, i)] = sdata.name.split("|", 1)[0].rstrip()
            if not done:
                raise GradeConfigError(_NO_SUBJECT_GROUP.format(sbj=sdata.name))
        # Fill unused slots
        if sbj_grades:
            for sid in sbj_grades:
                gmap["G.%s" % sid] = UNGRADED
        for tag, ilist in _grp2indexes.items():
            if ilist:
                for i in ilist:
                    gmap["G.%s.%s" % (tag, i)] = NO_SUBJECT
                    gmap["S.%s.%s" % (tag, i)] = NO_SUBJECT
        return gmap


###


def group_grades(all_keys: Set[str]) -> Tuple[Set[str], Dict[str, List[str]]]:
    """Determine the subject and grade slots in the template.
    <all_keys> is the complete set of template slots/keys.
    Keys of the form 'G.k.n' are sought: k is the group-tag, n is a number.
    Return a mapping {group-tag -> [index, ...]}.
    The index lists are sorted reverse-alphabetically (for popping).
    Note that the indexes are <str> values, not <int>.
    Also keys of the form 'g.sid' are collected as a set..
    """
    #    G_REGEXP = re.compile(r'G\.([A-Za-z]+)\.([0-9]+)$')
    tags: Dict[str, List[str]] = {}
    subjects: Set[str] = set()
    for key in all_keys:
        if key.startswith("G."):
            # G.<group tag>.<index>
            try:
                tag, index = key[2:].rsplit(".", 1)
            except ValueError:
                raise GradeReportError(_INVALID_SUBJECT_KEY.format(key=key))
            try:
                tags[tag].add(index)
            except KeyError:
                tags[tag] = {index}
        elif key.startswith("g."):
            # g.<subject tag>
            subjects.add(key[2:])
    tagmap: Dict[str, List[str]] = {
        tag: sorted(ilist, reverse=True) for tag, ilist in tags.items()
    }
    return subjects, tagmap


def sort_grade_keys(
    grades: List[Tuple[str, str, str]], # [(sid, sgroup, grade), ... ]
    template: Template
) -> Dict[str, str]:
    """Allocate the subjects and grades to the appropriate slots in the
    template.
    The grade list should be ordered and contain all subjects relevant
    for the pupil, possibly including UNCHOSEN and NULL ones.
    Return a {template-field: grade-entry} mapping.
    """
    metafields = template.metadata()["FIELD_INFO"]
    print_grade = metafields.get("PRINT_GRADE")

    all_keys = template.all_keys()
    print("\n§§§", sorted(all_keys))
    sbj_grades, grp2indexes = group_grades(all_keys)
    gmap = {}  # for the result
    pgrade: str  # for the print-version of the grades
    subjects = Subjects()
    for sid, sgroup, grade in grades:
        # Get the print representation of the grade
        if print_grade:
            try:
                pgrade = print_grade[grade]
            except KeyError:
                pgrade = print_grade.get("?") or "???"
                REPORT("WARNING", (
                    _BAD_GRADE if grade else _NO_GRADE).format(sid=sid)
                )
        elif grade:
            pgrade = grade
        else:
            pgrade = "???"
            REPORT("WARNING", _NO_GRADE.format(sid=sid))

        try:
            sbj_grades.remove(sid)
        except KeyError:
            pass
        else:
            # grade-only entry
            gmap[f"g.{sid}"] = pgrade
            continue

        if grade == NULL:   # Subjects not available in the pupil's groups
            continue    # Don't include these

        ### Fill subject and grade fields according to subject group
        # Get an index
        try:
            ilist = grp2indexes[sgroup]
        except KeyError:
            REPORT("ERROR", _NO_SUBJECT_GROUP.format(sid=sid, group=sgroup))
            continue
        try:
            i = ilist.pop()
        except IndexError:
            # No indexes left
            raise TemplateError(_NO_SLOT.format(tag=sgroup, sid=sid))
        gmap[f"G.{sgroup}.{i}"] = pgrade
        # For the subject name, strip possible extra bits, after '|':
        gmap[f"S.{sgroup}.{i}"] = subjects.sid2name[sid].split("|", 1)[0].rstrip()
    # Fill unused slots
    UNGRADED = print_grade["/"]
    if sbj_grades:
        for sid in sbj_grades:
            gmap[f"g.{sid}"] = UNGRADED
    for tag, ilist in grp2indexes.items():
        if ilist:
            for i in ilist:
                gmap[f"G.{tag}.{i}"] = UNGRADED
                gmap[f"S.{tag}.{i}"] = UNGRADED
    return gmap


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    _t = Template('Noten/SekI')

    # Subjects().pupil_subjects(_pid, grades=True)
    # returns a dict, sid: subject-data. However, sid is also in the
    # subject-data dict.

    #_GRADE_DATA = MINION(DATAPATH("CONFIG/GRADE_DATA"))
    _group = "12G.R"
    _pid = "200401"
    _filepath = DATAPATH(f"testing/Noten/NOTEN_1/Noten_{_group}_1")
    _gdata = readGradeFile(_filepath)
    _pgrades = _gdata["__GRADEMAP__"][_pid]
    _s = Subjects()
    _c, _g = class_group_split(_group)
    _slist = _s.report_subjects(_c, grades=True)
    print("\n +++ _slist", _slist)
    _pmap = _s.pupil_subjects(_pid, grades=True)
    print("\n +++ _pmap", _pid, _pmap)

    _grades = []
    for _sid, _sname in _slist:
        try:
            _grades.append((_sid, _pmap[_sid]["SGROUP"],
                    _pgrades.get(_sid) or ""))
        except KeyError:
            pass
    print("\n +++ _grades", _grades)

    _gkeys = sort_grade_keys(_grades, _t)
    print("\n +++ _gkeys", _gkeys)
    quit(0)

    _cgtable = GradeTable(_gdata)
    _grade_reports = GradeReports(_cgtable)
    print("\nSHARED DATA:", _grade_reports.gmap0)

