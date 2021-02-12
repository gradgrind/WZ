# -*- coding: utf-8 -*-

"""
core/pupils.py - last updated 2021-02-12

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

# Use a single json file to contain all the pupil data, as a list of
# value mappings (one for each pupil).
# When changes are made, date-timed back-ups are made, but only the
# first change of a day is backed up.
# Structure of the json file:
# SCHOOLYEAR: schoolyear
# TITLE: "Schülerliste"
# __PUPILS__: [<pdata>]     # <pdata> is a mapping, field -> value
# __MODIFIED__: <date-time>
# It would probably be good to have a gui-editor for such files, but
# the data can be exported as a table (tsv or xlsx). This can be
# edited with a separate tool and the result read in as an "update".

import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

### Messages
_SCHOOLYEAR_MISMATCH = "Schülerdaten: falsches Jahr in:\n  {filepath}"
_NAME_MISSING = "Eingabezeile fehlerhaft, Name unvollständig:\n  {row}"
#_PID_EXISTS = "Ungültiges Schülerkennzeichen, es gehört schon {name} in" \
#        " Klasse {klass}"
_PID_DUPLICATE = "Schülerkennzeichen {pid} mehrfach vorhanden:\n" \
        "  Klasse {c1} – {p1}\n  Klasse {c2} – {p2}"
_MISSING_FIELDS = "Diese Felder dürfen nicht leer sein:\n  {fields}"

import datetime, shutil, json, gzip

from tables.spreadsheet import Spreadsheet, TableError, make_db_table
from local.base_config import year_path, PupilsBase, USE_XLSX
from core.base import tussenvoegsel_filter, Dates, sortingName

class PupilError(Exception):
    pass

def sortkey(pdata):
    _lastname = pdata['LASTNAME']
    try:
        tv, lastname = _lastname.split('|', 1)
    except ValueError:
        tv, lastname = None, _lastname
    return sortingName(pdata['FIRSTNAME'], tv, lastname)

###

class _PupilList(list):
    """Representation for a list of pupil-data mappings.
    It also maintains a mapping {pid -> pupil-data}.
    The resulting list should only be modified via the
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
#
    def sortlist(self):
        """Alphabetical sort.
        """
        self.sort(key = sortkey)

###

class Pupils(PupilsBase):
    def __init__(self, schoolyear):
        super().__init__()
        self.schoolyear = schoolyear
        self.filepath = year_path(self.schoolyear, self.CLASS_TABLE)
        with gzip.open(self.filepath + '.json.gz', 'rt',
                encoding='UTF-8') as zipfile:
            data = json.load(zipfile)
        if data['SCHOOLYEAR'] != self.schoolyear:
            raise PupilError(_SCHOOLYEAR_MISMATCH.format(
                    filepath = self.filepath))
        self._modified = data.get('__MODIFIED__')
        for pdata in data['__PUPILS__']:
            pid = pdata['PID']
            try:
                pd0 = self[pid]
            except KeyError:
                pass
            else:
                raise PupilError(_PID_DUPLICATE.format(pid = pid,
                        p1 = self.name(pd0), c1 = pd0['CLASS'],
                        p2 = self.name(pdata), c2 = pdata['CLASS']))
            self[pid] = {f: pdata.get(f) or '' for f in self.FIELDS}
        self.fill_classes()
#
    def fill_classes(self):
        """Prepare class lists, sorted by name.
        """
        self._klasses = {}
        for pid, pdata in self.items():
            k = pdata['CLASS']
            try:
                plist = self._klasses[k]
            except KeyError:
                plist = _PupilList()
                self._klasses[k] = plist
            plist.append(pdata)
        for plist in self._klasses.values():
            plist.sortlist()
#
    def classes(self):
        """Return a sorted list of class names.
        """
        return sorted(self._klasses)
#
    @classmethod
    def name(cls, pdata):
        """Return the pupil's "short" name.
        """
        return pdata['FIRSTNAME'] + ' ' + cls.lastname(pdata)
#
    @staticmethod
    def lastname(pdata):
        """Return the pupil's lastname. This method is provided in order
        to "decode" the name, which could have a "tussenvoegsel" separator.
        """
        return pdata['LASTNAME'].replace('|', ' ')
