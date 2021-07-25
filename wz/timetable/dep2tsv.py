#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
timetable/dep2tsv.py

Last updated:  2021-07-22

Convert PB's Deputatspläne to something like tsv so that they can be
compared using a diff utility.


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

INPUT = 'Deputate_2021-07-13.xlsx'

import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
#TODO: maybe put this back in later?
#    from core.base import start
#    start.setup(os.path.join(basedir, 'TESTDATA'))
# This can be set up by core.base:
def DATAPATH(path):
#TODO: Adjust paths for reading input data to match the real situation
# (here I am using relative paths while testing).
    return os.path.join(os.path.dirname(__file__), 'DATA', *path.split('/'))

### +++++

from tables.spreadsheet import Spreadsheet, NewTable

filepath = DATAPATH(INPUT)
table = Spreadsheet(filepath)

outpath = filepath.rsplit('.', 1)[0] + '.txt'
with open(outpath, 'w', encoding = 'utf-8') as fh:
    for sheet in table.getTableNames():
        print("Reading", sheet)
        table.setTable(sheet)
        for row in table.table():
            if row[1] or row[2] or row[3] or row[4] or row[5]:
                fh.write('$$$ %s\n' % ' | '.join([d or '–' for d in row[:16]]))
        fh.write("\n=====================================================\n\n")
