"""
core/db_access.py

Last updated:  2022-08-01

Helper functions for accessing the database.


=+LICENCE=============================
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

=-LICENCE========================================
"""

DATABASE = "wz.sqlite"

########################################################################

import os

if __name__ == "__main__":
    import sys

    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    #    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "DATA-2023"))

T = TRANSLATIONS("core.db_access")

### +++++

from datetime import datetime
from shutil import copyfile
from glob import glob

from ui.ui_base import (
    ### QtSql:
    QSqlDatabase,
    QSqlQuery,
)


class NoRecord(Exception):
    pass


### -----


def open_database():
    """Ensure the connection to the database is open.
    The QtSql default connection is used.
    """
    dbpath = DATAPATH(DATABASE)
    con = QSqlDatabase.database()
    if con.isValid():
        if con.databaseName() == dbpath:
            # The connection is already open
            return con
        # Connected to another db: close it
        con.close()
        connectionName = con.connectionName()
        con = None  # needed to release the database object
        QSqlDatabase.removeDatabase(connectionName)
    # Open the connection
    con = QSqlDatabase.addDatabase("QSQLITE")
    con.setDatabaseName(dbpath)
    if not con.open():
        raise Bug(f"Cannot open database at {dbpath}")
    # print("TABLES:", con.tables())
    foreign_keys_on = "PRAGMA foreign_keys = ON"
    if not QSqlQuery(foreign_keys_on).isActive():
        raise Bug(f"Failed: {foreign_keys_on}")
    return con


def db_backup(name=""):
    dbpath = DATAPATH(DATABASE)
    if name:
        newfile = DATAPATH(name) + ".sqlite"
    else:
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        newfile = f"{dbpath}_{stamp}"
    copyfile(dbpath, newfile)
    existing = sorted(glob(dbpath + "_*"))
    msg = [T["BACKUP_TO"].format(f=newfile)]
    for f in existing[:-5]:
        msg.append(T["REMOVE_OLD_BACKUP"].format(f=f))
        os.remove(f)
    REPORT("INFO", "\n".join(msg))


"""
def table_extent(table):
    query = QSqlQuery(
        f"SELECT MAX(rowid) FROM {table}"
    )
    res = []
    while (query.next()):
        res.append(query.value(0))
    print("MAX rowid:", res)
    query = QSqlQuery(
        f"SELECT COUNT(rowid) FROM {table}"
    )
    res = []
    while (query.next()):
        res.append(query.value(0))
    print("COUNT:", res)
"""


def db_query(query_text):
    query = QSqlQuery(query_text)
    rec = query.record()
    nfields = rec.count()
    value_list = []
    while query.next():
        value_list.append([query.value(i) for i in range(nfields)])
    return value_list


class KeyValueList(list):
    def __init__(self, iterable, check=None):
        """Build a list which also has key -> index and key -> value methods.
        iterable:   Lists (key, value) pairs
        check:      If supplied, it takes a (key, value) pair and checks
                    its validity. If invalid it returns <None>. If valid,
                    it returns the value, which may be transformed.
        """
        super().__init__()
        self.__check = check
        self.__map = {}
        for item in iterable:
            self.append(item)

    def append(self, item):
        if not len(item) == 2:
            raise Bug(f"KeyValueList – new item is not a pair: {repr(item)}")
        if self.__check is not None:
            i2 = self.__check(item)
            if i2 is None:
                return    # Value invalid
            if i2 != item[1]:
                item = (item[0], i2)
        self.__map[item[0]] = len(self)
        super().append(item)

    def index(self, key):
        return self.__map[key]

    def map(self, key):
        return self[self.__map[key]][1]

    def key_list(self):
        return list(self.__map)


