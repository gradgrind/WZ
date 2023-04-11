try:
    standalone = STANDALONE
except NameError:
    standalone = False
if not standalone:
#    from .attendance import init; init()
    from .year_manager import init; init()
    from .pupils_manager import init; init()
    from .classes_manager import init; init()
    from .teachers_manager import init; init()
    from .course_editor import init; init()
    from .grades_manager import init; init()
    from .timetable_editor import init; init()
