# -*- coding: utf-8 -*-

"""
core/courses.py - last updated 2020-11-28

Handle course data.

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

### Messages
_TABLE_MISMATCH = "Schuljahr oder Klasse ungültig in Tabelle:\n  {path}"
_CLASS_MISSING = "Info-Feld {cl} fehlt in Fachliste:\n  {fpath}"
_FIELD_MISSING = "Feld „{field}“ fehlt in Fachliste:\n  {fpath}"
_MULTI_COMPOSITE = "Fach mit Kürzel „{sid}“ ist Unterfach für mehrere" \
        " Sammelfächer"
_NO_COMPONENTS = "Sammelfach {sid} hat keine Unterfächer"
_NOT_A_COMPOSITE = "Unterfach {sid}: „{sidc}“ ist kein Sammelfach"
_COMPOSITE_IS_COMPONENT = "Fach-Kürzel „{sid}“ ist sowohl als „Sammelfach“" \
        " als auch als „Unterfach“ definiert"


import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

from collections import namedtuple

from core.base import str2list, Dates
from local.base_config import SubjectsBase, USE_XLSX
from local.grade_config import (NULL_COMPOSITE, NOT_GRADED)
from tables.spreadsheet import Spreadsheet, TableError, make_db_table


class CourseError(Exception):
    pass

SubjectData = namedtuple('SubjectData', SubjectsBase.FIELDS)
GradeSubject = namedtuple('GradeSubject', ('sid', 'tids', 'composite',
        'report_groups', 'name'))

class _SubjectList(list):
    """Representation for a list of <SubjectData> instances.
    It also maintains a mapping {pid -> <SubjectData> instance}.
    The resulting list should be regarded as immutable!
    """
    def __init__(self, klass):
        self.klass = klass
        super().__init__()
        self._sidmap = {}

    def append(self, item):
        super().append(item)
        self._sidmap[item.SID] = item

###

class Subjects(SubjectsBase):
    """Manage the course/subject tables.
    """
    def __init__(self, schoolyear):
        self.schoolyear = schoolyear
        self._klasses = {}  # cache
#
    def class_subjects(self, klass):
        """Read the course data for the given school-class.
        Return a <_SubjectList> instance, a list of <SubjectData> tuples,
        the items being ordered as in the source table.
        The result also has the attribute <_sidmap>, which maps the sid
        to the course data.
        """
        try:
            table = self._klasses[klass]
        except KeyError:
            # Read in table for class
            fpath = self.read_class_path(klass)
            dbtable = Spreadsheet(fpath).dbTable()
            info = {r[0]:r[1] for r in dbtable.info}
            if info.get('SCHOOLYEAR') != self.schoolyear or \
                    info.get('CLASS') != klass:
                raise TableError(_TABLE_MISMATCH.format(path = fpath))
            table = _SubjectList(klass)
            self._klasses[klass] = table
            # Read table rows
            for line in dbtable:
                fdata = [line[dbtable.header[f]] for f in self.FIELDS]
                sdata = SubjectData(*fdata)
                table.append(sdata)
        return table
#
    def read_source_table(self, filepath):
        """Read in the file containing the course data.
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
            klass = info[self.CLASS]
        except KeyError:
            raise TableError(_CLASS_MISSING.format(
                    cl = self.CLASS, fpath = filepath))
        table = _SubjectList(klass)
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
            findex = [colmap[t.upper()] for f, t in self.FIELDS.items()]
        except KeyError:
            raise CourseError(_FIELD_MISSING.format(
                    fpath = filepath, field = t))
        # Read the rows
        for line in dbtable:
            fdata = [line[i] for i in findex]
            sdata = SubjectData(*fdata)
            table.append(sdata)
        return table
