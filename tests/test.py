#!/usr/bin/env python
"""
Send some test programs to an xserver.

For each dir in the current directory, send the contents of payload.xml and each
of the answer*.py, right*.py and wrong*.py files.
"""

import argparse
import glob
import json
import os
import os.path
import pprint
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
    print("Request took %.03f sec" % (end - start))

    if r.status_code != requests.codes.ok:
        print("Request error")

    #print "Text: ", r.text
    return r.text


def check_output(data, verbose, expected_correct):
    try:
        d = json.loads(data)
        if d["correct"] != expected_correct:
            print("ERROR: expected correct={}.  Message: {}".format(
                expected_correct, pprint.pformat(d)))

        elif verbose:
            print("Output: ")
            pprint.pprint(d) 

    except ValueError:
        print("ERROR: invalid json %r" % data)

def globs(dirname, *patterns):
    """
    Produce a sequence of all the files matching any of our patterns in dirname.
    """
    for pat in patterns:
        yield from glob.glob(os.path.join(dirname, pat))

def contents(fname):
    """
    Return the contents of the file `fname`.
    """
    with open(fname) as f:
        return f.read()

def check(dirname, verbose):
    """
    Look for payload.json, answer*.py, right*.py, wrong*.py, run tests.
    """
    payload_file = os.path.join(dirname, 'payload.json')
    if os.path.isfile(payload_file):
        payload = contents(payload_file)
    else:
        graders = list(globs(dirname, 'grade*.py'))
        if not graders:
            #print "No payload.json or grade*.py in {0}".format(dirname)
            return
        if len(graders) > 1:
            print(f"More than one grader in {dirname}")
            return
        # strip off everything up to and including graders/

        p = os.path.abspath(graders[0])
        index = p.find('graders/')
        if index < 0:
            #
            print("{} is not in the 6.00x graders dir, and there's no payload.json file"
                    ", so we don't know how to grade it".format(p))
            return
        else:
            grader_path = p[index + len('graders/'):]
            print('grader_path: ' + grader_path)
        payload = json.dumps({'grader': grader_path})

    for name in globs(dirname, 'answer*.py', 'right*.py'):
        print(f"Checking correct response from {name}")
        answer = contents(name)
        check_output(send(payload, answer), verbose, expected_correct=True)

    for name in globs(dirname, 'wrong*.py'):
        print(f"Checking wrong response from {name}")
        answer = contents(name)
        check_output(send(payload, answer), verbose, expected_correct=False)

def main(argv):
    global xserver

    parser = argparse.ArgumentParser(description="Send dummy requests to a qserver")
    parser.add_argument('server')
    parser.add_argument('root', nargs='?')
    parser.add_argument('-v', dest='verbose', action='store_true', help="verbose")

    args = parser.parse_args(argv)

    xserver = args.server
    if not xserver.endswith('/'):
        xserver += '/'

    root = args.root or '.'
    for dirpath, _, _ in os.walk(root):
        check(dirpath, args.verbose)

if __name__=="__main__":
    main(sys.argv[1:])
