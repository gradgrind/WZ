# -*- coding: utf-8 -*-

import sys
import time
sys.stdin.reconfigure(encoding='utf-8') # requires Python 3.7+


def flush_then_wait():
    sys.stdout.flush()
    sys.stderr.flush()
    time.sleep(0.5)


for line in sys.stdin:
    if line[0] == '!':
        for i in range(10):
            time.sleep(0.5)
            print("STEP %d\n" % (i + 1), flush = True)
        time.sleep(1.0)
        print("---", flush = True)
    elif line[0] == '$':
        break
    else:
        time.sleep(0.1)
        print(">>>", line.rstrip(), flush = True)
        print("---", flush = True)
