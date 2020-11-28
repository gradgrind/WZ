# -*- coding: utf-8 -*-
"""
grades/gradetable.py - last updated 2020-11-28

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

### Grade table header items
_SCHOOLYEAR = 'Schuljahr'
_GROUP = 'Klasse/Gruppe'
_TERM = 'Anlass'
_ISSUE_D = 'Ausgabedatum'      # or 'Ausstellungsdatum'?
_GRADES_D = 'Notendatum'


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


#TODO:
# Title for grade tables
#_TITLE0 = "Noten"
#_TITLE = "Noten, bis {date}"
_TITLE2 = "Tabelle erstellt am {time}"
#_TTITLE = "Klausurnoten"


import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

import datetime
from fractions import Fraction

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
from core.base import str2list, Dates
from core.pupils import Pupils
from core.courses import Subjects
from tables.spreadsheet import Spreadsheet, TableError, make_db_table
from tables.matrix import KlassMatrix
from local.base_config import DECIMAL_SEP, USE_XLSX, year_path
from local.grade_config import GradeBase, UNCHOSEN, NO_GRADE

"""TODO:
Use "internal" grade tables (tsv) which also include fields for
composite grades, "qualification", report-type (Abitur: date of
last exam ...). In short, all the info needed to print a report card.

Reading a grade table (at least the "external" ones) should check the
validity of the grades.
"""




class GradeTableError(Exception):
    pass

###

#TODO: use subject list as reference for all table reading?
class Grades(GradeBase):
    """A <Grades> instance manages the set of grades in the database for
    a pupil and "term".
    """
    def __init__(self, group, stream, grades):
        super().__init__(group, stream)
        for sid, g in grades.items():
            self[sid] = self.filter_grade(sid, g)
#




    @classmethod
    def forGroupTerm(cls, schoolyear, term, group):
        """Return a list of <Grades> instances for the given group and term.
        This is not intended for 'Single' reports.
        """
        klass, streams = cls.group2klass_streams(group)
        with DB(schoolyear) as dbconn:
            rows = dbconn.select('GRADES', CLASS = klass, TERM = term)
        if streams:
            return [cls(schoolyear, row) for row in rows
                    if row['STREAM'] in streams]
        else:
            return [cls(schoolyear, row) for row in rows]
#
    @staticmethod
    def list_pupil(schoolyear, pid):
        """List all grade entries for the given pupil.
        """
        with DB(schoolyear) as dbconn:
            return list(dbconn.select('GRADES', PID = pid))
#
#TODO: handling of 'S' reports not yet ok!
    @classmethod
    def forPupil(cls, schoolyear, term_or_date, pid):
        """Return <Grades> instance for the given pupil and term. If
        an unscheduled report is sought, <term_or_date> should be the
        date (YYYY-MM-DD) of the report.
        """
        # Determine whether <term_or_date> is a date
        for c, t in cls.categories():
            if c == term_or_date:
                # not a date
                with DB(schoolyear) as dbconn:
                    row = dbconn.select1('GRADES', PID = pid,
                            TERM = term_or_date)
                if not row:
                    raise GradeTableError(_NO_GRADES_ENTRY.format(
                            pid = pid, zum = t))
                break
        else:
            # date
            with DB(schoolyear) as dbconn:
                row = dbconn.select1('GRADES', PID = pid, TERM = 'S',
                        ISSUE_D = term_or_date)
            if not row:
                raise GradeTableError(_NO_GRADES_ENTRY.format(
                        pid = pid, zum = term_or_date))
        return cls(schoolyear, row)
#
    @classmethod
    def newPupil(cls, schoolyear, **fields):
        """Add a new grade entry for the given term and pupil.
        """
#TODO: What about "unscheduled" reports?
        with DB(schoolyear) as dbconn:
            rowid = dbconn.addEntry('GRADES', fields)
            row = dbconn.select1('GRADES', id = rowid)
        return cls(schoolyear, row)
#
    def update(self, **changes):
        """Update the fields of the grade entry.
        """
        with DB(self.schoolyear) as dbconn:
            rowid = self.grade_row['id']
            dbconn.updateOrAdd('GRADES', changes, update_only = True,
                    id = rowid)
            row = dbconn.select1('GRADES', id = rowid)
        # Reinitialize the instance
        self.__init__(self.schoolyear, row)
#
    def get_raw_grades(self):
        """Return the mapping {sid -> grade} for the "real" grades.
        In addition, the call to <self.filter_grade> also enters numerical
        grades (as integers) into the mapping <self.i_grade>:
            {sid -> grade value}.
        Non-numerical grades are not entered into <self.i_grade>.
        """
        if self._grades == None:
            self._grades = {}
            self._sid2tid = {}
            self.empty_grades = []
            for sg in str2list(self.grade_row['GRADES']):
                sid, g, tid = sg.split(':')
                self._grades[sid] = self.filter_grade(sid, g)
                self._sid2tid[sid] = tid
        return self._grades
#
    def sid2tid(self, sid):
        """Return the tag for the teacher who graded the given subject.
        If there is no entry for this subject, return <None>.
        """
        if self._sid2tid == None:
            self.get_raw_grades()   # Ensure cache is loaded
        return self._sid2tid.get(sid)
#
    def set_tid(self, sid, tid):
        """When a grade is updated, the updating teacher (or '-') must
        be set.
        """
        self._sid2tid[sid] = tid or '-'
#
    def get_full_grades(self, sdata_list, with_composites = False):
        """Return the full grade mapping including all subjects in
        <sdata_list>, a list of <SubjectData> instances. If
        <with_composites> is true, also the "composite" subjects will be
        processed and included.
        All subjects relevant for grades in the class are included.
        A <SubjectData> tuple has the following fields:
            sid: the subject tag;
            tids: a list of teacher ids, empty if the subject is a composite;
            composite: if the subject is a component, this will be the
                sid of its composite; if the subject is a composite, this
                will be the list of components, each is a tuple
                (sid, weight); otherwise the field is empty;
            report_groups: a list of tags representing a particular block
                of grades in the report template;
            name: the full name of the subject.
        The result is also saved as <self.full_grades>.
        """
        raw_grades = self.get_raw_grades()
        # Add subjects missing from GRADES field, process composites
        grades = {}
        for sdata in sdata_list:
            sid = sdata.sid
            if sdata.tids:
                g = raw_grades.pop(sid, '')
                grades[sid] = g
            elif with_composites:
                # A composite subject, calculate the component-average,
                # if possible. If there are no numeric grades, choose
                # NO_GRADE, unless all components are UNCHOSEN (in
                # which case also the composite will be UNCHOSEN).
                asum = 0
                ai = 0
                non_grade = UNCHOSEN
                for csid, weight in sdata.composite:
                    try:
                        gi = self.i_grade[csid]
                    except KeyError:
                        if raw_grades.get(csid) != UNCHOSEN:
                            non_grade = NO_GRADE
                    else:
                        ai += weight
                        asum += gi * weight
                if ai:
                    g = Frac(asum, ai).round()
                    grades[sid] = self.grade_format(g)
                    self.i_grade[sid] = int(g)
                else:
                    grades[sid] = non_grade
        if raw_grades:
            REPORT(_EXCESS_SUBJECTS.format(sids = ', '.join(raw_grades)))
        self.full_grades = grades
        return grades
#
    def set_pupil_name(self, name):
        """The pupil name can be set externally. This avoids having this
        module deal with pupil data.
        """
        self._pname = name
#
    def pupil_name(self):
        return self._pname

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


###




def new_table(schoolyear, klass, streams, term, pids):
    ### Pupil data
    pupils = Pupils(schoolyear)

    ### Subject data (for whole class)
    _courses = Subjects(schoolyear)
    sdata_list = _courses.grade_subjects(klass)

    gdata_list = []
#    date = ???
    for pdata in pupils.classPupils(klass, date = date):
        if streams and (pdata['STREAM'] not in self.streams):
            continue
        pname = pupils.pdata2name(pdata)
        gdata = Grades.newPupil(schoolyear, TERM = term,
                CLASS = pdata['CLASS'], STREAM = pdata['STREAM'],
                PID = pdata['PID'], ISSUE_D = '*', GRADES_D = '*',
#group! self!
                REPORT_TYPE = self.default_report_type(term, group))
        # Get all the grades, possibly including composites
        gdata.get_full_grades(self.sdata_list)
        gdata.set_pupil_name(pname)
        gdata_list.append(gdata)


# How to deal with composites?


#???
    # If the "term" refers to a special grade collection, allow the
    # data to be modified
    try:
        int(term)
    except ValueError:
        Grades.special_term(self)

    ### Collect rows
    self.grades_info = self.get_grade_info(schoolyear, term, group)
    self.gdata_list = []
    if (not force_open) and self._grades_closed():
        for gdata in Grades.forGroupTerm(schoolyear, term, group):
            # Get all the grades, possibly including composites.
            gdata.get_full_grades(self.sdata_list, with_composites)
            gdata.set_pupil_name(pupils.pid2name(gdata['PID']))
            self.gdata_list.append(gdata)
    else:
        date = self.grades_info['ISSUE_D']
        for pdata in pupils.classPupils(self.klass, date = date):
            if self.streams and (pdata['STREAM'] not in self.streams):
                continue
            pname = pupils.pdata2name(pdata)
            try:
                gdata = Grades.forPupil(schoolyear, term, pdata['PID'])
            except GradeTableError:
                # No entry in database table
                gdata = Grades.newPupil(schoolyear, TERM = term,
                        CLASS = pdata['CLASS'], STREAM = pdata['STREAM'],
                        PID = pdata['PID'], ISSUE_D = '*', GRADES_D = '*',
                        REPORT_TYPE = self.default_report_type(
                                term, group))
            else:
                # Check for changed pupil stream and class
                changes = {}
                if pdata['CLASS'] != gdata['CLASS']:
                    changes['CLASS'] = pdata['CLASS']
                if pdata['STREAM'] != gdata['STREAM']:
                    changes['STREAM']  = pdata['STREAM']
                if changes:
                    REPORT(_GROUP_CHANGE.format(
                            pname = pname,
                            delta = repr(changes)))
                    gdata.update(**changes)
            # Get all the grades, possibly including composites
            gdata.get_full_grades(self.sdata_list, with_composites)
            gdata.set_pupil_name(pname)
            self.gdata_list.append(gdata)

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
                <GradeBase._REPORT_GROUPS>
        <term>: a string representing a valid "term" (school-term, etc.)
        <schoolyear>: school-year
        <issue_d>: date of issue
        <grades_d>: date of grade finalization
        <subjects>: {sid -> subject-name}
        <name>: {pid -> (short) name}
        <stream>: {pid -> stream}
    """
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
        for sid in self.subjects:
            grades[sid] = gmap.get(sid) or ''
        for comp in self.composites:
            grades[comp] = gmap.get(comp) or ''
        for f in GradeBase.group_term_info(self.group, self.term,
                'GRADE_FIELDS_X'):
            grades[f] = gmap.get(f) or ''
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
        self.term = GradeBase.text2category(info.get(_TERM))
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
#
    @staticmethod
    def table_path(group, term):
        """Get file path for the grade table.
        """
        return GradeBase.grade_path(term) + '/' + \
                GradeBase.GRADE_TABLE.format(term = term, group = group)
