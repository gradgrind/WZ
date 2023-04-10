"""
local/grade_processing.py

Last updated:  2023-04-10

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
    "In Konfigurationdatei GRADE_CONFIG: unbekannte"
    " Notenberechnungsfunktion – „{name}“"
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
            g = grades[sid]
        except KeyError:
            raise Bug(f"Grade for sid {sid} not available")
        try:
            ilist.append(GRADE_NUMBER[g])
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
        except ValueError:
            pass
        except KeyError:
            raise Bug(f"Grade for sid {sid} not available")
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
        except ValueError:
            pass    # ignore non-grades
        except KeyError:
            raise Bug(f"Grade for sid {sid} not available")
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


#TODO: Building reports

def ReportName(grade_table, rtype):
    """Return a suitable file/folder name for a set of reports.
    """
    if instance:= grade_table["INSTANCE"]:
        instance = '-' + instance
    occasion = grade_table["OCCASION"]
    group = grade_table["CLASS_GROUP"]
    return f"{rtype}-{occasion}-{group}{instance}".replace(" ", "_")


def ProcessGradeData(pdata, grade_info, grade_config):
#TODO
    pdata["NOCOMMENT"] = "" if pdata.get("REMARKS") else "––––––––––"
    try:
        level = pdata["LEVEL"]
    except KeyError:
        pass
    else:
        pdata["LEVEL"] = grade_config["LEVEL_MAP"].get(level) or level
