"""
core/report_courses.py

Last updated:  2022-09-09

Access course/subject data for reports.

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

###############################################################

if __name__ == "__main__":
    # Enable package import if running as module
    import sys, os

    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    # start.setup(os.path.join(basedir, "TESTDATA"))
    start.setup(os.path.join(basedir, "DATA-2023"))

T = TRANSLATIONS("core.report_courses")

### +++++

from typing import NamedTuple

from core.db_access import db_read_table#, db_read_fields
from core.base import class_group_split
from core.basic_data import get_classes, SHARED_DATA, get_subjects_with_sorting
from core.classes import atomic_maps
from core.pupils import pupils_in_group, pupil_name


COURSE_FIELDS = (
    "GRP",
    "SUBJECT",
    "TEACHER",
    "REPORT",
)

### -----


class ReportSubjectData(NamedTuple):
#?
    klass: str

    group: str
    sid: str
    tid: str
    report: str


#? Rather use class-based version below? And caching! ...
'''def get_subjects_data() -> dict[str,list[ReportSubjectData]]:
    """Return subject information for all classes as a mapping.
    Each class has a list of <ReportSubjectData> instances.
    """
    # Get group info for checking groups
    __classes = get_classes()
    class2groups = {
        klass: __classes.group_info(klass)["GROUP_MAP"]
        for klass, _ in __classes.get_class_list()
    }

    class2subjects = {}
    for klass, group, sid, tid, report, grade, composite in db_read_fields(
        "COURSES", COURSE_FIELDS
    ):
        # CLASS, SUBJECT and TEACHER are foreign keys and should be
        # automatically bound to appropriate entries in the database.
        # GRP should be checked here ...
        if group and group not in class2groups[klass]:
            if klass != "--" and group != "*":
                REPORT(
                    "ERROR",
                    T["UNKNOWN_GROUP"].format(
                        klass=klass,
                        group=group,
                        sid=sid,
                        tid=tid,
                    )
                )
                continue
        data = ReportSubjectData(
            klass=klass,
            group=group,
            sid=sid,
            tid=tid,
            report=report,
            grade=grade,
            composite=composite,
        )
        try:
            class2subjects[klass].append(data)
        except KeyError:
            class2subjects[klass] = [data]
    return class2subjects
'''


def get_class_subjects(klass):
    """Return a list of data mappings, one for each "course" within the
    given class.
    This data is cached, so subsequent calls get the same instance.
    """
    key = f"SUBJECTS_{klass}"
    try:
        return SHARED_DATA[key]
    except KeyError:
        pass
    # Get group info for checking groups
    group_map = get_classes().group_info(klass)["GROUP_MAP"]
    rsdata = []
    for group, sid, tid, report in db_read_table(
        "COURSES", COURSE_FIELDS, CLASS=klass
    )[1]:
        # CLASS, SUBJECT and TEACHER are foreign keys and should be
        # automatically bound to appropriate entries in the database.
        # GRP should be checked here ...
        if group and (group != "*") and group not in group_map:
            REPORT(
                "ERROR",
                T["UNKNOWN_GROUP"].format(
                    klass=klass,
                    group=group,
                    sid=sid,
                    tid=tid,
                )
            )
            continue
        rsdata.append(
            ReportSubjectData(
#?
                klass=klass,

                group=group,
                sid=sid,
                tid=tid,
                report=report,
            )
        )
    SHARED_DATA[key] = rsdata
    return rsdata


def get_pupil_grade_matrix(class_group, text_reports=True):
    """Return a list of report subjects for the given group and for each
    subject the relevant teachers for each pupil in the group.
    """
    subject_map = get_subjects_with_sorting()
    # If I select the whole class, I want all courses (with pupils).
    # If I select group B, I want all courses available to some pupils
    # in group B.
    # Basically, a course should be included if it is possible for a
    # pupil of the given group to take part. Thus a subject-group should
    # only be excluded if it is empty or if it is in the same division
    # as the pupil-group, but distinct from it. The filtering is done by
    # comparing "atomic" groups (minimal sub-groups).
    klass, group = class_group_split(class_group)
    group_info = get_classes().group_info(klass)
    atoms = group_info["MINIMAL_SUBGROUPS"]
    subjects_data = get_class_subjects(klass)
    group2atoms = atomic_maps(atoms, list(group_info["GROUP_MAP"]))
    pupils = []
    for pdata in pupils_in_group(class_group):
        pgroups = pdata["GROUPS"]
        if pgroups:
            try:
                atoms = set(group2atoms['']).intersection(
                    *(group2atoms[g] for g in pgroups.split())
                )
                if not atoms:
                    raise KeyError
            except KeyError:
                REPORT(
                    "ERROR",
                    T["INVALID_GROUPS_FIELD"].format(
                        klass=klass,
                        pupil=pupil_name(pdata),
                        groups=pgroups
                    )
                )
                continue
        else:
            atoms = set(group2atoms[''])
        pupils.append((pdata, atoms, {}))
#        print("%%%", pupils[-1])
    tgroups = set(group2atoms[group])
    subject_set = {}
    for sdata in get_class_subjects(klass):
        report_flags = sdata.report.split('/', 1)[0]
        if text_reports:
            if 'A' not in report_flags:
                continue
        elif '1' not in report_flags:
            continue
        g = sdata.group
        if not g:
            continue
        if g == '*':
            g = ''
        s_atoms = set(group2atoms[g])
        if (not group) or tgroups.intersection(s_atoms):
            sid = sdata.sid
            subject_set[sid] = subject_map[sid]
            sid0 = '#' + sid.split('.')[0]
            for pdata, p_atoms, p_grade_tids in pupils:
                if s_atoms.intersection(p_atoms):
                    # Check for subjects with multiple entries (same
                    # sid/subject, but different sid-qualifiers).
                    # To this end there are "dummy" entries in
                    # <p_grade_tids> (key <sid0>) whose value is the
                    # first <sid> used for the subject.
                    try:
                        sid1 = p_grade_tids[sid0]
                    except KeyError:
                        p_grade_tids[sid0] = sid
                    else:
                        if sid1 != sid:
                            REPORT(
                                "ERROR",
                                T["PUPIL_HAS_MULTIPLE_SID"].format(
                                    klass=klass,
                                    pupil=pupil_name(pdata),
                                    subject=subject_map[sid][2].split('*')[0]
                                )
                            )
                    # Add teacher to set
                    tid = sdata.tid
                    if tid != '--':
                        try:
                            p_grade_tids[sid].add(tid)
                        except KeyError:
                            p_grade_tids[sid] = {tid}
    return subject_set, pupils


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from core.db_access import open_database
    open_database()

    for rsdata in get_class_subjects("11G"):
        print("  ---", rsdata)

    '''data = get_subjects_data()
    for k in sorted(data):
        print("\nCLASS:", k)
        for rsdata in data[k]:
            print("  ---", rsdata)
    '''

    kg = "12G.R"
    subjects, pupils = get_pupil_grade_matrix(kg, text_reports=False)
    print("\n SUBJECTS FOR GROUP", kg)
    for s in sorted(subjects.values()):
        print(" +++", s)

    print("\n PUPILS:")
    for pdata, p_atoms, p_grade_tids in pupils:
        print(" +++", pupil_name(pdata))
        print("            ", p_grade_tids)

