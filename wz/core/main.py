# -*- coding: utf-8 -*-

"""
core/main.py - last updated 2021-02-01

Text-stream based controller/dispatcher for all functions.

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
_SUBJECTS_CLASS = " ... Tabelle für Klasse {klass} aktualisiert"
_CHANGED_YEAR = "Aktuelles Schuljahr ist {year}"

import sys, os, builtins, traceback
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)
    from core.base import init
    try:
        datadir = sys.argv[1]
    except:
        datadir = None
    init(datadir)

sys.stdin.reconfigure(encoding='utf-8') # requires Python 3.7+

PARAGRAPH = '¶'
SPACE = '¬'
class _Main:
    """Commands have the form:
            COMMAND parameter1:value1 parameter2:value ...
        In values:
            Spaces (' ') are represented by '¬', so '¬' should not be used
            in values.
            Newlines are represented by '¶', so the character '¶' should
            not be used in values.
    Feedback to the caller is via messages. These are transmitted by the
    <_send> method. There are several types of message:
        '+++': Function completed successfully.
        '---': Function completed with errors.
        '>>>type message': A report. 'type' can be 'INFO', 'WARN', 'ERROR'
                or 'TRAP'. 'message' uses the same encoding as command
                parameter values (see above).
        '...text': Output from some subprogram (e.g. LibreOffice).
        ':::CALLBACK parameter1:value1 parameter2:value ...': A callback
                to the front-end, similar to the COMMAND to this handler.
    The messages '+++' and '---' are always the last messages sent in
    response to a COMMAND. No further COMMANDs can be received until one
    of these messages has been sent.
    To ease their use, there are helper methods (<send_...>) for each
    type. <REPORT>, <OUTPUT> and <CALLBACK> are made available as
    "builtins", so that they are easily accessible anywhere.

    All communication is via 'utf-8' streams.
    """
    def __init__(self, dbg_handle):
        self._dbg_handle = dbg_handle
        self.debug("))) Starting ...")
#
    def debug(self, msg):
        self._dbg_handle.write(msg + '\n')
        self._dbg_handle.flush()
#
    def encode(self, text):
        return PARAGRAPH.join(text.rstrip().replace(' ', SPACE).splitlines())
#
    def _send(self, message):
        """Send a line back to the manager/master/...
        It must end with a newline, so that it is recognizable as a
        complete line.
        """
        self.debug('OUT: ' + message + '\n')
        print(message, flush = True)
#
    def send_done(self, ok):
        self._send('+++' if ok else '---')
#
    def send_report(self, mtype, msg):
        self._send('>>>%s %s' % (mtype, self.encode(msg)))
#
    def send_callback(self, cmd, **parms):
        plist = ['%s:%s' % (key, self.encode(val))
                for key, val in parms.items()]
        self._send(':::%s %s' % (cmd, ' '.join(plist)))

    def send_output(self, text):
        self._send('...' + self.encode(text))
#
    def run(self):
        self.debug("))) Receiving ...")
        for line in sys.stdin:
            self.debug('IN: ' + line)
            ### decode
            plist = line.split()
            try:
                function_name = plist.pop(0)
                function = FUNCTIONS[function_name]
                # deal with the parameters
                params = {}
                for p in plist:
                    key, val = p.split(':', 1)
                    params[key] = val.replace(SPACE, ' ').replace(
                            PARAGRAPH, '\n')
            except:
                REPORT('TRAP', 'Invalid WZ-command:\n  %s' % line.rstrip())
                self.send_done(False)
                continue
            ### execute
            try:
                if function(**params):
                    self.send_done(True)
                    continue
            except:
                log_msg = traceback.format_exc()
                self.debug(log_msg)
                REPORT('TRAP', log_msg)
            self.send_done(False)

###

def start():
    with open(os.path.join(ZEUGSDIR, 'logs', 'debug'), 'w',
            encoding = 'utf-8') as dbg_fh:
        main = _Main(dbg_fh)
        builtins.REPORT = main.send_report
        builtins.OUTPUT = main.send_output
        builtins.CALLBACK = main.send_callback
        main.run()

# Collect available functions/commands
builtins.FUNCTIONS = {}

####### ------------------------------------------------------ #######

from core.base import Dates
from local.base_config import print_schoolyear

def get_years():
    """Return a list of available school-years and the currently selected
    one. If no valid year is currently set, use the current school-year,
    if there is data for it, otherwise the latest year for which there
    is data.
    The list also contains full display-names for the years (e.g.
    '2016 – 2017') and is formatted thus:
        year:full-name|year:full-name| ...
    """
    allyears = Dates.get_years()
    years = ['%s:%s' % (y, print_schoolyear(y)) for y in allyears]
    try:
        if SCHOOLYEAR not in allyears:
            raise ValueError
    except:
        thisyear = Dates.get_schoolyear()
        if thisyear not in allyears:
            thisyear = allyears[0]
        set_year(thisyear)
    CALLBACK('base_SET_YEARS', years = '|'.join(years), current = SCHOOLYEAR)
    return True

FUNCTIONS['BASE_get_years'] = get_years

###

def set_year(year):
    builtins.SCHOOLYEAR = year
    REPORT('INFO', _CHANGED_YEAR.format(year = year))
    return True

FUNCTIONS['BASE_set_year'] = set_year

######################################################################

from core.courses import Subjects

def update_subjects(filepath):
        subjects = Subjects(SCHOOLYEAR)
        srctable = subjects.read_source_table(filepath)
        opath = subjects.save_table(srctable)
        REPORT('INFO', _SUBJECTS_CLASS.format(klass = srctable.klass))
        return True

FUNCTIONS['SUBJECT_table_update'] = update_subjects

###

_BAD_PUPIL_TABLE = "Schülerdaten fehlerhaft:\n  {path}"

from core.pupils import Pupils
import json

class Pupils_Update:
    _instance = None
    @classmethod
    def start(cls, filepath):
        self = cls()
        cls._instance = self
        self.compare_file(filepath)
        return bool(cls._instance)
    @classmethod
    def done(cls):
        cls._instance = None
#
    def __init__(self):
        self.pupils = Pupils(SCHOOLYEAR)
#
    def compare_file(self, filepath):
        try:
            self.ptables = self.pupils.read_source_table(filepath)
        except:
            REPORT('ERROR', _BAD_PUPIL_TABLE.format(path = filepath))
            self.done()
            return
        self.delta = self.pupils.compare_new_data(self.ptables)
#TODO: return it as json? Is that too much for one line?
# Return it line-for-line? class-for-class?
        for klass, kdata in self.delta.items():
            klist = json.dumps(kdata)
            CALLBACK('pupil_DELTA', klass = klass, delta = klist)
        CALLBACK('pupil_DELTA_COMPLETE')
#
    @classmethod
    def update(cls, klass, delta_list):
        REPORT('OUT', '& %s: %s' % (klass, delta_list))
        return True





FUNCTIONS['PUPIL_table_delta'] = Pupils_Update.start
FUNCTIONS['PUPIL_table_update'] = Pupils_Update.update


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    start()
