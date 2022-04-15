"""
timetable/tt_process.py - last updated 2022-03-27

Activity allocation and other timetable processing

==============================
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
"""

#TODO ...

_TEST = False
_TEST = True

WEIGHTS = [None, "50", "67", "80", "88", "93", "95", "97", "98", "99", "100"]

LUNCH_BREAK = ("mp", "Mittagspause")

_MAX_GAPS_PER_WEEK = 10 # maximum value for max. gaps per week (for classes)


### Messages


########################################################################

import sys, os

if __name__ == "__main__":
    # Enable package import if running as module
    this = sys.path[0]
    appdir = os.path.dirname(this)
    sys.path[0] = appdir
    basedir = os.path.dirname(appdir)
    from core.base import start

    # TODO: Temporary redirection to use real data (there isn't any test data yet!)
    #    start.setup(os.path.join(basedir, 'TESTDATA'))
    #    start.setup(os.path.join(basedir, 'DATA'))
    start.setup(os.path.join(basedir, "NEXT"))

from typing import NamedTuple, Dict, List, Set, FrozenSet, Tuple

### +++++

#? use exception instead?
CONSTRAINT_FAIL = 10000

### -----

#TODO ... here is a first sketch:
def test_activity(activity_id, slot):
    activity = all_activities[activity_id]
    clashes = []
    penalty = 0
    # For activities with duration > 1, each slot must be checkd
    for i in range(activity.LENGTH):
        if activity.TAG:
            # Check teachers in block separately from subactivities
            tids = activity.TAG.BLOCK_TIDS
            if tids:
                clashes += test_teachers(tids, slot)
            for aid in activity.TAG.ACTIVITIES:
                subactivity = all_activities[aid]
                if not tids:
                    # For parallel activities (not blocks)
                    clashes += test_teachers(subactivity.TIDS, slot)
                c, p = test_one_activity(subactivity, slot)
                clashes += c
                penalty += p
        else:
            clashes += test_teachers(activity.TIDS, slot)
            c, p = test_one_activity(activity, slot)
            clashes += c
            penalty += p
        slot += 1
    return clashes, penalty

# Can I avoid repeated teacher testing in blocks?
# If I revert to a single activity it would be automatic, but I would need
# to have multiple class/group entries. This could be done by using a
# list of (class, group-set) pairs.
# A disadvantage of that would be the loss of per class teacher/subject
# lists.
# An alternative might be to separate teacher handling for block activities.
# There may be only little difference in efficiency ... by using a dict
# for the clashes, duplications could be avoided:
#    teacher_clashes[tid] = TeacherNotAvailable

def test_teachers(tids, slot):
    clashes = []
    for tid in tids:
        teacher = all_teachers[tid]
        aid = teacher.slots[slot]
        if aid != 0:
            if aid < 0:
                clashes.append(TeacherNotAvailable(tid))
            else:
                clashes.append(TeacherBusy(aid))
    return clashes

# Split blocks into multiple (one per class) activities?
# They could share a sort of link object accumulating the teachers?
# Also for other parallel activities ... assuming that is regarded as 100%.
# The test would presumably need to include the tied activities.

# Blocks can share teachers, other parallel activities can't.
# Most activities have one teacher and one class. But to cope with
# the other cases it might be simplest to have lists? But parallel
# activities should not include things from "sisters" ... so if there
# is a shared list, it would need to be in a distinct structure.
# I suppose this could list all component activities, these being then
# tested individually.

# What information do I need from a clash report? Conflicting activities?
# Teacher/class not available? Would just teacher/group problem be
# enough (could then inspect their week). For other constraints it might
# be enough to reference the constraint (constraints should have a
# text representation).

def test_one_activity(activity, slot):
# Here assume a single class + group-set per activitiy
    clashes = []
    klass = activity.CLASS
    aids = class_slots[slot]
    if aids == None:
        clashes.append(ClassNotAvailable(klass))
    else:
        groups = activity.GROUPS    # atomic groups
