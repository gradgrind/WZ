# -*- coding: utf-8 -*-

"""
local/grade_config.py

Last updated:  2020-12-03

Configuration for grade handling.
====================================
"""

### Messages
_BAD_GROUP_INFO = "Ungültige Zeile in grade_config.REPORT_GROUPS:\n  {line}"
_BAD_INFOTAG = "Ungültige Noten-Konfiguration für Gruppe {group}: {tag}"
_BAD_GROUP = "Ungültige Schülergruppe: {group}"
_BAD_TERM_REPORT = "Ungültige Noten-Konfiguration für Gruppe {group}:" \
        "Anlässe = ... {item}"
_BAD_ANLASS = "Ungültiger Anlass: {term}"
_BAD_TERM = "Ungültiger \"Anlass\" (Halbjahr): {term}"
_INVALID_GRADE = "Ungültige \"Note\": {grade}"
_BAD_XGRADE = "Ungültiges Zusatz-Notenfeld für Gruppe {grp}: {item}"
_BAD_AVERAGE = "Ungültiges Durchschnittsfeld für Gruppe {grp}: {item}"

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

###########################
_NORMAL_GRADES = f"""1+ ; 1 ; 1- ;  +
    2+ ; 2 ; 2- ; 3+ ; 3 ; 3- ; +
    4+ ; 4 ; 4- ; 5+ ; 5 ; 5- ; 6 ; +
    * ; nt ; t ; nb ; {UNCHOSEN}
"""

# *: ("no grade" ->) "––––––"
# nt: "nicht teilgenommen"
# t: "teilgenommen"
# nb: "kann nich beurteilt werden"
## ne: "nicht erteilt"
# <UNCHOSEN>: Subject not included in report

_ABITUR_GRADES = f"""15 ; 14 ; 13 ;  +
    12 ; 11 ; 10 ; 09 ; 08 ; 07 ; +
    06 ; 05 ; 04 ; 03 ; 02 ; 01 ; 00 ; +
    * ; nt ; t ; nb ; {UNCHOSEN}
"""

# Eine Sammlung der Daten für die Zeugnisgruppen.
# Nur für die hier eingetragenen Gruppen können Notenzeugnisse erstellt
# werden.
#TODO: Auch Zwischenzeugnisse hier durch 'Zeugnis' vertreten?
# Für Listen ist das Trennzeichen ';'. Auch wenn eine Liste keine oder
# nur einen Wert hat, muss das Trennzeichen vorhanden sein (am Ende in
# diesem Fall).
REPORT_GROUPS = f"""
# ************** Voreinstellungen ("defaults") **************
    Stufe = SekI
######## (grade table template):
    NotentabelleVorlage = Noten/Noteneingabe
######## ("streams" contained in "group"):
######## leer => keine Untergruppen in dieser Klasse/Gruppe:
    Maßstäbe = ;
######## ("term", etc. – scheduled reports: <term>/<default report type>)
######## <Anlass>/<Zeugnis-Art-Voreinstellung>; ...
    Anlässe = ;
######## (extra "grade" fields in internal table):
######## Zusätzliche "Notenfelder" in interner Notentabelle
    Notenfelder_X = *ZA/Zeugnis (Art);
######## Durchschnitte für Notenkonferenz:
    Durchschnitte = ;
######## (additional report types):
######## Zusätzliche Zeugnis-Arten, die für diese Gruppe gewählt werden
######## können
    ZeugnisArt_X = Abgang; Zeugnis
######## gültige "Noten":
    NotenWerte = {_NORMAL_GRADES}

# Gruppe '13':
:13
    Stufe = SekII
    NotentabelleVorlage = Noten/Noteneingabe-Abitur
######## (term '2': grades collected, but no report cards)
######## Für das 2. Halbjahr werden Noten gegeben, aber keine
######## Notenzeugnisse erstellt:
    Anlässe = 1/Zeugnis; 2/; A/Abitur
######## (The report type is determined by calculations):
    Notenfelder_X = *ZA/Zeugnis (Art); *F_D/Fertigstellung
    ZeugnisArt_X = Abgang;
    NotenWerte = {_ABITUR_GRADES}

:12.G
    Stufe = SekII
    NotentabelleVorlage = Noten/Noteneingabe-SII
    Maßstäbe = Gym;
    Anlässe = 1/Zeugnis; 2/Zeugnis
    Notenfelder_X = *ZA/Zeugnis (Art); *Q/Qualifikation
    ZeugnisArt_X = Abgang;
    NotenWerte = {_ABITUR_GRADES}

:12.R
    Maßstäbe = RS; HS
    Anlässe = 1/Zeugnis; 2/Abschluss
    Notenfelder_X = *ZA/Zeugnis (Art); *Q/Qualifikation
    Durchschnitte = :D/Φ Alle Fächer; :Dx/Φ De-En-Ma

:11.G
    Maßstäbe = Gym;
    Anlässe = 1/Orientierung; 2/Zeugnis
    Notenfelder_X = *ZA/Zeugnis (Art); *Q/Qualifikation
    ZeugnisArt_X = Abgang; Zeugnis
    Durchschnitte = :D/Φ Alle Fächer;

:11.R
    Maßstäbe = RS; HS
    Anlässe = 1/Orientierung; 2/Abschluss
    Notenfelder_X = *ZA/Zeugnis (Art); *Q/Qualifikation
    ZeugnisArt_X = Abgang; Zeugnis
    Durchschnitte = :D/Φ Alle Fächer; :Dx/Φ De-En-Ma

:10
    Anlässe = 2/Orientierung;

# Gruppen '09', '08', ... (benutzen die Voreinstellungen)
:09 08 07 06 05
"""

