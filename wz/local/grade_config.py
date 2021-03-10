# -*- coding: utf-8 -*-

"""
local/grade_config.py

Last updated:  2021-03-10

Configuration for grade handling.

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
#? _BAD_GROUP_INFO = "Ungültige Zeile in grade_config.REPORT_GROUPS:\n  {line}"

_BAD_INFOTAG = "Ungültige Noten-Konfiguration für Gruppe {group}: {tag}"
_BAD_GROUP = "Ungültige Schülergruppe: {group}"
_BAD_TERM_REPORT = "Ungültige Noten-Konfiguration für Gruppe {group}:" \
        "Anlässe = ... {item}"
_BAD_ANLASS = "Ungültiger Anlass: {term}"
_BAD_TERM = "Ungültiger \"Anlass\" (Halbjahr): {term}"
_INVALID_GRADE = "Ungültige \"Note\": {grade}"
_BAD_XGRADE = "Ungültiges Konfigurationsfeld ({tag}) für Gruppe {grp}: {item}"
_BAD_RTEMPLATE = "Ungültige Zeugnisvorlage für Gruppe {grp}: {item}"
_NO_RTEMPLATE = "Keine Zeugnisvorlage '{template}' für Gruppe {grp}"

# Special "grades"
UNCHOSEN = '/'
NO_GRADE = '*'
MISSING_GRADE = '?'
NO_SUBJECT = '––––––––––'   # entry in grade report for excess subject slot
UNGRADED = "––––––"         # entry in grade report, where there is no grade

# GRADE field in CLASS_SUBJECTS table
NULL_COMPOSITE = '/'
NOT_GRADED = '-'

# Streams/levels
STREAMS = {
    'Gym': 'Gymnasium',
    'RS': 'Realschule',
    'HS': 'Hauptschule',
#TODO:
#    'FS': 'Förderschule',
#    'GS': 'Grundschule'
}

_TEMPLATE_PATH = 'Noten/{fname}'

_GRADE_GROUPS = 'GRADE_GROUPS'
_GRADE_TERMS = 'GRADE_TERMS'

# Grade table "info" items
GRADE_INFO_FIELDS = {
    'SCHOOLYEAR': 'Schuljahr',
    'GROUP': 'Klasse/Gruppe',
    'TERM': 'Anlass',
    'ISSUE_D': 'Ausgabedatum',      # or 'Ausstellungsdatum'?
    'GRADES_D': 'Notendatum'
}


class GradeConfigError(Exception):
    pass

###########################

def all_streams(klass):
    """Return a list of streams available in the given class.
    """
#TODO: Only some of the classes have been properly considered here ...
    try:
        c = int(klass)
        if c == 13:
            return ['Gym']
        if c >= 10:
            return ['Gym', 'RS', 'HS']  # 'HS' only for "Abgänger"
        elif c >= 5:
            return ['Gym', 'RS']
        else:
            return ['GS']
    except:
#TODO ...
        # Förderklasse?
        c = int(klass[:2])
        if c >= 5:
            return ['FS', 'HS']
        return ['FS']


### Grade handling
class GradeBase(dict):
    """The base class for grade handling. It provides information
    specific to the locality. A subclass handles the set of
    grades for a particular report for a pupil in a more general way.
    """
    _terms = None     # term/occasion (cached configuration structure)
    # This is read/written only by cls.terms().
    #
    @classmethod
    def terms(cls):
        """Return list of "terms" (grading "occasions").
        """
        if not cls._terms:
            cls._terms = MINION(os.path.join(DATA, _GRADE_TERMS))
        return list(cls._terms)
#
    GRADE_PATH = 'NOTEN_{term}/Noten_{group}' # grade table: file-name
    #
    REPORT_DIR = 'Notenzeugnisse_{term}' # grade report: folder
    REPORT_NAME = '{group}_{rtype}'      # grade report: file name
    #
    _PRINT_GRADE = {
        '1': "sehr gut",
        '2': "gut",
        '3': "befriedigend",
        '4': "ausreichend",
        '5': "mangelhaft",
        '6': "ungenügend",
        NO_GRADE: UNGRADED,
        'nt': "nicht teilgenommen",
        't': "teilgenommen",
#            'ne': "nicht erteilt",
        'nb': "kann nicht beurteilt werden",
    }
#
    @staticmethod
    def group_info(group, tag):
        if not cls._group_info:
            cls._group_info = MINION(os.path.join(DATA, _GRADE_GROUPS))
        try:
            ginfo = cls._group_info[group]
        except KeyError as e:
            raise GradeConfigError(_BAD_GROUP.format(group = group)) from e
        try:
            return ginfo[tag]
        except KeyError as e:
            raise GradeConfigError(_BAD_INFOTAG.format(group = group,
                    tag = tag)) from e
#
    @classmethod
    def table_path(cls, group, term, subselect):
        """Get file path for the grade table.
        <group> is the group being graded.
        <term> is the "reason" for the grade table (end-of-term, etc.).
        <subselect> can be a pupil-id, a tag or a date, depending on the
        category.
        """
        path = cls.GRADE_PATH.format(term = term, group = group)
        if subselect:
            return path + '_' + subselect
        return path
#
    @classmethod
    def report_name(cls, group, term, rtype):
        """Get file name for the grade report.
        """
        name = cls.REPORT_NAME.format(group = group, rtype = rtype)
        if term[0] in ('S', 'T'):
            return name + '_' + term[1:]
        return name
#
    @classmethod
    def _group2klass_streams(cls, group):
        """Return the class and a list of streams for the given
        pupil group. Only those groups relevant for grade reports are
        acceptable.
        Return a pair: (class, stream-list).
        For undivided classes, an empty stream-list is returned.
        To avoid leaking implementation internals for the groups, this
        method should only be used within this module.
        """
        return (group.split('.', 1)[0], cls.group_info(group, 'Maßstäbe'))
#
#DEPRECATED?
    @classmethod
    def stream_in_group(cls, klass, stream, grouptag):
        """Return <True> if the stream is in the group. <grouptag> is
        just the group part of a group name (e.g. R for 12.R).
        <grouptag> may also be '*', indicating the whole class (i.e.
        all streams).
        """
        raise Bug("Deprecated?")
        if grouptag == '*':
            return True
        try:
            return stream in cls._GROUP_STREAMS[klass][grouptag]
        except KeyError as e:
            raise GradeConfigError(_BAD_GROUP.format(
                    group = klass + '.' + grouptag)) from e
#
#DEPRECATED?
    @classmethod
    def klass_stream2group(cls, klass, stream):
        """This is needed because the grades in general, and in particular
        the templates, are dependant on the grade groups.
        Return the group containing the given stream.
        """
        raise Bug("Deprecated?")
        try:
            for g, streams in cls._GROUP_STREAMS[klass].items():
                if stream in streams:
                    return klass + '.' + g
        except KeyError:
            return klass
#
    def __init__(self, group, stream, term):
        super().__init__()
        self.i_grade = {}
        self.stream = stream
        self.sekII = self.group_info(group, 'Stufe') == 'SekII'
        self.valid_grades = self.group_info(group, 'NotenWerte')
        # Set default report type according to "term" and group
        self._extras_defaults = {}
        try:
            self._extras_defaults['*ZA'] = self.group_info(group,
                    f'*ZA/{term}')[0]
        except:
            pass
#
    def extras_default(self, sid, g):
        """Substitute default values for empty "extras".
        """
        if g:
            return g
        # Default values ...
        return self._extras_defaults.get(sid) or ''
#
    def grade_format(self, g):
        """Format the grade corresponding to the given numeric string.
        """
        return g.zfill(2) if self.sekII else g.zfill(1)
#
    def print_grade(self, grade):
        """Return the string representation of the grade which should
        appear in the report.
        If the grade is UNCHOSEN, return <None>.
        The SekII forms have no space for longer entries, but the
        special "grades" are retained for "Notenkonferenzen".
        """
        if grade:
            if grade == UNCHOSEN:
                return None
        else:
            return MISSING_GRADE
        try:
            if self.sekII:
                if grade in self.valid_grades:
                    try:
                        int(grade)
                        return grade
                    except:
                        return UNGRADED
            else:
                return self._PRINT_GRADE[grade.rstrip('+-')]
        except:
            pass
        raise GradeConfigError(_INVALID_GRADE.format(grade = repr(grade)))
#
    @classmethod
    def term2group_rtype_list(cls, term):
        """Return list of (group, default-report-type) pairs for valid
        groups in the given "term".
        """
        groups = []
        for group in GROUP_INFO:
            try:
                groups.append((group, cls.group_info(group, f'*ZA/{term}')))
            except GradeConfigError:
                continue
        return groups
#
    @classmethod
    def report_template(cls, group, rtype):
        """Return the template "path" for the grade reports.
        """
        for item in cls.group_info(group, 'NotenzeugnisVorlage'):
            try:
                k, v = item.split('/')
            except ValueError as e:
                raise GradeConfigError(_BAD_RTEMPLATE.format(
                        grp = group, item = item))
            if rtype == k:
                return _TEMPLATE_PATH.format(fname = v)
        raise GradeConfigError(_NO_RTEMPLATE.format(grp = group,
                template = rtype))
#
    @classmethod
    def xgradefields(cls, group, term):
        return cls.xfields('Notenfelder_X', group, term)
#
    @classmethod
    def calc_fields(cls, group, term):
        return cls.xfields('Calc', group, term)
#
    @classmethod
    def xfields(cls, tag, group, term):
        """Return a mapping of additional fields (qualification,
        report type, etc.) which are treated similarly to grades:
            {sid(tag) -> name}
        """
        xfmap = {}
        for nf in cls.group_info(group, tag):
            try:
                k, v = nf.split('/')
            except ValueError as e:
                raise GradeConfigError(_BAD_XGRADE.format(
                        tag = tag, grp = group, item = nf))
            try:
                if cls.group_info(group,  k + '/' + term[0]):
                    xfmap[k] = v
            except GradeConfigError:
                if cls.group_info(group,  k):
                    xfmap[k] = v
        return xfmap
#
    @staticmethod
    def double_sided(group, rtype):
        return rtype != 'Orientierung'