#
    @classmethod
    def group_table(cls, schoolyear, group, term, ok_new = False, pids = None):
        """If <ok_new> is true, a new table may be created, otherwise
        the table must already exist.
        If <pids> is supplied it should be a list of pupil ids: only
        these pupils will be included in a new table. This is only
        relevant when creating a new table.
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
            if _term != term:
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
                    _self[pid] = Grades(_self.group, row[2],
                            _self._include_grades(gmap))
            return _self
        except TableError:
            # File doesn't exist
            if not ok_new:
                raise
            return cls.new_group_table(schoolyear, group, term, pids)
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
                    {sid: '' for sid in _self.subjects})
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
        try:
            template = GradeBase.GRADE_TABLE_TEMPLATES[self.group]
        except KeyError:
            template = GradeBase.GRADE_TABLE_TEMPLATES['*']
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
            (_TERM,          GradeBase.category2text(self.term)),
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
            ('TERM',          GradeBase.category2text(self.term)),
            ('GRADES_D',      self.grades_d),
            ('ISSUE_D',       self.issue_d)
        )
        fields = ['PID', 'PUPIL', 'STREAM']
        for sid in self.subjects:
            fields.append(sid)
        for comp in self.composites:
            fields.append(comp)
        for f in GradeBase.group_term_info(self.group, self.term,
                'GRADE_FIELDS_X'):
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
        print(" --->", os.getcwd(), table_path)
        tpdir = os.path.dirname(table_path)
        os.makedirs(tpdir, exist_ok = True)
        with open(table_path + suffix, 'wb') as fh:
            fh.write(bstream)






#? ... old stuff ...

#DEPRECATED
    @staticmethod
    def default_report_type(term, group):
        for grp, rtype in Grades.term2group_rtype_list(term):
            if grp == group:
                return rtype
        raise Bug("No report type for term {term}, group {group}".format(
                term = term, group = group))
#
#DEPRECATED
    @classmethod
    def get_grade_info(cls, schoolyear, term, group):
        """Fetch general information for the term/group.
        If necessary, initialize the entries.
        """
        kb = cls.info_keybase(term, group)
        ginfo = {}
        with DB(schoolyear) as dbconn:
            row = dbconn.select1('INFO', K = kb.format(field = 'ISSUE_D'))
            if row:
                ginfo['ISSUE_D'] = row['V']
                ginfo['GRADES_D'] = dbconn.select1('INFO',
                        K = kb.format(field = 'GRADES_D'))['V']
            else:
                # Initialize the information
                try:
                    date = dbconn.select1('INFO',
                            K = 'CALENDAR_TERM_%d' % (int(term) + 1))['V']
                except:
                    date = dbconn.select1('INFO',
                            K = 'CALENDAR_LAST_DAY')['V']
                else:
                    # Previous day, ensure that it is a weekday
                    td = datetime.timedelta(days = 1)
                    d = datetime.date.fromisoformat(date)
                    while True:
                        d -= td
                        if d.weekday() < 5:
                            date = d.isoformat()
                            break
                kb = cls.info_keybase(term, group)
                ginfo = {'ISSUE_D': date, 'GRADES_D': None}
                for key, value in ginfo.items():
                    dbconn.updateOrAdd('INFO',
                            {'K': kb.format(field = key), 'V': value},
                            K = key)
        return ginfo
#
#DEPRECATED
    @staticmethod
    def info_keybase(term, group):
        """Return the base for the INFO table key.
        """
        return 'GRADES_%s.%s_{field}' % (group, term)

###
###

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
    _schoolyear = 2016

    if True:
#    if False:
        _filepath = os.path.join(DATA, 'testing', 'NOTEN', 'Noten_13_A')
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
        _filepath = os.path.join(DATA, 'testing', 'NOTEN', 'Noten_2', 'Noten_12.G')
        _gtable = GradeTable(_schoolyear, _filepath)
        xlsx_bytes = _gtable.make_grade_table()
        with open(os.path.join(DATA, 'testing', 'tmp',
                'Noten_%s.xlsx' % _group), 'wb') as fh:
            fh.write(xlsx_bytes)

    if True:
        _gtable.save()

    quit(0)

#~~~~~~~~~~~~~~~~OLD STUFF ...
#    if True:
    if False:
        print("NEW ROW:", Grades.newPupil(_schoolyear, TERM = 'S1',
                CLASS = '12', STREAM = 'Gym', PID = '200888'))

        with DB(_schoolyear) as dbconn:
            row = dbconn.select1('GRADES', PID = '200888', TERM = 'S1')
        g = Grades(_schoolyear, row)

        g.update(STREAM = 'RS')
        print("CHANGED TO:", dict(g.grade_row))

        with DB(_schoolyear) as dbconn:
            dbconn.deleteEntry ('GRADES', id = g['id'])

#    if True:
    if False:
        _term = '2'
        _group = '12.R'
        print("\n ****", _group)
        term_grade = TermGrade(_schoolyear, _term, _group)
        for _gdata in term_grade.gdata_list:
            print("\nid:", _gdata['id'])
            print(":::", _gdata['PID'])
            print(_gdata.full_grades)

        _group = '12.G'
        print("\n ****", _group)
        term_grade = TermGrade(_schoolyear, _term, _group, with_composites = True)
        for _gdata in term_grade.gdata_list:
            print("\nid:", _gdata['id'])
            print(":::", _gdata['PID'])
            print(_gdata.full_grades)

        _group = '13'
        print("\n ****", _group)
        term_grade = TermGrade(_schoolyear, 'A', _group, force_open = True)
        for _gdata in term_grade.gdata_list:
            print("\nid:", _gdata['id'])
            print(":::", _gdata['PID'])
            print(_gdata.full_grades)

    if True:
#    if False:
#        print("\nGRADES 10/2:")
#        gt = GradeTable(os.path.join(DATA, 'testing', 'Noten_2', 'Noten_10'))
        print("\nGRADES 11.G/2:")
        gt = GradeTable(os.path.join(DATA, 'testing', 'Noten_2', 'Noten_11.G'))
        print("   TID:", gt.tid)
        print("   CLASS:", gt.klass)
        print("   TERM:", gt.term)
        print("   SCHOOL-YEAR:", gt.schoolyear)
        print("   ISSUE_D:", gt.issue_d)
        print("   GRADES_D:", gt.grades_d)

        print("\nSUBJECTS:", gt.subjects)
        print("\nGRADES:")
        for pid, grades in gt.items():
            print(" ::: %s (%s):" % (gt.name[pid], gt.stream[pid]), grades)

    if True:
        print("\n=============== Make Grade Table 13/1 ===============")
        xlsx_bytes = makeBasicGradeTable(_schoolyear, '1', '13',
                empty = True, force_open = True)
        dpath = os.path.join(DATA, 'testing', 'tmp')
        os.makedirs(dpath, exist_ok = True)
        filepath = os.path.join(dpath, 'Grades-13-1.xlsx')
        with open(filepath, 'wb') as fh:
            fh.write(xlsx_bytes)
        print(" --> %s" % filepath)


    quit(0)

    from core.db import DB
    _year = 2016
    dbconn = DB(_year)

    for folder in 'Noten_1', 'Noten_2':
        fpath = os.path.join(DATA, 'testing', folder)
        for f in os.listdir(fpath):
            if f.rsplit('.', 1)[-1] in ('xlsx', 'ods', 'tsv'):
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
