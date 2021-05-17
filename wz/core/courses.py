# -*- coding: utf-8 -*-

"""
core/courses.py - last updated 2021-05-17

Manage course/subject data.

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

# Use a single json file to contain all the subject data.
# It comprises two main areas: class-subjects and pupil-choices.
# There is general information:
#   SCHOOLYEAR: schoolyear
#   TITLE: "Fachdaten"
#   __MODIFIED__: <date-time>
# The class-subjects part has the following structure:
#   __SUBJECTS__: {class: [<sdata>, ...], ... }
#           <sdata> is a mapping, field -> value
# The pupil-choices part has the following structure:
#   __CHOICES__: {pid: [sid, ... ], ... }
# Only the sids of non-chosen courses are included. Also, only pupils
# who have non-chosen courses are included.
#
# It would probably be good to have a gui-editor for such files, but
# the data could be exported as a table (tsv or xlsx).
# At the moment only the choice tables can be exported (xlsx) for editing.
# This can be edited with a separate tool and the result read in as an
# "update".
# I currently assume that subject input tables will be retained in
# "source" format (xlsx/ods), so that these files can be edited and
# reloaded.

### Messages
_BAD_LINE = "Ungültige Zeile:\n  {line}\n  ... in {path}"
_UNKNOWN_SID = "Unbekanntes Fach-Kürzel: {sid}"
_SCHOOLYEAR_MISMATCH = "Fachdaten: falsches Jahr in:\n  {filepath}"
_MULTIPLE_SID = "Fach-Kürzel {sid} wird in Klasse {klass} für Gruppe" \
        " {group} mehrfach definiert"
_MULTIPLE_PID_SID = "Fach-Kürzel {sid} wird für {pname} (Klasse {klass})" \
        " mehrfach definiert: Gruppen {groups}"
_NAME_MISMATCH = "Fach-Kürzel {sid} hat in der Eingabe einen Namen" \
        " ({name2}), der vom voreingestellten Namen ({name1}) abweicht"

_YEAR_MISMATCH = "Falsches Schuljahr in Tabelle:\n  {path}"
_INFO_MISSING = "Info-Feld „{field}“ fehlt in Fachtabelle:\n  {fpath}"
_FIELD_MISSING = "Feld „{field}“ fehlt in Fachtabelle:\n  {fpath}"
_MULTI_COMPOSITE = "Fach mit Kürzel „{sid}“ ist Unterfach für mehrere" \
        " Sammelfächer"
_NO_COMPONENTS = "Sammelfach {sid} hat keine Unterfächer"
_NOT_A_COMPOSITE = "Unterfach {sid}: „{sidc}“ ist kein Sammelfach"
_COMPOSITE_IS_COMPONENT = "Fach-Kürzel „{sid}“ ist sowohl als „Sammelfach“" \
        " als auch als „Unterfach“ definiert"

### Fields
_TITLE = "Fachdaten"

###############################################################

import sys, os, datetime
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

from collections import namedtuple

from core.base import Dates
from core.pupils import PUPILS
from local.base_config import SubjectsBase, year_path, klass_group
from local.grade_config import NOT_GRADED, UNCHOSEN
from tables.spreadsheet import Spreadsheet, TableError, make_db_table
from tables.matrix import KlassMatrix
from tables.datapack import get_pack, save_pack

class CourseError(Exception):
    pass

NONE = ''
WHOLE_CLASS = '*'
NULL = 'X'

### +++++

def SUBJECTS(schoolyear):
    return Subjects._set_year(schoolyear)
##
class Subjects(SubjectsBase):
    """Manage the course/subject tables.
    """
    ## Implement a cache for subject/course information.
    _schoolyear = None
    _subjects = None
#
    @classmethod
    def _set_year(cls, year = None):
        """Load subject/course data for the given year.
        Clear data if no year.
        """
        if year != cls._schoolyear:
            cls._subjects = cls(year) if year else None
            cls._schoolyear = year
        return cls._subjects

##

    def __init__(self, schoolyear):
        self.schoolyear = schoolyear
        self.filepath = year_path(self.schoolyear, self.COURSE_TABLE)
        try:
            data = get_pack(self.filepath)
        except FileNotFoundError:
            self._modified = '–––'
            self._optouts = {}
            self._klasses = {}
        else:
            if data['SCHOOLYEAR'] != self.schoolyear:
                raise CourseError(_SCHOOLYEAR_MISMATCH.format(
                        filepath = self.filepath))
            self._modified = data.get('__MODIFIED__')
            self._klasses = data.get('__SUBJECTS__')
            self._optouts = data.get('__CHOICES__')
        self._names = None
#TODO: It is not clear that this method is actually needed!
        self.chosen(None)   # Initialize chosen-subject cache
#
#TODO: Consider whether to integrate the subject names in the json file.
# There could be methods to read and save it ... also a gui editor ...
    def subject_name(self, sid):
        if not self._names:
            fpath = year_path(self.schoolyear, self.SUBJECT_NAMES)
            names = {}
            with open(fpath, 'r', encoding = 'utf-8') as fh:
                for line in fh:
                    l = line.lstrip()
                    if l:
                        if l[0] == '#':
                            continue
                        try:
                            k, v = l.split(':', 1)
                        except ValueError:
                            raise CourseError(_BAD_LINE.format(
                                    path = fpath, line = line))
                        name = v.split('#', 1)[0].strip()
                        names[k.rstrip()] = name
            self._names = names
        try:
            return self._names[sid]
        except KeyError:
            raise CourseError(_UNKNOWN_SID.format(sid = sid))
#
    def classes(self):
        """Return a sorted list of class names.
        """
        return sorted(self._klasses)
#
#TODO: May want to provide gui editor ... would then also need an exporter!
    def import_source_table(self, filepath):
        """Read in a file containing the course data for a class.
        The field names are "localized".
        The file-path can be passed with or without type-extension.
        If no type-extension is given, the folder will be searched for a
        suitable file.
        Alternatively, <filepath> may be an in-memory binary stream
        (io.BytesIO) with attribute 'filename' (so that the
        type-extension can be read).
        """
        dbtable = Spreadsheet(filepath).dbTable()
        info = {r[0]:r[1] for r in dbtable.info}
        try:
            _year = info[self.SCHOOLYEAR]
        except KeyError as e:
            raise TableError(_INFO_MISSING.format(
                    field = self.SCHOOLYEAR, fpath = filepath)) from e
        if _year != self.schoolyear:
            raise TableError(_YEAR_MISMATCH.format(path = filepath))
        try:
            klass = info[self.CLASS]
        except KeyError as e:
            raise TableError(_INFO_MISSING.format(
                    field = self.CLASS, fpath = filepath)) from e
        table = []
        # Get column mapping: {field -> column index}
        # Convert the localized names to uppercase to avoid case problems.
        # Get the columns for the localized field names
        colmap = {}
        col = -1
        for t in dbtable.fieldnames():
            col += 1
            colmap[t.upper()] = col
        # ... then for the internal field names,
        try:
            findex = {f: colmap[t.upper()] for f, t in self.FIELDS.items()}
        except KeyError:
            raise CourseError(_FIELD_MISSING.format(
                    fpath = filepath, field = t))
        # Read the rows
        for line in dbtable:
            fdata = {f: line[i] or NONE for f, i in findex.items()}
            sname = fdata.pop('SUBJECT')
            sid = fdata['SID']
            sname0 = self.subject_name(sid)
            if sname != sname0:
                REPORT('WARN', _NAME_MISMATCH.format(sid = sid,
                        name1 = sname0, name2 = sname))
            table.append(fdata)
        self._klasses[klass] = table
        self.save()
        return klass
#
    def save(self):
        """Save the couse data as a compressed json file.
        The first save of a day causes the current data to be backed up.
        """
        # Back up old table, if it exists
        timestamp = Dates.timestamp()
        today = timestamp.split('_', 1)[0]
        data = {
            'TITLE': _TITLE,
            'SCHOOLYEAR': self.schoolyear,
            '__MODIFIED__': timestamp,
            '__SUBJECTS__': self._klasses,
            '__CHOICES__': self._optouts
        }
        save_pack(self.filepath, data, today)
        self._modified = timestamp
#
    def grade_subjects(self, klass, grouptag = None):
        """Return a mapping {sid -> subject-data} for the given group.
        subject-data is also a mapping ({field -> value}).
        An iterator over the subject-data mappings is available using
        the <values> method of the result mapping. This should retain
        the input order (automatic using the <dict> class).

        Note that the COMPOSITE field can contain multiple, space-
        separated entries. Normally these are just the tag (~sid) of a
        dependent special field, but they may take an optional argument
        after a ':' (no spaces!). This could, for example, be used to
        provide a weighting for averaging, e.g. '$D:2'.
        Weights should be <int>, to preserve exact rounding.
        """
        table = {}
        # Read table rows
        sclist = self._klasses.get(klass)
        if sclist:
            for sdata in sclist:
                # Filter on GROUP and SGROUP fields
                g = sdata['GROUP']
                if g != WHOLE_CLASS:
                    if not grouptag:
                        continue
                    if grouptag != g:
                        continue
                sgroup = sdata['SGROUP']
                if sgroup and sgroup != '-':
                    sid = sdata['SID']
                    if sid in table:
                        # Only a single entry per sid is permitted
                        raise CourseError(_MULTIPLE_SID.format(
                                klass = klass, group = grouptag,
                                sid = sid))
                    table[sid] = sdata
        return table
#
    def class_subjects(self, klass):
        """Return a mapping {pid -> {sid: subject-data}} for the given
        class.
        Only subjects are included which have an entry in the SGROUPS
        field, i.e. those for direct inclusion in reports.
        Note that also "composite" subjects will be included and
        subjects for which no grade is given (but a text report is
        expected).
        Subjects which are not possible for a pupil because of a group
        mismatch are not included.
        A second result is an ordered mapping of all subjects relevant
        for the class: {sid -> subject name}.
        """
        table = {}
        # Get pupil-data list
        pupils = PUPILS(self.schoolyear)
        plist = pupils.class_pupils(klass)
        # Get all subject data
        sclist = self._klasses.get(klass)
        sid_name = {}
        if sclist and plist:
            for sdata in sclist:
                if sdata['GROUP'] and sdata['SGROUP']:
                    sid = sdata['SID']
                    if sid not in sid_name:
                        sid_name[sid] = self.subject_name(sid)
            for pdata in plist:
                pid = pdata['PID']
                pgroups = pdata['GROUPS'].split()
                psids = {}
                table[pid] = psids
                for sdata in sclist:
                    sid = sdata['SID']
                    if sid not in sid_name:
                        continue
                    g = sdata['GROUP']
                    if g == WHOLE_CLASS or g in pgroups:
                        try:
                            sd0 = psids[sid]
                        except KeyError:
                            # ok!!
                            psids[sid] = sdata
                        else:
                            g0 = sd0['GROUP']
                            raise CourseError(_MULTIPLE_PID_SID.format(
                                    klass = klass,
                                    pname = pupils.name(pdata),
                                    sid = sid,
                                    groups = f'[{g0}, {g}]'))
        return table, sid_name

# -------------------------------------------------------

    def migrate(self):
        self.schoolyear = str(int(self.schoolyear) + 1)
        self.filepath = year_path(self.schoolyear, self.COURSE_TABLE)
        self.save()
#
#TODO: It is not clear that this method is actually needed!
    def chosen(self, pid):
        """Return a mapping {sid -> subject-data} for chosen, valid sids
        for the given pupil.
        All subjects are included which are valid for the pupil's groups
        and which are not marked in the choices table.
        The values are cached, and the cache must be initialized by
        calling this method with pid = <None>.
        """
        if not pid:
            # Initialization
            self._pid_choices = None
            return
        if not self._pid_choices:
            self._pid_choices = {}
            pid_sidmap, sid_name = self.class_subjects(klass)
            # Note that this includes "composite" subjects
            pupils = PUPILS(SCHOOLYEAR)
            for pid, sid_sdata in pid_sidmap.items():
                pdata = pupils[pid]
                pid = pdata['PID']
                # Get saved choices
                pchoice = self.optouts(pid)
                clist = {sid: sdata for sid, sdata in sid_sdata.items()
                        if sid not in pchoice}
                self._pid_choices[pid] = clist
        return self._pid_choices[pid]
#
    def optouts(self, pid):
        """Return a set of subjects which the given pupil has opted out of.
        """
        try:
            return set(self._optouts[pid])
        except KeyError:
            return set()
#
    def save_choices(self, klass, data):
        """Save the choices for the given class.
        Note that the parameter <klass> is not used here, as choices
        are saved purely on the basis of their pid.
        Thus <data> must contain an entry for all pupils whose choices
        are to be updated:
            [[pid, [sid, ...]], ... ]
        """
        for pid, clist in data:
            if clist:
                self._optouts[pid] = clist
            else:
                self._optouts.pop(pid, None)
        self.save()
#
    def import_choice_table(self, filepath):
        """Read in the file containing the course choices and save the
        data to the internal representation.
        The field names are "localized".
        The file-path can be passed with or without type-extension.
        If no type-extension is given, the folder will be searched for a
        suitable file.
        Alternatively, <filepath> may be an in-memory binary stream
        (io.BytesIO) with attribute 'filename' (so that the
        type-extension can be read).
        """
        dbtable = Spreadsheet(filepath).dbTable()
        info = {r[0]:r[1] for r in dbtable.info}
        try:
            _year = info[self.SCHOOLYEAR]
        except KeyError as e:
            raise TableError(_INFO_MISSING.format(
                    field = self.SCHOOLYEAR, fpath = filepath)) from e
        if _year != self.schoolyear:
            raise TableError(_YEAR_MISMATCH.format(path = filepath))
        try:
            klass = info[self.CLASS]
        except KeyError as e:
            raise TableError(_INFO_MISSING.format(
                    field = self.CLASS, fpath = filepath)) from e
        # Build a sid:column relationship
        sid2col = []
        col = 3
        for f in dbtable.fieldnames()[3:]:
            if f[0] != '$':
                # This should be a subject tag
                sid2col.append((f, col))
            col += 1
        table = []
        for row in dbtable:
            pid = row[0]
            if pid and pid != '$':
                clist = [sid for sid, col in sid2col if row[col]]
                if clist:
                    self._optouts[pid] = clist
                else:
                    self._optouts.pop(pid, None)
        self.save()
        return klass
#
    def make_choice_table(self, klass):
        """Build a basic pupil/subject table for course choices:

        Non-taken courses will be marked with <UNCHOSEN>.
        The field names will be localized.
        """
        ### Get template file
        template_path = os.path.join(RESOURCES, 'templates',
                    *self.CHOICE_TEMPLATE.split('/'))
        table = KlassMatrix(template_path)
        ### Set title line
        #table.setTitle("???")
        table.setTitle2(Dates.timestamp())
        ### Translate and enter general info
        info = (
            (self.SCHOOLYEAR,    str(self.schoolyear)),
            (self.CLASS,         klass)
        )
        table.setInfo(info)
        ### Go through the template columns and check if they are needed:
        sidcol = []
        col = 0
        rowix = table.row0()    # index of header row
        pid_sidmap, sid_name = self.class_subjects(klass)
        # Note that this includes "composite" subjects
        for sid, sname in sid_name.items():
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
        pupils = PUPILS(self.schoolyear)
        for pid, sid_sdata in pid_sidmap.items():
            pdata = pupils[pid]
            pid = pdata['PID']
            row = table.nextrow()
            table.write(row, 0, pid)
            table.write(row, 1, pupils.name(pdata))
            table.write(row, 2, pdata['GROUPS'])
            # Get saved choices
            pchoice = self.optouts(pid)
            for sid, col in sidcol:
                if sid in sid_sdata:
                    if sid in pchoice:
                        table.write(row, col, UNCHOSEN)
                else:
                    table.write(row, col, NULL, protect = True)
        # Delete excess rows
        row = table.nextrow()
        table.delEndRows(row)
        ### Save file
        table.protectSheet()
        return table.save()


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    _year = '2016'
    from core.base import init
    init()

    _subjects = Subjects(_year)
    print("INITIAL CLASSES:", _subjects.classes())

    print("\nIMPORT SUBJECT TABLES:")
    sdir = os.path.join(DATA, 'testing', 'FACHLISTEN')
    for f in sorted(os.listdir(sdir)):
        if len(f.split('.')) > 1:
            print("  ... Reading", f)
            table = _subjects.import_source_table(os.path.join(sdir, f))

    print("\nCLASSES:", _subjects.classes())

    _k, _g = '12', 'G'
    print("\n**** Subject data for group %s.%s: grading ****" % (_k, _g))
    for sdata in _subjects.grade_subjects(_k, _g).values():
        print("  ++", sdata)
    _k, _g = '12', 'R'
    print("\n**** Subject data for group %s.%s: grading ****" % (_k, _g))
    for sdata in _subjects.grade_subjects(_k, _g).values():
        print("  ++", sdata)

    for k in _subjects._klasses:
        table, subjects = _subjects.class_subjects(k)
        print("\n  --> %s:" % k)
        print("\n SUBJECTS:", subjects)
        print("\n PUPILS:")
        for pid, data in table.items():
            print("\n &&", pid, data)


    for _class in '11', '12', '13':
        odir = os.path.join(DATA, 'testing', 'tmp')
        os.makedirs(odir, exist_ok = True)
        xlsx_bytes = _subjects.make_choice_table(_class)
        tfile = os.path.join(odir, 'CHOICE_%s.xlsx' % _class)
        with open(tfile, 'wb') as fh:
            fh.write(xlsx_bytes)
            print("\nOUT (choice table):", tfile)
#    quit(0)

    print("\nIMPORT CHOICE TABLES:")
    idir = os.path.join(DATA, 'testing', 'FACHWAHL')
    for f in sorted(os.listdir(idir)):
        print("  ...", f)
        _subjects.import_choice_table(os.path.join(idir, f))

    for pid, optouts in _subjects._optouts.items():
        print(" --> %s:" % pid, ', '.join(optouts))

    _class = '13'
    odir = os.path.join(DATA, 'testing', 'tmp')
    os.makedirs(odir, exist_ok = True)
    xlsx_bytes = _subjects.make_choice_table(_class)
    tfile = os.path.join(odir, 'CHOICE2_%s.xlsx' % _class)
    with open(tfile, 'wb') as fh:
        fh.write(xlsx_bytes)
        print("\nOUT (choice table):", tfile)
