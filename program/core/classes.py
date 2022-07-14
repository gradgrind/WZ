"""
core/classes.py - last updated 2022-07-10

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

from typing import NamedTuple, Optional

from core.db_access import open_database, db_read_fields, read_pairs

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
        self.__group_info = {}
        # ?    open_database()
        for klass, name, divisions, classroom, tt_data in db_read_fields(
            "CLASSES",
            ("CLASS", "NAME", "DIVISIONS", "CLASSROOM", "TT_DATA"),
            sort_field="CLASS",
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
        if klass == "--":
            raise Bug("Empty class has no classroom")
        return self[klass].classroom

    def group_info(self, klass):
        if klass == "--":
            raise Bug("Empty class has no groups")
        try:
            return self.__group_info[klass]
        except KeyError:
            pass
        info = build_group_data(self[klass].divisions)
        self.__group_info[klass] = info
        return info


def build_group_data(divisions):
    """Process the class divisions to get a list of groups,
    minimal subgroups, independent divisions, group mapping appropriate
    to the independent divisions.
    Return the results as a <dict>.
    Internally groups are handled as <frozensets>, but the results use
    dotted strings.
    """

    def group2string(group):
        return ".".join(sorted(group))

    def groups2stringlist(groups):
        return sorted([group2string(g) for g in groups])

    results = {}
    groups = set()
    impossible_partners = {}  # {group -> {incompatible groups}}
    # Collect groups and build map (<impossible_partners>) giving all
    # other groups which are incompatible with each group in a "dot-join"
    # (an intersection).

    # Build "frozensets" of the member groups, splitting dotted items.
    divsets = []
    for div in divisions:
        gsets = set()
        for g in div:
            gset = frozenset(g.split("."))
            gsets.add(gset)
            # Add to list of "acceptable" groups
            groups.add(gset)
        divsets.append(gsets)
        # Extend the sets of mutually incompatible groups
        for gset in gsets:
            snew = gsets.copy()
            snew.remove(gset)
            try:
                impossible_partners[gset] |= snew
            except KeyError:
                impossible_partners[gset] = snew
    # Cycle until only independent divisions remain
    independent_divs = []
    while divsets:
        this_div = divsets.pop()
        independent = True
        for i in range(len(divsets)):
            idiv = divsets[i]
            cross_set = set()
            for gset1 in this_div:
                # print("§§ -1-", gset1)
                forbidden1 = impossible_partners.get(gset1) or set()
                for gset2 in idiv:
                    # print("§§ -2-", gset2)
                    addgroup = True
                    # If partner is subset of forbidden group, not independent
                    for f in forbidden1:
                        if gset2 >= f:
                            # ">=" is correct: as far as the members are
                            # concerned A.B is a subset of A.
                            independent = False
                            addgroup = False
                            break
                    if addgroup:
                        for f in impossible_partners.get(gset2) or set():
                            if gset1 >= f:
                                # ">=" is correct: see above.
                                independent = False
                                addgroup = False
                                break
                        if addgroup:
                            # print("§§ -3-", gset1 | gset2)
                            cross_set.add(gset1 | gset2)
            if not independent:
                break
        if independent:
            independent_divs.append(this_div)
        else:
            # Remove idiv
            del divsets[i]
            divsets.append(cross_set)
            # Start again ...
            # print("§§++ divsets:", divsets)
    # Collect minimal subgroups
    cross_terms = [set()]
    for div in independent_divs:
        __cross_terms = []
        for g in div:
            for ct in cross_terms:
                __cross_terms.append(ct | g)
        cross_terms = __cross_terms
        # print("\n???", cross_terms)
    # print("\nXXX", impossible_partners)

    # Simplify the division elements ...
    # print("\n§§ independent_divs:")
    __independent_divs = []
    gmap = {}
    for d in independent_divs:
        __gmap = {}
        gmod = {}
        for g in groups:
            glist = []
            for gd in d:
                if g == gd:
                    # print("?????==", ".".join(sorted(g)))
                    __gmap[g] = [g]
                    glist.clear()
                    break
                elif g < gd:
                    glist.append(gd)
            if glist:
                if len(glist) == 1:
                    # print("????!!", g, glist)
                    gmod[glist[0]] = g
                __gmap[g] = glist
        if __gmap:
            # print("?????", d, "-->", __gmap)
            for g, l in __gmap.items():
                ll = [gmod.get(gx) or gx for gx in l]
                # print("????XX", g, "->", ll, "<<", l, ">>")
                gmap[g] = ll
        __independent_divs.append([gmod.get(g) or g for g in d])
        # print(" +++", __independent_divs)
    idivs = [groups2stringlist(groups) for groups in __independent_divs]
    idivs.sort()
    gmapl = [
        (group2string(g), groups2stringlist(groups))
        for g, groups in gmap.items()
    ]
    gmapl.sort()
    return {
        "INDEPENDENT_DIVISIONS": idivs,
        "GROUP_MAP": dict(gmapl),
        "GROUPS": groups2stringlist(groups),
        "MINIMAL_SUBGROUPS": groups2stringlist(cross_terms),
    }


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    # _divs = [("A", "B"), ("G", "R"), ("A", "X", "Y")]
    # _divs = [("A", "B"), ("G", "R"), ("A", "G")]
    # _divs = [("A", "B", "C"), ("A", "R"), ("B", "S")]
    # _divs = [("A", "B"), ("A", "X", "Y"), ("B", "P", "Q")]
    # _divs = [("A", "B"), ("A", "I", "J"), ("A", "X", "Y"), ("B", "P", "Q")]
    # _divs = [("A", "B"), ("A", "I", "J"), ("C", "D"), ("C", "P", "Q")]
    # _divs = [("A", "B"), ("G", "R"), ("A", "B.G", "B.R")]
    # _divs = [("A", "B.G", "B.R"), ("G", "R"), ("A", "B")]
    # _divs = [("A", "B.G", "R"), ("G", "R")]
    # _divs = [("A", "B.G", "R"), ("X", "Y")]
    # _divs = [("A", "B.G", "R"), ("G", "R"), ("A", "B")]
    # _divs = [("A.G", "A.R", "B.G", "B.R"), ("G", "R")]
    # _divs = [("A.G", "A.R", "B.G", "B.R"), ("A", "B")]
    # _divs = [("A.G", "A.R", "B.G", "B.R"), ("A", "B"), ("G", "R")]
    # _divs = [("A", "B"), ("A", "B.G", "B.R")]
    # _divs = [("A", "B"), ("G", "R"), ("A.X", "A.Y", "G.P", "G.Q")]
    # _divs = [("A", "M"), ("A.X", "N")]
    # _divs = [("A", "M"), ("A.X", "N"), ("G", "R")]
    # _divs = [("A", "B.X"), ("P", "B.Y")]
    # _divs = [("A", "B", "C"), ("A", "X", "Y", "Z")]
    # _divs = [("G", "R"), ("A", "B.G", "B.R"), ("A", "B"), ("I", "II", "III")]
    _divs = [("G", "R"), ("A", "B.G", "R"), ("A", "B"), ("I", "II", "III")]

    print("\nGROUP DIVISIONS:", _divs, "->")
    res = build_group_data(_divs)
    print("\n ... Independent divisions:")
    for d in res["INDEPENDENT_DIVISIONS"]:
        print("  ", d)
    print("\n ... Group-map:")
    for g, l in res["GROUP_MAP"].items():
        print(f"  {str(g):20}: {l}")
    print("\n ... Groups:", res["GROUPS"])
    print("\n ... Atoms:", res["MINIMAL_SUBGROUPS"])

    print("\n -------------------------------\n")
    print("\nCLASS DATA:")

    open_database()
    _classes = Classes()
    for cdata in _classes.values():
        print("\n", cdata)

    print("\n -------------------------------\n")

    for k, v in _classes.get_class_list(False):
        try:
            print(f" ::: {k:6}: {v} // {_classes.get_classroom(k)}")
        except Bug as e:
            print(f" ::: {k:6}: {v} // {e}")

    _klass = "10G"
    print("\n -------------------------------\nGROUP INFO for class", _klass)
    res = _classes.group_info(_klass)
    print("\n ... Independent divisions:")
    for d in res["INDEPENDENT_DIVISIONS"]:
        print("  ", d)
    print("\n ... Group-map:")
    for g, l in res["GROUP_MAP"].items():
        print(f"  {str(g):20}: {l}")
    print("\n ... Groups:", res["GROUPS"])
    print("\n ... Atoms:", res["MINIMAL_SUBGROUPS"])
