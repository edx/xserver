#!/usr/bin/python
#------------------------------------------------------------
# File: pyxserver_wsgi.py
# Author: T. H. Kim <kimth@stanford.edu>
#
# Re-wrapped pyxserver to be compatible with nginx + (uWSGI or gunicorn)
#
# Run me with (may need su privilege for logging):
#        gunicorn -w 4 -b 127.0.0.1:3031 pyxserver_wsgi:application
#------------------------------------------------------------

import json
from time import localtime, strftime

import pyxserver
import logging


def do_GET(data):
    return "Hey, the time is %s" % strftime("%a, %d %b %Y %H:%M:%S", localtime())


def do_POST(data):
    payload = json.loads(data)
    body = payload['xqueue_body']

    post = json.loads(body)

    # Parse ExternalResponse interface
    cmd = post['edX_cmd']
    tests = post['edX_tests']
    processor = post['processor']
    print ' [*] cmd: %s' % cmd
    #print ' [*] tests: %s' % tests
    #print ' [*] processor: %s' % processor

    if cmd == 'get_score':
        student_response = post['edX_student_response']
        award, message = pyxserver.run_code_sandbox(processor, student_response, tests)

        '''
        # ExternalResponse reply format
        reply_template = "<edxgrade><awarddetail>%s</awarddetail><message><![CDATA[%s]]></message><awarded></awarded></edxgrade>"
        reply = reply_template % (award, message)
        '''

        # "External grader" reply format, following discussion with Berkeley and Harvard
        reply = {'correct': award == 'EXACT_ANS',
                  'score': -1,  # TODO: Partial grading
                  'msg': message}

        return json.dumps(reply)

    elif cmd == 'get_answers':
        expected, message = pyxserver.run_code_sandbox(processor, "", tests, getans=True)

        reply_template = "<edxgrade><message><![CDATA[%s]]></message><expected><![CDATA[%s]]></expected></edxgrade>"
        reply = reply_template % (message, json.dumps([expected]))

    return reply


# Entry point
def application(env, start_response):
    logging.basicConfig()

    # Handle request
    method = env['REQUEST_METHOD']
    data = env['wsgi.input'].read()

    print '-' * 60
    print method

    handlers = {'GET': do_GET,
                 'POST': do_POST,
                 }
    if method in handlers.keys():
        reply = handlers[method](data)
        print ' [*] reply:\n%s\n' % reply
        start_response('200 OK', [('Content-Type', 'text/html')])
        return reply
    else:
        start_response('404 Not Found', [('Content-Type', 'text/plain')])
        return ''
