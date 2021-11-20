"""
core/pupils.py - last updated 2021-11-20

Manage pupil data.

=+LICENCE=================================
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
=-LICENCE=================================

For each school class there is a DataTable containing the pupil data.
The file is a direct representation of the form in which pupil data
is read in and passed around, a mapping:
    {   '__INFO__':     {key: value, ... },
        '__FIELDS__':   [field1, ... ],
        '__ROWS__':     [{field: value, ... }, ... ]
    }
The info keys are, at present:
    __TITLE__: 'Pupil Data' (for example, not used in code)
    SCHOOLYEAR: '2016' (year in which the end of the school year falls)
    CLASS: '02G' (name of the class)
    __MODIFIED__: <date-time> (not used in code)
"""

### Messages
_SCHOOLYEAR_MISMATCH_DB = "Schüler-Datenbank-Fehler: falsches Jahr in\n{path}"
_CLASS_MISMATCH_DB = "Schüler-Datenbank-Fehler: falsche Klasse in\n{path}"
_DOUBLE_PID_DB = "Schüler-Datenbank-Fehler: Schüler-ID {pid} doppelt" \
        " vorhanden, in Klassen {k1} und {k2}"




_SCHOOLYEAR_MISMATCH = "Schülerdaten: falsches Jahr in:\n  {filename}"
_NO_SCHOOLYEAR = "Kein '{year}' angegeben in Schülertabelle:\n  {filename}"
_NO_SCHOOLYEAR_DB = "Schüler-Datenbank-Fehler: kein 'SCHOOLYEAR'"
_PID_DUPLICATE = "Schülerkennung {pid} mehrfach vorhanden:\n" \
        "  Klasse {c1} – {p1}\n  Klasse {c2} – {p2}"
_MISSING_FIELDS = "Diese Felder dürfen nicht leer sein:\n  {fields}"
_BACKUP_FILE = "Schülerdaten für Klasse {klass} gespeichert als:\n  {path}"
_FULL_BACKUP_FILE = "Alle Schülerdaten gespeichert als:\n  {path}"

_TITLE = 'Schülerdaten'

###############################################################

import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start
#    start.setup(os.path.join(basedir, 'TESTDATA'))
    start.setup(os.path.join(basedir, 'DATA'))

### +++++

#import io
import re
from glob import glob

#from local.base_config import PupilError, PupilsBase, sortkey
from core.base import Dates
from tables.spreadsheet import read_DataTable, filter_DataTable, \
        make_DataTable, make_DataTable_filetypes, TableError
#from tables.datapack import get_pack, save_pack

### -----

#TODO: I suppose the program should start with the stored data? If there is
# none (or if it is dodgy) there can be a question dialog to load from
# file.
# What about updating from file, with update selections?

### **************************************************************** ###

class PupilData(dict):
    def __init__(self, fromdict, klass=None):
        super().__init__()
        self.update(fromdict)
        if klass:
            self['CLASS'] = klass

    def __str__(self):
        """A visual representation of a pupil-data mapping.
        """
        items = ['{k}={v}'.format(k = f, v = v) for f, v in self.items()]
        return 'Pupil Data: <%s>' % '; '.join(items)

    def lastname(self):
        """A '|' may be present to separate a prefix ("tussenvoegsel")
        from the main name (see method <sorting_name> below).
        """
        return self['LASTNAME'].replace('|', '')

    def name(self):
        """Return the short-name of the pupil.
        """
        return f"{self['FIRSTNAME']} {self.lastname()}"

    def sorting_name(self):
        """In Dutch there is a word for those little last-name prefixes
        like "van", "von" and "de": "tussenvoegsel". For sorting purposes
        these can be a bit annoying because they should often be ignored,
        e.g. "Vincent van Gogh" would be sorted primarily under "G".

        A simple mechanism to handle this behaviour is provided by
        allowing the separator '|' to appear in a last-name. Anything
        before this separator is treated as a "tussenvoegsel". For
        sorting, the name will be reordered as:
            "last-name[_tussenvoegsel]_first-name"
        where the "[_tussenvoegsel]" bit is only present if this
        component is actually present.
        In addition, non-ASCII characters are substituted.
        """
        _lastname = self['LASTNAME']
        try:
            tv, _lastname = _lastname.split('|', 1)
            tv, _lastname = tv.rstrip(), _lastname.lstrip()
        except ValueError:
            return asciify(f"{_lastname}_{self['FIRSTNAME']}")
        return asciify(f"{_lastname}_{tv}_{self['FIRSTNAME']}")


