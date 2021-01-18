import os

for i in range(1):
    try:
        if os.fork() == 0:
            # in child
            break
        print("forked!")
    except:
        import sys
        print("Got exception: " + str(sys.exc_info()))

import time
time.sleep(60)   # Can I see a bunch of these in top?
print("hello world")

