# -*- coding: utf-8 -*-

"""
local/text_config.py

Last updated:  2021-01-11

Configuration items for text (Waldorf) reports.

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

COVER_NAME = '{klass}'      # report cover sheet: file name
COVER_DIR = 'MANTEL'        # report cover sheet: folder

def cover_template(klass):
    tp = 'Text/Mantel'
    if klass >= '12':
        tp += '-Abgang'
#    if klass[-1] == 'K':       # currently using the "normal" template
#        tp += '-Kleinklasse'
    return tp
