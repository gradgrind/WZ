# -*- coding: utf-8 -*-

"""
local/base_config.py

Last updated:  2020-12-23

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

LINEBREAK = '¶'    # character used as paragraph separator in text cells


import os, glob

from local.grade_config import GradeBase

###

SCHOOLYEARS = 'SCHULJAHRE'

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
    FIELDS = {
        'SID'       : 'Fach-Kürzel',
        'SUBJECT'   : 'Fach',
        'TIDS'      : 'Lehrer-Kürzel',
        'FLAGS'     : 'Merkmale',
        'SGROUPS'   : 'Fachgruppe'
    }
#
    CLASS = 'Klasse'    # info-line
#
    # The path to the class tables. This must end with '_{klass}' for
    # determining the class.
    TABLE_NAME = 'Fachlisten/KLASSE_{klass}'
#
    def read_class_path(self, klass = None):
        """Return the path to the table for the class.
        If <klass> is not given, return the directory path.
        """
        if klass != None:
            xpath = self.TABLE_NAME.format(klass = klass)
        else:
            xpath = os.path.dirname(self.TABLE_NAME)
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
    TITLE = "Schülerliste"
    FIELDS = {
        'CLASS'     : 'Klasse',         # This must be the first field!
        'PID'       : 'ID',
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
#
    def group2pupils(self, group, date = None):
        """Return a list of pupil-data items for the pupils in the group.
        Only those groups relevant for grade reports are acceptable.
        A date may be supplied to filter out pupils who have left.
        """
        klass, streams = GradeBase._group2klass_streams(group)
        return self.class_pupils(klass, *streams, date = date)

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
