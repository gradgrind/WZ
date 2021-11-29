"""
core/pupils.py - last updated 2021-11-27

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
_CLASS_MISSING = "In importierten Daten: Klasse fehlt für {name}"
_FILTER_ERROR = "Schülerdaten-Fehler: {mesg}"
_PID_INVALID = "Ungültige Schülerkennung für {name}: '{pid}'"
_MISSING_FIELDS = "Diese Felder dürfen nicht leer sein:\n  {fields}"


#???
_SCHOOLYEAR_MISMATCH = "Schülerdaten: falsches Jahr in:\n  {filename}"
_NO_SCHOOLYEAR = "Kein '{year}' angegeben in Schülertabelle:\n  {filename}"
_NO_SCHOOLYEAR_DB = "Schüler-Datenbank-Fehler: kein 'SCHOOLYEAR'"
_PID_DUPLICATE = "Schülerkennung {pid} mehrfach vorhanden:\n" \
        "  Klasse {c1} – {p1}\n  Klasse {c2} – {p2}"
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
import tarfile
from glob import glob

#from local.base_config import PupilError, PupilsBase, sortkey
from core.base import Dates
from tables.spreadsheet import read_DataTable, filter_DataTable, \
        make_DataTable, make_DataTable_filetypes, TableError

class PupilError(Exception):
    pass

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


#TODO: Need a similar reader for importing pupil data. Maybe just a
# dict: pid -> PupilData (including CLASS field)

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
        config = MINION(DATAPATH("CONFIG/PUPIL_DATA"))
        self.all_fields = {}
        self.fields = {}
        for f in config["INFO_FIELDS"]:
            k = f["NAME"]
            if k == "CLASS":
                self.all_fields["CLASS"] = (
                    f.get("DISPLAY_NAME") or k,
                    bool(f.get("REQUIRED"))
                )
        for f in config["TABLE_FIELDS"]:
            k = f["NAME"]
            self.fields[k] = (
                f.get("DISPLAY_NAME") or k,
                bool(f.get("REQUIRED"))
            )
        self.all_fields.update(self.fields)
        # Each class has a table-file (substitute {klass}):
        self.class_path = DATAPATH(CONFIG["PUPIL_TABLE"])
        for fpath in glob(self.class_path.format(klass="*")):
            #print("READING", fpath)
            class_table = read_DataTable(fpath)
            try:
                class_table = filter_DataTable(class_table, config,
                        notranslate=True)
            except TableError as e:
                raise PupilError(_FILTER_ERROR.format(
                        msg = f"{e} in\n {fpath}"))

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
        This should only be necessary if names are changed, or if a pupil
        is added to a class.
        """
        if nosave:
            return sorted(self.__classes[klass], key=PupilData.sorting_name)
        self.__classes[klass].sort(key=PupilData.sorting_name)

    def save(self, klass):
        """Save the data for the pupils in the given class to the
        pupil-database.
        The first save of a day causes the current data (all classes) to
        be backed up.
        """
        timestamp = Dates.timestamp()
        today = timestamp.split('_', 1)[0]
        folder = os.path.dirname(self.class_path)
        buname = os.path.basename(folder)
        bufolder = os.path.join(folder, "backup")
        bufile = os.path.join(bufolder, f"{buname}_{today}.tar.gz")
        if not os.path.isfile(bufile):
            if not os.path.isdir(bufolder):
                os.mkdir(bufolder)
            tar = tarfile.open(bufile, "w:gz")
            for fpath in glob(self.class_path.format(klass="*")):
                tar.add(fpath, f"{buname}/{os.path.basename(fpath)}")
            tar.close()
