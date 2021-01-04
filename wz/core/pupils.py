# -*- coding: utf-8 -*-

"""
core/pupils.py - last updated 2021-01-04

Database access for reading pupil data.

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

import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

### Messages
_TABLE_MISMATCH = "Schuljahr oder Klasse ungültig in Tabelle:\n  {path}"
_BAK_EXISTS = "WARNING: Backup-Archiv für heute existiert schon," \
        " keine neue wird erstellt:\n  {fpath}"
_UNKNOWN_PID = "Schüler „{pid}“ ist nicht bekannt"
_PID_EXISTS = "Ungültiges Schülerkennzeichen, es gehört schon {name} in" \
        " Klasse {klass}"

import datetime, glob, zipfile

from tables.spreadsheet import Spreadsheet, TableError, make_db_table
from local.base_config import PupilsBase, USE_XLSX
from core.base import name_filter, Dates


class _PupilData(dict):
    """The instances of this class represent the data pertaining to a
    single pupil. All entries should be strings.
    The instance is created (<__init__>) from a <DBtable> row, so all
    non-empty fields are strings.
    <field_index> is a list of (field, index) pairs. <index> is less
    than 0 for fields which are not supplied.
    Unsupplied fields are given the value <None>, while supplied but
    empty fields receive the value ''. Thus the two cases can be
    distinguished
    """
    def __init__(self, row, field_index, klass = None):
        """To cater for table rows which don't contain a CLASS field,
        the class can be supplied as an extra argument.
        """
        super().__init__()
        for f, i in field_index:
            if i < 0:
                # Field not supplied
                if klass and f == 'CLASS':
                    self[f] = klass
                else:
                    self[f] = None
            else:
                self[f] = row[i] or ''
#
    def name(self):
        """Return the pupil's "short" name.
        """
        return self['FIRSTNAME'] + ' ' + self['LASTNAME']
#
    def __str__(self):
        """A visual representation of the instance.
        """
        items = ['{k}={v}'.format(k = f, v = v) for f, v in self.items()]
        return '_PupilData:<%s>' % '; '.join(items)
#
    def compare(self, dt2, ignore_null = True):
        """Compare the fields of this instance with those of <dt2>.
        Return a list of pairs detailing the deviating fields:
            [(field, dt2-value), ...]
        If <ignore_null> is true, fields in <dt2> which are set to
        <None> will not be included.
        """
        delta = []
        for k, v in self.items():
            vnew = dt2[k]
            if v == vnew:
                continue
            if ignore_null and vnew == None:
                continue
            if v or vnew:
                # Register the change. If the cell should be emptied,
                # ensure that this is with the empty string, ''
                delta.append((k, vnew or ''))
        return delta
#
    def tweak(self, changes):
        """Update the fields in <changes>: [(field, new value), ...].
        """
        self.update(changes)
#
    def namesort(self):
        """Regenerate name fields, including PSORT for all changed and
        new entries. The names are regenerated to ensure that any
        "tussenvoegsel" (see <name_filter>) are in the LASTNAME field.
        """
        _ndata = name_filter(self['FIRSTNAMES'],
                self['LASTNAME'], self['FIRSTNAME'])
        _changes = ((
            ('FIRSTNAMES', _ndata[0]),
            ('LASTNAME', _ndata[1]),
            ('FIRSTNAME', _ndata[2]),
            ('PSORT', _ndata[3])
        ))
        self.tweak(_changes)
##
def NullPupilData(klass):
    """Return a "dummy" pupil-data instance, which can be used as a
    starting point for adding a new pupil.
    """
    data = {
        'CLASS': klass, 'FIRSTNAME': 'Hansi',
        'LASTNAME': 'von Meierhausen', 'FIRSTNAMES': 'Hans Herbert',
        'SEX': 'm', 'ENTRY_D': Dates.today()
    }
    fmap = []
    fvals = []
    i = 0
    for field in PupilsBase.FIELDS:
        fmap.append((field, i))
        i += 1
        try:
            val = data[field]
        except KeyError:
            val = ''
        fvals.append(val)
    return _PupilData(fvals, fmap, klass)

###

class _PupilList(list):
    """Representation for a list of <_PupilData> instances.
    It also maintains a mapping {pid -> <_PupilData> instance}.
    The resulting list should be regarded as immutable, except for the
    methods provided here.
    """
    def __init__(self):
        super().__init__()
        self._pidmap = {}
#
    def append(self, item):
        super().append(item)
        self._pidmap[item['PID']] = item
#
    def remove(self, item):
        super().remove(item)
        del(self._pidmap[item['PID']])
#
    def pid2pdata(self, pid):
        return self._pidmap[pid]

###

class Pupils(PupilsBase):
    def __init__(self, schoolyear):
        self.schoolyear = schoolyear
        self._klasses = {}      # cache for classes {class -> pupil-data list}
        self.clear_pid_cache()  # cache for pupils {pid -> pupil-data}
#
    def read_source_table(self, filepath):
        """Read in the file containing the "master" pupil data.
        The file-path can be passed with or without type-extension.
        If no type-extension is given, the folder will be searched for a
        suitable file.
        Alternatively, <filepath> may be an in-memory binary stream
        (io.BytesIO) with attribute 'filename' (so that the
        type-extension can be read).
        """
        ptable = Spreadsheet(filepath).dbTable()
        # Get column mapping: {field -> column index}
        # Convert the localized names to uppercase to avoid case problems.
        # Get the columns for the localized field names
        colmap = {}
        col = -1
        for t in ptable.fieldnames():
            col += 1
            colmap[t.upper()] = col
        # ... then for the internal field names,
        # the index is -1 for non-supplied fields:
        field_index = [(f, colmap.get(t.upper(), -1))
                for f, t in self.FIELDS.items()]
        # Collate rows into classes
        classes = {}
        for row in ptable:
            pd = _PupilData(row, field_index)
            # Regenerate name fields to "normalize" them and add sorting field:
            pd.namesort()
            klass = pd.get('CLASS')
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
        # Initialize empty lists for all classes, covering old and new data
        changes = {}
        for k in self._klasses:
            changes[k] = []
        for k in newclasses:
            changes[k] = []
        # Search for changes
        for klass, plist in newclasses.items():
            kchanges = changes[klass]
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
                klass0 = old['CLASS']
                if klass0 == klass:
                    if delta:
                        kchanges.append(('DELTA', old, delta))
                else:
                    # Changed class, add entry for OLD class.
                    # <delta> is passed in here, though it may be empty
                    changes[klass0].append(('CLASS', old, klass, delta))
        # Add removed pupils to list
        for pid in pidset:
            pdata = pid2data[pid]
            changes[pdata['CLASS']].append(('REMOVE', pdata))
        return changes
#
    def update_table(self, changes = None):
        """Apply the changes in the <changes> mapping to the pupil data.
        <changes> must include all classes, including those with no
        changes.
        The entries are basically those generated by <self.compare_new_data>,
        but it would be possible to insert a filtering step in between.
        If <changes> is not supplied, the name fields (in particular
        PSORT) are regenerated.
        """
        newclasses = [] # [(class, pupil list), ...] for the new tables
        if changes == None:
            for k in self.classes():
                _pdlist = self.class_pupils(klass)
                if _pdlist:
                    # Regenerate _all_ name and PSORT fields
                    for pdata in _pdlist:
                        pdata.namesort()
                    _pdlist.sort(key = lambda pdata: pdata.get('PSORT'))
                    newclasses.append((klass, pdlist))
        else:
            # Changes are transformed to pairs of remove and add operations
            cmap = {}       # {class -> list of "change" tuples}
            for klass, dlist in changes.items():
                try:
                    # There might already be an entry for the class, if
                    # a 'NEW' put it there.
                    kchanges = cmap[klass]
                except KeyError:
                    kchanges = []
                    cmap[klass] = kchanges
                for d in dlist:
                    if d[0] == 'CLASS':
                        pdata = d[1]
                        # Remove from old class
                        kchanges.append(('REMOVE', pdata))
                        # The pupil-data can now be modified, the
                        # REMOVE action requires only the PID-field
                        # (which won't be changed).
                        pdata.tweak(d[3])
                        # Add to new class
                        k_new = d[2]
                        try:
                            cmap[k_new].append(('NEW', pdata))
                        except KeyError:
                            cmap[k_new] = [('NEW', pdata)]
                    else:
                        kchanges.append(d)
            # Run through the classes and build updated versions
            for klass, dlist in cmap.items():
                try:
                    _pdlist = self.class_pupils(klass)
                except:
                    # A completely new class
                    _pdlist = _PupilList()
                to_remove = set()
                for d in dlist:
                    pdata = d[1]
                    if d[0] == 'NEW':
                        # Add to pupil list
                        _pdlist.append(pdata)
                    elif d[0] == 'REMOVE':
                        to_remove.add(pdata['PID'])
                    elif d[0] == 'DELTA':
                        # Amend and set sorting field
                        pdata.tweak(d[2])
                    else:
                        raise Bug("Bad delta key: %s" % d[0])
                pdlist = [pd for pd in _pdlist if pd['PID'] not in to_remove]
                # Resort class list
                if pdlist:
                    pdlist.sort(key = lambda pdata: pdata.get('PSORT'))
                    newclasses.append((klass, pdlist))

        # Save old files as zip-archive
        files = glob.glob(self.read_class_path('*'))
        bakdir = self.read_class_path()
        if files:
            bakzip = os.path.join(bakdir,
                    'BAK_%s.zip' % datetime.date.today().isoformat())
            try:
                with zipfile.ZipFile(bakzip, 'x') as zipo:
                   # Add class-table files to the zip
                    for f in files:
                        zipo.write(f, arcname = os.path.basename(f))
            except FileExistsError:
                REPORT('ERROR', _BAK_EXISTS.format(fpath = bakzip))

        # Create new tables, at first in temporary directory
        tmpdir = os.path.join(bakdir, 'tmp')
        os.makedirs(tmpdir)
        tables = []
        for klass, dlist in newclasses:
            info = (
                ('SCHOOLYEAR', self.schoolyear),
                ('CLASS', klass),
                ('changed', Dates.today())
            )
            bstream = make_db_table(self.TITLE, self.FIELDS,
                    dlist, info = info)
            fpath = self.read_class_path(klass)
            suffix = '.xlsx' if USE_XLSX else '.tsv'
            tfpath = os.path.join(tmpdir, os.path.basename(fpath)) + suffix
            with open(tfpath, 'wb') as fh:
                fh.write(bstream)

        # Remove old files, move new ones to proper location
        for f in files:
            os.remove(f)
        for f in os.listdir(tmpdir):
            os.rename(os.path.join(tmpdir, f), os.path.join(bakdir, f))
        os.rmdir(tmpdir)
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
            plist = self.class_pupils(k)
            self._pid2data.update(plist._pidmap)
        return self._pid2data
#
    def clear_pid_cache(self):
        self._pid2data = None
#
    def pid2name(self, pid):
        """Return the short name of a pupil given the PID.
        """
        return self[pid].name()
#
    def class_pupils(self, klass, *streams, date = None):
        """Read the pupil data for the given school-class (possibly with
        stream).
        Return a list of mappings {field -> value} (the table rows), the
        pupils being ordered alphabetically.
        The result also has the attribute <_pidmap>, which maps the pid
        to the pupil data.
        If a <date> is supplied, pupils who left the school before that
        date will not be included.
        If <*streams> are provided, only pupils in one of those streams
        are included, otherwise all pupils in the class.
        """
        try:
            ptable = self._klasses[klass]
        except KeyError:
            # Read in table for class
            fpath = self.read_class_path(klass)
            dbtable = Spreadsheet(fpath).dbTable()
            info = {r[0]:r[1] for r in dbtable.info}
            if info.get('SCHOOLYEAR') != self.schoolyear or \
                    info.get('CLASS') != klass:
                raise TableError(_TABLE_MISMATCH.format(path = fpath))
            ptable = _PupilList()
            self._klasses[klass] = ptable
            # Build access key to table row: [(field, row index), ...]
            field_index = []
            for f in self.FIELDS:
                try:
                    i = dbtable.header[f]
                except KeyError:
                    # Normally all the fields should be provided,
                    # except CLASS.
                    i = -1
                field_index.append((f, i))
            # Read table rows
            for pline in dbtable:
                pdata = _PupilData(pline, field_index, klass)
                if date:
                    # Check exit date
                    exd = pdata['EXIT_D']
                    if exd and exd < date:
                        continue
                if streams and pdata['STREAM'] not in streams:
                    continue
                ptable.append(pdata)
        return ptable
#
    def modify_pupil(self, pupil_data, changes):
        oldpid = pupil_data['PID']
        oldclass = pupil_data['CLASS']
        try:
            newpid = changes['PID']
        except KeyError:
            newpid = oldpid
        else:
            # Check that the PID doesn't exist already
            try:
                pdata = self[newpid]
            except TableError:
                pass
            else:
                raise TableError(_PID_EXISTS.format(
                        klass = pdata['CLASS'], name = pdata.name()))
        # Check PID validity
        self.check_new_pid_valid(newpid)
        newclass = changes.get('CLASS', oldclass)
        # Modify all changed fields in <pupil_data>
        if changes:
            pupil_data.tweak([(k, v) for k, v in changes.items()])
            pupil_data.namesort()
        if newclass:
            npdlist = self.class_pupils(newclass)
            if oldclass != newclass or not oldpid:
                # Add pupil to <newclass>
                npdlist.append(pupil_data)
                npdlist.sort(key = lambda pdata: pdata.get('PSORT'))
            self.save_class(newclass, npdlist)
        if oldclass and oldclass != newclass:
            # Remove pupil from current class
            opdlist = self.class_pupils(oldclass)
            opdlist.remove(pupil_data)
            self.save_class(oldclass, opdlist)
        # Invalidate global pid-mapping
        self.clear_pid_cache()
#
    def save_class(self, klass, pdlist):
        """Save the modified pupil-data list for the given class.
        """
        info = (
            ('SCHOOLYEAR', self.schoolyear),
            ('CLASS', klass),
            ('changed', Dates.today())
        )
        bstream = make_db_table(self.TITLE, self.FIELDS,
                pdlist, info = info)
        fpath = self.read_class_path(klass)
        suffix = '.xlsx' if USE_XLSX else '.tsv'
        with open(fpath + suffix, 'wb') as fh:
            fh.write(bstream)


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    from core.base import init
#************** Start new year from raw data **************#
#    from local.base_config import year_path
#    init('DATA')
#    _year = '2021'
#    pupils = Pupils(_year)
#    _ptables = pupils.read_source_table(year_path(_year,
#            'Quelldaten/new_pupils.xlsx'))
#    _delta = pupils.compare_new_data(_ptables)
#    for k, dlist in _delta.items():
#        print("\n --- KLASSE:", k)
#        for d in dlist:
#            print("  ", d)
#    pupils.update_table(_delta)
#    quit(0)
#----------------------------------------------------------#
    init('TESTDATA')

    _year = '2016'
    pupils = Pupils(_year)

    print("\nCLASSES:", pupils.classes())

    _klass = '12'
    print("\n $$$", _klass)
    for pdata in pupils.class_pupils(_klass):
        print("\n :::", pdata)

    _pid = '200502'
    _pdata = pupils[_pid]
    print("\n PUPIL %s (class %s)" % (_pdata['PID'], _pdata['CLASS']))
    print("  ", _pdata)

    # Re-sort tables
#    pupils.update_table()
#    quit(0)

    print("\n§§§ CHECK PUPILS UPDATE §§§")
    _ptables = pupils.read_source_table(os.path.join(DATA, 'testing',
            'delta_test_pupils_2016'))  # modified table
#            'PUPILS_2016.tsv')) # original table
    _delta = pupils.compare_new_data(_ptables)
    for k, dlist in _delta.items():
        print("\n --- KLASSE:", k)
        for d in dlist:
            print("  ", d)

    pupils.update_table(_delta)

    quit(0)
#TODO: reinstate some of the tests below?
    pid = '200502'
    pdata = pupils[pid]
    print("\nPID(%s):" % pid, pupils.pdata2name(pdata))
    print("  ...", dict(pdata))
    print("\nPID(%s):" % pid, pupils.pid2name('200506'))

    print("\nCLASSES:", pupils.classes())
    print("\nCLASSES with RS:", pupils.classes('RS'))

    print("\nSTREAMS in class 12:", pupils.streams('12'))

    cp = pupils.class_pupils('12', 'RS', date = None)
    print("\nPUPILS in 12.RS:")
    for pdata in cp:
        print(" --", dict(pdata))
    print("\nPUPIL 200888, in 12.RS:", dict(cp._pidmap['200888']))

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
    for pdata in pupils.class_pupils('12', 'RS', date = None):
        print(" --", dict(pdata))
    print("\n AND ... on 2016-02-01:")
    for pdata in pupils.class_pupils('12', 'RS', date = "2016-02-01"):
        print(" --", dict(pdata))
    pupils.remove("XXX")

    print("\nFAIL:")
    pdata1 = pupils['12345']
