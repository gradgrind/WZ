# -*- coding: utf-8 -*-

from collections import OrderedDict

def ordereddict_to_dict(value):
    for k, v in value.items():
        if isinstance(v, OrderedDict):
            value[k] = ordereddict_to_dict(v)
        elif isinstance(v, list):
            i = 0
            for el in v:
                if isinstance(el, OrderedDict):
                    v[i] = ordereddict_to_dict(el)
                i += 1
    return dict(value)

import xmltodict

ifile = 'data/importXML/import_basicdata+lessongrid.xml'
ifile = 'data/exportXML/export1.xml'
ifile = 'data/fwsb_2.fet'
ifile = 'xmltest.xml'
with open(ifile, 'rb') as fh:
    xml = fh.read()
print("XML:")
print(xml)
print("\nDICT:")
d = xmltodict.parse(xml)

print(ordereddict_to_dict(d))

print("\nreXML:")
print(xmltodict.unparse(d))
