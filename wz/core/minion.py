# -*- coding: utf-8 -*-
"""
core/minion.py - last updated 2021-03-07

Handle configuration data formatted as "MINION".

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

"""
MINION: MINImal Object Notation
-------------------------------

MINION is a simple configuration-file format taking ideas from JSON.

It contains structured data based on "dicts" (associative arrays), lists
and strings. Nothing else is supported.

dict: { key:value key:value ... }
    A "key" may contain any character except the MINION control characters:
        ' ': A separator, except within a "string".
        '#': Start a comment (until the end of the line).
        ':': Separates key from value in a dict.
        '{': Start a dict.
        '}': End a dict.
        '[': Start a list.
        ']': End a list.
        '<<<': Start a complex-string.
        '>>>': End a complex-string.
    A "value" may be a simple-string, a complex-string, a list or a dict.

list: [ value value ... ]

simple-string: A character sequence containing none of the above control
    characters.

complex-string: <<< any characters ... >>>
    A complex-string may be continued from one line to the next. In that
    case the next line must (also) be prefixed by '<<<'. Empty and
    comment lines will be ignored. Line breaks within a string are not
    directly supported – but provision is made for specifying escape
    characters.

Spaces are not needed around the other control characters, but they may
be used. Apart from within complex-strings and their use as separators,
spaces will be ignored.

