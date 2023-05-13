"""
local/grade_processing.py

Last updated:  2023-05-13

Functions to perform grade calculations.

=+LICENCE=============================
Copyright 2023 Michael Towers

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

UNKNOWN_GRADE_FUNCTION = (
    "In Konfigurationdatei GRADES_BASE: unbekannte"
    " Notenberechnungsfunktion – „{name}“"
)
UNKNOWN_GSVM = (
    "In Konfigurationdatei GRADES_BASE: unbekannte"
    " Gleichstellungsvermerk – „{gs}“"
)

### +++++

from typing import Optional
from local.abi_wani_calc import Abi_calc

AVERAGE_DP = 2  # decimal places for averages

GRADE_FUNCTIONS = {}

GRADE_NUMBER = {
    "1+": 15,
    "1": 14,
    "1-": 13,
    "2+": 12,
    "2": 11,
    "2-": 10,
    "3+": 9,
    "3": 8,
    "3-": 7,
    "4+": 6,
    "4": 5,
    "4-": 4,
    "5+": 3,
    "5": 2,
    "5-": 1,
    "6": 0
}

NUMBER_GRADE = {v: k for k, v in GRADE_NUMBER.items()}

NOGRADE = "––––––"  # for empty subjects/grades in reports

GSVM = {
    "HS": ("Dieses Zeugnis ist dem Sekundarabschluss I –"
            " Hauptschulabschluss gleichgestellt. Es vermittelt die"
            " gleiche Berechtigung wie das Zeugnis über den"
            " Sekundarabschluss I – Hauptschulabschluss."
    ),
    "RS": ("Dieses Zeugnis ist dem Sekundarabschluss I –"
            " Realschulabschluss gleichgestellt. Es vermittelt die"
            " gleiche Berechtigung wie das Zeugnis über den"
            " Sekundarabschluss I – Realschulabschluss."
    ),
    "Erw": ("Dieses Zeugnis ist dem Erweiterten Sekundarabschluss I"
            " gleichgestellt. Es vermittelt die"
            " gleiche Berechtigung wie das Zeugnis über den"
            " Erweiterten Sekundarabschluss I."
    ),
}

### -----

def GradeFunction(
    fname: str,
    subject: dict,
    grades: dict[str, str],
    raw_grades: Optional[dict[str, str]],
) -> Optional[list[tuple[str, dict]]]:
    """Perform the given function to calculate the value of the field
    specified by <subject>.
    Return <None> or a list of new column list entries:
        [(column type, column data), ... ]
    """
    if not fname:
        return []
    try:
        fn = GRADE_FUNCTIONS[fname]
    except KeyError:
        REPORT("ERROR", UNKNOWN_GRADE_FUNCTION.format(name=fname))
        return []
    return fn(grades, subject, raw_grades)


def ROUNDED_AVERAGE_I(
    grades: dict[str, str],
    sdata: dict,
    raw_grades: Optional[dict[str, str]],
):
    """Calculate the value of a "composite" subject from its component
    subject grades. This is using grades 1 – 6 (with +/-).
    No return.
    """
    COMPONENTS = sdata["PARAMETERS"]["COMPONENTS"]
    # print("\n === ROUNDED_AVERAGE_I:", grades, "\n ++", COMPONENTS)
    ilist = []
    for sid in COMPONENTS:
        try:
            ilist.append(GRADE_NUMBER[grades[sid]])
        except KeyError:
            pass
    if ilist:
        s = sum(ilist)
        a = int(s / len(ilist) + 0.5)
        astr = NUMBER_GRADE[a]
        # print("%%%%%%%%% ROUNDED_AVERAGE_I:", a, "-->", astr)
    else:
        astr = '*'
        # print("%%%%%%%%% ROUNDED_AVERAGE_I:", astr)
    sid = sdata["SID"]
    og = grades.get(sid) or ""
    if og != astr:
        grades[sid] = astr

GRADE_FUNCTIONS["ROUNDED_AVERAGE_I"] = ROUNDED_AVERAGE_I


def ROUNDED_AVERAGE_II(
    grades: dict[str, str],
    sdata: dict,
    raw_grades: Optional[dict[str, str]],
):
    """Calculate the value of a "composite" subject from its component
    subject grades. This is using grades 15 – 0.
    No return.
    """
    COMPONENTS = sdata["PARAMETERS"]["COMPONENTS"]
    # print("\n === ROUNDED_AVERAGE_II:", grades, "\n ++", COMPONENTS)
    ilist = []
    for sid in COMPONENTS:
        try:
            ilist.append(int(grades[sid]))
        except (ValueError, KeyError):
            pass
    if ilist:
        s = sum(ilist)
        a = int(s / len(ilist) + 0.5)
        astr = f'{a:02}'
    else:
        astr = '*'
    # print("%%%%%%%%% ROUNDED_AVERAGE_II:", astr)
    sid = sdata["SID"]
    og = grades.get(sid) or ""
    if og != astr:
        grades[sid] = astr

GRADE_FUNCTIONS["ROUNDED_AVERAGE_II"] = ROUNDED_AVERAGE_II


def AVERAGE_I(
    grades: dict[str, str],
    sdata: dict,
    raw_grades: Optional[dict[str, str]],
):
    """This calculates an average of a set of grades (1 – 6, ignoring
    +/-) to a number (AVERAGE_DP) of decimal places without rounding –
    for calculation of qualifications.
    No return.
    """
    COMPONENTS = sdata["PARAMETERS"]["COMPONENTS"]
    ilist = []
    for sid in COMPONENTS:
        try:
            ilist.append(int(grades[sid].rstrip('+-')))
        except (ValueError, KeyError):
            pass    # ignore non-grades
    if ilist:
        s = sum(ilist)
        a = s / len(ilist)
        astr0 = str(int(a * 10**AVERAGE_DP))
        astrl = astr0[:-AVERAGE_DP]
        astr = f"{astr0[:-AVERAGE_DP]},{astr0[-AVERAGE_DP:]}"
        # print("%%%%%%%%% AVERAGE_I:", astr0, "-->", astr)
    else:
        astr = '*'
        # print("%%%%%%%%% AVERAGE_I:", astr)
    sid = sdata["SID"]
    og = grades.get(sid) or ""
    if og != astr:
        grades[sid] = astr

GRADE_FUNCTIONS["AVERAGE_I"] = AVERAGE_I


# Abitur calculations -> report type (success, etc.)
GRADE_FUNCTIONS["ABITUR_NIWA_RESULT"] = Abi_calc


def ProcessGradeData(pdata, grade_info, grade_config):
    """Local tweaks needed to prepare the pupil's data for entry in
    a grade template.
    """
    try:
        no_grade = grade_info["SYMBOLS"]["NOGRADE"]
    except KeyError:
        pass
    else:
        for k, v in pdata.items():
            if v == NOGRADE:
                pdata[k] = no_grade
    pdata["NOCOMMENT"] = "" if pdata.get("REMARKS") else "––––––––––"
    try:
        level = pdata["LEVEL"]
    except KeyError:
        pass
    else:
        pdata["LEVEL"] = grade_config["LEVEL_MAP"].get(level) or level
    if (gs := pdata.get("GSVM")):
        pdata["GSVERMERK"] = "Gleichstellungsvermerk"
        try:
            pdata["GSVM"] = GSVM[gs]
        except KeyError:
            REPORT("ERROR", UNKNOWN_GSVM.format(gs=gs))
            pdata["GSVM"] = "???"
    try:
        pdata["CYEAR"] = str(int(pdata["CLASS"][:2]))
    except ValueError:
        pdata["CYEAR"] = str(int(pdata["CLASS"][0]))
