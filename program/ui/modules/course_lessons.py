"""
ui/modules/course_lessons.py

Last updated:  2022-04-17

Edit course and lesson data.


=+LICENCE=============================
Copyright 2022 Michael Towers

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

#TODO ...
_NAME = "Kurse/Stunden"
_TITLE ="Unterrichtskurse und -stunden verwalten"


### Messages

#####################################################

if __name__ == "__main__":
    import locale, sys, os, builtins
    print("LOCALE:", locale.setlocale(locale.LC_ALL, ''))
    this = sys.path[0]
    appdir = os.path.dirname(os.path.dirname(this))
    sys.path[0] = appdir
    try:
        builtins.PROGRAM_DATA = os.environ["PROGRAM_DATA"]
    except KeyError:
        basedir = os.path.dirname(appdir)
        builtins.PROGRAM_DATA = os.path.join(basedir, "wz-data")
    from ui.ui_base import StandalonePage as Page
    from core.base import start
#    start.setup(os.path.join(basedir, 'TESTDATA'))
#    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, 'DATA-2023'))
else:
    from ui.ui_base import StackPage as Page

from ui.ui_base import QHBoxLayout
from ui.course_editor_widget import CourseEditor

### -----

def init():
    MAIN_WIDGET.add_tab(Courses())


class Courses(Page):
    name = _NAME
    title = _TITLE

    def __init__(self):
        super().__init__()
        course_editor = CourseEditor()
        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(course_editor)


if __name__ == "__main__":
    from ui.ui_base import run
    widget = Courses()
    widget.resize(1000, 550)
    run(widget)
