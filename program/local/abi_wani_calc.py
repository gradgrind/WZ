"""
local/abi_wani_calc.py

Last updated:  2023-04-09

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

# Messages
SID_WITHOUT_EXTENSION = (
    "(Fach {name}: Kennzeichen {sid} hat keine „.“-Erweiterung"
)
INVALID_SID = (
    "Fach {name}: Kennzeichen {sid} hat eine ungültige „.“-Erweiterung"
)
NO_SLOT_LEFT = (
    "Fach {name} mit Kennzeichen {sid}: zu viele Fächer mit dieser"
    " „.“-Erweiterung"
)
TOO_FEW_SUBJECTS = "Zu wenige Fächer mit „.“-Erweiterung „{tag}“"
EMPTY_SLOTS = "Keine Daten für {n} Felder"
COMPOSITES_NOT_SUPPORTED = (
    "„Sammelfächer“ sind im Abitur nicht zulässig:\n  {names}"
)

### +++++

COND_PRINT = {True: "Ja", False: "Nein"}

GRADE_TEXT = {
    "0": "null", "1": "eins", "2": "zwei", "3": "drei",
    "4": "vier", "5": "fünf", "6": "sechs", "7": "sieben",
    "8": "acht", "9": "neun"
}

NO_GRADE = "/"

### -----


def sort_pupil_grades(
    grades: dict[str, str],
    raw_grades:dict[str, str],
    slist:list[tuple[str, str]],
) -> tuple[dict, dict, list[tuple[str,str]]]:
    """Sort the subjects and grades into the groups required for the
    calculations and certificate. This is based on the (necessary!)
    suffixes of the subject-ids (after '.'):
        3 "erweiterte" courses with written examinations    (.e)
        1 "grundlegende" course with written examination    (.g)
        2 courses with compulsory oral examinations         (.m)
        2 courses without compulsory examination            (.n)
    """
    gslots = {
        # The '.'-suffixes of the subjects: [start index, number of slots]
        'e': [1, 3],
        'g': [4, 1],
        'm': [5, 2],
        'n': [7, 2]
    }
#TODO: Do I need the COMPONENTS field? Why can't I just use the defined
# columns?
#    COMPONENTS = sdata["PARAMETERS"]["COMPONENTS"]
    sidmap = {} # map field tag to subject-id
    sidindex = {} # map basic subject-id (before '.') to subject index
    empty_slots = 0
    xsids = {}
    xsids_in = set()    # to check for new subjects with "Nachprüfung"
    xsids_out = []      # [(sid, name), ... ]
    for sid, sname in slist:
        if sid.endswith(".x"):  # subject with "Nachprüfung"
            xsids_in.add(sid)
            if sid not in xsids:
                # default value for such a subject
                xsids[sid] = NO_GRADE
            continue
        g = grades.get(sid) or ''
        if g == NO_GRADE: continue
        try:
            s0, x = sid.rsplit('.', 1)
            type_info = gslots[x]
        except ValueError:
            REPORT("ERROR", SID_WITHOUT_EXTENSION(sid=sid, name=sname))
            continue
        except KeyError:
            REPORT("ERROR", INVALID_SID.format(sid=sid, name=sname))
            continue
        # Grade field, sort according to '.'-suffixes
        i = type_info[1]
        if i == 0:
            REPORT("ERROR", NO_SLOT_LEFT.format(sid=sid, name=sname))
            continue
        type_info[1] = i - 1
        n = type_info[0]
        type_info[0] = n + 1
        tag = f"G{n}"
        sidmap[tag] = sid
        grades[tag] = g
        sidindex[s0] = n    # for FHS-calculations
        if not g:
            empty_slots += 1
        # Subject name without '*'-suffix
        name0 = sname.split('*', 1)[0]
        grades[f"S{n}"] = name0
        if n < 5:
            # Manage additional oral result
            tn = f"G{n}n"
            sn = f"{s0}.x"
            sidmap[tn] = sn
            try:
                gn = raw_grades[sn]
                if gn == NO_GRADE:  # actually, this shouldn't be possible
                    gn = ''
            except KeyError:
                gn = ''
            grades[tn] = gn
            xsids[sn] = gn
            xsids_out.append((sn, f"{name0}*nach"))
    for k, v in gslots.items():
        if v[1] != 0:
            REPORT("ERROR", TOO_FEW_SUBJECTS.format(tag=k))
    if empty_slots:
        REPORT("ERROR", EMPTY_SLOTS.format(n=str(empty_slots)))
    grades.update(xsids)
    newsids = [
        sn
        for sn in xsids_out
        if sn[0] not in xsids_in
    ]
    return (sidmap, sidindex, newsids)


def Abi_calc(
    grades: dict[str:str],
    raw_grades:dict[str,str],
    columns: dict[str, list[dict]],
    sdata: dict,
):
    """Perform the calculations to determine the result of the Abitur.
    NOTE that the <subjects> list can be modified (extended) by this
    function.
    The <grades> mapping has multiple entries modified (or added).
    """
    slist = [(s["SID"], s["NAME"]) for s in columns["subjects"]]
    if columns["composites"]:
        REPORT("ERROR", COMPOSITES_NOT_SUPPORTED.format(
            names=", ".join(s["NAME"] for s in columns["composites"])
        ))
    sidmap, sidindex, newsids = sort_pupil_grades(grades, raw_grades, slist)
    ## Extend subject list if necessary ('.x' grades)
    for sid, sname in newsids:
        columns["subjects"].append(
            {
                "SID": sid,
                "NAME": sname,
                "TYPE": "SUBJECT",
                "GROUP": "X",
            }
        )
    # Sort (again)
    columns["subjects"].sort(key=lambda k: (k["GROUP"], k["NAME"]))
    ## Now do the calculations
    scaled = []
    ## Subjects 1 – 4
    totalA = 0
    for i in 1,2,3,4:
        gtag = f"G{i}"
        gs = grades[gtag]
        try:
            g = int(gs)
        except ValueError:
            g = 0
        gtag += "n"
        gn = grades[gtag]
        if gn and gn != '*':
            avn10 = (g + int(gn)) * 5
        else:
            avn10 = g * 10
        if avn10 % 10 == 0:
            avns = str(avn10 // 10)
        else:
            avns = str(avn10 // 10) + ",5"
        grades[f"AVE_{i}"] = avns
        s = 8 if i == 4 else 12
        scl = (avn10 * s) // 10
        scaled.append(scl)
        scls = str(scl)
        grades[f"SCALED_{i}"] = scls
        totalA += scl
    grades["SUM_A"] = str(totalA)
    ## Subjects 5 – 8
    totalB = 0
    for i in 5,6,7,8:
        gtag = f"G{i}"
        gs = grades[gtag]
        try:
            g = int(gs)
        except ValueError:
            g = 0
        grades[f"AVE_{i}"] = str(g)
        scl = g * 4
        scaled.append(scl)
        grades[f"SCALED_{i}"] = str(scl)
        totalB += scl
    grades["SUM_B"] = str(totalB)
    ## The pass checks
    ok = True
    # Check 1: none with 0 points
    for i in scaled:
        if i == 0:
            ok = False
            break
    grades["COND_1"] = COND_PRINT[ok]
    # Check 2: at least two of first four >= 5 points
    n = 0
    for i in range(3):
        if scaled[i] and scaled[i] >= 60:
            n += 1
    if scaled[3] and scaled[3] >= 40:
        n += 1
    yes = n >= 2
    grades["COND_2"] = COND_PRINT[yes]
    ok &= yes
    # Check 3: at least two of last four >= 5 points
    n = 0
    for i in range(4, 8):
        if scaled[i] and scaled[i] >= 20:
            n += 1
    yes = n >= 2
    grades["COND_3"] = COND_PRINT[yes]
    ok &= yes
    # Check 4: <scaled14> >= 220
    yes = totalA >= 220
    grades["COND_4"] = COND_PRINT[yes]
    ok &= yes
    # Check 5: <scaled58> >= 80
    yes = totalB >= 80
    grades["COND_5"] = COND_PRINT[yes]
    ok &= yes
    ## The final result
    total = totalA + totalB
    grades["TOTAL"] = str(total)
    grades["RESULT"] = "–––"
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
        grades["Grade1"] = g1
        grades["Grade2"] = g2
        grades["GradeT"] = GRADE_TEXT[g1] + ", " + GRADE_TEXT[g2]
        grades["RESULT"] = g1 + "," + g2
        astr = "Abi"
    elif fhs(grades, sidindex, sdata["PARAMETERS"]["FHS"]):
        astr = "FHS"
    else:
        astr = "NA"
    sid = "REPORT_TYPE"
    og = grades.get(sid) or ""
    if og == astr:
        return None
    else:
        grades[sid] = astr
        return (sid, og)

#TODO: clean up (I think it is functional)
def fhs(fields, indexes, fhs_subjects):
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


    print("\n%%%%%%%%%%%% FHS:", fields)
    print("   ++", indexes)
    print("   --", fhs_subjects)

    s2g = {
        s: float(fields[f"AVE_{i}"].replace(',', '.'))
        for s, i in indexes.items()
    }
    print("   ~~", s2g)


    subjects = []
    grades = []
    # Get the best of each group
    try:
        de = fhs_subjects["Deutsch"]
        subjects.append(de)
        grades.append(s2g.pop(de))
        ma = fhs_subjects["Mathe"]
        subjects.append(ma)
        grades.append(s2g.pop(ma))
        bestof(fhs_subjects["NaWi"])
        bestof(fhs_subjects["Fremdsprachen"])
        bestof(fhs_subjects["BlockB"])
    except:
        raise Bug("Missing subject/grade")

    print("   1:", s2g)
    bestof(s2g)
    print("   1:", s2g)
    bestof(s2g)
    print("   1:", s2g)
    print("   subjects:", subjects)
    print("   grades:", grades)

    n5 = 0  # grades under 5 points
    e5 = 0  # eA-grades under 5 points
    z = False   # subject with 0 points?
    l5g3 = False    # >3 subjects under 5 points
    l5e2 = False    # >2 "eA"-subjects under 5 points
    for i, g in enumerate(grades): # check for 0 points and <5 points
        if g < 0.01:
            z = True
        elif g < 4.99:
            n5 += 1
            if indexes[subjects[i]] < 4:
                e5 += 1
    l5g3 = n5 > 3   # >3 subjects under 5 points
    l5e2 =  e5 > 2  # >2 "eA"-subjects under 5 points
    points20 = int(sum(grades[:4]) + 0.5)
    points35 = int(points20 + sum(grades[4:]) + 0.5)
    fields["sum"] = str(points35)
    points20fail = points20 < 20
    points35fail = points35 < 35

    print("&&&&&& fhs:", z, l5g3, l5e2, points20, points35)
    if z or l5g3 or l5e2 or points20fail or points35fail:
        return False
    if points35 >= 97:
        g1 = "1"
        g2 = "0"
    else:
        # Calculate final grade using a formula. To avoid rounding
        # errors, use integer arithmetic.
        g420 = 2380 - points35*20 + 21
        g1 = str(g420 // 420)
        g2 = str((g420 % 420) // 42)
    fields["Grade1"] = g1
    fields["Grade2"] = g2
    fields["GradeT"] = GRADE_TEXT[g1] + ", " + GRADE_TEXT[g2]
    fields["RESULT"] = "FHS: " + g1 + "," + g2

    print("&&&&&& fhs ok:", fields)
    return True
