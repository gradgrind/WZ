# -*- coding: utf-8 -*-
"""
field_handlers.py - last updated 2021-04-13

Handlers for special report/template fields.

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

########################################################################

There are two basic types of handler:
 - ones producing a result dependent on other – existing – fields
 - ones which transform an already existing field value
"""

### Messages
_CIRCULAR_DEPENDENCIES = "Zirkuläre Abhängigkeiten: [{fields}]"
_BAD_HANDLER_CALL = "Fehler beim Verarbeiten vom Händler {tag}:\n" \
        "  {handler}: {parms}"
_MISSING_FIELD = "{field}: Feld nicht bekannt"

########################################################################

NONE = ''
EMPTY = '???'

### +++++

class FieldHandlerError(Exception):
    pass

###

#TODO: Perhaps shouldn't use '*' as normal part of field name ('*B_T',
# etc.), because of possible interference with its use as a "joker".
# Use '+' instead. Maybe '$' instead of '.'?
class ManageHandlers(dict):
    """This manages the handlers for "special tags" in a template or
    grade table. These are tags that undergo some sort of processing
    rather than being directly entered into the template.
    Entries are provided as a <dict>, {handler: definition, ...}, or
    multiple <dicts> using the method <extend> (repeatedly).

    By including a wild-card ('*') in the handler tag, the handler can
    be used for multiple source tags.
    """
    def __init__(self, handler_map):
        self.handlers = {}
        self.wildmatches = {}
        super().__init__()
        if handler_map:
            self.extend(handler_map)
#
    def extend(self, handler_map):
        for tag, handler in handler_map.items():
            _h = HANDLERS[handler[0]]
            try:
                h = _h(*handler[1:])
            except TypeError:
                # Probably wrong number of arguments
                raise FieldHandlerError(_BAD_HANDLER_CALL.format(
                        tag = tag, handler = handler[0],
                        parms = repr(handler[1:])))
            self[tag] = h
            h.name = tag
            # Test for a wild-card in the field name
#TODO: If I stop using '*' as a "subject" prefix, I can remove the
# second part of the test:
            if tag.count('*') == 1 and tag[0] != '*':
                rex0 = re.escape(tag.replace('*', '@'))
                h.rex = rex0.replace('@', '(.*)') + '$'
            else:
                h.rex = None
#
    def get_handler(self, field):
        """Fetch the "special handler" for the given field, if there is
        one. If the handler is found by a wild-card match, save the part
        of the field name matching the '*' in the mapping
        <self.wildmatches>.
        Return the handler, or <None> if there is no special handler for
        the field.
        """
        # Use a cache for the handlers
        try:
            return self.handlers[field]
        except KeyError:
            pass
        try:
            h = self[field]
            self.handlers[field] = h
            return h
        except KeyError:
            # Try to match '*'
            for f, h in self.items():
                if h.rex:
                    m = re.match(h.rex, field)
                    if m:
                        self.handlers[field] = h
                        self.wildmatches[field] = m.group(1)
                        return h
        return None
#
    def sort_dependencies(self, fields):
        """Order the given fields so that a field which depends on other
        fields comes after the fields it depends on. Dependencies on
        fields not within <fields> are gathered in a separate list – it
        is assumed these will be provided before the dependent fields
        in <fields> are filled.
        In addition, each field which is required by another gets an
        entry in the mapping <self.depmap>, which maps the field to the
        set of other fields which require it.
        """
        # Results:
        ordered_fields = []
        dependencies = set()
        self.depmap = {}   # Build a dependants mapping here:
        # field -> {required-by-1, required-by-2, ...}
        #
        remaining = dict.fromkeys(fields)
        while remaining:
            to_add = []
            for f in remaining:
                m = self.get_handler(f)
                if m:
                    try:
                        dlist = m.depends()
                    except AttributeError:
                        # no dependencies
                        pass
                    else:
                        # Check dependencies
                        resolved = True
                        for d in dlist:
                            try:
                                self.depmap[d].add(f)
                            except KeyError:
                                self.depmap[d] = {f}
                            if d in remaining:
                                resolved = False
                            elif d not in ordered_fields:
                                # inefficient because of repetitions,
                                # but simple ...
                                dependencies.add(d)
                        if not resolved:
                            continue
                to_add.append(f)
            if to_add:
                for f in to_add:
                    ordered_fields.append(f)
                    remaining.pop(f)
            else:
                raise FieldHandlerError(_CIRCULAR_DEPENDENCIES.format(
                        fields = ', '.join(remaining)))
        return (ordered_fields, dependencies)

