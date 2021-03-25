### python >= 3.7
# -*- coding: utf-8 -*-
"""
tables/datapack.py - last updated 2021-03-22

Load and save structured data in a compact way (gzipped json)

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

### Messages:
_KEY_MISMATCH = "Feld {key} hat Wert {val} statt {exp} in:\n  {path}"

import os, json, gzip

class PackError(Exception):
    pass

###

def get_pack(filepath, **checks):
    """Get a gzipped json file from the given path (specified without
    the '.json.gz' ending).
    Raises <FileNotFoundError> if the file doesn't exist.
    Raises <PackError> if one of the control fields doesn't match the
    provided values.
    Returns the mapping.
    """
    fpath = filepath + '.json.gz'
    with gzip.open(fpath, 'rt', encoding='utf-8') as zipfile:
        data = json.load(zipfile)
    for key, val in checks.items():
        if data[key] != val:
            raise PackError(_KEY_MISMATCH.format(key = key,
                    val = data[key], exp = val, path = fpath))
    return data

###

def save_pack(filepath, **data):
    """Save the data mapping as a gzipped json file to the given path
    (specified without the '.json.gz' ending).
    Return the filename.
    Any existing file will be overwritten.
    """
    fpath = filepath + '.json.gz'
    os.makedirs(os.path.dirname(fpath), exist_ok = True)
    with gzip.open(fpath, 'wt', encoding = 'utf-8') as zipfile:
        json.dump(data, zipfile, ensure_ascii = False)
    return fpath
