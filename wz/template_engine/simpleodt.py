#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
simpleodt.py - last updated 2021-04-11

1) OdtReader
=============
Read the text content of odt files ignoring all formatting/style information.

2) OdtFields
===============
(a) Fetch the names of the "fields" from a LibreOfffice Writer file.
(b) Fill the "fields" in a LibreOfffice Writer file.

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
_MULTILINE_NO_PARA = "Mehrzeiliger Feld-Text, aber Feld ({tag}) nicht Absatz"

import sys, os
if __name__ == '__main__':
    # Enable package import if running as module for testing
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

import zipfile as zf
import io, re

import xmltodict

"""
    odt-format
    ===========

    The content is found in the file "content.xml".
    The following seems to be the simplest possible structure for paragraphs:

    1) An empty paragraph:
        <text:p text:style-name="Standard"/>

    2) With text:
        <text:p text:style-name="P1">[[geo AB 10_G]] Geographie; Arthur Benommen.
        </text:p>

        It looks like the text:style-name="P1" bit is not compulsory, but libreoffice
        seems to add it if it is not there.

    However, formatting information is embedded ...
        <text:p text:style-name="Standard">Mit etwas Text und – um die Sache
            <text:span text:style-name="T1">interessant</text:span>
            zu machen – etwas
            <text:span text:style-name="T2">Formatierung</text:span>
            !
        </text:p>

    As the zip file is unpacked to a byte array, all 'strings' used here
    must also be byte arrays.
    As far as I can tell, the encoding should always be utf-8 ...
"""

_ODT_CONTENT_FILE = 'content.xml'
_ODT_META_FILE = 'meta.xml'

from xml.parsers.expat import ParserCreate
from xml.sax.saxutils import escape

###

def xmlescape(text):
    return escape(text, entities = {
            "'": "&apos;",
            "\"": "&quot;"
        })

###

class DocumentError(Exception):
    pass

###

def substituteZipContent(infile, process = None, metaprocess = None):
    """Process the contents of an odt file using the function <process>.
    Return the resulting odt file as a <bytes> array.
    Normally the contents will be read.
    However, by setting <metaprocess> to a function, the metadata can
    be read.
    When information is to be read from the odt-file, rather than
    performing a transformation, only one processing function should be
    supplied and it should return an empty value: this will terminate
    the whole function early, returning <None>. The information to be
    read out must be extracted within the processing function and saved
    separately (see, for example, the "listUserFields" function).
    """
    sio = io.BytesIO()
    with zf.ZipFile(sio, "w", compression=zf.ZIP_DEFLATED) as zio:
        with zf.ZipFile(infile, "r") as za:
            for fin in za.namelist():
                indata = za.read(fin)
                if fin == _ODT_CONTENT_FILE and process:
                    indata = process(indata)
                    if not indata:
                        return None
                elif fin == _ODT_META_FILE and metaprocess:
                    indata = metaprocess(indata)
                    if not indata:
                        return None
                zio.writestr(fin, indata)
    return sio.getvalue()

###

class OdtFields:
    """Manage substitution of "fields" in an odt document.
    A field is a text snippet like "[[key]]". The key may contain ASCII
    letters, digits, '.' and '_', but must start with a letter.

    During editing these can get split up by intervening XML tags, etc.
    In order to avoid this they should have all formatting removed and
    then reapplied when editing is complete.

    If the field is the only content of a paragraph, the substition text
    may include line breaks. The resulting paragraphs will have the same
    style as the field's paragraph. Only snippets in the 'content.xml'
    file matching the following can be used in this way:
        <text:p text:style-name="style_name">[[tag]]</text:p>
    """
    _tagex = br'\[\[([a-zA-Z][a-zA-Z._0-9]*)\]\]'
    _parex = br'<text:p text:style-name="([a-zA-Z_0-9]*)">%s</text:p>' % _tagex
    _combex = br'%s|%s' % (_parex, _tagex)
