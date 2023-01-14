"""
grades/gradetable.py

Last updated:  2023-01-14

Access grade data, read and build grade tables.

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

#TODO: This should be a rewrite of "gradetables" with a more
# understandable structure, possibly some increased flexibility to handle
# local specialities (like Abitur!).

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
    start.setup(os.path.join(basedir, "DATA-2023"))

T = TRANSLATIONS("grades.grades_base")

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
from local.grade_processing import grade_function, special_handler

class GradeTableError(Exception):
    pass


NO_GRADE = "/"

### -----


def get_grade_config():
    """Fetch the base configuration data for grade handling. The
    resulting mapping is cached.
    """
    try:
        return SHARED_DATA["GRADES_BASE"]
    except KeyError:
        pass
    path = DATAPATH("CONFIG/GRADES_BASE")
    data = MINION(path)
    data["__PATH__"] = path
    SHARED_DATA["GRADES_BASE"] = data
    return data


def get_occasions_groups():
    """Get a list of occasions and for each occasion a list of groups
    which have an entry of that occasion. The result is cached.
    """
    try:
        return SHARED_DATA["GRADES_OCCASIONS_GROUPS"]
    except KeyError:
        pass
    occasions = {}
    SHARED_DATA["GRADES_OCCASIONS_GROUPS"] = occasions
    grade_config = get_grade_config()
    for group, gocclist in grade_config["GROUP_DATA"].items():
        for occ, odata in gocclist:
            try:
                ogd = occasions[occ]
            except KeyError:
                occasions[occ] = {group: odata}
            else:
                if group in ogd:
                    REPORT(
                        "ERROR",
                        T["DUPLICATE_OCCASION_IN_GROUP"].format(
                            group=group,
                            occasion=occ,
                            path=grade_config["__PATH__"]
                        )
                    )
                    continue
                ogd[group] = odata
    return occasions


def get_group_data(occasion: str, class_group: str):
    """Get configuration information pertaining to the grade table
    for the given group and "occasion".
    """
    try:
        return get_occasions_groups()[occasion][class_group]
    except KeyError:
        raise Bug(
            f'No grades config info for group "{class_group}",'
            f' "occasion" = {occasion}'
            f' in\n  {get_grade_config()["__PATH__"]}'
        )


class SubjectColumns(list):
    """A custom representation of the column data ("subjects").
    It is a list, but with a look-up function ("get") for sid keys.
    Only indexing and the methods below are supported, using others
    might well make a mess ...
    """
    def __init__(self):
        super().__init__()
        self.__map = {}

    def append(self, subject_data):
        self.__map[subject_data["SID"]] = len(self)
        super().append(subject_data)

    def get(self, sid):
        return self[self.__map[sid]]

    def column(self, sid):
        return self.__map[sid]


class PupilRows(list):
    """A custom representation of the row data (pupils).
    It is a list, but with a look-up function ("get") for pid keys.
    Only indexing and the methods below are supported, using others
    might well make a mess ...
    """
    def __init__(self):
        super().__init__()
        self.__map = {}

    def append(self, pupil_data, grade_map):
        self.__map[pupil_data["PID"]] = len(self)
        super().append((pupil_data, grade_map))

    def get(self, pid):
        return self[self.__map[pid]]

    def column(self, pid):
        return self.__map[pid]


def grade_table_info(occasion: str, class_group: str, instance: str = ""):
    """Get subject, pupil and group report-information for the given
    parameters.
    """
    subjects, pupils = get_pupil_grade_matrix(class_group, text_reports=False)
    group_data = get_group_data(occasion, class_group)
    klass, group = class_group_split(class_group)
    composites = {}
    composite_components = {}
    composite_references = {}
    averages = {}
    ### Complete the "subjects" list, including "composite" subjects,
    ### calculated fields and additional input fields.
    extra_fields = group_data["EXTRA_FIELDS"]
    try:
        sfun = group_data["SUBJECT_FUNCTION"]
    except KeyError:
        pass
    else:
        special_handler(sfun, subjects=subjects)

    # print("\n????? subjects:\n", subjects)

    subject_map = {}
    column_list = SubjectColumns()
    for sdata in sorted(subjects.values()):
        sid = sdata[1]
        sname = sdata[2]
        zgroup = sdata[3]
        # sdata[4] is the text-report custom settings, which are
        # not relevant here.
        value = {
            "SID": sid,
            "NAME": sname,
            "TYPE": "SUBJECT",
            "GROUP": zgroup,
        }
        subject_map[sid] = value
        column_list.append(value)
    result = {
        "OCCASION": occasion,
        "CLASS_GROUP": class_group,
        "INSTANCE": instance,
#?        "SUBJECTS": subject_map,
        "COLUMNS": column_list,
    }

    for odata in extra_fields:
        otype = odata["TYPE"]
        osid = odata["SID"]
        ## Collect "components"
        component_list = []
        cmplist = odata.get("COMPONENTS")
        if cmplist:
            if isinstance(cmplist, list):
                for cmpsid in odata["COMPONENTS"]:
                    try:
                        cmpdata = subject_map[cmpsid]
                    except KeyError:
                        # This potential component sid is not used
                        continue
                    if "COMPOSITE" in cmpdata:
                        REPORT(
                            "ERROR",
                            T["COMPONENT_OF_COMPOSITE"].format(
                                path=get_grade_config()["__PATH__"],
                                group=class_group,
                                occasion=occasion,
                                sid=osid,
                                name=odata["NAME"],
                                csid=cmpsid,
                                cname=cmpdata["NAME"]
                            )
                        )
                        continue # Don't include this component
                    component_list.append(cmpsid)
            else:
                REPORT(
                    "ERROR",
                    T["COMPONENTS_NOT_LIST"].format(
                        path=get_grade_config()["__PATH__"],
                        group=class_group,
                        occasion=occasion,
                        sid=osid,
                        name=odata["NAME"],
                    )
                )
                continue

        if otype == "COMPOSITE":
            if not component_list:
                REPORT(
                    "WARNING",
                    T["COMPOSITE_NO_COMPONENTS"].format(
                        path=get_grade_config()["__PATH__"],
                        group=class_group,
                        occasion=occasion,
                        sid=osid,
                        name=odata["NAME"]
                    )
                )
                continue # Don't include this composite subject
            for cmpsid in component_list:
                subject_map[cmpsid]["COMPOSITE"] = osid
            column_list.append(
                {
                    "SID": osid,
                    "NAME": odata["NAME"],
                    "TYPE": "SUBJECT",
                    "FUNCTION": odata["FUNCTION"],
                    "GROUP": odata["GROUP"],
                    "COMPONENTS": component_list
                }
            )
            continue

        if otype == "CALCULATE":
            if not component_list:
                # Collect all non-component subjects
                component_list = {
                    item["SID"]
                    for item in column_list
                    if item["TYPE"] == "SUBJECT" and "COMPOSITE" not in item
                }
                if not component_list:
                    REPORT(
                        "WARNING",
                        T["CALCULATE_NO_COMPONENTS"].format(
                            path=get_grade_config()["__PATH__"],
                            group=class_group,
                            occasion=occasion,
                            sid=osid,
                            name=odata["NAME"]
                        )
                    )
                    continue # Don't include this calcuöated field
            column_list.append(
                {
                    "SID": osid,
                    "NAME": odata["NAME"],
                    "TYPE": "CALCULATE",
                    "FUNCTION": odata["FUNCTION"],
                    "COMPONENTS": component_list,
                    "PARAMETERS": odata.get("PARAMEMETERS") or {}
                }
            )
            continue

        if otype == "INPUT":
            column_list.append(
                {
                    "SID": osid,
                    "NAME": odata["NAME"],
                    "TYPE": "INPUT",
                    "METHOD": odata["METHOD"],
                    "PARAMETERS": odata.get("PARAMEMETERS") or {}
                }
            )
            continue

        REPORT(
            "ERROR",
            T["INVALID_EXTRA_FIELD"].format(
                path=get_grade_config()["__PATH__"],
                group=class_group,
                occasion=occasion,
                sid=osid,
                name=odata["NAME"],
            )
        )

    result["GRADE_VALUES"] = group_data["GRADES"]
    result["GRADE_ENTRY"] = group_data.get("GRADE_ENTRY", "")
    result["SYMBOLS"] = group_data.get("SYMBOLS") or {}
    pupil_map = {}  # ordered dict!
    result["PUPILS"] = pupil_map
    for pdata, p_grade_tids in pupils:
        pupil_map[pdata["PID"]] = (pdata, p_grade_tids)
    return result


#TODO: Break up this enormous function to make it more understandable!
def full_grade_table(occasion, class_group, instance, pupil_grades=None):
    """Return full pupil and grade information – including calculated
    field values – for the given parameters.
    This may cause changes to the database, so that its contents
    correspond to the returned data.
    Pupils with no grade data will not be added to the database.
    The parameter <pupil_grades> is provided to enable the grades to be
    updated from an external sourde. This should be a mapping:
        {pid: {sid: grade, ...}, ...}
        The grade mapping should, however, also include "PUPIL" (name)
        and "LEVEL" entries.
    """
    table = pupil_subject_grade_info(occasion, class_group, instance)
    prepare_pupil_list(table)


def pupil_subject_grade_info(occasion, class_group, instance):
    """Collate basic data for the report instance:
        configuration data for the subjects,
        pupil data list,
        stored grade info
    """
    ### Get config info, including pupil list ({key: value/data})
    table_info = grade_table_info(occasion, class_group, instance)
    ### Get database records for pupils and grades:
    ###     {pid: (pdata, grade-map), ... }
    ### Note that CLASS and LEVEL fields are taken from the database
    ### GRADES record.
#    db_pupil_grades = {
    table_info["STORED_GRADES"] = {
        pdata["PID"]: (pdata, grademap)
        for pdata, grademap in read_stored_grades(
            occasion, class_group, instance
        )
    }
    ### Get general info from database concerning stored grades
    infolist = db_read_table(
        "GRADES_INFO",
        ["DATE_ISSUE", "DATE_GRADES", "MODIFIED"],
        CLASS_GROUP=class_group,
        OCCASION=occasion,
        INSTANCE=instance
    )[1]
    if infolist:
        if len(infolist) > 1:
            # This should not be possible
            raise Bug(
                f"Multiple entries in GRADES_INFO for {class_group}"
                f" / {occasion} / {instance}"
            )
        DATE_ISSUE, DATE_GRADES, MODIFIED = infolist[0]
    else:
        # No entry in database, add a new one using "today" for initial
        # date values
        DATE_ISSUE = Dates.today()
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
    return table_info


def prepare_pupil_list(table_info):
    """Tweak the list of pupils taking the current date into account.
    If the grading date (DATE_GRADES) is before "today", only the pupils
    with grades stored in the database will be included – this is
    regarded as a "closed category" (report-set instance), the group data
    is assumed to have been correct at the grading date. For closed
    category data only inspection of the data or possibly minor tweaks
    are expected.
    The database grade entries do not include pupils' personal data, this
    must be taken from the standard (current) pupils table. It is
    assumed that this won't change in the course of a year, with one or
    two exceptions:
     - A pupil might leave (and so be absent from later lists, but the
       other data should still be there).
     - There might be fixes (which I assume should also be incorporated
       in older data, if relevant).
     - The LEVEL field might change (for old data keep the old version).
       To enable retention, this field is added to the grade mapping.
    Finally, the field values are recalculated and the database entries
    updated if there has been a change.
    """
    table_changed = False
    pdata_list = PupilRows()    # [(pdata, grades),  ... ]
    grades0 = {}   # for change detection, decision update vs. insert, etc.
    #    {pid: initial grade-map, ... }
    DATE_GRADES = table_info["DATE_GRADES"]
    if DATE_GRADES < Dates.today():
        # Closed category: include only pupils with stored grade entries,
        # i.e. assume the list of pupils is fixed at the grading date.
#        if pupil_grades:
#            raise Bug("Shouldn't be called with <pupil_grades>")
        for db_pdata, db_grademap in table_info["STORED_GRADES"].values():
            pname = pupil_name(db_pdata)
            if db_pdata["CLASS"] != db_pdata["__CLASS__"]:
                REPORT(
                    "WARNING",
                    T["CLASS_CHANGED"].format(
                        name=pname,
                        new_class=db_pdata["__CLASS__"]
                    )
                )
            if db_pdata["LEVEL"] != db_pdata["__LEVEL__"]:
                REPORT(
                    "WARNING",
                    T["LEVEL_CHANGED"].format(
                        name=pname,
                        db_level=db_pdata["LEVEL"],
                        new_level=db_pdata["__LEVEL__"]
                    )
                )
            grades0[db_pdata["PID"]] = db_grademap
            # Update the grade map
            grades = complete_grademap(
                table_info["COLUMNS"],
                db_grademap,
                pname   # just for messages
            )
            pdata_list.append(db_pdata, grades)
        if not pdata_list:
            REPORT("WARNING", T["NO_PUPIL_GRADES"].format(
                report_info=f"{class_group} / {occasion} / {instance}"
            ))

    else:
        # Category still open, use current pupil list, grades from database
        for pid, data in table_info.pop("PUPILS").items():
            pdata, sid_tids = data
            exit_date = pdata["DATE_EXIT"]
            if exit_date and DATE_GRADES > exit_date:
                continue    # pupil has left the school
            pname = pupil_name(pdata)
            try:
                db_pdata, db_grademap = table_info["STORED_GRADES"].pop(pid)
                grades0[pid] = db_grademap
            except KeyError:
                db_grademap = {}
            else:
                if db_pdata["LEVEL"] != pdata["LEVEL"]:
                    REPORT(
                        "WARNING",
                        T["LEVEL_UPDATED"].format(
                            name=pname,
                            db_level=db_pdata["LEVEL"],
                            new_level=pdata["LEVEL"],
                        )
                    )
                    # Update db field
                    db_update_field("GRADES", "LEVEL", pdata["LEVEL"],
                        OCCASION=occasion,
                        CLASS_GROUP=class_group,
                        INSTANCE=instance,
                        PID=pid
                    )
                    table_changed = True
            # Update the grade map
            grades = complete_grademap(
                table_info["COLUMNS"],
                db_grademap,
                pname,  # just for messages
                sid_tids
            )
            pdata_list.append(pdata, grades)
        # Remove pupils from grade table if they are no longer in the group.
        # This must be done because otherwise they would be "reinstated"
        # as soon as the date-of-issue is past.
        for pid, data in table_info["STORED_GRADES"].items():
            REPORT(
                "WARNING",
                T["REMOVING_PUPIL_GRADES"].format(
                    name=pupil_name(data[0])
                )
            )
            db_delete_rows("GRADES",
                OCCASION=occasion,
                CLASS_GROUP=class_group,
                INSTANCE=instance,
                PID=pid
            )
            table_changed = True

    del(table_info["STORED_GRADES"])
    table_info["PUPIL_LIST"] = pdata_list

    ### Recalculate contents of all cells with FUNCTION parameter
    for pdata, grades in pdata_list:
        pid = pdata["PID"]
        changes = calculate_pid_grades(table_info, pid)
        try:
            old_grades = grades0[pid]
        except KeyError:
            continue
        if old_grades != grades:
            print(
                f'\n*** TODO: UPDATE_GRADE_RECORD:\n'
                f'1) {write_pairs_dict(old_grades)}\n'
                f'2) {write_pairs_dict(grades)}'
            )
            continue
            # Update database record
            db_update_field("GRADES",
                "GRADE_MAP", write_pairs_dict(grades),
                OCCASION=occasion,
                CLASS_GROUP=class_group,
                INSTANCE=instance,
                PID=pid
            )
            table_changed = True
    if table_changed:
        set_grade_update_time(table_info)
    return table_info


# Grades supplied externally
# --------------------------
# A table of grades can be loaded from an external source. It is
# possible that the list of pupils doesn't correspond to that in
# the database (though that shouldn't be the normal case!). If that
# contains a pupil not in the master list, there should be a warning.
# Perhaps there should also be a warning if there is an attempt to
# place a grade in a "forbidden" (NO_GRADE) slot? I could skip such an
# automatic allocation, but allow it manually, or via dialog? That
# might also apply to the importing of grades from the database?
# Normally external grades should not be entered into a closed category.
# Should there be exceptions? Perhaps not – if it was really necessary,
# I could reopen the category by changing the date before importing the
# data (presumably resetting the date afterwards).
# If the LEVEL doesn't match, issue a warning but use the internal value.

#?
    if True:
        # Use the current master list of pupils for this group
        # ... but look for changed pupils (,CLASS) and LEVEL fields
        if pupil_grades: # externally supplied grade table
            # Don't use db_grades
            for pid, data in master_pupils.items():
                pdata, sid_tids = data
                exit_date = pdata["DATE_EXIT"]
                if exit_date and DATE_GRADES > exit_date:
                    continue    # pupil has left the school
                # Although the database entries are not needed, the pid
                # list is still needed to decide for update vs insert.
                # Also outdated entries need removing
                try:
                    db_pdata, db_grademap = table_info["STORED_GRADES"].pop(pid)
                    grades0[pid] = db_grademap
                except KeyError:
                    db_grademap = {}
                try:
                    new_grade_data = pupil_grades.pop(pid)
                except KeyError:
                    new_grade_data = {}
                    REPORT(
                        "WARNING",
                        T["NOT_IN_TABLE"].format(
                            name=pupil_name(pdata)
                        )
                    )
                else:
                    name = new_grade_data.pop("PUPIL")
                    table_level = new_grade_data.pop("LEVEL")
                    if table_level != pdata["LEVEL"]:
                        REPORT(
                            "WARNING",
                            T["LEVEL_MISMATCH"].format(
                                name=pupil_name(pdata),
                                table_level=table_level
                            )
                        )
                # Update the grade map
                grades = complete_grades(sid2data, sid_tids, new_grade_data)
                pdata_list.append(pdata, grades)
            for pid, new_grade_data in pupil_grades.items():
                if pid[0] != '_':
                    REPORT(
                        "WARNING",
                        T["PUPIL_NOT_IN_GROUP"].format(
                            name=new_grade_data["PUPIL"]
                        )
                    )
        else:   # grades from database
            for pid, data in master_pupils.items():
                pdata, sid_tids = data
                exit_date = pdata["DATE_EXIT"]
                if exit_date and DATE_GRADES > exit_date:
                    continue    # pupil has left the school
                try:
                    db_pdata, db_grademap = db_pupil_grades.pop(pid)
                    grades0[pid] = db_grademap
                except KeyError:
                    db_grademap = {}
                else:
                    if db_pdata["LEVEL"] != pdata["LEVEL"]:
                        REPORT(
                            "WARNING",
#TODO: Probably need a different message:
                            T["LEVEL_CHANGED"].format(
                                name=pupil_name(pdata),
                                db_level=db_pdata["LEVEL"]
                            )
                        )
                        # Update db field
                        db_update_field("GRADES", "LEVEL", pdata["LEVEL"],
                            OCCASION=occasion,
                            CLASS_GROUP=class_group,
                            INSTANCE=instance,
                            PID=pid
                        )
                        table_changed = True
                # Update the grade map
                grades = complete_grades(sid2data, sid_tids, db_grademap)
                pdata_list.append(pdata, grades)
        # Remove pupils from grade table if they are no longer in the group.
        # This must be done because otherwise they would be "reinstated"
        # as soon as the date-of-issue is past.
        for pid, data in db_pupil_grades.items():
            REPORT(
                "WARNING",
                T["REMOVING_PUPIL_GRADES"].format(
                    name=pupil_name(data[0])
                )
            )
            db_delete_rows("GRADES",
                OCCASION=occasion,
                CLASS_GROUP=class_group,
                INSTANCE=instance,
                PID=pid
            )
            table_changed = True
#?    table_info["ALL_SIDS"] = sid2data
    pid2row = {}
    table_info["PID2ROW"] = pid2row
    table_info["GRADE_TABLE_PUPILS"] = pdata_list


def set_grade_update_time(table_info):
    """Set the modification date+time for a report instance.
    Call after changes to the grade information.
    """
    timestamp = Dates.timestamp()
    db_update_field("GRADES_INFO", "MODIFIED", timestamp,
        OCCASION=table_info["OCCASION"],
        CLASS_GROUP=table_info["CLASS_GROUP"],
        INSTANCE=table_info["INSTANCE"]
    )
    table_info["MODIFIED"] = timestamp


def complete_grademap(sid2data, grades, name, p_grade_tids=None):
    """Ensure that the given grade data is "complete", according to
    the subjects list for the group and the subjects for which this
    pupil has a teacher (if this data is available).
    """
    grade_map = {}
    for sdata in sid2data:
        sid = sdata["SID"]
        if sdata["TYPE"] == "SUBJECT":
            if p_grade_tids is None:
                try:
                    grade_map[sid] = grades[sid]
                except KeyError:
                    grade_map[sid] = NO_GRADE
            elif p_grade_tids.get(sid):
                grade_map[sid] = grades.get(sid) or ""
            else:
                g = grades.get(sid)
                if g and g != NO_GRADE:
                    REPORT(
                        "WARNING",
                        T["GRADE_WITH_NO_TEACHER"].format(
                            sid=sid,
                            sname=sdata["NAME"],
                            grade=grades[sid],
                            pupil=name,
                        )
                    )
                grade_map[sid] = NO_GRADE
        else:
            try:
                grade_map[sid] = grades[sid]
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
    return grade_map


def calculate_pid_grades(table, pid):
    """Calculate the evaluated cells of the pupil data from "left to
    right" (lower to higher index).
    A calculation may depend on the value in an evaluated cell, but
    not on evaluated cells to the right (because of the order of
    evaluation).
    The set of grades should be complete before calling this function,
    i.e. all subjects should have entries (such as is achieved by
    calling <complete_grademap>).
    """
    grades = table["PUPIL_LIST"].get(pid)[1]
    subjects = table["COLUMNS"]
    changed_grades = []
    for sdata in subjects:
        sid = sdata["SID"]
        try:
            fn = sdata["FUNCTION"]
        except KeyError:
            continue
        # The function modifies <grades>
#TODO: Is that enough data for the functions? Would subject data for other
# subjects be needed?
        changed_grades.append(grade_function(fn, sdata, grades))
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
        # Save current volatile field values
        pdata["__CLASS__"] = pdata["CLASS"]
        pdata["__LEVEL__"] = pdata["LEVEL"]
        # Substitute these fields with data from the record
        pdata["CLASS"] = class_group_split(class_group)[0]
        pdata["LEVEL"] = row[1]
        # Get grade (etc.) info as mapping
        grade_map = read_pairs(row[2])
        plist.append((pdata, dict(grade_map)))
    return plist


def update_pupil_grades(grade_table, pid):
    # Recalculate row
    row = grade_table["PID2ROW"][pid]
    changed_grades = calculate_row(grade_table, row)
    # Save grades to database
    grades = grade_table["GRADE_TABLE_PUPILS"][row][1]
    gstring = write_pairs_dict(grades)
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
    timestamp = update_grade_time(
        OCCASION=OCCASION,
        CLASS_GROUP=CLASS_GROUP,
        INSTANCE=INSTANCE
    )
    return changed_grades, timestamp


def update_table_info(field, value, OCCASION, CLASS_GROUP, INSTANCE):
    timestamp = Dates.timestamp()
    db_update_field("GRADES_INFO", field, value,
        OCCASION=OCCASION,
        CLASS_GROUP=CLASS_GROUP,
        INSTANCE=INSTANCE
    )
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
    date_format = CONFIG["DATEFORMAT"]
    info: dict[str, str] = {
        info_transl["SCHOOLYEAR"]: SCHOOLYEAR,
        info_transl["CLASS_GROUP"]: class_group,
        info_transl["OCCASION"]: occasion,
        info_transl["INSTANCE"]: instance,
        info_transl["DATE_GRADES"]: Dates.print_date(DATE_GRADES, date_format),
        info_transl["DATE_ISSUE"]: Dates.print_date(DATE_ISSUE, date_format),
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
        exit_date = pdata["DATE_EXIT"]
        if exit_date and DATE_GRADES > exit_date:
            continue    # pupil has left the school
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


def load_from_file(
    filepath: str,
    occasion: str,
    class_group: str,
    instance: str = "",
):
    data = read_grade_table_file(filepath)
    # -> dict[str, dict[str, str]]
    info = data["__INFO__"]
    val = info.get("SCHOOLYEAR")
    if val != SCHOOLYEAR:
        raise GradeTableError(T["SCHOOLYEAR_MISMATCH"].format(val=val))
    val = info.get("OCCASION")
    if val != occasion:
        raise GradeTableError(T["OCCASION_MISMATCH"].format(val=val))
    val = info.get("CLASS_GROUP")
    if val != class_group:
        raise GradeTableError(T["CLASS_GROUP_MISMATCH"].format(val=val))
    val = info.get("OCCASION")
    if val != occasion:
        raise GradeTableError(T["INSTANCE_MISMATCH"].format(val=val))
    return data


def read_grade_table_file(
    filepath: str,
) -> dict[str, dict[str, str]]:
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
    header_map = grade_config["HEADERS"]
    info_map = {t: f for f, t in grade_config["INFO_FIELDS"]}
    datatable = read_DataTable(filepath)
    info = {(info_map.get(k) or k): v for k, v in datatable["__INFO__"].items()}
    ### Get the rows as mappings
    # fields = datatable["__FIELDS__"]
    pinfo_map = {}
    gdata: dict[str, dict[str, str]] = {
        "__INFO__": info,
        "__PUPILS__": pinfo_map,
    }
    group_data = get_group_data(info["OCCASION"], info["CLASS_GROUP"])
    valid_grades = get_valid_grades(group_data["GRADES"])
    for pdata in datatable["__ROWS__"]:
        pinfo = {h: pdata.pop(t) for h, t in header_map}
        pid: str = pinfo.pop("PID")
        if pid == "$":
            continue
        pinfo_map[pid] = pinfo
        gdata[pid] = pdata
        # Check validity of grades
        for k, v in pdata.items():
            if v and v not in valid_grades:
                REPORT(
                    "ERROR",
                    T["INVALID_GRADE"].format(
                        filepath=info["__FILEPATH__"],
                        pupil=pinfo["PUPIL"],
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

    print("\n*** occasions_groups:")
    for k, v in get_occasions_groups().items():
        print("\n  +++", k)
        for g, data in v.items():
            print("\b   --------", g)
            print(data)

    print("\n *** group data: class 13, Abitur")
    print(get_group_data("Abitur", "13"))


    # gtinfo = grade_table_info("1. Halbjahr", "12G.R")
    gtinfo = grade_table_info("Abitur", "13")
    # gtinfo = grade_table_info("2. Halbjahr", "12G.R")
#    print("\n*** SUBJECTS")
#    for val in gtinfo["SUBJECTS"]:
#        print("    ---", val)
    print("\n*** COLUMNS")
    for item in gtinfo.pop("COLUMNS"):
        print("\n    ---", item)
    print("\n*** GRADE_VALUES", gtinfo.pop("GRADE_VALUES"))
    print("\n*** PUPILS")
    for pid, pinfo in gtinfo.pop("PUPILS").items():
        pdata, p_grade_tids = pinfo
        print(f"\n +++ {pdata}")
        print(" .........", p_grade_tids)

    print("\n\n REMAINDER:\n", gtinfo)

    full_grade_table("Abitur", "13", "")

    quit(0)

    _o = "1. Halbjahr"
    _cg = "13"
    _i = ""
    path = OPEN_FILE("Tabelle (*.xlsx *.ods *.tsv)")
    if path:
        pid2grades = load_from_file(
            filepath=path,
            occasion=_o,
            class_group=_cg,
            instance=_i,
        )
        # Merge in pupil info
        for pid, pinfo in pid2grades["__PUPILS__"].items():
            pid2grades[pid].update(pinfo)
        print("\n\n ************ pid2grades **********************\n", pid2grades)
        print("\n\n *********************************\n")
        gt = full_grade_table(_o, _cg, _i, pid2grades)

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

    print("\n******************************************************")

    #grade_table = full_grade_table("1. Halbjahr", "12G.R", "").items()
    #grade_table = full_grade_table("1. Halbjahr", "13", "").items()
    grade_table = full_grade_table("Kursnoten", "13", "Klausur 1").items()

    print("\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

    for k, v in grade_table:
        print("\n =======", k, "\n", v)

    #print("\n&&&&&&&&&&&&&&&&&", get_group_data("1. Halbjahr", "13"))
