"""
grades/makereports.py

Last updated:  2022-12-25

Generate the grade reports for a given group and "occasion" (term,
semester, special, ...).
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
_MULTI_GRADE_GROUPS = "Fach {sbj} passt zu mehr als eine Fach-Gruppe"

###############################################################

import sys, os

if __name__ == "__main__":
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))

T = TRANSLATIONS("grades.makereports")

### +++++

from core.base import Dates
#from core.pupils import Pupils
#from core.courses import Subjects, UNCHOSEN, NULL

# from local.base_config import year_path, \
#        print_schoolyear, LINEBREAK
#from local.local_grades import class_year

# from local.grade_config import UNCHOSEN, MISSING_GRADE, NO_GRADE, UNGRADED, \
#        GradeConfigError, NO_SUBJECT
# from local.grade_template import info_extend
from template_engine.template_sub import Template, TemplateError
from grades.gradetable import full_grade_table, get_grade_config
from local.grade_functions import process_grade_data

### -----


def make_reports(occasion, class_group, instance):
    """The resulting pdfs will be combined into a single pdf-file for
    each report type. If the reports are double-sided, empty pages
    are added as necessary.
    Return a list of file-paths for the report-type pdf-files.
    """
    grade_info = full_grade_table(occasion, class_group, instance)
    # Fields:
    # OCCASION, CLASS_GROUP, INSTANCE,
    # SUBJECTS,
    # COMPONENTS,
    # COMPOSITES,
    # EXTRAS,
    # GRADES,
    # GRADE_ENTRY,
    # PUPILS,           // {pid: (pdata, {sid: {tid, ...}}), ...}
    # DATE_ISSUE,
    # DATE_GRADES,
    # MODIFIED,
    # ALL_SIDS,         // {sid: sdata, ...}
    #                   // sdata contains SID, NAME, [GROUP,] etc.
    # PUPIL_GRADES,
    # GRADE_TABLE_PUPILS,
    # SYMBOLS

    # I can get the template path via the REPORT_TYPE "grade" for each pupil.
    # grade_info["ALL_SIDS"]["REPORT_TYPE"]["VALUES"] is a list of [key
    # path] pairs.

    ### Divide the subjects into groups
    subject_groups = {}
    for sdata in grade_info["ALL_SIDS"].values():
        try:
            group = sdata["GROUP"]
        except KeyError:
            continue
        try:
            subject_groups[group].append(sdata)
        except KeyError:
            subject_groups[group] = [sdata]
#    print("\n$$$$$$$$$ GROUPED SUBJECTS:")
#    for group, slist in subject_groups.items():
#        print("  ***", group)
#        for sdata in slist:
#            print("        ---", sdata)

    ### Divide the pupils according to report type
    rtypes = {}
    for pid, data in grade_info["PUPILS"].items():
        pdata, stdata = data
        #print("\n", pdata)
        #print("  ---", stdata)
        pid = pdata["PID"]

#TODO: Also need data from GRADES_INFO table
        grades = grade_info["PUPIL_GRADES"][pid]
        #print("  ***", grades)
        rtype = grades["REPORT_TYPE"]
        try:
            rtypes[rtype].append(pid)
        except KeyError:
            rtypes[rtype] = [pid]

    ### Build reports for each report-type separately
    rtype_path = dict(grade_info["ALL_SIDS"]["REPORT_TYPE"]["VALUES"])
    path_list = [
        build_report_type(
            rtype,
            pid_list,
            rtype_path,
            subject_groups,
            grade_info
        )
        for rtype, pid_list in rtypes.items()
    ]

#TODO
    return

    if x:
        if y:
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
#            gmap["STREAM"] = grades.stream
#            gmap["SekII"] = grades.sekII
#            comment = grades.pop("*B", "")
#            if comment:
#                comment = comment.replace(LINEBREAK, "\n")
#            gmap["COMMENT"] = comment

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



        _tg = prepare_report_data(rtype, pid_list)
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



def build_report_type(
    rtype: str,
    pid_list: list[str],
    rtype_path: dict[str,str],
    subject_groups: dict[str,list[str]],
    grade_info: dict
) -> str:
    """Build grade reports of the given type (<rtype>) for the given
    pupils (<pid_list>).
    """
    try:
        tpath = rtype_path[rtype]
    except KeyError:
        REPORT(
            "ERROR",
            T["INVALID_REPORT_TYPE"].format(
                rtype=rtype, pids=", ".join(pid_list)
            )
        )
        return ""
    print("\nTEMPLATE:", rtype, tpath, pid_list)
    template = Template(tpath)
    all_keys = template.all_keys()
    subjects, tagmap = group_grades(all_keys)
    print("\n§§§ SUBJECTS:", subjects)
    print("\n§§§ TAGMAP:", tagmap)

    ## Template field/value processing
    metadata = template.metadata()
    template_field_info = metadata.get("FIELD_INFO") or {}
    grade_map = template_field_info.get("GRADE_MAP") or {}
    print("\nGRADE MAP:", grade_map)

    ## Transform subject groups?
    try:
        gmap = template_field_info["GROUP_MAP"]
    except KeyError:
        sgroups = subject_groups
    else:
        sgroups = {}
        for g, slist in subject_groups.items():
            try:
                g1 = gmap[g]
            except KeyError:
                REPORT("ERROR", T["UNKNOWN_SUBJECT_GROUP"].format(
                    path=template.template_path , group=g
                ))
                continue
            if not g1:
                continue    # these subjects are not shown
            try:
                sgroups[g1] += slist
            except KeyError:
                sgroups[g1] = slist.copy()
    print("\nSUBJECT GROUPS:", sgroups)

    ## Build the data mappings and generate the reports
    date_format = (
        template_field_info.get("DATEFORMAT") or CONFIG["DATEFORMAT"]
    )
    base_data = {
        "SCHOOL": CONFIG["SCHOOL_NAME"],
        "SCHOOLBIG": CONFIG["SCHOOL_NAME"].upper(),
        "SCHOOLYEAR": CALENDAR["~SCHOOLYEAR_PRINT"],
        "DATE_ISSUE": grade_info["DATE_ISSUE"],
        "DATE_GRADES": grade_info["DATE_GRADES"],
    }
    base_data.update(grade_info["SYMBOLS"])
    gmaplist = []
    for pid in pid_list:
        rptdata = base_data.copy()
        data = grade_info["PUPILS"][pid]
        rptdata.update(data[0])
        rptdata.update(grade_info["PUPIL_GRADES"][pid])
        sort_grade_keys(rptdata, subjects, tagmap, sgroups, grade_map)
        # Locality-specific processing:
        process_grade_data(rptdata, grade_info, get_grade_config())

        # Format dates
        for k, v in rptdata.items():
            if k.startswith("DATE_"):
                if v:
                    v = Dates.print_date(v, date_format)
                else:
                    v = ""
                rptdata[k] = v

#TODO ...
        print("\n**** CHECK FIELDS ****")
        for k in all_keys:
            if k in rptdata:
                print(f"$$$$$$$$ {k:<20}", rptdata[k])
            else:
                print(f"-------- {k:<20}")
        for k in rptdata:
            if k not in all_keys:
                print(f"+++++++++ {k:<20}", rptdata[k])
        gmaplist.append(rptdata)

#        print("\n ====>", grades)

#TODO ...
    return ""




#??????????????????
def prepare_report_data(rtype, pid_list):
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
        REPORT("ERROR", T["BAD_REPORT_TYPE"].format(rtype=rtype))
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


def group_grades(all_keys: set[str]) -> tuple[set[str], dict[str, list[str]]]:
    """Determine the subject and grade slots in the template.
    <all_keys> is the complete set of template slots/keys.
    Keys of the form 'G.k.n' are sought: k is the group-tag, n is a number.
    Return a mapping {group-tag -> [index, ...]}.
    The index lists are sorted reverse-alphabetically (for popping).
    Note that the indexes are <str> values, not <int>.
    Also keys of the form 'g.sid' are collected as a set..
    """
    #    G_REGEXP = re.compile(r'G\.([A-Za-z]+)\.([0-9]+)$')
    tags: dict[str, list[str]] = {}
    subjects: set[str] = set()
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


def sort_grade_keys(rptdata, subjects, tagmap, sgroups, grade_map):
    """Remap the subject/grade data to fill the keyed slots in the
    report template.
    <rptdata>: the data mapping, {sid: value, ...}
    <subjects>: the set of template tags of the form "g.sid"
    <tagmap>: a mapping to subject group to available tag indexes,
        {subject-group: [index, ...], ...}
        The indexes are in "reverse" order, so that popping them
        produces increasing values.
    <grade_map>: {grade: print form of grade, ...}
    The mapping <rptdata> is modified to include the results.
    """
    def print_grade(grade):
        try:
            return grade_map[grade]
        except KeyError:
            if grade:
                REPORT("ERROR", T["BAD_GRADE"].format(sid=sid, grade=grade))
                return "?"
            return ""
    NOGRADE = print_grade("/")

    for sid in subjects:
        try:
            g = rptdata.pop(sid)
        except KeyError:
            REPORT("WARNING", T["MISSING_SUBJECT_GRADE"].format(sid=sid))
            g = '/'
        rptdata[f"g.{sid}"] = print_grade(g)

    for tag, sdata_list in sgroups.items():
        keys = tagmap[tag].copy()
        for sdata in sdata_list:
            sid = sdata["SID"]
            try:
                g = rptdata.pop(sid)
            except KeyError:
                continue
            try:
                k = keys.pop()
            except IndexError:
                REPORT("ERROR", T["TOO_FEW_KEYS"].format(tag=tag))
                continue
            rptdata[f"G.{tag}.{k}"] = print_grade(g)
            rptdata[f"S.{tag}.{k}"] = sdata["NAME"]

        for k in keys:
            rptdata[f"G.{tag}.{k}"] = NOGRADE
            rptdata[f"S.{tag}.{k}"] = NOGRADE


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from core.db_access import open_database
    open_database()
    make_reports("1. Halbjahr", "12G.R", "")

    quit(0)

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