#
    @classmethod
    def listUserFields(cls, odtfile):
        """List all tag-fields.
        If the tag field is the only item in a paragraph, also the
        paragraph style can be read.
        Return a tuple: (tag, style or <None>)
        The regular expression parses
            <text:p text:style-name="style_name">[[tag]]</text:p>
        or
            [[tag]]
        in the xml content file.
        """
        tagmap = []
        def _process(xmldata):
            for vals in re.findall(cls._combex, xmldata):
                style = vals[0] or None
                if style:
                    tagmap.append((vals[1].decode('utf-8'),
                            style.decode('utf-8')))
                else:
                    tagmap.append((vals[2].decode('utf-8'), None))
            return None

        substituteZipContent(odtfile, _process)
        return tagmap
#
    @classmethod
    def fillUserFields(cls, odtfile, itemdict, FIELD_INFO = None):
        """<odtfile> is the full file-path to the template file.
        <itemdict> is a mapping of field values, the substitutions.
        <FIELD_INFO> may be a <str>, specifying a new "comment" metadata
        ("dc.description"). If the value is '', the metadata item
        will be removed.
        """
        useditems = set()
        nonitems = set()
#
        def _sub(rem):
            #print(":::", rem.group(0), "->")
            style = rem.group(1) or None
            # The tags are converted to <str> so that the item mapping
            # doesn't need to work with <bytes>.
            if style:
                tag = rem.group(2).decode('utf-8')
            else:
                tag = rem.group(3).decode('utf-8')
            try:
                item = itemdict[tag]
                if item == None:
                    raise Bug("tag '%s': None" % tag)
                sub_string = xmlescape(item).encode('utf-8')
                useditems.add(tag)
            except KeyError:
                nonitems.add(tag)
                if itemdict:
                    # If the tag mapping is not empty, leave the tag field
                    return rem.group(0)
                sub_string = ('{' + tag + '}').encode('utf-8')
            lines = sub_string.splitlines()
            if style:
                ## Reconstruct the paragraph
                # Get paragraph prefix
                para = rem.group(0).split(b'[', 1)[0]
                # Build the lines
                sub_lines = [para + line + b'</text:p>' for line in lines]
                sub_string = b''.join(sub_lines)
            elif len(lines) > 1:
                raise DocumentError(_MULTILINE_NO_PARA.format(tag = tag))
            #print(sub_string)
            return sub_string
#
        def _process(xmldata):
            """Use the regular expression to find all field declarations.
            Those for which an entry is provided in <itemdict> will have
            their values substituted.
            """
            return re.sub(cls._combex, _sub, xmldata)
#
        def _metaprocess(xmldata):
            """Remove user-defined fields.
            """
            if FIELD_INFO:
                bc = b'<dc:description>%s</dc:description>' % \
                        escape(FIELD_INFO).encode('utf-8')
            else:
                bc = b''
            return re.sub(b'<dc:description>[^<]*</dc:description>',
                    bc, xmldata)

        odtBytes = substituteZipContent(odtfile, _process,
                metaprocess = None if FIELD_INFO == None else _metaprocess)
        return (odtBytes, useditems, nonitems)

###

class Metadata:
    """Manage the metadata of an odt-file (it could also be used on an
    ods-file).
    """
    def __init__(self, odtfile):
        """<odtfile> is the full path to the file to be processed.
        Its metadata will be read (to <self.xmldict>).
        """
        self.odtfile = odtfile
        substituteZipContent(odtfile, metaprocess = self._process)
#
    def _process(self, xmldata):
        self.xmldict = xmltodict.parse(xmldata)
        self.office_meta = self.xmldict['office:document-meta']['office:meta']
        return None
#
    def doc_meta(self):
        kv = {}
        for k, v in self.office_meta.items():
            try:
                k1, k2 = k.split(':', 1)
            except ValueError:
                continue
            if k1 == 'dc':
                kv[k2] = v
        return kv
#
    def user_meta(self):
        kv = {}
        for ud in self.office_meta.get('meta:user-defined', []):
            try:
                kv[ud['@meta:name']] = ud['#text']
            except KeyError:
                pass
        return kv
