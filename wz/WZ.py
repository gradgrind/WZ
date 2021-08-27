# -*- coding: utf-8 -*-
"""
WZ.py

Last updated:  2021-05-25

Main user-interface – start application.


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

import sys, os, builtins

builtins.NONE = ''
this = sys.path[0]
APPDIR = os.path.dirname(this)
#??args = set(sys.path[1:])
args = set(sys.argv[1:])
try:
    args.remove('--debug')
except KeyError:
    def __debug(*msg):
        pass
else:
    def __debug(*msg):
        print("DEBUG:::", *msg)
builtins.DEBUG = __debug
DEBUG("sys.argv:", sys.argv)


#############################################################test

from time import sleep
from threading import Timer
from threading import Thread, Event
from queue import SimpleQueue   # Python >= 3.7
import json


from ui import wz_main
if __name__ == '__main__':
    wz_main.main(args, APPDIR)#, modlist)

quit(0)

#############################################################

### -----

def test():
    t = Timer(1.0, hello)
    t.start()
    print(" ...")
    sleep(3)
    print("Moin!")

def hello():
    print("Grüß Gott!")

def rprt():
    print("Morzhe ...")


"""
class Backend:
    def __init__(self):
        self.event = Event()
        self.thread = Thread()
#
    def call(self, module, function, *args, **kargs):
#TODO: handle module map, etc.


        f(*args, **kargs)
"""


if __name__ == '__main__':

    quit(0)

    builtins.WINDOW = ui_load('wz.ui')
#    WINDOW.intro_text.setMarkdown("# CHANGED\n\nI got access to the widget!")
#    print(getattr(WINDOW, 'intro_text').toPlainText())

    WINDOW.pb_calendar.clicked.connect(test)
    WINDOW.pb_pupil.clicked.connect(rprt)



    WINDOW.show()
    sys.exit(app.exec())
###

#TODO?
from __modules__ import modules
modlist = []
for m, desc in modules:
    modlist.append(m)
    DEBUG("INCLUDING %s: %s" % (m, desc))
