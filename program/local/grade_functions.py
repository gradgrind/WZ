"""
local/grade_functions.py

Last updated:  2022-12-25

Functions to perform grade calculations.

=+LICENCE=============================
Copyright 2022 Michael Towers

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

T = TRANSLATIONS("local.grade_functions")

### +++++

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

### ---

def grade_function(fname:str, grades:list[str]) -> str:
    try:
        return GRADE_FUNCTIONS[fname](grades)
    except KeyError:
        REPORT("ERROR", T["UNKNOWN_GRADE_FUNCTION"].format(name=fname))


#TODO ...

def ROUNDED_AVERAGE_I(grades):
    ilist = []
    for g in grades:
        try:
            ilist.append(GRADE_NUMBER[g])
        except KeyError:
            pass
    if ilist:
        s = sum(ilist)
        a = int(s / len(ilist) + 0.5)
        astr = NUMBER_GRADE[a]
    else:
        astr = '*'
    print("%%%%%%%%% ROUNDED_AVERAGE_I:", grades, astr)
    return astr

GRADE_FUNCTIONS["ROUNDED_AVERAGE_I"] = ROUNDED_AVERAGE_I

def ROUNDED_AVERAGE_II(grades):
    ilist = []
    for g in grades:
        try:
            ilist.append(int(g))
        except ValueError:
            pass
    if ilist:
        s = sum(ilist)
        a = int(s / len(ilist) + 0.5)
        astr = f'{a:02}'
    else:
        astr = '*'
    print("%%%%%%%%% ROUNDED_AVERAGE_II:", grades, astr)
    return astr

GRADE_FUNCTIONS["ROUNDED_AVERAGE_II"] = ROUNDED_AVERAGE_II

def AVERAGE_I(grades):
    ilist = []
    for g in grades:
        try:
            ilist.append(int(g.rstrip('+-')))
        except ValueError:
            pass
    if ilist:
        s = sum(ilist)
        a = s / len(ilist)
        astr = str(round(a, 2)).replace('.', ',')
    else:
        astr = '*'
    print("%%%%%%%%% AVERAGE_I:", grades, astr)
    return astr

GRADE_FUNCTIONS["AVERAGE_I"] = AVERAGE_I




#TODO: Building reports

def process_grade_data(pdata, grade_info, grade_config):
#TODO
    pdata["NOCOMMENT"] = "" if pdata["REMARKS"] else "––––––––––"
    try:
        level = pdata["LEVEL"]
    except KeyError:
        pass
    else:
        pdata["LEVEL"] = grade_config["LEVEL_MAP"].get(level) or level