###

class FieldMap(dict):
    def __init__(self, manager, dict0):
        super().__init__(dict0)
        self.manager = manager
#
    def exec_(self, field, force = False):
        """If <force> is true, dependent fields with missing dependencies
        will use their own value. Otherwise missing dependencies will
        raise an exception.
        Return the processed field value (for display/print).
        """
        m = self.manager.get_handler(field)
        if m:
            return m.exec_(self, field, force)
        return self.value(field)
#
    def value(self, field):
        try:
            return self[field]
        except KeyError:
            raise FieldHandlerError(_MISSING_FIELD.format(field = field))
#
    def selection(self, field):
        """Return a selection "type" for the given field. If there is
        no special handler for the field, it is regarded as a text-line.
        Otherwise the "type" is got from the <values> method of the
        handler. If this method does not exist, <NONE> is returned,
        indicating a field whose value is derived from other fields.
        In order to handle such fields when the fields they depend on
        are not available – such is needed by the template-filler
        module – the <force_values> method of the handler is called.
        """
        m = self.manager.get_handler(field)
        if m:
            try:
                return m.values()
            except AttributeError:
                # Not an "input" field, it derives its value from other fields.
                try:
                    return m.force_values(self)
                except AttributeError:
                    pass
                return NONE
        return 'LINE'

####### ++++++++++++++++ The handlers ++++++++++++++++ #######

#WARNING: Be careful with transforming handlers. The saved value may not
# be the same as the displayed value!

# Format for printed dates (as used by <datetime.datetime.strftime>):
_DATE_FORMAT = '%d.%m.%Y'

### Messages
_BAD_DATE_VALUE = "DATE-Feld {field}: Ungültiger Wert ({value})"
_MAPSELECT_BAD_VALUE = "MAPSELECT-Feld {field}: Ungültiger Wert ({value})"
_MAPFROM_BAD_VALUE = "MAPFROM-Feld {field}: Ungültiger Wert ({value})"
_SELECT_BAD_VALUE = "SELECT-Feld {field}: Ungültiger Wert ({value})"
_FROM_BAD_FIELD = "FROM-Feld {field}: Feldquelle {source} unbekannt"
_MAPFROM_BAD_FIELD = "MAPFROM-Feld {field}: Feldquelle {source} unbekannt"
_IF_BAD_FIELD = "IF-Feld {field}: Feldquelle {source} unbekannt"
_UPPER_BAD_FIELD = "UPPER-Feld {field}: Feldquelle {source} unbekannt"
_MAPIF_BAD_FIELD = "MAPIF-Feld {field}: Feldquelle {source} unbekannt"

import datetime, re

class F_DATE:
    """Template value is a locale-determined representation (e.g.
    "06.12.2016") of the iso-date (e.g. "2016-12-06") stored in the
    field.
    In order to assist editing such a field, a calendar pop-up can be
    provided.
    """
    def exec_(self, fieldmap, field, force):
        """output value != field value
        The value is unchanged.
        """
        date = fieldmap.value(field)
        try:
            d = datetime.datetime.strptime(date, "%Y-%m-%d")
            return d.strftime(_DATE_FORMAT)
        except:
            if date:
                raise FieldHandlerError(_BAD_DATE_VALUE.format(
                        field = self.name, value = fieldmap.value(field)))
            return EMPTY
