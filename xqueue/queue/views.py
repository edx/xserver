from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
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

# Log in
#--------------------------------------------------
@csrf_exempt
def log_in(request):
    if request.method == 'POST':
        p = request.POST.dict()
        if p.has_key('username') and p.has_key('password'):
            user = authenticate(username=p['username'], password=p['password'])
            if user is not None:
                login(request, user)
                return HttpResponse(_compose_reply(success=True,
                                               content='Logged in'))
            else:
                return HttpResponse(_compose_reply(success=False,
                                               content='Incorrect login credentials'))
        else:
            return HttpResponse(_compose_reply(success=False,
                                               content='Insufficient login info'))
    else:
        return HttpResponse(_compose_reply(success=False,
                                           content='Log in with HTTP POST'))

# Status check
#--------------------------------------------------
def status(request):
    return HttpResponse(_compose_reply(success=True, content='OK'))

# Xqueue submission from LMS
#--------------------------------------------------
@csrf_exempt
@login_required
def submit(request):
    if request.method == 'POST':
        print request.FILES.keys()
        for filename in request.FILES.keys():
            uploaded_file = request.FILES.get(filename)
            print '-'*60
            print uploaded_file.name
            print uploaded_file.read()

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

# External polling interface
#    1) get_queuelen
#    2) get_submission
#    3) put_result
#--------------------------------------------------

@login_required
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
            return HttpResponse(_compose_reply(success=False, 
                                               content='Valid queue names are: '+' '.join(queue_common.QUEUES)))
    
    return HttpResponse(_compose_reply(success=False,
                                       content="'get_queuelen' must provide parameter 'queue_name'"))

@login_required
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
                                 requester=requester,
                                 qitem=qitem) # qitem is serialized
                pjob.save()

                # Deliver sanitized qitem to the requester.
                #    Remove header originating from the LMS
                #    Replace with header relevant for xqueue callback
                qitem = json.loads(qitem) # De-serialize qitem
                qitem.pop(queue_common.HEADER_TAG)
                header = { 'pjob_id' : pjob.id,
                           'pjob_key': pjob_key, } 
                qitem.update({queue_common.HEADER_TAG: json.dumps(header)})
                channel.basic_ack(method.delivery_tag)
                return HttpResponse(_compose_reply(success=True,
                                                   content=json.dumps(qitem)))

            connection.close()

    return HttpResponse(_compose_reply(success=False,
                                       content="'get_submission' must provide parameter 'queue_name'"))

@csrf_exempt
@login_required
def put_result(request):
    '''
        Graders post their results here.
    '''
    if request.method == 'POST':
        p = request.POST.dict()
        ext_header = json.loads(p[queue_common.HEADER_TAG])

        # Extract from the record of pulled jobs
        try:
            pjob_id = ext_header['pjob_id']
            pjob = PulledJob.objects.get(id=pjob_id)
        except PulledJob.DoesNotExist:
            return HttpResponse(_compose_reply(success=False,
                                               content='Pulled job does not exist in Xqueue records'))
        
        if pjob.pjob_key != ext_header['pjob_key']:
            return HttpResponse(_compose_reply(success=False,
                                               content='Pulled job key does not match database'))

        qitem = pjob.qitem # Original queued item
        qitem = json.loads(qitem)
        lms_header = json.loads(qitem[queue_common.HEADER_TAG])
        queue_consumer.post_to_lms(lms_header, p[queue_common.BODY_TAG])

        return HttpResponse(_compose_reply(success=True, content=''))
    else:
        return HttpResponse(_compose_reply(success=False,
                                           content="'put_result' must use HTTP POST"))