# At present the groups include the class, which is duplication ...
        for aid in aids:
            activity2 = all_activities[aid]
            if activity2.GROUPS & groups:
                clashes.append(GroupBusy(aid))
    # Handle constraints
    penalty = 0
    for cix in activity.CONSTRAINTS:
        constraint = all_constraints[cix]
#?
        cval = constraint.handle(slot) # aid?
        if cval:
            if cval < 0:
#?
                clashes.append(constraint.report(aid)) #?
            else:
                penalty += cval
    return clashes, penalty




class ProcessData:
    def __init__(self):
        self.teacher_constraints = {}

    def add_teacher_constraint(self, tid, constraint):
        try:
            self.teacher_constraints[tid].append(constraint)
        except KeyError:
            self.teacher_constraints[tid] = [constraint]


class TeacherConstraint:
    def __init__(self, tid):
        self.tid = tid

# Actually, at this stage there is no process data! That is passed to
# the constraint handler while checking ...
# These constraint items are the general (thread-safe) handlers.
class Teacher_LUNCHBREAK(TeacherConstraint):
    def __init__(self, data, tid):
        """Teacher's lunch breaks
        For each period (or at least each possible lunch period) there
        should be a list of other periods such that one of them needs
        to be free.
        """
        super().__init__(tid)
        self.lunch_map = tuple(set() for i in data.periods_per_week)
        x = 0
        for daylist in data.TEACHERS.lunch_periods[tid]:
            for p in daylist:
                self.lunch_map[x + p].update(x + i for i in daylist if i != p)
            x += data.periods_per_day

#???
    def constrain(self, allocation_map, period):
        """If this period is allocated, is there a lunch break?
        It is assumed that <period> is free!
        """
        for p in self.lunch_map[period]:
            if self.tid not in allocation_map[p]:
                return 0
        return CONSTRAINT_FAIL


class Teacher_MINPERDAY(TeacherConstraint):
    def __init__(self, data, tid, value):
        super().__init__(tid)
#TODO
        # Add to (teacher) constraints
        # Link from teachers? Link from activities?
        # Each activity could simply have a list of constraint indexes?
        #  ... I suppose length (duration in periods), too ... though that
        # could be in another list?
        # If there is just a single constraint list (no guarantee that
        # that will cover all constraint needs!), those for teachers
        # should be shared, not repeated. This approach will probably
        # need more storage (teacher constraint list repeated for each
        # activity).

"""
To allow parallel "runs" it would be necessary to duplicate the data
structures which can be modified. That is, things like allocation arrays
and constraint "penalties". Basic, fixed, data structures (e.g. Teachers,
Activities?) could be shared between "runs".

Demands:
 - Check if activity can be placed in a particular period (-> delta penalty?).
 - Place activity (changes penalty).

A check will consider teachers and pupil groups and various constraints,
which could concern subjects, etc.
Is it possible to avoid getting multiple penalties when multiple atomic
groups are concerned? If the constraints are activity-based and not
group-based this should be automatic.

Performing a check, various constraint penalties can be changed. These
need to be collected separately or managed in such a way that they can
be reverted easily. This could be a list of (constraint, new value) pairs.
The new value could also be a delta. It would also be possible to build
a complete new constraint-penalty array. Depending on the memory management,
that could even be more efficient. That would be a sort of snapshot
arrangenment, and conceptually nice and simple!

Then there is the question of whether I want to move to integer-indexed
arrays for the items that are currently string-indexed. Would there be
a significant efficiency improvement (in Python!)? It might be sensible
to start without the transformation, as this would be "simpler". It
could be modified if improvements are needed.

It would probably be good to have just one master placement map, which
could be an array of placements (day + period), one for each activity –
a single value, week-period, would be more compact ...

How would a check go?
 - Groups busy/blocked?
 - Teachers busy/blocked?
 - class/group lunch breaks
 - (*) class/group gaps
 - (*) class/group min. lessons
 - ...
 - (*) teacher gaps
 - (*) teacher min. lessons
 - teacher max. block length
 - teacher lunch breaks
 - ...

 - activities: subjects on same day
 - activities: subject ordering

 - Rooms busy/blocked? This is tricky because there might be a list of
 alternatives for some or all of the rooms. If there is a free room in
 the list, that can be taken. If not, the activities using the rooms in
 the list need to be checked to find out if they can use an alternative ...

 - ...

Some of the constraints (*) are not so suited for insertion testing, they
are rather orientated towards final evaluation of the completed timetable.
Perhaps these should be kept separate. In an allocation algorithm there
might need to be special handlers.
"""

