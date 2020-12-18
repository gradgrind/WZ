# -*- coding: utf-8 -*-

"""
local/grade_template.py

Last updated:  2020-12-18

Manage templates for grade reports.


=+LICENCE=============================
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

=-LICENCE========================================
"""

#TODO: Abitur/13

#? ... this one is only for Abitur:
#    data['FrHr'] = 'Herr' if grades.pdata['SEX'] == 'm' else 'Frau'



### Messages
_INVALID_RTYPE = "Ungültiger Zeugnistyp: '{rtype}'"
_INVALID_QUALI = "Ungültiges Qualifikationsfeld für Schüler {pid}: '{quali}'"


from local.grade_config import GradeConfigError, STREAMS

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
    rtype = grade_map['REPORT_TYPE']
    if rtype == 'Zeugnis':
        stream = grade_map['STREAM']
        term = grade_map['TERM']
        if grade_map['SekII']:
            grade_map['QP12'] = ''
            if term == '1':
                grade_map['HJ'] = '1'
            elif term == '2':
                grade_map['HJ'] = '1. und 2.'
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
            if term[0] == 'S':
                grade_map['Zeugnis'] = 'Zwischenzeugnis'
                grade_map['ZEUGNIS'] = 'ZWISCHENZEUGNIS'
            else:
                grade_map['Zeugnis'] = 'Zeugnis'
                grade_map['ZEUGNIS'] = 'ZEUGNIS'
                grade_map['LEVEL'] = STREAMS[stream] # SekI only
                # Versetzung 11.Gym -> 12.Gym
                if (stream == 'Gym' and term == '2'
                        and grade_map['CLASS'] == '11'
                        and grade_map['*Q'] == 'Erw'):
                    comment = grade_map['COMMENT']
                    newcomment = VERSETZUNG_11_12.format(
                            grades_d = grade_map['GRADES_D'])
                    if comment:
                        newcomment += '\n' + comment
                    grade_map['COMMENT'] = newcomment
        grade_map['NOCOMMENT'] = '' if grade_map['COMMENT'] else _NOCOMMENT

    elif rtype == 'Orientierung':
        grade_map['LEVEL'] = STREAMS[stream] # SekI only

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
        stream = grade_map['STREAM']
        term = grade_map['TERM']
        if grade_map['SekII']:
            if grade_map['CYEAR'] == '12':
                grade_map['QP12'] = QP12_TEXT.format(
                        vom = grade_map['QUALI_D'],
                        bis = grade_map['ISSUE_D'])
                term = grade_map['TERM']
                grade_map['GS'] = GS_TEXT['HS']
                if term == '2':
                    try:
                        grade_map['GS'] = GS_TEXT[grade_map['*Q']]
                    except KeyError:
                        pass
        else:
            grade_map['GSVERMERK'] = ''
            grade_map['GS'] = ''
            stream = grade_map['STREAM']
            grade_map['LEVEL'] = STREAMS[stream]
            # Gleichstellungsvermerk
            klass = grade_map['CYEAR']
            term = grade_map['TERM']
            q = grade_map['*Q']
            if (klass == '10' and term == '2') or klass in ('11', '12'):
                if q in ('Erw', 'RS', 'HS'):
                    grade_map['GS'] = GS_TEXT['HS']     # only HS-Abschluss
                    grade_map['GSVERMERK'] = "Gleichstellungsvermerk"
    else:
        raise GradeConfigError(_INVALID_RTYPE.format(rtype = rtype))
    grade_map['NOCOMMENT'] = '' if grade_map['COMMENT'] else _NOCOMMENT

###

#Abgang Quali:HS/RS/Erw/-
#Abschluss Quali:HS/RS/Erw (no Quali => no Abschluss!)
#Zeugnis 12G/2: Quali must be Erw for Versetzung
#Zeugnis 11G/2: Average < 3,00 for Versetzung
# Could calculate a suggested Quali value?

"""
SCHOOLBIG
SCHOOL
SCHOOLYEAR
ISSUE_D
COMMENT = ""
NOCOMMENT = "––––––––––"

SekI:
    ZEUGNIS
    Zeugnis
    LEVEL
    CLASS
    +SekI-Abgang:
        CYEAR (class number)
        GSVERMERK: "Gleichstellungsvermerk" or ""
        GS: Gleichstellungsvermerk (HS) or ""
        +SekI-Abschluss:
            SEKI: e.g. Erweiterter Sekundarabschluss I
    COMMENT: Versetzung? (11:Gym/2 only) ... with GRADES_D
    NOCOMMENT: "" if COMMENT set
SekII-12:
    HJ: "1." or "1. und 2."
    QP12: "hat den 12. Jahrgang der Qualifikationsphase vom 15.08.2019"
        " bis zum 15.07.2020 besucht." (needs QUALI_D, last-school-day)
    COMMENT: Versetzung? ... with GRADES_D
    NOCOMMENT: "" if COMMENT set

SekII-12-Abgang:
    QP12: see above, but with EXIT_D instead of last-school-day
    GS: Gleichstellungsvermerk
SekII-13_1:
    QUALI_D
SekII-13-Abgang:
    QUALI_D
    EXIT_D
    all Abitur grades from 12 and 13

Abitur (etc):
    HOME
    FrHr
    calculated abi grades, etc.
"""