#
    def replace(self, data = None, dc = None):
        """If <data> is supplied, all existing user-meta data will be
        removed. It should be a <dict> containing new
        user-meta values. This can be an empty <dict>.
        If <dc> is supplied, it should be a <dict> containing new
        values for selected items of the "dc:" metadata An item can be
        removed by giving it value ''.
        Return the resulting odt-file as a <bytes> array.
        """
        def _replace(xmldata):
            if data:
                self.office_meta['meta:user-defined'] = [
                    {   '@meta:name': k,
                        '@meta:value-type': 'string',
                        '#text': v
                    } for k, v in data.items()]
            elif data != None:
                self.office_meta.pop('meta:user-defined', None)
            if dc:
                for k, v in dc.items():
                    if v:
                        self.office_meta['dc:' + k] = v
                    else:
                        self.office_meta.pop('dc:' + k, None)
            return xmltodict.unparse(self.xmldict).encode('utf-8')
        #+
        return substituteZipContent(self.odtfile, metaprocess = _replace)
"""
Note that only <, > and & are escaped as XML-entities. LibreOffice also
escapes " and '. However, this does not seem to be necessary, LibreOffice
will apparently quite happily read in these characters unescaped.
Keys with escaped characters should probably be avoided completely.
If escaping of " and ' in the generated XML is desired, it is probably
necessary to patch xmltodict

At the top, replace the import of XMLGenerator:

from xml.sax.saxutils import XMLGenerator as Generator
from xml.sax.saxutils import escape
class XMLGenerator(Generator):
    def characters(self, content):
        if content:
            self._finish_pending_start_element()
            if not isinstance(content, str):
                content = str(content, self._encoding)
            self._write(escape(content, entities = {
                    "'": "&apos;",
                    "\"": "&quot;"
                }))

"""

###

class OdtReader:
    """Uses the expat parser to get at the paragraphs and their contained data.
    All formatting information is ignored, and complicated structures
    may cause parsing errors.
    An xml string is parsed to a list of paragraphs (without '\n'). This
    string is normally the 'content.xml' within an odt file (which is a
    zip archive). The file path is passed to <OdtReader.readOdtFile>.
    However, the function <OdtReader.parseXML> is also available to parse
    <bytes> data directly.

    Note that the expat parser converts all items to unicode.

    An instance of the expat parser can only handle a single file, so
    a new instance must be created for each file to be parsed.
    """
    _lines = None
    _text = None
#
    @classmethod
    def parseXML(cls, xmldata):
        parser = ParserCreate()

        parser.StartElementHandler = cls._start_element
        parser.EndElementHandler = cls._end_element
        parser.CharacterDataHandler = cls._char_data

        cls._lines = []
        parser.Parse(xmldata)
        return cls._lines
#
    ############ 3 handler functions ############
#
    @classmethod
    def _start_element(cls, name, attrs):
        #print('>>> Start element:', name, attrs)
        if name == 'text:p':
            if cls._text != None:
                raise DocumentError('OdtNestedParagraph')
            cls._text = ""
#
    @classmethod
    def _end_element(cls, name):
        #print('>>> End element:', name)
        if name == 'text:p':
            if cls._text == None:
                raise DocumentError('OdtParagraphEnd')
            cls._lines.append(cls._text)
            cls._text = None
#
    @classmethod
    def _char_data(cls, data):
        #print('>>> Character data:', type (data), repr(data))
        if cls._text == None:
            raise DocumentError('OdtBadData')
        else:
            cls._text += data
#
    ############ end handler functions ############
#
    @classmethod
    def readOdtFile(cls, filepath):
        xmldata = cls._getOdtContent(filepath)
        return cls.parseXML(xmldata)
#
    @staticmethod
    def _getOdtContent(filepath):
        """Returns the content xml file – I assume always bytes encoded as utf-8.
        """
        with zf.ZipFile(filepath) as zipfile:
            xmlbytes = zipfile.read(_ODT_CONTENT_FILE)
        return xmlbytes
#
    @classmethod
    def readFile(cls, xmlfile):
        with open(xmlfile, "rb") as fi:
            xmldata = fi.read()
        return cls.parseXML(xmldata)


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

########################################################################
#Setting a variable (which is already defined in the file) in an odt:
#<text:variable-set text:name="hide1" office:value-type="float" office:value="0" style:data-style-name="N0">0</text:variable-set>
########################################################################

