# -*- coding: utf-8 -*-

"""
local/base_config.py

Last updated:  2021-05-21

General configuration items.

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
### Messages
_NAME_MISSING = "Eingabezeile fehlerhaft, Name unvollständig:\n  {row}"

### External program (command to run, depends on system and platform):
import platform

if platform.system() == 'Windows':
    raise NameError("Path to LibreOffice missing")
    LIBREOFFICE = ''
else:
    LIBREOFFICE = 'libreoffice'
    #LIBREOFFICE = 'LibreOffice-fresh.standard.help-x86_64.AppImage'

#######################################################################

DECIMAL_SEP = ','

# First month of school year (Jan -> 1, Dec -> 12):
SCHOOLYEAR_MONTH_1 = 8
# Format for printed dates (as used by <datetime.datetime.strftime>):
DATEFORMAT = '%d.%m.%Y'
NO_DATE = '*'   # an unspecified date

CALENDAR_FILE = 'Kalender'

USE_XLSX = False

CALENDER_HEADER = \
"""### Ferien und andere Jahresdaten
### Version: {date}
############################################################
# Diese Kopfzeilen sollten nicht geändert werden, das Datum
# wird beim Speichern automatisch aktualisiert.
#-----------------------------------------------------------

"""

import os, glob, builtins, re

#???
from local.grade_config import GradeBase

NONE = ''

### +++++

SCHOOLYEARS = 'Schuljahre'
SCHOOLYEAR = 'Schuljahr'
CLASS = 'Klasse'
GROUP = 'Gruppe'
GROUPS = 'Gruppen'

###

def year_path(schoolyear, fpath = None):
    """Return a path within the data folder for a school year.
    <fpath> is a '/' separated path relative to the year folder.
    """
    if fpath:
        return os.path.join(DATA, SCHOOLYEARS, schoolyear,
                *fpath.split('/'))
    return os.path.join(DATA, SCHOOLYEARS, schoolyear)

###

def print_schoolyear(schoolyear):
    """Convert a school-year (<str>) to the format used for output
    """
    return '%d – %s' % (int(schoolyear) - 1, schoolyear)

###

def print_class(klass):
    """Return the class name as used in text reports.
    """
    return klass.lstrip('0')

###

def class_year(klass):
    """Get just the year part of a class name, as <str>, padded to
    2 digits.
    """
    try:
        k = int(klass[:2])
    except:
        k = int(klass[0])
    return f'{k:02}'

###

def klass_group(group):
    """Split a group name (e.g. '11.G' into class ('11') and group tag ('G').
    If there is no '.' in the group name, this is assumed to be the class
    and the group is <NONE>.
    """
    try:
        klass, gtag = group.split('.')
    except ValueError:
        klass, gtag = group, NONE
    return klass, gtag

###

class SubjectsBase:
    TITLE = "Fachliste"
    CHOICE_TITLE = "Fächerwahl"
    FIELDS = {
        'SID'       : 'Fach-Kürzel',
        'SUBJECT'   : 'Fach',
        'TIDS'      : 'Lehrer-Kürzel',  # can be multiple, space-separated
        'GROUP'     : GROUP,
        'COMPOSITE' : 'Sammelfach',     # can be multiple, space-separated
        'SGROUP'    : 'Fachgruppe'
    }
#
    # The path to the course data for a school-year:
    COURSE_TABLE = 'Klassen/Kurse'
    # The path to the list of sid: name definitions:
    SUBJECT_NAMES = 'Fachliste'
#TODO: deprecated ...
#
    CHOICE_TEMPLATE = 'Fachwahl'
#
    def read_class_path(self, klass = None, choice = False):
        """Return the path to the table for the class.
        If <klass> is not given, return the directory path.
        If <choice> is true, return the path to the choice table.
        """
        table = self.CHOICE_NAME if choice else self.TABLE_NAME
        if klass != None:
            xpath = table.format(klass = klass)
        else:
            xpath = os.path.dirname(table)
        return year_path(self.schoolyear, xpath)
#
    def group_subjects(self, group):
        klass, streams = GradeBase._group2klass_streams(group)
#TODO: filter on group? E.g. -G in FLAGS for "not in group G"?
# Would probably only apply to grade reports? (Because G/R are only
# used there?)
        return self.class_subjects(klass)

###

class PupilsBase(dict):
    TITLE = "Schülerliste"
    FIELDS = {
        'CLASS'     : CLASS,         # This must be the first field!
        'PID'       : 'ID',
        'FIRSTNAME' : 'Rufname',
        'LASTNAME'  : 'Name',
        'GROUPS'    : GROUPS,        # probably not in imported data
        'FIRSTNAMES': 'Vornamen',
        'DOB_D'     : 'Geburtsdatum',
        'POB'       : 'Geburtsort',
        'SEX'       : 'Geschlecht',
        'HOME'      : 'Ort',
        'ENTRY_D'   : 'Eintrittsdatum',
        'EXIT_D'    : 'Schulaustritt',
        'QUALI_D'   : 'Eintritt-SekII'  # not in imported data
    }
#
    ESSENTIAL_FIELDS = 'CLASS', 'FIRSTNAMES', 'LASTNAME', 'FIRSTNAME', \
            'POB', 'DOB_D', 'SEX', 'ENTRY_D', 'HOME'
#
    SEX = ('m', 'w')    # Permissible values for a field
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
    def sorting_name(self, pid):
        return sortkey(self[pid])
#
#TODO: -> config file?
    # The path to the class (pupil) tables.
    CLASS_TABLE = 'Klassen/Schueler'
#
    def group2pupils(self, group, date = None):
        """Return a list of pupil-data items for the pupils in the group.


        Only those groups relevant for grade reports are acceptable.
        A date may be supplied to filter out pupils who have left.
        """
#TODO
        klass, streams = GradeBase._group2klass_streams(group)
        return self.class_pupils(klass, *streams, date = date)
#
    @staticmethod
    def check_new_pid_valid(pid):
        """Check that the pid is of the correct form.
        """
        try:
            int(pid)
            return
        except:
            _PID_INVALID = "Ungültige Schülerkennung: '{pid}'"
            raise ValueError(_PID_INVALID.format(pid = pid or ''))
#
    def nullPupilData(self, klass):
        """Return a "dummy" pupil-data instance, which can be used as a
        starting point for adding a new pupil.
        """
        return {
            'PID': str(int(sorted(self)[-1]) + 1),
            'CLASS': klass, 'FIRSTNAME': 'Hansi',
            'LASTNAME': 'von|Meierhausen', 'FIRSTNAMES': 'Hans Herbert',
            'SEX': 'm', 'DOB_D': '2010-04-01', 'POB': 'Münster',
            'ENTRY_D': '2016-11-11', 'HOME': 'Hannover'
        }
#
    @classmethod
    def year_step(cls, pdata, calendar):
        klass = pdata['CLASS']
        groups = set(pdata['GROUPS'].split())
        leavers = cls.leaving_groups(klass)
        if leavers:
            if leavers == '*':
                return None
            if groups & leavers:
                return None
        # Progress to next class ...
        kyear = class_year(klass)
        knew = int(kyear) + 1
        ksuffix = klass[2:]
        klass = f'{knew:02}{ksuffix}'
        pd = pdata.copy()
        pd['CLASS'] = klass
        # Handle entry into "Qualifikationsphase"
        if knew == 12 and 'G' in groups:
            try:
                pd['QUALI_D'] = calendar['~NEXT_FIRST_DAY']
            except KeyError:
                pass
        return pd
#
    @staticmethod
    def leaving_groups(klass):
        if klass > '12':
            return '*'
        if klass == '12':
            return {'R'}
        return None
#
    def _read_source_table(self, ptable, tweak_names):
        """Read a pupil-data list from ptable, containing only the pupil
        fields (in self.FIELDS) which are actually present in the file.
        If <tweak_names> is true, the names will be analysed for
        "tussenvoegsel" and re-split accordingly.
        """
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
        missing = []    # check that essential fields are present
        for f, t in self.FIELDS.items():
            try:
                field_index.append((f, colmap[t.upper()]))
            except KeyError:
                pass
        plist = []   # collect pupil data
        for row in ptable:
            pdata = {}
            plist.append(pdata)
            for f, i in field_index:
                pdata[f] = row[i] or ''
            if tweak_names:
                # "Renormalize" the name fields
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
        return plist


####### Name Handling #######
# In Dutch there is a word for those little lastname prefixes like "von",
# "zu", "van" "de": "tussenvoegsel". For sorting purposes these can be a
# bit annoying because they are often ignored, e.g. "van Gogh" would be
# sorted under "G".

def tussenvoegsel_filter(firstnames, lastname, firstname):
    """Given raw firstnames, lastname and short firstname,
    ensure that any "tussenvoegsel" is at the beginning of the lastname
    (and not at the end of the first name) and that spaces are normalized.
    If there is a "tussenvoegsel", it is separated from the rest of the
    lastname by '|' (without spaces). This makes it easier for a sorting
    algorithm to remove the prefix to generate a sorting key.
    """
    # If there is a '|' in the lastname, replace it by ' '
    firstnames1, tv, lastname1 = tvSplit(firstnames,
            lastname.replace('|', ' '))
    firstname1 = tvSplit(firstname, 'X')[0]
    if tv:
        lastname1 = tv + '|' + lastname1
    return (firstnames1, lastname1, firstname1)

###

def tvSplit(fnames, lname):
    """Split off a "tussenvoegsel" from the end of the first-names,
    <fnames>, or the start of the surname, <lname>.
    These little name parts are identified by having a lower-case
    first character.
    Also ensure normalized spacing between names.
    Return a tuple: (
            first names without tussenvoegsel,
            tussenvoegsel or <None>,
            lastname without tussenvoegsel
        ).
    """
#TODO: Is the identification based on starting with a lower-case
# character adequate?
    fn = []
    tv = fnames.split()
    while tv[0][0].isupper():
        fn.append(tv.pop(0))
        if not len(tv):
            break
    if not fn:
        raise ValueError(_BADNAME.format(name = fnames + ' / ' + lname))
    ln = lname.split()
    while ln[0].islower():
        if len(ln) == 1:
            break
        tv.append(ln.pop(0))
    return (' '.join(fn), ' '.join(tv) or None, ' '.join(ln))

###

def sortkey(pdata):
    _lastname = pdata['LASTNAME']
    try:
        tv, lastname = _lastname.split('|', 1)
    except ValueError:
        tv, lastname = None, _lastname
    return sortingName(pdata['FIRSTNAME'], tv, lastname)

###

def sortingName(firstname, tv, lastname):
    """Given first name, "tussenvoegsel" and last name, produce an ascii
    string which can be used for sorting the people alphabetically.
    """
    if tv:
        sortname = lastname + ' ' + tv + ' ' + firstname
    else:
        sortname = lastname + ' ' + firstname
    return asciify(sortname)

###

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
            return lookup [c]
        except:
            return '^'

    lookup = ASCII_SUB
    return re.sub (invalid_re, rsub, string)

###

# Substitute characters used to convert utf-8 strings to ASCII, e.g. for
# portable filenames, Dateinamen. Non-ASCII characters which don't have
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
