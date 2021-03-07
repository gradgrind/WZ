# -*- coding: utf-8 -*-
"""
grades/gradetable.py - last updated 2021-03-04

Temporary / test module?
Convert grade tables (and other) between "spreadsheet" and json formats.

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
"""

### Messages
_TABLE_YEAR_MISMATCH = "Falsches Schuljahr in Tabelle:\n  {filepath}"


import sys, os, datetime, json, gzip
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

from tables.spreadsheet import Spreadsheet, TableError
from local.base_config import NO_DATE
from local.grade_config import GRADE_INFO_FIELDS

###

def matrix2mapping(schoolyear, filepath, info_names = None):
    """Read the header info and pupils' lines from the given table file.
    Each data row starts with "pid", pupil-name and stream fields.
    This is followed by a field for each "sid" (generally a subject-tag).
    The "spreadsheet" module is used as backend so .ods, .xlsx and .tsv
    formats are possible. The filename may be passed without extension –
    <Spreadsheet> then looks for a file with a suitable extension.
    <Spreadsheet> also supports in-memory binary streams (io.BytesIO)
    with attribute 'filename' (so that the type-extension can be read).
    Only the non-empty cells from the source table will be included.
    A mapping structure is built:
    The info items are included as top-level "key -> value" pairs.
    The source keys may be localized, they will be converted to the
    "internal" names using the <info_names> mapping:
        {internal-name: local-name, ... }
    A 'SCHOOLYEAR' field is expected and is checked against the
    parameter <choolyear>.
    The pupil lines are available as a list of mappings via the
    '__PUPILS__' key.
    Each pupil mapping has the structure:
        {'PID': pid, 'NAME': pname, 'STREAM': stream,
        '__DATA__': {sid: value, ... }}
    """
    ss = Spreadsheet(filepath)
    dbt = ss.dbTable()
    if info_names:
        rfields = {v: k for k, v in info_names.items()}
    else:
        rfields = None
    info = {}
    for row in dbt.info:
        k = row[0]
        if k:
            if rfields:
                try:
                    k = rfields[k]
                except:
                    REPORT('WARN', 'No localization for field'
                        ' "{field}"'.format(field = k))
            info[k] = row[1]
    year = info.get('SCHOOLYEAR')
    if year != schoolyear:
        raise TableError(_TABLE_YEAR_MISMATCH.format(
                    filepath = filepath))
    sid2col = []
    col = 0
    for f in dbt.fieldnames():
        if col > 2:
            if f[0] != '$':
                # This should be a subject tag
                sid2col.append((f, col))
        col += 1
    # Assume the first three columns are pid, pname and stream
    # Only include non-empty cells from the source table
    _rows = []
    for row in dbt:
        pid = row[0]
        if pid and pid != '$':
            gmap = {}
            _row = {'PID': pid, 'NAME': row[1], 'STREAM': row[2],
                    '__DATA__': gmap}
            for sid, col in sid2col:
                val = row[col]
                if val:
                    gmap[sid] = val
            _rows.append(_row)
    info['__PUPILS__'] = _rows
    return info

###

def save(filepath, data):
# Back up old table, if it exists?
    timestamp = datetime.datetime.now().isoformat(sep = '_',
            timespec = 'minutes')
#    if not os.path.isdir(filepath):
#        os.makedirs(filepath)
    fpath = filepath + '.json.gz'
#    if os.path.isfile(fpath):
#        today = timestamp.split('_', 1)[0]
#        bpath = os.path.join(self.filepath, today + '.json.gz')
#        if not os.path.isfile(bpath):
#            shutil.copyfile(fpath, bpath)
    data['__MODIFIED__'] = timestamp
    with gzip.open(fpath, 'wt', encoding = 'utf-8') as zipfile:
        json.dump(data, zipfile, ensure_ascii = False)
    return fpath


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    from core.base import init
    init()
    _schoolyear = '2016'
    _term = '2'

    from local.base_config import year_path
    from local.grade_config import GradeBase

    for _term in ('1', '2', 'A', 'S', 'T'):
        table_path = year_path(_schoolyear,
                    GradeBase.table_path('*', _term, None))
        d = os.path.dirname(table_path)
        for f in os.listdir(d):
            if f.endswith('.tsv'):
                f1 = os.path.join(d, f)
                gmap = matrix2mapping(_schoolyear, f1)
                f2 = f1.rsplit('.', 1)[0]
                print("\n$$$", save(f2, gmap))
