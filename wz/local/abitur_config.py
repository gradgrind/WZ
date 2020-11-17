# -*- coding: utf-8 -*-

"""
local/abitur_config.py

Last updated:  2020-11-17

Configuration for Abitur-grade handling.
====================================
"""

_TOO_MANY_E = "Zu viele Kurse mit „eA“"
_NO_X = "Kurs „{sid}“ fehlt"
_TOO_FEW_E = "„eA“-Kurse fehlen"
_TOO_MANY_G = "Zu viele schriftliche Kurse mit „gA“"
_NO_G = "Kein schriftlicher Kurs mit „gA“"
_TOO_MANY_M = "Zu viele mündliche Kurse"
_TOO_FEW_M = "Mündliche Kurse fehlen"
_EXCESS_SUBJECTS = "Unerwartete Fächer: „{sids}“"

def check_subjects(grades):
    """<grades> is a list of (sid, grade) pairs.
    Check that the subjects are correct for the abitur exams.
    Note that the order of the subjects is important: e e e g m m m m.
    """
    sidset = {sid for sid, _ in grades}    # for finding excess entries
    e = 0   # expect 3 sids with '.e'
    g = 0   # expect 1 sid with '.g'
    m = 0   # expect 4 sids with '.m'
    for sid, _ in grades:
        if sid.endswith('.e'):
            if e > 2:
                return _TOO_MANY_E
            e += 1
            sidset.remove(sid)
            sidx = sid[:-1] + 'x'
            try:
                sidset.remove(sidx)
            except KeyError:
                return _NO_X.format(sid = sidx)
        elif sid.endswith('.g'):
            if e != 3:
                return _TOO_FEW_E
            if g > 0:
                return _TOO_MANY_G
            g += 1
            sidset.remove(sid)
            sidx = sid[:-1] + 'x'
            try:
                sidset.remove(sidx)
            except KeyError:
                return _NO_X.format(sid = sidx)
        elif sid.endswith('.m'):
            if g != 1:
                return _NO_G
            if m > 3:
                return _TOO_MANY_M
            m += 1
            sidset.remove(sid)
    if m != 4:
        return _TOO_FEW_M
    if sidset:
        return _EXCESS_SUBJECTS.format(sids = ', '.join(sidset))
    return None