#TODO: Remove older backups?
            print(f"BACKED UP @ {bufile}")
        self.save_data(
            klass,
            self.__classes[klass],
            self.class_path.format(klass=klass),
            SCHOOLYEAR,
            timestamp
        )

    def save_data(self, klass, pupil_list, filepath, schoolyear,
            timestamp=None):
        if not timestamp:
            timestamp = Dates.timestamp()
        data = {
            "__FIELDS__": list(self.fields),
            "__INFO__": {
                "__TITLE__": _TITLE,
                "SCHOOLYEAR": schoolyear,
                "CLASS": klass,
                "__MODIFIED__": timestamp
            },
            "__ROWS__": pupil_list
        }
        tsvbytes = make_DataTable(data, "tsv")
        with open(filepath, "wb") as fh:
            fh.write(tsvbytes)





    def compare_update(self, newdata):
        """Compare the new data with the existing data and compile a list
        of changes, grouped according to class. There are three types:
            - new pupil
            - pupil to remove (pupils shouldn't be removed within a
              school-year, just marked in EXIT_D, but this could be needed
              for patching or migrating to a new year)
            - field(s) changed.
        """
        class_delta = {}
        rest_pids = dict(self)  # remove processed pids from this set
        for pid, pdata in newdata.items():
            try:
                klass = pdata["CLASS"]
            except KeyError:
                raise PupilError(_CLASS_MISSING.format(name = pdata.name()))
            try:
                odata = rest_pids.pop(pid)
            except KeyError:
                # New pupil
                try:
                    class_delta[klass].append(('NEW', pdata))
                except KeyError:
                    class_delta[klass] = [('NEW', pdata)]
                continue
            # Compare data
            delta = self.compare(odata, pdata)
            if delta:
                # CLASS changes are registered in the new class.
