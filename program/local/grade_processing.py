"""
local/grade_processing.py

Last updated:  2023-01-17

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

AVERAGE_DP = 2  # decimal places for averages

########################################################################

from typing import Optional
T = TRANSLATIONS("local.grade_processing")

### +++++

GRADE_FUNCTIONS = {}

SPECIAL_HANDLERS = {}

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
    fname:str, sdata:dict, grades:dict[str,str]
) -> tuple[str,str]:
    """Perform the given function to calculate the value of the field
    specified by <sdata>.
    Return (sid, old-value).
    """
    if not fname:
        return []
    try:
        fn = GRADE_FUNCTIONS[fname]
    except KeyError:
        REPORT("ERROR", T["UNKNOWN_GRADE_FUNCTION"].format(name=fname))
        return []
    return fn(grades, sdata)


def SpecialHandler(fname, **kargs) -> None:
    try:
        fn = SPECIAL_HANDLERS[fname]
    except KeyError:
        REPORT("ERROR", T["UNKNOWN_SPECIAL_FUNCTION"].format(name=fname))
        return
    fn(**kargs)


def ROUNDED_AVERAGE_I(
    grades: dict[str:str], sdata:dict
) -> Optional[tuple[str,str]]:
    """Calculate the value of a "composite" subject from its component
    subject grades. This is using grades 1 – 6 (with +/-).
    Return a list of changes: (sid, grade) pairs.
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
    og = grades[sid]
    if og == astr:
        return None
    else:
        grades[sid] = astr
        return [(sid, og)]

GRADE_FUNCTIONS["ROUNDED_AVERAGE_I"] = ROUNDED_AVERAGE_I


def ROUNDED_AVERAGE_II(
    grades: dict[str:str], sdata:dict
) -> Optional[tuple[str,str]]:
    """Calculate the value of a "composite" subject from its component
    subject grades. This is using grades 15 – 0.
    Return a list of changes: (sid, grade) pairs.
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
    og = grades[sid]
    if og == astr:
        return None
    else:
        grades[sid] = astr
        return [(sid, og)]

GRADE_FUNCTIONS["ROUNDED_AVERAGE_II"] = ROUNDED_AVERAGE_II


def AVERAGE_I(
    grades: dict[str:str], sdata:dict
) -> Optional[tuple[str,str]]:
    """This calculates an average of a set of grades (1 – 6, ignoring
    +/-) to a number (AVERAGE_DP) of decimal places without rounding –
    for calculation of qualifications.
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
    og = grades[sid]
    if og == astr:
        return None
    else:
        grades[sid] = astr
        return [(sid, og)]

GRADE_FUNCTIONS["AVERAGE_I"] = AVERAGE_I


#TODO
def ABITUR_NIWA_RESULT(
    grades: dict[str:str], sdata:dict
) -> Optional[tuple[str,str]]:
    return None

GRADE_FUNCTIONS["ABITUR_NIWA_RESULT"] = ABITUR_NIWA_RESULT


def abi_extra_subjects(subjects):
    """Add grade slots for additional exam results in Abitur.
    """
    nsid = 1000
    for sdata in sorted(subjects.values()):
        if sdata [3] in ('E', 'G'):
            name = sdata[2].split('*', 1)[0] + "*nach"
            sid = sdata[1].split('.', 1)[0] + ".x"
            subjects[sid] = [nsid, sid, name, 'X', None]
            nsid += 1

SPECIAL_HANDLERS["ABI_WANI_SUBJECTS"] = abi_extra_subjects


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
