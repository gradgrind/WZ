# Course (subject) Table

The course table contains the course (subject) information for each class. It also contains basic information on chosen courses for each pupil. It is stored as a compressed JSON-file. All _leaf_-values are strings.

The top-level keys are:

- `TITLE`: currently not used in any significant way,
- `SCHOOLYEAR`: the calendar year in which the school-year ends (e.g. 2021 for year 2020 – 2021),
- `__MODIFIED__`: timestamp (not really used, but might be useful in the stored version),
- `__SUBJECTS__`: mapping, the key is the school-class, the value is the list of subject-data mappings,
- `__CHOICES__`: a mapping, the key is the pupil-id, the value is a list of subject-ids for courses which the pupil _doesn't_ take.

The reason for the negative definition of the `__CHOICES__` field is that it allows an entry for a pupil to be optional: only pupils need to be included where there _are_ non-taken courses.

The subject-data mappings have the following keys:

- `SID`: subject-id,
- `TIDS`: (space separated) list of teacher-ids,
- `GROUP`: teaching group, e.g. '*' (whole class) or 'G',
- `COMPOSITE`: (space separated) list of dependent subject-ids, with optional weighting (e.g. '$D' or '$Ku:2'),
- `SGROUP`: subject-group (area of report form for the subject).