#TODO: Should they also be registered in the old class?
                try:
                    class_delta[klass].append(('DELTA', odata, delta))
                except KeyError:
                    class_delta[klass] = [('DELTA', odata, delta)]
        # Add removed pupils to list
        for pid, pdata in rest_pids.items():
            klass = pdata["CLASS"]
            try:
                class_delta[klass].append(('REMOVE', pdata))
            except KeyError:
                class_delta[klass] = [('REMOVE', pdata)]
        return class_delta

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

    def update_classes(self, changes):
        """Apply the changes in the <changes> lists to the pupil data.
        The entries are basically those generated by <self.compare_update>,
        but it would be possible to insert a filtering step before
        calling this function.
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

    def fill_classes(self):
        """The pupils are allocated to classes and sorted within these.
        """
        self.__classes = {}
        for pid, pdata in self.items():
            klass = pdata["CLASS"]
            try:
                self.__classes[klass].append(pdata)
            except KeyError:
                self.__classes[klass] = [pdata]
        for klass in self.__classes:
            self.sort_class(klass)

    def remove_pupil(self, pid):
        pdata = self.pop(pid)
        klass = pdata["CLASS"]
        i = 0
        for pd in self.__classes[klass]:
            if pd["PID"] == pid:
                del(self.__classes[klass][i])
#TODO: if class now empty, remove it?
                break
            i += 1
        # Make changes persistent
        self.save()
        return True

    def modify_pupil(self, pupil_data_list):
        """This is used by the pupil-data editor. All changes to a pupil's
        data should pass through here.
        It ensures that the internal structures are consistent and that
        the changes get saved to persistent storage.
        By supplying a pupil-id which is not already in use, a new
        pupil can be added. If no pupil-id is supplied, a new value
        will be generated automatically.
        <pupil_data_list> is a list of pupil-data mappings.
        """
        for pdata in pupil_data_list:
            pid = pdata["PID"]
            if pid:
                if pid not in self:
                    # A new pupil ... check PID validity
                    if not check_pid_valid(pid):
                        REPORT("ERROR", _PID_INVALID.format(
                            name=pdata.name(), pid=pid))
                        return False
            else:
                pid = new_pid(self)
            # Check that essential fields are present
            missing = []
            for f, fdata in self.all_fields.items():
                if fdata[1]:    # an essential field
                    if not pdata.get(f):
                        missing.append(fdata[0])
            if missing:
                REPORT("ERROR", _MISSING_FIELDS.format(
                        fields = "\n  ".join(missing)))
                return False
            # Rebuild pupil entry
            self[pid] = {f: pupil_data.get(f) or "" for f in self.all_fields}
        # Regenerate class lists
        self.fill_classes()
        # Make changes persistent
        self.save()
        return True

    def migrate(self, repeat_pids = [], save_in = None):
        """Create a pupil-data structure for the following year.
        If <save_in> is provided, it should be a folder-path: the new
        pupil data will be saved here (as DataTables) instead of in the
        internal data area (subfolder "NEXT").
        If <repeat_pids> is provided it should be an iterable object
        listing pupil-ids for those who will definitely stay on, even
        if their class/group would suggest leaving. This is, of course,
        overridden by a leaving date! Their data (including class) will,
        be unchanged.
        """
        stay_pids = set(repeat_pids)
        nextyear = str(int(SCHOOLYEAR) + 1)
        day1 = Dates.day1(nextyear) # for filtering out pupils who have left
        newpupils = {}
        _class_path = DATAPATH(CONFIG["PUPIL_TABLE"], base="NEXT")
        # Filter out pupils from final classes, tweak pupil data
        for klass in self.classes():
            for _pdata in self.class_pupils(klass, date = day1):
                pdata = _pdata.copy()
                pid = pdata['PID']
                if pid in stay_pids:
                    new_klass = klass
                else:
                    # Progress to next class
                    new_klass = next_class(pdata)
                try:
                    newpupils[new_klass].append(pdata)
                except KeyError:
                    newpupils[new_klass] = [pdata]
        folder = os.path.dirname(_class_path)
        for dpath in glob(_class_path.format(klass="*")):
            os.remove(dpath)
        os.makedirs(folder, exist_ok=True)
        timestamp = Dates.timestamp()
        for klass, pdlist in newpupils.items():
            pdlist.sort(key=PupilData.sorting_name)
            self.save_data(
                klass,
                pdlist,
                _class_path.format(klass=klass),
                nextyear,
                timestamp
            )


#TODO: Custom functions ... where to put these?
def next_class(pdata):
    """Adjust the pupil data to the next class.
    Note that this is an "in-place" operation, so if the original data
    should remain unchanged, pass in a copy.
    """
    klass = pdata['CLASS']
    leaving_groups = CONFIG["LEAVING_GROUPS"].get(klass)
    if leaving_groups:
        if leaving_groups == "*":
            return "X"
        for g in pdata['GROUPS'].split():
            if g in leaving_groups:
                return "X"
    # Progress to next class ...
    k_year = class_year(klass)
    k_new = int(k_year) + 1
    k_suffix = klass[2:]
    klass = f"{k_new:02}{k_suffix}"
    # Handle entry into "Qualifikationsphase"
    if k_new == 12 and 'G' in pdata['GROUPS'].split():
        try:
            pdata['QUALI_D'] = CALENDAR['~NEXT_FIRST_DAY']
        except KeyError:
            pass
    return klass


def class_year(klass):
    """Get just the year part of a class name, as <str>, padded to
    2 digits.
    """
    try:
        k = int(klass[:2])
    except:
        k = int(klass[0])
    return f'{k:02}'


def new_pid(pupils):
    """Generate a new pid conforming to the requirements of
    function <check_pid_valid>.
    """
    # Base the new pid on today's date, adding a number to the end.
    today = Dates.today().replace("-", "")  # it must be an integer
    collect = []
    for pid in pupils:
        if pid.startswith(today):
            try:
                i = int(pid[8:])
            except ValueError:
                continue
            collect.append(i)
    if collect:
        collect.sort()
        i = str(collect[-1] + 1)
    else:
        i = "1"
    return today + i


def check_pid_valid(pid):
    """Check that the pid is of the correct form.
    """
    # Accept any integer.
    try:
        int(pid)
        return True
    except:
        return False


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

#    pupils.save("12G")

    pupils.migrate()

    print("\nNEW PID:", new_pid(pupils))

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