#
    def grade_subjects(self, group):
        """Return a list of <GradeSubject> named-tuples for the given group.
        Only subjects relevant for grade reports are included, i.e. those
        with non-empty report_groups (see below). That does not mean
        they will all be included in the report – that depends on the
        slots in the template.
        Each element has the following fields:
            sid: the subject tag;
            tids: a list of teacher ids, empty if the subject is a composite;
            composite: if the subject is a component, this will be the
                sid of its composite; if the subject is a composite, this
                will be the list of components, each is a tuple
                (sid, weight); otherwise the field is empty;
            report_groups: a list of tags representing a particular block
                of grades in the report template;
            name: the full name of the subject.
        "Composite" grades are marked in the database by having no tids.
        Grade "components" are marked by having an entry starting with '*'
        in their FLAGS field. The first element of this field (after
        stripping the '*') is the composite subject tag.
        *** Weighting of components ***
         Add to composite in FLAGS field: *Ku:2  for weight 2.
        Weights should be <int>, to preserve exact rouding.
        """
        composites = {}
        subjects = []
        for sdata in self.group_subjects(group):    # see <SubjectsBase>
            sid = sdata.SID
            _rgroups = sdata.SGROUPS
            if (not _rgroups) or _rgroups == NOT_GRADED:
                # Subject not relevant for grades
                continue
            rgroups = _rgroups.split()
            flags = sdata.FLAGS
            comp = None     # no associated composite
            if flags:
                for f in flags.split():
                    if f[0] == '*':
                        # This subject is a grade "component"
                        if comp:
                            # >1 "composite"
                            raise CourseError(_MULTI_COMPOSITE.format(
                                    sid = sid))
                        # Get the associated composite and the weighting:
                        comp = f[1:]    # remove the '*'
                        try:
                            comp, _weight = comp.split(':')
                        except ValueError:
                            weight = 1
                        else:
                            weight = int(_weight)
                        if comp == NULL_COMPOSITE:
                            continue
                        try:
                            composites[comp].append((sid, weight))
                        except KeyError:
                            composites[comp] = [(sid, weight)]
            tids = sdata.TIDS
            if tids:
                tids = tids.split()
            else:
                # composite subject
                tids = None
                if comp:
                    raise CourseError(_COMPOSITE_IS_COMPONENT.format(
                            sid = sid))
                # The 'composite' field must be modified later
            subjects.append(GradeSubject(sid, tids, comp, rgroups,
                    sdata.SUBJECT))
        ### Add the 'composite' field to composite subjects,
        ### check that the referenced composites are valid,
        ### check that all composites have components.
        result = []
        for sbjdata in subjects:
            if sbjdata.tids:
                # Not a composite
                result.append(sbjdata)
            else:
                # A composite
                try:
                    comp = composites.pop(sbjdata.sid)
                except KeyError:
                    raise CourseError(_NO_COMPONENTS.format(sid = sbjdata.sid))
                result.append(sbjdata._replace(composite = comp))
        for sid, sid_w_list in composites.items():
            # Invalid composite,
            # more than one is not very likely, just report the first one
            raise CourseError(_NOT_A_COMPOSITE.format(
                    sidc = sid, sid = sid_w_list[0][0]))
        return result
#
    def save_table(self, table):
        """Save the given table to the subject folder.
        """
        info = (
            ('SCHOOLYEAR', self.schoolyear),
            ('CLASS', table.klass)
        )
        # <make_db_table> requires a list of <dict>s, not tuples
        dlist = [row._asdict() for row in table]
        bstream = make_db_table(Dates.today(), self.FIELDS,
                dlist, info = info)
        fpath = self.read_class_path(table.klass)
        suffix = '.xlsx' if USE_XLSX else '.tsv'
        tfpath = fpath + suffix
        with open(tfpath, 'wb') as fh:
            fh.write(bstream)
        return tfpath



if __name__ == '__main__':
    _year = '2016'
    from core.base import init
    init('TESTDATA')

    _subjects = Subjects(_year)
    _filepath = os.path.join(DATA, 'testing', 'FACHLISTEN', 'Fachliste-09')
    _srctable = _subjects.read_source_table(_filepath)
    print("\n CLASS", _srctable.klass)
    for row in _srctable:
        print("  ", row._asdict())

    print("\nIMPORT SUBJECT TABLES:")
    sdir = os.path.join(DATA, 'testing', 'FACHLISTEN')
    for f in sorted(os.listdir(sdir)):
        if len(f.split('.')) > 1:
            print("  ... Reading", f)
            table = _subjects.read_source_table(os.path.join(sdir, f))
            print("  -->", _subjects.save_table(table))

    print("\n**** Subject data for class 11: grading ****")
    for sdata in _subjects.grade_subjects('11.G'):
        print("  ++", sdata)
