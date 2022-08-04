try:
    standalone = STANDALONE
except NameError:
    standalone = False
if not standalone:
    from .attendance import init; init()
    from .pupils_manager import init; init()
    from .teachers import init; init()
    from .course_lessons import init; init()
