"""
core/pupils.py - last updated 2022-12-04

Manage pupil data.

=+LICENCE=================================
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
=-LICENCE=================================
"""

#TODO ... T ...

_TITLE = "Schülerdaten"

### Messages
_SCHOOLYEAR_MISMATCH_DB = "Schüler-Datenbank-Fehler: falsches Jahr in\n{path}"
_CLASS_MISMATCH_DB = "Schüler-Datenbank-Fehler: falsche Klasse in\n{path}"
_DOUBLE_PID_DB = (
    "Schüler-Datenbank-Fehler: Schüler-ID {pid} doppelt"
    " vorhanden, in Klassen {k1} und {k2}"
)
_CLASS_MISSING = "In importierten Daten: Klasse fehlt für {name}"
_FILTER_ERROR = "Schülerdaten-Fehler: {msg}"
_PID_INVALID = "Ungültige Schülerkennung für {name}: '{pid}'"
_MISSING_FIELDS = "Diese Felder dürfen nicht leer sein:\n  {fields}"
_INVALID_CLASS = (
    "Importierte Schülerdaten: Ungültige Klasse ({klass}),"
    " Zeile\n  {row}\n ... in\n {path}"
)

###############################################################

import sys, os

if __name__ == "__main__":
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))

T = TRANSLATIONS("core.pupils")

### +++++

from core.db_access import db_read_table, db_read_unique_entry, NoRecord
from core.base import class_group_split
from core.basic_data import SHARED_DATA

#? ...
import re
import tarfile
from glob import glob

from core.base import Dates
from local.local_pupils import (
    check_pid_valid,
    next_class,
    read_pupils_source
)

### -----

# TODO???: I suppose the program should start with the stored data? If there is
# none (or if it is dodgy) there can be a question dialog to load from
# file.
# What about updating from file, with update selections?

### **************************************************************** ###

def pupil_data(pid, allow_none=False):
    """Return a mapping of the pupil-data for the given pupil-id.
    IMPORTANT: This data is not cached.
    """
    try:
        flist, row = db_read_unique_entry("PUPILS", PID=pid)
    except NoRecord:
        if allow_none:
            return None
        REPORT("ERROR", T["UNKNOWN_PID"].format(pid=pid))
    return dict(zip(flist, row))


def get_pupil_fields():
    return {f[0]: f[1:] for f in CONFIG["PUPILS_FIELDS"]}


def get_pupils(klass):
    """Return a list of data mappings, one for each member of the given class.
    This data is cached, so subsequent calls get the same instance.
    """
    key = f"PUPILS_{klass}"
    try:
        return SHARED_DATA[key]
    except KeyError:
        pass
    field_list = get_pupil_fields()
    l = len(field_list)
    pupils = []
    for row in db_read_table(
        "PUPILS",
        field_list,
        sort_field="SORT_NAME",
        CLASS=klass,
    )[1]:
        pupils.append(dict(zip(field_list, row)))
    SHARED_DATA[key] = pupils
    return pupils


def pupils_in_group(class_group, date=None):
    """Read the pupil data for the given school-class (possibly with
    group specifier, e.g. "12G.A").
    Return a list of mappings {field -> value} (the table rows), the
    pupils being ordered alphabetically.
    If <date> is supplied, pupils who left the school before that
    date will not be included.
    """
    k, g = class_group_split(class_group)
    plist = get_pupils(k)
    if g:
        plist2 = []
        for pdata in plist:
            if g in pdata["GROUPS"].split():
                if date:
                    # Check exit date
                    if exd := pdata.get("EXIT_D"):
                        if exd < date:
                            continue
                plist2.append(pdata)
        return plist2
    else:
        return plist


def pupil_name(pupil_data):
    """Return the short-name of the pupil."""
    return f"{pupil_data['FIRSTNAME']} {pupil_data['LASTNAME']}"


def final_year_pupils():
    """Return lists of pupils in their final year:
    {class: [(pid, name), ... ], ...}
    """
    collect = {}
    for k_g in CONFIG["LEAVING_GROUPS"]:
        for pdata in pupils_in_group(k_g):
            k = pdata["CLASS"]
            item = (pdata["PID"], pupil_name(pdata))
            try:
                collect[k].append(item)
            except KeyError:
                collect[k] = [item]
    return collect


#########################################



class X:

