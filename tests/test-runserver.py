#!/usr/bin/env python
"""
Send some test programs to an xserver.

For each dir in the current directory, send the contents of payload.xml and each
of the correct*.py and wrong*.py files.
"""

import argparse
import glob
import json
import logging
import os
import os.path
import requests
import sys
import time
import random

logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger(__name__)

runserver = 'http://127.0.0.1:3031/'

unique = str(random.randint(100000, 999999))

def upload(paths):
    """
    Given a list of paths, upload them to the sandbox, and return an id that
    identifies the created directory.
    """
    files = { os.path.basename(f)+unique: open(f) for f in paths}
    return upload_files(files)

def upload_files(files):
    endpoint = upload_server + 'upload'
    r = requests.post(endpoint, files=files)

    if r.status_code != requests.codes.ok:
        log.error(f"Request error: {r.text}")
        return None

    if r.json is None:
        log.error("sandbox50 /upload failed to return valid json.  Response:" +  r.text)
        return None

    id = r.json.get('id')
    log.debug('Upload_files response: ' + r.text)
    return id

def run(id, cmd):
    # Making run request

    headers = {'content-type': 'application/json'}
    run_args = {'cmd': cmd,
                'sandbox': { 'homedir': id }}

    endpoint = runserver + 'run'
    r = requests.post(endpoint, headers=headers, data=json.dumps(run_args))

    if r.json is None:
        log.error("sandbox50 /run failed to return valid json.  Response:" +  r.text)
        return None

    log.debug('run response: ' + r.text)
    return r.json

def main(args):
    global runserver
    global upload_server
    if len(args) < 4:
        print("Usage: test-runserver.py http://x-server-to-upload-to:port/ http://x-server-to-run-on:port/ FILES cmd")
        print("The first file in FILES will be randomized by appending a random string,")
        print("and the name of that file in 'cmd' will be modified the same way.")
        sys.exit(1)

    upload_server = args[0]
    if not upload_server.endswith('/'):
        upload_server += '/'
    runserver = args[1]
    if not runserver.endswith('/'):
        runserver += '/'

    files = args[2:-1]
    cmd = args[-1]

    start = time.time()
    id = upload(files)
    print("Upload took %.03f sec" % (time.time() - start))
    
    start = time.time()
    cmd = cmd.replace(files[0], files[0]+unique)
    r = run(id, cmd)
    print("run took %.03f sec" % (time.time() - start))
    if r is None:
        print('error')

if __name__=="__main__":
    main(sys.argv[1:])

