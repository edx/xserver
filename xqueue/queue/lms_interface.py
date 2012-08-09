from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse 
from django.views.decorators.csrf import csrf_exempt

from boto.s3.connection import S3Connection
from boto.s3.key import Key
import json

from queue.models import Submission
from queue.views import compose_reply
from util import *

import queue_common
import queue_producer 

@csrf_exempt
@login_required
def submit(request):
    '''
    Handle submissions to Xqueue from the LMS
    '''
    if request.method != 'POST':
        return HttpResponse(compose_reply(False, 'Queue requests should use HTTP POST'))
    else:
        # queue_name, xqueue_header, xqueue_body are all serialized
        (request_is_valid, queue_name, xqueue_header, xqueue_body) = _is_valid_request(request.POST)

        if not request_is_valid: 
            return HttpResponse(compose_reply(False, 'Queue request has invalid format'))
        else:
            if queue_name not in queue_common.QUEUES:
                return HttpResponse(compose_reply(False, "Queue '%s' not found" % queue_name))
            else:
                # Check for file uploads
                s3_keys = dict() # For internal Xqueue use
                s3_urls = dict() # For external grader use
                for filename in request.FILES.keys():
                    s3_key = make_hashkey(xqueue_header+filename)
                    s3_url = _upload_to_s3(request.FILES[filename],s3_key) # TODO: Sanity check on file (e.g. size)
                    s3_keys.update({filename: s3_key})
                    s3_urls.update({filename: s3_url})

                # Track the submission in the Submission database
                submission = Submission(requester_id=get_request_ip(request),    
                                        queue_name=queue_name,
                                        xqueue_header=xqueue_header,
                                        xqueue_body=xqueue_body,
                                        s3_urls=json.dumps(s3_urls),
                                        s3_keys=json.dumps(s3_keys))
                submission.save()

                qitem  = str(submission.id) # Submit the Submission pointer to queue
                qcount = queue_producer.push_to_queue(queue_name, qitem)
                
                # For a successful submission, return the count of prior items
                return HttpResponse(compose_reply(success=True, content="%d" % qcount))
        

def _is_valid_request(xrequest):
    '''
    Check if xrequest is a valid request for Xqueue. Checks:
        1) Presence of 'xqueue_header' and 'xqueue_body'
        2) Presence of specific metadata in 'xqueue_header'
            ['lms_callback_url', 'lms_key', 'queue_name']

    Returns:
        is_valid:   Flag indicating success (Boolean)
        queue_name: Name of intended queue (string)
        header:     Header portion of xrequest (string)
        body:       Body portion of xrequest (string)
    '''
    fail = (False, '', '', '')
    try:
        header = xrequest['xqueue_header']
        body   = xrequest['xqueue_body']
    except (TypeError, KeyError):
        return fail

    try:
        header_dict = json.loads(header)
    except (TypeError, ValueError):
        return fail

    if not isinstance(header_dict, dict):
        return fail

    for tag in ['lms_callback_url', 'lms_key', 'queue_name']:
        if not header_dict.has_key(tag):
            return fail

    queue_name = str(header_dict['queue_name']) # Important: Queue name must be str!
    return (True, queue_name, header, body)
    

def _upload_to_s3(file_to_upload, s3_keyname):
    '''
    Upload file to S3 using provided keyname.

    Returns:
        public_url: URL to access uploaded file 
    '''
    conn = S3Connection(settings.AWS_ACCESS_KEY, settings.AWS_SECRET_KEY)
    bucketname = settings.AWS_ACCESS_KEY+'bucket' # TODO: Bucket name(s)
    bucket = conn.create_bucket(bucketname.lower())

    k = Key(bucket)
    k.key = s3_keyname
    k.set_metadata('filename',file_to_upload.name)
    k.set_contents_from_file(file_to_upload)
    public_url = k.generate_url(60*60*24) # Timeout in seconds. TODO: Make permanent (until explicit cleanup)
    
    return public_url
