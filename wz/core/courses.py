# -*- coding: utf-8 -*-

"""
core/courses.py

Last updated:  2022-01-03

Manage course/subject data.

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

### Messages
_FILTER_ERROR = "Fachdaten-Fehler: {msg}"
_SCHOOLYEAR_MISMATCH = "Fachdaten: falsches Jahr in\n{path}"
_CLASS_MISMATCH = "Fachdaten: falsche Klasse in\n{path}"
_MULTIPLE_SID = (
    "Fach-Kürzel {sid} wird in Klasse {klass} in sich"
    " überschneidenden Schülergruppen benutzt: {group1}, {group2}"
)
_MULTIPLE_PID_SID = (
    "Fach-Kürzel {sid} wird für {pname} (Klasse {klass})"
    " mehrfach definiert: Gruppen {groups}"
)
_NAME_MISMATCH = (
    "Fach-Kürzel {sid} hat in der Eingabe einen Namen"
    " ({name2}), der vom voreingestellten Namen ({name1}) abweicht"
)
_UNKNOWN_GROUP = "Klasse {klass}: unbekannte Gruppe – '{group}'"
_INVALID_PUPIL_GROUPS = (
    "Klasse {klass}:{pname} hat ungültige Gruppe(n):" " {groups}"
)

# ?
_YEAR_MISMATCH = "Falsches Schuljahr in Tabelle:\n  {path}"
_INFO_MISSING = "Info-Feld „{field}“ fehlt in Fachtabelle:\n  {fpath}"

### Fields
_TITLE = "Fachdaten"
_TITLE_COURSE_CHOICE = "Fächerwahl"

###############################################################

import sys, os, re
from typing import Dict, List, Tuple, Optional

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

from core.base import Dates, class_group_split
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


class CourseError(Exception):
    pass


WHOLE_CLASS = "*"
NULL = "X"
UNCHOSEN = "/"
#NOT_GRADED = "-"

### -----


def Subjects():
    return __SubjectsCache._instance()


class __SubjectsCache:
    """Manage the course/subject tables.

    This is a "singleton" class, i.e. there should be only one instance,
    which is accessible via the <_instance> method.
    """

    __instance = None

    @classmethod
    def _clear_cache(cls):
        cls.__instance = None

    @classmethod
    def _instance(cls):
        """Fetch the cached instance of this class.
        If the school-year has changed, reinitialize the instance.
        """
        try:
            if cls.__instance.__schoolyear == SCHOOLYEAR:
                return cls.__instance
        except:
            pass
        cls.__instance = cls()
        cls.__instance.__schoolyear = SCHOOLYEAR
        return cls.__instance

    def __init__(self):
        # All subject names: {sid: subject-name, ... }
        self.sid2name: Dict[str, str]
        #        self.class_info: Dict[str,str]
        self.sid2name = MINION(DATAPATH(CONFIG["SUBJECT_DATA"]))
        #        self.class_info = {}

        # Cache for class "info" fields, access via method <class_info>:
        # {class: {key: value, ... }, ...}
        self.__class_info: Dict[str, Dict[str, str]]
        self.__class_info = {}

        # Cache for class course definition lines, access via method
        # <class_subjects>: {class: [{field: value, ... }, ... ], ... }
        self.__classes: Dict[str, List[Dict[str, str]]]
        self.__classes = {}

        # Cache for processed class group info: {class: GroupData()}
        self.__group_info: Dict[str, GroupData]
        self.__group_info = {}

        # Caches for report subject data (whole class), access via methods
        # report_subjects and report_sgmap
        self.__report_subjects: Dict[Tuple[str, bool], List[Tuple[str, str]]]
        self.__report_subjects = {}
        self.__report_sgmap: Dict[Tuple[str, bool], Dict[str, Dict[str, dict]]]
        self.__report_sgmap = {}

        # Fields:
        self.config = MINION(DATAPATH("CONFIG/SUBJECT_DATA"))
        # Each class has a table-file (substitute {klass}):
        self.class_path = DATAPATH(CONFIG["SUBJECT_TABLE"])

    def classes(self) -> List[str]:
        """Return a sorted list of class names."""
        tpl = os.path.basename(self.class_path).format(klass="([^.]+)")
        clist: List[str] = []
        for f in os.listdir(os.path.dirname(self.class_path)):
            rm = re.match(tpl, f)
            if rm:
                clist.append(rm.group(1))
        clist.sort()
        return clist

    def class_subjects(self, klass: str) -> List[Dict[str, str]]:
        if klass not in self.__classes:
            self.__read_class_data(klass)
        return self.__classes[klass]

    def class_info(self, klass: str) -> Dict[str, str]:
        if klass not in self.__class_info:
            self.__read_class_data(klass)
        return self.__class_info[klass]

    def __read_class_data(self, klass):
        """Read the class subject data from the "database" for the
        current year. The results are cached for access by the methods
        <class_info> and <class_subjects>.
        """
        fpath = self.class_path.format(klass=klass)
        # print("READING", fpath)
        class_table = read_DataTable(fpath)
        try:
            class_table = filter_DataTable(class_table, self.config)
        except TableError as e:
            raise CourseError(_FILTER_ERROR.format(msg=f"{e} in\n {fpath}"))
        info = class_table["__INFO__"]
        if info["SCHOOLYEAR"] != SCHOOLYEAR:
            raise CourseError(_SCHOOLYEAR_MISMATCH.format(path=fpath))
        if klass != info["CLASS"]:
            raise CourseError(_CLASS_MISMATCH.format(path=fpath))
        self.__class_info[klass] = info

        # TODO: Really remove subject names?
        # Remove and check the subject names (the subject names are not
        # stored in the internal table).
        table = class_table["__ROWS__"]
        for row in table:
            sname = row.pop("SNAME")
            sid = row["SID"]
            sname0 = self.sid2name.get(sid) or "---"
            if sname != sname0:
                REPORT(
                    "WARNING",
                    _NAME_MISMATCH.format(sid=sid, name1=sname0, name2=sname),
                )
        self.__classes[klass] = table

    def group_info(self, klass):
        """Return the <GroupData> instance for the given class."""
        try:
            return self.__group_info[klass]
        except KeyError:
            pass
        gi = GroupData(klass, self.class_info(klass)["GROUPS"])
        self.__group_info[klass] = gi
        return gi

    def report_subjects(self, klass: str, grades=True) -> List[Tuple[str, str]]:
        """Return a subject list: [(sid, subject-name), ... ]."""
        try:
            return self.__report_subjects[(klass, grades)]
        except KeyError:
            pass
        return self.__report_subject_data(klass, grades)[0]

    def report_sgmap(
        self, klass: str, grades=True
    ) -> Dict[str, Dict[str, dict]]:
        """Return a mapping from subject and group to the subject data:
        {sid: {group: subject-data (dict), ... }, ...}
        """
        try:
            return self.__report_sgmap[(klass, grades)]
        except KeyError:
            pass
        return self.__report_subject_data(klass, grades)[1]

    def __report_subject_data(self, klass: str, grades: bool):
        """Cache report subject data for the given class.
        If <grades> is true, then the data is for grade reports, otherwise
        text reports.
        Only the subjects with an entry in the SGROUP field, i.e.
        those for direct inclusion in reports, are included.
        If <grades> is true, also "composite" subjects will be included,
        but subjects with SGROUP='-' will be excluded.
        """
        table = []
        # Get all subject data
        sclist = self.class_subjects(klass)
        subjects = []
        sgmap = {}
        if sclist:
            # Get processed group data
            group_data = self.group_info(klass)
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
                        subjects.append((sid, self.sid2name[sid]))
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
        self.__report_subjects[(klass, grades)] = subjects
        self.__report_sgmap[(klass, grades)] = sgmap
        return subjects, sgmap

    # TODO: There should perhaps also be a function to check that a pupil
    # is not in mutually exclusive groups.

    # Consider a group G with members also in A and B, then consider a subject
    # with distinct entries for A and B! Without complete group data for the
    # pupils it may be impossible to determine whether a given pupil is in
    # group A or group B. Thus, which course data to choosemay not be clear.
    # This problem should be reported. The user can then decide whether to
    # add a pupil group or adapt the course table. If the report doesn't
    # break off execution, there would be a third choice: use the first
    # matching set of course data (this is certainly not ideal, though).

    def filter_pupil_group(
        self, class_group: str, grades: bool = True, date: Optional[str] = None
    ) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str, dict]]]:
        """Return the subject data for all pupils in the given group.
        The first return value is the ordered subject list:
            [(sid, subject-name), ... ]
        The second return value is the ordered pupil list:
            [(pid, pupil-name, pupil-groups, {sid: subject-data, ... }), ... ]
        """
        klass: str
        group: str
        klass, group = class_group_split(class_group)
        subjects: List[Tuple[str, str]] = self.report_subjects(klass, grades)
        sgmap: Dict[str, Dict[str, dict]] = self.report_sgmap(klass, grades)
        group_data = self.group_info(klass)
        if group:
            pgset: Set[str] = group_data.element_groups[group]
            slist = subjects
            subjects = []
            for sid, sname in slist:
                for sg, sdata in sgmap[sid].items():
                    if sg == "*" or (pgset & group_data.element_groups[sg]):
                        subjects.append((sid, sname))
                        break
        # Get pupil-data list
        plist: List[dict] = Pupils().class_pupils(klass, date=date)
        table: List[Tuple[str, str, str, dict]] = []
        for pdata in plist:
            _pgroups: str = pdata["GROUPS"]
            pgroups: List[str] = _pgroups.split()
            if group and group not in pgroups:
                # The given group must be explicitly set for the pupil
                continue
            pid = pdata["PID"]
            pname = pdata.name()
            # Determine pupil's minimal group, as far as possible
            try:
                pset = frozenset.intersection(
                    *[group_data.element_groups[pg] for pg in pgroups]
                )
            except KeyError:
                raise CourseError(
                    _INVALID_PUPIL_GROUPS.format(
                        klass=klass, pname=pname, groups=_pgroups
                    )
                )

            # TODO: include groups for course / pupil???
            # subject for whole class is certainly valid
            # for pupil is valid ... if also for subject? Is a conflict possible?
            # Surely the pupil must be at least as restrictive ...
            psids = {}
            table.append((pid, pname, _pgroups, psids))
            for sid, gmap in sgmap.items():
                for g, sdata in gmap.items():
                    if g == WHOLE_CLASS or (
                        #                        pgset & group_data.element_groups[g]
                        pset
                        & group_data.element_groups[g]
                    ):
                        if sid in psids:
                            # raise CourseError(
                            REPORT(
                                "WARNING",
                                _MULTIPLE_PID_SID.format(
                                    klass=klass,
                                    pname=pname,
                                    sid=sid,
                                    groups=f"[{psids[sid]['GROUP']}, {g}]",
                                ),
                            )
                        else:
                            psids[sid] = sdata
        return subjects, table


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

########################################################################

# Where to put the file?
def makeChoiceTable(klass: str) -> bytes:
    """Build a basic pupil/subject table for course-choice input using a
        template.

    #TODO: Also possible to include the existing choices?
    """
    ### Get template file
    template_path: str = RESOURCEPATH(CONFIG["COURSE_CHOICE_TEMPLATE"])
    table = KlassMatrix(template_path)
    choice_info: dict = MINION(DATAPATH("CONFIG/COURSE_CHOICE_DATA"))

    ### Set title line
    table.setTitle(
        _TITLE_COURSE_CHOICE.format(
            time=datetime.datetime.now().isoformat(sep=" ", timespec="minutes")
        )
    )

    ### Gather general info
    info_transl: Dict[str, str] = {}
    info_item: dict
    for info_item in choice_info["INFO_FIELDS"]:
        f = info_item["NAME"]
        t = info_item["DISPLAY_NAME"]
        info_transl[f] = t
    info: Dict[str, str] = {
        info_transl["SCHOOLYEAR"]: SCHOOLYEAR,
        info_transl["CLASS"]: klass,
    }
    table.setInfo(info)

    ### Get subjects for text reports ... assuming this covers
    ### all needed subjects!
    subjects = Subjects()
    class_subjects: List[Tuple[str, str]]
    class_pupils: List[Tuple[str, str, dict]]
    class_subjects, class_pupils = subjects.filter_pupil_group(
        klass, grades=False
    )

    ### Go through the template columns and check if they are needed:
    rowix: List[int] = table.header_rowindex  # indexes of header rows
    if len(rowix) != 2:
        raise GradeTableError(_TEMPLATE_HEADER_WRONG.format(path=template_path))
    sidcol: List[Tuple[str, int]] = []
    sid: str
    sname: str
    for sid, sname in class_subjects:
        # Add subject
        col: int = table.nextcol()
        sidcol.append((sid, col))
        table.write(rowix[0], col, sid)
        table.write(rowix[1], col, sname)
    # Enforce minimum number of columns
    while col < 18:
        col = table.nextcol()
        table.write(rowix[0], col, "")
    # Delete excess columns
    table.delEndCols(col + 1)

    ### Add pupils
    for pid, pname, pgroups, sdata in class_pupils:
        row = table.nextrow()
        table.write(row, 0, pid)
        table.write(row, 1, pname)
        table.write(row, 2, pgroups)
        for sid, col in sidcol:
            if sid in sdata:
                # TODO: Get existing value ...
                g = ""
                if g:
                    table.write(row, col, g)
            else:
                table.write(row, col, "X", protect=True)
    # Delete excess rows
    row = table.nextrow()
    table.delEndRows(row)

    ### Save file
    table.protectSheet()
    return table.save_bytes()


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    #    import io
    _subjects = Subjects()
    print("SUBJECTS:", _subjects.sid2name)

    print("\nINITIAL CLASSES:", _subjects.classes())

    _klass = "11G"
    _sgmap = _subjects.report_sgmap(_klass)
    _slist = _subjects.report_subjects(_klass)
    print(f"\n Class {_klass}, subjects:")
    for _sid, _sname in _slist:
        print(f"   +++++ {_sid}: {_sname}")
        for _sg, _sdata in _sgmap[_sid].items():
            print(f"      -- {_sg}: {repr(_sdata)}")

    _gdata = _subjects.group_info(_klass)
    print("\n*** minimal_subgroups:\n", _gdata.minimal_subgroups)
    print("\n*** element_groups:\n", _gdata.element_groups)
    print("\n*** divisions:\n", _gdata.divisions)
    print("\n*** class_groups:\n", _gdata.class_groups)
    print("\n*** groupsets_class:\n", _gdata.groupsets_class)
    print("\n *****************************************\n")

    _table = _subjects.filter_pupil_group("11G.G")
    print(f"\n Class 11G, subjects for group 'G':\n", _table[0])
    print("\n Class 11G, pupils for group 'G':")
    for _pid, _pname, _pgroups, _smap in _table[1]:
        print(f"\n   +++++ {_pname}: {repr(_smap)}")

    print("\n *****************************************")
    _gdata = GroupData("12G", "A.G B.G B.R | P Q")
    print("\n*** minimal_subgroups:\n", _gdata.minimal_subgroups)
    print("\n*** element_groups:\n", _gdata.element_groups)
    print("\n*** divisions:\n", _gdata.divisions)
    print("\n*** class_groups:\n", _gdata.class_groups)
    print("\n*** groupsets_class:\n", _gdata.groupsets_class)

    _tbytes = makeChoiceTable("12G")
    _tpath = DATAPATH("testing/tmp/ChoiceTable.xlsx")
    _tdir = os.path.dirname(_tpath)
    if not os.path.isdir(_tdir):
        os.makedirs(_tdir)
    with open(_tpath, "wb") as _fh:
        _fh.write(_tbytes)
    print(f"\nWROTE SUBJECT CHOICE TABLE TO {_tpath}\n")

    quit(0)
    ########################################################################

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
