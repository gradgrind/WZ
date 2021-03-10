# -*- coding: utf-8 -*-

"""
core/interface_grades.py - last updated 2021-02-27

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

### Messages

### Labels, etc.
_ALL_PUPILS = "Gesamttabelle"
_NEW_REPORT = "Neues Zeugnis"
_EXCEL_FILE = "Excel-Datei (*.xlsx)"
_TABLE_FILE = "Tabellendatei (*.xlsx *.ods *.tsv)"


import glob

from core.base import Dates
from local.base_config import year_path
from local.grade_config import GradeBase, UNCHOSEN
from local.abitur_config import AbiCalc
from grades.gradetable import FailedSave, GradeTableFile, \
        GradeTable, GradeTableError, Grades
from grades.makereports import GradeReports


class GradeManager:
    @staticmethod
    def init():
        CALLBACK('grades_SET_TERMS', terms = GradeBase.terms(), term = '')
        return True
#
    @classmethod
    def set_term(cls, term):
        cls.term = term
        groups = [grp for grp, rtype in
                GradeBase.term2group_rtype_list(term)]
        CALLBACK('grades_SET_GROUPS', groups = groups)
        return True
#
    @classmethod
    def set_group(cls, group):
        """<group> may be <None>. This is used to preserve <cls.group>.
        """
        if group:   #?
            cls.group = group
#?
        cls.pid = ''
        gtable = GradeTable(SCHOOLYEAR, cls.group, cls.term, ok_new = True)
        cls.grade_table = gtable
        # Separate out "component" subjects
        cls.main_sids = []
        cls.components = []
        for sid, name in gtable.subjects.items():
            if sid in gtable.components:
                cls.components.append((sid, name))
            else:
                cls.main_sids.append((sid, name))
        # Fetch "composite" subjects and "calculated" fields
        cls.composites = [(sid, name)
                for sid, name in gtable.composites.items()]
        cls.calcs = [(sid, name)
                for sid, name in gtable.calcs.items()]
        ## Get lists of acceptable values for "selection" fields
        selects = []
        # for grades:
        selects.append(('grade', Grades.group_info(cls.group, 'NotenWerte')))
        # for "extra" fields:
        cls.extras = []
        for sid, name in gtable.extras.items():
            cls.extras.append((sid, name))
            if sid == '*ZA':
                _ZA_vals = Grades.group_info(group, f'*ZA/{cls.term[0]}')
                selects.append((sid, _ZA_vals))
            elif sid == '*Q':
                selects.append((sid, Grades.group_info(group, '*Q')))

        term0 = cls.term[0]
        if term0 in ('S', 'T'): # special reports or test results
            termnull = term0 + '*'
            cls.term = cls.pid if cls.pid else termnull
            # Get list of existing reports for the group
            table_path = year_path(SCHOOLYEAR,
                    GradeBase.table_path(cls.group, termnull))
            date_list = sorted([f.rsplit('_', 1)[1].split('.', 1)[0]
                    for f in glob.glob(table_path)], reverse = True)
            if group and date_list:
                # Show next date
                today = Dates.today()
                for date in date_list:
                    if today > date:
                        break
                    # Select this date initially
                    cls.pid = term0 + date
                    cls.term = cls.pid
            # Note that the "pupil" list is in this case not that at all,
            # but a list of report dates:
            plist = [('', _NEW_REPORT)] + [(term0 + d, d) for d in date_list]
        else:
            pid_names = [(pid, name)
                    for pid, name in gtable.name.items()]
            plist = [('', _ALL_PUPILS)] + pid_names
        CALLBACK('grades_SET_PUPILS', termx = cls.term, group = cls.group,
                pid_name_list = plist, pid = cls.pid)
        CALLBACK('grades_SET_GRID',
                info = (
                        (gtable.SCHOOLYEAR, gtable.schoolyear, ''),
                        (gtable.GROUP, gtable.group, ''),
                        (gtable.TERM, gtable.term, ''),
                        (gtable.GRADES_D, gtable.grades_d, 'GRADES_D'),
                        (gtable.ISSUE_D, gtable.issue_d, 'ISSUE_D')
                    ),
                main_sids = cls.main_sids,
                components = cls.components,
                composites = cls.composites,
                calcs = cls.calcs,
                extras = cls.extras,
                selects = selects,
                pupil_data = cls.group_grades()
        )
        return True
#
    @classmethod
    def group_grades(cls):
        """Prepare the grade data for passing to the grid.
        """
        # Pupil lines
        rows = []
        for pid, grades in cls.grade_table.items():
            pname = cls.grade_table.name[pid]
            gmap = {}
            row = [pid, pname, grades.stream, gmap]
            rows.append(row)
            for sid, _ in cls.main_sids:
                gmap[sid] = grades.get(sid, UNCHOSEN)
            for sid, _ in cls.components:
                gmap[sid] = grades.get(sid, UNCHOSEN)
            for sid, _ in cls.composites:
                gmap[sid] = grades[sid]
            if cls.calcs:
                for sid, g in cls.grade_table.recalc(pid):
                    gmap[sid] = g
            for sid, _ in cls.extras:
                gmap[sid] = grades[sid]
        return rows
#
    @classmethod
    def grade_changed(cls, pid, sid, val):
        updates = []
        grades = cls.grade_table[pid]
        # Update the grade, includes special handling for numbers
        grades.set_grade(sid, val)
        if sid in cls.grade_table.extras:
# also save these? ... at least the persistent ones ...
            return
        # If it is a component, recalculate the composite
        if sid in cls.grade_table.components:
            csid = cls.grade_table.sid2subject_data[sid].composite
            if csid == UNCHOSEN:
                # There is no "real" composite
                return
            grades.composite_calc(
                    cls.grade_table.sid2subject_data[csid])
            updates.append((pid, csid, grades[csid]))
        # Recalculate the averages, etc.
        for sid, val in cls.grade_table.recalc(pid):
            updates.append((pid, sid, val))
        if updates:
            CALLBACK('grades_SET_GRADES', grades = updates)
        return True
#
    @classmethod
    def value_changed(cls, tag, val):
        if tag = 'GRADES_D':
            cls.grade_table.grades_d = val
        elif tag = 'ISSUE_D':
            cls.grade_table.issue_d = val
        # Other tags are ignored.
#TODO: other relevant tags (for tests or Abi or specials)?
#
    @classmethod
    def save(cls):
        cls.grade_table.save()
#TODO: There could be a new tag or group?
# So like init, but retaining "term", tag, group, pid (where relevant)
# Like <set_term>?
# ... maybe not a new group?
        CALLBACK('grades_???')
        return True
#
    @classmethod
    def make_table(cls, filepath = None):
        """Produce an xlsx-table containing the group's grades.
        This is especially useful for entering grades.
        If no <filepath> is given, there will be a callback to the
        front-end to supply one (and then call this function again).
        """
        gtable = cls.grade_table
        if filepath:
            qbytes = gtable.make_grade_table()
            with open(filepath, 'wb') as fh:
                fh.write(bytes(qbytes))
        else:
            filename = os.path.basename(GradeBase.table_path(
                    gtable.group, gtable.term, gtable.subselect)) + '.xlsx'
            CALLBACK('*SAVE_FILE*', filetype = _EXCEL_FILE,
                    filename = filename, callback = 'GRADES_make_table')
        return True






#+++++++++++++++ Abitur +++++++++++++++#

    @classmethod
    def set_abi_pupil(cls, pid):
        """A new pupil has been selected: reset the grid accordingly.
        """
        cls.pid = pid
        # Set pupil's name (NAME) and completion date (FERTIG_D)
        gtable = cls.grade_table
        cells = []  # [(tag, value), ... ] -> use <set_text>
        cells.append(('SCHOOLYEAR', gtable.schoolyear))
        cells.append(('NAME', gtable.name[pid]))
        CALLBACK('abitur_SET_CELLS', data = cells)
        cls.abi_calc = AbiCalc(gtable, pid)
        # Set date of completion: if no value for pupil, use group date
        cls.abi_calc.set_editable_cell('FERTIG_D',
                cls.abi_calc.grade_map['*F_D'] or gtable.grades_d)
        # Set subject names and grades
        allvals = cls.abi_calc.all_values()
        cells = []  # [(tag, value), ... ] -> use <set_text_init>
        for tag, val in allvals:
            if tag[0] != '*':
                cells.append((tag, val))
        CALLBACK('abitur_INIT_CELLS', data = cells)
        cls.update_abi_calc()
        return True
#
    @classmethod
    def update_abi_calc(cls):
        """Update all the calculated parts of the grid from the current
        grades.
        """
        cells = []
        for tag, val in cls.abi_calc.calculate().items():
            cells.append((tag, val))
        CALLBACK('abitur_SET_CELLS', data = cells)
#
    @classmethod
    def abi_set_value(cls, tag, val):
# Save in grade_table?
        if tag.startswith('GRADE_'):
            cls.abi_calc.set_editable_cell(tag, val)
            cls.update_abi_calc()
        elif tag == 'FERTIG_D':
            cls.abi_calc.set_editable_cell(tag, val)
        else:
            raise Bug("Invalid cell change, %s: %s" % (tag, val))
        return True
#
    @classmethod
    def save_abi(cls):
        """Collect the fields to be saved and pass them to the
        <GradeTable> method.
        """
        pgtable = cls.grade_table[self.pid]
        pgtable.set_grade('*F_D', cls.abi_calc.value('FERTIG_D'))
        for s, g in cls.abi_calc.get_all_grades():
            pgtable.set_grade(s, g)
#TODO: also '*ZA'?
        cls.grade_table.save()
        CALLBACK('abitur_???')
        return True



FUNCTIONS['GRADES_init'] = GradeManager.init
FUNCTIONS['GRADES_set_term'] = GradeManager.set_term
FUNCTIONS['GRADES_set_group'] = GradeManager.set_group
FUNCTIONS['GRADES_subselect'] = GradeManager.subselect
FUNCTIONS['GRADES_grade_changed'] = GradeManager.grade_changed
FUNCTIONS['GRADES_save'] = GradeManager.save
FUNCTIONS['GRADES_make_table'] = GradeManager.make_table
#?
FUNCTIONS['ABITUR_set_pupil'] = GradeManager.set_abi_pupil
FUNCTIONS['ABITUR_set_value'] = GradeManager.abi_set_value
FUNCTIONS['ABITUR_save_current'] = GradeManager.save_abi
