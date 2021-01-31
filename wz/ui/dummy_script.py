# -*- coding: utf-8 -*-

import sys
import time
sys.stdin.reconfigure(encoding='utf-8') # requires Python 3.7+


def flush_then_wait():
    sys.stdout.flush()
    sys.stderr.flush()
    time.sleep(0.5)


sys.stdout.write("Script stdout 1\n")
sys.stdout.write("Script stdout 2\n")
sys.stdout.write("Script stdout 3\n")
sys.stderr.write("Total time: 00:05:00\n")
sys.stderr.write("Total complete: 10%\n")
flush_then_wait()

sys.stdout.write("name=Martin\n")
sys.stdout.write("Script stdout 4\n")
sys.stdout.write("Script stdout 5\n")
sys.stderr.write("Total complete: 30%\n")
flush_then_wait()

sys.stderr.write("Elapsed time: 00:00:10\n")
sys.stderr.write("Elapsed time: 00:00:50\n")
sys.stderr.write("Total complete: 50%\n")
sys.stdout.write("country=Nederland\n")
flush_then_wait()

sys.stderr.write("Elapsed time: 00:01:10\n")
sys.stderr.write("Total complete: 100%\n")
sys.stdout.write("Script stdout 6\n")
sys.stdout.write("Script stdout 7\n")
sys.stdout.write("website=www.learnpyqt.com\n")
flush_then_wait()

for line in sys.stdin:
    if line[0] == '!':
        for i in range(10):
            time.sleep(0.5)
            print("STEP %d\n" % (i + 1), flush = True)
        time.sleep(1.0)
        print("XXX", flush = True)
    elif line[0] == '$':
        break
    else:
        time.sleep(1.0)
        print(">>>", line, flush = True)
