"""
core/classes.py - last updated 2022-06-17

Manage class data.

=+LICENCE=================================
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
=-LICENCE=================================
"""

########################################################################

if __name__ == "__main__":
    import sys, os

    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    #    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))

T = TRANSLATIONS("core.classes")

### +++++

from typing import NamedTuple

from core.db_management import (
    open_database,
    db_read_fields,
    read_pairs
)

### -----


class ClassData(NamedTuple):
    klass: str
    name: str
    divisions: list[list[str]]
    classroom: str
    tt_data: dict


class Classes(dict):
    def __init__(self):
        super().__init__()
        # ?    open_database()
        for klass, name, divisions, classroom, tt_data in db_read_fields(
            "CLASSES",
            ("CLASS", "NAME", "DIVISIONS", "CLASSROOM", "TT_DATA"),
            sort_field="CLASS"
        ):
            # Parse groups
            divlist = []
            if divisions:
                for div in divisions.split("|"):
                    # print("???", klass, repr(div))
                    groups = div.split()
                    if groups:
                        divlist.append(groups)
                    else:
                        SHOW_ERROR(T["INVALID_GROUP_FIELD"].format(klass=klass))
            self[klass] = ClassData(
                klass=klass,
                name=name,
                divisions=divlist,
                classroom=classroom,
                tt_data=dict(read_pairs(tt_data)),
            )

    def get_class_list(self, skip_null=True):
        classes = []
        for k, data in self.items():
            if k == "--" and skip_null:
                continue
            classes.append((k, data.name))
        return classes

    def get_classroom(self, klass):
        return self[klass].classroom


def build_group_data(divisions):
    """Process a class's group (GRP) field to get a list of groups and
    minimal subgroups.
    Return (groups, minimal subgroups)
    """
    groups = set()
    impossible_partners = {}    # {group -> {incompatible groups}}
    # Collect groups and build map (<impossible_partners>) giving all
    # other groups which are incompatible with each group in a "dot-join".
    divn = 0
    for div in divisions:
        for g in div:
            groups.add(g)
            snew = set(div) - {g}
            try:
                impossible_partners[g] |= snew
            except KeyError:
                impossible_partners[g] = snew
        divn += 1
    # Collect minimal subgroups
    cross_terms = [set()]
    for div in divisions:
        __cross_terms = []
        for g in div:
            for ct in cross_terms:
                if g in ct:
                    __cross_terms.append(ct)
                elif not (ct & impossible_partners[g]):
                    gg = set(g.split("."))
                    if len(gg) > 1:
                        for gx in gg:
                            try:
                                nopairx = impossible_partners[gx]
                            except KeyError:
                                continue
                            if (ct & nopairx):
                                break
                        else:
                            __cross_terms.append(ct | gg)
                    else:
                        __cross_terms.append(ct | gg)
        cross_terms = __cross_terms
        #print("\n???", cross_terms)
    print("\nXXX", impossible_partners)
    print("\n§GROUPS:", sorted(groups))
    print("\n§XTERMS:", cross_terms)

    print("§§§§§§§§§§§§§§§§§§§§§§§§§")
    all_groups = {}
    ndiv = 0
    divsets = []
    for div in divisions:

        divset = set(div)
        for si in divsets:
            isect = si & divset
            if isect:
                print("???", si, divset)

        for g in div:
            try:
                all_groups[g].append(divn)
            except KeyError:
                all_groups[g] = [divn]
                continue


        divsets.append(divset)
        ndiv += 1
    print("§§§§§§§§§§§§§§§§§§§§§§§§§")

    return sorted(groups), [frozenset(ct) for ct in cross_terms]


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    _divs = [("A", "B"), ("G", "R"), ("A", "X", "Y")]
    _divs = [("A", "B"), ("A", "X", "Y"), ("B", "P", "Q")]
    _divs = [("A", "B"), ("A", "I", "J"), ("A", "X", "Y"), ("B", "P", "Q")]
    _divs = [("A", "B"), ("A", "I", "J"), ("C", "D"), ("C", "P", "Q")]
    #_divs = [("A", "B"), ("G", "R"), ("A", "B.G", "B.R")]
    #_divs = [("A", "B.G", "B.R"), ("G", "R"), ("A", "B")]
    #_divs = [("G", "R"), ("A", "B.G", "B.R"), ("A", "B"), ("I", "II", "III")]

    #_divs = [("A", "B", "C"), ("A", "X", "Y", "Z")]
    # What about specifying subgroups? e.g. B.G and B.R ... perhaps A.G, A.R
    # G -> A+B.G, B -> B.G+B.R

    print("\nGROUP DIVISIONS:", _divs, "->")
    groups, minsubgroups = build_group_data(_divs)
    print("\n ... Groups:", groups)
    print("\n ... Atoms:", minsubgroups)

    quit(0)

    print("\n -------------------------------\n")
    print("CLASS DATA:")

    open_database()
    _classes = Classes()
    for cdata in _classes.values():
        print("\n", cdata)

    print("\n -------------------------------\n")

    for k, v in _classes.get_class_list(False):
        print(f" ::: {k:6}: {v} // {_classes.get_classroom(k)}")
