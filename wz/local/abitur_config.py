# -*- coding: utf-8 -*-

"""
local/abitur_config.py

Last updated:  2021-03-29

Configuration for Abitur-grade handling.
====================================
"""

### Configuration
_GW = ('Ges',)     # Geschichte / Politik-Wirtschaft / Erdkunde
_NW = ('Bio', 'Ph', 'Ch')   # Naturwissenschaften
_FS = ('En', 'Fr')  # Fremdsprachen

### Messages
_E_WRONG = "{n} Kurse mit „eA“ (erwartet: 3)"
_G_WRONG = "{n} schriftliche Kurse mit „gA“ (erwartet: 1)"
_M_WRONG = "{n} mündliche Kurse (erwartet: 4)"
_X_WRONG = "{n} mündliche Nachprüfungen (erwartet: 4)"
_X_ALONE = "Keine entsprechende schriftliche Prüfung für Fach {sid}"
_MULTISID = "Fach {sid} doppelt vorhanden"
_BAD_SID = "Unerwartetes Fach: {sid}"

from local.grade_config import UNCHOSEN#, NO_GRADE

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
    @staticmethod
    def subjects(grade_table):
        """Tweak to add additional (subject) entries for Abitur results.
        """
        sdmap = {}
        smap = {}
        for sid, sdata in grade_table.sid2subject_data.items():
            sdmap[sid] = sdata
            smap[sid] = sdata.name
            if sid.endswith('.e') or sid.endswith('.g'):
                new_sdata = sdata._replace(
                        sid = sdata.sid[:-1] + 'x',
# <tids> must have a value, otherwise it will not be passed by the
# composites filter, but is this alright? (rather ['X']?)
                        tids = 'X',
                        composite = None,
                        report_groups = None,
                        name = sdata.name.split('|', 1)[0] + '| nach'
                    )
                sdmap[new_sdata.sid] = new_sdata
                smap[new_sdata.sid] = new_sdata.name
        grade_table.sid2subject_data = sdmap
        grade_table.subjects = smap
