# -*- coding: utf-8 -*-
"""
grade_handlers.py - last updated 2021-05-16

Handlers for special grade table entries.

==============================
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

########################################################################
"""

### Messages


### Constants
NO_AVERAGE = '–––'

########################################################################

import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

from fractions import Fraction

from local.base_config import DECIMAL_SEP
from local.grade_config import UNCHOSEN, NO_GRADE
from local.field_handlers import FieldMap, FieldHandler, HANDLERS, NONE

### +++++

class GradeMap(FieldMap):
    """This manages fields and their values for a grade table.
    """
    def __init__(self, gradetable, pid):
        self.gradetable = gradetable
        super().__init__(gradetable.pid2grade_data(pid))

####### ++++++++++++++++ The handlers ++++++++++++++++ #######

#WARNING: Be careful with transforming handlers. The saved value may not
# be the same as the displayed value!

class F_AVERAGE(FieldHandler):
    """Calculate the (weighted) average of the grades which specify this
    field as a target.
    """
    @classmethod
    def init(cls, htype, tag):
        h = super().init(htype, tag)
#TODO: How can I get at the source fields?!
        h['source_fields'] = '???'
        return h
#
    def __init__(self, field, data):
        self.source_fields = data['source_fields']
#
    def exec_(self, fieldmap, field, value, trap_empty):
        """output value == field value
        The field value will be updated if the source has changed.
        """
#TODO
        pass

class F_COMPOSITE(FieldHandler):
    """Calculate the (weighted) average of the grades which specify this
    field as a target. The result is a grade.
    """
    pass
#TODO


###

#??? This should probably be in the base module, but it is still incomplete!
class F_GRADE_SUBJECT(FieldHandler):
    """Handler for a slot accepting a subject name. The field tag should
    have the form "S.x.nn", where x is the subject-block tag (e.g. "1"
    or "B") and nn is a two digit number (e.g. 03). The nn part should
    start at 01 (for the first entry) and each subsequent field is then
    incremented by 1.
    There is an associated grade field having the form "G.x.nn", where
    x and nn are the same as in the subject field.
    The <exec_> method seeks matching subject-grade entries in the
    supplied data.
    """
#TODO
    def __init__(self, field, data):
        super().__init__(field, data)
        self.grade_field = 'G' + self.name[1:]
#
    def exec_(self, fieldmap, field, value, trap_empty):
        """output value may differ from field value:
        anything after '|' (if present) is stripped.
        If there is a fitting subject-grade entry, this will be
        entered in the corresponding grade field.
        """
        if value == None:
            # Get subject-grade data
#TODO: What about the subject name???
# It could come from the subjects mapping, if this is attached ...
            subject_block = self.wildmatch[0]
            for k, v in fieldmap.items():
                try:
                    s0, b = k.split('.', 1)
                except ValueError:
                    continue
                if b != subject_block:
                    continue
#TODO: I think this may be problematic because of reuse of fieldmap?
# presumably that can be cleared before starting?
                if k in fieldmap.subject_block_index:
                    continue

                fieldmap.subject_block_index[k] = self.wildmatch[1]

# Let's assume that v is a tuple (name, grade) ...
                fieldmap[field] = v[0]
                fieldmap[self.grade_field] = v[1]








            try:
                value = fieldmap[self.source_field]
            except KeyError:
                raise FieldHandlerError(_MAPFROM_BAD_FIELD.format(
                        field = self.name, source = self.source_field))



        fieldmap[self.grade_field] = value


        if (not value) and trap_empty:
            raise EmptyField
        try:
            return self.value_map[value]
        except KeyError:
            fieldmap[field] = NONE
            raise FieldHandlerError(_MAPFROM_BAD_VALUE.format(
                    field = self.name, value = value))
#
    def depends(self):
        return [self.source_field]
#
    def force_values(self, fieldmap):
        if self.source_field in fieldmap:
            return NONE   # dependent on existing field
        return [self.name, list(self.value_map)]

###

class Frac(Fraction):
    """A <Fraction> subclass with custom <truncate> and <round> methods
    returning strings.
    """
    def truncate(self, decimal_places = 0):
        if not decimal_places:
            return str(int(self))
        v = int(self * 10**decimal_places)
        sval = ("{:0%dd}" % (decimal_places+1)).format(v)
        return (sval[:-decimal_places] + DECIMAL_SEP + sval[-decimal_places:])
#
    def round(self, decimal_places = 0):
        f = Fraction(1,2) if self >= 0 else Fraction(-1, 2)
        if not decimal_places:
            return str(int(self + f))
        v = int(self * 10**decimal_places + f)
        sval = ("{:0%dd}" % (decimal_places+1)).format(v)
        return (sval[:-decimal_places] + DECIMAL_SEP + sval[-decimal_places:])

###

