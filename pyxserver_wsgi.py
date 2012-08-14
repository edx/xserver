#!/usr/bin/python
#------------------------------------------------------------
# Run me with (may need su privilege for logging):
#        gunicorn -w 4 -b 127.0.0.1:3031 pyxserver_wsgi:application
#------------------------------------------------------------

import json
from lxml import etree
from time import localtime, strftime 

import pyxserver
import logging


def do_GET(data):
    return "Hey, the time is %s" % strftime("%a, %d %b %Y %H:%M:%S", localtime())


def do_POST(data):
    # This server expects jobs to be pushed to it from the queue
    xpackage = json.loads(data)
    body  = xpackage['xqueue_body']
    files = xpackage['xqueue_files'] 

    # Delivery from the lms
    body = json.loads(body) 
    grader_payload = body['grader_payload']
    student_response = body['student_response']

    # Extract pyxserver-specific content from the grader_payload. Note that 
    #   external graders are free to define their payload format.
    grader_payload = etree.fromstring(grader_payload)
    tests = grader_payload.find('tests').text.strip()
    processor = grader_payload.find('processor').text

    award, message = pyxserver.run_code_sandbox(processor, student_response, tests)

    # "External grader" reply format
    correct = award == 'EXACT_ANS'
    points = 1 if correct else 0
    reply = { 'correct': correct,
              'score': points, 
              'msg': message }

    return json.dumps(reply)

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