#
    def __init__(self, grade_table, pid):
        """<grade_table> is the <GradeTable> instance, <pid> the pupil id.
        """
        def get_name(sid):
            """Return subject name without possible suffix.
            """
            return grade_table.subjects[sid].split('|', 1)[0].rstrip()
        #
        self.grade_map = grade_table[pid]   # {sid -> grade}
        # Indexes for subjects and grades:
        e, g, m = 0, 3, 4
        xsids = []
        # Grade tags:
        self.sid2tag = {}
        self.sid2i   = {}       # {stripped-sid -> index}
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
                if sid0 in self.sid2i:
                    raise AbiturError(_MULTISID.format(sid = sid0))
                self.sid2i[sid0] = e
                self.set_editable_cell(gtag, grade)
                self.sid2tag[sid] = gtag
                self.tag2sid[gtag] = sid
            elif sid.endswith('.g'):
                g += 1
                self.tags['SUBJECT_%d' % g] = get_name(sid)
                gtag = 'GRADE_%d' % g
                sid0 = sid[:-2]
                if sid0 in self.sid2i:
                    raise AbiturError(_MULTISID.format(sid = sid0))
                self.sid2i[sid0] = g
                self.set_editable_cell(gtag, grade)
                self.sid2tag[sid] = gtag
                self.tag2sid[gtag] = sid
            elif sid.endswith('.m'):
                m += 1
                self.tags['SUBJECT_%d' % m] = get_name(sid)
                gtag = 'GRADE_%d' % m
                sid0 = sid[:-2]
                if sid0 in self.sid2i:
                    raise AbiturError(_MULTISID.format(sid = sid0))
                self.sid2i[sid0] = m
                self.set_editable_cell(gtag, grade)
                self.sid2tag[sid] = gtag
                self.tag2sid[gtag] = sid
            elif sid.endswith('.x'):
                xsids.append((sid, grade))
            elif sid.startswith('*'):
                self.tags[sid] = grade
            else:
                raise AbiturError(_BAD_SID.format(sid = sid))
        # This must come after <self.sid2i> has been completed
        nxsids = 0
        for sid, grade in xsids:
            try:
                n = self.sid2i[sid[:-2]]
                if int(n) >= 5:
                    self.grade_map[sid] = UNCHOSEN
                    continue
            except KeyError as e:
                raise AbiturError(_X_ALONE.format(sid = sid)) from e
            gtag = 'GRADE_%d_m' % n
            self.set_editable_cell(gtag, grade)
            self.sid2tag[sid] = gtag
            self.tag2sid[gtag] = sid
            nxsids += 1
        # Check for correct numbers of each type
        if e != 3:
            raise AbiturError(_E_WRONG.format(n = e))
        if g != 4:
            raise AbiturError(_G_WRONG.format(n = g - 3))
        if m != 8:
            raise AbiturError(_M_WRONG.format(n = m - 4))
        if nxsids != 4:
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
        supplemental oral exam grades may also have the value <NO_GRADE>,
        which indicates that the exam didn't / won't take place.
        Return the field values as a mapping: {field -> value (str)}.
        """
        fields = {}     # the result mapping, {field -> value (str)}

        ## process the grades -> averages, scaled averages, etc.
        scaled = []     # 8 scaled averages
        scaled14 = 0    # partial total, subjects 1 – 4
        scaled58 = 0    # partial total, subjects 5 – 8
        complete = True # flag for "all grades present"
        for n in range(1, 9):   # 1 – 8
            try:
                g = int(self.tags['GRADE_%d' % n])
            except:
                g = None
                complete = False
            if n < 5:
                factor = 4 if n == 4 else 6
                _gx = self.tags['GRADE_%d_m' % n]
                try:
                    gx = int(_gx)
                    s = (g + gx) * factor
                    scaled.append(s)
                    scaled14 += s
                    fields['SCALED_%d' % n] = str(s)
                    _av2 = g + gx
                    _av = _av2 // 2
                    if _av2 % 2:
                        fields['AVERAGE_%d' % n] = str(_av) + ',5'
                        fields['AVER_%d' % n] = str(_av + 1).zfill(2)
                    else:
                        av = str(_av)
                        fields['AVERAGE_%d' % n] = av
                        fields['AVER_%d' % n] = av.zfill(2)
                except:
                    # Both fields must be non-empty.
                    if g == None or not _gx:
                        complete = False
                        scaled.append(None)
                        fields['SCALED_%d' % n] = ''
                        fields['AVERAGE_%d' % n] = ''
                        fields['AVER_%d' % n] = ''
                    else:
                        s = g * factor * 2
                        scaled14 += s
                        scaled.append(s)
                        _g = str(g)
                        fields['SCALED_%d' % n] = str(s)
                        fields['AVERAGE_%d' % n] = _g
                        fields['AVER_%d' % n] = _g.zfill(2)
            elif g == None:
                scaled.append(None)
                fields['SCALED_%d' % n] = ''
                fields['AVERAGE_%d' % n] = ''
                fields['AVER_%d' % n] = ''
            else:
                s = g * 4
                scaled.append(s)
                scaled58 += s
                _g = str(g)
                fields['SCALED_%d' % n] = str(s)
                fields['AVERAGE_%d' % n] = _g
                fields['AVER_%d' % n] = _g.zfill(2)

        ## partial totals
        fields['s1_4'] = str(scaled14)
        fields['s5_8'] = str(scaled58)

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
            if scaled[i] and scaled[i] >= 60:
                n += 1
        if scaled[3] and scaled[3] >= 40:
            n += 1
        ja = n >= 2
        fields['JA_2'] = self.JA[ja]
        ok &= ja
        # Check 3: at least two of last four >= 5 points
        n = 0
        for i in range(4, 8):
            if scaled[i] and scaled[i] >= 20:
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
        fields['FINAL_GRADE'] = '–––'
        if complete:
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
                fields['Note1'] = g1
                fields['Note2'] = g2
                fields['Note'] = g1 + ',' + g2
                fields['NoteT'] = self._gradeText[g1] + ', ' + \
                        self._gradeText[g2]
                fields['FINAL_GRADE'] = g1 + ',' + g2
                fields['REPORT_TYPE'] = 'Abi'
            elif self.fhs(fields):
                fields['REPORT_TYPE'] = 'FHS'
            else:
                fields['REPORT_TYPE'] = 'X'
        else:
            fields['REPORT_TYPE'] = None
        self.calc_map = fields
        return fields
#
    def fhs(self, fields):
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
        s2g = {s: int(fields['AVER_%d' % i]) for s, i in self.sid2i.items()}
        subjects = []
        grades = []
        # Get the best of each group
        try:
            subjects.append('De')
            grades.append(s2g.pop('De'))
            subjects.append('Ma')
            grades.append(s2g.pop('Ma'))
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
        fields['sum'] = str(points35)
        if points20 < 20:
            return False
        if points35 < 35:
            return False
        # Calculate final grade using a formula. To avoid rounding
        # errors, use integer arithmetic.
        g420 = 2380 - points35*20 + 21
        g1 = str(g420 // 420)
        g2 = str((g420 % 420) // 42)
        fields['Note1'] = g1
        fields['Note2'] = g2
        fields['NoteT'] = self._gradeText[g1] + ', ' + self._gradeText[g2]
        fields['FINAL_GRADE'] = 'FHS: ' + g1 + ',' + g2
        return True