def average(sid2weight, sid2grade, punkte = False, composite = False):
    """Calculate the average of the grades for the subjects in <sid2weight>,
    taking their weightings into account.
    Assume that the input data is valid.
    Non-numerical grades are ignored.
    If <punkte> is true, the grades use the 00 – 15 point scale, otherwise
    normal "Noten" (6 – 1, with +/-).
    If <composite> is true, the result will be a grade, taking + and -
    into account.
    If <composite> is false, the average will be calculated to 2 decimal
    places. Note that here + and - are ignored.
    Note that rounding is advantageous (4.5 -> 5) on the 00 – 15 point
    scale and disadvantageous on the normal "Notenskala", because on this
    scale a larger number is a lower grade. It is not clear whether
    making the rounding on the normal scale advantageous would conform
    to the regulations.
    Also it is not clear that the calculation of the "composites" should
    be allowed to use the + and - tags. As all grades appear on the
    reports without these, it may be confusing in those cases where the
    calculated composite grade would be different (with/without + and -).
    """
    asum = 0
    ai = 0
    if punkte:
        conv = Punkte_converter
    elif composite:
        conv = Noten_converter
    else:
        conv = Noten_converter_strip
    for sid, w in sid2weight.items():
        g = sid2grade.get(sid) or UNCHOSEN
        gi = conv.tonum(g)
        if gi < 0:
            continue
        asum += gi * w
        ai += w
    if ai:
        frac = Frac(asum, ai)
        if composite:
            # Return a grade
            n, d = frac.numerator, frac.denominator
            i = n // d
            if (n % d) * 2 >= d:
                # round up
                i += 1
            return conv.tograde(i)
        return frac.round(2)
    else:
        return NO_GRADE if composite else NO_AVERAGE

###

class Noten_converter:
    _g2num = {
        '1+': 15, '1': 14, '1-': 13,
        '2+': 12, '2': 11, '2-': 10,
        '3+': 9, '3': 8, '3-': 7,
        '4+': 6, '4': 5, '4-': 4,
        '5+': 3, '5': 2, '5-': 1,
        '6': 0,
        'nt': -1, 'nb': -1, 't': -1, UNCHOSEN: -1, NO_GRADE: -1#, 'ne': -1
    }
    _num2g = ['6','5', '5',  '5+', '4-', '4', '4+', '3-', '3', '3+',
            '2-', '2', '2+', '1-', '1', '1+']
#
    @classmethod
    def tonum(cls, grade):
        return cls._g2num[grade]
#
    @classmethod
    def tograde(cls, num):
        if num < 0 or num > 15:
            raise ValueError
        return cls._num2g[num]

###

class Punkte_converter(Noten_converter):
    _g2num = {
        '15': 15, '14': 14, '13': 13,
        '12': 12, '11': 11, '10': 10,
        '09': 9, '08': 8, '07': 7,
        '06': 6, '05': 5, '04': 4,
        '03': 3, '02': 2, '01': 1,
        '00': 0,
        'nt': -1, 'nb': -1, 't': -1, UNCHOSEN: -1, NO_GRADE: -1#, 'ne': -1
    }
    _num2g = ['0','01', '02',  '03', '04', '05', '06', '07', '08', '09',
            '10', '11', '12', '13', '14', '15']

###

class Noten_converter_strip:
    _g2num = {
        '1+': 1, '1': 1, '1-': 1,
        '2+': 2, '2': 2, '2-': 2,
        '3+': 3, '3': 3, '3-': 3,
        '4+': 4, '4': 4, '4-': 4,
        '5+': 5, '5': 5, '5-': 5,
        '6': 6,
        'nt': -1, 'nb': -1, 't': -1, UNCHOSEN: -1, NO_GRADE: -1#, 'ne': -1
    }
    _num2g = ['6','5', '5',  '5+', '4-', '4', '4+', '3-', '3', '3+',
            '2-', '2', '2+', '1-', '1', '1+']
#
    @classmethod
    def tonum(cls, grade):
        return cls._g2num[grade]
#
    @classmethod
    def tograde(cls, num):
        if num < 0 or num > 15:
            raise ValueError
        return cls._num2g[num]

###

#TODO ... should be possible to use the above averaging code
    def composite_calc(self, sdata):
        """Recalculate a composite grade.
        <sdata> is the subject-data for the composite, the (weighted)
        average of the components will be calculated, if possible.
        If there are no numeric grades, choose NO_GRADE, unless all
        components are UNCHOSEN (in which case also the composite will
        be UNCHOSEN).
        """
#TODO: Now that I can unchoose composites, NO_GRADE could be used here too.
        asum = 0
        ai = 0
        non_grade = UNCHOSEN
        for csid, weight in sdata['COMPONENTS'].items():
            gi = self.i_grade[csid]
            if gi >= 0:
                ai += weight
                asum += gi * weight
            elif self[csid] != UNCHOSEN:
                non_grade = NO_GRADE
        sid = sdata['SID']
        if ai:
            g = Frac(asum, ai).round()
            self[sid] = self.grade_format(g)
            self.i_grade[sid] = int(g)
        else:
            self[sid] = non_grade

#---------------------------
HANDLERS.update({k[2:]: v for k, v in locals().items() if k[:2] == 'F_'})

#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    _year = '2016'
    from core.base import init
    init()

    sw = {'En': 1, 'De':1, 'Ma':2}
    sg = {'En': '2+', 'Ma': '4-'}
    print("AVERAGE GRADE:", average(sw, sg, punkte = False, composite = True))
    print("Math. AVERAGE:", average(sw, sg, punkte = False, composite = False))
