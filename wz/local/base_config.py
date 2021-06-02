# -*- coding: utf-8 -*-

"""
local/base_config.py

Last updated:  2021-06-02

General configuration items.

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

import os, glob, builtins, re

#???
from local.grade_config import GradeBase

NONE = ''

class PupilError(Exception):
    pass

### -----

#TODO: deprecated? (now in calendar file for current year)
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

class SubjectsBase:
    TITLE = "Fachliste"
    CHOICE_TITLE = "Fächerwahl"
#
#TODO: to CONFIG?
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
#TODO: year_path ...
        return year_path(self.schoolyear, xpath)
#
    def group_subjects(self, group):
        klass, streams = GradeBase._group2klass_streams(group)
#TODO: filter on group? E.g. -G in FLAGS for "not in group G"?
# Would probably only apply to grade reports? (Because G/R are only
# used there?)
        return self.class_subjects(klass)

###

class PupilsBase:
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
    def next_class(cls, pdata):
        klass = pdata['CLASS']
        # Progress to next class ...
        kyear = class_year(klass)
        knew = int(kyear) + 1
        ksuffix = klass[2:]
        klass = f'{knew:02}{ksuffix}'
        pd = pdata.copy()
        pd['CLASS'] = klass
        # Handle entry into "Qualifikationsphase"
        if knew == 12 and 'G' in pd['GROUPS'].split():
            try:
                pd['QUALI_D'] = CALENDAR['~NEXT_FIRST_DAY']
            except KeyError:
                pass
        return pd
#
    @staticmethod
    def process_source_table(ptable):
        """Given a raw set of pupil-data from a table file, perform any
        processing necessary to transform it to the internal database
        form.
        In this version there is an analysis for "tussenvoegsel" and a
        re-splitting of name fields accordingly.
        """
        translate = {f: t or f
            for f, t, *x in SCHOOL_DATA['PUPIL_FIELDS']
        }
        nn = translate['FIRSTNAMES']
        n = translate['FIRSTNAME']
        l = translate['LASTNAME']
        if not ptable['__INFO__'].get('__KEEP_NAMES__'):
            for pdata in ptable['__ROWS__']:
                # "Renormalize" the name fields
                try:
                    firstnames = pdata[nn]
                    lastname = pdata[l]
                except KeyError:
                    raise PupilError(_NAME_MISSING.format(
                            row = repr(pdata)))
                pdata[nn], pdata[l], pdata[n] = tussenvoegsel_filter(
                        firstnames, lastname, pdata.get(n) or firstnames)


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