#
    def values(self):
        return 'DATE'

###

class F_TEXT:
    """Template value is a potentially multi-line text.
    In order to assist editing such a field, a text-area pop-up can be
    provided.
    """
#
    def exec_(self, fieldmap, field, force):
        """output value != field value.
        The value is unchanged.
        """
        return fieldmap.value(field)
#
    def values(self):
        return 'TEXT'

###

class F_IFEMPTY:
    """Shown value is customized when the field is empty, e.g.:
        S.*: [IFEMPTY ––––––––––]
    """
    def __init__(self, no_entry):
        self.no_entry = no_entry
#
    def exec_(self, fieldmap, field, force):
        """output value != field value
        The value is unchanged.
        """
        val = fieldmap.value(field)
        if val:
            return val
        else:
            return self.no_entry
#
    def values(self):
        return 'LINE'

###

class F_SELECT:
    """Field value may be one of the given values.
    """
    def __init__(self, value_list):
        self.value_list = value_list
#
    def exec_(self, fieldmap, field, force):
        """output value == field value
        The field value will be cleared if it was invalid.
        """
        value = fieldmap.value(field)
        if value in self.value_list:
            return value
        if value:
            fieldmap[field] = NONE
            raise FieldHandlerError(_SELECT_BAD_VALUE.format(
                    field = self.name, value = value))
        return EMPTY
#
    def values(self):
        return [self.name, self.value_list.copy()]

###

class F_MAPSELECT:
    """Like SELECT, but the selected value will be transformed via the
    mapping for insertion in the template.
    """
    def __init__(self, value_map):
        self.value_map = value_map
#
    def exec_(self, fieldmap, field, force):
        """output value != field value
        The field value will be cleared if it was invalid.
        """
        value = fieldmap.value(field)
        try:
            return self.value_map[value]
        except KeyError:
            if value:
                fieldmap[field] = NONE
                raise FieldHandlerError(_MAPSELECT_BAD_VALUE.format(
                        field = self.name, value = value))
            return EMPTY
#
    def values(self):
        return [self.name, list(self.value_map)]

###

class F_MAPIF(F_MAPSELECT):
    """Like MAPSELECT, but make the selection display conditional on
    another field being set.
    """
    def __init__(self, source_field, no_entry, value_map):
        super().__init__(value_map)
        self.source_field = source_field
        self.no_entry = no_entry
#
    def exec_(self, fieldmap, field, force):
        """output value != field value
        The field value will be cleared if it was invalid.
        """
        source = self.source_field
        try:
            wildmatch = fieldmap.manager.wildmatches[field]
            if wildmatch:
                source = source.replace('*', wildmatch)
        except KeyError:
            pass
        try:
            cond = fieldmap[source]
        except KeyError:
            # This makes no sense without the source field, so raise an
            # exception even if force is true
            raise FieldHandlerError(_MAPIF_BAD_FIELD.format(
                    field = self.name, source = source))
        if cond:
            return super().exec_(fieldmap, field, force)
        return self.no_entry

###

class F_FROM:
    """Simply copy a field value from another field.
    """
    def __init__(self, source_field, ftype = None):
        self.field_type = ftype or 'LINE'
        self.source_field = source_field
#
    def exec_(self, fieldmap, field, force):
        """output value == field value
        The field value will be updated if the source has changed.
        """
        try:
            value = fieldmap[self.source_field]
            fieldmap[field] = value
        except KeyError:
            if not force:
                raise FieldHandlerError(_FROM_BAD_FIELD.format(
                        field = self.name, source = self.source_field))
            value = fieldmap.value(field)
        return value
#
    def depends(self):
        return [self.source_field]
#
    def force_values(self, fieldmap):
        if self.source_field in fieldmap:
            return NONE   # dependent on existing field
        return self.field_type

###

