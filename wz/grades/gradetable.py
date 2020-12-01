# -*- coding: utf-8 -*-
"""
grades/gradetable.py - last updated 2020-11-30

Access grade data, read and build grade tables.

==============================
Copyright 2020 Michael Towers

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

#TODO: Special reports might best have tags S2016-04-32, where the date
# is ISSUE_D. That way they are, like the other "terms", time-based.
# The tables would also be group-based, so a file name might be
# 'Noten_10_S2016-04-32'.

### Grade table "info" items
_SCHOOLYEAR = 'Schuljahr'
_GROUP = 'Klasse/Gruppe'
_TERM = 'Anlass'
_ISSUE_D = 'Ausgabedatum'      # or 'Ausstellungsdatum'?
_GRADES_D = 'Notendatum'

#TODO: comments – where should these be stored?

### Messages
_TABLE_CLASS_MISMATCH = "Falsche Klasse in Notentabelle:\n  {filepath}"
_TABLE_TERM_MISMATCH = "Falscher \"Anlass\" in Notentabelle:\n  {filepath}"
_TABLE_YEAR_MISMATCH = "Falsches Schuljahr in Notentabelle:\n  {filepath}"
_PIDS_NOT_IN_GROUP = "Schüler nicht in Gruppe {group}: {pids}"

_NO_GRADES_ENTRY = "Keine Noten für Schüler {pid} zum {zum}"
_EXCESS_SUBJECTS = "Unerwartete Fachkürzel in der Notenliste: {sids}"
_TEACHER_MISMATCH = "Fach {sid}: Alte Note wurde von {tid0}," \
        " neue Note von {tid}"
_BAD_GRADE = "Ungültige Note im Fach {sid}: {g}"


_TITLE2 = "Tabelle erstellt am {time}"


import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

import datetime
from fractions import Fraction

from core.base import str2list, Dates
from core.pupils import Pupils
from core.courses import Subjects
from tables.spreadsheet import Spreadsheet, TableError, make_db_table
from tables.matrix import KlassMatrix
from local.base_config import DECIMAL_SEP, USE_XLSX, year_path
from local.grade_config import GradeBase, UNCHOSEN, NO_GRADE

class GradeTableError(Exception):
    pass

###

class Grades(GradeBase):
    """A <Grades> instance manages the set of grades in the database for
    a pupil and "term".
    """
    def __init__(self, group, stream, grades):
        super().__init__(group, stream)
        for sid, g in grades.items():
            self[sid] = self.filter_grade(sid, g)
#
    def filter_grade(self, sid, g):
        """Return the possibly filtered grade <g> for the subject <sid>.
        Integer values are stored additionally in the mapping
        <self.i_grade> (only for subjects with numerical grades).
        """
        # There can be normal, empty, non-numeric and badly-formed grades
        if g:
            if g in self.valid_grades:
                # Separate out numeric grades, ignoring '+' and '-'.
                # This can also be used for the Abitur scale, though the
                # stripping is superfluous.
                try:
                    self.i_grade[sid] = int(g.rstrip('+-'))
                except ValueError:
                    pass
            else:
                REPORT("ERROR: " + _BAD_GRADE.format(sid = sid, g = g))
                g = ''
        else:
            g = ''  # ensure that the grade is a <str>
        return g
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
            try:
                gi = self.i_grade[csid]
            except KeyError:
                if self[csid] != UNCHOSEN:
                    non_grade = NO_GRADE
            else:
                ai += weight
                asum += gi * weight
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

class GradeTable(dict):
    """Manage the grade data for a term (etc.) and group.
    <term> need not actually be a "school term", though it may well be.
    It is used rather to specify the "occasion" determining the issue
    of the reports.
    For each possible, valid combination of "term" and group there is
    a grade table (pupil-subject, with some general information).
    The class instance is a mapping: {pid -> <Grades> instance}. The
    stream is available in the <Grades> instance.
    Additional information is available as attributes:
        <group>: school-class/group, as specified in
                <GradeBase.REPORT_GROUPS>
        <term>: a string representing a valid "term" (school-term, etc.)
        <schoolyear>: school-year
        <issue_d>: date of issue
        <grades_d>: date of grade finalization
        <subjects>: {sid -> subject-name}
        <name>: {pid -> (short) name}
        <stream>: {pid -> stream}
    """
    SCHOOLYEAR = _SCHOOLYEAR
    GROUP = _GROUP
    TERM = _TERM
    ISSUE_D = _ISSUE_D
    GRADES_D = _GRADES_D
#
    def __init__(self, schoolyear, filepath = None):
        super().__init__()
        self.schoolyear = schoolyear
        self.group = None
        self.term = None
        self.issue_d = None
        self.grades_d = None
        self.subjects = None
        self.name = None
        if filepath:
            self._read_grade_table(filepath)
#
    def _set_group(self, group):
        self.group = group
        # Get subjects
        subjects = Subjects(self.schoolyear)
        self.sid2subject_data = {} # {sid -> subject_data}
        self.subjects = {}   # mapping just for "real" subjects, sid -> name
        self.composites = [] # list of composite sids
        for gs in subjects.grade_subjects(group):
            self.sid2subject_data[gs.sid] = gs
            if gs.tids:
                self.subjects[gs.sid] = gs.name
            else:
                # composite
                self.composites.append(gs.sid)
#
    def _include_grades(self, gmap):
        grades = {}

#TODO: do I really need self.subjects AND self.sid2subject_data?

#TODO: adding .x subjects in Abi! ... possibly in grade_config (see
# <special_term>).
        if self.term == 'A':
            # Add additional oral exam grades
            sdmap = {}
            smap = {}
            for sid, sdata in self.sid2subject_data.items():
                sdmap[sid] = sdata
                smap[sid] = sdata.name
                if sid.endswith('.e') or sid.endswith('.g'):
                    if gmap.get(sid) == UNCHOSEN:
                        continue
                    new_sdata = sdata._replace(
                            sid = sdata.sid[:-1] + 'x',
# <tids> must have a value, otherwise it will not be passed by the
# composites filter, but is this alright? (rather ['X']?)
                            tids = 'X',
                            composite = None,
                            report_groups = None,
                            name = sdata.name.split('|', 1)[0] + '| nach'
                        )
                    sdmap[new_sdata.sid] = new_sdata
                    smap[new_sdata.sid] = new_sdata.name
            self.sid2subject_data = sdmap
            self.subjects = smap

        for sid in self.subjects:
            grades[sid] = gmap.get(sid) or ''
        for comp in self.composites:
            grades[comp] = gmap.get(comp) or ''
        for f in GradeBase.group_info(self.group,  'Notenfelder_X'):
            grades['X_' + f] = gmap.get(f) or ''
        return grades
#
    def _read_grade_table(self, filepath):
        """Read the header info and pupils' grades from the given table file.
        The "spreadsheet" module is used as backend so .ods, .xlsx and .tsv
        formats are possible. The filename may be passed without extension –
        <Spreadsheet> then looks for a file with a suitable extension.
        <Spreadsheet> also supports in-memory binary streams (io.BytesIO)
        with attribute 'filename' (so that the type-extension can be read).
        The <info> mapping of the table should contain the keys:
            'SCHOOLYEAR', 'GROUP', 'TERM', 'ISSUE_D', 'GRADES_D'
        """
        ss = Spreadsheet(filepath)
        dbt = ss.dbTable()
        info = {row[0]: row[1] for row in dbt.info if row[0]}
        self._set_group(info.get(_GROUP))
        self.term = GradeBase.text2term(info.get(_TERM))
        year = info.get(_SCHOOLYEAR)
        if year != str(self.schoolyear):
            raise GradeTableError(_TABLE_YEAR_MISMATCH.format(
                        filepath = filepath))
        self.issue_d = info.get(_ISSUE_D)
        self.grades_d = info.get(_GRADES_D)
        sid2col = []
        col = 0
        for f in dbt.fieldnames():
            if col > 2:
                if f[0] != '$':
                    # This should be a subject tag
                    sid2col.append((f, col))
            col += 1
        self.name = {}
        for row in dbt:
            pid = row[0]
            if pid and pid != '$':
                gmap = {sid: row[col] for sid, col in sid2col}
                self.name[pid] = row[1]
                # stream = row[2]
                self[pid] = Grades(self.group, row[2],
                        self._include_grades(gmap))
                # No need to calculate composites here.
#
    @staticmethod
    def table_path(group, term):
        """Get file path for the grade table.
        """
        return GradeBase.GRADE_PATH.format(term = term, group = group)
#
    @classmethod
    def group_table(cls, schoolyear, group, term, ok_new = False):
        """If <ok_new> is true, a new table may be created, otherwise
        the table must already exist.
        """
        # Get file path
        # Get file path and write file
        table_path = year_path(schoolyear, cls.table_path(group, term))
        try:
            # Read the "internal" table for this group/term
            _self = cls(schoolyear)
            ss = Spreadsheet(table_path)
            dbt = ss.dbTable()
            info = {row[0]: row[1] for row in dbt.info if row[0]}
            _yr = info.get('SCHOOLYEAR')
            if _yr != str(schoolyear):
                raise Bug(_TABLE_YEAR_MISMATCH.format(filepath = filepath))
            _grp = info.get('GROUP')
            if _grp != group:
                raise Bug(_TABLE_CLASS_MISMATCH.format(filepath = table_path))
            _self._set_group(group)
            _trm = info.get('TERM')
            if _trm != term:
                raise Bug(_TABLE_TERM_MISMATCH.format(filepath = table_path))
            _self.term = term
            _self.issue_d = info.get('ISSUE_D')
            _self.grades_d = info.get('GRADES_D')
            sid2col = []
            col = 0
            for f in dbt.fieldnames():
                if col > 2:
                    if f[0] != '$':
                        # This should be a subject tag
                        sid2col.append((f, col))
                col += 1
            _self.name = {}
            for row in dbt:
                pid = row[0]
                if pid and pid != '$':
                    gmap = {sid: row[col] for sid, col in sid2col}
                    _self.name[pid] = row[1]
                    # stream = row[2]
                    grades = Grades(_self.group, row[2],
                            _self._include_grades(gmap))
                    _self[pid] = grades
                    for comp in _self.composites:
                        grades.composite_calc(_self.sid2subject_data[comp])
#                        print("§§§", pid, comp, grades[comp])
            return _self
        except TableError:
            # File doesn't exist
            if not ok_new:
                raise
            return cls.new_group_table(schoolyear, group, term)
#
    @classmethod
    def new_group_table(cls, schoolyear, group, term, pids = None):
        """Make an empty grade table.
        If <pids> is supplied it should be a list of pupil ids: only
        these pupils will be included in the new table.
        """
        _self = cls(schoolyear)
        _self._set_group(group)
        _self.term = term
        # Initialize the dates (issue at end of term, or end of year)
        calendar = Dates.get_calendar(schoolyear)
        try:
            date = calendar['TERM_%d' % (int(term) + 1)]
        except KeyError:
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
        _self.issue_d = date
        _self.grades_d = '*'
        # Pupil information
        _self.name = {}
        # Pupil data, select pupils
        pupils = Pupils(schoolyear)
        pidset = set(pids) if pids else None
        pid_list = []
        for pdata in pupils.group2pupils(group, date = date):
            pid = pdata['PID']
            if pids:
                try:
                    pidset.remove(pid)
                except KeyError:
                    continue
            _self.name[pid] = pdata.name()
            # Set grades (all empty)
            _self[pid] = Grades(group, pdata['STREAM'],
                    _self._include_grades({}))
            # No need to calculate composites.
            pid_list.append(pid)
        if pidset:
            raise GradeTableError(_PIDS_NOT_IN_GROUP.format(
                    group = group, pids = ', '.join(pidset)))
        return _self
#
    def make_grade_table(self):
        """Build a basic pupil/subject table for grade input.
        The field names will be localized.
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
        dt = datetime.datetime.now()
        table.setTitle2(_TITLE2.format(time = dt.isoformat(
                    sep=' ', timespec='minutes')))

        ### Translate and enter general info
        info = (
            (_SCHOOLYEAR,    str(self.schoolyear)),
            (_GROUP,         self.group),
            (_TERM,          GradeBase.term2text(self.term)),
            (_GRADES_D,      self.grades_d),
            (_ISSUE_D,       self.issue_d)
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
    def save(self):
        """Save the data to the "database".
        """
        info = (
            ('SCHOOLYEAR',    str(self.schoolyear)),
            ('GROUP',         self.group),
            ('TERM',          self.term),
            ('GRADES_D',      self.grades_d),
            ('ISSUE_D',       self.issue_d)
        )
        fields = ['PID', 'PUPIL', 'STREAM']
        for sid in self.subjects:
            fields.append(sid)
        for comp in self.composites:
            fields.append(comp)
        for f in GradeBase.group_info(self.group,  'Notenfelder_X'):
            fields.append(f)
        # Get line data
        dlist = []
        for pid, grades in self.items():
            dmap = {'PID': pid, 'PUPIL': self.name[pid],
                    'STREAM': grades.stream}
            dmap.update(grades)
            dlist.append(dmap)
        # "Title"
        dt = datetime.datetime.now().isoformat(sep=' ', timespec='minutes')
        bstream = make_db_table(dt,         # "title"
                fields, dlist, info = info)
        suffix = '.xlsx' if USE_XLSX else '.tsv'
        # Get file path and write file
        table_path = year_path(self.schoolyear,
                self.table_path(self.group, self.term))
        tpdir = os.path.dirname(table_path)
        os.makedirs(tpdir, exist_ok = True)
        tfile = table_path + suffix
        with open(tfile, 'wb') as fh:
            fh.write(bstream)
        return tfile

###
#TODO: I probably still need something like this:
def update_grades(schoolyear, term, pid, tid = None, grades = None, **fields):
    """Compare the existing GRADES entry with the data passed in:
    <grades> is a mapping {sid -> grade}.
    Update the database entry if there is a (permissible) change.
    The GRADES entry is keyed by <pid> and <term>.
    """
    gdata = Grades.forPupil(schoolyear, term, pid)
    gdata.get_full_grades()
    if grades:
        # Compare the contained grades with those in gdata.full_grades.
        # Check that the teacher is permitted to perform the update.
        for sid, g in gdata.full_grades.items():
            try:
                g1 = grades[sid]
                if g1 not in gdata.valid_grades:
                    raise GradeTableError(_BAD_GRADE.format(
                            sid = sid, g = g1))
            except KeyError:
                continue
            if tid:
                tid0 = gdata.sid2tid(sid)
                if tid0 and tid0 != tid:
                    raise GradeTableError(_TEACHER_MISMATCH.format(
                            sid = sid, tid0 = tid0, tid = tid))
            if g1 != g:
                gdata.full_grades[sid] = g
                gdata.set_tid(sid, tid)
        # Build the new grades entry
        glist = ['%s:%s:%s' % (sid, g, gdata.sid2tid(sid))
                for sid, g in gdata.full_grades.items() if g]
        newgrades = ','.join(glist)
    else:
        # No change to grades
        newgrades = None
#TODO

    if fields:
        # Only the administrator may perform these updates?
        pass

# This is old code:
    gt = GradeTable(os.path.join(fpath, f))
    print ("\n*** READING: %s.%s, class %s, teacher: %s" % (
            gt.schoolyear, gt.term or '-',
            gt.klass, gt.tid or '-'))
    for pid, grades in gt.items():
        print(" ::: %s (%s):" % (gt.name[pid], gt.stream[pid]), grades)
        # <grades> is a mapping: {sid -> grade}
        glist = ['%s:%s:%s' % (sid, g, gt.tid or '-')
                for sid, g in grades.items() if g]

        # The GRADES table has the fields:
        #   (id – Integer, primary key), PID, CLASS, STREAM,
        #   TERM, GRADES, REPORT_TYPE, ISSUE_D, GRADES_D,
        #   QUALI, COMMENT
        valmap = {
            'PID': pid,
            'CLASS': gt.klass,
            'STREAM': gt.stream[pid],
            'TERM': gt.term,
            'GRADES': ','.join(glist)
        }

# At some point the class, stream and pupil subject choices should be checked,
# but maybe not here?

        # Enter into GRADES table
        with dbconn:
            dbconn.updateOrAdd('GRADES', valmap,
                    PID = pid, TERM = gt.term)




#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    from core.base import init
    init('TESTDATA')
    _schoolyear = '2016'

    if True:
#    if False:
        _filepath = os.path.join(DATA, 'testing', 'NOTEN', 'NOTEN_A',
                'Noten_13_A')
        _gtable = GradeTable(_schoolyear, _filepath)
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
        _group = '12.G'
        _term = '2'
        print("\n\nGRADE TABLE for %s, term %s" % (_group, _term))
        _gtable = GradeTable.group_table(_schoolyear, _group, _term,
                ok_new = True)
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
        # Read all existing test tables into the internal form
#    if False:
        odir = os.path.join(DATA, 'testing', 'tmp')
        os.makedirs(odir, exist_ok = True)
        from glob import glob
        _filepath = os.path.join(DATA, 'testing', 'NOTEN', 'NOTEN_*', 'Noten_*')
        for f in sorted(glob(_filepath)):
            _gtable = GradeTable(_schoolyear, f)
            print("READ", f)
            fname = os.path.basename(f)
            xlsx_bytes = _gtable.make_grade_table()
            tfile = os.path.join(odir, fname.rsplit('.', 1)[0] + '.xlsx')
            with open(tfile, 'wb') as fh:
                fh.write(xlsx_bytes)
                print("OUT:", tfile)
            print("INTERNAL: -->", _gtable.save())
