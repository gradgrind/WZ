"""
grades/make_grade_reports.py

Last updated:  2023-04-11
Generate the grade reports for a given group and "occasion" (term,
semester, special, ...).
Fields in template files are replaced by the report information.

In the templates there are grouped and numbered slots for subject names
and the corresponding grades.

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

# TODO: Sonderzeugnisse

# TODO: Maybe also "Sozialverhalten" und "Arbeitsverhalten"
# TODO: Praktika? e.g.
#       Vermessungspraktikum:   10 Tage
#       Sozialpraktikum:        3 Wochen
# TODO: Maybe component courses (& eurythmy?) merely as "teilgenommen"?

### Regular expression for embedded expressions in symbol values:
###     {VALUE_KEY} or {FUNCTION:VALUE_KEY}
### VALUE_KEY can contain '/' characters, which act as separators
### so that keying of mappings and indexing of arrays is possible.
RE_VALUE_KEY = r'\{(?:([A-Za-z][A-Za-z0-9_]*):)?([A-Za-z0-9_./]+)\}'


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

import re
from core.base import Dates
from core.pupils import pupil_name
from template_engine.template_sub import Template
from grades.grades_base import FullGradeTable, GetGradeConfig
from local.grade_processing import ProcessGradeData, ReportName, NOGRADE

### -----


def MakeReports(full_grade_table, show_data=False) -> list[str]:
    """Make the reports for the given grade table.
    The resulting pdfs will be combined into a single pdf-file for
    each report type. If the reports are double-sided, empty pages
    are added as necessary.
    If <show_data> is true, additional debugging information will be
    shown.
    Return a list of file-paths for the report-type pdf-files.
    """
    ### Table fields:
        # OCCASION, CLASS_GROUP, INSTANCE,
        # SUBJECTS,
        # COLUMNS,
        # GRADE_VALUES,
        # GRADE_ENTRY,
        # DATE_ISSUE,
        # DATE_GRADES,
        # MODIFIED,
        # PUPIL_LIST,
        # SYMBOLS

    # I can get the template path via the REPORT_TYPE value for each pupil.
    # full_grade_table["COLUMNS"][type].get(["REPORT_TYPE"])["PARAMETERS"]["CHOICES"]
    # is a list of [key, path] pairs.

    ### Divide the subjects into groups
    subject_groups = {}
    column_lists = full_grade_table["COLUMNS"]
    for stype in ("SUBJECT", "COMPOSITE"):
        for sdata in column_lists[stype]:
            if (group := sdata["GROUP"]):
                try:
                    subject_groups[group].append(sdata)
                except KeyError:
                    subject_groups[group] = [sdata]
    ### Divide the pupils according to report type
    rtypes = {}
    for pdata, grades in full_grade_table["PUPIL_LIST"]:
        pid = pdata["PID"]
        # print("  ***", pupil_name(pdata), grades)
        rtype = grades["REPORT_TYPE"]
        try:
            rtypes[rtype].append(pid)
        except KeyError:
            rtypes[rtype] = [pid]
    ### Build reports for each report-type separately
    try:
        rtdata = column_lists["INPUT"].get("REPORT_TYPE")
    except KeyError:
        rtdata = column_lists["CALCULATE"].get("REPORT_TYPE")
    rtype_path = dict(rtdata["PARAMETERS"]["CHOICES"])
    fplist = []
    for rtype, pid_list in rtypes.items():
        try:
            tpath = rtype_path[rtype]
        except KeyError:
            if rtype:
                REPORT(
                    "ERROR",
                    T["INVALID_REPORT_TYPE"].format(
                        rtype=rtype, pids=", ".join(pid_list)
                    ),
                )
            else:
                REPORT(
                    "WARNING",
                    T["NO_REPORT_TYPE"].format(pids=", ".join(pid_list))
                )
            continue
        # print(f"\nTEMPLATE: '{rtype}' for {pid_list}\n  {tpath}")
        template = Template(tpath)
        gmaplist = collect_report_type_data(
            template, pid_list, subject_groups, full_grade_table, show_data
        )
        # make_pdf: data_list, dir_name, working_dir, double_sided
        pdf_path = template.make_pdf(
            gmaplist,
            ReportName(full_grade_table, rtype=rtype),
            DATAPATH("GRADES"),
            # TODO: get value from gui?
            double_sided=1,  # 1 => if number of pages odd and >1
        )
        fplist.append(pdf_path)
        REPORT("INFO", T["PDF_FILE"].format(path=pdf_path))
    return fplist


def collect_report_type_data(
    template: Template,
    pid_list: list[str],
    subject_groups: dict[str, list[str]],
    grade_info: dict,
    show_data: bool,
) -> str:
    """Build grade reports of the given type (<rtype>) for the given
    pupils (<pid_list>).
    """
    all_keys = template.all_keys()
    if show_data:
        REPORT(
            "INFO",
            T["ALL_KEYS"].format(
                keys=", ".join(sorted(all_keys)),
                path=template.template_path
            ),
        )
    subjects, tagmap = group_grades(all_keys, template)
    # print("\n§§§ SUBJECTS:", subjects)
    # print("\n§§§ TAGMAP:", tagmap)

    ## Template field/value processing
    metadata = template.metadata()
    template_field_info = metadata.get("FIELD_INFO") or {}
    grade_map = template_field_info.get("GRADE_MAP") or {}
    # print("\nGRADE MAP:", grade_map)

    ## Transform subject groups?
    sgmap = template_field_info.get("SUFFIX_GROUP_MAP") or {}
    gmap = template_field_info.get("GROUP_MAP") or {}
    # print("\n ??? TEMPLATE GROUP MAP:", gmap)
    sgroups = {}
    for g in sorted(subject_groups):
        for sdata in subject_groups[g]:
            # print(f"\n ??? SUBJECT GROUP {g}:", sdata)
            sid = sdata["SID"]
            try:
                sid0, gsuff = sid.rsplit(".", 1)
            except ValueError:
                pass
            else:
                try:
                    gs = sgmap[gsuff]
                    if not gs:
                        continue  # this subject is not shown
                except KeyError:
                    pass
                else:
                    try:
                        sgroups[gs].append(sdata)
                    except KeyError:
                        sgroups[gs] = [sdata]
                    continue
            try:
                g1 = gmap[g]
                if not g1:
                    continue  # this subject is not shown
            except KeyError:
                REPORT(
                    "ERROR",
                    T["UNKNOWN_SUBJECT_GROUP"].format(
                        path=template.template_path, group=g
                    ),
                )
                continue
            try:
                sgroups[g1].append(sdata)
            except KeyError:
                sgroups[g1] = [sdata]
    # print("\nSUBJECT GROUPS:", sgroups)

    ## Build the data mappings and generate the reports
    date_format = template_field_info.get("DATEFORMAT") or CONFIG["DATEFORMAT"]
    base_data = {
        "SCHOOL": CONFIG["SCHOOL_NAME"],
        "SCHOOLBIG": CONFIG["SCHOOL_NAME"].upper(),
        "SCHOOLYEAR": CALENDAR["SCHOOLYEAR_PRINT"],
        "DATE_ISSUE": grade_info["DATE_ISSUE"],
        "DATE_GRADES": grade_info["DATE_GRADES"],
        "FUNCTIONS": {
            "DATE": lambda d: Dates.print_date(d, date_format),
        }
    }
    gmaplist = []
    for pdata, grades in grade_info["PUPIL_LIST"]:
        if pdata["PID"] not in pid_list:
            continue
        rptdata = base_data.copy()
        rptdata.update(pdata)
        rptdata.update(grades)
        sort_grade_keys(rptdata, subjects, tagmap, sgroups, grade_map)
        # Locality-specific processing:
        ProcessGradeData(rptdata, grade_info, GetGradeConfig())
        # Add symbols
        for k, v in grade_info["SYMBOLS"].items():
            rptdata[k] = substitute_symbol(rptdata, v)
        # Format dates
        for k, v in rptdata.items():
            if k.startswith("DATE_"):
                if v:
                    v = Dates.print_date(v, date_format)
                else:
                    v = ""
                rptdata[k] = v
        # Additional field/value mappings
        mappings = template_field_info.get("MAPPINGS")
        if mappings:
            for f, f2, m in mappings:
                try:
                    v = rptdata[f]
                except KeyError:
                    continue
                try:
                    v2 = m[v]
                except KeyError:
                    REPORT(
                        "ERROR",
                        T["MISSING_DOC_MAPPING"].format(
                            path=template.template_path,
                            field1=f,
                            value1=v
                        )
                    )
                    continue
                rptdata[f2] = v2
        lines = []
        pname = pupil_name(rptdata)
        for k in sorted(all_keys):
            if k in rptdata:
                lines.append(T["USED_KEY"].format(key=k, val=rptdata[k]))
            else:
                REPORT("ERROR", T["MISSING_KEY"].format(name=pname, key=k))
        if show_data:
            for k in sorted(rptdata):
                if k not in all_keys:
                    lines.append(T["UNUSED_KEY"].format(key=k, val=rptdata[k]))
            REPORT(
                "INFO",
                T["CHECK_FIELDS"].format(
                    name=pupil_name(rptdata), data="\n".join(lines)
                ),
            )
        gmaplist.append(rptdata)
    return gmaplist


def group_grades(
    all_keys: set[str],
    template: Template, # just for error reporting
) -> tuple[set[str], dict[str, list[str]]]:
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
                REPORT(
                    "ERROR",
                    T["BAD_SUBJECT_KEY"].format(
                        key=key,
                        path=template.template_path,
                    )
                )
            try:
                tags[tag].add(index)
            except KeyError:
                tags[tag] = {index}
        elif key.startswith("g."):
            # g.<subject tag>
            subjects.add(key[2:])
    tagmap: dict[str, list[str]] = {
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
                REPORT(
                    "ERROR",
                    T["BAD_GRADE"].format(
                        sid=sid, grade=grade, pupil=pupil_name(rptdata)
                    ),
                )
                return "?"
            return ""
    # REPORT("OUT", repr(rptdata))
    for sid in subjects:
        try:
            g = rptdata.pop(sid)
        except KeyError:
#TODO: Is this possible?
            assert(False)
            REPORT(
                "WARNING",
                T["MISSING_SUBJECT_GRADE"].format(
                    sid=sid, pupil=pupil_name(rptdata)
                ),
            )
            rptdata[f"g.{sid}"] = "XXX"
        else:
            if g:
                rptdata[f"g.{sid}"] = print_grade(g)
            else:
                REPORT(
                    "WARNING",
                    T["EMPTY_SUBJECT_GRADE"].format(
                        sid=sid, pupil=pupil_name(rptdata)
                    ),
                )
                rptdata[f"g.{sid}"] = "???"

    for tag, sdata_list in sgroups.items():
        # REPORT("OUT", f'### S-Group {tag}, {[sd["SID"] for sd in sdata_list]}')
        try:
            keys = tagmap[tag].copy()
        except KeyError:
            REPORT(
                "ERROR",
                T["MISSING_SUBJECT_GROUP"].format(
                    tag=tag, pupil=pupil_name(rptdata)
                ),
            )
            continue
        for sdata in sdata_list:
            sid = sdata["SID"]
            try:
                g = rptdata.pop(sid)
            except KeyError:
                continue
            try:
                k = keys.pop()
            except IndexError:
                REPORT(
                    "ERROR",
                    T["TOO_FEW_KEYS"].format(
                        tag=tag, pupil=pupil_name(rptdata)
                    ),
                )
                continue

            rptdata[f"S.{tag}.{k}"] = sdata["NAME"].split("*", 1)[0]
            if g:
                rptdata[f"G.{tag}.{k}"] = print_grade(g)
            else:
                REPORT(
                    "WARNING",
                    T["EMPTY_SUBJECT_GRADE"].format(
                        sid=sid, pupil=pupil_name(rptdata)
                    ),
                )
                rptdata[f"G.{tag}.{k}"] = "???"

        for k in keys:
            rptdata[f"G.{tag}.{k}"] = NOGRADE
            rptdata[f"S.{tag}.{k}"] = NOGRADE


def substitute_symbol(report_data_mapping:dict, symbol:str):
    """Evaluate all embedded variables (between curly brackets) in
    <symbol>.
    <report_data_mapping> provides the environment for the item
    evaluation. The available functions are provided in the element
    with key "FUNCTIONS".
    """
    def do_sub(rem):
        # print(":::", rem.group(0), "->")
        fn = rem.group(1)
        tag = rem.group(2)
        taglist = tag.split("/")
        try:
            item = report_data_mapping[taglist.pop(0)]
            while not isinstance(item, str):
                arg = taglist.pop(0)    # possible IndexError
                if isinstance(item, dict):
                    item = item[arg]    # possible KeyError
                elif isinstance(item, list):
                    if (i := int(arg)) < 0:     # possible ValueError
                        raise ValueError
                    item = item[i]      # possible ValueError
                else:
                    raise ValueError
        except (KeyError, ValueError, IndexError):
            REPORT(
                "ERROR",
                T["UNDEFINED_SYMBOL"].format(symbol=sym, element=tag)
            )
            return rem.group(0)
        if fn:
            try:
                f = report_data_mapping["FUNCTIONS"][fn]
            except KeyError:
                REPORT(
                    "ERROR",
                    T["UNDEFINED_FUNCTION"].format(symbol=sym, fn=fn)
                )
                return rem.group(0)
            return f(item)
        else:
            return item

    return re.sub(RE_VALUE_KEY, do_sub, symbol)


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":

    symbols = {
        "HJ": "1. und 2. Halbjahr",
        "QP12": ("hat den 12. Jahrgang der Qualifikationsphase vom"
            + " {DATE_QPHASE} bis zum {DATE:CALENDAR/LAST_DAY} besucht.")
    }
    report_symbols = {
        "DATE_QPHASE": "26.08.2022",
        "CALENDAR": CALENDAR,
        "FUNCTIONS": {
            # A bodge for testing!
            "DATE": lambda d: Dates.print_date(d, CONFIG["DATEFORMAT"]),
        }
    }
    print("§§§ REPORT SYMBOLS:")
    print(report_symbols)
    print("\n ===========================================\n")
    for sym, val in symbols.items():
        print(f"{sym}: {substitute_symbol(report_symbols, val)}")

#    quit(0)

    from core.db_access import open_database

    open_database()
    fgtable = FullGradeTable(occasion="1. Halbjahr", class_group="12G.G", instance="")

    fpaths = PROCESS(
        MakeReports,
        title="Build reports",
        full_grade_table=fgtable,
        show_data=True,
    )
    for f in fpaths:
        print("--->", f)
