### python >= 3.7
# -*- coding: utf-8 -*-

"""
tables/simple_ods_reader.py

Last updated:  2021-11-20

OdsReader:
Read the data from the sheets of an ods-file ignoring all formatting and
style information.
An ods-file is a zipped archive, the content is found in the file
member file "content.xml".

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

import sys, os
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir

import zipfile as zf
from types import SimpleNamespace
from xml.parsers.expat import ParserCreate

ODS_CONTENT_FILE = 'content.xml'
ODS_META_FILE = 'meta.xml'

_debug = False # set to <True> to have expat parser events printed to stdout.

class OdsReader(dict):
    def __init__ (self, filepath, ignore_covered_cells=False):
        """Read an ".ods" (LibreOffice) spreadsheet as a list of rows,
        each row is a list of cell values.
        All sheets in the file are read, a <dict> of sheets
        (name -> row list) is built.
        If <ignore_covered_cells> is true, all covered (under a merge) cells
        are read as empty, otherwise their (hidden) value will be returned.

        This is a read-only utility. Formulae, style, etc. are not retained.
        For formulae the last-calculated value is returned.
        All values are returned as strings.
        Numbers which can be represented as integers (xxxx.0) are returned
        as integers (in string form).
        """
        super().__init__()
        # Read the file to a list form (see <OdsReader>)
        sheets = readOdsFile(filepath, ignore_covered_cells)
        # Extract the needed data in the form specified above
        self._mergedRanges = {}
        for sheetname, rows, mergelist in sheets:
            rowlist = []
            for row in rows:
                cells = []
                for cell in row:
                    if cell == None:
                        cells.append('')
                    else:
                        ctype, cval, ctext, cformula = cell
                        if ctype == None:
                            v = ''
                        elif ctype == 'string':
                            v = ctext.strip()
                        elif ctype == 'float':
                            # Fix for integers returned as floats
                            i = int(cval)
                            v = str(i if i == cval else cval)
                        else:
                            v = str(cval)
                        cells.append(v)
                rowlist.append(cells)
            self[sheetname] = rowlist
            self._mergedRanges[sheetname] = mergelist


    def mergedRanges (self, sheetname):
        """Returns a list like ['AK2:AM2', 'H33:AD33', 'I34:J34', 'L34:AI34'].
        """
        mrlist = []
        for mr in self._mergedRanges[sheetname]:
            # (rcount, ccount, rs or 1, cs or 1) -> "A2:B4" (for example)
            c1 = get_column_letter (mr[1] + 1)
            r1 = mr[0] + 1
            c2 = get_column_letter (mr[1] + mr[3])
            r2 = mr[0] + mr[2]
            mrlist.append("%s%d:%s%d" % (c1, r1, c2, r2))
        return mrlist



def readOdsFile(filepath, ignore_covered_cells):
    """Uses the expat parser to get at the tables and their data.
    All formatting information is ignored.
    If <ignore_covered_cells> is true, all covered (under a merge) cells
    are read as empty, otherwise their (hidden) value will be returned.
    An xml string is parsed to a table of cell values.
    Note that the expat parser converts all items to unicode.
    """
    INFO = SimpleNamespace()    # variables available to all sub-functions
    INFO.sheets = None
    INFO.rows = None
    INFO.rowcount = None
    INFO.rowrepeat = None
    INFO.cells = None
    INFO.ncols = None
    INFO.cellcount = None
    INFO.celltype = None
    INFO.repeat = None
    INFO.value = None
    INFO.paras = None
    INFO.text = None
    INFO.mergeList = None
    INFO.merge = None

    def show(*args):
        """To aid debugging: print event info if <_debug> is true.
        """
        if _debug:
            print(*args, flush=True)

    ############ expat event-handler functions ############

    def start_element(name, attrs):
        show('>>> Start element:', name, attrs)
        if name == 'table:table-cell' or name == 'table:covered-table-cell':
            assert INFO.celltype == None
            INFO.repeat = int(attrs.get("table:number-columns-repeated", 1))
            INFO.paras = []
            INFO.formula = attrs.get('table:formula')
            INFO.celltype = attrs.get('office:value-type')
            if INFO.celltype == None:
                # Empty cells are handled specially because there can be a
                # very large number of these at the end of a row
                INFO.celltype = '__EMPTY__'
                INFO.value = None
            elif INFO.celltype in ('float', 'percentage', 'currency'):
                value = attrs.get('office:value')
                if value == None:
                    INFO.value = None
                else:
                    INFO.value = float(value)
            elif INFO.celltype == 'string':
                INFO.value = attrs.get('office:string-value')
            elif INFO.celltype == 'boolean':
                value = attrs.get('office:boolean-value')
                if value == 'true':
                    INFO.value = True
                else:
                    assert value == 'false'
                    INFO.value = False
            elif INFO.celltype == 'date':
                INFO.value = attrs.get('office:date-value')
            elif INFO.celltype == 'time':
                INFO.value = attrs.get('office:time-value')
            else:
                print("ERROR: unknown cell type:", INFO.celltype, flush=True)
                assert False
            # Note merge information
            INFO.merge = (attrs.get('table:number-rows-spanned'),
                    attrs.get('table:number-columns-spanned'))

        elif name == 'text:p':
            assert INFO.text == None
            INFO.text = ""

        elif name == 'table:table-row':
            assert INFO.cells == None
            INFO.cellcount = 0
            INFO.cells = []
            INFO.rowrepeat = int(attrs.get("table:number-rows-repeated", 1))

        elif name == 'table:table':
            assert INFO.rows == None
            INFO.sheetname = attrs['table:name']
            show('\n    --- sheet name: %s\n' % INFO.sheetname)
            INFO.rows = []
            INFO.rowcount = 0
            INFO.mergeList = []
            INFO.ncols = 0

        elif name == 'office:spreadsheet':
            assert INFO.sheets == None
            INFO.sheets = []


    def end_element(name):
        show('>>> End element:', name)
        if name == 'table:table-cell' or name == 'table:covered-table-cell':
            # Retrieve merge information
            rs, cs = INFO.merge
            # Check whether this is the main cell of a merged range
            if rs or cs:
                INFO.mergeList.append((INFO.rowcount, INFO.cellcount,
                        int (rs or 1), int (cs or 1)))

            if INFO.celltype == '__EMPTY__' and INFO.formula != None:
                # Don't count formula cells as empty, even if there is no value,
                # but mark them as empty untyped.
                INFO.celltype = None

            if name == 'table:covered-table-cell' and ignore_covered_cells:
                INFO.celltype = '__EMPTY__'

            if INFO.celltype != '__EMPTY__':
                # Add skipped empty cells
                while len(INFO.cells) < INFO.cellcount:
                    # Add an empty cell
                    INFO.cells.append(None)

                val = (INFO.celltype, INFO.value, "\n".join(INFO.paras),
                        INFO.formula)
                for i in range(INFO.repeat):
                    INFO.cells.append(val)

            #else:
                # Don't add any cells yet. Wait to see if there are any
                # non-empty calls afterwards.

            INFO.cellcount += INFO.repeat
            INFO.celltype = None
            INFO.repeat = None
            INFO.paras = None

        elif name == 'text:p':
            assert INFO.text != None
            if INFO.paras != None:
                INFO.paras.append(INFO.text)
            INFO.text = None

        elif name == 'table:table-row':
            if INFO.cells:
                # The row is not empty: add skipped empty rows
                while len (INFO.rows) < INFO.rowcount:
                    # Add an empty row
                    INFO.rows.append([])

                for i in range(INFO.rowrepeat):
                    INFO.rows.append(INFO.cells)

                nc = len(INFO.cells)
                if nc > INFO.ncols:
                    INFO.ncols = nc

            # else:
            #     Don't add any rows yet. Wait to see if there are any
            #     non-empty rows afterwards.

            INFO.rowcount += INFO.rowrepeat
            INFO.cells = None

        elif name == 'table:table':
            # Equalise the row lengths
            for row in INFO.rows:
                while len(row) < INFO.ncols:
                    row.append(None)

            INFO.sheets.append((INFO.sheetname, INFO.rows, INFO.mergeList))
            INFO.sheetname = None
            INFO.rows = None
            INFO.rowcount = None
            INFO.mergeList = None


    def char_data(data):
        show('>>> Character data:', type(data), repr(data))
        if INFO.sheets != None:
            # Only while parsing the data of a sheet is <INFO._text> not <None>
            # but this method can also be called at other places, where
            # the data is of no interest.
            INFO.text += data

    ############ end handler functions ############

    # Get the content xml file (utf-8).
    with zf.ZipFile(filepath) as zipfile:
        xmlbytes = zipfile.read(ODS_CONTENT_FILE)
    parser = ParserCreate()
    parser.StartElementHandler = start_element
    parser.EndElementHandler = end_element
    parser.CharacterDataHandler = char_data
    parser.Parse(xmlbytes)
    return INFO.sheets


import io
import xmltodict
def substituteZipContent(infile, process = None, metaprocess = None):
    """Process the contents of an ods file using the function <process>.
    Return the resulting odt file as a <bytes> array.
    Normally the contents will be read.
    However, by setting <metaprocess> to a function, the metadata can
    be read.
    When information is to be read from the odt-file, rather than
    performing a transformation, only one processing function should be
    supplied and it should return an empty value: this will terminate
    the whole function early, returning <None>. The information to be
    read out must be extracted within the processing function and saved
    separately.
    """
    sio = io.BytesIO()
    with zf.ZipFile(sio, "w", compression=zf.ZIP_DEFLATED) as zio:
        with zf.ZipFile(infile, "r") as za:
            for fin in za.namelist():
                indata = za.read(fin)
                if fin == ODS_CONTENT_FILE and process:
                    indata = process(indata)
                    if not indata:
                        return None
                elif fin == ODS_META_FILE and metaprocess:
                    indata = metaprocess(indata)
                    if not indata:
                        return None
                zio.writestr(fin, indata)
    return sio.getvalue()


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    from core.base import start
    basedir = os.path.dirname(appdir)
    start.setup(os.path.join(basedir, 'TESTDATA'))
    import io

    def _process(xmldata):
        d = xmltodict.parse(xmldata, dict_constructor=dict)
        row0 = d["office:document-content"][
            "office:body"][
                "office:spreadsheet"][
                    "table:table"][
                        "table:table-row"][
                            "table:table-cell"]
        print("ROW0:", row0)
        row0[1]["text:p"] = "1"
        return xmltodict.unparse(d).encode('utf-8')

    filepath = DATAPATH('testing/Test0B.ods')
    odsbytes = substituteZipContent(filepath, _process)
    with open(DATAPATH('testing/tmp/Test0Bx.ods'), 'wb') as fh:
        fh.write(odsbytes)

    print("\n ––––––––––––––––––––––––––––––––––––\n")
    fname = os.path.basename(filepath)
    import xmltodict, json
    with zf.ZipFile(filepath) as zipfile:
        xmlbytes = zipfile.read(ODS_CONTENT_FILE)
    d = xmltodict.parse(xmlbytes, dict_constructor=dict)
#    d = xmltodict.parse(xmlbytes)
#    print(json.dumps(d, indent=4))
    print(d)

    print("\n ––––––––––––––––––––––––––––––––––––\n")
    filepath = DATAPATH('testing/Test1.ods')
    fname = os.path.basename(filepath)
    ss = OdsReader(filepath)
    for sheet, table in ss.items():
        print("\n SHEET:", sheet)
        for row in table:
            print("-->", row)
    print("\n\nAnd now using a file-like object ...\n")
    with open(filepath, 'rb') as fbi:
        bytefile = fbi.read()
    flo = io.BytesIO(bytefile)
    flo.filename = fname
    ss = OdsReader(flo)
    for sheet, table in ss.items():
        print("\n SHEET:", sheet)
        for row in table:
            print("-->", row)