class F_UPPER:
    """Field value is upper cased version of source field.
    """
    def __init__(self, source_field):
        self.source_field = source_field
#
    def exec_(self, fieldmap, field, force):
        """output value == field value
        The field value will be updated if the source has changed.
        """
        try:
            value = fieldmap[self.source_field].upper()
            fieldmap[field] = value
        except KeyError:
            if not force:
                raise FieldHandlerError(_UPPER_BAD_FIELD.format(
                        field = self.name, source = self.source_field))
            value = fieldmap.value(field)
        return value
#
    def depends(self):
        return [self.source_field]
#
    def force_values(self, fieldmap):
        if self.source_field in fieldmap:
            return NONE   # dependent on existing field
        return 'LINE'

###

class F_MAPFROM:
    def __init__(self, source_field, value_map):
        self.source_field = source_field
        self.value_map = value_map
#
    def exec_(self, fieldmap, field, force):
        """output value != field value
        The field value will be updated if the source has changed.
        """
        try:
            value = fieldmap[self.source_field]
        except KeyError:
            if not force:
                raise FieldHandlerError(_MAPFROM_BAD_FIELD.format(
                        field = self.name, source = self.source_field))
            value = fieldmap.value(field)
            try:
                return self.value_map[value]
            except KeyError:
                if value:
                    fieldmap[field] = NONE
                    raise FieldHandlerError(_MAPFROM_BAD_VALUE.format(
                            field = self.name, value = value))
        else:
            try:
                val = self.value_map[value]
                fieldmap[field] = val
                return val
            except KeyError:
                if value:
                    fieldmap[self.source_field] = NONE
                    raise FieldHandlerError(_MAPFROM_BAD_VALUE.format(
                            field = self.source_field, value = value))
        return EMPTY
#
    def depends(self):
        return [self.source_field]
#
    def force_values(self, fieldmap):
        if self.source_field in fieldmap:
            return NONE   # dependent on existing field
        return [self.name, list(self.value_map)]

###

class F_IF:
    def __init__(self, source_field, trueval, falseval):
        self.source_field = source_field
        self.trueval = trueval
        self.falseval = falseval
#
    def exec_(self, fieldmap, field, force):
        """output value == field value
        The field value will be updated if the source has changed.
        """
        try:
            value = fieldmap[self.source_field]
        except KeyError:
            if not force:
                raise FieldHandlerError(_IF_BAD_FIELD.format(
                        field = self.name, source = self.source_field))
            return fieldmap.value(field)
        val = self.trueval if value else self.falseval
        fieldmap[field] = val
        return val
#
    def depends(self):
        return [self.source_field]
#
    def force_values(self, fieldmap):
        if self.source_field in fieldmap:
            return NONE   # dependent on existing field
        return 'LINE'


HANDLERS = {k[2:]: v for k, v in locals().items() if k[:2] == 'F_'}

#### ------------------------------------------------------------ ####

if __name__ == '__main__':
    print("\nHANDLERS:", HANDLERS)

    mh = ManageHandlers({
        'COMMENT': ['FROM', '*B_T'],
        'LEVEL': ['MAPFROM', 'STREAM', {
            'Gym': 'Gymnasium',
            'RS': 'Realschule',
            'HS': 'Hauptschule'
            }],
        'NOCOMMENT': ['IF', 'COMMENT', '', '––––––––––'],
        'G.*': ['MAPSELECT', {
            '1': 'sehr gut',
            '2': 'gut',
            '3': 'befriedigend',
            '4': 'ausreichend',
            '5': 'mangelhaft',
            '6': 'ungenügend',
            'nt': 'nicht teilgenommen>>>',
            't': 'teilgenommen',
            'nb': 'kann nicht beurteilt werden',
            '*': '––––––'
            }]
    })

    fields = FieldMap(mh, {'G1': '4'})
    print(" ==>", mh['G.*'].exec_(fields, 'G1', False))
