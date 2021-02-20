# -*- coding: utf-8 -*-

"""
core/main.py - last updated 2021-02-20

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
_CHANGED_YEAR = "Aktuelles Schuljahr ist {year}"
_FAILED = "{fname} FEHLGESCHLAGEN"

import sys, os, builtins, traceback, json
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

class _Main:
    """Commands from the front-end are passed as json strings (mappings).
    The function to be called is identified by the '__NAME__' entry.
    All other entries are parameters. Those not starting with '_' are
    passed to the function as named parameters.

    Information and callbacks may also be passed back to the front-end.
    These are also json strings (mappings) with the following keys:

        '__CALLBACK__' supplies the name of the callback function to be
        invoked. This is available to back-end functions via the
        <CALLBACK> "builtin".

        All keys not starting with '_' are named parameters to the
        callback function.

        Other keys are presently not used.

    There are two special callbacks:

        1) '*DONE*' is a "completion message", which is involed when the
        back-end function is finished, freeing the interface for a
        new action. It has one parameter: 'cc', which can have the value
        'OK' (indicating successful completion) or else an automatically
        generated localized version of '<call name> FAILED').
        Back-end functions signal successful completion by returning a
        true value.

        2) '*REPORT*' sends messages back to the user. It supports various
        categories of report: 'INFO', 'WARN', 'ERROR' and 'TRAP'
        (the latter indicating that something went wrong enexpectedly).
        There is a shortcut "builtin" for these calls: <REPORT>, taking
        message-type and message as arguments.

        In addition there is the message category 'OUT', which is rather
        like 'INFO' in that it adds text to the front-end's reporting
        mechanism. However, these messages will only be displayed if
        some other report (one of the main categories) causes a message
        to appear, or during a long-running process. The idea behind
        this message is primarily to allow feedback during long-running
        or faulty processes, when it might otherwise be unclear to the
        user what is happening – or, indeed, whether anything is
        happening. It is directly accessible via the 'OUTPUT' "builtin",
        which takes a single argument, the message.

    Communication is via stdio, using utf-8 encoding.
    """
    def __init__(self, dbg_handle):
        self._dbg_handle = dbg_handle
        self.debug("))) Starting ...")
#
    def debug(self, msg):
        self._dbg_handle.write(msg + '\n')
        self._dbg_handle.flush()
#
    def send_done(self, ok):
        self.send_callback('*DONE*', cc = 'OK' if ok
                else _FAILED.format(fname = self.function_name))
#
    def send_report(self, mtype, msg):
        self.send_callback('*REPORT*', mtype = mtype, msg = msg)
#
    def send_callback(self, cmd, **parms):
        """Send a message back to the manager/master/...
        It should end with a newline, to ensure that it is recognizable
        as a complete line.
        """
        parms['__CALLBACK__'] = cmd
        msg = json.dumps(parms, ensure_ascii = False)
#TODO: ...
#        self.debug('+++ OUT:\n' + json.dumps(parms,
#                ensure_ascii = False, indent = 2))
        self.debug('+++ OUT: ' + msg)
        print(msg, flush = True)
#
    def send_output(self, text):
        self.send_report('OUT', text)
#
    def run(self):
        self.debug("))) Receiving ...")
        for line in sys.stdin:
            self.debug('IN: ' + line)
            ### decode
            try:
                cmd = json.loads(line)
                self.function_name = cmd.pop('__NAME__')
                function = FUNCTIONS[self.function_name]
                # deal with the parameters
                params = {k: v for k, v in cmd.items() if k[0] != '_'}
            except:
                REPORT('TRAP', 'Invalid WZ-command:\n  %s' % line.rstrip())
                self.send_done(False)
                continue
            ### execute
            try:
                self.send_done(function(**params))
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
        builtins.DEBUG = main.debug
        builtins.REPORT = main.send_report
        builtins.OUTPUT = main.send_output
        builtins.CALLBACK = main.send_callback
        main.run()

# Collect available functions/commands
builtins.FUNCTIONS = {}

####### ------------------------------------------------------ #######

from core.base import Dates
from local.base_config import print_schoolyear


def get_years(year = None):
    """Return (via callback) a list of available school-years and the
    currently selected one.
    If <year> is given, try to use this as the current year.
    Otherwise, if no valid year is currently set, use the
    current school-year, if there is data for it, otherwise the latest
    year for which there is data.
    The list also contains full display-names for the years (e.g.
    '2016 – 2017'):
        [[year, full-name], ...]
    """
#TODO: !!! This is really messed up ...
    allyears = Dates.get_years()
    if year and year in allyears:
        set_year(year)
    else:
        try:
            if SCHOOLYEAR not in allyears:
                raise ValueError
        except:
            thisyear = Dates.get_schoolyear()
            if thisyear not in allyears:
                thisyear = allyears[0]
            set_year(thisyear)
    CALLBACK('base_SET_YEARS', years = [(y, print_schoolyear(y))
            for y in allyears], current = SCHOOLYEAR)
    return True

FUNCTIONS['BASE_get_years'] = get_years

###

def get_school_data():
    CALLBACK('base_SET_SCHOOL_DATA', data = SCHOOL_DATA)
    return True

FUNCTIONS['BASE_get_school_data'] = get_school_data

###

def set_year(year):
    builtins.SCHOOLYEAR = year
    REPORT('INFO', _CHANGED_YEAR.format(year = year))
    CALLBACK('base_YEAR_CHANGED')
    return True

FUNCTIONS['BASE_set_year'] = set_year


######################################################################

import core.interface_pupils
import core.interface_subjects
import core.interface_calendar


#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    start()
