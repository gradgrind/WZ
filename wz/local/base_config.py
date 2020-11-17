# -*- coding: utf-8 -*-

"""
local/base_config.py

Last updated:  2020-11-17

General configuration items.
============================
"""

SCHOOL_NAME = 'Freie Michaelschule'
FONT = 'Droid Sans'


DECIMAL_SEP = ','

# First month of school year (Jan -> 1, Dec -> 12):
SCHOOLYEAR_MONTH_1 = 8
# Format for printed dates (as used by <datetime.datetime.strftime>):
DATEFORMAT = '%d.%m.%Y'

CALENDAR_FILE = 'Kalender'

USE_XLSX = False


import os, glob

def year_path(schoolyear, fpath = None):
    """Return a path within the data folder for a school year.
    <fpath> is a '/' separated path relative to the year folder.
    """
    if fpath:
        return os.path.join(DATA, 'SCHULJAHRE', str(schoolyear),
                *fpath.split('/'))
    return os.path.join(DATA, 'SCHULJAHRE', str(schoolyear))

def print_schoolyear(schoolyear):
    """Convert a school-year (<int>) to the format used for output
    """
    return '%d – %d' % (schoolyear-1, schoolyear)

def class_year(klass):
    """Get just the year part of a class name.
    """
    try:
        return int(klass[:2])
    except:
        return int(klass[0])


class PupilsBase:
    TITLE = "Schülerliste"
    FIELDS = {
        'PID'       : 'ID',
#        'CLASS'     : 'Klasse',
        'PSORT'     : 'Sortiername',    # ! generated on record entry
        'FIRSTNAME' : 'Rufname',
        'LASTNAME'  : 'Name',
        'STREAM'    : 'Maßstab',        # probably not in imported data
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
    SCHOOLYEAR = 'Schuljahr'
    CLASS = 'Klasse'
    #
    # The path to the class tables. This must end with '_{klass}' for
    # determining the class in method <classes>.
    TABLE_NAME = 'Klassen/KLASSE_{year}_{klass}'
    #
    def classes(self):
        """Return a sorted list of class names.
        """
        files = glob.glob(year_path(self.schoolyear, self.TABLE_NAME.format(
                year = self.schoolyear, klass = '*')))
        return sorted([f.rsplit('_', 1)[-1].split('.', 1)[0]
                for f in files])
    #
    def read_class_path(self, klass = None):
        """Return the path to the table for the class.
        If <klass> is not given, return the directory path.
        """
        if klass != None:
            xpath = self.TABLE_NAME.format(
                    year = self.schoolyear, klass = klass)
        else:
            xpath = os.path.dirname(self.TABLE_NAME)
        return year_path(self.schoolyear, xpath)

###

# Ersatz-Zeichen für Dateinamen, die vom Programm erstellt werden, damit nur
# ASCII-Zeichen verwendet werden. Andere Nicht-ASCII-Zeichen werden durch
# '^' ersetzt.
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
    # Cyrillic (sieht wie das letzte Zeichen aus, ist aber anders!):
    'ё': 'e',
    'ñ': 'n'
}
