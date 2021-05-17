### python >= 3.7
# -*- coding: utf-8 -*-
"""
tables/datapack.py - last updated 2021-05-17

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

import os, json, gzip

### +++++

def get_pack(filepath):
    """Get a gzipped json file from the given path (specified without
    the '.json.gz' ending).
    Raises <FileNotFoundError> if the file doesn't exist.
    Returns the mapping.
    """
    fpath = filepath + '.json.gz'
    with gzip.open(fpath, 'rt', encoding='utf-8') as zipfile:
        data = json.load(zipfile)
    return data

###

def save_pack(filepath, data, backup = None):
    """Save the data mapping as a gzipped json file to the given path
    (specified without the '.json.gz' ending).
    Return the filename.
    Any existing file will be overwritten, but if <backup> is supplied
    the old file will be moved to:
        '~' + file-name + '~' + backup + '.json.gz'
    ...  if that file doesn't already exist.
    """
    fpath = filepath + '.json.gz'
    d = os.path.dirname(filepath)
    os.makedirs(d, exist_ok = True)
    if backup and os.path.isfile(fpath):
        f = os.path.basename(filepath)
        bpath = os.path.join(d, '~' + f + '~' + backup + '.json.gz')
        if not os.path.isfile(bpath):
            os.rename(fpath, bpath)
    with gzip.open(fpath, 'wt', encoding = 'utf-8') as zipfile:
        json.dump(data, zipfile, ensure_ascii = False)
    return fpath


