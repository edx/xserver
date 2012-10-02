#!/usr/bin/python
#------------------------------------------------------------
# Run me with (may need su privilege for logging):
#        gunicorn -w 4 -b 127.0.0.1:3031 pyxserver_wsgi:application
#------------------------------------------------------------

import cgi    # for the escape() function
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

results_template = """
<div class="test">
<header>Test results</header>
  <section>
    <div class="shortform">
    {status}
    </div>
    <div class="longform">
    {results}
    </div>
  </section>
</div>
"""

results_ok_template = """
  <div class="result-output result-correct">
    <h4>{short-description}</h4>
    <p>{long-description}</p>
    <dl>
    <dt>Output:</dt>
    <dd>{actual-output}</dd>
    </dl>
  </div>
"""


results_error_template = """
  <div class="result-output result-incorrect">
    <h4>{short-description}</h4>
    <p>{long-description}</p>
    <dl>
    <dt>Your output:</dt>
    <dd class="result-error">{actual-output}</dd>
    <dt>Our output:</dt>
    <dd>{expected-output}</dd>
    </dl>
  </div>
"""

def to_dict(result):
    # long description may or may not be provided.  If not, don't display it.
    # TODO: replace with mako template
    esc = cgi.escape
    if result[1]:
        long_desc = '<p>{0}</p>'.format(esc(result[1]))
    else:
        long_desc = ''
    return {'short-description': esc(result[0]),
            'long-description': long_desc,
            'correct': result[2],   # Boolean; don't escape.
            'expected-output': esc(result[3]),
            'actual-output': esc(result[4])
            }

def render_results(results):
    output = []
    test_results = [to_dict(r) for r in results['tests']]
    for result in test_results:
        if result['correct']:
            template = results_ok_template
        else:
            template = results_error_template
        output += template.format(**result)

    status = 'CORRECT' if results['correct'] else 'INCORRECT'
    return results_template.format(status=status, results=''.join(output))


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
    payload = body['grader_payload']
    try:
        grader_config = json.loads(payload)
    except ValueError as err:
        # If parsing json fails, erroring is fine--something is wrong in the content.
        # However, for debugging, still want to see what the problem is
        log.debug("error parsing: '{0}' -- {1}".format(payload, err))
        raise

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
              'msg': render_results(results) }

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
            log.exception("Error processing request: {0}".format(data))
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
