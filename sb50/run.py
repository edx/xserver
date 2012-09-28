#!/usr/bin/env python
"""Helper script to run a command on sandbox50"""

import json
import logging
import requests
import os
import os.path
import sys
import time
import settings

run_url = None

def upload(paths):
    """
    Given a list of paths, upload them to the sandbox, and return an id that
    identifies the created directory.
    """
    files = dict( (os.path.basename(f), open(f)) for f in paths)
    return upload_files(files)

def upload_files(files):
    endpoint = settings.RUN_URL + 'upload'
    r = requests.post(endpoint, files=files)

    if r.status_code != requests.codes.ok:
        log.error("Request error: {0}".format(r.text))
        return None

    #log.debug("Response: " +  r.json)

    id = r.json.get('id')
    return id

def run(id, cmd):
    # Making run request

    headers = {'content-type': 'application/json'}
    run_args = {'cmd': cmd,
                'sandbox': { 'homedir': id }}
    endpoint = settings.RUN_URL + 'run'
    r = requests.post(endpoint, headers=headers, data=json.dumps(run_args))
    return r.json


def sb50_run_code(code):
    """Upload passed in code file to the code exec sandbox as code.py, run it.

    Return tuple (stdout, stderr), which may be None"""

    #print "Running code: \n{0}".format(code)

    files = {'code.py': ('code.py', code)}
    start = time.time()
    id = upload_files(files)
    # TODO: statsd
    print "upload took %.03f sec" % (time.time() - start)

    start = time.time()
    r = run(id, '/usr/bin/python code.py')
    print "run took %.03f sec" % (time.time() - start)

    return r['stdout'], r['stderr']
