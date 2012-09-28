#!/usr/bin/env python

# Create all the directories. Use all the inodes.
# DO NOT RUN AT HOME...

import os

def main():
    i = 0
    while True:
        i += 1
        if i % 100 == 0:
            print "Made {0} dirs!".format(i)
        os.mkdir('deepdir')
        os.chdir('deepdir')

if __name__ == "__main__":
    main()