#??
    def save(self, klass=None):
        """Save the data for the pupils in the given class to the
        pupil-database. If no class is supplied, save all classes.
        The first save of a day causes the current data (all classes) to
        be backed up.
        """
        timestamp = Dates.timestamp()
        today = timestamp.split("_", 1)[0]
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
            # TODO: Remove older backups?
            print(f"BACKED UP @ {bufile}")
        if klass:
            classes = [klass]
        else:
            classes = self.classes()
        for k in classes:
            self.save_data(
                k,
                self.__classes[k],
                self.class_path.format(klass=k),
                SCHOOLYEAR,
                timestamp,
            )




    def compare_update(newdata):
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
                raise PupilError(_CLASS_MISSING.format(name=pdata.name()))
            try:
                odata = rest_pids.pop(pid)
            except KeyError:
                # New pupil
                try:
                    class_delta[klass].append(("NEW", pdata))
                except KeyError:
                    class_delta[klass] = [("NEW", pdata)]
                continue
            # Compare data
            delta = self.compare(odata, pdata)
            if delta:
                # CLASS changes are registered in the new class.
                # TODO: Should they also be registered in the old class?
                try:
                    class_delta[klass].append(("DELTA", odata, delta))
                except KeyError:
                    class_delta[klass] = [("DELTA", odata, delta)]
        # Add removed pupils to list
        for pid, pdata in rest_pids.items():
            klass = pdata["CLASS"]
            try:
                class_delta[klass].append(("REMOVE", pdata))
            except KeyError:
                class_delta[klass] = [("REMOVE", pdata)]
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
                if d[0] == "NEW":
                    # Add to pupils
                    self[pdata["PID"]] = pdata
                elif d[0] == "REMOVE":
                    # Remove from pupils
                    del self[pdata["PID"]]
                elif d[0] == "DELTA":
                    # changes field values
                    self[pdata["PID"]].update(d[2])
                else:
                    raise Bug("Bad delta key: %s" % d[0])
        if count > 0:
            # Regenerate class lists
            self.fill_classes()
            # Make changes persistent
            self.save()

    def fill_classes(self):
        """The pupils are allocated to classes and sorted within these."""
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
                del self.__classes[klass][i]
                # TODO: if class now empty, remove it?
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
                        REPORT(
                            "ERROR",
                            _PID_INVALID.format(name=pdata.name(), pid=pid),
                        )
                        return False
            else:
                pid = new_pid(self)
            # Check that essential fields are present
            missing = []
            for f, fdata in self.all_fields.items():
                if fdata[1]:  # an essential field
                    if not pdata.get(f):
                        missing.append(fdata[0])
            if missing:
                REPORT(
                    "ERROR", _MISSING_FIELDS.format(fields="\n  ".join(missing))
                )
                return False
            # Rebuild pupil entry
            self[pid] = {f: pdata.get(f) or "" for f in self.all_fields}
        # Regenerate class lists
        self.fill_classes()
        # Make changes persistent
        self.save()
        return True

    def migrate(self, repeat_pids=[], save_in=None):
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
        day1 = Dates.day1(nextyear)  # for filtering out pupils who have left
        newpupils = {}
        _class_path = DATAPATH(CONFIG["PUPIL_TABLE"], base="NEXT")
        # Filter out pupils from final classes, tweak pupil data
        for klass in self.classes():
            for _pdata in self.class_pupils(klass, date=day1):
                pdata = _pdata.copy()
                pid = pdata["PID"]
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
                timestamp,
            )


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    from core.db_access import open_database
    open_database()

#TODO: switch to test data ...

    # get_pupils("11G")

    __k = "11G.R"
    print(f"\nPupils in {__k}:")
    for pdata in pupils_in_group(__k):
        print("  +++", pdata)
        pid = pdata["PID"]


    print("\nFinal-year pupils:")
    for k, pdata in final_year_pupils().items():
        print("  +++", k)
        for item in pdata:
            print("        ::", item)

    print(f"\nDATA FOR PID={pid}:")
    print(pupil_data(pid))

    quit(0)


    pupils_src = read_pupils_source(
        DATAPATH("MISC/pupils_from_access"),
    )

    for p in pupils_src:
        print(" +++", p)
    quit(0)

    # ************** Start new year from raw data **************#
    # TODO
    #    init(os.path.join(os.path.dirname(os.path.dirname(this)), 'DATA'))
    ##   year = '2021'
    #    pupils = PUPILS()

    # TODO: year_path ?
    #    _ptables = Pupils_File(_year, filepath = year_path(_year,
    #            'Quelldaten/PUPILS_2021.tsv'), norm_fields = False)
    #    _delta = pupils.compare_update(_ptables)
    #    for k, dlist in _delta.items():
    #        print("\n --- KLASSE:", k)
    #        for d in dlist:
    #            print("  ", d)
    #    pupils.update_classes(_delta)
    #    quit(0)
    # ----------------------------------------------------------#

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

    _delta = pupils.compare_update(pmap)
    for k, dlist in _delta.items():
        print("\n --- KLASSE:", k)
        for d in dlist:
            print("  ", d)

    #    pupils.update_classes(_delta)

#    pupils.migrate()

    print("\nNEW PID:", new_pid(pupils))

    quit(0)
    ### Make a trial migration to next school-year.
    ### This also makes a back-up of the current pupil data.
    pupils.migrate(
        repeat_pids=("200888", "200301"),
        save_as=DATAPATH(f"testing/tmp/PUPILS_NEXT_{SCHOOLYEAR}"),
    )

    _ptables = Pupil_File(
        DATAPATH("testing/delta_test_pupils_2016.ods"), extend=False
    )

    _delta = pupils.compare_update(_ptables)
    for k, dlist in _delta.items():
        print("\n --- KLASSE:", k)
        for d in dlist:
            print("  ", d)
    pupils.update_classes(_delta)

    ### Show the information for all pupils in a class
    _klass = "12"
    print("\n $$$", _klass)
    plist = pupils.class_pupils(_klass)
    for pdata in plist:
        print("\n :::", pdata)

    ### Show the information for a single pupil, keyed by pid
    _pid = "200502"
    _pdata = pupils[_pid]
    print("\n PUPIL %s (class %s)" % (_pdata["PID"], _pdata["CLASS"]))
    print("  ", _pdata)

    ### Update the pupil data with some changes from a new "master" table
    print("\n§§§ CHECK PUPILS UPDATE §§§")
    _ptables = Pupil_File(
        DATAPATH("testing/delta_test_pupils_2016.ods"), extend=False
    )
    _delta = pupils.compare_update(_ptables)
    for klass, changes in _delta.items():
        print("CLASS %s:" % klass)
        for c in changes:
            print("  $  ", c)
    pupils.update_classes(_delta)

    ### Revert the changes by "updating" from a saved table
    _ptables = Pupil_File(DATAPATH("testing/PUPILS_2016.tsv"))
    _delta = pupils.compare_update(_ptables)
    for k, dlist in _delta.items():
        print("\n --- KLASSE:", k)
        for d in dlist:
            print("  ", d)
    pupils.update_classes(_delta)
