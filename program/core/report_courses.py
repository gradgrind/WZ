"""
core/report_courses.py

Last updated:  2022-09-03

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

from core.db_access import db_read_fields
from core.basic_data import get_classes

COURSE_FIELDS = (
    "CLASS",
    "GRP",
    "SUBJECT",
    "TEACHER",
    "REPORT",
    "GRADE",
    "COMPOSITE"
)

### -----


class ReportSubjectData(NamedTuple):
    klass: str
    group: str
    sid: str
    tid: str
    report: str
    grade: str
    composite: str


def get_subjects_data() -> dict[str,list[ReportSubjectData]]:
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


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from core.db_access import open_database
    open_database()

    data = get_subjects_data()
    for k in sorted(data):
        print("\nCLASS:", k)
        for rsdata in data[k]:
            print("  ---", rsdata)
