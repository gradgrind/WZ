"""
grades/gradetable.py

Last updated:  2022-12-25

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

# Bear in mind that a pupil's groups and "level" can change during a
# school-year. Thus these fields are saved along with the grades when
# grade reports are built and issued. After a set of grade reports has
# been issued, subsequent inspection of the data for this issue should
# show the state at the time of issue. Inspection and editing prior to
# the date of issue should update to the latest database state of the
# pupils.

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

from typing import Optional
import datetime

from core.base import class_group_split, Dates
from core.db_access import (
    db_read_table,
    read_pairs,
    db_new_row,
    db_delete_rows,
    db_update_field,
    write_pairs_dict,
)
from core.basic_data import SHARED_DATA, get_subjects_with_sorting
from core.pupils import pupil_name, pupil_data
from core.report_courses import get_pupil_grade_matrix
from tables.spreadsheet import read_DataTable
from tables.matrix import KlassMatrix
from local.grade_functions import grade_function

class GradeTableError(Exception):
    pass


NO_GRADE = "/"

### -----


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
        symbols = odata["__SYMBOLS__"].copy()
    except KeyError:
        symbols = {}
    try:
        cgodata = odata[class_group].copy()
    except KeyError:
        raise GradeTableError(
            T["INVALID_OCCASION_GROUP"].format(occasion=o, group=class_group)
        )
    try:
        symbols.update(cgodata.pop("__SYMBOLS__"))
    except KeyError:
        pass
    cgodata["SYMBOLS"] = symbols
    return cgodata


def grade_table_info(occasion: str, class_group: str, instance: str = ""):
    ### Get subject, pupil and group report-information
    subjects, pupils = get_pupil_grade_matrix(class_group, text_reports=False)
    group_data = get_group_data(occasion, class_group)
    print("??????", group_data)
    klass, group = class_group_split(class_group)
    grade_info = get_grade_config()
    composites = {}
    composite_components = {}
    composite_references = {}
    averages = {}
    try:
        __extra_info = grade_info["GRADE_FIELDS_EXTRA"][klass]
    except KeyError:
        pass
    else:
        # Get "composites" and "calculates", check sid not in subjects table:
        sid_map = get_subjects_with_sorting()
        composite_map = grade_info["COMPOSITES"]
        for sid in composite_map:
            if sid in sid_map:
                raise GradeTableError(T["BAD_COMPOSITE_SID"].format(sid=sid))
        extras_map = grade_info["CALCULATES"]
        for sid in extras_map:
            if sid in sid_map:
                raise GradeTableError(T["BAD_CALCULATE_SID"].format(sid=sid))
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
        for sid, fn in __clist:
            try:
                name, sorting, components = composite_map[sid]
            except KeyError:
                raise GradeTableError(T["UNKNOWN_COMPOSITE"].format(sid=sid))
            composites[sid] = (name, fn, sorting)
            composite_references[sid] = []
            for cmpn in components:
                if cmpn in composite_components:
                    raise GradeTableError(
                        T["COMPONENT_NOT_UNIQUE"].format(sid=cmpn)
                    )
                composite_components[cmpn] = sid
        averages = {}
        for sid, fn in __alist:
            try:
                name, subject_list = extras_map[sid]
            except KeyError:
                raise GradeTableError(T["UNKNOWN_CALCULATE"].format(sid=sid))
            averages[sid] = (name, fn, subject_list)

    subject_list = []
    component_list = []
    for sdata in sorted(subjects.values()):
        # print("§§§§§§§§", sdata)
        # Subjects counting towards composites need some sort of reference
        # to their target – so that a change can trigger a recalculation.
        sid = sdata[1]
        sname = sdata[2]
        zgroup = sdata[3]
        # sdata[4] is the text-report custom settings, which are
        # not relevant  here.
        value = {"SID": sid, "NAME": sname, "TYPE": "SUBJECT", "GROUP": zgroup}
        try:
            composite = composite_components[sid]
            value["COMPOSITE"] = composite
            composite_references[composite].append(sid)
            # A "composite component"
            component_list.append(value)
        except KeyError:
            # A "normal" subject, not a "composite component"
            subject_list.append(value)
    result = {
        "OCCASION": occasion,
        "CLASS_GROUP": class_group,
        "INSTANCE": instance,
        "SUBJECTS": subject_list,
        "COMPONENTS": component_list
    }

    # Composites
    composite_list = []
    result["COMPOSITES"] = composite_list
    for k, v in composites.items():
        f = v[1]
        if f:
            references = composite_references[k]
            if not references:
                REPORT(
                    "WARNING",
                    T["COMPOSITE_NO_COMPONENTS"].format(
                        sid=k, name=v[0]
                    )
                )
            composite_list.append(
                {
                    "SID": k,
                    "NAME": v[0],
                    "TYPE": "COMPOSITE",
                    "FUNCTION": f,
                    "GROUP": v[2],
                    "COMPONENTS": references
                }
            )

    # Now all the extra fields
    extra_list = []
    result["EXTRAS"] = extra_list
    for k, v in averages.items():
        extra_list.append(
            {
                "SID": k,
                "NAME": v[0],
                "TYPE": "CALCULATE",
                "FUNCTION": v[1],
                "COMPONENTS": v[2]
            }
        )
    for k, v in group_data.items():
        if k[0] == "?":
            node = {
                "SID": k[1:],
                "NAME": v[0],
                "TYPE": v[1]
            }
            try:
                node["VALUES"] = v[2]
            except IndexError:
                node["VALUES"] = []
            extra_list.append(node)
    result["GRADES"] = group_data["GRADES"]
    result["GRADE_ENTRY"] = group_data.get("GRADE_ENTRY", "")
    result["SYMBOLS"] = group_data["SYMBOLS"]

    pupil_map = {}
    result["PUPILS"] = pupil_map
    for pdata, p_atoms, p_grade_tids in pupils:
        pupil_map[pdata["PID"]] = (pdata, p_grade_tids)

    return result


def full_grade_table(occasion, class_group, instance):
    ### Get config info
    table_info = grade_table_info(occasion, class_group, instance)
    ### Get stored pupils and grades
    pid2grades = {}
    pdata_list = []
    for pdata, grade_map in read_stored_grades(
        occasion, class_group, instance
    ):
        pdata_list.append(pdata)
        pid2grades[pdata["PID"]] = grade_map
    ### Get general info from database concerning stored grades
    infolist = db_read_table(
        "GRADES_INFO",
        ["DATE_ISSUE", "DATE_GRADES", "MODIFIED"],
        CLASS_GROUP=class_group,
        OCCASION=occasion,
        INSTANCE=instance
    )[1]
    today = Dates.today()
    if infolist:
        if len(infolist) > 1:
            raise Bug(
                f"Multiple entries in GRADES_INFO for {class_group}"
                f" / {occasion} / {instance}"
            )
        DATE_ISSUE, DATE_GRADES, MODIFIED = infolist[0]

#TODO
#later?
#        if DATE_GRADES >= Dates.today():
#            # Assume the list of pupils is fixed at the issue date
#            pdata_list.clear()
    else:
        # No entry in database, use "today" for initial date values
        DATE_ISSUE = today
        DATE_GRADES = DATE_ISSUE
        MODIFIED = "–––––"
        if pdata_list:
            raise Bug("Stored grades but no entry in GRADES_INFO for"
                f" {class_group} / {occasion} / {instance}"
            )
        db_new_row("GRADES_INFO",
            CLASS_GROUP=class_group,
            OCCASION=occasion,
            INSTANCE=instance,
            DATE_ISSUE=DATE_ISSUE,
            DATE_GRADES=DATE_GRADES
        )
    table_info["DATE_ISSUE"] = DATE_ISSUE
    table_info["DATE_GRADES"] = DATE_GRADES
    table_info["MODIFIED"] = MODIFIED
    subject_list = table_info["SUBJECTS"]
    ## Fields: SID:str, NAME:str, TYPE:str=SUBJECT, GROUP:str
    components_list = table_info["COMPONENTS"]
    ## Fields: SID:str, NAME:str, TYPE:str=SUBJECT, GROUP:str, COMPOSITE:str
    composites_list = table_info["COMPOSITES"]
    ## Fields: SID:str, NAME:str, TYPE:str=COMPOSITE, GROUP:str, FUNCTION:str, COMPONENTS:list[str]
    extras_list = table_info["EXTRAS"]
    ## Fields: SID:str, NAME:str, TYPE:str=CALCULATE, FUNCTION:str, COMPONENTS:list[str]
    ## Fields: SID:str, NAME:str, TYPE:str=CALCULATE, FUNCTION:str, COMPONENTS:'*'
    ## Fields: SID:str, NAME:str, TYPE:str=CHOICE, VALUES:list[str]
    ## Fields: SID:str, NAME:str, TYPE:str=CHOICE_MAP, VALUES:list[list[str,str]]
    ## Fields: SID:str, NAME:str, TYPE:str=TEXT
    # The mapping in <sid2data> is ordered!
    sid2data = {
        sdata["SID"]: sdata
        for sdata in (
            subject_list + components_list + composites_list + extras_list
        )
    }
    pid2grade_map = {}
    pid2level_change = set()
    pid2old_grades = {}
    if DATE_GRADES < today:
        # Assume the list of pupils is fixed at the grading date
        # Use stored pupils for this issue
        if pdata_list:
            for pdata in pdata_list:
                pid = pdata["PID"]
                __grade_map = pid2grades.get(pid) or {}
                grade_map = {}
                pid2grade_map[pid] = grade_map
                for sid in sid2data:
                    grade_map[sid] = __grade_map.get(sid, "")
        else:
            REPORT("ERROR", T["NO_PUPIL_GRADES"].format(
                report_info=f"{class_group} / {occasion} / {instance}"
            ))
    else:
        # Use the current list of pupils for this group
        # ... but look for changed pupils and LEVEL fields
        old_pdata = {
            pdata["PID"]: pdata["LEVEL"]
            for pdata in pdata_list
        }
        pdata_list = []
        for pid, pinfo in table_info["PUPILS"].items():
            pdata, p_grade_tids = pinfo
            pdata_list.append(pdata)
            try:
                old_level = old_pdata.pop(pid)
            except KeyError:
                __grade_map = {}
            else:
                if pdata["LEVEL"] != old_level:
                    pid2level_change.add(pid)
                __grade_map = dict(pid2grades.pop(pid))
            pid2old_grades[pid] = __grade_map
            grade_map = {}
            pid2grade_map[pid] = grade_map
            for sid, sdata in sid2data.items():
                if sdata["TYPE"] == "SUBJECT" and not p_grade_tids.get(sid):
                    grade_map[sid] = NO_GRADE
                else:
                    try:
                        grade_map[sid] = __grade_map[sid]
                    except KeyError:
                        # Consider the value list for defaults, taking
                        # the first entry
                        try:
                            values = sdata["VALUES"]
                        except KeyError:
                            grade_map[sid] = ""
                        else:
                            if values:
                                default = values[0]
                            else:
                                default = ""
                            # The value can be a single string or a pair
                            if isinstance(default, list):
                                grade_map[sid] = default[0]
                            else:
                                grade_map[sid] = default
            # Delay the comparison with the old data until after the
            # computations. This allows for changes in the calculations.
        # Remove pupils from grade table if they are no longer in the group.
        # This must be done because otherwise they would be "reinstated"
        # as soon as the date-of-issue is past.
        for pid in old_pdata:
            db_delete_rows("GRADES",
                OCCASION=occasion,
                CLASS_GROUP=class_group,
                INSTANCE=instance,
                PID=pid
            )
    table_info["ALL_SIDS"] = sid2data
    table_info["PUPIL_GRADES"] = pid2grade_map
    table_info["GRADE_TABLE_PUPILS"] = pdata_list
    # Calculate contents of all cells with FUNCTION
    table_changed = False
    for pdata in pdata_list:
        pid = pdata["PID"]
        changes = calculate_row(table_info, pid)
        if pid in pid2level_change:
#
            print(f"\n!!!!!!!!!! level changed for {pid}")
            db_update_field("GRADES", "LEVEL", pdata["LEVEL"],
                OCCASION=occasion,
                CLASS_GROUP=class_group,
                INSTANCE=instance,
                PID=pid
            )
            table_changed = True
        old_grades = pid2old_grades[pid]
        if old_grades:
            new_grades = pid2grade_map[pid]
            if new_grades != old_grades:
#
                print(f"\n!!!!!!!!!! grades changed for {pid}")

                # The update only occurs if there was already an entry
                # for the pupil (<old_grades> not empty)
                db_update_field("GRADES",
                    "GRADE_MAP", write_pairs_dict(new_grades),
                    OCCASION=occasion,
                    CLASS_GROUP=class_group,
                    INSTANCE=instance,
                    PID=pid
                )
                table_changed = True
        # print("+++++++ CALCULATED CHANGES:", changes)
    if table_changed:
        print("$$$ Read grade table data done")
        update_grade_time(
            OCCASION=occasion,
            CLASS_GROUP=class_group,
            INSTANCE=instance,
        )
    return table_info


def calculate_row(table, pid):
    """Calculate the evaluated cells of the row from "left to right"
    (lower to higher index).
    A calculation may depend on the value in an evaluated cell, but
    not on evaluated cells to the right (because of the order of
    evaluation).
    "Composite" subjects are evaluated first.
    """
    grades = table["PUPIL_GRADES"][pid]
    subjects = table["SUBJECTS"]
    final_grades = [grades.get(sdata["SID"]) for sdata in subjects]
    composites = table["COMPOSITES"]
    extras = table["EXTRAS"]
    # print("\n**** CALCULATE:", pid, grades)
    changed_grades = []

    for sdata in composites:
        sid = sdata["SID"]
        f = sdata["FUNCTION"]
        components = sdata["COMPONENTS"]
        value = grades[sid]
        glist = [grades.get(__sid) for __sid in components]
        new_value = grade_function(f, glist)
        final_grades.append(new_value)
        if new_value != value:
            grades[sid] = new_value
            changed_grades.append((sid, value))
        # print("   --- COMPOSITE:", sid, value, "->", new_value, components)

    for sdata in extras:
        try:
            f = sdata["FUNCTION"]
        except KeyError:
            continue
        sid = sdata["SID"]
        components = sdata["COMPONENTS"]
        value = grades[sid]
        if components == '*':
            glist = final_grades
        else:
#TODO: Would it be better to exclude not-yet-calculated entries? At present
# all entries are available, but might  not be up-to-date.
            glist = [grades.get(__sid) for __sid in components]
        new_value = grade_function(f, glist)
        if new_value != value:
            grades[sid] = new_value
            changed_grades.append((sid, value))
        # print("   --- EXTRA:", sid, value, "->", new_value, components)

    return changed_grades


def read_stored_grades(
    occasion: str,
    class_group: str,
    instance: str = ""
) -> list[tuple[dict, dict]]:
    """Return an ordered list containing personal info and grade info
    from the database for each pupil covered by the parameters.
    """
    fields = [
        # "OCCASION",
        # "CLASS_GROUP",
        # "INSTANCE",
        "PID",
        "LEVEL",  # The level might have changed, so this field is relevant
        "GRADE_MAP",
    ]
    flist, rlist = db_read_table(
        "GRADES",
        fields,
        OCCASION=occasion,
        CLASS_GROUP=class_group,
        INSTANCE=instance,
    )
    plist = []
    for row in rlist:
        pid = row[0]
        pdata = pupil_data(pid)  # this mapping is not cached => it is mutable
        # Substitute the pupil fields which could differ in the grade data
        pdata["CLASS"] = class_group_split(class_group)[0]
        pdata["LEVEL"] = row[1]
        # Get grade (etc.) info as mapping
        grade_map = read_pairs(row[2])
        plist.append((pdata, dict(grade_map)))
    return plist


def update_pupil_grades(grade_table, pid):
    # Recalculate row
    changed_grades = calculate_row(grade_table, pid)
    # print("\nCHANGED:", changed_grades)
    # Save grades to database
    grades = grade_table["PUPIL_GRADES"][pid]
    gstring = write_pairs_dict(grades)
    # print("GRADES", "GRADE_MAP", gstring,
    #    grade_table["OCCASION"],
    #    grade_table["CLASS_GROUP"],
    #    grade_table["INSTANCE"],
    #    pid
    #)
    OCCASION = grade_table["OCCASION"]
    CLASS_GROUP = grade_table["CLASS_GROUP"]
    INSTANCE = grade_table["INSTANCE"]
    if not db_update_field("GRADES",
        "GRADE_MAP", gstring,
        OCCASION=OCCASION,
        CLASS_GROUP=CLASS_GROUP,
        INSTANCE=INSTANCE,
        PID=pid
    ):
        db_new_row("GRADES",
            OCCASION=OCCASION,
            CLASS_GROUP=CLASS_GROUP,
            INSTANCE=INSTANCE,
            PID=pid,
            LEVEL=pupil_data(pid)["LEVEL"],
            GRADE_MAP=gstring
        )
    print("$$$ update grades")
    timestamp = update_grade_time(
        OCCASION=OCCASION,
        CLASS_GROUP=CLASS_GROUP,
        INSTANCE=INSTANCE
    )
    return changed_grades, timestamp


def update_grade_time(OCCASION, CLASS_GROUP, INSTANCE):
    timestamp = Dates.timestamp()
    db_update_field("GRADES_INFO", "MODIFIED", timestamp,
        OCCASION=OCCASION,
        CLASS_GROUP=CLASS_GROUP,
        INSTANCE=INSTANCE
    )
#--
    print("%%% Update grade timestamp:\n"
        f"  {CLASS_GROUP}/{OCCASION}/{INSTANCE}: {timestamp}"
    )
    return timestamp


def update_table_info(field, value, OCCASION, CLASS_GROUP, INSTANCE):
    timestamp = Dates.timestamp()
    db_update_field("GRADES_INFO", field, value,
        OCCASION=OCCASION,
        CLASS_GROUP=CLASS_GROUP,
        INSTANCE=INSTANCE
    )
    print("$$$ update table info")
    timestamp = update_grade_time(
        OCCASION=OCCASION,
        CLASS_GROUP=CLASS_GROUP,
        INSTANCE=INSTANCE
    )
    return timestamp


def make_grade_table(
    occasion: str,
    class_group: str,
    instance: str = "",
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
    components = gtinfo["COMPONENTS"]
    pupils = gtinfo["PUPILS"]

    ### Get template file
    template_path = RESOURCEPATH("templates/" + gtinfo["GRADE_ENTRY"])
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
    info_item: dict
    grade_info = get_grade_config()
    info_transl: dict[str, str] = dict(grade_info["INFO_FIELDS"])
    info: dict[str, str] = {
        info_transl["SCHOOLYEAR"]: SCHOOLYEAR,
        info_transl["CLASS_GROUP"]: class_group,
        info_transl["OCCASION"]: occasion,
        info_transl["INSTANCE"]: instance,
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
    for sdata in subjects + components:
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
                if g := pgrades.get(sid):
                    table.write(row, col, g)
            else:
                table.write(row, col, NO_GRADE, protect=True)
    # Delete excess rows
    row = table.nextrow()
    table.delEndRows(row)

    ### Save file
    table.protectSheet()
    return table.save_bytes()


def read_grade_table_file(
    filepath: str,
) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
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
    info = {(info_map.get(k) or k): v for k, v in datatable["__INFO__"].items()}
    ### Get the rows as mappings
    # fields = datatable["__FIELDS__"]
    # print("\nFIELDS:", fields)
    gdata: dict[str, dict[str, str]] = {"__INFO__": info}
    group_data = get_group_data(info["OCCASION"], info["CLASS_GROUP"])
    valid_grades = get_valid_grades(group_data["GRADES"])
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
                            grade=v,
                        ),
                    )
                    pdata[k] = ""
    return gdata


def get_valid_grades(value_table) -> dict[str,str]:
    """Make a mapping of valid grades to their print values from the
    configuration table (in GRADE_CONFIG).
    """
    gmap = {}
    for row in value_table:
        text = row[1]
        for val in row[0]:
            gmap[val] = text or val
    return gmap


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
    print("\n*** COMPOSITE-COMPONENTS")
    for val in gtinfo["COMPONENTS"]:
        print("    ---", val)
    print("\n*** COMPOSITES")
    for val in gtinfo["COMPOSITES"]:
        print("    ---", val)
    print("\n*** EXTRA COLUMNS")
    for val in gtinfo["EXTRAS"]:
        print("    ---", val)
    print("\n*** GRADES", gtinfo["GRADES"])
    print("\n*** PUPILS")
    for pid, pinfo in gtinfo["PUPILS"].items():
        pdata, p_grade_tids = pinfo
        print(f"\n +++ {pdata}")
        print(" .........", p_grade_tids)

    print("\n*** STORED GRADES")
    stored_grades = read_stored_grades("1. Halbjahr", "12G.R")

    print("\n???????????????????????????????????????????????????????")

    #grade_table = full_grade_table("1. Halbjahr", "12G.R", "").items()
    grade_table = full_grade_table("2. Halbjahr", "13", "").items()

    print("\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

    for k, v in grade_table:
        print("\n =======", k, "\n", v)

    #print("\n&&&&&&&&&&&&&&&&&", get_group_data("1. Halbjahr", "13"))
