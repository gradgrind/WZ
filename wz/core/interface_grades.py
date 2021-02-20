# -*- coding: utf-8 -*-

"""
core/interface_grades.py - last updated 2021-02-20

Controller/dispatcher for grade management.

==============================
Copyright 2021 Michael Towers

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

#TODO ...

### Messages


from core.base import Dates
from local.base_config import year_path
from local.grade_config import GradeBase, UNCHOSEN
from grades.gradetable import FailedSave, GradeTableFile, \
        GradeTable, GradeTableError, Grades
from grades.makereports import GradeReports


class GradeManager:
#?
    def init(cls):
        CALLBACK('grades_SET_TERMS', terms = GradeBase.terms())
        return True
#
    def set_term(cls, term):
        self.term = term
        groups = [grp for grp, rtype in
                GradeBase.term2group_rtype_list(term[0])]
        CALLBACK('grades_SET_GROUPS', groups = groups)
#
    def set_group(cls, group):
        self.group = group
        self.grade_table = GradeTable(schoolyear, group, term,
                ok_new = True)
        # Separate out "component" subjects
        main_sids = {}
        components = {}
        for sid, name in self.grade_table.subjects.items():
            if sid in self.grade_table.components:
                components[sid] = name
            else:
                main_sids[sid] = name
        ## Get lists of acceptable values for "selection" fields
        selects = []
        # for grades:
        selects.append(('grade', Grades.group_info(group, 'NotenWerte')))
        # for "extra" fields:
        for sid, name in self.grade_table.extras.items():
            if sid == '*ZA':
                _ZA_vals = Grades.group_info(group, f'*ZA/{term[0]}')
                selects.append((sid, _ZA_vals))
                ZA_default = _ZA_vals[0] if _ZA_vals else ''
#            elif sid.endswith('_D'):
#                'DATE'
            elif sid == '*Q':
                selects.append((sid, Grades.group_info(group, '*Q')))






FUNCTIONS['GRADES_set_term'] = GradeManager.set_term
