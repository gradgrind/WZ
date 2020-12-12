# -*- coding: utf-8 -*-

"""
local/abitur_config.py

Last updated:  2020-12-12

Configuration for Abitur-grade handling.
====================================
"""

### Messages
_E_WRONG = "{n} Kurse mit „eA“ (erwartet: 3)"
_G_WRONG = "{n} schriftliche Kurse mit „gA“ (erwartet: 1)"
_M_WRONG = "{n} mündliche Kurse (erwartet: 4)"
_X_WRONG = "{n} mündliche Nachprüfungen (erwartet: 4)"
_X_ALONE = "Keine entsprechende schriftliche Prüfung für Fach {sid}"
_MULTISID = "Fach {sid} doppelt vorhanden"
_BAD_SID = "Unerwartetes Fach: {sid}"

from local.grade_config import UNCHOSEN

class AbiturError(Exception):
    pass


class AbiCalc:
    """Manage a mapping of all necessary grade components for an
    Abitur report.
    """
    _gradeText = {'0': 'null', '1': 'eins', '2': 'zwei', '3': 'drei',
            '4': 'vier', '5': 'fünf', '6': 'sechs', '7': 'sieben',
            '8': 'acht', '9': 'neun'
    }
#
    JA = {True: 'Ja', False: 'Nein'}
#
    def __init__(self, grade_table, pid):
        """<grade_table> is the <GradeTable> instance, <pid> the pupil id.

        a list of pairs: [(sid, grade), ...].
        <snames> is a subject-name mapping: {sid -> name}.
        The name can have a qualifier suffix ('| ...').
        """
        def get_name(sid):
            """Return subject name without possible suffix.
            """
            return grade_table.subjects[sid].split('|', 1)[0].rstrip()
#-
        self.grade_map = grade_table[pid]   # {sid -> grade}
        # Indexes for subjects and grades:
        e, g, m = 0, 3, 4
        xsids = []
        # Grade tags:
        self.sid2tag = {}
        sid2n = {}              # stripped sid (only e and g)
        self.tag2sid = {}
        self.tags = {}          # {tag -> value}
        for sid, grade in self.grade_map.items():
            if grade == UNCHOSEN:
                continue
            if sid.endswith('.e'):
                e += 1
                self.tags['SUBJECT_%d' % e] = get_name(sid)
                gtag = 'GRADE_%d' % e
                sid0 = sid[:-2]
                if sid0 in sid2n:
                    raise AbiturError(_MULTISID.format(sid = sid0))
                sid2n[sid0] = e
                self.set_editable_cell(gtag, grade)
                self.sid2tag[sid] = gtag
                self.tag2sid[gtag] = sid
            elif sid.endswith('.g'):
                g += 1
                self.tags['SUBJECT_%d' % g] = get_name(sid)
                gtag = 'GRADE_%d' % g
                sid0 = sid[:-2]
                if sid0 in sid2n:
                    raise AbiturError(_MULTISID.format(sid = sid0))
                sid2n[sid0] = g
                self.set_editable_cell(gtag, grade)
                self.sid2tag[sid] = gtag
                self.tag2sid[gtag] = sid
            elif sid.endswith('.m'):
                m += 1
                self.tags['SUBJECT_%d' % m] = get_name(sid)
                gtag = 'GRADE_%d' % m
                self.set_editable_cell(gtag, grade)
                self.sid2tag[sid] = gtag
                self.tag2sid[gtag] = sid
            elif sid.endswith('.x'):
                xsids.append((sid, grade))
            elif not sid.startswith('*'):
                raise AbiturError(_BAD_SID.format(sid = sid))
        # This must come after <sid2n> has been completed
        for sid, grade in xsids:
            try:
                n = sid2n[sid[:-2]]
            except KeyError as e:
                raise AbiturError(_X_ALONE.format(sid = sid)) from e
            gtag = 'GRADE_%d_m' % n
            self.set_editable_cell(gtag, grade)
            self.sid2tag[sid] = gtag
            self.tag2sid[gtag] = sid
        # Check for correct numbers of each type
        if e != 3:
            raise AbiturError(_E_WRONG.format(n = e))
        if g != 4:
            raise AbiturError(_G_WRONG.format(n = g - 3))
        if m != 8:
            raise AbiturError(_M_WRONG.format(n = m - 4))
        if len(xsids) != 4:
            raise AbiturError(_X_WRONG.format(n = len(xsids)))
