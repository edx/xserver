#!/usr/bin/python
#------------------------------------------------------------
# Run me with (may need su privilege for logging):
#        gunicorn -w 4 -b 127.0.0.1:3031 pyxserver_wsgi:application
#------------------------------------------------------------

import json
import logging
import os
import os.path
import sys
from time import localtime, strftime

import settings    # Not django, but do something similar

import sb50.run


# make sure we can find the grader files
sys.path.append(settings.GRADER_ROOT)
import grade

logging.config.dictConfig(settings.LOGGING)

log = logging.getLogger("xserver." + __name__)

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
    student_response = body['student_response']
    # If parsing json fails, erroring is fine--something is wrong in the content.
    payload = body['grader_payload']
    grader_config = json.loads(payload)

    log.debug("Processing submission, grader payload: {0}".format(payload))
    relative_grader_path = grader_config['grader']
    grader_path = os.path.join(settings.GRADER_ROOT, relative_grader_path)
    results = grade.grade(grader_path, student_response, sb50.run)


    # Make valid XML message
    # test = { 'title': '6.00x Grader',
    #          'shortform': award,
    #          'longform': message }

    reply = { 'correct': results['correct'],
              'score': results['score'],
              'msg': '<pre>' + json.dumps(results) + '</pre>' }

    return json.dumps(reply)

# Entry point
def application(env, start_response):

    log.info("Starting application")
    # Handle request
    method = env['REQUEST_METHOD']
    data = env['wsgi.input'].read()

    log.debug('-' * 60)
    log.debug(method)

    def post_wrapper(data):
        try:
            return do_POST(data)
        except:
            log.exception("Error processing request")
            return None

    handlers = {'GET': do_GET,
                 'POST': post_wrapper,
                 }
    if method in handlers.keys():
        reply = handlers[method](data)

        if reply is not None:
            log.debug(' [*] reply:\n%s\n' % reply)

            start_response('200 OK', [('Content-Type', 'text/html')])
            return reply

    # If we fell through to here, complain.
    start_response('404 Not Found', [('Content-Type', 'text/plain')])
    return ''
