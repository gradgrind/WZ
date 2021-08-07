# -*- coding: utf-8 -*-
from itertools import combinations

plist0 = (2,3,4,5,6)
allcombis = []
for l in range(len(plist0), 0, -1):
    allcombis += [set(c) for c in combinations(plist0, l)]
print(allcombis)

#def getcombis(k, plist):
#    pset = set(plist)
#    return {frozenset(c) for c in allcombis if k in c and c <= pset}

def getcombis(k, plist):
    allcombis = set()
    for l in range(len(plist), 0, -1):
        for c in combinations(plist, l):
            if k in c:
                print("###", c)
                allcombis.add(frozenset(c))
    print("###--->", allcombis)
    return allcombis


data1 = {
    2: (2,3,4,5),
    3: (2,3,4,5,6),
    4: (2,3,4,6),
    5: (2,3,5,6),
    6: (3,4,5,6)
}

data2 = {
    2: (2,3,4,5),
    3: (2,3,4,5,6),
    4: (2,3,4,5,6),
    5: (2,3,4,5,6),
    6: (3,4,5,6)
}

data3 = {
    2: (2,3,4),
    3: (2,3),
    4: (2,4),
    5: (5,)
}

def process(data):
    kcombis = set()
    for k, pl in data.items():
        gc = getcombis(k, pl)
#        print(f"\n??? {k}:", gc)
        kcombis.update(gc)
    xcombis = []
    for combi in kcombis:
        # Check with all components
#        print("&&&", combi)
        for p in combi:
#            print("%%%", p)
            plist = data[p]
            for q in combi:
                if q not in plist:
                    break
            else:
                # ok
                continue
            break
        else:
            xcombis.append(combi)
#            print("***", combi)
    # Eliminate subsets
    ycombis = []
    for c in xcombis:
        for c2 in xcombis:
            if c < c2:
                print("---", c)
                break
        else:
            print("+++", c)

process(data1)
