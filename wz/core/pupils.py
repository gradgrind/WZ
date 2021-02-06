# -*- coding: utf-8 -*-

"""
core/pupils.py - last updated 2021-02-06

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

# Fundamental redesign. Use a single file, json encoded, so that updates
# can be sort-of atomic (otherwise automatic handling of changes of class
# might be awkward). Keep a certain number of update steps, for an "undo"
# function. Back-ups can be gzipped and date-timed.
# Structure of the json file:
# SCHOOLYEAR: schoolyear
# TITLE: "Schülerliste"
# __PUPILS__: [<pdata>]     # <pdata> is a mapping, field: value
# __CHANGED__: <date-time>
# It would probably be good to have a gui-editor for such files ...

import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

### Messages
_SCHOOLYEAR_MISMATCH = "Schülerdaten: falsches Jahr in:\n  {filepath}"
_NAME_MISSING = "Eingabezeile fehlerhaft, Name unvollständig:\n  {row}"

_TABLE_MISMATCH = "Schuljahr oder Klasse ungültig in Tabelle:\n  {path}"
_BAK_EXISTS = "WARNING: Backup-Archiv für heute existiert schon," \
        " keine neue wird erstellt:\n  {fpath}"
_UNKNOWN_PID = "Schüler „{pid}“ ist nicht bekannt"
_PID_EXISTS = "Ungültiges Schülerkennzeichen, es gehört schon {name} in" \
        " Klasse {klass}"
_PID_DUPLICATE = "Schülerkennzeichen {pid} mehrfach vorhanden:\n" \
        "  Klasse {c1} – {p1}\n  Klasse {c2} – {p2}"

import datetime, shutil, json, gzip

from tables.spreadsheet import Spreadsheet, TableError, make_db_table
from local.base_config import year_path, PupilsBase
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

def NullPupilData(klass):
    """Return a "dummy" pupil-data instance, which can be used as a
    starting point for adding a new pupil.
    """
    return {
        'CLASS': klass, 'FIRSTNAME': 'Hansi',
        'LASTNAME': 'von|Meierhausen', 'FIRSTNAMES': 'Hans Herbert',
        'SEX': 'm', 'ENTRY_D': Dates.today()
    }

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
        self._changes = data['__CHANGED__']
        for pdata in data['__PUPILS__']:
            klass = pdata['CLASS']
            pid = pdata['PID']
            try:
                pd0 = self[pid]
            except KeyError:
                pass
            else:
                raise PupilError(_PID_DUPLICATE.format(pid = pid,
                        p1 = self.name(pd0), c1 = pd0['CLASS'],
                        p2 = self.name(pdata), c2 = klass))
            self[pid] = pdata
        self.fill_classes()
#
    def fill_classes(self):
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
        return list(self._klasses)
#
    @staticmethod
    def name(pdata):
        """Return the pupil's "short" name.
        """
        return pdata['FIRSTNAME'] + ' ' + pdata.lastname()
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

        # "Renormalize" the name fields
        for klass, plist in classes.items():
            for pdata in plist:
                try:
                    firstnames = pdata['FIRSTNAMES']
                    lastname = pdata['LASTNAME']
                except KeyError:
                    raise PupilError(_NAME_MISSING.format(row = repr(pdata)))
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
#? no special handling for class change?
                if delta:
                    kchanges.append(('DELTA', old, delta))
#
#                klass0 = old['CLASS']
#                if klass0 == klass:
#                    if delta:
#                        kchanges.append(('DELTA', old, delta))
#                else:
#                    # Changed class, add entry for OLD class.
#                    # <delta> is passed in here, though it may be empty
#                    changes[klass0].append(('REMOVE', old))
#                    old.tweak(delta)
#                    changes[klass].append(('NEW', old))
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
                    pdata.update(d[2])
                else:
                    raise Bug("Bad delta key: %s" % d[0])
        # Regenerate class lists
        self.fill_classes()
        # Make changes persistent
        self.save()
#
#TODO
    def modify_pupil(self, pupil_data, changes):
        """This is used by the pupil-data editor. All changes to a pupil's
        data should pass through here.
        It ensures that the internal structures are consistent and that
        the changes get saved to the persistent storage.
        """
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
#TODO: To save method?
            # Update __EXTRA__ field
            extra = {k: v for k, v in pupil_data.items()
                    if (k not in self.FIELDS) and v}
            pupil_data['__EXTRA__'] = json.dumps(extra)
        if newclass:
            npdlist = self.class_pupils(newclass)
            if oldclass != newclass or not oldpid:
                # Add pupil to <newclass>
                npdlist.append(pupil_data)
                npdlist.sort(key = sortkey)
            self.save_class(newclass, npdlist)
        if oldclass and oldclass != newclass:
            # Remove pupil from current class
            opdlist = self.class_pupils(oldclass)
            opdlist.remove(pupil_data)
#TODO: backup true?
            self.save_class(oldclass, opdlist, backup = False)
        # Invalidate global pid-mapping
        self.clear_pid_cache()
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
        for plist in self._klasses.values():
            for pd in plist:
                pdlist.append(pd)
        data = {
            '__TITLE__': 'Klassen',
            'SCHOOLYEAR': _year,
            '__CHANGED__': timestamp,
            '__PUPILS__': pdlist
        }
        with gzip.open(fpath, 'wt', encoding = 'utf-8') as zipfile:
            json.dump(data, zipfile, ensure_ascii = False)


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
    init()

    _year = '2016'
    pupils = Pupils(_year)

    print("\nCLASSES:", pupils.classes())
#    for k, plist in pupils._klasses.items():
#        plist.sortlist()
#    pupils.save()
#    quit(0)


    _klass = '12'
    print("\n $$$", _klass)
    plist = pupils.class_pupils(_klass)
    for pdata in plist:
        print("\n :::", pdata)

    _pid = '200502'
    _pdata = pupils[_pid]
    print("\n PUPIL %s (class %s)" % (_pdata['PID'], _pdata['CLASS']))
    print("  ", _pdata)

    print("\n§§§ CHECK PUPILS UPDATE §§§")
    _ptables = pupils.read_source_table(os.path.join(DATA, 'testing',
            'delta_test_pupils_2016'))  # modified table
    _delta = pupils.compare_update(_ptables)

    for klass, changes in _delta.items():
        print("CLASS %s:" % klass)
        for c in changes:
            print("  $  ", c)

#    quit(0)

    pupils.update_classes(_delta)

    _ptables = pupils.read_source_table(os.path.join(DATA, 'testing',
            'PUPILS_2016.tsv')) # original table
    _delta = pupils.compare_update(_ptables)
    for k, dlist in _delta.items():
        print("\n --- KLASSE:", k)
        for d in dlist:
            print("  ", d)
    pupils.update_classes(_delta)

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
