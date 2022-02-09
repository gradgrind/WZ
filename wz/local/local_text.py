"""
local/local_text.py

Last updated:  2022-02-05

Configuration (location-specific information) for text-report handling.

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

### Messages

### +++++

import sys, os

if __name__ == "__main__":
    import locale

    print("LOCALE:", locale.setlocale(locale.LC_ALL, ""))
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    start.setup(os.path.join(basedir, "TESTDATA"))
#    start.setup(os.path.join(basedir, 'DATA'))

### -----


def text_report_class(klass: str) -> bool:
    """Return <True> if <klass> is a valid class for text reports.
    """
    # All classes except 13 receive text reports. The test must also
    # exclude classes starting with "XX" (used for timetabling).
    return klass < "13"


if __name__ == "__main__":
    pass
