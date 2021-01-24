# -*- coding: utf-8 -*-

"""
core/main.py - last updated 2021-01-24

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

import sys, os, builtins, traceback
if __name__ == '__main__':
    # Enable package import if running as module
    this = sys.path[0]
    sys.path[0] = os.path.dirname(this)

### Messages

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
    """
    def __init__(self):
        pass
#
    def run(self):
        for line in sys.stdin:
            ### decode
            plist = line.split()
            try:
                function_name = plist.pop(0)
#TODO: check command validity
                function = _echo

                # deal with the parameters
                params = {}
                for p in plist:
                    key, val = p.split(':', 1)
                    params[key] = val.replace(SPACE, ' ').replace(
                            PARAGRAPH, '\n')
            except:
                self.report('TRAP', 'Invalid WZ-command:\n  %s' %
                        line.rstrip())
                print('---', flush = True)
                continue
            ### execute
            try:
                if function(**params):
                    print('+++')
                    continue
            except:
                log_msg = '{val}\n\n:::{emsg}'.format(val = exc_value,
                        emsg = ''.join(traceback.format_exception(
                                exc_type, exc_value, exc_traceback)))
                self.report('TRAP', log_msg)
            print('---', flush = True)
#
    def report(self, mtype, msg):
        msg_enc = PARAGRAPH.join(msg.rstrip().replace(
                ' ', SPACE).splitlines())
        print('>>>%s:%s' % (mtype, msg_enc), flush = True)
#
def start():
    main = _Main()
    builtins.REPORT = main.report
    main.run()

#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#--#

def _echo(**params):
    #CMD a:1 B:A¬sentence.¶A¬second¬line.
    REPORT('INFO', repr(params).replace(r'\n', '\n'))
    return True

if __name__ == '__main__':
    start()
