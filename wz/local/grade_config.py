# -*- coding: utf-8 -*-

"""
local/grade_config.py

Last updated:  2021-03-18

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
_BAD_INFOTAG = "Ungültige Konfiguration für Notegruppe {group}: {tag}"
_BAD_GROUP = "Ungültige Schülergruppe: {group}"
_BAD_TERMTAG = "Ungültige Konfiguration für Notenanlass {term}: {tag}"
_BAD_TERM = "Ungültige Notenanlass: {term}"
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

import os

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
    # This is read/written only by cls.term_info().
    _group_info = None  # information about groups (cache)
    # This is read/written only by cls._group_info().
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
    @classmethod
    def term_info(cls, term, tag = None):
        """Return an element from the "term" information configuration.
        If <term> is empty, return the list of "terms".
        Otherwise, fetch the information for the given "term". If <tag>
        is empty, return all the information (a mapping), otherwise
        return just the entry for the given tag (key).
        """
        if not cls._terms:
            cls._terms = MINION(os.path.join(DATA, _GRADE_TERMS))
        if term:
            try:
                tinfo = cls._terms[term]
            except KeyError as e:
                raise GradeConfigError(_BAD_TERM.format(term = term)) from e
        else:
            return list(cls._terms)
        if tag:
            try:
                return tinfo[tag]
            except KeyError as e:
                raise GradeConfigError(_BAD_TERMTAG.format(term = term,
                        tag = tag)) from e
        else:
            return tinfo
#
    @classmethod
    def group_info(cls, group, tag = None):
        """Return an element from the group information configuration.
        If <group> is empty, return the list of groups.
        Otherwise, fetch the information for the given group. If <tag>
        is empty, return all the information (a mapping), otherwise
        return just the entry for the given tag (key).
        There are default entries in the pseudogroup "__DEFAULT__".
        """
        if not cls._group_info:
            cls._group_info = MINION(os.path.join(DATA, _GRADE_GROUPS))
        if group:
            try:
                ginfo = cls._group_info[group]
            except KeyError as e:
                raise GradeConfigError(_BAD_GROUP.format(group = group)) from e
        else:
            return list(cls._group_info)
        if tag:
            try:
                return ginfo[tag]
            except KeyError as e:
                try:
                    return cls._group_info['__DEFAULT__'][tag]
                except KeyError as e:
                    raise GradeConfigError(_BAD_INFOTAG.format(
                            group = group, tag = tag)) from e
        else:
            return ginfo
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
#?
    @classmethod
    def term2group_rtype_list(cls, term):
        """Return list of (group, default-report-type) pairs for valid
        groups in the given "term".
        """
        groups = []
        for group in cls.group_info(None):
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
                k, v = item
            except ValueError as e:
                raise GradeConfigError(_BAD_RTEMPLATE.format(
                        grp = group, item = repr(item)))
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
            {sid(key) -> (name, value)}
        The "value" is the entry for the group and term in the
        group configuration.
        """
        xfmap = {}
        for nf in cls.group_info(group, tag):
            try:
                key, display = nf
            except ValueError as e:
                raise GradeConfigError(_BAD_XGRADE.format(
                        tag = tag, grp = group, item = repr(nf)))
            try:
                # First seek term-specific entry
                g2item = cls.group_info(group, '%s/%s' % (key, term))
            except GradeConfigError:
                # otherwise seek a default entry
                try:
                    g2item = cls.group_info(group, key)
                except GradeConfigError:
                    # No entry:
                    g2item = None
            if g2item:
                xfmap[key] = (display, g2item)
        return xfmap
#
    @staticmethod
    def double_sided(group, rtype):
        return rtype != 'Orientierung'
