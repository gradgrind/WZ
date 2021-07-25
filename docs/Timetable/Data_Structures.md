# Data Structures

All items – lessons, rooms, teachers and class-groups – are stored in arrays, so that they can be addressed by indexes rather than addresses. A 16-bit index should be plenty for all normal needs here, even the lessons. However, by using a type alias, some flexibility can be ensured.

### Lessons

These have a list of class-groups, a list of teachers, a list of rooms. A lesson record could be represented by a variable length cell array, the length depending on how many entries each of the fields has. If all records are allocated from a single large array. As it is built when data input is complete and presumably not changed subsequently, except for lesson allocation and deallocation, the variable length should be no great problem. All indexes would be to this mega-array. Of course, great care should be exercised to ensure that accesses remain within the allocated area.

`class-groups` are perhaps best represented as pairs: class-index + group-map. That would require two cells. This can be followed by other such pairs, or by a null cell (terminator).

`teachers` is a null-terminated list of teacher-indexes.

`rooms` is a null-terminated list of room-indexes.

### Rooms

Each room needs a week-array of Lesson_Indexes. I assume that a room can only accommodate one lesson tile per period.

### Teachers

Each teacher needs a week-array of Lesson_Indexes. I assume that a teacher can only be attached to one lesson tile per period.
 
### Classes and Groups
 
A class can have multiple lessons per period. For a clash check, an array of bitmaps for allocated groups in each period is probably useful.

To handle reconstruction of group lists from group bitmaps, a dictionary is probably the most straightforward (although bit-shifting might be an alternative).

Although not *strictly* necessary, a direct way to get at the lessons associated with a given period is probably sensible. They could be accessed by searching through the whole global lesson list, but this seems rather inefficient. Of course a simple array won't work here because of periods with multiple lessons.

### Subjects

To avoid multiple lessons in some subject on one day, a days-array for each subject and each class/group could be helpful. It could indicate which period is already occupied by this subject. This could well result in a rather sparse data structure, but the total space will not be large enought to make this a problem. Say, max. 100 subjects, 5 days, max 50 classes (could be a lot more if groups are handled completely separately). For each day a single byte would be enough. That would be 25kB, plus handling of the groups, the space for this depending very much on the representation, in total probably significantly less than 1MB.

## Slots for a lesson chip

When a chip is selected, this is probably the desired action.

Identify possible slots for the given chip. There might be more than one degree of possibility (e.g. blocked by fixed constraints vs. blocked by other chip placements). It would be good to be able to report on the clashes.

Further information might come from other constraints, e.g. "two chips for a subject should not be placed on the same day."

A possible algorithm:

```
for i in range(nslots):
    state = 0
    for each teacher:
        t = teacher.slots[i]
        if t not null:
            state = t
            break
    if state < 0:
        states[i] = state
    
    for each klass, groups:
        k = klass.slots[i]
        if k & groups not null:
# If classes are to have fixed blocking constraints, that could be done via a negative
# value here. But if groups can have fixed blocking, perhaps I would need separate full
# entries for each group?


# Rooms can be handled like teachers.

```

## Lesson chips for a given slot

When a slot is selected, this is probably the desired action. The selection will be within a particular class.

Identify possible chips for the given class and slot. There might be more than one degree of possibility (e.g. blocked by fixed constraints vs. blocked by other chip placements). It would be good to be able to report on the clashes.

Further information might come from other constraints, e.g. "two chips for a subject should not be placed on the same day."

It might also be interesting to know which already placed chips could be moved to the slot, so perhaps _all_ the chips for the given class should be checked.

## Further tests

When attempting automatic placement one could either try to fill the slots or try to place the chips. In either case, it might make sense to start with the items which have the fewest choices.

Placing a chip in a slot would have no effect on other slots, but it might not fill the slot completely. Should one then try to fill the slot, or move on to the next slot?

If searching for a placement for a chip, it might be good to prefer earlier slots.

There should probably not be too many decisions because that costs time. Fine details will need to be settled later with a scoring mechanism.

Indeed the simplest approach might be to only seek matches without blocks. If there are none, then a move would be necessary, so slots with chip clashes would then need to be taken into account.

Classes (and individual groups?) can have fixed blocks, as can teachers, and perhaps rooms. What about subjects? If so, it might make more sense to place them manually?
