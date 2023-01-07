"""
local/abitur_wani.py

Last updated:  2023-01-06

Handling Abitur qualifications in a Waldorf school in Niedersachsen.

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

COND_PRINT = {True: "Ja", False: "Nein"}

GRADE_TEXT = {
    "0": "null", "1": "eins", "2": "zwei", "3": "drei",
    "4": "vier", "5": "fünf", "6": "sechs", "7": "sieben",
    "8": "acht", "9": "neun"
}

########################################################################

if __name__ == "__main__":
    # Enable package import if running as module
    import sys, os
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))

T = TRANSLATIONS("local.abitur")

### +++++


#TODO
#        self.grade_table = full_grade_table("Abitur", group, "")

# Can't I get the pupils from grade_table?
#        self.pupil_data_list = self.grade_table["GRADE_TABLE_PUPILS"]
        # [(pdata, grademap), ... ]

def choose_pupil(grade_table:dict, index:int) -> dict:
    pupil_data_list = grade_table["GRADE_TABLE_PUPILS"]
    pdata, grademap = pupil_data_list[index]
    # print("\n==", self.pdata)
    sid_data = grade_table["ALL_SIDS"]
    gslots = {
        # The '.'-suffixes: [start index, number of slots]
        'e': [1, 3],
        'g': [4, 1],
        'm': [5, 2],
        'n': [7, 2]
    }
    sidmap = {} # map result key to subject tag
    result = {
        "__SIDMAP__": sidmap,
        "__PUPIL__": pdata
    }
    empty_slots = 0
    for sid, g in grademap.items():
        if g == '/': continue
        try:
            s0, x = sid.rsplit('.', 1)
            type_info = gslots[x]
        except ValueError:
            # Non-grade field
            sidmap[sid] = sid
            result[sid] = g
            if not g:
                empty_slots += 1
            continue
        except KeyError:
            REPORT("ERROR", T["INVALID_SID"].format(sid=sid))
            continue
        # Grade field, sort according to '.'-suffixes
        i = type_info[1]
        if i == 0:
            REPORT("ERROR", T["NO_SLOT"].format(sid=sid))
            continue
        type_info[1] = i - 1
        n = type_info[0]
        type_info[0] = n + 1
        tag = f"G{n}"
        sidmap[tag] = sid
        result[tag] = g
        if not g:
            empty_slots += 1
        # Subject name without '*'-suffix
        result[f"S{n}"] = sid_data[sid]["NAME"].split('*', 1)[0]
    for k, v in gslots.items():
        if v[1] != 0:
            REPORT("ERROR", T["TOO_FEW_SUBJECTS"].format(tag=k))
    if empty_slots:
        REPORT("ERROR", T["EMPTY_SLOTS"].format(n=str(empty_slots)))
    return result


def calculate(grades:dict[str,str]) -> dict[str,str]:
    """Perform the calculations to determine the result of the Abitur.
    """
    print("\nTODO: calculate", grades)

    fields = {}
    scaled = []

    ## Subjects 1 – 4
    totalA = 0
    for i in 1,2,3,4:
        gtag = f"G{i}"
        gs = grades[gtag]
        fields[gtag] = gs
        try:
            g = int(gs)
        except ValueError:
            g = 0
        gtag += "n"
        gn = grades[gtag]
        fields[gtag] = gn
        if gn and gn != '*':
            avn10 = (g + int(gn)) * 5
        else:
            avn10 = g * 10
        if avn10 % 10 == 0:
            avns = str(avn10 // 10)
        else:
            avns = str(avn10 // 10) + ",5"
        fields[f"AVE_{i}"] = avns
        s = 8 if i == 4 else 12
        scl = (avn10 * s) // 10
        scaled.append(scl)
        scls = str(scl)
        fields[f"SCALED_{i}"] = scls
        totalA += scl
    fields["SUM_A"] = str(totalA)

    ## Subjects 5 – 8
    totalB = 0
    for i in 5,6,7,8:
        gtag = f"G{i}"
        gs = grades[gtag]
        fields[gtag] = gs
        try:
            g = int(gs)
        except ValueError:
            g = 0
        fields[f"AVE_{i}"] = str(g)
        scl = g * 4
        scaled.append(scl)
        fields[f"SCALED_{i}"] = str(scl)
        totalB += scl
    fields["SUM_B"] = str(totalB)

    ## The pass checks
    ok = True
    # Check 1: none with 0 points
    for i in scaled:
        if i == 0:
            ok = False
            break
    fields["COND_1"] = COND_PRINT[ok]
    # Check 2: at least two of first four >= 5 points
    n = 0
    for i in range(3):
        if scaled[i] and scaled[i] >= 60:
            n += 1
    if scaled[3] and scaled[3] >= 40:
        n += 1
    yes = n >= 2
    fields["COND_2"] = COND_PRINT[yes]
    ok &= yes
    # Check 3: at least two of last four >= 5 points
    n = 0
    for i in range(4, 8):
        if scaled[i] and scaled[i] >= 20:
            n += 1
    yes = n >= 2
    fields["COND_3"] = COND_PRINT[yes]
    ok &= yes
    # Check 4: <scaled14> >= 220
    yes = totalA >= 220
    fields["COND_4"] = COND_PRINT[yes]
    ok &= yes
    # Check 5: <scaled58> >= 80
    yes = totalB >= 80
    fields["COND_5"] = COND_PRINT[yes]
    ok &= yes

    ## The final result
    total = totalA + totalB
    fields["TOTAL"] = str(total)

#TODO

    fields["RESULT"] = "–––"
    if ok:
        # Calculate final grade using a formula. To avoid rounding
        # errors, use integer arithmetic.
        g180 = (1020 - total)
        g1 = str (g180 // 180)
        if g1 == "0":
            g1 = "1"
            g2 = "0"
        else:
            g2 = str ((g180 % 180) // 18)
        fields["Grade1"] = g1
        fields["Grade2"] = g2
        fields["GradeT"] = GRADE_TEXT[g1] + ", " + GRADE_TEXT[g2]
        fields["RESULT"] = g1 + "," + g2
        fields["REPORT_TYPE"] = "Abi"
#TODO++
#    elif fhs(fields):
#        fields["REPORT_TYPE"] = "FHS"
    else:
        fields["REPORT_TYPE"] = "NA"

    return fields


#TODO
def fhs(fields):
    """Calculations for "Fachhochschulreife".
    """
    def bestof(sids):
        s = None
        g = -1
        for sid in sids:
            try:
                _g = s2g[sid]
            except KeyError:
                continue
            if _g > g:
                s = sid
                g = _g
        del(s2g[s])
        subjects.append(s)
        grades.append(g)
    #-
    s2g = {s: int(fields["AVER_%d" % i]) for s, i in self.sid2i.items()}
    subjects = []
    grades = []
    # Get the best of each group
    try:
        subjects.append("De")
        grades.append(s2g.pop("De"))
        subjects.append("Ma")
        grades.append(s2g.pop("Ma"))
#?
        bestof(_FS)
        bestof(_NW)
        bestof(_GW)
    except:
        raise Bug("Missing subject/grade")
    bestof(s2g)
    bestof(s2g)
    n = 0   # ok-grades
    _n = 0  # grades under 5 points
    for i in grades:    # check for 0 points and <5 points
        if not i:
            return False
        if i < 5:
            _n += 1
            if _n == 4:
                # >3 subjects under 5 points
                return False
            if _n == 3 and n == 0:
                # >2 "eA"-subjects under 5 points
                return False
    points20 = sum(grades[:4])
    points35 = points20 + sum(grades[4:])
    fields["sum"] = str(points35)
    if points20 < 20:
        return False
    if points35 < 35:
        return False
    # Calculate final grade using a formula. To avoid rounding
    # errors, use integer arithmetic.
    g420 = 2380 - points35*20 + 21
    g1 = str(g420 // 420)
    g2 = str((g420 % 420) // 42)
    fields["Note1"] = g1
    fields["Note2"] = g2
    fields["NoteT"] = self._gradeText[g1] + ", " + self._gradeText[g2]
    fields["RESULT"] = "FHS: " + g1 + "," + g2
    return True
