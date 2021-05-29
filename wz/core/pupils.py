# -*- coding: utf-8 -*-

"""
core/pupils.py - last updated 2021-05-29

Manage pupil data.

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
# field-value mappings (one for each pupil).
# When changes are made, date-time labelled back-ups are made, but only
# the first change of a day is backed up.
# Structure of the json file:
# SCHOOLYEAR: schoolyear
# TITLE: "Schülerliste"     # not used
# __PUPILS__: [<pdata>]     # <pdata> is a mapping, field -> value
# __MODIFIED__: <date-time>
# It would probably be good to have a gui-editor for such files, but
# the data can be exported as a table (tsv or xlsx). This can be
# edited with a separate tool and the result read in as an "update".

import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start
    start.setup(os.path.join(basedir, 'TESTDATA'))

### Messages
_SCHOOLYEAR_MISMATCH = "Schülerdaten: falsches Jahr in:\n  {filename}"
_NO_SCHOOLYEAR = "Kein '{year}' angegeben in Schülertabelle:\n  {filename}"
_SCHOOLYEAR_MISMATCH_DB = "Schüler-Datenbank-Fehler: falsches Jahr"
_NO_SCHOOLYEAR_DB = "Schüler-Datenbank-Fehler: kein 'SCHOOLYEAR'"
_PID_DUPLICATE = "Schülerkennung {pid} mehrfach vorhanden:\n" \
        "  Klasse {c1} – {p1}\n  Klasse {c2} – {p2}"
_MISSING_FIELDS = "Diese Felder dürfen nicht leer sein:\n  {fields}"
_BACKUP_FILE = "Schülerdaten für Klasse {klass} gespeichert als:\n  {path}"
_FULL_BACKUP_FILE = "Alle Schülerdaten gespeichert als:\n  {path}"

import datetime, io

from local.base_config import PupilError, PupilsBase, sortkey
from core.base import Dates
from tables.spreadsheet import Spreadsheet, TableError, \
        read_DataTable, filter_DataTable, make_DataTable, \
        make_DataTable_filetypes
from tables.datapack import get_pack, save_pack

### -----

#TODO: Consider adding data types (incl. selection lists) to field/info-lists.

#TODO: I suppose the program should start with the stored data? If there is
# none (or if it is dodgy) there can be a question dialog to load from
# file.
# What about updating from file, with update selections?

def Pupil_File(filepath, extend = True):
    with open(filepath, 'rb') as fh:
        fbytes = fh.read()
    return Pupils.init_from_bytes(fbytes, filepath, extend)
##
class Pupils(dict):
    """Handler for pupil data.
    Pupil-data items (mappings) can be added from various sources:
     - the internal database
     - an external file
     - an external modified version of the existing data.
    Normally the fields defined for a pupil (CONFIG['CLASS_TABLE'])
    will be included, adding empty ones (<NONE>) if necessary. See the
    method <init_from_bytes>.
    An instance of this class is a <dict> holding the pupil data as a
    mapping: {pid -> {field: value, ...}}.
    The data is also sorted (alphabetically) into classes, the results
    being available through the method <class_pupils>.
    """
    __pupils = None     # cache for current year
    #+
    @classmethod
    def fetch(cls):
        """This is the main method for fetching the current data, which
        is then cached in memory.
        """
        if not cls.__pupils:
            cls.__pupils = cls()
        return cls.__pupils
    #+
    @classmethod
    def tocache(cls, pupils = None):
        """Set or clear the cache.
        """
        cls.__pupils = pupils
#
    @classmethod
    def init_from_bytes(cls, filebytes, filename, extend = True):
        """Make a <Pupils> instance from a file passed as <bytes>.
        The <filename> parameter is necessary to determine the type of
        data (ods, xlsx or tsv) – on the basis of its ending.
        For update tables, <extend> should be false, so that no fields
        are added to those in the source.
        """
        bstream = io.BytesIO(filebytes)
        bstream.filename = filename
        T_SCHOOLYEAR = CONFIG['T_SCHOOLYEAR']
        ptable = read_DataTable(bstream)
        PupilsBase.process_source_table(ptable)
        ptable = filter_DataTable(ptable,
                SCHOOL_DATA['PUPIL_FIELDS'],
                infolist = [['SCHOOLYEAR', T_SCHOOLYEAR, False]],
                extend = extend)
        info = ptable['__INFO__']
        sy = info.get('SCHOOLYEAR')
        if sy:
            if sy != SCHOOLYEAR:
                raise PupilError(_SCHOOLYEAR_MISMATCH.format(
                        filename = filename))
        else:
            REPORT('WARN', _NO_SCHOOLYEAR.format(
                    year = CONFIG['T_SCHOOLYEAR'],
                    filename = filename))
        return cls(ptable)
#
    def __init__(self, ptable = None):
        """If there is no data, look for the internal database. Fail if
        it is not present.
        """
        super().__init__()
        if not ptable:
            filepath = DATAPATH(CONFIG['CLASS_TABLE'])
            ptable = get_pack(filepath)
            try:
                if ptable['__INFO__']['SCHOOLYEAR'] != SCHOOLYEAR:
                    raise PupilError(_SCHOOLYEAR_MISMATCH_DB)
            except KeyError:
                raise PupilError(_NO_SCHOOLYEAR_DB)
        self.__fields = ptable['__FIELDS__']
        self.__info = ptable['__INFO__']
        self.set_data(ptable['__ROWS__'])
#
    def set_data(self, pdata_list):
        """Initialize the pupil-data mapping from the given pupil-data.
        items. The pupils are also allocated to classes and sorted within
        these.
        """
        self.__classes = {}
        for pdata in pdata_list:
            pid = pdata['PID']
            pd0 = self.get(pid)
            if pd0:
                raise PupilError(_PID_DUPLICATE.format(pid = pid,
                        p1 = self.name(pd0), c1 = pd0['CLASS'],
                        p2 = self.name(pdata), c2 = pdata['CLASS']))
            klass = pdata.get('CLASS')
            if not klass:
                raise PupilError(_CLASS_MISSING.format(row = repr(pdata)))
            try:
                plist = self.__classes[klass]
            except KeyError:
                plist = _PupilList()
                self.__classes[klass] = plist
            self[pid] = pdata
            plist.append(pdata)
        for plist in self.__classes.values():
            plist.sortlist()
#
    def save(self):
        """Save the pupil data to the pupil-database.
        The first save of a day causes the current data to be backed up,
        if it exists.
        """
        timestamp = Dates.timestamp()
        today = timestamp.split('_', 1)[0]
        pdlist = []
        for klass in self.classes():
            pdlist += self.__classes[klass]
        self.__info = {
            '__TITLE__': 'Pupil Data',
            'SCHOOLYEAR': SCHOOLYEAR,
            '__MODIFIED__': timestamp,
        }
        data = {
            '__INFO__': self.__info,
            '__FIELDS__': self.__fields,
            '__ROWS__': pdlist
        }
        save_pack(DATAPATH(CONFIG['CLASS_TABLE']), data, today)
        if self != self.__pupils:
            # Make this the cached pupil-data
            self.tocache(self)
#
    def classes(self):
        """Return a sorted list of class names.
        """
        return sorted(self.__classes)


#TODO: update ...
#
    @staticmethod
    def pstring(pdata):
        """A visual representation of a pupil-data mapping.
        """
        items = ['{k}={v}'.format(k = f, v = v) for f, v in pdata.items()]
        return 'Pupil Data: <%s>' % '; '.join(items)
#
    def class_pupils(self, klass, groups = None, date = None):
        """Read the pupil data for the given school-class (possibly with
        group filter).
        Return a list of mappings {field -> value} (the table rows), the
        pupils being ordered alphabetically.
        The result also has the attribute <_pidmap>, which maps the pid
        to the pupil data.
        If a <date> is supplied, pupils who left the school before that
        date will not be included.
        If <groups> is provided, only pupils in one of these groups are
        included, otherwise all pupils in the class. <groups> must be a
        <set> – '*' is not valid here.
        """
        plist = _PupilList()
        for pdata in self.__classes[klass]:
            if date:
                # Check exit date
                exd = pdata.get('EXIT_D')
                if exd and exd < date:
                    continue
            if groups and not (groups & set(pdata.get('GROUPS'))):
                continue
            plist.append(pdata)
        return plist
#
    def compare_update(self, newdata):
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
        for k in self.__classes:
            changes[k] = []
        for k in newdata.__classes:
            changes[k] = []
        # Search for changes
        for klass, plist in newdata.__classes.items():
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
        # Only include non-empty lists in result
        return {k: clist for k, clist in changes.items() if clist}
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
        count = 0
        for klass, change_list in changes.items():
            count += len(change_list)
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
        if count > 0:
            # Regenerate class lists
            self.fill_classes()
            # Make changes persistent
            self.save()
#
    def remove_pupil(self, pid):
        del(self[pid])
        # Regenerate class lists
        self.fill_classes()
        # Make changes persistent
        self.save()
        return True
#
    def modify_pupil(self, pupil_data_list):
        """This is used by the pupil-data editor. All changes to a pupil's
        data should pass through here.
        It ensures that the internal structures are consistent and that
        the changes get saved to the persistent storage.
        By supplying a pupil-id which is not already in use, a new
        pupil can be added.
        <pupil_data_list> is a list of pupil-data mappings.
        """
        for pupil_data in pupil_data_list:
            pid = pupil_data['PID']
            # Check that essential fields are present
            missing = []
            for f in self.ESSENTIAL_FIELDS:
                if not pupil_data.get(f):
                    missing.append(self.FIELDS[f])
            if missing:
                REPORT('ERROR', _MISSING_FIELDS.format(
                        fields = '\n  '.join(missing)))
                return False
            if pid not in self:
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
    def backup(self, filepath, klass = None):
        """Save a table with all the pupil data for back-up purposes.
        This can be used as an "update" source to reinstate an earlier
        state.
        The field names are "translated".
        If <klass> is supplied, only the data for that class will be saved.
        """
        info = [
            (CONFIG['T_SCHOOLYEAR'], self.schoolyear),
            ('__MODIFIED__', self._modified),
            ('__KEEP_NAMES__', '*') # The names don't need "renormalizing"
        ]
        if klass:
            info.append(('__CLASS__', klass))
            classes = [klass]
        else:
            classes = self.classes()
        pdlist = []
        for k in classes:
            pdlist.append({})
            for pd in self.class_pupils(k):
                pdlist.append(pd)
        try:
            filetype = filepath.rsplit('.', 1)[1]
            if filetype not in make_db_table_filetypes:
                raise IndexError
        except IndexError:
            filetype = CONFIG.get('TABLE_FORMAT') or 'tsv'
            filepath += '.' + filetype
        bstream = make_db_table(self.TITLE, self.FIELDS,
                pdlist, info = info, filetype = filetype)
        with open(filepath, 'wb') as fh:
            fh.write(bstream)
        REPORT('INFO', _BACKUP_FILE.format(klass = klass,
                path = filepath) if klass
                else _FULL_BACKUP_FILE.format(path = filepath))
#
#TODO ...
    def migrate(self, repeat_pids):
        """Create a pupil-data structure for the following year.
        """
        # Pass the calendar (for the current year) to the function
        # handling the step (<year_step>) in case dates are needed.
        calendar = Dates.get_calendar(self.schoolyear)
        nextyear = str(int(self.schoolyear) + 1)
        day1 = Dates.day1(nextyear) # for filtering out pupils who have left
        newpupils = []
        for pid, pdata in self.items():
            # Filter out pupils who have left
            exit_date = pdata['EXIT_D']
            if exit_date and exit_date < day1:
                continue
            if pid in repeat_pids:
                newpupils.append(pdata.copy())
            else:
                pd = self.year_step(pdata, calendar)
                if pd:
                    newpupils.append(pd)
        # Sort into classes and save
        pupils = _Pupils(nextyear)
        pupils.set_data(newpupils, norm_fields = True)
        pupils.save()
#
#TODO
    def final_year_pupils(self, klass):
        """Return list of pupil-data items for pupils in their final year.
        """
        lgroups = self.leaving_groups(klass)
        if lgroups:
            if lgroups == '*':
                plist = self.class_pupils(klass)
            else:
                plist = self.class_pupils(klass, groups = lgroups)
            return [(pdata['PID'], self.name(pdata)) for pdata in plist]
        else:
            return None

###

class _PupilList(list):
    """Representation for a list of pupil-data mappings.
    It also maintains a mapping {pid -> pupil-data}.
    The resulting list should only be modified via the
    methods provided here.
    """
    def __init__(self):
        super().__init__()
        self.__pidmap = {}
#
    def append(self, item):
        super().append(item)
        self.__pidmap[item['PID']] = item
#
    def remove(self, item):
        super().remove(item)
        del(self.__pidmap[item['PID']])
#
    def pid2pdata(self, pid):
        return self.__pidmap[pid]
#
    def sortlist(self):
        """Alphabetical sort.
        """
        self.sort(key = sortkey)


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':

#************** Start new year from raw data **************#
#TODO
#    init(os.path.join(os.path.dirname(os.path.dirname(this)), 'DATA'))
##   year = '2021'
#    pupils = PUPILS()

#TODO: year_path ?
#    _ptables = Pupils_File(_year, filepath = year_path(_year,
#            'Quelldaten/PUPILS_2021.tsv'), norm_fields = False)
#    _delta = pupils.compare_update(_ptables)
#    for k, dlist in _delta.items():
#        print("\n --- KLASSE:", k)
#        for d in dlist:
#            print("  ", d)
#    pupils.update_classes(_delta)
#    quit(0)
#----------------------------------------------------------#

    _ptables = Pupil_File(DATAPATH('testing/PUPILS_2016.tsv')) # original table
    print("\nCLASSES (file):", _ptables.classes())

# This overwrites the current database.
#    _ptables.save()

    print("\nLEAVING in 12:", _ptables.final_year_pupils('12'))

    pupils = Pupils.fetch()
    print("\nCLASSES (db):", pupils.classes())

    _ptables = Pupil_File(DATAPATH('testing/delta_test_pupils_2016.ods'),
            extend = False)

    _delta = pupils.compare_update(_ptables)
    for k, dlist in _delta.items():
        print("\n --- KLASSE:", k)
        for d in dlist:
            print("  ", d)


#TODO ...
    quit()

    pupils.update_classes(_delta)
    ### Migrate to next year
#    pupils.migrate([])

    ### Make a back-up table
    bpath = DATAPATH('testing/tmp/PUPILS_%s' % pupils.schoolyear)
    pupils.backup(bpath)

#************** Read and write **************#
### This just does a resorting of the data within the json file
### (the sorting is done when loading the file), which should
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
    _ptables = Pupils_File(
            filepath = DATAPATH('testing/delta_test_pupils_2016'),
            norm_fields = False)  # modified table
    _delta = pupils.compare_update(_ptables)
    for klass, changes in _delta.items():
        print("CLASS %s:" % klass)
        for c in changes:
            print("  $  ", c)
    pupils.update_classes(_delta)

    ### Revert the changes by "updating" from a saved table
    _ptables = Pupils_File(filepath = DATAPATH('testing/PUPILS_2016.tsv'),
            norm_fields = True) # original table
    _delta = pupils.compare_update(_ptables)
    for k, dlist in _delta.items():
        print("\n --- KLASSE:", k)
        for d in dlist:
            print("  ", d)
    pupils.update_classes(_delta)
