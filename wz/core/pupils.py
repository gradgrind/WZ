# -*- coding: utf-8 -*-

"""
core/pupils.py - last updated 2020-11-15

Database access for reading pupil data.

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

#TODO: without sqlite? using individual tsv for each class?
# import from big file, adding PSORT, STREAM, etc?

import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

### Messages
_TABLE_MISMATCH = "Schuljahr oder Klasse ungültig in Tabelle:\n  {path}"

_UNKNOWN_PID = "Schüler „{pid}“ ist nicht bekannt"


#from fnmatch import fnmatchcase
#from collections import UserList


from tables.spreadsheet import Spreadsheet, TableError
from tables.dictuple import dictuple
from local.base_config import PupilsBase#, year_path



PupilData = dictuple("PupilData", PupilsBase.FIELDS)

class Pupils(PupilsBase):
    def __init__(self, schoolyear):
        self.schoolyear = schoolyear
        self._klasses = {}  # cache
        self._pid2data = None  # cache
#
    def read_source_table(self, filepath):
        """Read in the file containing the "master" pupil data.
        """
#TODO: Perhaps this should be in the "local" package? This could indirect,
# perhaps with **kargs to accommodate various parameters?

        """The filepath can be passed with or without type-extension.
        If no type-extension is given, the folder will be searched for a
        suitable file.
        Alternatively, <filepath> may be an in-memory binary stream
        (io.BytesIO) with attribute 'filename' (so that the
        type-extension can be read).
        """
        ptable = Spreadsheet(filepath).dbTable()
        # Map local field name to internal field name, ignore case
        rFIELDS = {t.upper(): f for f, t in self.FIELDS.items()}
        rFIELDS[self.CLASS.upper()] = 'CLASS'
        # Get column mapping: {field -> column index}
        colmap = {}
        col = -1
        for t in ptable.fieldnames():
            col += 1
            try:
                f = rFIELDS[t.upper()]
            except:
                continue
            colmap[f] = col
        class_col = colmap['CLASS']
        # Collate rows into classes
        classes = {}
        for row in ptable:
            vals = []
            for f in self.FIELDS:
                try:
                    col = colmap[f]
                except KeyError:
                    vals.append(None)
                else:
# Need to distinguish between empty fields and non-supplied fields!
                    vals.append(row[col] or '')
            pd = PupilData(vals)
            klass = row[class_col]
            try:
                classes[klass].append(pd)
            except:
                classes[klass] = [pd]
        return classes
#
    def compare_new_data(self, newclasses):
        """Compare the new data with the existing data and compile a list
        of changes, grouped according to class. There are three classes:
            - new pupil
            - pupil to remove (not very likely, actually pupils shouldn't
             be removed, only marked in EXIT_D!)
            - field(s) changed.
        """
        pid2data = self._load_all_classes()
        pidset = set(pid2data)      # to register removed pupils
        changes = {}
        for klass, plist in newclasses.items():
            kchanges = []
            changes[klass] = kchanges
            for pdata in plist:
                pid = pdata.get('PID')
                try:
                    old = pid2data[pid]
                except KeyError:
                    # New entry
                    kchanges.append(('NEW', pdata))
                    continue
                pidset.remove(pid)
                # Compare fields: <pdata> fields which are set to <None>
                # will not be included.
                delta = old.compare(pdata)
                if old._class == klass:
                    if delta:
                        kchanges.append(('DELTA', old, delta))
                else:
                    # <delta> is passed in here, though it may be empty
                    kchanges.append(('CLASS', old, delta))
        # Add removed pupils to list
        for pid in pidset:
            pdata = pid2data[pid]
            klass = pdata._class
            try:
                changes[klass].append(('REMOVE', pdata))
            except KeyError:
                changes[klass] = [('REMOVE', pdata)]
        return changes
#
    def __getitem__(self, pid):
        if not self._pid2data:
            # Build the cache
            self._load_all_classes()
        try:
            return self._pid2data[pid]
        except KeyError as e:
            raise TableError(_UNKNOWN_PID.format(pid = pid)) from e
#
    def _load_all_classes(self):
        """Build and return mapping {pid -> pupil-data}.
        """
        self._pid2data = {}
        for k in self.classes():
            plist = self.classPupils(k)
            self._pid2data.update(plist._pidmap)
        return self._pid2data
#
    def pid2name(self, pid):
        """Return the short name of a pupil given the PID.
        """
        pdata = self[pid]
        return self.pdata2name(pdata)
#
    @staticmethod
    def pdata2name(pdata):
        """Return the short name of a pupil given the database row.
        """
        return pdata['FIRSTNAME'] + ' ' + pdata['LASTNAME']
#
    def streams(self, klass):
        """Return a sorted list of stream names for the given class.
        """
        with self.dbconn:
            return sorted(self.dbconn.selectDistinct('PUPIL', 'STREAM',
                    CLASS = klass))
#
    def check_pupil(self, pid):
        """Test whether the given <pid> is used.
        """
        try:
            self[pid]
            return True
        except KeyError:
            return False
#
    def classPupils(self, klass, stream = None, date = None):
        """Read the pupil data for the given school-class (possibly with
        stream).
        Return a list of pupil-data (database rows), the pupils being
        ordered alphabetically.
        These pupil-data items have the class as an additional attribute,
        <_class>.
        If a <date> is supplied, pupils who left the school before that
        date will not be included.
        If <stream> is provided, only pupils in that stream are included,
        otherwise all pupils in the class.
        """
        try:
            ptable = self._klasses[klass]
        except KeyError:
            # Read in table for class
            fpath = self.read_class_path(klass)
            ptable = Spreadsheet(fpath).dbTable()
            info = {r[0]:r[1] for r in ptable.info}
            if info.get(self.SCHOOLYEAR) != str(self.schoolyear) or \
                    info.get(self.CLASS) != klass:
                raise TableError(_TABLE_MISMATCH.format(path = fpath))
            self._klasses[klass] = ptable
            # Set class attribute, add mapping {pid -> pdata}
            pidmap = {}
            ptable._pidmap = pidmap
            for pdata in ptable:
                pdata._class = klass
                pidmap[pdata.get('PID')] = pdata

        if date or stream:
            rows = []
            for row in ptable:
                # Check exit date
                if date:
                    exd = row['EXIT_D']
                    if exd and exd < date:
                        continue
                if stream and row['STREAM'] != stream:
                    continue
                rows.append(row)
            return rows
        return ptable
#
    def new(self, **fields):
        """Add a new pupil with the given data. <fields> is a mapping
        containing all the necessary fields.
        """
        with self.dbconn:
            self.dbconn.addEntry('PUPIL', fields)
#
    def update(self, pid, **changes):
        """Edit the given fields (<changes>: {field -> new value}) for
        the pupil with the given id. Field PID may not be changed!
        """
        with self.dbconn:
            self.dbconn.updateOrAdd('PUPIL', changes, update_only = True,
                    PID = pid)
#
    def remove(self, pid):
        """Remove the pupil with the given id from the database.
        """
        with self.dbconn:
            self.dbconn.deleteEntry('PUPIL', PID = pid)




if __name__ == '__main__':
    from core.base import init
    init('TESTDATA')

    _year = 2016
    pupils = Pupils(_year)

    print("\nCLASSES:", pupils.classes())

    _klass = '12'
    print("\n $$$", _klass)
    for pdata in pupils.classPupils(_klass):
        print("\n :::", pdata)

    _pid = '200502'
    _pdata = pupils[_pid]
    print("\n PUPIL %s (class %s)" % (_pdata.get('PID'), _pdata._class))
    print("  ", _pdata)


    print("\n§§§ UPDATE PUPILS §§§")
    _ptables = pupils.read_source_table(os.path.join(DATA, 'testing',
            'delta_test_pupils_2016'))
    _delta = pupils.compare_new_data(_ptables)
    for k, dlist in _delta.items():
        print("\n --- KLASSE:", k)
        for d in dlist:
            print("  ", d)
#DON'T actually update with these items!

    quit(0)



    pid = '200502'
    pdata = pupils[pid]
    print("\nPID(%s):" % pid, pupils.pdata2name(pdata))
    print("  ...", dict(pdata))
    print("\nPID(%s):" % pid, pupils.pid2name('200506'))

    print("\nCLASSES:", pupils.classes())
    print("\nCLASSES with RS:", pupils.classes('RS'))

    print("\nSTREAMS in class 12:", pupils.streams('12'))

    cp = pupils.classPupils('12', stream = 'RS', date = None)
    print("\nPUPILS in 12.RS:")
    for pdata in cp:
        print(" --", dict(pdata))
    print("\nPUPIL 200888, in 12.RS:", dict(cp.pidmap['200888']))

    try:
        pupils.remove("XXX")
    except:
        pass
    print("\nAdd, update (and remove) a pupil:")
    pupils.new(PID="XXX", FIRSTNAME="Fred", LASTNAME="Jones", CLASS="12",
        PSORT="ZZZ")
    print(" -->", dict(pupils["XXX"]))
    pupils.update("XXX", STREAM="RS", EXIT_D="2016-01-31")
    print("\nUPDATE (showRS):")
    for pdata in pupils.classPupils('12', stream = 'RS', date = None):
        print(" --", dict(pdata))
    print("\n AND ... on 2016-02-01:")
    for pdata in pupils.classPupils('12', stream = 'RS', date = "2016-02-01"):
        print(" --", dict(pdata))
    pupils.remove("XXX")

    print("\nFAIL:")
    pdata1 = pupils['12345']
