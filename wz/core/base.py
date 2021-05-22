# -*- coding: utf-8 -*-
"""
core/base.py

Last updated:  2021-05-22

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
_MISSING_SCHOOLYEAR = "Schuljahr-Feld ('SCHOOLYEAR') fehlt im Kalender"
_BAD_DATE = "Ungültiges Datum im Kalender: {line}"
_INVALID_SCHOOLYEAR = "Ungültiges Schuljahr: {year}"
_DODGY_SCHOOLYEAR = "[?] Möglicherweise fehlerhaftes Schuljahr: {year}"
_BAD_CONFIG_LINE = "In Konfigurationsdatei {cfile}:\n  ungültige Zeile: {line}"
_DOUBLE_CONFIG_TAG = "In Konfigurationsdatei {cfile}:\n" \
        "  mehrfacher Eintrag: {tag} = ..."

import sys, os, re, builtins, datetime
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

class Bug(Exception):
    pass
builtins.Bug = Bug

from minion import Minion
__Minion = Minion()
builtins.MINION = __Minion.parse_file

NO_DATE = '*'   # an unspecified date

###

class DataError(Exception):
    pass

###

#TODO: Rather get <datadir> from "settings" (if datadir empty)?
# For a successful start there must be at least a legal calendar.
# Soon afterwards there would need to be pupil data and subject data.


class start:
    __WZDIR = None      # Base folder for WZ code and data/resources
    __DATA = None       # Base folder for school data
#
    @classmethod
    def setup(cls, datadir = None):
        appdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        cls.__WZDIR = os.path.join(os.path.dirname(appdir))
        builtins.WZPATH = cls.__wzdir
        if datadir:
            cls.__DATA = datadir
        else:
            cls.__DATA = os.path.join(cls.__WZDIR, 'TESTDATA')
        builtins.DATAPATH = cls.__datadir
        builtins.RESOURCEPATH = cls.__resourcedir
        builtins.CONFIG = MINION(DATAPATH('CONFIG'))
        builtins.SCHOOL_DATA = MINION(DATAPATH(CONFIG['SCHOOL_DATA']))
        builtins.NONE = ''
        cls.set_year()
#
    @classmethod
    def set_year(cls):
        builtins.CALENDAR = Dates.get_calendar(DATAPATH(
                CONFIG['CALENDAR_FILE']))
        builtins.SCHOOLYEAR = CALENDAR['SCHOOLYEAR']
#
    @classmethod
    def __wzdir(cls, path):
        """Return a path within the application base folder.
        <path> is a '/'-separated path relative to this folder.
        """
        return os.path.join(cls.__WZDIR, *path.split('/'))
#
    @classmethod
    def __datadir(cls, path):
        """Return a path within the school-data folder.
        <path> is a '/'-separated path relative to this folder.
        """
        return os.path.join(cls.__DATA, *path.split('/'))
#
    @classmethod
    def __resourcedir(cls, path):
        """Return a path within the resources folder.
        <path> is a '/'-separated path relative to this folder.
        """
        return os.path.join(cls.__DATA, 'RESOURCES', *path.split('/'))

###

def report(mtype, text):
    """The default reporting function prints to stdout.
    It can be overridden later.
    """
    print('%s: %s' % (mtype, text), flush = True)
builtins.REPORT = report

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
            return d.strftime(CONFIG['DATEFORMAT'])
        except:
            if trap:
                raise DataError("Ungültiges Datum: '%s'" % date)
        return None
#
#TODO: deprecated?
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
#
    @classmethod
    def today(cls, iso = True):
        try:
            # Allow "faking" the current date (at least in some respects ...).
            today = SCHOOL_DATA['TODAY']
        except KeyError:
            today = datetime.date.today().isoformat()
        return today if iso else cls.dateConv(today)
#
    @staticmethod
    def timestamp():
        """Return a "timestamp", accurate to the minute.
        It can be used for dating files, etc.
        """
        return datetime.datetime.now().isoformat(sep = '_',
                timespec = 'minutes')
#
    @staticmethod
    def day1(schoolyear):
        """Return the date of the first day of the school year.
        """
        m1 = int(CONFIG['SCHOOLYEAR_MONTH_1'])
        return '%s-%02d-01' % (schoolyear if m1 == 1
                else str(int(schoolyear) - 1), m1)
#
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
#
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
#
    @classmethod
    def save_calendar(cls, text, fpath = None):
        """Save the given text as a calendar file to the given path.
        If no path is supplied, save as the current calendar file.
        Some very minimal checks are made.
        """
        cls.check_calendar(__Minion.parse(text)) # check the school year
        header = CONFIG['CALENDER_HEADER'].format(date = cls.today())
        try:
            text = text.split('#---', 1)[1]
            text = text.lstrip('-')
            text = text.lstrip()
        except:
            pass
        text = header + text
        if not fpath:
            fpath = DATAPATH(CONFIG['CALENDAR_FILE'])
        os.makedirs(os.path.dirname(fpath), exist_ok = True)
        with open(fpath, 'w', encoding = 'utf-8') as fh:
            fh.write(text)
        return text
#
    @classmethod
    def get_calendar(cls, fpath):
        """Parse the given calendar file (full path):
        """
        cal = MINION(fpath)
        cls.check_calendar(cal)
        return cal
#
    @classmethod
    def check_calendar(cls, calendar):
        """Check the given calendar object.
        """
        try:
            schoolyear = calendar['SCHOOLYEAR']
        except KeyError:
            raise DataError(_MISSING_SCHOOLYEAR)
        # Check that the year is reasonable
        y0 = cls.today().split('-', 1)[0]
        try:
            y1 = int(schoolyear)
        except ValueError:
            raise DataError(_INVALID_SCHOOLYEAR.format(year = schoolyear))
        if schoolyear not in (y0, str(int(y0) + 1)):
            raise DataError(_DODGY_SCHOOLYEAR.format(year = schoolyear))
        for k, v in calendar.items():
            if isinstance(v, list):
                # range of days, check validity
                if k[0] == '~' or (cls.check_schoolyear(schoolyear, v[0])
                        and cls.check_schoolyear(schoolyear, v[1])):
                    continue
            else:
                # single day, check validity
                if k[0] == '~' or cls.check_schoolyear(schoolyear, v):
                    continue
            raise DataError(_BAD_DATE.format(line = '%s: %s' % (k, v)))
        return calendar
#
    @classmethod
    def migrate_calendar(cls):
        """Generate a "starter" calendar for the next schoolyear.
        It simply takes that from the current year and adds 1 to the
        year part of each date. Not much, but better than nothing?
        It of course still needs extensive editing.
        """
        def fn_sub(m):
            y = m.group(1)
            if y == lastyear:
                y = SCHOOLYEAR
            elif y == SCHOOLYEAR:
                y = nextyear
            return y
        fpath = DATAPATH(CONFIG['CALENDAR_FILE'])
        with open(fpath, 'r', encoding = 'utf-8') as fh:
            text = fh.read()
        lastyear = str(int(SCHOOLYEAR) - 1)
        nextyear = str(int(SCHOOLYEAR) + 1)
        rematch = r'([0-9]{4})'
        text = re.sub(rematch, fn_sub, text)
        return text


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    start.setup()
    print("Current school year:", Dates.get_schoolyear())
    print("DATE:", Dates.print_date('2016-04-25'))
    try:
        print("BAD Date:", Dates.print_date('2016-02-30'))
    except DataError as e:
        print(" ... trapped:", e)
    print("\n\nCalendar for 2017:\n", Dates.migrate_calendar())