class Timetable:
    """Each teacher has a weekly period-array containing an activity index,
    0 (no activity) or -1 (blocked). In this module the teachers are
    referenced by index!
    """

    def __init__(self, teacher_info, class_info, room_info):
        self.teacher_info: List[Tuple[str,List[int],list]] = teacher_info
        # The constraint list (last tuple element) contains pairs:
        #   (function, value).
        # The function is one of the "teacher_constraint" methods below.

# It may be better to have just one method for all teacher constraints?
# Otherwise a lot of data must be passed around ...
# On the other hand, maybe that is better than untidy code?
    def teacher_constraint_LUNCHBREAK(self,
            tix:int,
            period:int,
            lunch_map:List[Set[int]]
        ) -> int:
        """This constraints has – at present – no weighting factor, either
        there must be a lunch break, or there needn't be one.
        """
#? pass tweek instead of tix?
        tweek = self.teacher_info[tix][1]
        if tweek[period] < 1:
            return 0
        # Check "companion" periods
        for p in lunch_map[period]:
            if tweek[p] < 1:
                return 0
        return CONSTRAINT_FAIL
# Or raise exception?
        raise TT_Constraint_Broken(_NO_LUNCH_BREAK.format(tix=tix, period=period))

    def teacher_constraint_MINPERDAY(self, tix, period, value):
#TODO: This one doesn't make any sense as a blocking constraint for
# activity allocation. It might be better as a final evaluation ...
# On the other hand, doing manual allocation it might be good to have
# a constant overview of the not (yet/ideally) fulfilled constraints?
        pass

# What about a list/mapping of current constraint points?

# Actually, it is probably sensible not to count a blocked lesson as
# a gap! I.e. only 0 counts as gap ... as far as plain gaps are concerned.

    def day_gaps(self, weeklist, day):
        daylist = []
        i = day*self.periods_per_day
        l = i + self.periods_per_day
        while weeklist[i] <= 0:
            i += 1
            if i == l:
                return 0
        while True:
            l -= 1
            if l == i:
                return 0
            if weeklist[l] > 0:
                break
        gaps = 0
        for j in range(i + 1, l):
            if weeklist[j] <= 0:
                gaps += 1
        return gaps

# It might be best to have a sort of cache which is updated when an
# allocation or deallocation is made.
        # init:
        self.gaps = [0] * len(data.daytags)
        # ...
        self.gaps0 = self.gaps.copy()
        l = data.periods_per_day
        i0 = day * l
        daylist = weeklist[i0:i0+l]
        daylist[period] = aid
        i = 0
        gaps, pgaps = 0, -1
        started = False
        for a in daylist:
            if a > 0:
                if pgaps > 0:
                    gaps + pgaps
                pgaps = 0
            elif pgaps >= 0:
                pgaps += 1


    def teacher_constraint_MAXGAPSPERDAY(self, tix, period, value):
#? tweek?
        gaps = self.day_gaps(tweek, period // self.periods_per_day)



    def teacher_constraint_MAXGAPSPERWEEK(self, tix, period, value):
        gaps = 0
#? ndays? tweek?
        for dayix in range(ndays):
            gaps += self.day_gaps(tweek, dayix)



    def teacher_constraint_MAXBLOCK(self, tix, period):
        pass


