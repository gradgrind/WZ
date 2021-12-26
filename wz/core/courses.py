# -*- coding: utf-8 -*-

"""
core/courses.py - last updated 2021-12-25

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

Use a single file to contain all the subject data as a mapping.
It comprises two main areas: class-subjects and pupil-choices.
There is also general information, keyed by '__INFO__':
    __TITLE__: 'Subject Data' (for example, not used in code)
    SCHOOLYEAR: '2016' (year in which the end of the school year falls)
    __MODIFIED__: <date-time> (not used in code)

The class-subjects part has the following structure:
    __SUBJECTS__: {class: [<sdata>, ...], ... }
           <sdata> is a mapping, {field: value}
The pupil-choices part has the following structure:
    __CHOICES__: {pid: [sid, ... ], ... }
Only the sids of non-chosen courses are included. Also, only pupils
who have non-chosen courses are included there.
"""
#TODO: It would probably be good to have a gui-editor for such files, but
# the data could be exported as a table (tsv or xlsx).
# At the moment only the choice tables can be exported (xlsx) for editing.
# This can be edited with a separate tool and the result read in as an
# "update".
# I currently assume that subject input tables will be retained in
# "source" format (xlsx/ods), so that these files can be edited and
# reloaded.

### Messages
_FILTER_ERROR = "Fachdaten-Fehler: {msg}"
_SCHOOLYEAR_MISMATCH = "Fachdaten: falsches Jahr in\n{path}"
_CLASS_MISMATCH = "Fachdaten: falsche Klasse in\n{path}"
_MULTIPLE_SID = "Fach-Kürzel {sid} wird in Klasse {klass} für Gruppe" \
        " {group} mehrfach definiert"

_BAD_LINE = "Ungültige Zeile:\n  {line}\n  ... in {path}"
_UNKNOWN_SID = "Unbekanntes Fach-Kürzel: {sid}"
#_SCHOOLYEAR_MISMATCH = "Fachdaten: falsches Jahr ({year})"
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

import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start
    start.setup(os.path.join(basedir, 'TESTDATA'))

### +++++

import datetime
from glob import glob

from core.base import Dates
from core.pupils import Pupils
from tables.spreadsheet import read_DataTable, filter_DataTable, \
        make_DataTable, make_DataTable_filetypes, \
        TableError, spreadsheet_file_complete
from tables.matrix import KlassMatrix
from tables.datapack import get_pack, save_pack
# year_path !

class CourseError(Exception):
    pass

WHOLE_CLASS = '*'
NULL = 'X'

### -----

#TODO: LOCAL!?
UNCHOSEN = '/'
NOT_GRADED = '-'

#?????
class SubjectsBase:
    TITLE = "Fachliste"
    CHOICE_TITLE = "Fächerwahl"
#
#TODO: to CONFIG?
    # The path to the course data for a school-year:
    COURSE_TABLE = 'Klassen/Kurse'
    # The path to the list of sid: name definitions:
    SUBJECT_NAMES = 'Fachliste'
#TODO: deprecated ...
#
    CHOICE_TEMPLATE = 'Fachwahl'
#
    def read_class_path(self, klass = None, choice = False):
        """Return the path to the table for the class.
        If <klass> is not given, return the directory path.
        If <choice> is true, return the path to the choice table.
        """
        table = self.CHOICE_NAME if choice else self.TABLE_NAME
        if klass != None:
            xpath = table.format(klass = klass)
        else:
            xpath = os.path.dirname(table)
#TODO: year_path ...
        return year_path(self.schoolyear, xpath)
#
    def group_subjects(self, group):
        klass, streams = GradeBase._group2klass_streams(group)
#TODO: filter on group? E.g. -G in FLAGS for "not in group G"?
# Would probably only apply to grade reports? (Because G/R are only
# used there?)
        return self.class_subjects(klass)

### XXXXX

class Subjects:
    """Manage the course/subject tables.
    """
    __subjects = None       # cache for the classes' subject data
    __subject_names = None  # cache for the subject name data

    @classmethod
    def fetch(cls, reset = False):
        """This is the main method for fetching the current data, which
        is then cached in memory.
        """
        if reset:
            cls.__subjects = None
            return None
        if not cls.__subjects:
            cls.__subjects = cls()
        return cls.__subjects
    #+
    @classmethod
    def subject_name(cls, sid = None, reset = False):
        """If reset is true, clear the cache, return <None>.
        Otherwise return the subject name for the given subject-id.
        If the subject-id is not supplied, return the whole subject list
        as a mapping: {subject-id: subject-name}.
        """
        if reset:
            cls.__subject_names = None
            return None
        if not cls.__subject_names:
            cls.__subject_names = MINION(DATAPATH(CONFIG['SUBJECT_DATA']))
        if sid:
            try:
                return cls.__subject_names[sid]
            except KeyError as e:
                raise CourseError(_UNKNOWN_SID.format(sid = sid))
        return cls.__subject_names
#
    def __init__(self):
        self.subject_names = MINION(DATAPATH(CONFIG['SUBJECT_DATA']))
        self.__classes = {}
        # Fields:
        config = MINION(DATAPATH("CONFIG/SUBJECT_DATA"))
        # Each class has a table-file (substitute {klass}):
        self.class_path = DATAPATH(CONFIG["SUBJECT_TABLE"])
        for fpath in glob(self.class_path.format(klass="*")):
            #print("READING", fpath)
            class_table = read_DataTable(fpath)
            try:
                class_table = filter_DataTable(
                    class_table, config
                )
            except TableError as e:
                raise CourseError(_FILTER_ERROR.format(msg=f"{e} in\n {fpath}"))
            info = class_table["__INFO__"]
            if info["SCHOOLYEAR"] != SCHOOLYEAR:
                raise CourseError(_SCHOOLYEAR_MISMATCH.format(path=fpath))
            klass = info["CLASS"]
            if self.class_path.format(klass=klass) != fpath.split('.', 1)[0]:
                raise CourseError(_CLASS_MISMATCH.format(path=fpath))

