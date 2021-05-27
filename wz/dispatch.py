# -*- coding: utf-8 -*-

"""
dispatch.py - last updated 2021-05-24

Dispatcher for call to back-end functions from front-end.

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

# This bit isolates front from back-end
from importlib import import_module

IMPORTS = {}

def BACKEND(module, target, *args, **kargs):
    """Only pass arguments that can be JSONified.
    """
    try:
        m = IMPORTS[module]
    except KeyError:
        m = import_module(module)
        IMPORTS[module] = m
    return getattr(m, target)(*args, **kargs)
# The next step would be callbacks, or coroutines?

from PySide6.QtConcurrent import QtConcurrent
QtConcurrent.run()



quit(0)
##########################

### Messages
_CHANGED_YEAR = "Aktuelles Schuljahr ist {year}"
_FAILED = "{fname} FEHLGESCHLAGEN"

import sys, os, builtins, traceback, json
#sys.stdin.reconfigure(encoding='utf-8') # requires Python 3.7+

### -----

#from importlib import import_module

#import_module('ui_modules.' + m)


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
        (the latter indicating that something went wrong unexpectedly).
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
        happening at all. It is directly accessible via the 'OUTPUT'
        "builtin", which takes a single argument, the message.

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

def startup():
    logdir = WZPATH('logs')
    if not os.path.isdir(logdir):
        os.makedirs(logdir)
    with open(os.path.join(logdir, 'debug'), 'w',
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

### -----

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

###

from local.grade_config import STREAMS
from core.pupils import PUPILS

def get_classes():
    pupils = PUPILS(SCHOOLYEAR)
    selects = {
            'SEX': pupils.SEX,
#TODO?
            'STREAMS': streams
        }
    classes = pupils.classes()
    CALLBACK('template_SET_CLASSES', selects = selects, classes = classes)
    return True

FUNCTIONS['TEMPLATE_get_classes'] = get_classes

######################################################################

#TODO: use module list
import backend

#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

if __name__ == '__main__':
    from core.base import start

#TODO: Actually, before setting up the datadir, the modules would need loading ...
# Could there be a default module loading from the __modules__ module?
# An option could be to pass it as a command line list?
#sys.argv: app, [datadir,] -- module module module ...
# If datadir is not provided, uses TESTDATA (unpacking testdata.tar.gz
# if TESTDATA does not exist?)

    start.setup(datadir)

    startup()