def db_read_table(
    table, fields, *wheres, distinct=False, sort_field=None, **keys
):
    """Read a list of table entries.
    <fields> specifies which fields are to be read. It may be
        - null/empty (=> '*'),
        - a list of strings (field names).
    <wheres> are WHERE conditions (as strings). If there is more than
    one, they are joined by "AND".
    If <distinct> is true, the "DISTINCT" keyword is added to the query.
    <sort_field> is an optional field to sort on.
    <keys> are WHERE conditions with "=" (value is str) or "IN" (value
    is list).
    Return a list of fields and a list of records (each is a list).
    """
    where_cond = [w for w in wheres]
    for k, v in keys.items():
        if isinstance(v, str):
            where_cond.append(f'"{k}" = "{v}"')
        elif isinstance(v, int):
            where_cond.append(f'"{k}" = {v}')
        elif isinstance(v, list):
            instring = ", ".join(
                [f'"{_v}"' if isinstance(_v, str) else str(_v) for _v in v]
            )
            where_cond.append(f'"{k}" IN ( {instring} )')
        else:
            raise Bug(f"Unexpected comparison value: '{repr(v)}' for '{f}'")
    if where_cond:
        where_clause = f" WHERE {' AND '.join(where_cond)}"
    else:
        where_clause = ""
    f = ", ".join([f'"{f}"' for f in fields]) if fields else "*"
    o = f' ORDER BY "{sort_field}"' if sort_field else ""
    d = " DISTINCT" if distinct else ""
    qtext = f"SELECT{d} {f} FROM {table}{where_clause}{o}"
    # print("§§§", qtext)
    query = QSqlQuery(qtext)
    rec = query.record()
    nfields = rec.count()
    value_list = []
    while query.next():
        value_list.append([query.value(i) for i in range(nfields)])
    if fields:
        if len(fields) != nfields:
            raise Bug(f"Wrong number of fields in record: {nfields} ≠ {len(fields)}")
        return fields, value_list
    else:
        return [rec.fieldName(i) for i in range(nfields)], value_list


def db_read_unique_field(table, field, *wheres, **keys):
    flist, rlist = db_read_table(table, [field], *wheres, **keys)
    if len(rlist) == 1:
        return rlist[0][0]
    if not rlist:
        raise NoRecord
    raise Bug("Record not unique")


def db_read_full_table(table, *wheres, sort_field=None, **keys):
    return db_read_table(table, None, *wheres, sort_field=None, **keys)


def db_values(table, value_field, *wheres, **keys):
    """Wrapper for db_read_table returning a single list, just the
    first fields of each record. Thus it is especially suitable when
    only a single field is to be read from the table.
    """
    fields, value_list = db_read_table(table, [value_field], *wheres, **keys)
    return [v[0] for v in value_list]


def db_key_value_list(
    table, key_field, value_field, sort_field=None, check=None
):
    """Return a <KeyValueList> of (key, value) pairs from the given
    database table.
    """
    fields, value_list = db_read_table(
        table, [key_field, value_field], sort_field=sort_field
    )
    return KeyValueList(value_list, check)


def db_read_fields(table, fields, sort_field=None):
    """Read all records from the given table.
    Return a list of tuples containing these fields in the given order.
    """
    fields, value_list = db_read_table(table, fields, sort_field=sort_field)
    return value_list


def db_update_fields(table, field_values, *wheres, **keys):
    where_cond = [w for w in wheres]
    for k, v in keys.items():
        if isinstance(v, str):
            where_cond.append(f'"{k}" = "{v}"')
        elif isinstance(v, int):
            where_cond.append(f'"{k}" = {v}')
        elif isinstance(v, list):
            instring = ", ".join(
                [f'"{_v}"' if isinstance(_v, str) else str(_v) for _v in v]
            )
            where_cond.append(f'"{k}" IN ( {instring} )')
        else:
            raise Bug("Unexpected comparison value: '{repr({v})'")
    if where_cond:
        where_clause = f" WHERE {' AND '.join(where_cond)}"
    else:
        where_clause = ""

    fields = []
    for f, v in field_values:
        if isinstance(v, str):
            fields.append(f'"{f}" = "{v}"')
        elif isinstance(v, int):
            fields.append(f'"{f}" = {v}')
        else:
            raise Bug(f"Unexpected field value: '{repr(v)}' for '{f}'")

    f = ", ".join(fields)
    qtext = f"UPDATE {table} SET {f}{where_clause}"
    # print("§§§", qtext)
    query = QSqlQuery()
    if query.exec(qtext):
        return True
    error = query.lastError()
    SHOW_ERROR(error.text())
    return False


def db_update_field(table, field, value, *wheres, **keys):
    return db_update_fields(table, [(field, value)], *wheres, **keys)


def db_new_row(table, **values):
    flist, vlist = [], []
    for f, v in values.items():
        flist.append(f'"{f}"')
        if isinstance(v, str):
            vlist.append(f'"{v}"')
        elif isinstance(v, int):
            vlist.append(f"{v}")
        else:
            raise Bug(f"Unexpected field value: '{repr(v)}' for '{f}'")
    qtext = (
        f"INSERT INTO {table} ({', '.join(flist)}) VALUES ({', '.join(vlist)})"
    )
    # print("§§§", qtext)
    query = QSqlQuery()
    if query.exec(qtext):
        newid = query.lastInsertId()
        # print("-->", newid)
        return newid
    error = query.lastError()
    SHOW_ERROR(error.text())
    return None


