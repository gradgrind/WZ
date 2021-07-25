#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TT/tt1.py

Last updated:  2021-06-19

Timetable ... data handling / actions ...


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

#TODO ...

def test_chip_slot(chip, slot):
    """Test whether the given chip can be placed in the given slot.
    There can be various results:
     - No problem
     - Group clash
     - Teacher clash
     - Room clash
     - Subject already placed somewhere on the day for at least one of
      the groups in the chip
    """
    pass

# The chip needs to have a list of classes, each of these providing a
# bitmap for the groups – or else one large bitmap with all class/group
# items. The awkward thing with the latter is trying to get the groups
# from it. Its total length might only be 100 bits or so, though with
# highly divided classes it could be much more.
# The former is a more elaborate structure, but perhaps more easily
# resolved to classes and groups.
    for class_groups in chips[chip].class_groups:
        if class_groups.groups & slots[slot].groups:
            clash



def find_chip_slot(chip):
    """Identify possible slots for the given chip. There might be more
    than one grade of possibility (e.g. see test_chip slot, or blocked
    only by chip placements within this class, or blocked by fixed
    unavailability vs. removable clash). It would be good to be able
    to report on the clashes.

    This could be called when a chip is selected:

    1) Collect DAYs on which no CLASS in the chip has this SUBJECT.
      This is perhaps not a fixed criterion, so it might be necessary to
      search within these days too?
    2) Find slots

    """
    pass

# It might be worth having two variants:
#   a) strict, for fast automatic placement – I might then first place
#     the chips with few choices.
#   b) extensive, providing full details of clashes, especially whether
#     a placement would be possibly by moving one or more other chips.
# The second variant might also have an extended mode, where the placement
# possibilities for the displaced chips are investigated. I could accept
# a displacement if all affected chips can be placed. If this gets "stuck"
# a more drastic displacement might be necessary, only failing if a
# displaced chip has no non-fixed slot available. To avoid loops, it
# might be worth "remembering" where each affected chip started. A more
# extensive "memory" might result in code which is more inefficient than
# the cost of a few repetitions.

# Consider at least some form of caching, though it shouldn't get too
# complicated. As soon as a chip is moved (or some parameter changed) it
# might be safest – and least confusing – to clear the caches.

#!!! This is not fully implemented, proper python!
def find_free_slots(chip):
    def test_slot():
        for each teacher in chip:
            if teacher.slots[slot]:
                return False
        for each group in chip:
            if group.slots[slot]:
                return False
        for each room in chip:
            if room.slots[slot]:
                return False
        return True

    slots = []
    for each slot:
        if test_slot():
            slots.append(slot)
    return slots

# It may well be better to use classes instead of groups and for each
# class have bitmaps for the groups.

# One could compare this with a search for chips which fit in a given slot.
# That would raise the additional question of filling the slot – which
# combinations can fill the slot? But then, only certain unfilled slots
# are undesirable, at midday each group needs a break. It might be better
# to leave such considerations to an optimizing stage.
# However, once a chip has been placed, the others can be checked to see
# whether they can be added to this slot (skip if already full? can this
# be tested for easily?).
# Once a chip has been placed thus, it should be reomved from the "unset"
# list for each of its classes.

# The slot-first approach might have some advantages:
#  - easier prior allocation of certain subjects in early slots?
#  - easier allocation of lunch breaks?
# Note that these represent algorithmic complications and they might be
# better handled by more optimization steps based on shorter setting
# times.

# A big question is of how fast can a random setting be done? What is
# the likelihood that there are no solutions or too few?

# To increase the chance that solutions are found, there should be as
# few constraints as possible. Perhaps some constraints can be left
# out at first, then gradually added?

# Could some constraints come bundled with special search strategies?
# E.g.: to force a lunch break, look at days which need one and choose
# the slots where the existing tiles can be replaced most easily.
# Repeat if necessary.