#
    @staticmethod
    def pstring(pdata):
        """A visual representation of a pupil-data mapping.
        """
        items = ['{k}={v}'.format(k = f, v = v) for f, v in pdata.items()]
        return 'Pupil Data: <%s>' % '; '.join(items)
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
        plist = _PupilList()
        for pdata in self._klasses[klass]:
            if date:
                # Check exit date
                exd = pdata.get('EXIT_D')
                if exd and exd < date:
                    continue
            if streams and pdata.get('STREAM') not in streams:
                continue
            plist.append(pdata)
        return plist
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
        info = {r[0]:r[1] for r in ptable.info}
        # Get column mapping: {field -> column index}
        # Convert the localized names to uppercase to avoid case problems.
        # Get the columns for the localized field names
        colmap = {}
        col = -1
        for t in ptable.fieldnames():
            col += 1
            colmap[t.upper()] = col
        # ... then for the internal field names,
        # collect positions of fields to be collected, if possible
        field_index = []
        for f, t in self.FIELDS.items():
            try:
                field_index.append((f, colmap[t.upper()]))
            except KeyError:
                pass
        # Collate rows into classes
        classes = {}
        for row in ptable:
            pdata = {}
            for f, i in field_index:
                pdata[f] = row[i] or ''
            try:
                klass = pdata['CLASS']
                if not klass:
                    raise KeyError
            except KeyError:
                raise PupilError(_CLASS_MISSING.format(row = repr(pdata)))
            try:
                plist = classes[klass]
            except KeyError:
                plist = _PupilList()
                classes[klass] = plist
            plist.append(pdata)
        for klass, plist in classes.items():
            if not info.get('__KEEP_NAMES__'):
                # "Renormalize" the name fields
                for pdata in plist:
                    try:
                        firstnames = pdata['FIRSTNAMES']
                        lastname = pdata['LASTNAME']
                    except KeyError:
                        raise PupilError(_NAME_MISSING.format(
                                row = repr(pdata)))
                    pdata['FIRSTNAMES'], \
                    pdata['LASTNAME'], \
                    pdata['FIRSTNAME'] = tussenvoegsel_filter(
                            firstnames, lastname,
                            pdata.get('FIRSTNAME') or firstnames)
            plist.sortlist()
        return classes
#
    def compare_update(self, newclasses):
        """Compare the new data with the existing data and compile a list
        of changes, grouped according to class. There are three types:
            - new pupil
            - pupil to remove (pupils shouldn't be removed within a
              school-year, just marked in EXIT_D, but this could be needed
              for patching or migrating to a new year)
            - field(s) changed.
        """
        pidset = set(self)      # to register removed pupils
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
                    old = self[pid]
                except KeyError:
                    # New entry
                    kchanges.append(('NEW', pdata))
                    continue
                pidset.remove(pid)
                # Compare fields.
                delta = self.compare(old, pdata)
                if delta:
                    # There is no special handling for change of CLASS
                    kchanges.append(('DELTA', old, delta))
        # Add removed pupils to list
        for pid in pidset:
            pdata = self[pid]
            changes[pdata['CLASS']].append(('REMOVE', pdata))
        return changes
#
    @staticmethod
    def compare(old, new):
        """Compare the fields of the old pupil-data with the new ones.
        Return a list of pairs detailing the deviating fields:
            [(field, new-value), ...]
        If a field is missing in the new data, it will be ignored (not
        included in the resulting list).
        """
        delta = []
        for k, v in old.items():
            try:
                vnew = new[k]
            except KeyError:
                continue
            if v != vnew:
                delta.append((k, vnew))
        return delta
#
    def update_classes(self, changes):
        """Apply the changes in the <changes> lists to the pupil data.
        The entries are basically those generated by <self.compare_update>,
        but it would be possible to insert a filtering step in between.
        """
        for klass, change_list in changes.items():
            for d in change_list:
                pdata = d[1]
                if d[0] == 'NEW':
                    # Add to pupils
                    self[pdata['PID']] = pdata
                elif d[0] == 'REMOVE':
                    # Remove from pupils
                    del(self[pdata['PID']])
                elif d[0] == 'DELTA':
                    # changes field values
                    self[pdata['PID']].update(d[2])
                else:
                    raise Bug("Bad delta key: %s" % d[0])
        # Regenerate class lists
        self.fill_classes()
        # Make changes persistent
        self.save()
#
    def modify_pupil(self, pupil_data):
        """This is used by the pupil-data editor. All changes to a pupil's
        data should pass through here.
        It ensures that the internal structures are consistent and that
        the changes get saved to the persistent storage.
        """
        pid = pupil_data['PID']
        if pupil_data.get('*REMOVE*'):
            remove = True
        else:
            remove = False
            # Check that essential fields are present
            missing = []
            for f in self.ESSENTIAL_FIELDS:
                if not pupil_data.get(f):
                    missing.append(self.FIELDS[f])
            if missing:
                REPORT('ERROR', _MISSING_FIELDS.format(
                        fields = '\n  '.join(missing)))
                return False
        if remove:
            del(self[pid])
        else:
            if pid not in self:
