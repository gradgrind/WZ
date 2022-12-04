"""
local/local_pupils.py - last updated 2022-12-04

Manage pupil data – school/location specific code.

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

T = TRANSLATIONS("core.pupils")

### +++++

import re

from core.base import Dates
from tables.spreadsheet import read_DataTable, filter_DataTable, TableError

### -----

def next_class(pdata):
    """Adjust the pupil data to the next class.
    Note that this is an "in-place" operation, so if the original data
    should remain unchanged, pass in a copy.
    """
    klass = pdata["CLASS"]
    leaving_groups = CONFIG["LEAVING_GROUPS"].get(klass)
    if leaving_groups:
        if leaving_groups == "*":
            return "X"
        for g in pdata["GROUPS"].split():
            if g in leaving_groups:
                return "X"
    # Progress to next class ...
    k_year = class_year(klass)
    k_new = int(k_year) + 1
    k_suffix = klass[2:]
    klass = f"{k_new:02}{k_suffix}"
    # Handle entry into "Qualifikationsphase"
    if k_new == 12 and "G" in pdata["GROUPS"].split():
        try:
            pdata["DATE_QPHASE"] = CALENDAR["~NEXT_FIRST_DAY"]
        except KeyError:
            pass
    return klass


def class_year(klass):
    """Get just the year part of a class name, as <str>, padded to
    2 digits.
    """
    try:
        k = int(klass[:2])
    except:
        k = int(klass[0])
    return f"{k:02}"


def new_pid(pupils):
    """Generate a new pid conforming to the requirements of
    function <check_pid_valid>.
    """
    # Base the new pid on today's date, adding a number to the end.
    today = Dates.today().replace("-", "")  # it must be an integer
    collect = []
    for pid in pupils:
        if pid.startswith(today):
            try:
                i = int(pid[8:])
            except ValueError:
                continue
            collect.append(i)
    if collect:
        collect.sort()
        i = str(collect[-1] + 1)
    else:
        i = "1"
    return today + i


def check_pid_valid(pid):
    """Check that the pid is of the correct form."""
    # Accept any integer.
    try:
        int(pid)
        return True
    except:
        return False


def asciify(string, invalid_re=None):
    """This converts a utf-8 string to ASCII, e.g. to ensure portable
    filenames are used when creating files.
    Also spaces are replaced by underlines.
    Of course that means that the result might look quite different from
    the input string!
    A few explicit character conversions are given in the mapping
    <ASCII_SUB>.
    By supplying <invalid_re>, an alternative set of exclusion characters
    can be used.
    """
    # regex for characters which should be substituted:
    if not invalid_re:
        invalid_re = r"[^A-Za-z0-9_.~-]"

    def rsub(m):
        c = m.group(0)
        if c == " ":
            return "_"
        try:
            return lookup[c]
        except:
            return "^"

    lookup = ASCII_SUB
    return re.sub(invalid_re, rsub, string)


# Substitute characters used to convert utf-8 strings to ASCII, e.g. for
# portable filenames. Non-ASCII characters which don't have
# entries here will be substituted by '^':
ASCII_SUB = {
    "ä": "ae",
    "ö": "oe",
    "ü": "ue",
    "ß": "ss",
    "Ä": "AE",
    "Ö": "OE",
    "Ü": "UE",
    "ø": "oe",
    "ô": "o",
    "ó": "o",
    "é": "e",
    "è": "e",
    # Latin:
    "ë": "e",
    # Cyrillic (looks like the previous character, but is actually different):
    "ё": "e",
    "ñ": "n",
}


def read_pupils_source(filepath):
    """Read a spreadsheet file containing pupil data from an external
    "master" database.
    """
    field_list = [
        {
            'NAME': field[0],
            'DISPLAY_NAME': field[1],
            'REQUIRED': len(field) > 2,
        }
        for field in CONFIG["PUPILS_FIELDS"] + CONFIG["PUPILS_EXTRA_FIELDS"]
    ]
    fields = {
        'INFO_FIELDS': [],
        'TABLE_FIELDS': field_list}
    data = read_DataTable(filepath)
    try:
        data = filter_DataTable(data, fields, extend=False)
    except TableError as e:
        raise ValueError(
            T["FILTER_ERROR"].format(msg=f"{e} \n ... in\n {filepath}")
        )
    # Change class names, adjust pupil names ("tussenvoegsel")
    day1 = CALENDAR["FIRST_DAY"]
    pupils = []
    for row in data["__ROWS__"]:
        if (x:=row.get("DAY_EXIT")):
            if x < day1:
                continue
        klass = row["CLASS"]
        try:
            if klass[-1] == "K":
                klass = f"{int(klass[:-1]):02}K"
            elif klass != "13":
                klass = f"{int(klass):02}G"
        except ValueError:
            raise ValueError(
                T["INVALID_CLASS"].format(
                    klass=klass,
                    row=repr(row),
                    path=filepath
                )
            )
        (
            row["FIRSTNAMES"],
            row["LASTNAME"],
            row["FIRSTNAME"],
            sort_name
        ) = tussenvoegsel_filter(
            row["FIRSTNAMES"], row["LASTNAME"], row["FIRSTNAME"]
        )
        if not row.get("SORT_NAME"):
            row["SORT_NAME"] = sort_name
        pupils.append(row)
    return pupils


def get_sortname(pdata):
    """Construct a string to use in sorting pupil names and for
    pupil-related file names. The result should preferably be ASCII-only
    and without spaces, but that is not compulsory.
    """
    return tussenvoegsel_filter(
        pdata["FIRSTNAMES"],
        pdata["LASTNAME"],
        pdata["FIRSTNAME"]
    )[-1]


def tussenvoegsel_filter(firstnames, lastname, firstname):
    """In Dutch there is a word for those little last-name prefixes
    like "van", "von" and "de": "tussenvoegsel". For sorting purposes
    these can be a bit annoying because they should often be ignored,
    e.g. "Vincent van Gogh" would be sorted primarily under "G".

    This function accepts names which contain a "tussenvoegsel" as
    a suffix to the first names or as a prefix to the last-name (the
    normal case). Also a "sorting-name" is generated containing
    only ASCII characters and no spaces.

    Given raw firstnames, lastname and short firstname, ensure that any
    "tussenvoegsel" is at the beginning of the lastname (and not at the
    end of the first name) and that spaces are normalized.
    Return a tuple: (
            first names without "tussenvoegsel",
            surname, potentially with "tussenvoegsel",
            first name,
            sorting name
        ).
    """
    firstnames1, tv, lastname1 = tvSplit(firstnames, lastname)
    firstname1 = tvSplit(firstname, "X")[0]
    if tv:
        lastname1 = tv + lastname1
    return (
        firstnames1,
        lastname1,
        firstname1,
        asciify(f"{lastname1}_{firstname1}")
    )

def tvSplit(firstnames, lastname):
    """Split off a "tussenvoegsel" from the end of the first-names,
    or the start of the surname.
    These little name parts are identified by having a lower-case
    first character.
    Also ensure normalized spacing between names.
    Return a tuple: (
            first names without tussenvoegsel,
            tussenvoegsel or <None>,
            surname without tussenvoegsel
        ).
    """
    # TODO: Is the identification based on starting with a lower-case
    # character adequate?
    fn = []
    tv = firstnames.split()
    while tv[0][0].isupper():
        fn.append(tv.pop(0))
        if not len(tv):
            break
    if not fn:
        raise ValueError(
            T["BAD_NAME"].format(name=f"{firstnames} / {lastname}")
        )
    ln = lastname.split()
    while ln[0].islower():
        if len(ln) == 1:
            break
        tv.append(ln.pop(0))
    # Add space to <tv> for prefixing to <lastname>
    tv = (" ".join(tv) + " ") if tv else None
    return (" ".join(fn), tv, " ".join(ln))
