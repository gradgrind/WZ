# -*- coding: utf-8 -*-
"""
core/base.py

Last updated:  2021-03-25

Basic configuration and structural stuff.

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
_BAD_DATE = "Ungültiges Datum im Kalender: {line}"
_INVALID_SCHOOLYEAR = "Ungültiges Schuljahr: {year}"
_BAD_CONFIG_LINE = "In Konfigurationsdatei {cfile}:\n  ungültige Zeile: {line}"
_DOUBLE_CONFIG_TAG = "In Konfigurationsdatei {cfile}:\n" \
        "  mehrfacher Eintrag: {tag} = ..."

# Configuration file
_SCHOOL_DATA = 'SCHOOL_DATA'

import sys, os, re, builtins, datetime
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

class Bug(Exception):
    pass
builtins.Bug = Bug

from minion import Minion
builtins.MINION = Minion().parse_file

from keyword import iskeyword
import local.base_config as CONFIG

###

class DataError(Exception):
    pass

def init(datadir = None):
    appdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    builtins.ZEUGSDIR = os.path.join(os.path.dirname (appdir))
    if not datadir:
        datadir = os.path.join(ZEUGSDIR, 'TESTDATA')
    builtins.DATA = datadir
    builtins.RESOURCES = os.path.join(DATA, 'RESOURCES')
    builtins.SCHOOL_DATA = MINION(os.path.join(DATA, _SCHOOL_DATA))


def report(mtype, text):
    """The default reporting function prints to stdout.
    It can be overridden later.
    """
    print('%s: %s' % (mtype, text), flush = True)
builtins.REPORT = report

#

def read_float(string):
    # Allow spaces (e.g. as thousands separator)
    inum = string.replace(' ', '')
    # Allow ',' as decimal separator
    return float(inum.replace (',', '.'))

#

def str2list(string, sep = ','):
    """Convert a string with separator character to a list.
    Accept also <None> as string input.
    """
    if string:
        return [s.strip() for s in string.split(sep)]
    return []

###

class Dates:
    @staticmethod
    def print_date(date, trap = True):
        """Convert a date string from the program format (e.g. "2016-12-06")
        to the format used for output (e.g. "06.12.2016").
        If an invalid date is passed, a <DataError> is raised, unless
        <trap> is false. In that case <None> – an invalid date – is returned.
        """
        try:
            d = datetime.datetime.strptime(date, "%Y-%m-%d")
            return d.strftime(CONFIG.DATEFORMAT)
        except:
            if trap:
                raise DataError("Ungültiges Datum: '%s'" % date)
        return None

    @classmethod
    def convert_dates(cls, mapping):
        """Convert all date values in the given mapping to the format
        used for output (see method <print_date>). The date values are
        those with keys ending '_D'.
        Return a list of the keys for failed conversions.
        """
        fails = []
        for key, val in mapping.items():
            if key.endswith('_D'):
                try:
                    mapping[key] = cls.print_date(val)
                except DataError:
                    fails.append(key)
        return fails

    @classmethod
    def today(cls, iso = True):
        try:
            # Allow "faking" the current date (at least in some respects ...).
            today = SCHOOL_DATA['TODAY']
        except KeyError:
            today = datetime.date.today().isoformat()
        return today if iso else cls.dateConv(today)

    @staticmethod
    def timestamp():
        """Return a "timestamp", accurate to the minute.
        It can be used for dating files, etc.
        """
        return datetime.datetime.now().isoformat(sep = '_',
                timespec = 'minutes')

    @staticmethod
    def day1(schoolyear):
        return '%s-%02d-01' % (schoolyear if CONFIG.SCHOOLYEAR_MONTH_1 == 1
                else str(int(schoolyear) - 1), CONFIG.SCHOOLYEAR_MONTH_1)

    @classmethod
    def check_schoolyear(cls, schoolyear, d = None):
        """Test whether the given date <d> lies within the schoolyear.
        Return true/false.
        If no date is supplied, return a tuple (first day, last day).
        """
        d1 = cls.day1(schoolyear)
        oneday = datetime.timedelta(days = 1)
        d2 = datetime.date.fromisoformat(cls.day1(str(int(schoolyear) + 1)))
        d2 -= oneday
        d2 = d2.isoformat()
        if d:
            if d < d1:
                return False
            return d <= d2
        return (d1, d2)

    @classmethod
    def get_schoolyear(cls, d = None):
        """Return the school-year containing the given date <d>.
        If no date is given, use "today".
        """
        if not d:
            d = cls.today()
        y = int(d.split('-', 1)[0])
        if d >= cls.day1(y + 1):
            return str(y + 1)
        return str(y)

    @classmethod
    def get_years(cls):
        """Return a list of the school-years ([<str>, ...]) for which
        there is data available, sorted with the latest first.
        No validity checks are made on the data, beyond checking that
        a calendar file exists for each year.
        """
        sypath = os.path.join(DATA, CONFIG.SCHOOLYEARS)
        years = []
        for d in os.listdir(sypath):
            try:
                y = int(d)
                if os.path.exists(os.path.join(sypath, d,
                        CONFIG.CALENDAR_FILE)):
                    years.append(d)
            except:
                pass
        return sorted(years, reverse=True)
#
    @staticmethod
    def read_calendar(schoolyear):
        fpath = CONFIG.year_path(schoolyear, CONFIG.CALENDAR_FILE)
        with open(fpath, 'r', encoding = 'utf-8') as fh:
            return fh.read()
#
    @classmethod
    def save_calendar(cls, schoolyear, text):
        header = CONFIG.CALENDER_HEADER.format(date = cls.today())
        try:
            text = text.split('#---', 1)[1]
            text = text.lstrip('-')
            text = text.lstrip()
        except:
            pass
        text = header + text
        fpath = CONFIG.year_path(schoolyear, CONFIG.CALENDAR_FILE)
        os.makedirs(os.path.dirname(fpath), exist_ok = True)
        with open(fpath, 'w', encoding = 'utf-8') as fh:
            fh.write(text)
        return text
#
    @classmethod
    def get_calendar(cls, schoolyear):
        """Read the calendar file for the given school year.
        """
        fpath = CONFIG.year_path(schoolyear, CONFIG.CALENDAR_FILE)
        rawdata = MINION(fpath)
        calendar = {}
        for k, v in rawdata.items():
            try:
                v1, v2 = v.split('/')
            except:
                # single day
                date = v.strip()
                # check validity
                if k[0] == '~' or cls.check_schoolyear(schoolyear, date):
                    calendar[k] = date
                    continue
            else:
                # range of days
                date1, date2 = v1.rstrip(), v2.lstrip()
                if k[0] == '~' or (cls.check_schoolyear(schoolyear, date1)
                        and cls.check_schoolyear(schoolyear, date2)):
                    calendar[k] = (date1, date2)
                    continue
            raise DataError(_BAD_DATE.format(line = '%s: %s' % (k, v)))
        return calendar
#
    @classmethod
    def migrate_calendar(cls, schoolyear):
        """Generate a "starter" calendar for the next schoolyear.
        It simply takes that from the current year and adds 1 to the
        year part of each date. Not much, but better than nothing?
        It of course still needs extensive editing.
        """
        def fn_sub(m):
            y, md = m.group(1), m.group(2)
            if y == lastyear:
                y = schoolyear
            elif y == schoolyear:
                y = nextyear
            return y + md
        text = cls.read_calendar(schoolyear)
        lastyear = str(int(schoolyear) - 1)
        nextyear = str(int(schoolyear) + 1)
        rematch = r'([0-9]{4})(-[0-9]{2}-[0-9]{2})'
        text = re.sub(rematch, fn_sub, text)
        cls.save_calendar(nextyear, text)
        return text

###

####### Name Sorting #######
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
#    sortname = sortingName(firstname1, tv, lastname1)
    if tv:
        lastname1 = tv + '|' + lastname1
    return (firstnames1, lastname1, firstname1)#, sortname)

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

def asciify(string, invalid_re = None):
    """This converts a utf-8 string to ASCII, e.g. to ensure portable
    filenames are used when creating files.
    Also spaces are replaced by underlines.
    Of course that means that the result might look quite different from
    the input string!
    A few explicit character conversions are given in the config module
    under 'ASCII_SUB'.
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

    lookup = CONFIG.ASCII_SUB
    return re.sub (invalid_re, rsub, string)


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    init()
    print(asciify("§Aö.#"))
    print("Current school year:", Dates.get_schoolyear())
    print("DATE:", Dates.print_date('2016-04-25'))
    try:
        print("BAD Date:", Dates.print_date('2016-02-30'))
    except DataError as e:
        print(" ... trapped:", e)
    print("\nCalendar for 2016:\n", Dates.get_calendar('2016'))

#    print("\n\nCalendar for 2017:\n", Dates.migrate_calendar('2016'))
