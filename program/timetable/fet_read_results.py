"""
timetable/fet_read_results.py - last updated 2022-10-28

Fetch the placements after a fet run and update the database accordingly.
There is also a function to generate an aSc-file.

==============================
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
"""

########################################################################

import sys, os

if __name__ == "__main__":
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    # TODO: Temporary redirection to use real data (there isn't any test data yet!)
    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    #    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))

from typing import Optional

#T = TRANSLATIONS("timetable.fet_data")
#Tc = TRANSLATIONS("timetable.constraints_class")

### +++++

import xmltodict

from core.db_access import db_backup, db_update_fields
from ui.ui_base import QFileDialog

### -----

def read_fet_file(xmlfile):
    """Read the fet file used to generate the timetable.
    Only the activities and their placements are read.
    The activities contain the lesson-id in the "Comments" field.
    Return a mapping {activity-id -> lesson-id} and a set of "locked"
    activity-ids.
    """
    with open(xmlfile, "rb") as fh:
        xml = fh.read()
    activity_data = xmltodict.parse(xml)["fet"]
    activities = activity_data["Activities_List"]["Activity"]
    a2lid = {}
    for activity in activities:
        lid = activity["Comments"]
        if lid:
            a2lid[activity["Id"]] = lid
    placements = activity_data["Time_Constraints_List"][
        "ConstraintActivityPreferredStartingTime"
    ]
    locked_set = set()
    for placement in placements:
        if placement["Permanently_Locked"] == "true":
            locked_set.add(placement["Activity_Id"])
    return a2lid, locked_set


def read_placements(fet_file, placement_file):
    """Get the preset placements from a fet "activities" file (passed
    as a file path) generated by a successful run of fet.
    The lesson identifiers and the "locked" status is obtained from the
    original data.
    """
    # Get the activity data
    activity2lesson, locked_activities = read_fet_file(fet_file)
    # Get the placement data
    with open(placement_file, "rb") as fh:
        xml = fh.read()
    pos_data = xmltodict.parse(xml)
    pos_list = pos_data["Activities_Timetable"]["Activity"]
    for p in pos_list:
        aid = p["Id"]
        lesson_id = activity2lesson.get(aid)
        if lesson_id and p['Day']:
            # Non-placed activities have no day, they must be skipped.
            field_values = [("PLACEMENT", f"{p['Day']}.{p['Hour']}")]
            room = p['Room']
            if room:
                rlist = p.get('Real_Room')
                if rlist:
                    field_values.append(("ROOMS", ','.join(rlist)))
                else:
                    field_values.append(("ROOMS", room))
            # print("§§§", lesson_id, field_values)
            db_update_fields("LESSONS", field_values, id=int(lesson_id))


def getActivities(working_folder):
#TODO: T ...
    d = QFileDialog(None, "Open fet 'activities' file", "", "'Activities' Files (*_activities.xml)")
    d.setFileMode(QFileDialog.ExistingFile)
    d.setOptions(QFileDialog.DontUseNativeDialog)
    history_file = os.path.join(working_folder, "activities_history")
    if os.path.isfile(history_file):
        with open(history_file, "r", encoding="utf-8") as fh:
            history = fh.read().split()
        d.setHistory(history)
        if history:
            print("$$$", history)
            d.setDirectory(history[0])
    d.exec()
    files = d.selectedFiles()
    if files:
        with open(history_file, "w", encoding="utf-8") as fh:
            fh.write("\n".join(d.history()[-10:]))
        return files[0]
    return None


def make_asc_file(asc_file):
    from timetable.asc_data import (
        TimetableCourses,
        get_subjects_aSc,
        get_teachers_aSc,
        get_days_aSc,
        get_periods_aSc,
        get_rooms_aSc,
        get_classes_aSc,
        get_groups_aSc,
        build_dict,
    )
    days = get_days_aSc()
    periods = get_periods_aSc()
    allrooms = get_rooms_aSc()
    classes = get_classes_aSc()
    groups = get_groups_aSc()
    courses = TimetableCourses()
    courses.read_class_lessons()
    allsubjects = get_subjects_aSc(courses.timetable_subjects)
    teachers = get_teachers_aSc(courses.timetable_teachers)
    xml_aSc = xmltodict.unparse(
        build_dict(
            ROOMS=allrooms,
            PERIODS=periods,
            TEACHERS=teachers,
            SUBJECTS=allsubjects,
            CLASSES=classes,
            GROUPS=groups,
            LESSONS=courses.asc_lesson_list,
            CARDS=courses.asc_card_list,
            # CARDS = [],
        ),
        pretty=True,
    )

    with open(asc_file, "w", encoding="utf-8") as fh:
        fh.write(xml_aSc.replace("\t", "   "))
#TODO: T ...
    REPORT("INFO", f"TIMETABLE XML -> {asc_file}")


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from shutil import copyfile
    from core.db_access import open_database

    open_database()

    outdir = DATAPATH("TIMETABLE/out")
    os.makedirs(outdir, exist_ok=True)
    placements = getActivities(outdir)
    ending = "_activities.xml"
    if placements:
        if placements.endswith(ending):
            pfile = os.path.basename(placements)
            pbase = pfile[:-(len(ending))]
            if True:
#                db_backup()
                fet_file = os.path.join(outdir, pbase + ".fet")
                pxfile = os.path.join(outdir, pfile)
                if pxfile != placements:
                    copyfile(placements, pxfile)
                # print(f"Reading from\n  {fet_file} and\n  {placements}")
                read_placements(fet_file, pxfile)
#
#                quit(0)

                db_backup(pbase)

            # Generate asc-file
            ascfile_redirect = os.path.join(outdir, "ascdir")
            if os.path.isfile(ascfile_redirect):
                with open(ascfile_redirect, "r", encoding="utf-8") as fh:
                    odir = fh.read().strip()
            else:
                odir = QFileDialog.getExistingDirectory(
                    None,
#TODO: T ...
                    "Open Directory",
                    options = (
                        QFileDialog.DontUseNativeDialog
                        #| QFileDialog.ShowDirsOnly
                    )
                )
                with open(ascfile_redirect, "w", encoding="utf-8") as fh:
                    fh.write(odir)
            asc_file = os.path.join((odir or outdir), pbase + "_asc.xml")
            make_asc_file(asc_file)
        else:
#TODO: T ...
            REPORT("ERROR", f"Placements file-name must end with '{ending}'")

    quit(0)

#TODO?
    # ??? tag-lids are gone, and multirooms are now available as virtual rooms
    import json

    outpath = os.path.join(outdir, "tag-lids.json")
    # Save association of lesson "tags" with "lids" and "xlids"
    lid_data = {
        "tag-lids": _classes.tag_lids,
        "lid-xlids": {lids[0]: lids[1:] for lids in _classes.xlids},
    }
    with open(outpath, "w", encoding="utf-8") as fh:
        json.dump(lid_data, fh, indent=4)
    print("\nTag – Lesson associations ->", outpath)

    outpath = os.path.join(outdir, "multiple-rooms")
    with open(outpath, "w", encoding="utf-8") as fh:
        for mr in _classes.multirooms:
            groups = ", ".join(mr["GROUPS"])
            sname = _classes.SUBJECTS[mr["SID"]]
            fh.write(
                f"\nKlasse {mr['CLASS']} ({groups})"
                f" :: {sname}: {mr['NUMBER']}"
            )

    print("\nSubjects with multiple rooms ->", outpath)