if __name__ == '__main__':
    from core.base import init
    init()

    _filename = 'SekI.odt'
    _odtfile = os.path.join(DATA, 'testing', _filename)
    md = Metadata(_odtfile)
    print("\nMETADATA (normal):", md.doc_meta())
    print("\nMETADATA (user):", md.user_meta())

    _odir = os.path.join(DATA, 'testing', 'tmp')
    os.makedirs(_odir, exist_ok = True)
    _out = os.path.join(_odir, 'MOD0_' + _filename)
    with open(_out, 'wb') as fh:
        fh.write(md.replace(dc = {'description': '', 'title': 'New "Title"'}))
    print("\nWrote (with new meta-data)" + _out)
    md = Metadata(_odtfile)
    _out = os.path.join(_odir, 'MOD1_' + _filename)
    with open(_out, 'wb') as fh:
        fh.write(md.replace(data =
            {   'USER-DATA': 'First entry',
                'NEW.*_': 'Just added this: <&> öÄüß§€'
            })
        )
    print("\nWrote (with new custom meta-data)" + _out)

#    quit(0)

    _odtfile = os.path.join(DATA, 'testing', 'testdoc.odt')
    _out = os.path.join(_odir, 'testdoc_1.odt')
    odtBytes, used, notsub = OdtFields.fillUserFields(_odtfile,
            {'TITLE': 'Zeugnisse ...'}, FIELD_INFO = '')
    with open(_out, 'bw') as fout:
        fout.write(odtBytes)

    print("\nREAD:", _odtfile)
    for l in OdtReader.readOdtFile(_odtfile):
        print("§§§", l)

    _odtfile = os.path.join(DATA, 'testing', 'SekI.odt')
    print("\n USER FIELDS:")
    for match in OdtFields.listUserFields(_odtfile):
        print("  ::", match)
#    _itemdict = {}
    _school = 'Freie Michaelschule'
    _itemdict = {
        'SCHOOL': _school,
        'SCHOOLBIG': _school.upper(),
        'CLASS': '11',
        'SCHOOLYEAR': '2015 – 2016',
        'FIRSTNAMES': 'Hans Hermann',
        'LASTNAME': 'Höllermaß',
        'S.V.01': 'Arbeit-Wirtschaft-Technik',
        'G.V.01': 'kann nicht beurteilt werden',
        'S.V.02': 'Medienkunde',
        'G.V.02': 'befriedigend',
        'COMMENT': 'Eine Bemerkung, die sich über mehrere Absätze erstreckt.' \
                '\nInhaltlich ist hier allerdings nicht viel zu holen, was' \
                ' vielleicht zu bedauern ist, aber letztendlich nicht' \
                ' ungewöhnlich.' \
                '\nMehr gibt es nicht.',
        'NOCOMMENT': ''
    }
    _out = os.path.join(_odir, 'test-out1.odt')
    odtBytes, used, notsub = OdtFields.fillUserFields(_odtfile, _itemdict,
            FIELD_INFO = '')
    with open(_out, 'bw') as fout:
        fout.write(odtBytes)
    print("\nSUBSTITUTE from %s to %s" % (_odtfile, _out))
    print("  ... used:", sorted(used))
    print("\n  ... not supplied:", sorted(notsub))
    _out = os.path.join(_odir, 'test-out2.odt')
    odtBytes, used, notsub = OdtFields.fillUserFields(_odtfile, _itemdict,
            FIELD_INFO = "A New Comment:\n'Line 2'\n\"Line 3\"\n<&>§€ß")
    with open(_out, 'bw') as fout:
        fout.write(odtBytes)
    print("\n Changed \"comment\" metadata -> %s" % _out)

#    quit(0)

    _dirpath = os.path.join(RESOURCES, 'templates', 'Noten')
    _itemdict = {}  # Just test that fields are ok
    for f in os.listdir(_dirpath):
        print("\nINPUT:", f)
        _odtfile = os.path.join(_dirpath, f)
        _outfile = os.path.join(_odir, 'test-' + f)
        odtBytes, used, notsub = OdtFields.fillUserFields(_odtfile, _itemdict)
        with open(_outfile, 'bw') as fout:
            fout.write(odtBytes)
        print("\nSUBSTITUTE to %s" % _outfile)
        print("  ... used:", sorted(used))
        print("\n  ... not supplied:", sorted(notsub))
