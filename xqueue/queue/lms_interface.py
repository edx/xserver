from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse 
from django.views.decorators.csrf import csrf_exempt

from boto.s3.connection import S3Connection
from boto.s3.key import Key
import json

from queue.models import Submission
from queue.views import compose_reply, make_hashkey
import queue_common
import queue_producer 

# Xqueue submission from LMS
#--------------------------------------------------
@csrf_exempt
@login_required
def submit(request):
    if request.method != 'POST':
        return HttpResponse(compose_reply(False, 'Queue requests should use HTTP POST'))
    else:
        xrequest = request.POST.copy()
        (request_is_valid, queue_name, xqueue_header, xqueue_body) = _is_valid_request(xrequest)

        if not request_is_valid: 
            return HttpResponse(compose_reply(False, 'Queue request has invalid format'))
        else:
            if queue_name not in queue_common.QUEUES:
                return HttpResponse(compose_reply(False, "Queue '%s' not found" % queue_name))
            else:
                # Check for file uploads
                files = dict()
                for filename in request.FILES.keys():
                    s3_keyname = make_hashkey(filename) # TODO: Need salt
                    s3_url = _upload_to_s3(request.FILES[filename],s3_keyname)
                    files.update({filename: s3_url}) 

                # Attach the uploaded file URLs to submission
                footer = {'files': files}
                submission.update({queue_common.FOOTER_TAG: footer})

                # TODO: Track the submission in the Submission database

                # Serialize the queue request, and push to queue
                qitem = json.dumps(submission)
                qcount = queue_producer.push_to_queue(queue_name, qitem)
                
                # For a successful submission, return the count of prior items
                return HttpResponse(compose_reply(success=True,
                                                  content="%d" % qcount))
        

def _is_valid_request(xrequest):
    '''
    Check if xrequest is a valid request for Xqueue. Checks:
        1) Presence of 'xqueue_header' and 'xqueue_body'
        2) Presence of specific metadata in 'xqueue_header'

    Returns:
        is_valid:   Flag indicating success (Boolean)
        queue_name: Name of intended queue (string)
        header:     Header portion of xrequest (string)
        body:       Body portion of xrequest (string)
    '''
    try:
        header = xrequest['xqueue_header']
        body   = xrequest['xqueue_body']
    except KeyError:
        return (False, '', '', '')

    try:
        header_dict = json.loads(header)
    except ValueError, err:
        return (False, '', '', '')

    for tag in ['lms_callback_url', 'lms_key', 'queue_name']:
        if not header_dict.has_key(tag):
            return (False, '', '', '')

    queue_name = str(header_dict['queue_name']) # Important: Queue name must be str!
    return (True, queue_name, header, body)
    
def _upload_to_s3(file_to_upload, s3_keyname):
    conn = S3Connection(settings.AWS_ACCESS_KEY, settings.AWS_SECRET_KEY)
    bucketname = settings.AWS_ACCESS_KEY+'bucket' # TODO: Bucket name(s)
    bucket = conn.create_bucket(bucketname.lower())

    k = Key(bucket)
    k.key = s3_keyname
    k.set_metadata('filename',file_to_upload.name)
    k.set_contents_from_file(file_to_upload)
    public_url = k.generate_url(60*60*24) # Timeout in seconds. TODO: Make permanent (until explicit cleanup)
    
    return public_url
