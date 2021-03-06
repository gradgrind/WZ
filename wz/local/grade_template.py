# -*- coding: utf-8 -*-

"""
local/grade_template.py

Last updated:  2021-03-29

Manage template-specific fields for grade reports.


=+LICENCE=============================
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

=-LICENCE========================================
"""

### Messages
_INVALID_RTYPE = "Ungültiger Zeugnistyp: '{rtype}'"
_INVALID_QUALI = "Ungültiges Qualifikationsfeld für Schüler {pid}: '{quali}'"

from core.base import Dates
from local.grade_config import GradeConfigError, STREAMS, GradeBase

VERSETZUNG_11_12 = "Durch Konferenzbeschluss vom {grades_d} in die" \
                        " Qualifikationsphase versetzt."
VERSETZUNG_12_13 = "Durch Konferenzbeschluss vom {grades_d} in die" \
                        " 13. Klasse versetzt."
QP12_TEXT = "hat den 12. Jahrgang der Qualifikationsphase vom {vom}" \
        " bis zum {bis} besucht."
GS_TEXT = {
    'HS': "Dieses Zeugnis ist dem Sekundarabschluss I – Hauptschulabschluss" \
            " gleichgestellt. Es vermittelt die gleiche Berechtigung wie" \
            " das Zeugnis über den Sekundarabschluss I – Hauptschulabschluss.",
    'RS': "Dieses Zeugnis ist dem Sekundarabschluss I – Realschulabschluss" \
            " gleichgestellt. Es vermittelt die gleiche Berechtigung wie" \
            " das Zeugnis über den Sekundarabschluss I – Realschulabschluss.",
    'Erw': "Dieses Zeugnis ist dem Erweiterten Sekundarabschluss I" \
            " gleichgestellt. Es vermittelt die gleiche Berechtigung wie" \
            " das Zeugnis über den Erweiterten Sekundarabschluss I."
}
SEKI_TEXT = {
    'HS': "Sekundarabschluss I – Hauptschulabschluss",
    'RS': "Sekundarabschluss I – Realschulabschluss",
    'Erw': "Erweiterter Sekundarabschluss I"
}

_NOCOMMENT = '––––––––––'


def info_extend(grade_map):
    def set_field(field):
        """If there is a configuration value for the given field, set it.
        Return the "tag", if there is a "tag/" prefix, otherwise the value.
        """
        try:
            val = GradeBase.term_info(term, field)
        except GradeConfigError:
            return None
        try:
            tag, val = val.split('/', 1)
        except ValueError:
            tag = val
        grade_map[field] = val
        return tag
    #
    term = grade_map['TERM']
    HJ = set_field('HJ')
    stream = grade_map['STREAM']
    grade_map['LEVEL'] = STREAMS[stream] # Only relevant for SekI
    rtype = grade_map['REPORT_TYPE']
    if rtype == 'Zeugnis':
        if grade_map['SekII']:
            grade_map['QP12'] = ''
            if HJ == '2':
                grade_map['QP12'] = QP12_TEXT.format(
                        vom = grade_map['QUALI_D'],
                        bis = grade_map['ISSUE_D'])
                if grade_map['*Q'] == 'Erw':
                    # Versetzung 12.Gym -> 13.Gym
                    comment = grade_map['COMMENT']
                    newcomment = VERSETZUNG_12_13.format(
                        grades_d = grade_map['GRADES_D'])
                    if comment:
                        newcomment += '\n' + comment
                    grade_map['COMMENT'] = newcomment
        else:
            Z = set_field('Zeugnis')
            if Z:
                grade_map['ZEUGNIS'] = Z.upper()
            # Versetzung 11.Gym -> 12.Gym
            if (stream == 'Gym' and HJ == '2'
                    and grade_map['CLASS'] == '11'
                    and grade_map['*Q'] == '12'):
                comment = grade_map['COMMENT']
                newcomment = VERSETZUNG_11_12.format(
                        grades_d = grade_map['GRADES_D'])
                if comment:
                    newcomment += '\n' + comment
                grade_map['COMMENT'] = newcomment
        grade_map['NOCOMMENT'] = '' if grade_map['COMMENT'] else _NOCOMMENT

    elif rtype == 'Abschluss':
        q = grade_map['*Q']
        if q == 'Erw' and grade_map['CYEAR'] == '11':
            q = 'RS'    # 'Erw' not possible in class 11
        try:
            grade_map['SEKI'] = SEKI_TEXT[q] # SekI 'Abschluss' only
        except KeyError as e:
            raise GradeConfigError(_INVALID_QUALI.format(
                    pid = grade_map['PID'], quali = q or '')) from e
        grade_map['NOCOMMENT'] = '' if grade_map['COMMENT'] else _NOCOMMENT

    elif rtype == 'Abgang':
        if grade_map['SekII']:
            if grade_map['CYEAR'] == '12':
                grade_map['QP12'] = QP12_TEXT.format(
                        vom = grade_map['QUALI_D'],
                        bis = grade_map['ISSUE_D'])
                grade_map['GS'] = GS_TEXT['HS']
                if HJ == '2':
                    try:
                        grade_map['GS'] = GS_TEXT[grade_map['*Q']]
                    except KeyError:
                        pass
        else:
            grade_map['GSVERMERK'] = ''
            grade_map['GS'] = ''
            # Gleichstellungsvermerk
            klass = grade_map['CYEAR']
            q = grade_map['*Q']
            if (klass == '10' and HJ == '2') or klass in ('11', '12'):
                if q in ('Erw', '12', 'RS', 'HS'):
                    grade_map['GS'] = GS_TEXT['HS']     # only HS-Abschluss
                    grade_map['GSVERMERK'] = "Gleichstellungsvermerk"
    elif rtype in ('Abi', 'X', 'FHS'):
        grade_map['FrHr'] = 'Herr' if grade_map['SEX'] == 'm' else 'Frau'
        grade_map['FERTIG_D'] = Dates.print_date(grade_map['*F_D'])
    elif rtype != 'Orientierung':
        raise GradeConfigError(_INVALID_RTYPE.format(rtype = rtype))
    grade_map['NOCOMMENT'] = '' if grade_map['COMMENT'] else _NOCOMMENT