GROUP_INFO = {}
default = {}
info = default
continuation = None
for line in REPORT_GROUPS.splitlines():
    line = line.strip()
    if (not line) or line[0] == '#':
        continue
    if continuation:
        line = continuation + line
        continuation = None
    if line[0] == ':':
        # A new group, or new groups: start from the default values.
        # A shallow copy is adequate here:
        info = default.copy()
        for g in line[1:].split():
            GROUP_INFO[g] = info
        continue
    if line[-1] == '+':
        continuation = line[:-1]
        continue
    try:
        tag, val = line.split('=')
    except ValueError as e:
        raise GradeConfigError(_BAD_GROUP_INFO.format(line = line)) from e
    _vals = val.split(';')
    if len(_vals) > 1:
        vals = []
        for v in _vals:
            v = v.strip()
            if v:
                vals.append(v)
    else:
        vals = val.strip()
    info[tag.strip()] = vals
###########################

## Localized field names.
## This also determines the fields for the GRADES table.
#GRADES_FIELDS = {
#    'PID'       : 'ID',
#    'CLASS'     : 'Klasse',
#    'STREAM'    : 'Maßstab',    # Grading level, etc.
#    'TERM'      : 'Anlass',     # Term/Category
#    'GRADES'    : 'Noten',
#    'REPORT_TYPE': 'Zeugnistyp',
#    'ISSUE_D'   : 'Ausstellungsdatum',
#    'GRADES_D'  : 'Notenkonferenz',
#    'QUALI'     : 'Qualifikation',
#    'COMMENT'   : 'Bemerkungen'
#}


class GradeConfigError(Exception):
    pass

#class GradeError(Exception):
#    pass

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
            return ['HS', 'FS']
        return ['GS']


### Grade handling
class GradeBase(dict):
    """The base class for grade handling. It provides information
    specific to the locality. A subclass handles the set of
    grades for a particular report for a pupil in a more general way.
    """
    _ANLASS = (
        # term/category-tag, text version
        ('1', '1. Halbjahr'),
        ('2', '2. Halbjahr'),
        ('A', 'Abitur'),
        ('S*', 'Sonderzeugnisse')
    )
    #
    GRADE_PATH = 'NOTEN_{term}/Noten_{group}_{term}'  # grade table: file-name
    #
    _PRINT_GRADE = {
        '1': "sehr gut",
        '2': "gut",
        '3': "befriedigend",
        '4': "ausreichend",
        '5': "mangelhaft",
        '6': "ungenügend",
        '*': UNGRADED,
        'nt': "nicht teilgenommen",
        't': "teilgenommen",
#            'ne': "nicht erteilt",
        'nb': "kann nicht beurteilt werden",
    }
