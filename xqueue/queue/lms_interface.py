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
        p = request.POST.dict()
        if queue_producer.is_valid_request(p):            # Check headers are correct
            queue_name = queue_producer.get_queue_name(p)
            if queue_name in queue_common.QUEUES:         # Check that requested queue exists
                if queue_name != 'null':                  # Check that non-'null' queue
                    # Serialize the queue request
                    qitem = json.dumps(p)

                    # Check for file uploads
                    for filename in request.FILES.keys():
                        s3_keyname = make_hashkey(qitem+filename)
                        _upload_to_s3(request.FILES[filename],s3_keyname)

                    qcount = queue_producer.push_to_queue(queue_name, qitem)

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

def _upload_to_s3(file_to_upload, s3_keyname):
    conn = S3Connection(settings.AWS_ACCESS_KEY, settings.AWS_SECRET_KEY)
    bucketname = settings.AWS_ACCESS_KEY+'bucket' # TODO: Bucket name(s)
    bucket = conn.create_bucket(bucketname.lower())

    k = Key(bucket)
    k.key = s3_keyname
    k.set_metadata('filename',file_to_upload.name)
    k.set_contents_from_file(file_to_upload)
    public_url = k.generate_url(60*60*24) # Timeout in seconds
    
    return public_url
