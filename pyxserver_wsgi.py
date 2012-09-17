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

def _compose_single_test(test):
    '''
    Generate the return payload for a single external grader test.

    Param 'test' is a dict with keys:
        'title':
        'shortform': Short (~1 sentence) summary of test
        'longform':  Long output that is initially collapsed
    '''
    test_msg = '<div class="test">'
    if 'title' in test:
        test_msg += '<header><h3>'
        test_msg += test['title']
        test_msg += '</h3></header>'

    test_msg += '<section>'
    if 'shortform' in test:
        test_msg += '<div class="shortform">'
        test_msg += test['shortform']
        test_msg += '</div>'

    if 'longform' in test:
        test_msg += '<div class="longform">'
        test_msg += test['longform']
        test_msg += '</div>'

    test_msg += '</section>'
    test_msg += '</div>'
    return test_msg 

def compose_score_msg(tests):
    score_msg = '<div>'
    for test in tests:
        score_msg += _compose_single_test(test)
    score_msg += '</div>'
    return score_msg


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
    message = '<span>' + message + '</span>'
    correct = award == 'EXACT_ANS'
    points = 1 if correct else 0

    # Make valid XML message
    test = { 'title': '6.00x Pyxserver', 
             'shortform': award,
             'longform': message }
    tests = [test]
    score_msg = compose_score_msg(tests)

    reply = { 'correct': correct,
              'score': points, 
              'msg': score_msg }

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
