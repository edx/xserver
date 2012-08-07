from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse 
from django.views.decorators.csrf import csrf_exempt

from boto.s3.connection import S3Connection
from boto.s3.key import Key
import json

from queue.views import compose_reply, make_hashkey
import queue_common
import queue_producer 

# Xqueue submission from LMS
#--------------------------------------------------
@csrf_exempt
@login_required
def submit(request):
    if request.method == 'POST':
        submission = request.POST.dict()
        (is_valid_request, lms_header) = _is_valid_request(submission)
        if is_valid_request:                           # Check headers are correct
            queue_name = str(lms_header['queue_name']) # Important: queue_name must be str, not unicode!
            if queue_name in queue_common.QUEUES:      # Check that requested queue exists
                # Check for file uploads
                files = dict()
                for filename in request.FILES.keys():
                    s3_keyname = make_hashkey(filename) # TODO: Need salt
                    s3_url = _upload_to_s3(request.FILES[filename],s3_keyname)
                    files.update({ filename: s3_url }) 

                # Attach the uploaded file URLs to submission
                footer = {'files': files}
                submission.update({queue_common.FOOTER_TAG: footer})

                # Serialize the queue request
                qitem = json.dumps(submission)

                # TODO: Track the request in the Submission database

                qcount = queue_producer.push_to_queue(queue_name, qitem)
                
                # For a successful submission, return the count of prior items
                return HttpResponse(compose_reply(success=True,
                                                  content="%d" % qcount))
            else:
                return HttpResponse(compose_reply(success=False,
                                                  content="Queue '%s' not found" % queue_name))
        
        return HttpResponse(compose_reply(success=False,
                                          content='Queue request has invalid format'))
    else:
        return HttpResponse(compose_reply(success=False,
                                          content='Queue requests should use HTTP POST'))

def _is_valid_request(submission):
    '''
    A valid xqueue request must contain correct metadata 
        associated with the key HEADER_TAG
    '''
    try:
        header = json.loads(submission[queue_common.HEADER_TAG])
    except ValueError, err:
        return (False, None)

    is_valid = True
    for tag in ['lms_callback_url', 'lms_key', 'queue_name']:
        if not header.has_key(tag):
            is_valid = False
    return (is_valid, header)
    
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
