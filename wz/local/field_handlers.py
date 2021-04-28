# -*- coding: utf-8 -*-
"""
field_handlers.py - last updated 2021-04-28

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
_BAD_HANDLER_CALL = "Fehler beim Verarbeiten vom Händler {tag}\n" \
        " ... wahrscheinlich falsche Parameteranzahl:\n" \
        "  {handler}: {parms}"
_MISSING_FIELD = "{field}: Feld nicht bekannt"
_NO_YEAR = "Kein Schuljahr im Feld {field}"
_NO_CLASS = "Keine Klasse im Feld {field}"

########################################################################

NONE = ''

### +++++

class FieldHandlerError(Exception):
    pass

class EmptyField(Exception):
    pass

###

#TODO: Perhaps shouldn't use '*' as normal part of field name ('*B_T',
# etc.), because of possible interference with its use as a "joker".
# Use '+' instead. Maybe '$' instead of '.'?


class FieldMap(dict):
    """This manages fields and their values, especially for templates
    but it could also be used by a grade table, for example.

    Also special handlers for particular fields are possible. Firstly
    they allow a field value to be formatted differently for display
    (print, etc.) purposes – the value undergoes some sort of processing
    rather than being directly entered into the template.
    It is also possible to provide processing which depends on the
    values of other fields.
    Particular types of input validation or entry (e.g. list selection
    or date entry) can be specified.

    The special handlers are are provided as a <dict>:
        {handler: definition, ...},
    or multiple <dicts> by using the method <add_handlers> (repeatedly).

    Normally handlers are specified by keying on the field name, but by
    including a wild-card ('*') in the key, the same handler definition
    can be used for multiple field names.

    The handlers themselves are provided as classes with names starting
    'F_' (followed by the "type-name" of the handler).
    """
    def __init__(self, dict0):
        super().__init__(dict0)
        self.handlers = {}
        self.normaltags = {}
        self.generictags = []
#
    def add_handlers(self, handler_map):
        if handler_map:
            for tag, handler in handler_map.items():
                htype, params = handler[0], handler[1:]
                _h = HANDLERS[htype]
                try:
                    h = _h.init(htype, tag, *params)
                except TypeError:
                    # Probably wrong number of arguments
                    raise FieldHandlerError(_BAD_HANDLER_CALL.format(
                            tag = tag, handler = htype,
                            parms = repr(params)))
                h['handler'] = _h
                if 'rex' in h:
                    self.generictags.append(h)
                else:
                    self.normaltags[tag] = h
#
    def get_handler(self, field):
        """Fetch the "special handler" for the given field, if there is
        one.
        Return the handler, or <None> if there is no special handler for
        the field.
        """
        # Use a cache for the handlers
        try:
            return self.handlers[field]
        except KeyError:
            pass
        try:
            _h = self.normaltags[field]
        except KeyError:
            # Not found, try a "generic":
            for _h in self.generictags:
                try:
                    h = _h['handler'](field, _h)
                    break
                except _NoMatch:
                    pass
            else:
                return None
        else:
            # A "normal" field handler
            h = _h['handler'](field, _h)
        self.handlers[field] = h
        return h
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
                            if d in remaining:
                                resolved = False
                                break
                        if not resolved:
                            continue
                        for d in dlist:
                            if d not in ordered_fields:
                                # potentially inefficient because of
                                # repetitions, but simple ...
                                dependencies.add(d)
                            try:
                                self.depmap[d][f] = None
                            except KeyError:
                                self.depmap[d] = {f: None}
                to_add.append(f)
            if to_add:
                for f in to_add:
                    ordered_fields.append(f)
                    remaining.pop(f)
            else:
                raise FieldHandlerError(_CIRCULAR_DEPENDENCIES.format(
                        fields = ', '.join(remaining)))
        return (ordered_fields, dependencies)
#
    def exec_(self, field, value = None, trap_empty = False):
        """If <value> is provided, this will be used as value by
        dependent fields with missing dependencies. Otherwise missing
        dependencies will raise a <FieldHandlerError> exception.
        If <trap_empty> is true, empty fields – and fields depending
        on empty fields – will cause an <EmptyField> exception to be
        raised. This allows for such fields to remain unsubstituted.
        Return the processed field value (for display/print).
        """
        m = self.get_handler(field)
        if m:
            return m.exec_(self, field, value, trap_empty)
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
        m = self.get_handler(field)
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

"""Handler instances provide methods for dealing with template fields.
Each field has a handler, its class depending on the definition in
a source file. The value of a field with no handler is simply passed
on unchanged.
Some fields depend on others. Such a field has a <depends> method
returning a list of the fields it depends on.

