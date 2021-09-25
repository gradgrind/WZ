# -*- coding: utf-8 -*-

"""
TT/placement.py - last updated 2021-09-12

Handling placement of lessons within the timetable.

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
_REMOVE_FIXED_LESSON = "Folgende Unterrichtsstunden können nicht" \
        " verschoben werden:\n{lessons}"

### -----

class Timetable:
    def __init__(self):
        # For each slot collect the allocated groups
        self.groups = {day: {period: set() for period in PERIODS}
                for day in DAYS}
        # ... and the teachers and "fixed" rooms
        self.teachers = Teachers(teachers)
        self.rooms = Rooms(rooms)
        #self.ndays = len(days)
        #self.nperiods = len(periods)
        # Make an entry for each period of the week, for each class.
        # This is the basis for the class view.
        self.classes = {
            {day: {period: LessonSlot() for period in periods}
                for day in days
            }
                for klass in classes
        }
# Does that include "class" XX?
#TODO: add blocked lessons and lunch-break possibilities

# Actually each class would need a bitvec for every period of the week
# (to determine efficiently whether a group is occupied), but in this
# front-end, the information can be found in the <self.classes> structure
# and that might be adequately efficient. Keeping the information in one
# place can make the code more manageable.

        # Lessons are identified by integers, the corresponding objects
        # are available in this list:
        self.lessons = lessons

#TODO: placements
# Possibly have a special lesson for a blocked period?

#???
        self.klass = self.classes[0]



### *** LESSON PLACEMENT *** ###
# When dealing with lesson placement, presumably also soft constraints
# and the resulting score should be calculated.
# Also room allocation should be done, not only for fixed rooms.

# Multiperiod lessons are managed by referencing the lesson in all covered
# periods. The lesson object itself would have the starting period.
#TODO: This needs error checking!

#TODO: I need special lessons for end-of-day (l = 0? see below),
# teacher-not-available, teacher-lunch-break, class-not-available,
# group-lunch-break, ...
# Could I take the lowest indexes for these? Can they be used repeatedly,
# or do I need a separate item for each usage?
# Maybe not-available and lunch-break should be handled differently –
# lunch-break could be handled entirely as a soft constraint,
# not-available is fixed, perhaps with a negative number (or 0? be careful
# if testing booleans) as lesson index.

    def test_place_lesson(self, lesson, day, period):
        """Test whether the given lesson can be placed in the given period.
        Return a set of blocking lessons or other reasons.
        """
        lesson_object = self.lessons[lesson]
        # Check lessons allocated in this slot for clashes.
        # If the lesson covers more than one period, check also the
        # other affected periods.
        lx = set()
        i = lesson_object['length']
        # If the lesson has length > 1, check that it is not too late in
        # the day.
        if i > 1 and not next_period(period, step = i - 1):
            return {0}
        while True:
            # Seek group clashes
            lesson_groups = lesson_object['groups']
            for klass in lesson_object['classes']:
                # Get the lessons placed in the given slot for this class:
                for l in self.classes[klass][day][period]:
#TODO: A not-available can affect just one group? I haven't catered for that
# in my tables ... at present only whole classes.
                    if self.lessons[l]['groups'] & lesson_groups:
                        lx.add(l)
            # Seek teacher clashes
            for tid in lesson_object['teachers']:
                l = self.teachers[tid][day][period]
                if l:
                    lx.add(l)
#TODO: A possible problem with using "lesson objects" to denote
# class/group/teacher/room not available is that it might be difficult
# to count these as gaps. As these not-availables will mostly be at the
# end of a day, that might not be a big problem. Lunch-breaks could be
# more difficult if these are done as lessons.
            # Seek room clashes
            rooms = lesson_object['rooms'] # a list (can be multiple rooms)
            for roominfo in rooms:
                # (for each required room ...)
                # roominfo is [room or <None>, [room1, room2, ... ]]
                roomlist = roominfo[1]
                if len(roomlist) == 1:
                    # Only this one room is permissible:
                    room = roomlist[0]
                    # Is the room in use?
                    l = self.rooms[room][day][period]
                    if l:
                        # It is occupied by lesson <l>.
                        l_object = self.lessons[l]
                        lrooms = l_object['rooms']
                        for lrinfo in lrooms:
                            # Seek this room in the list of rooms used by <l>
                            if lrinfo[0] == room:
                                if len(rinfo[1]) == 1:
                                    # This is a fixed room allocation,
                                    # this other lesson must be displaced.
                                    lx.add(l)
                                break
                        else:
                            raise Bug("Room not found in allocated lesson")
            # Next period
            i -= 1
            if i > 0:
                period = next_period(period)
            else:
                break
        return lx
#
    def place_lesson(self, lesson, day, period):
        """Place the given lesson in the given slot. Any blocking lessons
        will be removed, if none of them is fixed.
        The classes, teachers and rooms arrays must be set.
        """
        blocking_lessons = self.test_place_lesson(lesson, day, period)
        fixed_blockers = []
        for l in blocking_lessons:
            l_object = self.lessons[l]
            if l_object['fixed']:
                fixed_blockers.append(lesson_print(l_object))
        if fixed_blockers:
            raise TT_GuiError(_REMOVE_FIXED_LESSON.format(
                    lessons = '\n'.join(fixed_blockers)))
        for l in blocking_lessons:
            self.displace_lesson(l)
        ### Place the lesson
        lesson_object = self.lessons[lesson]
        lesson_object['day'], lesson_object['period'] = day, period
        i = lesson_object['length']
        while True:
            # Manage class/group allocation for each covered lesson slot.
            for klass in lesson_object['classes']:
                self.classes[klass][day][period].append(lesson)
            # Manage teacher allocation
            for tid in lesson_object['teachers']:
                self.teachers[tid][day][period] = lesson
            # Manage fixed room allocation – at this stage a room is only
            # allocated if it is "fixed", i.e. if no alternative is given.
            # If the room is already in use, the lesson using it must lose
            # possession. If that lesson also has no alternative, that
            # lesson will have been displaced (above).
            # Also lessons requiring multiple rooms are managed here.
            rooms = lesson_object['rooms'] # a list (can be multiple rooms)
            for roominfo in rooms:
                # (for each required room ...)
                # roominfo is [room or <None>, [room1, room2, ... ]]
                roomlist = roominfo[1]
                if len(roomlist) == 1:
                    # Only this one room is permissible:
                    room = roomlist[0]
                    # Is the room in use?
                    l = self.rooms[room][day][period]
                    if l:
                        # It is occupied by lesson <l>.
                        l_object = self.lessons[l]
                        lrooms = l_object['rooms']
                        for lrinfo in lrooms:
                            # Seek this room in the list of rooms used by <l>
                            if lrinfo[0] == room:
                                if len(rinfo[1]) == 1:
                                    # This is a fixed room allocation, this
                                    # other lesson should have been displaced.
                                    raise Bug("Lesson should have been displaced")
                                else:
                                    # Otherwise just deallocate the room.
                                    lrinfo[0] = None
                                break
                        else:
                            raise Bug("Room not found in allocated lesson")
                    roominfo[0] = room
                    self.rooms[room][day][period] = lesson
                else:
                    # Don't allocate a room yet.
                    roominfo[0] = None
                    # (actually, this field should already be empty ...)
            # Next period
            i -= 1
            if i > 0:
                period = next_period(period)
            else:
                break
#TODO: Update the gui
#
    def displace_lesson(self, lesson):
        """Remove lesson from timetable.
        It must be removed from the classes(, groups?), teachers and rooms
        arrays.
        """
        lesson_object = self.lessons[lesson]
        day, period = lesson_object['day'], lesson_object['period']
        lesson_object['day'], lesson_object['period'] = None, None
        rooms = lesson_object['rooms']
        teachers = lesson_object['teachers']
        classes = lesson_object['classes']
        i =  lesson_object['length']
        while True:
            # Manage class/group deallocation for each covered lesson slot.
            for tid in teachers:
                if self.teachers[tid][day][period] != lesson:
                    raise Bug("Teacher-lesson mismatch")
                self.teachers[tid][day][period] = None
            for room in rooms:
                if room:
                    if self.rooms[room][day][period] != lesson:
                        raise Bug("Room-lesson mismatch")
                    self.rooms[room][day][period] = None
            for klass in classes:
                # Here the slots are lists ...
                try:
                    # This list is modified, not replaced!
                    self.classes[klass][day][period].remove(lesson)
                except ValueError:
                    raise Bug("Class-lesson mismatch")
            # Next period
            i -= 1
            if i > 0:
                period = next_period(period)
            else:
                break
#TODO: Update the gui



#TODO: A room allocator for rooms with a list of options.
# This can be used at the end ofan automatic placement run, or perhaps
# immediately for manual placements.
# It would involve, roughly:
# First check if there are possibilities among the options.
# Otherwise go through each blocking lesson to see if anything can be
# freed up. This can be done recursively.

# In the menu for a placed(!) lesson, it should be possible to select the
# room, where there is a choice. This could mean displacing or
# reallocating another lesson, probably in another class. I suppose this
# should be offered with a warning about what will happen to which lesson.
# As with aSc it is maybe betterto indicate that a lesson is missing a
# room than to remove it. This could perhaps be done with some sort of
# colouring or other highlighting.

# In the end, it makes no sense to have a very complicated system, it
# could make the code difficult to follow and unreliable. The way aSc
# does it is actually quite acceptable.

#
# For a lesson try to find a room or rooms from the list of options
    def get_room(self, day, period, room):
        """Try to free the given room from the lesson it houses. This works
        if there is a free room in the options for that lesson.
        """
# The first run should probably just be a test ...
        i = 0
        rslot = self.rooms[day][period]
        rl = rslot[room]
        i = 0
        for r in rl.rooms:
            if r == room:
                options = rl.room_options[i]
                for o in options:
                    ol = rslot[o]
                    return (rl, i, o)
            i += 1
        return None
#

#TODO:
# To actually perform the above replacement:
        rl.rooms[i] = o
        self.rooms[day][period][o] = rl



#
    def which_lessons(self, day, period):
        """Discover which lessons can be placed directly in the given
        period without any conflicts.
        """
# Is this really useful, and should there be a distinction between hard
# and soft constraints? Should I calculate and display the score?

###


#TODO!
# Perhaps the shown info can be filtered according to where the lesson
# is displayed?
# In lesson tiles: Fr A ESM ? The full info can be shown on hover (etc.)
# in a status line.
# In clashes, possibly multiple full info in status line(s).
# In a class view, only groups from other classes should be shown as
# class.group.
def lesson_print(lesson_object):
    """Return an informative string describing the lesson.
    """
    return "10G [A] Fr ESM r10G *2 @ Di:3"
    # class of definition?
    # active classes
    # groups
    # subject
    # teachers
    # length
    # if set: day, period

#
def next_period(period, step = 1):
    """Return the key of the following period, or <None> if <key>
    is the last period.
    """
    try:
        return PERIODS[PERIODS.index(period) + step]
    except IndexError:
        return None



###############################??????? Rather just use dicts and lists?
class Rooms(dict):
    def __init__(self, rooms):
        """Every room has a lesson reference for each period of the week.
        """
        super().__init__()
        for room in rooms:
            self[room] = {day: {period: None for period in periods}
                for day in days
            }

###

class Teachers(dict):
    def __init__(self, teachers):
        """Every teacher has a lesson reference for each period of the week.
        """
        super().__init__()
        for teacher in teachers:
            self[teacher] = {day: {period: None for period in periods}
                for day in days
            }

#TODO: add blocked lessons and lunch-break possibilities

###

class LessonSlot(dict):
    """A period within the timetable of a class.
    """
    def __init__():
        super().__init__()
        self.groups = set()
        self.lessons = []

###

class Lesson:
    """Representation of a "lesson" within the timetable.
    """
    def __init__(self):
        self.sid = None
        self.classes = []
        self.groups = []
        self.teachers = []
        self.rooms = []
        self.room_options = []
        self.placement = None
    #
#    def place_test(self, day, period):
#        """Test whether this lesson can be placed in the given slot.
#        """