class Pupils(dict):
    """Handler for pupil data.
    The internal pupil data should be read and written only through this
    interface.
    An instance of this class is a <dict> holding the pupil data as a
    mapping: {pid -> {field: value, ...}}.
    The fields defined for a pupil are read from the configuration file
    CONFIG/PUPIL_DATA. For convenience, a field CLASS is added
    internally to each pupil record.
    The list of pupil-ids for a class is available via the method
    <class_pupils> (alphabetically ordered).
    """
    def __init__(self):
        self.__classes = {}
        super().__init__()
        # Fields:
        self.config = MINION(DATAPATH("CONFIG/PUPIL_DATA"))
        # Each class has a table-file (substitute {klass}):
        self.class_path = DATAPATH(CONFIG["PUPIL_TABLE"])
        for fpath in glob(self.class_path.format(klass="*")):
            #print("READING", fpath)
            class_table = read_DataTable(fpath)
            try:
                class_table = filter_DataTable(class_table, self.config,
                        notranslate=True)
            except TableError as e:
#TODO
                print("ERROR:", str(e), "in\n", fpath)
                raise

            # The data should already be alphabetically ordered here.
            info = class_table["__INFO__"]
            if info["SCHOOLYEAR"] != SCHOOLYEAR:
                raise PupilError(_SCHOOLYEAR_MISMATCH_DB.format(path=fpath))
            klass = info["CLASS"]
            if self.class_path.format(klass=klass) != fpath:
                raise PupilError(_CLASS_MISMATCH_DB.format(path=fpath))
            pdata_list = []
            self.__classes[klass] = pdata_list
            for row in class_table["__ROWS__"]:
                pid = row["PID"]
                if pid in self:
                    raise PupilError(_DOUBLE_PID_DB.format(pid=pid,
                            k1=self[pid]["CLASS"], k2=klass))
                pdata = PupilData(row, klass)
                self[pid] = pdata
                pdata_list.append(pdata)

    def classes(self):
        """Return a sorted list of class names.
        """
        return sorted(self.__classes)

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
        list/set of groups – '*' is not valid here.
        """
        plist = []
        groupset = set(groups or [])
        for pdata in self.__classes[klass]:
            if date:
                # Check exit date
                exd = pdata.get("EXIT_D")
                if exd and exd < date:
                    continue
            if groups and not (groupset & set(pdata.get("GROUPS"))):
                continue
            plist.append(pdata)
        return plist

    def pid2name(self, pid):
        return self[pid].name()

    def final_year_pupils(self):
        """Return lists of pupils in their final year:
            {class: [(pid, name), ... ], ...}
        """
        collect =  {}
        for k, l in CONFIG["LEAVING_GROUPS"].items():
            if l == '*':
                plist = self.class_pupils(k)
            else:
                plist = self.class_pupils(k, groups = l)
            collect[k] = [(pdata['PID'], pdata.name()) for pdata in plist]
        return collect

    def sort_class(self, klass, nosave=False):
        """Sort the pupil data items for the given class alphabetically.
        This should only be necessary if names are changed.
        """
        if nosave:
            return sorted(self.__classes[klass], key=PupilData.sorting_name)
        self.__classes[klass].sort(key=PupilData.sorting_name)





#TODO ...
#
#
#
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
            '__TITLE__': _TITLE,
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
            for f, *tnx in SCHOOL_DATA['PUPIL_FIELDS']:
                fields.append(f)
                if tnx[1]:     # an essential field
                    if not pupil_data.get(f):
                        missing.append(tnx[0] or f)
            if missing:
                REPORT('ERROR', _MISSING_FIELDS.format(
                        fields = '\n  '.join(missing)))
                return False
            if pid not in self:
                # A new pupil ... check PID validity
                self.check_new_pid_valid(pid)
            # Rebuild pupil entry
            self[pid] = {f: pupil_data.get(f) or NONE for f in self.__fields}
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
        info = {
            CONFIG['T_SCHOOLYEAR']: self.__info.get('SCHOOLYEAR'),
            '__MODIFIED__': self.__info.get('__MODIFIED__') \
                    or Dates.timestamp(),
            '__KEEP_NAMES__': '*' # The names don't need "renormalizing"
        }
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
            if filetype not in make_DataTable_filetypes:
                raise IndexError
        except IndexError:
            filetype = CONFIG.get('TABLE_FORMAT') or 'tsv'
            filepath += '.' + filetype
        data = {
            '__INFO__': info,
            '__FIELDS__': self.__fields,
            '__ROWS__': pdlist
        }
        fbytes = make_DataTable(data, filetype)
        fdir = os.path.dirname(filepath)
        if not os.path.isdir(fdir):
            os.makedirs(fdir, exist_ok = True)
        with open(filepath, 'wb') as fh:
            fh.write(fbytes)
        REPORT('INFO', _BACKUP_FILE.format(klass = klass,
                path = filepath) if klass
                else _FULL_BACKUP_FILE.format(path = filepath))
#
    def migrate(self, repeat_pids = [], save_as = None):
        """Create a pupil-data structure for the following year.
        If <save_as> is provided, it should be a file-path: the new
        pupil data will be saved here (as a DataTable) instead of in the
        internal database.
        The current pupil data is saved as a DataTable to the 'tmp'
        folder within the data area.
        If <repeat_pids> is provided it should be an iterable object
        listing pupil-ids for those who will definitely stay on, even
        if their class/group would suggest leaving. This is, of course,
        overridden by a leaving date! Their data (including class) will,
        however be unchanged.
        """
        yes_pids = set(repeat_pids)
        nextyear = str(int(SCHOOLYEAR) + 1)
        day1 = Dates.day1(nextyear) # for filtering out pupils who have left
        newpupils = []
        # Filter out pupils from final classes, tweak pupil data
        for klass in self.classes():
            leavers = {pd[0] for pd in self.final_year_pupils(klass)}
            pdlist = self.class_pupils(klass, date = day1)
            for pdata in pdlist:
                pid = pdata['PID']
                if pid in yes_pids:
                    # Don't check if leaver, don't tweak
                    newpupils.append(pdata.copy())
                elif pid not in leavers:
                    # Progress to next class ...
                    new_pd = PupilsBase.next_class(pdata)
                    if new_pd:
                        # Also <next_class> can filter out pupils
                        newpupils.append(new_pd)
        info = {
            'SCHOOLYEAR': nextyear,
        }
        ptable = {
            '__INFO__': info,
            '__FIELDS__': self.__fields,
            '__ROWS__': newpupils
        }
        pupils = _Pupils(ptable)
        pupils.fill_classes()
        # First back-up the existing data.
        self.backup(DATAPATH(f'tmp/pupils_{SCHOOLYEAR}'))
        if save_as:
            # Don't replace the existing pupil data for the current year,
            # save the new table somewhere else.
            pupils.backup(save_as)
        else:
            # This replaces the existing pupil data for the current year!
            pupils.save()




def asciify(string, invalid_re = None):
    """This converts a utf-8 string to ASCII, e.g. to ensure portable
    filenames are used when creating files.
    Also spaces are replaced by underlines.
    Of course that means that the result might look quite different from
    the input string!
    A few explicit character conversions are given in the mapping
    <ASCII_SUB>.
    By supplying <invalid_re>, an alternative set of exclusion characters
    can be used.
    """
    # regex for characters which should be substituted:
    if not invalid_re:
        invalid_re = r'[^A-Za-z0-9_.~-]'
    def rsub (m):
        c = m.group (0)
        if c == ' ':
            return '_'
        try:
            return lookup[c]
        except:
            return '^'

    lookup = ASCII_SUB
    return re.sub(invalid_re, rsub, string)


# Substitute characters used to convert utf-8 strings to ASCII, e.g. for
# portable filenames. Non-ASCII characters which don't have
# entries here will be substituted by '^':
ASCII_SUB = {
    'ä': 'ae',
    'ö': 'oe',
    'ü': 'ue',
    'ß': 'ss',
    'Ä': 'AE',
    'Ö': 'OE',
    'Ü': 'UE',
    'ø': 'oe',
    'ô': 'o',
    'ó': 'o',
    'é': 'e',
    'è': 'e',
    # Latin:
    'ë': 'e',
    # Cyrillic (looks like the previous character, but is actually different).
    'ё': 'e',
    'ñ': 'n'
}

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

# Overwrite the current database.
#    _ptables = Pupil_File(DATAPATH('testing/PUPILS_2016.tsv')) # original table
#    _ptables.save()

    pupils = Pupils()
    print("\nCLASSES (db):", pupils.classes())
    for k, l in pupils.final_year_pupils().items():
        print(f"\nLEAVING in {k}: {repr(l)}")

#    for klass in pupils.classes():
#        print(f"\nSORT {klass}:")
#        for pdata in pupils.sort_class(klass, nosave=True):
#            print(f"  {pdata.sorting_name()}")
    quit(0)
    ### Make a trial migration to next school-year.
    ### This also makes a back-up of the current pupil data.
    pupils.migrate(repeat_pids = ('200888', '200301'),
            save_as = DATAPATH(f'testing/tmp/PUPILS_NEXT_{SCHOOLYEAR}'))

    _ptables = Pupil_File(DATAPATH('testing/delta_test_pupils_2016.ods'),
            extend = False)

    _delta = pupils.compare_update(_ptables)
    for k, dlist in _delta.items():
        print("\n --- KLASSE:", k)
        for d in dlist:
            print("  ", d)
    pupils.update_classes(_delta)

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
    _ptables = Pupil_File(DATAPATH('testing/delta_test_pupils_2016.ods'),
            extend = False)
    _delta = pupils.compare_update(_ptables)
    for klass, changes in _delta.items():
        print("CLASS %s:" % klass)
        for c in changes:
            print("  $  ", c)
    pupils.update_classes(_delta)

    ### Revert the changes by "updating" from a saved table
    _ptables = Pupil_File(DATAPATH('testing/PUPILS_2016.tsv'))
    _delta = pupils.compare_update(_ptables)
    for k, dlist in _delta.items():
        print("\n --- KLASSE:", k)
        for d in dlist:
            print("  ", d)
    pupils.update_classes(_delta)
