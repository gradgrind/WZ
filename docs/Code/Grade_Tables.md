# Grade Tables

These represent the grades for all pupils in a group (which can be a whole class) for a particular term (semester, etc.). They include general data such as school-year, class/group, date of issue, etc., as well as the individual subject grades for the pupils. There can also be further, non-grade information, such as a qualification which will be awarded, a report category (for example, a normal report or a leaving report) and a comment section.

The data is structured internally as a mapping ("dict" in python):

```python
{'HEADER':
 	{'SCHOOLYEAR': '2021',
     'GROUP': '12.G',
     'TERM': '2',
     'ISSUE_D': '2021-07-21',
     'GRADES_D': '2021-07-10'
    },
 'MEMBERS':
 	[{'PID': '001234', 'NAME': 'Hans Müller', 'LEVEL': 'Gym',
      '__GRADES__': {'De': '08', 'En': '11', ...},
      '__EXTRA__': {..., '+Q': '13', '+Z': 'Zeugnis', ...}
     },
        ...
    ],
 '__MODIFIED__': '2021-07-10'
}
```

The subjects taught in a group are available in the subject/course table for the class, which can be filtered according to the group in question. All subjects which are relevant for the group should be graded, an ungraded subject is seen as rendering the grading incomplete. Subjects which are not taken by a particular pupil receive a "special grade": '/'. There may be other "special grades" to cover particular situations (e.g. not gradable because of long absence).

This data-mapping is stored as a compressed JSON-file, which allows a direct, one-to-one correspondence to the structure defined above.

It might be worth considering an additional top-level entry, `__PID__`, providing a mapping from the pupil-id ('PID' field) to the data for that pupil in the  'MEMBERS' list. This can, however, be generated externally whenever needed.

