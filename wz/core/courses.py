# -*- coding: utf-8 -*-

"""
core/courses.py - last updated 2022-01-01

Manage course/subject data.

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

Use "data-tables" to contain the subject data for the classes as a mapping.

CHOICE TABLES?

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
# TODO: It would probably be good to have a gui-editor for such files, but
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
_MULTIPLE_SID = (
    "Fach-Kürzel {sid} wird in Klasse {klass} in sich"
    " überschneidenden Schülergruppen benutzt: {group1}, {group2}"
)
_UNKNOWN_GROUP = "Klasse {klass}: unbekannte Gruppe – '{group}'"

_BAD_LINE = "Ungültige Zeile:\n  {line}\n  ... in {path}"
_UNKNOWN_SID = "Unbekanntes Fach-Kürzel: {sid}"
# _SCHOOLYEAR_MISMATCH = "Fachdaten: falsches Jahr ({year})"
_MULTIPLE_PID_SID = (
    "Fach-Kürzel {sid} wird für {pname} (Klasse {klass})"
    " mehrfach definiert: Gruppen {groups}"
)
_NAME_MISMATCH = (
    "Fach-Kürzel {sid} hat in der Eingabe einen Namen"
    " ({name2}), der vom voreingestellten Namen ({name1}) abweicht"
)

_YEAR_MISMATCH = "Falsches Schuljahr in Tabelle:\n  {path}"
_INFO_MISSING = "Info-Feld „{field}“ fehlt in Fachtabelle:\n  {fpath}"
_FIELD_MISSING = "Feld „{field}“ fehlt in Fachtabelle:\n  {fpath}"
_MULTI_COMPOSITE = (
    "Fach mit Kürzel „{sid}“ ist Unterfach für mehrere" " Sammelfächer"
)
_NO_COMPONENTS = "Sammelfach {sid} hat keine Unterfächer"
_NOT_A_COMPOSITE = "Unterfach {sid}: „{sidc}“ ist kein Sammelfach"
_COMPOSITE_IS_COMPONENT = (
    "Fach-Kürzel „{sid}“ ist sowohl als „Sammelfach“"
    " als auch als „Unterfach“ definiert"
)

### Fields
_TITLE = "Fachdaten"

###############################################################

import sys, os

if __name__ == "__main__":
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    start.setup(os.path.join(basedir, "TESTDATA"))

### +++++

import datetime
from glob import glob

from core.base import Dates
from core.pupils import Pupils
from tables.spreadsheet import (
    read_DataTable,
    filter_DataTable,
    make_DataTable,
    make_DataTable_filetypes,
    TableError,
    spreadsheet_file_complete,
)
from tables.matrix import KlassMatrix
from tables.datapack import get_pack, save_pack

# year_path !


class CourseError(Exception):
    pass


WHOLE_CLASS = "*"
NULL = "X"
UNCHOSEN = "/"
NOT_GRADED = "-"

### -----


class Subjects:
    """Manage the course/subject tables."""

    __subjects = None  # cache for the classes' subject data
    __subject_names = None  # cache for the subject name data

    @classmethod
    def fetch(cls, reset=False):
        """This is the main method for fetching the current data, which
        is then cached in memory.
        """
        if reset:
            cls.__subjects = None
            return None
        if not cls.__subjects:
            cls.__subjects = cls()
        return cls.__subjects

    # +
    @classmethod
    def subject_name(cls, sid=None, reset=False):
        """If reset is true, clear the cache, return <None>.
        Otherwise return the subject name for the given subject-id.
        If the subject-id is not supplied, return the whole subject list
        as a mapping: {subject-id: subject-name}.
        """
        if reset:
            cls.__subject_names = None
            return None
        if not cls.__subject_names:
            cls.__subject_names = MINION(DATAPATH(CONFIG["SUBJECT_DATA"]))
        if sid:
            try:
                return cls.__subject_names[sid]
            except KeyError as e:
                raise CourseError(_UNKNOWN_SID.format(sid=sid))
        return cls.__subject_names

    #
    def __init__(self):
        self.subject_names = MINION(DATAPATH(CONFIG["SUBJECT_DATA"]))
        self.__classes = {}
        self.class_info = {}
        # Fields:
        config = MINION(DATAPATH("CONFIG/SUBJECT_DATA"))
        # Each class has a table-file (substitute {klass}):
        self.class_path = DATAPATH(CONFIG["SUBJECT_TABLE"])
        for fpath in glob(self.class_path.format(klass="*")):
            # print("READING", fpath)
            class_table = read_DataTable(fpath)
            try:
                class_table = filter_DataTable(class_table, config)
            except TableError as e:
                raise CourseError(_FILTER_ERROR.format(msg=f"{e} in\n {fpath}"))
            info = class_table["__INFO__"]
            if info["SCHOOLYEAR"] != SCHOOLYEAR:
                raise CourseError(_SCHOOLYEAR_MISMATCH.format(path=fpath))
            klass = info["CLASS"]
            if self.class_path.format(klass=klass) != fpath.split(".", 1)[0]:
                raise CourseError(_CLASS_MISMATCH.format(path=fpath))
            self.class_info[klass] = info

            # TODO: manage groups ... for intersection testing ...

            # TODO: Really remove subject names?
            # Remove and check the subject names (the subject names are not
            # stored in the internal table).
            table = class_table["__ROWS__"]
            for row in table:
                sname = row.pop("SNAME")
                sid = row["SID"]
                sname0 = self.subject_names.get(sid) or "---"
                if sname != sname0:
                    REPORT(
                        "WARNING",
                        _NAME_MISMATCH.format(
                            sid=sid, name1=sname0, name2=sname
                        ),
                    )
            self.__classes[klass] = table

    def classes(self):
        """Return a sorted list of class names."""
        return sorted(self.__classes)

    #
    # TODO: May want to provide gui editor ... would then also need an exporter!
    # TODO: Do I want to check the class before saving???

    # TODO: If using formatted source tables, I won't be able to edit and
    # save them within WZ! – except by starting (e.g.) LibreOffice ...
    def save(self):
        """Save the couse data.
        The first save of a day causes the current data to be backed up.
        """
        timestamp = Dates.timestamp()
        today = timestamp.split("_", 1)[0]
        data = {
            "__INFO__": {
                "__TITLE__": _TITLE,
                "SCHOOLYEAR": SCHOOLYEAR,
                "__MODIFIED__": timestamp,
            },
            "__SUBJECTS__": self.__klasses,
            "__CHOICES__": self.__optouts,
        }
        save_pack(self.filepath, data, today)
        self.__modified = timestamp

    #
    # TODO: deprecated? see <class_subjects>
    def grade_subjects(self, klass, grouptag=None):
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
                g = sdata["GROUP"]
                if g != WHOLE_CLASS:
                    if not grouptag:
                        continue
                    if grouptag != g:
                        continue
                sgroup = sdata["SGROUP"]
                if sgroup and sgroup != "-":
                    sid = sdata["SID"]
                    if sid in table:
                        # Only a single entry per sid is permitted
                        raise CourseError(
                            _MULTIPLE_SID.format(
                                klass=klass, group=grouptag, sid=sid
                            )
                        )
                    table[sid] = sdata
        return table

    def class_subjects(self, klass, grades=True):
        """Return report-subject data for the given class:
            (   [(sid, subject-name), ... ],

                {sid: {group: subject-data (dict), ... }, ...}
            )
        Only the subjects with an entry in the SGROUP field, i.e.
        those for direct inclusion in reports, are included.
        If <grades> is true, also "composite" subjects will be included,
        but subjects with SGROUP='-' will be excluded.
        """
        table = []
        # Get all subject data
        sclist = self.__classes.get(klass)
        subjects = []
        sgmap = {}
        # Process group data
        group_data = GroupData(klass, self.class_info[klass]["GROUPS"])
        if sclist:
            for sdata in sclist:
                sg = sdata["GROUP"]
                srs = sdata["SGROUP"]
                if sg and srs:
                    sid = sdata["SID"]
                    if grades:
                        if srs == "-":
                            continue
                    elif sid[0] == "$":
                        continue
                    try:
                        gmap = sgmap[sid]
                    except KeyError:
                        sgmap[sid] = {sg: sdata}
                        subjects.append((sid, self.subject_name(sid)))
                        continue
                    # Check for overlapping with any existing entry.
                    s0 = group_data.element_groups[sg]
                    for g in gmap:
                        if s0 & group_data.element_groups[g]:
                            raise CourseError(
                                _MULTIPLE_SID.format(
                                    klass=klass, sid=sid, group1=g, group2=sg
                                )
                            )
                    gmap[sg] = sdata
        return subjects, sgmap, group_data

# This was an attempt to list subject data for the pupils
        # Get pupil-data list
        pupils = Pupils()
        plist = pupils.class_pupils(klass)
        for pdata in plist:
            pid = pdata["PID"]
            pgroups = pdata["GROUPS"].split()
            psids = {}
            table.append((pid, psids))
            for sid, gmap in sgmap.items():
                for g, sdata in gmap.items():
                    if g == WHOLE_CLASS or g in pgroups:
                        try:
                            sd0 = psids[sid]
                        except KeyError:
                            # ok!!
                            psids[sid] = sdata
                        else:
                            g0 = sd0["GROUP"]
                            raise CourseError(
                                _MULTIPLE_PID_SID.format(
                                    klass=klass,
                                    pname=pdata.name(),
                                    sid=sid,
                                    groups=f"[{g0}, {g}]",
                                )
                            )
        return {"__SUBJECTS__": subjects, "__PUPILS__": table}

#TODO: There should perhaps also be a function to check that a pupil
# is not in mutually exclusive groups.


def filter_group(group, subjects, sgmap, group_data):
    """Filter the subjects from <Subjects.class_subjects> for the
    given group.
    """
    subjects2 = []
    smap = {}
    s0 = group_data.element_groups[group]
    for sid, sname in subjects:
        for sg, sdata in sgmap[sid].items():
            if sg == '*' or (s0 & group_data.element_groups[sg]):

                if sid in smap:
                    raise CourseError(
#??? ... klass???
                        _MULTIPLE_FILTER_SID.format(
                            klass=klass, sid=sid, group1=g, group2=sg
                        )
                    )

                subjects2.append((sid, sname))
                smap[sid] = sdata
    return subjects2, smap




class GroupData:
    def __init__(self, klass, raw_groups):
        """Parse the GROUPS info-field (passed as <raw_groups>) for the
        given class. This is a '|'-separated list of mutually exclusive
        class divisions.
        A division is a space-separated list of groups. These groups
        may contain '.' characters, in which case they are intersections
        of "atomic" groups (no dot). Neither these atomic groups nor the
        dotted intersections may appear in more than one division.
        A division might be "A.G B.G B.R".
        The following attributes are set:
            klass: The class, same as the parameter <klass>.
            divisions: List of lists of division entries (the first entry
                    is always ['*'] for the whole class).
            minimal_subgroups: An alphabetical list of the non-intersecting
                    subgroups.
            element_groups: Map the atomic groups (no dot) to the
                    corresponding set of minimal subgroups (note that
                    '*' is not included here as an atomic group – nor is
                    any other representation of the whole class).
            class_groups: As element_groups, but the minimal subgroups
                    have the class as prefix (followed by '.').
            groupsets_class: Basically the reverse of class_groups, mapping
                    sets of minimal subgroups to an atomic group, but here
                    the atomic groups have the class as prefix (followed
                    by '.'). In addition, the set of all minimal subgroups
                    maps to the class itself and '*' maps to the set of
                    all minimal subgroups – if there is one, otherwise
                    to the class itself.
        """
        if klass.startswith("XX"):
            return
        ### Add declared class divisions (and their groups).
        self.klass = klass
        self.divisions = [["*"]]
        divs = []
        atomic_groups = [frozenset()]
        all_atoms = set()
        for glist in raw_groups.split("|"):
            dgroups = glist.split()
            self.divisions.append(dgroups)
            division = [frozenset(item.split(".")) for item in dgroups]
            divs.append(division)
            ag2 = []
            for item in atomic_groups:
                for item2 in division:
                    all_atoms |= item2
                    ag2.append(item | item2)
            atomic_groups = ag2
        # print("§§§ DIVISIONS:", klass, self.divisions)
        # All (dotted) atomic groups:
        self.minimal_subgroups = [".".join(sorted(ag)) for ag in atomic_groups]
        self.minimal_subgroups.sort()
        # print(f'$$$ "Atomic" groups in class {klass}:', self.minimal_subgroups)
        ### Make a mapping of single, undotted groups to sets of dotted
        ### atomic groups.
        self.element_groups = {
            a: frozenset(
                [".".join(sorted(ag)) for ag in atomic_groups if a in ag]
            )
            for a in all_atoms
        }
        # print(f'$$$ "Element" groups in class {klass}:', self.element_groups)
        #
        #        ### The same for the dotted groups from the divisions (if any)
        #        self.extended_groups = {}
        #        for division in divs:
        #            for item in division:
        #                if item not in self.element_groups:
        #                    self.extended_groups['.'.join(sorted(item))] = \
        #                        frozenset.intersection(
        #                            *[self.element_groups[i] for i in item])
        #        print(f'$$$ "Extended" groups in class {klass}:', self.extended_groups)

        self.class_groups = {}
        #        for _map in self.element_groups, self.extended_groups:
        #            for k, v in _map.items():
        #                self.class_groups[k] = frozenset([f'{self.klass}.{ag}'
        #                        for ag in v])
        for k, v in self.element_groups.items():
            self.class_groups[k] = frozenset([f"{self.klass}.{ag}" for ag in v])
            # print(")))", self.class_groups[k])
        # And now a reverse map, avoiding duplicate values (use the
        # first occurrence, which is likely to be simpler)
        self.groupsets_class = {}
        for k, v in self.class_groups.items():
            if v not in self.groupsets_class:
                self.groupsets_class[v] = f"{self.klass}.{k}"
        # TODO: It is not clear where the whole-class entries should occur, and in
        # which form.
        fs_whole = frozenset([self.klass])
        self.groupsets_class[fs_whole] = self.klass
        # Add "whole class" minimal subgroups to the reverse mapping
        all_groups = frozenset(
            [f"{self.klass}.{msg}" for msg in self.minimal_subgroups]
        )
        if all_groups:
            self.groupsets_class["*"] = all_groups
            self.groupsets_class[all_groups] = self.klass
        else:
            self.groupsets_class["*"] = fs_whole

    #        print("+++", klass, self.class_groups)
    #        print("---", klass, self.groupsets_class)

    def group_classgroups(self, group):
        """Return the (frozen)set of "full" groups for the given group.
        The group may be dotted. Initially only the "elemental"
        groups, including the full class, are available, but dotted
        groups will be added if they are not already present.
        This method may need to be overridden in the back-end (see
        <make_class_groups>)
        """
        try:
            return self.class_groups[group]
        except KeyError:
            pass
        gsplit = group.split(".")
        if len(gsplit) > 1:
            group = ".".join(sorted(gsplit))
            try:
                return self.class_groups[group]
            except KeyError:
                pass
            try:
                gset = frozenset.intersection(
                    *[self.class_groups[g] for g in gsplit]
                )
            except KeyError:
                pass
            else:
                if gset:
                    # Add to group mapping
                    self.class_groups[group] = gset
                    # and to reverse mapping
                    grev = self.groupsets_class
                    if gset not in grev:
                        # ... if there isn't already an entry
                        grev[gset] = f"{self.klass}.{group}"
                    return gset
        raise CourseError(_UNKNOWN_GROUP.format(klass=self.klass, group=group))

    #

    # TODO: Do I need this?
    # What is here a "group"? Can it be dotted?
    #    @staticmethod
    #    def split_class_group(group):
    #        """Given a "full" group (with class), return class and group
    #        separately.
    #        This method may need to be overridden in the back-end (see
    #        <make_class_groups>)
    #        """
    #        k_g = group.split(".", 1)
    #        return k_g if len(k_g) == 2 else (group, "")

    # -------------------------------------------------------

    # TODO
    def migrate(self):
        self.schoolyear = str(int(self.schoolyear) + 1)
        self.filepath = year_path(self.schoolyear, self.COURSE_TABLE)
        self.save()

    #
    # TODO: It is not clear that this method is actually needed!
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
            # klass???
            pid_sidmap, sid_name = self.class_subjects(klass)
            # Note that this includes "composite" subjects
            pupils = PUPILS(SCHOOLYEAR)
            for pid, sid_sdata in pid_sidmap.items():
                pdata = pupils[pid]
                pid = pdata["PID"]
                # Get saved choices
                pchoice = self.optouts(pid)
                clist = {
                    sid: sdata
                    for sid, sdata in sid_sdata.items()
                    if sid not in pchoice
                }
                self._pid_choices[pid] = clist
        return self._pid_choices[pid]

    #
    def optouts(self, pid):
        """Return a set of subjects which the given pupil has opted out of."""
        try:
            return set(self.__optouts[pid])
        except KeyError:
            return set()

    #
    # TODO
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
    # TODO
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
        info = {r[0]: r[1] for r in dbtable.info}
        try:
            _year = info[self.SCHOOLYEAR]
        except KeyError as e:
            raise TableError(
                _INFO_MISSING.format(field=self.SCHOOLYEAR, fpath=filepath)
            ) from e
        if _year != self.schoolyear:
            raise TableError(_YEAR_MISMATCH.format(path=filepath))
        try:
            klass = info[self.CLASS]
        except KeyError as e:
            raise TableError(
                _INFO_MISSING.format(field=self.CLASS, fpath=filepath)
            ) from e
        # Build a sid:column relationship
        sid2col = []
        col = 3
        for f in dbtable.fieldnames()[3:]:
            if f[0] != "$":
                # This should be a subject tag
                sid2col.append((f, col))
            col += 1
        table = []
        for row in dbtable:
            pid = row[0]
            if pid and pid != "$":
                clist = [sid for sid, col in sid2col if row[col]]
                if clist:
                    self._optouts[pid] = clist
                else:
                    self._optouts.pop(pid, None)
        self.save()
        return klass

    #
    # TODO
    def make_choice_table(self, klass):
        """Build a basic pupil/subject table for course choices:

        Non-taken courses will be marked with <UNCHOSEN>.
        The field names will be localized.
        """
        ### Get template file
        template_path = os.path.join(
            RESOURCES, "templates", *self.CHOICE_TEMPLATE.split("/")
        )
        table = KlassMatrix(template_path)
        ### Set title line
        # table.setTitle("???")
        table.setTitle2(Dates.timestamp())
        ### Translate and enter general info
        info = ((self.SCHOOLYEAR, str(self.schoolyear)), (self.CLASS, klass))
        table.setInfo(info)
        ### Go through the template columns and check if they are needed:
        sidcol = []
        col = 0
        rowix = table.row0()  # index of header row
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
            pid = pdata["PID"]
            row = table.nextrow()
            table.write(row, 0, pid)
            table.write(row, 1, pupils.name(pdata))
            table.write(row, 2, pdata["GROUPS"])
            # Get saved choices
            pchoice = self.optouts(pid)
            for sid, col in sidcol:
                if sid in sid_sdata:
                    if sid in pchoice:
                        table.write(row, col, UNCHOSEN)
                else:
                    table.write(row, col, NULL, protect=True)
        # Delete excess rows
        row = table.nextrow()
        table.delEndRows(row)
        ### Save file
        table.protectSheet()
        return table.save()


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    #    import io
    _subjects = Subjects()
    print("SUBJECTS:", _subjects.subject_names)

    print("\nINITIAL CLASSES:", _subjects.classes())

    _klass = "11G"
    # clsubjs = _subjects.class_subjects(_klass, grades=False)
    _slist, _sgmap, _gdata = _subjects.class_subjects(_klass)
    print(f"\n Class {_klass}, subjects:")
    for _sid, _sname in _slist:
        print(f"   +++++ {_sid}: {_sname}")
        for _sg, _sdata in _sgmap[_sid].items():
            print(f"      -- {_sg}: {repr(_sdata)}")

    print("\n*** minimal_subgroups:\n", _gdata.minimal_subgroups)
    print("\n*** element_groups:\n", _gdata.element_groups)
    print("\n*** divisions:\n", _gdata.divisions)
    print("\n*** class_groups:\n", _gdata.class_groups)
    print("\n*** groupsets_class:\n", _gdata.groupsets_class)

    _slist2, _smap = filter_group("R", _slist, _sgmap, _gdata)
    print(f"\n Class {_klass}, subjects for group 'R':")
    for _sid, _sname in _slist2:
        print(f"   +++++ {_sid}: {_sname}\n  {repr(_smap[_sid])}")

    print("\n *****************************************")
    _gdata = GroupData("12G", "A.G B.G B.R | P Q")
    print("\n*** minimal_subgroups:\n", _gdata.minimal_subgroups)
    print("\n*** element_groups:\n", _gdata.element_groups)
    print("\n*** divisions:\n", _gdata.divisions)
    print("\n*** class_groups:\n", _gdata.class_groups)
    print("\n*** groupsets_class:\n", _gdata.groupsets_class)

    quit(0)

    print("\nIMPORT SUBJECT TABLES:")
    sdir = DATAPATH("testing/FACHLISTEN")
    for f in sorted(os.listdir(sdir)):
        if len(f.split(".")) > 1:
            fpath = os.path.join(sdir, f)
            print("  ... Reading", fpath)
            try:
                _subjects.import_source_table(fpath)
            except TableError as e:
                print("ERROR:", str(e))

    print("\nCLASSES:", _subjects.classes())
    quit(0)

    # TODO
    _k, _g = "12", "G"
    print("\n**** Subject data for group %s.%s: grading ****" % (_k, _g))
    for sdata in _subjects.grade_subjects(_k, _g).values():
        print("  ++", sdata)
    _k, _g = "12", "R"
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

    for _class in "11", "12", "13":
        odir = os.path.join(DATA, "testing", "tmp")
        os.makedirs(odir, exist_ok=True)
        xlsx_bytes = _subjects.make_choice_table(_class)
        tfile = os.path.join(odir, "CHOICE_%s.xlsx" % _class)
        with open(tfile, "wb") as fh:
            fh.write(xlsx_bytes)
            print("\nOUT (choice table):", tfile)
    #    quit(0)

    print("\nIMPORT CHOICE TABLES:")
    idir = os.path.join(DATA, "testing", "FACHWAHL")
    for f in sorted(os.listdir(idir)):
        print("  ...", f)
        _subjects.import_choice_table(os.path.join(idir, f))

    for pid, optouts in _subjects._optouts.items():
        print(" --> %s:" % pid, ", ".join(optouts))

    _class = "13"
    odir = os.path.join(DATA, "testing", "tmp")
    os.makedirs(odir, exist_ok=True)
    xlsx_bytes = _subjects.make_choice_table(_class)
    tfile = os.path.join(odir, "CHOICE2_%s.xlsx" % _class)
    with open(tfile, "wb") as fh:
        fh.write(xlsx_bytes)
        print("\nOUT (choice table):", tfile)