#TODO: also a flag for a new pupil?
                # A new pupil ...
                # Check PID validity
                self.check_new_pid_valid(pid)
            # Rebuild pupil entry
            self[pid] = {f: pupil_data.get(f) or '' for f in self.FIELDS}
        # Regenerate class lists
        self.fill_classes()
        # Make changes persistent
        self.save()
        return True
#
    def save(self):
        """Save the pupil data as a compressed json file.
        The first save of a day causes the current data to be backed up.
        """
        # Back up old table, if it exists
        timestamp = datetime.datetime.now().isoformat(sep = '_',
                timespec = 'minutes')
        if not os.path.isdir(self.filepath):
            os.makedirs(self.filepath)
        fpath = self.filepath + '.json.gz'
        if os.path.isfile(fpath):
            today = timestamp.split('_', 1)[0]
            bpath = os.path.join(self.filepath, today + '.json.gz')
            if not os.path.isfile(bpath):
                shutil.copyfile(fpath, bpath)
        pdlist = []
        for klass in self.classes():
            for pd in self.class_pupils(klass):
                # It's probably most convenient to save all fields,
                # e.g. in case the json is edited externally.
                # The space saving through filtering is minimal.
                #pd = {k: v for k, v in pd.items() if v}
                pdlist.append(pd)
        data = {
            'TITLE': 'Pupil Data',
            'SCHOOLYEAR': self.schoolyear,
            '__MODIFIED__': timestamp,
            '__PUPILS__': pdlist
        }
        with gzip.open(fpath, 'wt', encoding = 'utf-8') as zipfile:
            json.dump(data, zipfile, ensure_ascii = False)
        self._modified = timestamp
#
    def backup(self, filepath):
        """Save a table with all the pupil data for back-up purposes.
        This can be used as an "update" source to reinstate an earlier
        state.
        The field names are "translated".
        """
        info = (
            (self.SCHOOLYEAR, self.schoolyear),
            ('__MODIFIED__', self._modified),
            ('__KEEP_NAMES__', '*')
        )
        pdlist = []
        for klass in self.classes():
            pdlist.append({})
            for pd in self.class_pupils(klass):
                pdlist.append(pd)
        bstream = make_db_table(self.TITLE, self.FIELDS,
                pdlist, info = info)
        suffix = '.xlsx' if USE_XLSX else '.tsv'
        with open(filepath + suffix, 'wb') as fh:
            fh.write(bstream)


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    from core.base import init

#************** Start new year from raw data **************#
#    init(os.path.join(os.path.dirname(os.path.dirname(this)), 'DATA'))
#    _year = '2021'
#    pupils = Pupils(_year)
#    _ptables = pupils.read_source_table(year_path(_year,
#            'Quelldaten/PUPILS_2021.tsv'))
#    _delta = pupils.compare_update(_ptables)
#    for k, dlist in _delta.items():
#        print("\n --- KLASSE:", k)
#        for d in dlist:
#            print("  ", d)
#    pupils.update_classes(_delta)
#    quit(0)
#----------------------------------------------------------#

    init()
    _year = '2016'
    pupils = Pupils(_year)
    print("\nCLASSES:", pupils.classes())

    ### Make a back-up table
    pupils.backup(os.path.join(DATA, 'testing', 'tmp',
            'PUPILS_%s' % _year))
#    quit(0)

#************** Read and write **************#
### This just does a resorting of the data within the json file
### (the sorting os done when loading the file), which should
### make no difference ...
#    pupils.save()
#    quit(0)
#----------------------------------------------------------#

    ### Show the information for all pupils in a class
    _klass = '12'
    print("\n $$$", _klass)
    plist = pupils.class_pupils(_klass)
    for pdata in plist:
        print("\n :::", pdata)

    ### Show the information for a single pupil, keyed by pid
    _pid = '200502'
    _pdata = pupils[_pid]
    print("\n PUPIL %s (class %s)" % (_pdata['PID'], _pdata['CLASS']))
    print("  ", _pdata)

    ### Update the pupil data with some changes from a new "master" table
    print("\n§§§ CHECK PUPILS UPDATE §§§")
    _ptables = pupils.read_source_table(os.path.join(DATA, 'testing',
            'delta_test_pupils_2016'))  # modified table
    _delta = pupils.compare_update(_ptables)
    for klass, changes in _delta.items():
        print("CLASS %s:" % klass)
        for c in changes:
            print("  $  ", c)
    pupils.update_classes(_delta)

    ### Revert the changes by "updating" from a saved table
    _ptables = pupils.read_source_table(os.path.join(DATA, 'testing',
            'PUPILS_2016.tsv')) # original table
    _delta = pupils.compare_update(_ptables)
    for k, dlist in _delta.items():
        print("\n --- KLASSE:", k)
        for d in dlist:
            print("  ", d)
    pupils.update_classes(_delta)