#
    @staticmethod
    def group_info(group, tag):
        try:
            ginfo = GROUP_INFO[group]
        except KeyError as e:
            raise GradeConfigError(_BAD_GROUP.format(group = group)) from e
        try:
            return ginfo[tag]
        except KeyError as e:
            raise GradeConfigError(_BAD_INFOTAG.format(group = group,
                    tag = tag)) from e
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
    def __init__(self, group, stream):
        super().__init__()
        self.i_grade = {}
        self.stream = stream
        self.sekII = self.group_info(group, 'Stufe') == 'SekII'
        self.valid_grades = self.group_info(group, 'NotenWerte')
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
        The SekII forms have no space for longer remarks, but the
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
    def terms(cls):
        """Return list of tuples: (term tag, term name).
        """
        return [(cat[0], cat[1]) for cat in cls._ANLASS]
#
    @classmethod
    def term2text(cls, term):
        """For grade tables, produce readable "term" entries.
        """
        for t, text in cls.terms():
            if term == t:
                return text
        if term[0] == 'S':
            return term
        raise Bug("INVALID term: %s" % term)
#
    @classmethod
    def text2term(cls, text):
        """For grade tables, convert the readable "term" entries to
        the corresponding tag.
        """
        for term, txt in cls.terms():
            if text == txt:
                return term
        if text[0] == 'S':
            return text
        raise Bug("INVALID term text: %s" % text)
#
    @classmethod
    def term2group_rtype_list(cls, term):
        """Return list of (group, default-report-type) pairs for valid
        groups in the given term.
        """
        groups = []
        for group, data in GROUP_INFO.items():
            for item in cls.group_info(group, 'Anlässe'):
                try:
                    t, report_type = item.split('/')
                except ValueError as e:
                    raise GradeConfigError(_BAD_TERM_REPORT.format(
                            group = group, item = item)) from e
                if t == term:
                    groups.append((group, report_type))
        return groups
#
    @classmethod
    def xgradefields(cls, group):
        """Return a mapping of additional fields (qualification,
        report type, etc.) which are treated similarly to grades:
            {sid(tag) -> name}
        """
        xfmap = {}
        for nf in cls.group_info(group,  'Notenfelder_X'):
            try:
                k, v = nf.split('/')
            except ValueError as e:
                raise GradeConfigError(_BAD_XGRADE.format(
                        grp = group, item = nf))
            xfmap[k] = v
        return xfmap
#
    @classmethod
    def averages(cls, group):
        amap = {}
        for a in cls.group_info(group,  'Durchschnitte'):
            try:
                k, v = a.split('/')
            except ValueError as e:
                raise GradeConfigError(_BAD_AVERAGE.format(
                        grp = group, item = a))
            amap[k] = v
        return amap

#TODO
    @staticmethod
    def special_term(termGrade):
        raise Bug("TODO")
        if termGrade.term != 'A':
            raise GradeConfigError(_BAD_TERM.format(term = term))
        # Add additional oral exam grades
        slist = []
        termGrade.sdata_list
        for sdata in termGrade.sdata_list:
            slist.append(sdata)
            if sdata.sid.endswith('.e') or sdata.sid.endswith('.g'):
                slist.append(sdata._replace(
                        sid = sdata.sid[:-1] + 'x',
# <tids> must have a value, otherwise it will not be passed by the
# composites filter, but is this alright? (rather ['X']?)
                        tids = 'X',
                        composite = None,
                        report_groups = None,
                        name = sdata.name.split('|', 1)[0] + '| nach'
                    )
                )
        termGrade.sdata_list = slist
