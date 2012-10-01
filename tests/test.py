#!/usr/bin/env python
"""
Send some test programs to an xserver.

For each dir in the current directory, send the contents of payload.xml and each
of the correct*.py and wrong*.py files.
"""

import argparse
import glob
import json
import os
import os.path
from path import path
import requests
import sys
import time

xserver = 'http://127.0.0.1:3031/'

def send(payload, answer):
    """
    Send a grading request to the xserver
    """

    body = {'grader_payload': payload,
            'student_response': answer}

    data = {'xqueue_body': json.dumps(body),
            'xqueue_files': ''}

    start = time.time()
    r = requests.post(xserver, data=json.dumps(data))
    end = time.time()
    print "Request took %.03f sec" % (end - start)

    if r.status_code != requests.codes.ok:
        print "Request error"

    #print "Text: ", r.text
    return r.text


def check_contains(string, substr):
    if not substr in string:
        print "ERROR: Expected '{0}' in '{1}'".format(substr, string)

def check_not_contains(string, substr):
    if substr in string:
        print "ERROR: Expected '{0}' not to be in '{1}'".format(substr, string)

def check_right(string):
    check_contains(string, '\"correct\": true')

def check_wrong(string):
    check_contains(string, '\"correct\": false')

def check(dirname):
    """
    Look for payload.json, correct*.py, wrong*.py, run tests.
    """
    payload_file = os.path.join(dirname, 'payload.json')
    if not os.path.isfile(payload_file):
        print "no payload.json in {0}".format(dirname)
        return

    with open(payload_file) as f:
        payload = f.read()

    for name in glob.glob(os.path.join(dirname, 'correct*.py')):
        print "Checking correct response from {0}".format(name)
        with open(name) as f:
            answer = f.read()
        check_right(send(payload, answer))

    for name in glob.glob(os.path.join(dirname, 'wrong*.py')):
        print "Checking wrong response from {0}".format(name)
        with open(name) as f:
            answer = f.read()
        check_wrong(send(payload, answer))

def main(args):
    global xserver
    if len(args) != 1:
        print "Usage: test.py http://some-x-server:port/"
        sys.exit(1)

    xserver = args[0]
    if not xserver.endswith('/'):
        xserver += '/'

    root = '.'
    for name in os.listdir(root):
        d = os.path.join(root, name)
        if os.path.isdir(d):
            check(d)

if __name__=="__main__":
    main(sys.argv[1:])

