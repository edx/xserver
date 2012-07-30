from django.http import HttpResponse 
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from queue.models import PulledJob

import hashlib
import json
import pika

import queue_common
import queue_producer 
import queue_consumer

# Xqueue reply format:
#    JSON-serialized dict:
#    { 'return_code': 0(success)/1(error),
#      'content'    : 'my content', }
#--------------------------------------------------
def _compose_reply(success, content):
    return_code = 0 if success else 1
    return json.dumps({ 'return_code': return_code,
                        'content': content })

# Xqueue submission from LMS
#--------------------------------------------------
@csrf_exempt
def submit(request):
    if request.method == 'POST':
        p = request.POST.dict()
        if queue_producer.is_valid_request(p):
            # Which queue do we send to? 
            # Does this xserver instance manage this queue?
            queue_name = queue_producer.get_queue_name(p)
            if queue_name in queue_common.QUEUES:
                queue_producer.push_to_queue(queue_name, p)
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

# External polling interface
#    1) get_queuelen
#    2) get_submission
#    3) put_result
#--------------------------------------------------
def get_queuelen(request):
    '''
        Retrieves the length of queue named by GET['queue_name'].
        If queue_name is invalid or null, returns list of all queue names
    '''
    g = request.GET.copy()
    if 'queue_name' in g:
        queue_name = str(g['queue_name'])
        if queue_name in queue_common.QUEUES:
            job_count = queue_producer.push_to_queue(queue_name)
            return HttpResponse(_compose_reply(success=True, content=job_count))
        else:    
            # Queue name incorrect: List all queues
            return HttpResponse(_compose_reply(success=False, content=' '.join(queue_common.QUEUES)))
    
    return HttpResponse(_compose_reply(success=False,
                                       content="Must provide parameter 'queue_name'"))

def get_submission(request):
    '''
        Retrieves a student submission from queue named by GET['queue_name'].
        The submission is pulled out from the queue, but is tracked in a separate 
            database in xqueue
    '''
    g = request.GET.copy()
    if 'queue_name' in g:
        queue_name = str(g['queue_name'])
        if queue_name not in queue_common.QUEUES:
            return HttpResponse(_compose_reply(success=False,
                                               content="Queue '%s' not found" % queue_name))
        else:
            # Pull a single submission (if one exists) from the named queue
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=queue_common.RABBIT_HOST))
            channel = connection.channel()
            channel.queue_declare(queue=queue_name, durable=True)

            # 'qitem' is the queued item. We expect it to be the serialized
            #   form of the following dict:
            #   { 'xqueue_header': serialized_xqueue_header,
            #     'xqueue_body'  : serialized_xqueue_body, }
            method, header, qitem = channel.basic_get(queue=queue_name)

            if method.NAME == 'Basic.GetEmpty': # Got nothing
                return HttpResponse(_compose_reply(success=False,
                                                   content="Queue '%s' is empty" % queue_name))
            else:
                # Info on pull requester
                requester = request.META['REMOTE_ADDR']
                pulltime = timezone.now()
                print 'Pull request from %s at %s' % (requester, str(pulltime))

                # Track the pull request in our database
                h = hashlib.md5()
                h.update(str(pulltime))
                h.update(qitem)
                pjob_key = h.hexdigest()
                pjob = PulledJob(pjob_key=pjob_key,
                                 pulltime=pulltime,
                                 worker=requester,
                                 submission=qitem)
                pjob.save()

                # Deliver sanitized qitem to the requester.
                #    Remove header originating from the LMS
                #    Replace with header relevant for xqueue callback
                qitem = json.loads(qitem)
                qitem.pop(queue_common.HEADER_TAG)
                header = { 'pjob_id' : pjob.id,
                           'pjob_key': pjob_key, } 
                qitem.update({queue_common.HEADER_TAG: json.dumps(header)})
                channel.basic_ack(method.delivery_tag)
                return HttpResponse(_compose_reply(success=True,
                                                   content=json.dumps(qitem)))

            connection.close()

    return HttpResponse(_compose_reply(success=False,
                                       content="Must provide parameter 'queue_name'"))

@csrf_exempt
def put_result(request):
    '''
        Graders post their results here.
    '''
    if request.method == 'POST':
        p = request.POST.dict()
        header = json.loads(p.pop(queue_common.HEADER_TAG))

        # Extract from the record of pulled jobs
        try:
            pjob_id = header['pjob_id']
            pjob = PulledJob.objects.get(id=pjob_id)
        except PulledJob.DoesNotExist:
            return HttpResponse(_compose_reply(success=False,
                                               content='Pulled job does not exist in Xqueue records'))

        print pjob
        return HttpResponse(_compose_reply(success=True, content=''))
    else:
        return HttpResponse(_compose_reply(success=False,
                                           content='Queue requests should use HTTP POST'))