def db_delete_rows(table, *wheres, **keys):
    where_cond = [w for w in wheres]
    for k, v in keys.items():
        if isinstance(v, str):
            where_cond.append(f'"{k}" = "{v}"')
        elif isinstance(v, int):
            where_cond.append(f'"{k}" = {v}')
        elif isinstance(v, list):
            instring = ", ".join(
                [f'"{_v}"' if isinstance(_v, str) else str(_v) for _v in v]
            )
            where_cond.append(f'"{k}" IN ( {instring} )')
        else:
            raise Bug("Unexpected comparison value: '{repr({v})'")
    if where_cond:
        where_clause = f" WHERE {' AND '.join(where_cond)}"
    else:
        where_clause = ""
    qtext = f"DELETE FROM {table}{where_clause}"
    # print("§§§", qtext)
    query = QSqlQuery()
    if query.exec(qtext):
        return True
    error = query.lastError()
    SHOW_ERROR(error.text())
    return False


"""
# This picks up unique columns, but not unique constraints on multiple columns
def db_unique_fields(table):
    fieldinfo = db_query(f"PRAGMA table_info({table})")
    fields = []
    for uf in db_query(f"PRAGMA index_list({table})"):
        if uf[2] == 1:  # "unique"
            # second element is like f'sqlite_autoindex_{table}_n'
            index = int(uf[1].rsplit('_', 1)[1]) - 1
            fields.append(fieldinfo[index][1])
    return fields
"""


def read_pairs(data):
    """Read a list of (key, value) pairs from the given string.

    Each line of the input supplies one such pair.
    Key and value are separated by ':'.
    This format is used for special database fields which
    contain multiple key-value pairs.
    """
    pairs = []
    for line in data.splitlines():
        try:
            k, v = line.split(":", 1)
            pairs.append((k.strip(), v.strip()))
        except ValueError:
            SHOW_ERROR(T["BAD_KEY_VALUE_LIST"].format(text=data))
    return pairs


# -+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-

# An example of code to create and populate the CLASSES table
def enter_classes():
    con = open_database()
    print("TABLES0:", con.tables())

    query = QSqlQuery()
    query.exec("drop table CLASSES")
    if not query.exec(
        "create table CLASSES(CLASS text primary key,"
        " NAME text unique not null, CLASSROOM text)"
    ):
        error = query.lastError()
        SHOW_ERROR(error.text())

    classes = []
    names = []
    classrooms = []
    for i in range(1, 13):
        k = f"{i:02}G"
        classes.append(k)
        names.append(f"{i}. Großklasse")
        classrooms.append(f"r{k}")
        k = f"{i:02}K"
        classes.append(k)
        names.append(f"{i}. Kleinklasse")
        classrooms.append(f"r{k}")
    classes.append("13")
    names.append("13. Klasse")
    classrooms.append("r13")

    classes.append("--")
    names.append("keine Klasse")
    classrooms.append("")

    query.prepare("insert into CLASSES values (?, ?, ?)")
    query.addBindValue(classes)
    query.addBindValue(names)
    query.addBindValue(classrooms)
    if not query.execBatch():
        error = query.lastError()
        SHOW_ERROR(error.text())
    print("TABLES1:", con.tables())


# --#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == "__main__":
    #    enter_classes()

    db_backup()
    quit(0)

    l = KeyValueList([("a", 1), ("b", 2), ("c", 3)])
    l.append(("d", 4))
    print("KeyValueList:", l)
    print("   ... map('b'):", l.map("b"))

    open_database()

    print("\nTEACHERS:")
    for k, v in db_key_value_list("TEACHERS", "TID", "NAME", "SORTNAME"):
        print(f"  {k:6}: {v}")

    print("\nCOURSES:")
    for r in db_read_fields(
        "COURSES", ("course", "CLASS", "GRP", "SUBJECT", "TEACHER")
    ):
        print("  ", r)

    _sid = "En"
    _tid = "MF"
    print(f"\nCOURSES for {_tid} in {_sid}:")
    print("  ", db_values("COURSES", "CLASS", TEACHER=_tid, SUBJECT=_sid))

    fields, values = db_read_full_table("COURSES", CLASS="10G")
    print("\nCOURSES in 10G:", fields)
    for row in values:
        print("  ", row)

# It seems that null entries are read as empty strings ...
