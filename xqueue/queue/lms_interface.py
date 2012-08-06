from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse 
from django.views.decorators.csrf import csrf_exempt

from boto.s3.connection import S3Connection
from boto.s3.key import Key
import json

from queue.views import _compose_reply
import queue_common
import queue_producer 

# Xqueue submission from LMS
#--------------------------------------------------
@csrf_exempt
@login_required
def submit(request):
    if request.method == 'POST':
        # Check for file uploads
        for filename in request.FILES.keys():
            _upload_to_s3(request.FILES[filename])

        p = request.POST.dict()
        if queue_producer.is_valid_request(p):
            queue_name = queue_producer.get_queue_name(p)
            if queue_name in queue_common.QUEUES:
                if queue_name != 'null':
                    queue_producer.push_to_queue(queue_name, json.dumps(p))
                return HttpResponse(_compose_reply(success=True,
                                                   content="Job submitted to queue '%s'" % queue_name))
            else:
                return HttpResponse(_compose_reply(success=False,
                                                   content="Queue '%s' not found" % queue_name))
        
        return HttpResponse(_compose_reply(success=False,
                                           content='Queue request has invalid format'))
    else:
        return HttpResponse(_compose_reply(success=False,
                                           content='Queue requests should use HTTP POST'))

def _upload_to_s3(file_to_upload):
    conn = S3Connection(settings.AWS_ACCESS_KEY, settings.AWS_SECRET_KEY)
    bucketname = settings.AWS_ACCESS_KEY+'bucket' # TODO: Bucket name(s)
    bucket = conn.create_bucket(bucketname.lower())

    k = Key(bucket)
    k.key = file_to_upload.name
    k.set_metadata('filename',file_to_upload.name)
    k.set_contents_from_file(file_to_upload)
    public_url = k.generate_url(60*60*24) # Timeout in seconds
    
    print '_upload_to_s3: uploaded %s to\n  %s' % (file_to_upload.name, public_url)
    return public_url