#? Remove subject names?
            # Remove and check the subject names (the subject names are not
            # stored in the internal table).
            table = class_table["__ROWS__"]
            for row in table:
                sname = row.pop('SNAME')
                sid = row['SID']
                sname0 = self.subject_names.get(sid) or "---"
                if sname != sname0:
                    REPORT('WARN', _NAME_MISMATCH.format(sid = sid,
                            name1 = sname0, name2 = sname))
            self.__classes[klass] = table

    def classes(self):
        """Return a sorted list of class names.
        """
        return sorted(self.__classes)
#
#TODO: May want to provide gui editor ... would then also need an exporter!
#TODO: Do I want to check the class before saving???

#TODO: If using formatted source tables, I won't be able to edit and
# save them within WZ! – except by starting (e.g.) LibreOffice ...
    def save(self):
        """Save the couse data.
        The first save of a day causes the current data to be backed up.
        """
        timestamp = Dates.timestamp()
        today = timestamp.split('_', 1)[0]
        data = {
            '__INFO__': {
                '__TITLE__': _TITLE,
                'SCHOOLYEAR': SCHOOLYEAR,
                '__MODIFIED__': timestamp,
            },
            '__SUBJECTS__': self.__klasses,
            '__CHOICES__': self.__optouts
        }
        save_pack(self.filepath, data, today)
        self.__modified = timestamp
#
#TODO: deprecated? see <class_subjects>
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

    def class_subjects(self, klass, grades=True):
        """Return report-subject data for the given class:
            {   '__SUBJECTS__': [ (sid, subject name), ... ],
                '__PUPILS__': [ (pid, {sid: subject-data, ... }}), ... ]
            }
        The __SUBJECTS__ list includes all subjects relevant
        for the class, but only those which have an entry in the SGROUP
        field, i.e. those for direct inclusion in reports.
        If <grades> is true, also "composite" subjects will be included
        and subjects with SGROUP='-' will be excluded.
        In the pupil data, __PUPILS__, only those subjects are included
        which are relevant for the groups in which the pupil is a member.
        """
        table = []
        # Get pupil-data list
        pupils = Pupils()
        plist = pupils.class_pupils(klass)
        # Get all subject data
        sclist = self.__classes.get(klass)
        sid_name = {}
        subjects = []
        sgmap = {}
        if sclist and plist:
            for sdata in sclist:
                print("?????", sdata)
                sg = sdata['GROUP']
                srs = sdata['SGROUP']
                if sg and srs:
                    sid = sdata['SID']
                    if grades:
                        if sg == "-":
                            continue
                    else:
                        if sid[0] == "$":
                            continue
                    if sid not in sid_name:
                        sname = self.subject_name(sid)
                        sid_name[sid] = sname
                        subjects.append((sid, sname))
                    sgkey = (sid, sg)
                    if sgkey in sgmap:
                        raise CourseError(
                            _MULTIPLE_SID.format(
                                klass=klass,
                                sid=sid,
                                group=sg
                            )
                        )
                    sgmap[sgkey] = sdata
#TODO ...
# Should I check for '*' and group both defined for a sid above?
# Maybe a double mapping would be better? {sid: {group: sdata}}

                    try:
                        gmap = sgmap[sid]
                    except KeyError:
                        sgmap[sid] = {sg: sdata}
                    else:
                        if sg == '*':
                            error
                        elif '*' in gmap:
                            error
                        elif sg in gmap:
                            error


            for pdata in plist:
                pid = pdata['PID']
                pgroups = pdata['GROUPS'].split()
                psids = {}
                table.append((pid, psids))
                for sgkey, sdata in sgmap.items():
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
                                    pname = pdata.name(),
                                    sid = sid,
                                    groups = f'[{g0}, {g}]'))
        return {
           '__SUBJECTS__': subjects,
            '__PUPILS__': table
            }

# -------------------------------------------------------

#TODO
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
#klass???
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
            return set(self.__optouts[pid])
        except KeyError:
            return set()
#
#TODO
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
                self.__optouts[pid] = clist
            else:
                self.__optouts.pop(pid, None)
        self.save()
#
#TODO
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
#TODO
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
#    import io
    _subjects = Subjects()
    print("SUBJECTS:", _subjects.subject_names)

    print("\nINITIAL CLASSES:", _subjects.classes())

    _klass = '12G'
    clsubjs = _subjects.class_subjects(_klass)
    print(f"\n Class {_klass}, subjects:", clsubjs["__SUBJECTS__"])
    print(f"\n Class {_klass}, individual:")
    for pid, sbjs in clsubjs["__PUPILS__"]:
        print(f"*** PUPIL: {pid} ***")
        for sid, sdata in sbjs.items():
            print(f"  {sdata}")
    quit(0)

    print("\nIMPORT SUBJECT TABLES:")
    sdir = DATAPATH('testing/FACHLISTEN')
    for f in sorted(os.listdir(sdir)):
        if len(f.split('.')) > 1:
            fpath = os.path.join(sdir, f)
            print("  ... Reading", fpath)
            try:
                _subjects.import_source_table(fpath)
            except TableError as e:
                print("ERROR:", str(e))

    print("\nCLASSES:", _subjects.classes())
    quit(0)

#TODO
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
