#!/usr/bin/python
from requests.auth import HTTPBasicAuth

import json
import sys
import requests

# Info for Xqueue sandbox
xqueue_url = 'https://sandbox-xqueue.edx.org'
django_auth = {'username': 'lms', 'password': '***REMOVED***'}
requests_auth = HTTPBasicAuth('anant','agarwal')

# My sandbox
#xqueue_url = 'http://ec2-23-20-116-174.compute-1.amazonaws.com'
#django_auth = {'username': 'lms', 'password': 'pass'}

def main():
    '''
    Demo of the (asynchronous) external grading interface,
        and uploaded file access

    Xqueue API consists of:
        0) login:          Log in
        1) get_queuelen:   Get length of specific queue
        2) get_submission: Get single submission from a specific queue
        3) put_result:     Return the results of a submission
    '''
    if len(sys.argv) > 1:
        queue_name = sys.argv[1]
    else:
        queue_name = 'null'

    # 0. Log in
    #------------------------------------------------------------
    s = requests.session(auth=requests_auth)

    r = s.post(xqueue_url+'/xqueue/login/', data=django_auth)
    (error, msg) = parse_xreply(r.text)
    print msg
    if error: # We'll assume no error code for the remainder of the demo
        return

    # 1. Get length of queue
    #------------------------------------------------------------
    r = s.get(xqueue_url+'/xqueue/get_queuelen/', params={'queue_name':queue_name})
    (_, queuelen) = parse_xreply(r.text)
    queuelen = int(queuelen)
    print "Queue '%s' has %d awaiting jobs" % (queue_name, queuelen)
    if queuelen < 1:
        return

    # 2. Contact xqueue and get a student submission
    #------------------------------------------------------------
    r = s.get(xqueue_url+'/xqueue/get_submission/', params={'queue_name':queue_name})
    (_, xpackage) = parse_xreply(r.text)

    xpackage = json.loads(xpackage)

    xheader = xpackage['xqueue_header'] # Xqueue callback, secret key
    xbody   = xpackage['xqueue_body']   # Grader-specific serial data
    xfiles  = xpackage['xqueue_files']  # JSON-serialized Dict {'filename': 'uploaded_file_url'} of student-uploaded files

    #msg = '<div class="test">Hello</div>'
    msg = '''
<div class="external-grader-message">
    <div class="test">
        <header>
            <h3>Test title #1</h3>
        </header>

        <div class="shortform">
            <p>Short form test info here</p>
        </div>

        <div class="longform">
            <div class="longform-header">
                <p>This is an into to the long form</p>
            </div>
            <div class="longform-body">
                <p>This is the rest of the long form information</p>
                <p>This is the rest of the long form information</p>
                <p>This is the rest of the long form information</p>
            </div>
        </div>
    </div>
</div>
'''

    grader_reply = { 'correct': True,
                     'score': 10,
                     'msg': msg }
    grader_reply = json.dumps(grader_reply)

    # 3. Return graded result to xqueue
    #------------------------------------------------------------
    returnpackage = {'xqueue_header': xheader,
                     'xqueue_body'  : grader_reply,}
    r = s.post(xqueue_url+'/xqueue/put_result/', data=returnpackage)
    print r
    print r.text

def parse_xreply(xreply_str):
    try:
        xreply = json.loads(xreply_str)
        return_code = xreply['return_code'] # Nonzero return code indicates error
        msg = xreply['content']
    except Exception:
        return (1, 'Unexpected reply from server.')
    return (return_code, msg)


if __name__ == "__main__":
    main()
