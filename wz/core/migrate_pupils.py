# -*- coding: utf-8 -*-
"""

core/migrate_pupils.py

Last updated:  2021-10-05

"Move" pupils from one school-year to the next.


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

_TITLE = 'Schülerdaten'

###############################################################
import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start
#TODO: Temporary redirection to use real data (there isn't any test data yet!)
#    start.setup(os.path.join(basedir, 'TESTDATA'))
    start.setup(os.path.join(basedir, 'DATA'))

from core.base import Dates
from local.base_config import class_year
from tables.spreadsheet import read_DataTable, make_DataTable


def migrate_pupils(repeat_pids = []):
    """Create a pupil-data structure for the following year.
    If <save_as> is provided, it should be a file-path: the new
    pupil data will be saved here (as a DataTable) instead of in the
    internal database.
    The current pupil data is saved as a DataTable to the 'tmp'
    folder within the data area.
    If <repeat_pids> is provided it should be an iterable object
    listing pupil-ids for those who will definitely stay on in the same
    class, even if their class/group would suggest leaving. This is, of
    course, overridden by a leaving date!
    """
    keep_pids = set(repeat_pids)
    nextyear = str(int(SCHOOLYEAR) + 1)
    day1 = Dates.day1(nextyear) # for filtering out pupils who have left
    newpupils = {}
    class_tables = DATAPATH(CONFIG['CLASS_TABLE'])
    # Filter out pupils from final classes, tweak pupil data
    for fname in sorted(os.listdir(class_tables)):
        class_data = read_DataTable(os.path.join(class_tables, fname))
        info = class_data['__INFO__']
        rows = class_data['__ROWS__']
        klass = info['CLASS']
        k_year = class_year(klass)
        k_new = int(k_year) + 1
        k_suffix = klass[2:]
        new_klass = f'{k_new:02}{k_suffix}'
        new_pdata = []
        newpupils[new_klass] = new_pdata
        for pdata in rows:
            exit_date = pdata['EXIT_D']
            if exit_date and exit_date <= day1:
                continue
            pid = pdata['PID']
            if pid in keep_pids:
                # Add to new list for old class
                newpupils[klass].append(pdata)
            else:
                pd = local_next_class(new_klass, pdata)
                if pd:
                    new_pdata.append(pd)
    info = {
        '__TITLE__': _TITLE,
        'SCHOOLYEAR': nextyear,
        'CLASS': None,
        '__MODIFIED__': Dates.timestamp(),
    }
    data = {
        '__INFO__': info,
        '__FIELDS__': [f[0] for f in CONFIG['PUPIL_FIELDS']],
        '__ROWS__': None
    }
    outdir = DATAPATH(CONFIG['CLASS_TABLE'], 'PENDING')
    os.makedirs(outdir, exist_ok = True)
    table_type = CONFIG['TABLE_FORMAT']
    for klass, pdlist in newpupils.items():
        info['CLASS'] = klass
        data['__ROWS__'] = sorted(pdlist, key = lambda pd: pd['PSORT'])
        kbytes = make_DataTable(data, table_type)
        fpath = os.path.join(outdir, CONFIG['PUPIL_TABLE'].format(
                klass = klass) + '.' + table_type)
        #print(" -->", fpath)
        with open(fpath, 'wb') as fh:
            fh.write(kbytes)




#TODO: -> local module
def local_next_class(klass, pdata):
    # Handle entry into "Qualifikationsphase"
    if klass == '12G' and 'G' in pdata['GROUPS'].split():
        pd = pdata.copy()
        pd['QUALI_D'] = CALENDAR['~NEXT_FIRST_DAY']
        return pd
    return pdata



if __name__ == '__main__':
    migrate_pupils()
