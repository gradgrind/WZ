# -*- coding: utf-8 -*-
"""
core/base.py

Last updated:  2020-12-01

Basic configuration and structural stuff.

=+LICENCE=================================
Copyright 2020 Michael Towers

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
_BAD_CALENDAR_LINE = "Ungültige Zeile im Kalender: {line}"
_DOUBLE_DATE_TAG = "Mehrfacher Kalendereintrag: {tag} = ..."

_CALENDAR = 'Kalender'  # Calendar file (in year folder)

import sys, os, re, builtins, datetime
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

class Bug(Exception):
    pass
builtins.Bug = Bug

import local.base_config as CONFIG

#

def init(datadir = 'DATA'):
    appdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    builtins.ZEUGSDIR = os.path.join(os.path.dirname (appdir))
    builtins.DATA = os.path.join(ZEUGSDIR, datadir)
    builtins.RESOURCES = os.path.join(DATA, 'RESOURCES')


def report(text):
    """The default reporting function prints to stdout.
    It can be overridden later.
    """
    print(text)
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

class DateError(Exception):
    pass
class Dates:
    @staticmethod
    def print_date(date, trap = True):
        """Convert a date string from the program format (e.g. "2016-12-06")
        to the format used for output (e.g. "06.12.2016").
        If an invalid date is passed, a <DateError> is raised, unless
        <trap> is false. In that case <None> – an invalid date – is returned.
        """
        try:
            d = datetime.datetime.strptime(date, "%Y-%m-%d")
            return d.strftime(CONFIG.DATEFORMAT)
        except:
            if trap:
                raise DateError("Ungültiges Datum: '%s'" % date)
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
                except DateError:
                    fails.append(key)
        return fails

    @classmethod
    def today(cls, iso = True):
        today = datetime.date.today().isoformat()
        return today if iso else cls.dateConv(today)

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
                if os.path.exists(os.path.join(sypath, d, _CALENDAR)):
                    years.append(d)
            except:
                pass
        return sorted(years, reverse=True)

    @classmethod
    def get_calendar(cls, schoolyear):
        """Read the calendar file for the given school year.
        """
        fpath = CONFIG.year_path(schoolyear, CONFIG.CALENDAR_FILE)
        calendar = {}
        with open(fpath, encoding = 'utf-8') as fi:
            for l in fi:
                line = l.strip()
                if (not line) or line[0] == '#':
                    continue
                try:
                    k, v = line.split('=')
                except ValueError as e:
                    raise DateError(_BAD_CALENDAR_LINE.format(
                            line = l)) from e
                k = k.strip()
                if not k:
                    raise DateError(_BAD_CALENDAR_LINE.format(line = l))
                if k in calendar:
                    raise DateError(_DOUBLE_DATE_TAG.format(tag = k))
                try:
                    v1, v2 = v.split(':')
                except:
                    # single day
                    date = v.strip()
                    # check validity
                    if cls.check_schoolyear(schoolyear, date):
                        calendar[k] = date
                        continue
                else:
                    # range of days
                    date1, date2 = v1.strip(), v2.strip()
                    if (cls.check_schoolyear(schoolyear, date1)
                            and cls.check_schoolyear(schoolyear, date2)):
                        calendar[k] = (date1, date2)
                        continue
                raise DateError(_BAD_DATE.format(line = l))
        return calendar

###

####### Name Sorting #######
# In Dutch there is a word for those little lastname prefixes like "von",
# "zu", "van" "de": "tussenvoegsel". For sorting purposes these can be a
# bit annoying because they are often ignored, e.g. "van Gogh" would be
# sorted under "G".

def name_filter(firstnames, lastname, firstname):
    """Given raw firstnames, lastname and short firstname.
    Ensure that any "tussenvoegsel" is at the beginning of the lastname
    (and not at the end of the first name) and that spaces are normalized.
    Also generate a "sorting" name, a field which combines name components
    to sort the entries alphabetically in a fairly consistent way,
    considering "tussenvoegsel".
    """
    firstnames1, tv, lastname1 = tvSplit(firstnames, lastname)
    firstname1 = tvSplit(firstname, 'X')[0]
    sortname = sortingName(firstname1, tv, lastname1)
    if tv:
        lastname1 = tv + ' ' + lastname1
    return (firstnames1, lastname1, firstname1, sortname)

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
    Also ensure normalized spacing between names.
    Return a tuple: (
            first names without tussenvoegsel,
            tussenvoegsel or <None>,
            lastname without tussenvoegsel
        ).
    """
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

def asciify(string):
    """This converts a utf-8 string to ASCII, e.g. to ensure portable
    filenames are used when creating files.
    Also spaces are replaced by underlines.
    Of course that means that the result might look quite different from
    the input string!
    A few explicit character conversions are given in the config file
    'ASCII_SUB'.
    """
    # regex for characters which should be substituted:
    _invalid_re = r'[^A-Za-z0-9_.~-]'
    def rsub (m):
        c = m.group (0)
        if c == ' ':
            return '_'
        try:
            return lookup [c]
        except:
            return '^'

    lookup = CONFIG.ASCII_SUB
    return re.sub (_invalid_re, rsub, string)





if __name__ == '__main__':
    init('TESTDATA')
    print("Current school year:", Dates.get_schoolyear())
    print("DATE:", Dates.print_date('2016-04-25'))
    try:
        print("BAD Date:", Dates.print_date('2016-02-30'))
    except DateError as e:
        print(" ... trapped:", e)
    print("\nCalendar for 2016:\n", Dates.get_calendar(2016))
