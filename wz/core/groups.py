# -*- coding: utf-8 -*-
"""

core/groups.py

Last updated:  2021-09-25

Read the groups from the class courses table.


=+LICENCE=============================
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

=-LICENCE========================================
"""


CLASS_DIVISIONS = {}
ATOMIC_LISTS = {}
ELEMENT_GROUPS = {}
EXTENDED_GROUPS = {}
CLASS_GROUPS = {}
GROUPSETS_CLASS = {}


def read_groups(klass, raw_groups):
    """Parse the GROUPS data for the given class.
    This is a '|'-separated list of mutually exclusive class divisions.
    A division is a space-separated list of groups. These groups
    may contain '.' characters, in which case they are intersections
    of "atomic" groups (no dot). Neither these atomic groups nor the
    dotted intersections may appear in more than one division.
    A division might be "A.G B.G B.R".
    As the class divisions must be given as a set of non-intersecting
    groups, the atomic (undotted) groups may need to be expressed
    (for the timetable) as a combination of dotted groups, e.g. B as
    "B.G,B.R".
    """
    if klass.startswith('XX'):
        return
    ### Add declared class divisions (and their groups).
    divisions = [['*']]     # start with the whole class ('*')
    divs = []
    atomic_groups = [frozenset()]
    all_atoms = set()
    for glist in raw_groups.split('|'):
        dgroups = glist.split()
        divisions.append(dgroups)
        division = [frozenset(item.split('.')) for item in dgroups]
        divs.append(division)
        ag2 = []
        for item in atomic_groups:
            for item2 in division:
                all_atoms |= item2
                ag2.append(item | item2)
        atomic_groups = ag2
    CLASS_DIVISIONS[klass] = divisions
    #print("§§§ DIVISIONS:", klass, divisions)
    al = ['.'.join(sorted(ag)) for ag in atomic_groups]
    al.sort()
    ATOMIC_LISTS[klass] = al  # All (dotted) atomic groups
    #print(f'$$$ "Atomic" groups in class {klass}:', al)
    ### Make a mapping of single, undotted groups to sets of dotted
    ### atomic groups.
    gmap = {a: frozenset(['.'.join(sorted(ag))
                    for ag in atomic_groups if a in ag])
            for a in all_atoms}
    #print(f'$$$ "Element" groups in class {klass}:', gmap)
    ELEMENT_GROUPS[klass] = gmap
    ### The same for the dotted groups from the divisions (if any)
    xmap = {}
    for division in divs:
        for item in division:
            istring = '.'.join(sorted(item))
            if istring not in gmap:
                xmap[istring] = frozenset.intersection(
                        *[gmap[i] for i in item])
    #print(f'$$$ "Extended" groups in class {klass}:', xmap)
    EXTENDED_GROUPS[klass] = xmap
    make_class_groups(klass)
#
def make_class_groups(klass):
    """Build the entry for <CLASS_GROUPS> for the given class.
    Also build the reversed mapping <GROUPSETS_CLASS>.
    This method may need to be overriden in the back-end.
    """
    gmap = {}
    for _map in ELEMENT_GROUPS[klass], EXTENDED_GROUPS[klass]:
        for k, v in _map.items():
            gmap[k] = frozenset([f'{klass}.{ag}' for ag in v])
    CLASS_GROUPS[klass] = gmap
    # And now a reverse map, avoiding duplicate values (use the
    # first occurrence, which is likely to be simpler)
    reversemap = {}
    for k, v in gmap.items():
        if v not in reversemap:
            reversemap[v] = f'{klass}.{k}'
    GROUPSETS_CLASS[klass] = reversemap
    # Add "whole class" elements to both mappings
    _whole_class = klass
    fs_whole = frozenset([_whole_class])
    reversemap[fs_whole] = _whole_class
    all_groups = frozenset([f'{klass}.{ag}'
            for ag in ATOMIC_LISTS[klass]])
    if all_groups:
        gmap['*'] = all_groups
        reversemap[all_groups] = _whole_class
    else:
        gmap['*'] = fs_whole
#    print("+++", klass, gmap)
#    print("---", klass, reversemap)
#
def group_classgroups(klass, group):
    """Return the (frozen)set of "full" groups for the given class
    and group. The group may be dotted. Initially only the "elemental"
    groups, including the full class, are available, but dotted
    groups will be added if they are not already present.
    This method may need to be overridden in the back-end (see
    <make_class_groups>)
    """
    cg = CLASS_GROUPS[klass]
    try:
        return cg[group]
    except KeyError:
        pass
    gsplit = group.split('.')
    if len(gsplit) > 1:
        group = '.'.join(sorted(gsplit))
        try:
            return cg[group]
        except KeyError:
            pass
        try:
            gset = frozenset.intersection(*[cg[g] for g in gsplit])
        except KeyError:
            pass
        else:
            if gset:
                # Add to group mapping
                cg[group] = gset
                # and to reverse mapping
                grev = GROUPSETS_CLASS[klass]
                if gset not in grev:
                    # ... if there isn't already an entry
                    grev[gset] = f'{klass}.{group}'
                return gset
    raise TT_Error(_UNKNOWN_GROUP.format(klass = klass, group = group))
#
def split_class_group(group):
    """Given a "full" group (with class), return class and group
    separately.
    This function may need to be overridden in the back-end (see
    <make_class_groups>)
    """
    k_g = group.split('.', 1)
    return k_g if len(k_g) == 2 else (group, '')


if __name__ == '__main__':
    def lprint(title, l):
        print(f"\n{title}:")
        for v in l:
            print(f"  {v}")
    def dprint(title, d):
        print(f"\n{title}:")
        for k, v in d.items():
            print(f"  {repr(k)}: {repr(v)}")
    __class = "12G"
    read_groups(__class, "A.G B.G B.R | I II III")
#TODO: The group "B.G" is not available in CLASS_GROUPS and GROUPSETS_CLASS
# (A.G is the same as A and B.R is the same as R – these are present)
    lprint("CLASS_DIVISIONS", CLASS_DIVISIONS[__class])
    lprint("ATOMIC_LISTS", ATOMIC_LISTS[__class])
    dprint("ELEMENT_GROUPS", ELEMENT_GROUPS[__class])
    dprint("CLASS_GROUPS", CLASS_GROUPS[__class])
    dprint("GROUPSETS_CLASS", GROUPSETS_CLASS[__class])
