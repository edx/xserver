#!/usr/bin/python
#------------------------------------------------------------
# Run me with (may need su privilege for logging):
#        gunicorn -w 4 -b 127.0.0.1:3031 pyxserver_wsgi:application
#  (remove the -w 4 for debugging--don't want 4 workers)
# gunicorn --preload -b 127.0.0.1:3031 --timeout=35 --pythonpath=. pyxserver_wsgi:application
#------------------------------------------------------------

import cgi    # for the escape() function
import json
import logging
import os
import os.path
from statsd import statsd
import sys
from time import localtime, strftime, time

import settings    # Not django, but do something similar

from sandbox import sandbox

# make sure we can find the grader files
sys.path.append(settings.GRADER_ROOT)
import grade

logging.config.dictConfig(settings.LOGGING)

log = logging.getLogger("xserver." + __name__)


results_template = u"""
<div class="test">
<header>Test results</header>
  <section>
    <div class="shortform">
    {status}
    </div>
    <div class="longform">
      {errors}
      {results}
    </div>
  </section>
</div>
"""


results_correct_template = u"""
  <div class="result-output result-correct">
    <h4>{short-description}</h4>
    <p>{long-description}</p>
    <dl>
    <dt>Output:</dt>
    <dd class="result-actual-output">
       <pre>{actual-output}</pre>
       </dd>
    </dl>
  </div>
"""


results_incorrect_template = u"""
  <div class="result-output result-incorrect">
    <h4>{short-description}</h4>
    <p>{long-description}</p>
    <dl>
    <dt>Your output:</dt>
    <dd class="result-actual-output"><pre>{actual-output}</pre></dd>
    <dt>Correct output:</dt>
    <dd><pre>{expected-output}</pre></dd>
    </dl>
  </div>
"""


def format_errors(errors):
    esc = cgi.escape
    error_string = ''
    error_list = [esc(e) for e in errors or []]
    if error_list:
        items = u'\n'.join([u'<li><pre>{0}</pre></li>\n'.format(e) for e in error_list])
        error_string = u'<ul>\n{0}</ul>\n'.format(items)
        error_string = u'<div class="result-errors">{0}</div>'.format(error_string)
    return error_string


def to_dict(result):
    # long description may or may not be provided.  If not, don't display it.
    # TODO: replace with mako template
    esc = cgi.escape
    if result[1]:
        long_desc = u'<p>{0}</p>'.format(esc(result[1]))
    else:
        long_desc = u''
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
            template = results_correct_template
        else:
            template = results_incorrect_template
        output += template.format(**result)

    errors = format_errors(results['errors'])

    status = 'INCORRECT'
    if errors:
        status = 'ERROR'
    elif results['correct']:
        status = 'CORRECT'

    return results_template.format(status=status,
                                   errors=errors,
                                   results=''.join(output))


def do_GET(data):
    return "Hey, the time is %s" % strftime("%a, %d %b %Y %H:%M:%S", localtime())


def do_POST(data):
    statsd.increment('xserver.post-requests')
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
        statsd.increment('xserver.grader_payload_error')

        log.debug("error parsing: '{0}' -- {1}".format(payload, err))
        raise

    log.debug("Processing submission, grader payload: {0}".format(payload))
    relative_grader_path = grader_config['grader']
    grader_path = os.path.join(settings.GRADER_ROOT, relative_grader_path)
    start = time()
    # TODO: Temporary code, to make transition easier: once all deployed versions of 6.00 have code
    # that expects grade() to be passed the grader payload dict, will get rid of the conditional.
    if hasattr(grade, 'TEMPORARY_WANTS_CONFIG'):
        results = grade.grade(grader_path, grader_config, student_response, sandbox)
    else:
        # old version didn't take the config
        results = grade.grade(grader_path, student_response, sandbox)

    statsd.histogram('xserver.grading-time', time() - start)

    # Make valid JSON message
    reply = { 'correct': results['correct'],
              'score': results['score'],
              'msg': render_results(results) }

    statsd.increment('xserver.post-replies (non-exception)')

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
