# -*- coding: utf-8 -*-

"""
local/base_config.py

Last updated:  2021-03-02

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

### External program (command to run, depends on system and platform):
import platform

if platform.system() == 'Windows':
    LIBREOFFICE = ''
else:
    LIBREOFFICE = 'libreoffice'
    #LIBREOFFICE = 'LibreOffice-fresh.standard.help-x86_64.AppImage'

#LUALATEX = 'lualatex'

#######################################################################

DECIMAL_SEP = ','

# First month of school year (Jan -> 1, Dec -> 12):
SCHOOLYEAR_MONTH_1 = 8
# Format for printed dates (as used by <datetime.datetime.strftime>):
DATEFORMAT = '%d.%m.%Y'
NO_DATE = '*'   # an unspecified date

CALENDAR_FILE = 'Kalender'

USE_XLSX = False

LINEBREAK = '§'    # character used as paragraph separator in text cells

CALENDER_HEADER = \
"""### Ferien und andere Jahresdaten
### Version: {date}
############################################################
# Diese Kopfzeilen sollten nicht geändert werden, das Datum
# wird beim Speichern automatisch aktualisiert.
#-----------------------------------------------------------

"""

import os, glob

from local.grade_config import GradeBase, all_streams

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
    FIELDS = {
        'SID'       : 'Fach-Kürzel',
        'SUBJECT'   : 'Fach',
        'TIDS'      : 'Lehrer-Kürzel',
        'FLAGS'     : 'Merkmale',
        'SGROUPS'   : 'Fachgruppe'
    }
#
    SCHOOLYEAR = 'Schuljahr'    # info-line
    CLASS = 'Klasse'            # info-line
#
    # The path to the course data for a school-year:
    COURSE_TABLE = 'Klassen/Kurse'
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
        'CLASS'     : 'Klasse',         # This must be the first field!
        'PID'       : 'ID',
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
    ESSENTIAL_FIELDS = 'CLASS', 'FIRSTNAMES', 'LASTNAME', 'FIRSTNAME', \
            'POB', 'DOB_D', 'SEX', 'ENTRY_D', 'HOME'
#
    SEX = ('m', 'w')    # Permissible values for a field
#
    SCHOOLYEAR = 'Schuljahr'
#
    # The path to the class (pupil) tables.
    CLASS_TABLE = 'Klassen/Schueler'
#
    def group2pupils(self, group, date = None):
        """Return a list of pupil-data items for the pupils in the group.
        Only those groups relevant for grade reports are acceptable.
        A date may be supplied to filter out pupils who have left.
        """
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
            'SEX': 'm'
        }
#
    @classmethod
    def year_step(cls, pdata):
        klass = pdata['CLASS']
        stream = pdata['STREAM']
        leavers = cls.leaving_groups(klass)
        if leavers == '*':
            return None
        if leavers and stream in leavers:
            return None
        # Progress to next class ...
        kyear = class_year(klass)
        knew = int(kyear) + 1
        ksuffix = klass[2:]
        klass = f'{knew:02}{ksuffix}'
        pd = pdata.copy()
        pd['CLASS'] = klass
        streams = all_streams(klass)
        if stream not in streams:
            pd['STREAM'] = streams[0]
        return pd
#
    @staticmethod
    def leaving_groups(klass):
        if klass > '12':
            return '*'
        if klass == '12':
            return ('RS', 'HS')
        return None

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
