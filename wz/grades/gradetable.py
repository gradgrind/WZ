# -*- coding: utf-8 -*-
"""
grades/gradetable.py - last updated 2021-03-24

Access grade data, read and build grade tables.

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
_INVALID_INFO_KEY = "Ungüliges INFO-Feld ({key}) in Notentabelle:\n  {fpath}"
_TABLE_CLASS_MISMATCH = "Falsche Klasse/Gruppe in Notentabelle:\n  {fpath}"
_TABLE_TERM_MISMATCH = "Falscher \"Anlass\" in Notentabelle:\n  {fpath}"
_TABLE_YEAR_MISMATCH = "Falsches Schuljahr in Notentabelle:\n  {fpath}"
_PIDS_NOT_IN_GROUP = "Schüler nicht in Gruppe {group}: {pids}"
_WARN_EXTRA_PUPIL = "Unerwarteter Schüler ({name}) in" \
        " Notentabelle:\n  {tfile}"
_WARN_EXTRA_SUBJECT = "Unerwartetes Fach ({sid}) in" \
        " Notentabelle:\n  {tfile}"
_ERROR_OVERWRITE2 = "Neue Note für {name} im Fach {sid} mehrmals" \
        " vorhanden:\n  {tfile1}\n  {tfile2}"
_WARN_OVERWRITE = "Geänderte Note für {name} im Fach {sid}:\n  {tfile}"
_NEW_GRADE_EMPTY = "Bug: leeres Notenfeld für {name} im Fach {sid}:\n  {tfile}"
_BAD_GRADE = "Ungültige Note im Fach {sid}: {g}"
_NO_DATE = "Kein Notendatum angegeben"
#_DATE_EXISTS = "Ausgabedatum existiert schon"

_TITLE2 = "Tabelle erstellt am {time}"


import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

import datetime
from fractions import Fraction
from collections import namedtuple

from core.base import Dates
from core.pupils import PUPILS
from core.courses import Subjects
from tables.spreadsheet import Spreadsheet, TableError, make_db_table
from tables.matrix import KlassMatrix
from tables.datapack import get_pack, save_pack
from local.base_config import DECIMAL_SEP, USE_XLSX, year_path, NO_DATE
from local.grade_config import GradeBase, UNCHOSEN, NO_GRADE, \
        GRADE_INFO_FIELDS, GradeConfigError
from local.abitur_config import AbiCalc

class GradeTableError(Exception):
    pass

class FailedSave(Exception):
    pass

###

class _Grades(GradeBase):
    """A <_Grades> instance manages the set of grades in the database for
    a pupil and "term".
    """
#    def __init__(self, group, stream, term):
#        super().__init__(group, stream, term)
#
    def init_grades(self, gmap):
        """Initialize the subject-grade mapping.
        This cannot be in <__init__> because the <_Grades> instance may
        be needed to prepare the grades (if they depend on group/term).
        """
        for sid, g in gmap.items():
            self.set_grade(sid, g)
#
    def filter_grade(self, sid, g):
        """Return the possibly filtered grade <g> for the subject <sid>.
        Integer values are stored additionally in the mapping
        <self.i_grade> – only for subjects with numerical grades, others
        are set to -1.
        """
        if sid[0] == '*':
            # An "extra" field – there may be default values ...
            return self.extras_default(sid, g)
        # There can be normal, empty, non-numeric and badly-formed grades
        gi = -1     # integer value
        if g:
            if g in self.valid_grades:
                # Separate out numeric grades, ignoring '+' and '-'.
                # This can also be used for the Abitur scale, though the
                # stripping is superfluous.
                try:
                    gi = int(g.rstrip('+-'))
                except ValueError:
                    pass
            else:
                REPORT('ERROR', _BAD_GRADE.format(sid = sid, g = g))
                g = ''
        else:
            g = ''  # ensure that the grade is a <str>
        self.i_grade[sid] = gi
        return g
#
    def set_grade(self, sid, grade):
        """Update a single grade.
        """
        self[sid] = self.filter_grade(sid, grade)
#
    def composite_calc(self, sdata):
        """Recalculate a composite grade.
        <sdata> is the subject-data for the composite, the (weighted)
        average of the components will be calculated, if possible.
        If there are no numeric grades, choose NO_GRADE, unless all
        components are UNCHOSEN (in which case also the composite will
        be UNCHOSEN).
        """
        asum = 0
        ai = 0
        non_grade = UNCHOSEN
        for csid, weight in sdata.composite:
            gi = self.i_grade[csid]
            if gi >= 0:
                ai += weight
                asum += gi * weight
            elif self[csid] != UNCHOSEN:
                non_grade = NO_GRADE
        if ai:
            g = Frac(asum, ai).round()
            self[sdata.sid] = self.grade_format(g)
            self.i_grade[sdata.sid] = int(g)
        else:
            self[sdata.sid] = non_grade

###

class Frac(Fraction):
    """A <Fraction> subclass with custom <truncate> and <round> methods
    returning strings.
    """
    def truncate(self, decimal_places = 0):
        if not decimal_places:
            return str(int(self))
        v = int(self * 10**decimal_places)
        sval = ("{:0%dd}" % (decimal_places+1)).format(v)
        return (sval[:-decimal_places] + DECIMAL_SEP + sval[-decimal_places:])
#
    def round(self, decimal_places = 0):
        f = Fraction(1,2) if self >= 0 else Fraction(-1, 2)
        if not decimal_places:
            return str(int(self + f))
        v = int(self * 10**decimal_places + f)
        sval = ("{:0%dd}" % (decimal_places+1)).format(v)
        return (sval[:-decimal_places] + DECIMAL_SEP + sval[-decimal_places:])

###

class _GradeTable(dict):
    """Manage the grade data for a term (etc.) and group.
    <term> need not actually be a "school term", though it may well be.
    It is used rather to specify the "occasion" determining the issue
    of the reports.
    For each possible, valid combination of "term" and group there is
    a grade table (pupil-subject, with some general information).
    The class instance is a mapping: {pid -> <_Grades> instance}. The
    stream is available in the <_Grades> instance.
    Additional information is available as attributes:
        <group>: school-class/group, as specified in
                <GradeBase.REPORT_GROUPS>
        <term>: a string representing a valid "term" (school-term, etc.)
        <subselect>: depending on <term>, may be empty, 'STUDENT' or
                'TAG'.
        <schoolyear>: school-year
        <issue_d>: date of issue
        <grades_d>: date of grade finalization
        <sid2subject_data>: {sid -> subject_data} also for "special" sids
        <subjects>: {sid -> subject-name}   (just "real" sids)
        <composites>: {sid -> subject-name} ("composite" sids)
        <components>: set of "component" sids
        <extra>: {sid/tag -> text name} ("extra" data, treated as grade)
        <name>: {pid -> (short) name}
    """
#
    def __init__(self, schoolyear):
        super().__init__()
        self.schoolyear = schoolyear
        self.group = None
        self.term = None
        self.subselect = None
        self.issue_d = None
        self.grades_d = None
        self.sid2subject_data = None
        self.subjects = None
        self.composites = None
        self.extras = None
        self.name = {}
        self.calcs = None
        self.abicalc = None
#
    def _new_group_table(self, pids = None, grade_data = None):
        """Initialize an empty table for <self.group> and <self.term>.
        If <pids> is not null, only include these pupils.
        <grade_data> is a grade-table. It is used for including existing
        data in a current, non-finished table.
        """
        if grade_data:
            date = grade_data.get('ISSUE_D') or NO_DATE
            self.issue_d = date
            self.grades_d = grade_data.get('GRADES_D') or NO_DATE
            grade_maps = {}
            for pdata in grade_data['__PUPILS__']:
                grade_maps[pdata['PID']] = pdata['__DATA__']
        else:
            grade_maps = None
            ## Initialize the dates (issue at end of term, or end of year)
            if self.term in ('S', 'T'):
                # ... unless it is a special table
                date = NO_DATE
            else:
                calendar = Dates.get_calendar(self.schoolyear)
                try:
                    date = calendar['TERM_%d' % (int(self.term) + 1)]
                except:
                    date = calendar['LAST_DAY']
                else:
                    # Previous day, ensure that it is a weekday
                    td = datetime.timedelta(days = 1)
                    d = datetime.date.fromisoformat(date)
                    while True:
                        d -= td
                        if d.weekday() < 5:
                            date = d.isoformat()
                            break
            self.issue_d = date
            self.grades_d = NO_DATE

        ## Pupil information
        # Pupil data, select pupils
        pupils = PUPILS(self.schoolyear)
        pidset = set(pids) if pids else None
        for pdata in pupils.group2pupils(self.group, date = date):
            pid = pdata['PID']
            if pids:
                try:
                    pidset.remove(pid)
                except KeyError:
                    continue
            self.name[pid] = pupils.name(pdata)
            # Set grades
            try:
                gmap = grade_maps[pid]
            except:
                gmap = {}
            grades = _Grades(self.group, pdata['STREAM'], self.term)
            grades.init_grades(self._include_grades(grades, gmap))
            self[pid] = grades
            for comp in self.composites:
                grades.composite_calc(self.sid2subject_data[comp])
            if self.term == 'Abitur':
                grades.abicalc = AbiCalc(self, pid)
        if pidset:
            raise GradeTableError(_PIDS_NOT_IN_GROUP.format(
                    group = self.group, pids = ', '.join(pidset)))
#
    def _set_group_term(self, group, term, tag):
        """Set the subjects and extra pupil-data fields for the given
        group and term (and tag, in the case of TAG-subselects).
        """
        self.group = group
        self.term = term
        self.subselect = tag
        # Get subjects
        subjects = Subjects(self.schoolyear)
        self.sid2subject_data = {} # {sid -> subject_data}
        self.subjects = {}   # name-mapping just for "real" subjects
        self.composites = {} # name-mapping for composite sids
        self.components = set() # set of "component" sids
        for gs in subjects.grade_subjects(group):
            sid = gs.sid
            self.sid2subject_data[sid] = gs
            if gs.tids:
                # "real" (taught) subject
                self.subjects[sid] = gs.name
                if gs.composite:
                    self.components.add(sid)
            else:
                # "composite" subject
                self.composites[sid] = gs.name
        # data for "extra" sid-fields:
        self.extras = _Grades.xgradefields(group, term)
        # data for additional info fields, whose values are calculated
        # from the other fields:
        self.calcs = _Grades.calc_fields(group, term)
        if term == 'Abitur':
            # Modify for Abitur
            AbiCalc.subjects(self)
#
    def _include_grades(self, grades, gmap):
        """Return a grade mapping.
        Include grades for all subjects and extra entries.
        Initial values are taken from the mapping <gmap>: {sid -> grade}.
        The expected entries are set previously in method <_set_group_term>.
        """
        sid2grade = {}
        for sid in self.subjects:
            sid2grade[sid] = gmap.get(sid) or ''
        for comp in self.composites:
            sid2grade[comp] = gmap.get(comp) or ''
        for xsid in self.extras:
            # Where appropriate use default values
            sid2grade[xsid] = grades.extras_default(xsid, gmap.get(xsid))
        return sid2grade
#
    def make_grade_table(self):
        """Build a basic pupil/subject table for grade input.
        The field names (and TERM value) will be localized.
        It will contain the existing grades. To get an empty table,
        initialize the <GradeTable> instance using method <new_group_table>.
        """
        ### Get template file
        template = GradeBase.group_info(self.group, 'NotentabelleVorlage')
        template_path = os.path.join(RESOURCES, 'templates',
                    *template.split('/'))
        table = KlassMatrix(template_path)

        ### Set title line
#        table.setTitle("???")
        table.setTitle2(Dates.timestamp())

        ### Translate and enter general info
        info = (
            (GRADE_INFO_FIELDS['SCHOOLYEAR'],    str(self.schoolyear)),
            (GRADE_INFO_FIELDS['GROUP'],         self.group),
            (GRADE_INFO_FIELDS['TERM'],          self.term),
            (GRADE_INFO_FIELDS['GRADES_D'],      self.grades_d),
            (GRADE_INFO_FIELDS['ISSUE_D'],       self.issue_d)
        )
        table.setInfo(info)
        ### Go through the template columns and check if they are needed:
        sidcol = []
        col = 0
        rowix = table.row0()    # index of header row
        for sid, sname in self.subjects.items():
            # Add subject
            col = table.nextcol()
            sidcol.append((sid, col))
            table.write(rowix, col, sid)
            table.write(rowix + 1, col, sname)
        # Enforce minimum number of columns
        while col < 18:
            col = table.nextcol()
            table.write(rowix, col, None)
        # Delete excess columns
        table.delEndCols(col + 1)
        ### Add pupils
        for pid, gmap in self.items():
            row = table.nextrow()
            table.write(row, 0, pid)
            table.write(row, 1, self.name[pid])
            table.write(row, 2, gmap.stream)
            for sid, col in sidcol:
                g = gmap.get(sid)
                if g:
                    table.write(row, col, g)
        # Delete excess rows
        row = table.nextrow()
        table.delEndRows(row)
        ### Save file
        table.protectSheet()
        return table.save()
#
    def save(self, tag = None):
        """Save the data to the "database".
        """
        fields = []
        for sid in self.subjects:
            fields.append(sid)
        for xsid in self.extras:
            fields.append(xsid)
        # The calculated fields are not saved.
        # Get line data
        dlist = []
        for pid, grades in self.items():
            gmap = {}
            dmap = {'PID': pid, 'NAME': self.name[pid],
                    'STREAM': grades.stream, '__DATA__': gmap}
            for sid in fields:
                v = grades.get(sid)
                if v:
                    gmap[sid] = v
            dlist.append(dmap)
        # Get file path and write file
        table_path = year_path(self.schoolyear,
                GradeBase.table_path(self.group, self.term, tag))
        data = {
            'SCHOOLYEAR': self.schoolyear,
            'GROUP':      self.group,
            'TERM':       self.term,
            'GRADES_D':   self.grades_d,
            'ISSUE_D':    self.issue_d,
            '__PUPILS__': dlist,
            '__MODIFIED__': Dates.timestamp()
        }
#TODO: Title?
        return save_pack(table_path, **data)
#
    def recalc(self, pid):
        """Calculate the values for the "Calc" fields.
        Return a list: [(sid, val), ... ]
        """
        svlist = []
        for sid in self.calcs:
            if sid == '.D':
                svlist.append((sid, self.average(pid)))
            elif sid == '.Dx':
                svlist.append((sid, self.average_dem(pid)))
            elif sid == '.Q':
                try:
                    _ac = self[pid].abicalc
                except AttributeError:
                    pass
                else:
                    _amap = _ac.calculate()
                    svlist.append((sid, _amap['REPORT_TYPE']))
        return svlist
#
    def average(self, pid):
        """Calculate the average of all grades, including composites,
        but ignoring components and non-numerical grades.
        """
        asum = 0
        ai = 0
        grades = self[pid]
        for sid in self.subjects:
            if self.sid2subject_data[sid].composite:
                # A component
                continue
            gi = grades.i_grade[sid]
            if gi >= 0:
                asum += gi
                ai += 1
        for sid in self.composites:
            gi = grades.i_grade[sid]
            if gi >= 0:
                asum += gi
                ai += 1
        if ai:
            return Frac(asum, ai).round(2)
        else:
            return '–––'
#
    def average_dem(self, pid):
        """Special average for "Realschulabschluss": De-En_Ma only.
        """
        asum = 0
        ai = 0
        grades = self[pid]
        for sid in ('De', 'En', 'Ma'):
            gi = grades.i_grade[sid]
            if gi >= 0:
                asum += gi
                ai += 1
        if ai:
            return Frac(asum, ai).round(2)
        else:
            return '–––'

###

class GradeTableFile(_GradeTable):
    def __init__(self, schoolyear, filepath):
        """Read the header info and pupils' grades from the given table file.
        The "spreadsheet" module is used as backend so .ods, .xlsx and .tsv
        formats are possible. The filename may be passed without extension –
        <Spreadsheet> then looks for a file with a suitable extension.
        <Spreadsheet> also supports in-memory binary streams (io.BytesIO)
        with attribute 'filename' (so that the type-extension can be read).
        The <info> mapping of the table should contain the keys:
            'SCHOOLYEAR', 'GROUP', 'TERM', 'ISSUE_D', 'GRADES_D'
        Only the non-empty cells from the source table will be included.
        """
        super().__init__(schoolyear)
        ss = Spreadsheet(filepath)
        self.filepath = ss.filepath
        dbt = ss.dbTable()
        info = {}
        # Translate info field names using reversed mapping.
        rfields = {v: k for k, v in GRADE_INFO_FIELDS.items()}
        for row in dbt.info:
            if row[0]:
                key, val = row[:2]
                try:
                    key = rfields[key]
                except KeyError:
                    # Also accept unlocalized field names
                    if key not in GRADE_INFO_FIELDS:
                        raise GradeTableError(_INVALID_INFO_KEY.format(
                                key = key, fpath = self.filepath))
                info[key] = val
        self.issue_d = info.get('ISSUE_D') or NO_DATE
        self.grades_d = info.get('GRADES_D') or NO_DATE
        term = info.get('TERM').replace(' ', '_')
        subsel = GradeBase.term_info(term, 'subselect')
        self._set_group_term(info.get('GROUP'), term,
                self.grades_d if subsel == 'TAG' else None)
        year = info.get('SCHOOLYEAR')
        if year != str(self.schoolyear):
            raise GradeTableError(_TABLE_YEAR_MISMATCH.format(
                        fpath = filepath))
        sid2col = []
        col = 0
        for f in dbt.fieldnames():
            if col > 2:
                if f[0] != '$':
                    # This should be a subject tag
                    if f in self.subjects or f in self.extras:
                        sid2col.append((f, col))
                    else:
                        REPORT('WARN', _WARN_EXTRA_SUBJECT.format(sid = f,
                                tfile = self.filepath))
            col += 1
        # Only include non-empty cells from the source table
        for row in dbt:
            pid = row[0]
            if pid and pid != '$':
                gmap = {}
                for sid, col in sid2col:
                    val = row[col]
                    if val:
                        gmap[sid] = val
                self.name[pid] = row[1]
                grades = _Grades(self.group, row[2], self.term)
                #grades.init_grades(self._include_grades(grades, gmap))
                grades.init_grades(gmap)
                self[pid] = grades

###

class NewGradeTable(_GradeTable):
    """An empty grade table.
    """
    def __init__(self, schoolyear, group, term, pids = None):
        """If <pids> is supplied it should be a list of pupil ids: only
        these pupils will be included in the new table.
        """
        super().__init__(schoolyear)
        self._set_group_term(group, term, None)
        self._new_group_table(pids)

###

class GradeTable(_GradeTable):
    def __init__(self, schoolyear, group, term, tag = None, ok_new = False):
        """If <ok_new> is true, a new table may be created, otherwise
        the table must already exist.
        <tag> is for "term"-types with "subselect=TAG" only.
        If the field 'ISSUE_D' is after the "current" date, or not yet
        set, the table should be created as a new one – if there is an
        existing table, its grade data will be imported.
        """
        super().__init__(schoolyear)
        self._set_group_term(group, term, tag)
        # Get file path
        table_path = year_path(schoolyear,
                GradeBase.table_path(group, term, tag))
        try:
            # Read the "internal" table for this group/term(/tag)
            gdata = get_pack(table_path, SCHOOLYEAR = schoolyear,
                    GROUP = group, TERM = term)
        except FileNotFoundError:
            # File doesn't exist
            if not ok_new:
                raise
            self._new_group_table()
            return
        issue_d = gdata.get('ISSUE_D') or NO_DATE
        if issue_d == NO_DATE or issue_d >= Dates.today():
            # The data is not yet "closed".
            self._new_group_table(grade_data = gdata)
            return
        self.issue_d = issue_d
        self.grades_d = gdata.get('GRADES_D') or NO_DATE
        for row in gdata.get('__PUPILS__'):
            pid = row['PID']
            gmap = row['__DATA__']
            self.name[pid] = row['NAME']
            grades = _Grades(group, row.get('STREAM'), term)
            grades.init_grades(self._include_grades(grades, gmap))
            self[pid] = grades
            for comp in self.composites:
                grades.composite_calc(self.sid2subject_data[comp])
            if self.term == 'Abitur':
                grades.abicalc = AbiCalc(self, pid)
#
    def check_group_term(self, gtable):
        """Check that group and term in <gtable> match those of
        the current instance.
        """
#        if gtable.schoolyear != self.schoolyear:
#            raise GradeTableError(_TABLE_YEAR_MISMATCH.format(
#                    fpath = gtable.filepath))
        if gtable.group != self.group:
            raise GradeTableError(_TABLE_CLASS_MISMATCH.format(
                    fpath = gtable.filepath))
        if gtable.term != self.term:
            raise GradeTableError(_TABLE_TERM_MISMATCH.format(
                    fpath = gtable.filepath))
#
    def integrate_partial_data(self, *gtables):
        """Include the data from the given (partial) tables.
         - Only non-empty source table fields will be used for updating.
         - Only allow an entry to be supplied in one source table.
         - Updates to non-empty fields will issue a warning.
        The current grade table is updated but not saved.
        Return the number of overwritten non-empty entries. This can be
        used to decide whether the changes should be saved.
        """
        tfiles = {}     # {pid:sid -> table file} (keep track of sources)
        overwrite = 0
        for gtable in gtables:
            for pid, grades in gtable.items():
                try:
                    pgrades = self[pid]
                except KeyError:
                    REPORT('WARN', _WARN_EXTRA_PUPIL.format(
                            name = gtable.name[pid],
                            tfile = gtable.filepath))
                    continue
                for sid, g in grades.items():
                    if not g:
                        # This should not occur!
                        REPORT('ERROR', _NEW_GRADE_EMPTY.format(
                                sid = sid,
                                name = gtable.name[pid],
                                tfile = gtable.filepath))
                        continue    # don't update
                    g0 = pgrades[sid]
                    key = '%s:%s' % (pid, sid)
                    tfile1 = tfiles.get(key)
                    tfile2 = gtable.filepath
                    tfiles[key] = tfile2
                    if g != g0:
                        if tfile1:
                            REPORT('ERROR', _ERROR_OVERWRITE2.format(
                                    sid = sid,
                                    name = gtable.name[pid],
                                    tfile1 = tfile1,
                                    tfile2 = tfile2))
                            continue    # don't update
                        if g0:
                            overwrite += 1
                            REPORT('WARN', _WARN_OVERWRITE.format(
                                    sid = sid,
                                    name = gtable.name[pid],
                                    tfile = tfile2))
                        pgrades[sid] = g
        # A "recalc" should not be necessary if the grade file is
        # reloaded after saving – which is the expected usage.
        # Otherwise the calculations should probably be redone:
        #for pid in self:
        #    self.recalc(pid)
        return overwrite


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    from core.base import init
    init()
    _schoolyear = '2016'

    if True:
#    if False:
        _filepath = os.path.join(DATA, 'testing', 'Noten', 'NOTEN_A',
                'Noten_13_A')
#        _filepath = os.path.join(DATA, 'testing', 'Noten', 'NOTEN_1_11.G',
#                'Noten_11.G_1-AB')
        _gtable = GradeTableFile(_schoolyear, _filepath)
        print("SUBJECTS:", _gtable.subjects)
        print("GROUP:", _gtable.group)
        print("TERM:", _gtable.term)
        print("YEAR:", _gtable.schoolyear)
        print("ISSUE_D:", _gtable.issue_d)
        print("GRADES_D:", _gtable.grades_d)
        print("NAMES:", _gtable.name)
        print("COMPOSITES:", _gtable.composites)
        print("COMPONENTS:", _gtable.components)
        print("EXTRAS:", _gtable.extras)
        print("CALCS:", _gtable.calcs)
        for _pid, _gdata in _gtable.items():
            print("???", _pid, _gdata.stream, _gdata)

    quit(0)
#TODO...

    if True:
#    if False:
        _group = '12.G'
        _term = '2'
        print("\n\nGRADE TABLE for %s, term %s" % (_group, _term))
        _gtable = GradeTable(_schoolyear, _group, _term, ok_new = True)
        print("SUBJECTS:", _gtable.subjects)
        print("GROUP:", _gtable.group)
        print("TERM:", _gtable.term)
        print("YEAR:", _gtable.schoolyear)
        print("ISSUE_D:", _gtable.issue_d)
        print("GRADES_D:", _gtable.grades_d)
        print("NAMES:", _gtable.name)
        for _pid, _gdata in _gtable.items():
            print("???", _pid, _gdata.stream, _gdata)

    if True:
#    if False:
        _group = '11.G'
        _term = 'S2016-03-01'
        print("\n\nGRADE TABLE for %s, term %s" % (_group, _term))
        _gtable = GradeTable(_schoolyear, _group, _term, ok_new = True)
        print("SUBJECTS:", _gtable.subjects)
        print("GROUP:", _gtable.group)
        print("TERM:", _gtable.term)
        print("YEAR:", _gtable.schoolyear)
        print("ISSUE_D:", _gtable.issue_d)
        print("GRADES_D:", _gtable.grades_d)
        print("NAMES:", _gtable.name)
        for _pid, _gdata in _gtable.items():
            print("???", _pid, _gdata.stream, _gdata)
        print("INTERNAL: -->", _gtable.save())

    quit(0)

    if True:
        # Read all existing test tables into the internal form
#    if False:
        odir = os.path.join(DATA, 'testing', 'tmp')
        os.makedirs(odir, exist_ok = True)
        from glob import glob
        _filepath = os.path.join(DATA, 'testing', 'Noten', 'NOTEN_*', 'Noten_*')
        for f in sorted(glob(_filepath)):
            _gtable = GradeTableFile(_schoolyear, f)
            print("READ", f)
            fname = os.path.basename(f)
            xlsx_bytes = _gtable.make_grade_table()
            tfile = os.path.join(odir, fname.rsplit('.', 1)[0] + '.xlsx')
            with open(tfile, 'wb') as fh:
                fh.write(xlsx_bytes)
                print("OUT:", tfile)
            print("INTERNAL: -->", _gtable.save())