#
    def value(self, tag):
        """Return the value in the given cell.
        """
        return self.tags[tag]
#
    def all_values(self):
        """Return a list of all tags and values: [(tag, value), ...].
        """
        return [(t, v) for t, v in self.tags.items()]
#
    def set_editable_cell(self, tag, value):
        """Enter value in the general <self.tags> mapping.
        """
        self.tags[tag] = value
#
    def get_all_grades(self):
        """Return a list of all (subject, grade) pairs, including the
        'UNCHOSEN' ones. This list does not include "special" fields.
        """
        grade_list = []
        for sid, grade in self.grade_map.items():   # {sid -> grade}
            if grade == UNCHOSEN:
                grade_list.append((sid, UNCHOSEN))
            elif sid[0] != '*':
                tag = self.sid2tag[sid]
                grade_list.append((sid, self.tags[tag]))
        return grade_list
#
    def calculate(self):
        """Perform all the calculations necessary for the grade editor
        AND the report form.
        The grades are available in the mapping <self.tags>.
        All entries are strings. They can be in the range '00' to '15',
        or '' (indicating that the grade is not yet available). The
        supplemental oral exam grades may also have the value '*', which
        indicates that the exam didn't / won't take place.
        Return the field values as a mapping: {field -> value (str)}.
        """
        fields = {}     # the result mapping, {field -> value (str)}

        ## process the grades -> averages, scaled averages, etc.
        scaled = []     # 8 scaled averages
        scaled14 = 0    # partial total, subjects 1 – 4
        scaled58 = 0    # partial total, subjects 5 – 8
        for n in range(1, 9):   # 1 – 8
            try:
                g = int(self.tags['GRADE_%d' % n])
            except:
                g = None
            if n < 5:
                factor = 4 if n == 4 else 6
                try:
                    gx = int(self.tags['GRADE_%d_m' % n])
                    s = (g + gx) * factor
                    scaled.append(s)
                    scaled14 += s
                    fields['SCALED_%d' % n] = str(s)
                    av2 = g + gx
                    av = str(av2 // 2)
                    if av2 % 2:
                        av += ',5'
                    fields['AVERAGE_%d' % n] = av
                except:
                    # If the extra grade is numerical, but the main
                    # grade not, treat the subject as ungraded.
                    if g == None:
                        scaled.append(None)
                        fields['SCALED_%d' % n] = ''
                        fields['AVERAGE_%d' % n] = ''
                    else:
                        s = g * factor * 2
                        scaled14 += s
                        scaled.append(s)
                        fields['SCALED_%d' % n] = str(s)
                        fields['AVERAGE_%d' % n] = str(g)
            elif g == None:
                scaled.append(None)
                fields['SCALED_%d' % n] = ''
                fields['AVERAGE_%d' % n] = ''
            else:
                s = g * 4
                scaled.append(s)
                scaled58 += s
                fields['SCALED_%d' % n] = str(s)
                fields['AVERAGE_%d' % n] = str(g)

        ## partial totals
        fields['TOTAL_1-4'] = str(scaled14)
        fields['TOTAL_5-8'] = str(scaled58)

        ## the pass checks
        ok = True
        # Check 1: none with 0 points
        for i in scaled:
            if i == 0:
                ok = False
                break
        fields['JA_1'] = self.JA[ok]
        # Check 2: at least two of first four >= 5 points
        n = 0
        for i in range(3):
            if scaled[i] >= 60:
                n += 1
        if scaled[3] >= 40:
            n += 1
        ja = n >= 2
        fields['JA_2'] = self.JA[ja]
        ok &= ja
        # Check 3: at least two of last four >= 5 points
        n = 0
        for i in range(4, 8):
            if scaled[i] >= 20:
                n += 1
        ja = n >= 2
        fields['JA_3'] = self.JA[ja]
        ok &= ja
        # Check 4: <scaled14> >= 220
        ja = scaled14 >= 220
        fields['JA_4'] = self.JA[ja]
        ok &= ja
        # Check 5: <scaled58> >= 80
        ja = scaled58 >= 80
        fields['JA_5'] = self.JA[ja]
        ok &= ja

        total = scaled14 + scaled58
        fields['SUM'] = str(total)

        # The final grade
        if ok:
            # Calculate final grade using a formula. To avoid rounding
            # errors, use integer arithmetic.
            g180 = (1020 - total)
            g1 = str (g180 // 180)
            if g1 == '0':
                g1 = '1'
                g2 = '0'
            else:
                g2 = str ((g180 % 180) // 18)
            fields['FINAL_GRADE'] = g1 + ',' + g2
            fields['PASS'] = 'true'
        else:
            fields['FINAL_GRADE'] = '–––'
            fields['PASS'] = 'false'
# Fachabi, etc?
        return fields

###

    def getFullGrades(self):
        """Return the full tag mapping for an Abitur report.
        """
        gmap = self.zgrades.copy()
        errors = []
        critical = []
        ### First the 'E' points
        eN = []
        n1, n2 = 0, 0
        for i in range(8):
            try:
                s = int(self.sngg[i][2])
            except:
                critical.append(_NO_GRADE % self.sngg[i][1])
                s = 0
            if i < 4:
                # written exam
                f = 4 if i == 3 else 6  # gA / eA
                try:
                    e = s + int(self.sngg[i][3])
                except:
                    e = s + s
                if e >= 10:
                    n1 += 1
                e *= f
            else:
                # oral exam
                e = 4 * s
                if e >= 20:
                    n2 += 1
            gmap["E%d" % (i+1)] = str(e)
            eN.append(e)
            if e == 0:
                errors.append(_NULL_ERROR % self.sngg[i][1])

        if critical:
            for e in critical:
                REPORT.Error(e)
            raise GradeError

        t1 = eN[0] + eN[1] + eN[2] + eN[3]
        gmap["TOTAL1"] = t1
        if t1 < 220:
            errors.append(_LOW1_ERROR)
        t2 = eN[4] + eN[5] + eN[6] + eN[7]
        gmap["TOTAL2"] = t2
        if t2 < 80:
            errors.append(_LOW1_ERROR)
        if n1 < 2:
            errors.append(_UNDER2_1_ERROR)
        if n2 < 2:
            errors.append(_UNDER2_2_ERROR)

        if errors:
            gmap["Grade1"] = "–––"
            gmap["Grade2"] = "–––"
            gmap["GradeT"] = "–––"
            for e in errors:
                REPORT.Warn(_FAILED, error=e)
            gmap["PASS"] = False
            return gmap

#TODO: What about Fachabi?

        # Calculate final grade using a formula. To avoid rounding
        # errors, use integer arithmetic.
        g180 = (1020 - t1 - t2)
        g1 = str (g180 // 180)
        if g1 == '0':
            g1 = '1'
            g2 = '0'
        else:
            g2 = str ((g180 % 180) // 18)
        gmap["Grade1"] = g1
        gmap["Grade2"] = g2
        gmap["GradeT"] = self._gradeText[g1] + ", " + self._gradeText[g2]
        gmap["PASS"] = True
        return gmap


#TODO
    @classmethod
    def FachAbiGrade (cls, points):
        """Use a formula to calculate "Abiturnote" (Waldorf/Niedersachsen).
        To avoid rounding errors, use integer arithmetic.
        """
        g420 = 2380 - points*20 + 21
        p420 = str (g420 // 420) + cls._dp + str ((g420 % 420) // 42)
        return p420
