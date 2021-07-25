#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TT/tt0.py

Last updated:  2021-07-04

Timetable ... initial "chip" placement ...


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

#TODO: subject management missing ...
def place_chips_0(klass):
    chips = CHIPS(klass)
#TODO: pre-sort, removing already placed chips?
    for period in PERIODS:
        for day in DAYS:
            if not fillable(klass, day, period):
                # The cell is already filled or blocked
                continue
#TODO: return if no chips left! – or simply add slots to free list!
            for chip in chips:
# It might be best here to leave the chips in their array and just mark
# them as placed. This would possibly simplify the use of "multi-chips".
# However the set of already-placed chips would gradually grow, so the
# list of initial fruitless tests would grow. What about using a sort of
# cyclic buffer, with the initial index keeping pace with the placements?
                if place(klass, day, period, chip, test_only = False):
                    if not fillable(klass, day, period):
                        # The cell is already filled or blocked
                        break

# I could build a list of slots which still have space in the above loop.

# At the end of this, there would be a – possibly empty – set of unplaced
# chips. The tricky question is: how to place these?
# It can only be by replacing others, which must then be placed in turn.
# The first attempt might be to look for a slot where the displaced
# chip(s) can be moved without further displacements. But this could be
# rather inefficient. What about an initial search identifying chips
# which can be moved in this way? That might allow more than one
# replacement.



def fillable(klass, day, period):
#TODO: test for blocked?
    return get_groups(klass, day, period) == get_all_groups(klass)