It is possible that a template is normally supplied with data using
different field names or data which is not formatted correctly for the
intended usage. The handler for a field which uses this data will then
depend on this "external" data and use it to prepare a value for the
field in question. In the case of the template-filler module, this data
is not available, so the data must be supplied directly by means of the
<value> parameter to the <exec_> method. This value is used only when
"external" data sources are not available.
Note that there can still be a reformatting of the value for
display purposes, that is independent of the processing required to
get the internal value.
To communicate to a handler that it should use internal rather than
external data, there is a <value> parameter to the <exec_> method.

This is managed in a two-stage process. First the definition of the
handlers is read as <dict> and pre-processed by the static method
<init> of the corresponding handler class. This returns a data structure
which can be provided to the class as instantiation data when needed for
handling a particular field. It is done like this because some special
processing is needed for handlers where the "key" has a wildcard.
Without this feature, the two stages would not be necessary. It means
certain information can be shared among all instances using this key.
(with no wildcard there will be only one instance).
"""

class _NoMatch(Exception):
    pass
#
class FieldHandler:
    @staticmethod
    def init(htype, tag):
        h = {'name': tag, 'type': htype}
        # Test for a wild-card in the field name
#TODO: If I stop using '*' as a "subject" prefix, I can remove the
# second part of the test:
        if tag.count('*') == 1 and tag[0] != '*':
            # The tag contains a wildcard
            rex0 = re.escape(tag.replace('*', '@'))
            h['rex'] = rex0.replace('@', '(.*)') + '$'
        return h
#
    def __init__(self, field, data):
        try:
            rex = data['rex']
        except KeyError:
            # This is a normal field
            pass
        else:
            # This is a "generic" field.
            m = re.match(rex, field)
            if m:
                self.wildmatch = m.group(1)
            else:
                raise _NoMatch
        self.name = field

###

class F_DATE(FieldHandler):
    """Handler for a "standard" date field.
    Deliver a locale-determined representation (e.g. "06.12.2016") of
    the iso-date (e.g. "2016-12-06") stored in the field.
    In order to assist editing such a field, a calendar pop-up can be
    provided.
    """
    def exec_(self, fieldmap, field, value, trap_empty):
        """output value != field value
        The value is unchanged.
        """
        date = fieldmap.value(field)
        if (not date) and trap_empty:
            raise EmptyField
        try:
            d = datetime.datetime.strptime(date, "%Y-%m-%d")
            return d.strftime(_DATE_FORMAT)
        except:
            raise FieldHandlerError(_BAD_DATE_VALUE.format(
                    field = self.name, value = date))
#
    def values(self):
        return 'DATE'

###

class F_TEXT(FieldHandler):
    """Template value is a potentially multi-line text.
    In order to assist editing such a field, a text-area pop-up can be
    provided.
    """
#
    def exec_(self, fieldmap, field, value, trap_empty):
        """output value != field value.
        The value is unchanged.
        """
        val = fieldmap.value(field)
        if (not val) and trap_empty:
            raise EmptyField
        return val

#
    def values(self):
        return 'TEXT'

###

class F_IFEMPTY(FieldHandler):
    """Shown value is customized when the field is empty, e.g.:
        S.*: [IFEMPTY ––––––––––]
    """
    @classmethod
    def init(cls, htype, tag, no_entry):
        h = super().init(htype, tag)
        h['no_entry'] = no_entry
        return h
#
    def __init__(self, field, data):
        super().__init__(field, data)
        self.no_entry = data['no_entry']
#
    def exec_(self, fieldmap, field, value, trap_empty):
        """output value != field value
        The value is unchanged.
        """
        val = fieldmap.value(field)
        if val:
            return val
        if trap_empty:
            raise EmptyField
        return self.no_entry
#
    def values(self):
        return 'LINE'

###

class F_SELECT(FieldHandler):
    """Field value may be one of the given values.
    """
    @classmethod
    def init(cls, htype, tag, value_list):
        h = super().init(htype, tag)
        h['value_list'] = value_list
        return h
#
    def __init__(self, field, data):
        super().__init__(field, data)
        self.validation = data['name']
        self.value_list = data['value_list']
#
    def exec_(self, fieldmap, field, value, trap_empty):
        """output value == field value
        The field value will be cleared if it was invalid.
        """
        val = fieldmap.value(field)
        if (not val) and trap_empty:
            raise EmptyField
        if val in self.value_list:
            return val
        fieldmap[field] = NONE
        raise FieldHandlerError(_SELECT_BAD_VALUE.format(
                field = self.name, value = val))
#
    def values(self):
        return [self.validation, self.value_list.copy()]

###

class F_MAPSELECT(FieldHandler):
    """Like SELECT, but the selected value will be transformed via the
    mapping for insertion in the template.
    """
    @classmethod
    def init(cls, htype, tag, value_map):
        h = super().init(htype, tag)
        h['value_map'] = value_map
        return h
#
    def __init__(self, field, data):
        super().__init__(field, data)
        self.validation = data['name']
        self.value_map = data['value_map']
#
    def exec_(self, fieldmap, field, value, trap_empty):
        """output value != field value
        The field value will be cleared if it was invalid.
        """
        val = fieldmap.value(field)
        if (not val) and trap_empty:
            raise EmptyField
        try:
            return self.valmod(val)
        except KeyError:
            fieldmap[field] = NONE
            raise FieldHandlerError(_MAPSELECT_BAD_VALUE.format(
                    field = self.name, value = value))
#
    def valmod(self, value):
        """This allows subclasses to easily add preprocessing to the
        internal value before using it as key to the lookup table.
        """
        return self.value_map[value]
#
    def values(self):
        return [self.validation, list(self.value_map)]

###

class F_MAPIF(F_MAPSELECT):
    """Like MAPSELECT, but make the selection display conditional on
    another field being set.
    """
    @classmethod
    def init(cls, htype, tag, source_field, no_entry, value_map):
        h = super().init(htype, tag, value_map)
        h['source_field'] = source_field
        h['no_entry'] = no_entry
        return h
#
    def __init__(self, field, data):
        super().__init__(field, data)
        self.validation = data['name']
        self.value_map = data['value_map']
        try:
            self.source_field = data['source_field'].replace('?',
                    self.wildmatch)
        except AttributeError:
            self.source_field = data['source_field']
        self.no_entry = data['no_entry']
#
    def exec_(self, fieldmap, field, value, trap_empty):
        """output value != field value
        The field value will be cleared if it was invalid.
        """
        try:
            cond = fieldmap[self.source_field]
        except KeyError:
            # This makes no sense without the source field, so raise an
            # exception even if value is provided
            raise FieldHandlerError(_MAPIF_BAD_FIELD.format(
                    field = self.name, source = self.source_field))
        if cond:
            return super().exec_(fieldmap, field, value, trap_empty)
        elif trap_empty:
            raise EmptyField
        return self.no_entry

###

class F_FROM(FieldHandler):
    """Simply copy a field value from another field.
    """
    @classmethod
    def init(cls, htype, tag, source_field, ftype = None):
        h = super().init(htype, tag)
        h['source_field'] = source_field
        h['field_type'] = ftype or 'LINE'
        return h
#
    def __init__(self, field, data):
        super().__init__(field, data)
        self.field_type = data['field_type']
        try:
            self.source_field = data['source_field'].replace('?',
                    self.wildmatch)
        except AttributeError:
            self.source_field = data['source_field']
#
    def exec_(self, fieldmap, field, value, trap_empty):
        """output value == field value
        The field value will be updated if the source has changed.
        """
        if value == None:
            try:
                value = fieldmap[self.source_field]
            except KeyError:
                raise FieldHandlerError(_FROM_BAD_FIELD.format(
                        field = self.name, source = self.source_field))
        fieldmap[field] = value
        if (not value) and trap_empty:
            raise EmptyField
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

class F_UPPER(FieldHandler):
    """Field value is upper cased version of source field.
    """
    @classmethod
    def init(cls, htype, tag, source_field):
        h = super().init(htype, tag)
        h['source_field'] = source_field
        return h
#
    def __init__(self, field, data):
        super().__init__(field, data)
        try:
            self.source_field = data['source_field'].replace('?',
                    self.wildmatch)
        except AttributeError:
            self.source_field = data['source_field']
#
    def exec_(self, fieldmap, field, value, trap_empty):
        """output value == field value
        The field value will be updated if the source has changed.
        """
        try:
            val = fieldmap[self.source_field].upper()
        except KeyError:
            if value == None:
                raise FieldHandlerError(_UPPER_BAD_FIELD.format(
                        field = self.name, source = self.source_field))
            val = value.upper()
        fieldmap[field] = val
        if (not val) and trap_empty:
            raise EmptyField
        return val
#
    def depends(self):
        return [self.source_field]
#
    def force_values(self, fieldmap):
        if self.source_field in fieldmap:
            return NONE   # dependent on existing field
        return 'LINE'

###

class F_MAPFROM(FieldHandler):
    @classmethod
    def init(cls, htype, tag, source_field, value_map):
        h = super().init(htype, tag)
        h['source_field'] = source_field
        h['value_map'] = value_map
        return h
#
    def __init__(self, field, data):
        super().__init__(field, data)
        try:
            self.source_field = data['source_field'].replace('?',
                    self.wildmatch)
        except AttributeError:
            self.source_field = data['source_field']
        self.value_map = data['value_map']
#
    def exec_(self, fieldmap, field, value, trap_empty):
        """output value != field value
        The field value will be updated if the source has changed.
        """
        if value == None:
            try:
                value = fieldmap[self.source_field]
            except KeyError:
                raise FieldHandlerError(_MAPFROM_BAD_FIELD.format(
                        field = self.name, source = self.source_field))
        fieldmap[field] = value
        if (not value) and trap_empty:
            raise EmptyField
        try:
            return self.value_map[value]
        except KeyError:
            fieldmap[field] = NONE
            raise FieldHandlerError(_MAPFROM_BAD_VALUE.format(
                    field = self.name, value = value))
#
    def depends(self):
        return [self.source_field]
#
    def force_values(self, fieldmap):
        if self.source_field in fieldmap:
            return NONE   # dependent on existing field
        return [self.name, list(self.value_map)]

###

class F_IF(FieldHandler):
    @classmethod
    def init(cls, htype, tag, source_field, trueval, falseval):
        h = super().init(htype, tag)
        h['source_field'] = source_field
        h['trueval'] = trueval
        h['falseval'] = falseval
        return h
#
    def __init__(self, field, data):
        super().__init__(field, data)
        try:
            self.source_field = data['source_field'].replace('?',
                    self.wildmatch)
        except AttributeError:
            self.source_field = data['source_field']
        self.trueval = data['trueval']
        self.falseval = data['falseval']
#
    def exec_(self, fieldmap, field, value, trap_empty):
        """output value == field value
        The field value will be updated if the source has changed.
        """
        try:
            value = fieldmap[self.source_field]
        except KeyError:
            # This makes no sense without the source field, so raise an
            # exception even if value is provided
            raise FieldHandlerError(_IF_BAD_FIELD.format(
                    field = self.name, source = self.source_field))
        if (not value) and trap_empty:
            raise EmptyField
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

## +++ Special handlers for particular fields +++ ##

# This is a bit of a bodge to allow the test code to run ...
if __name__ != '__main__': from local.base_config import print_schoolyear

class F_SCHOOLYEAR(FieldHandler):
    """Handler for the school-year representation.
    """
    def exec_(self, fieldmap, field, value, trap_empty):
        """output value != field value
        The value is unchanged.
        """
        val = fieldmap.value(field)
        if val:
            return print_schoolyear(val)
        if trap_empty:
            raise EmptyField
        raise FieldHandlerError(_NO_YEAR.format(field = field))
#
    def values(self):
        return 'LINE'

###

# This is a bit of a bodge to allow the test code to run ...
if __name__ != '__main__': from local.base_config import print_class

class F_CLASS(FieldHandler):
    """Handler for the school-class representation.
    """
    def exec_(self, fieldmap, field, value, trap_empty):
        """output value != field value
        The value is unchanged.
        """
        val = fieldmap.value(field)
        if val:
            return print_class(val)
        if trap_empty:
            raise EmptyField
        raise FieldHandlerError(_NO_CLASS.format(field = field))
#
    def values(self):
        return 'LINE'

###

#TODO: This is just an idea ...
class F_MAPSELECT_GRADE(F_MAPSELECT):
    """Like SELECT, but the selected value will be transformed via the
    mapping for insertion in the template. This is a special version
    for grades, stripping off + and -.
    """
    def valmod(self, value):
        return self.value_map[value.rstrip('+-')]



HANDLERS = {k[2:]: v for k, v in locals().items() if k[:2] == 'F_'}

#### ------------------------------------------------------------ ####

if __name__ == '__main__':
    print("\nHANDLERS:", HANDLERS)

    fieldmap = FieldMap({'G.1': '4-'})
    fieldmap.add_handlers({
        'COMMENT': ['FROM', '*B_T'],
        'LEVEL': ['MAPFROM', 'STREAM', {
            'Gym': 'Gymnasium',
            'RS': 'Realschule',
            'HS': 'Hauptschule'
            }],
        'NOCOMMENT': ['IF', 'COMMENT', '', '––––––––––'],
        'G.*': ['MAPSELECT_GRADE', {
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

    print(" ==>", fieldmap.exec_('G.1', None))
