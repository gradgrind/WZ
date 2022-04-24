"""
uutility/db_management.py

Last updated:  2022-04-24

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

DATABASE = "db1.sqlite"

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

T = TRANSLATIONS("utility.db_management")

### +++++

from ui.ui_base import (
    ### QtSql:
    QSqlDatabase,
    QSqlQuery,
)

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


#def table_extent(table):
#    query = QSqlQuery(
#        f"SELECT MAX(rowid) FROM {table}"
#    )
#    res = []
#    while (query.next()):
#        res.append(query.value(0))
#    print("MAX rowid:", res)
#    query = QSqlQuery(
#        f"SELECT COUNT(rowid) FROM {table}"
#    )
#    res = []
#    while (query.next()):
#        res.append(query.value(0))
#    print("COUNT:", res)


def db_read_fields(table, fields, sort_field=None):
    """Read all records from the given table.
    Return a list of tuples containing these fields in the given order.
    """
    qfields = ", ".join(fields)
    o = f" ORDER BY {sort_field}" if sort_field else ""
    query = QSqlQuery(
        f"SELECT {', '.join(fields)} FROM {table}{o}"
    )
    record_list = []
    n = len(fields)
    while (query.next()):
        record_list.append(tuple(query.value(i) for i in range(n)))
    return record_list


def db_key_value_list(table, key_field, value_field, sort_field):
    """Return a list of (key, value) pairs from the given database table."""
    query = QSqlQuery(
        f"SELECT {key_field}, {value_field} FROM {table}"
        f" ORDER BY {sort_field}"
    )
    key_value_list = []
    while (query.next()):
        key_value_list.append((query.value(0), query.value(1)))
    return key_value_list


def db_values(table, value_field, **keys):
    where_cond = [f"{k} = '{v}'" for k, v in keys.items()]
    if where_cond:
        where_clause = f" WHERE {' AND '.join(where_cond)}"
    else:
        where_clause = ""
    query = QSqlQuery(f"SELECT {value_field} FROM {table}{where_clause}")
    value_list = []
    while (query.next()):
        value_list.append(query.value(0))
    return value_list


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
            k, v = line.split(':', 1)
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

    open_database()

    print("\nTEACHERS:")
    for k, v in db_key_value_list("TEACHERS", "TID", "NAME", "SORTNAME"):
        print(f"  {k:6}: {v}")

    print("\nCOURSES:")
    for r in db_read_fields(
        "COURSES",
        ("course", "CLASS", "GRP", "SUBJECT", "TEACHER")
    ):
        print("  ", r)

    _sid = "En"
    _tid = "MF"
    print(f"\nCOURSES for {_tid} in {_sid}:")
    print("  ", db_values("COURSES", "CLASS", TEACHER=_tid, SUBJECT=_sid))

    #table = "LESSONS"
    #print("\nExtent of table {table}:")
    #table_extent(table)
