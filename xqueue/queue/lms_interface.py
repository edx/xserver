from django.contrib.auth.decorators import login_required
from django.http import HttpResponse 
from django.views.decorators.csrf import csrf_exempt

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
    print file_to_upload.name