The top level of a MINION text is a "dict" – without the surrounding
braces ({ ... }).
"""

### Messages
_BAD_DICT_LINE = "Ungültige Zeile (Schlüssel: Wert):\n  {line} – {text}"
_MULTI_KEY = "Schlüssel mehrfach definiert:\n  {line} – {key}"
_BAD_DICT_VALUE = "Ungültiger Schlüssel-Wert:\n  {line} – {val}"
_BAD_LIST_VALUE = "Ungültiger Listeneintrag:\n  {line} – {val}"
_BAD_STRINGX = "Ungültige Text-Zeile:\n  {line} – {text}"
_NO_KEY = "Schlüssel erwartet:\n  {line} – {text}"
_EARLY_END = "Vorzeitiges Ende der Eingabe in Zeile {line}:\n  {text}"
_NESTING_ERROR = "Datenstruktur nicht ordentlich abgeschlossen"

### Special symbols, etc.
_COMMENT = '#'
_KEYSEP  = ':'
_LIST0 = '['
_LIST1 = ']'
_DICT0 = '{'
_DICT1 = '}'
_DICTK = ':'
_STRING0 = '<<<'
_lenSTRING0 = len(_STRING0)
_STRING1 = '>>>'
_REGEX = r'(\s+|:|#|\[|\]|\{|\}|<<<|>>>)' # all special items

import re

class MinionError(Exception):
    pass

###

# This should implement python's string escaping:
#    escaped = codecs.escape_decode(bytes(myString, "utf-8"))[0].decode("utf-8")

class Minion:
    """An impure recursive-descent parser for a MINION string.
    Usage:
        minion = Minion(escape_dict = None)
        python_dict = minion.parse(text)
    """
    def __init__(self, escape_dict = None):
        self.escape_dict = escape_dict
        if escape_dict:
            elist = [re.escape(e) for e in escape_dict]
            self.rxsub = '|'.join(elist)
#
    def parse(self, text):
        self.line_number = 0
        self.lines = text.splitlines()
        data, rest = self.DICT(None)
        if rest or self.line_number < len(self.lines):
            raise MinionError(_EARLY_END.format(
                    line = self.line_number,
                    text = self.lines[self.line_number - 1]))
        return data
#
    def read_line(self):
        if self.line_number >= len(self.lines):
            if self.line_number == len(self.lines):
                # No more lines
                self.line_number += 1
                return _DICT1
            raise MinionError(_NESTING_ERROR)
        line = self.lines[self.line_number]
        self.line_number += 1
        return line.strip()
#
    def read_symbol(self, line):
        """Read up to the next "break-item" (space or special character
        or character sequence) on the current line.
        Return a triple: (pre-break-item, break-item, remainder)
        If there is no break-item or it is a comment, return
            (pre-break-item, None, None).
        """
        try:
            line = line.strip()
            sym, sep, rest = re.split(_REGEX, line, 1)
        except:
            return line, None, None
        if sep == '#':
            # Comment
            return sym, None, None
        if sep[0] == ' ':
            if rest.startswith('#'):
                # Comment
                return sym, None, None
            # If there is a space as break-item, use <None>.
            sep = None
        return sym, sep, rest
#
    def DICT(self, line):
        dmap = {}
        while True:
            key, sep, rest = self.read_symbol(line)
            if sep == _DICTK:
                if not key:
                    raise MinionError(_NO_KEY.format(
                        line = self.line_number, text = line))
                if key in dmap:
                    raise MinionError(_MULTI_KEY.format(
                            line = self.line_number, key = key))
            elif sep == _DICT1 and not key:
                # End of DICT
                return dmap, rest
            else:
                if key or sep or rest:
                    raise MinionError(_BAD_DICT_LINE.format(
                            line = self.line_number, text = line))
                line = self.read_line()
                continue
            while not rest:
                rest = self.read_line()
            val, sep, rest2 = self.read_symbol(rest)
            if val:
                # A simple-string value
                dmap[key] = val
                if sep == _DICT1:
                    return dmap, rest2
                elif sep:
                    raise MinionError(_BAD_DICT_LINE.format(
                            line = self.line_number, text = line))
            elif sep == _STRING0:
                # A complex-string value
                dmap[key], rest2 = self.STRING(rest2)
            elif sep == _DICT0:
                # A sub-item (DICT or LIST)
                dmap[key], rest2 = self.DICT(rest2)
            elif sep == _LIST0:
                dmap[key], rest2 = self.LIST(rest2)
            else:
                raise MinionError(_BAD_DICT_VALUE.format(
                            line = self.line_number, val = rest))
            line = rest2
#
    def STRING(self, line):

        #def resub(m):
        #    return self.escape_dict[m.group(0)]
        lx = []
        while True:
            try:
                line, rest = line.split(_STRING1, 1)
                lx.append(line)
                s0 = ''.join(lx)
                if self.escape_dict:
                    s0 = re.sub(self.rxsub,
                            lambda m: self.escape_dict[m.group(0)],
                            s0)
                return s0, rest.lstrip()
            except ValueError:
                # no end, continue to next line
                lx.append(line)
            while True:
                # Empty lines and comment-lines are ignored
                line = self.read_line()
                if (not line) or line.startswith(_COMMENT):
                    continue
                try:
                    l1, l2 = line.split(_STRING0, 1)
                    if not l1:
                        line = l2
                        break
                except ValueError:
                    pass
                raise MinionError(_BAD_STRINGX.format(
                        line = self.line_number, text = line))
#
    def LIST(self, line):
        lx = []
        while True:
            while not line:
                line = self.read_line()
            sym, sep, rest = self.read_symbol(line)
            if sym:
                lx.append(sym)
            if not sep:
                line = rest
                continue
            if sep == _LIST1:
                # End of list
                return lx, rest
            elif sep == _STRING0:
                # A complex-string value
                sym, rest = self.STRING(rest)
            elif sep == _DICT0:
                # A DICT sub-item
                sym, rest = self.DICT(rest)
            elif sep == _LIST0:
                # A LIST sub-item
                sym, rest = self.LIST(rest)
            else:
                raise MinionError(_BAD_LIST_VALUE.format(
                            line = self.line_number, val = rest))
            lx.append(sym)
            line = rest



if __name__ == '__main__':
    minion = Minion({r'\n': '\n', r'\\': '\\', r'\t': '\t'})
    with open('../local/grade_config.minion', 'r', encoding = 'utf-8') as fh:
        test = fh.read()
    test = test.replace('_ABITUR_GRADES', "[15 14 13 12 11 10 09 08 07"
            " 06 05 04 03 02 01 00 * n t nb /]")
    data = minion.parse(test)
    for k, v in data.items():
        print("\n *** SECTION %s ***" % k)
        for k1, v1 in v.items():
            print("  ... %s: %s" % (k1, v1))
