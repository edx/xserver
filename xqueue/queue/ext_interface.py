from django.contrib.auth.decorators import login_required
from django.http import HttpResponse 
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

import json
import pika

from queue.models import Submission 
from queue.views import compose_reply, make_hashkey
import queue_common
import queue_producer 
import queue_consumer

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
            return HttpResponse(compose_reply(True, job_count))
        else: # Queue name incorrect: List all queues    
            return HttpResponse(compose_reply(False, 'Valid queue names are: '+' '.join(queue_common.QUEUES)))
    return HttpResponse(compose_reply(False, "'get_queuelen' must provide parameter 'queue_name'"))

@login_required
def get_submission(request):
    '''
    Retrieve a single submission from queue named by GET['queue_name'].
    '''
    g = request.GET.copy()
    if 'queue_name' not in g:
        return HttpResponse(compose_reply(False, "'get_submission' must provide parameter 'queue_name'"))
    else:
        queue_name = str(g['queue_name'])
        if queue_name not in queue_common.QUEUES:
            return HttpResponse(compose_reply(False, "Queue '%s' not found" % queue_name))
        else:
            # Pull a single submission (if one exists) from the named queue
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=queue_common.RABBIT_HOST))
            channel = connection.channel()
            channel.queue_declare(queue=queue_name, durable=True)

            # qitem is the item from the queue
            method, header, qitem = channel.basic_get(queue=queue_name)

            if method.NAME == 'Basic.GetEmpty': # Got nothing
                return HttpResponse(compose_reply(False, "Queue '%s' is empty" % queue_name))
            else:
                submission_id = int(qitem)
                try:
                    submission = Submission.objects.get(id=submission_id)
                except Submission.DoesNotExist:
                    channel.basic_ack(method.delivery_tag)
                    return HttpResponse(compose_reply(False, "Error with queued submission. Please try again"))

                # Collect info on pull event
                grader    = request.META['REMOTE_ADDR']
                pull_time = timezone.now()
                pullkey   = make_hashkey(str(pull_time)+qitem)
                
                submission.grader    = grader
                submission.pull_time = pull_time
                submission.pullkey   = pullkey 
                
                submission.save()

                # Prepare payload to external grader
                ext_header = {'submission_id':submission_id, 'submission_key':pullkey} 
                
                payload = {'xqueue_header': json.dumps(ext_header),
                           'xqueue_body': submission.xqueue_body,
                           'xqueue_files': submission.s3_urls} 

                channel.basic_ack(method.delivery_tag)

                return HttpResponse(compose_reply(True,content=json.dumps(payload)))

            connection.close()


@csrf_exempt
@login_required
def put_result(request):
    '''
    Graders post their results here.
    '''
    if request.method != 'POST':
        return HttpResponse(compose_reply(False, "'put_result' must use HTTP POST"))
    else:
        post = request.POST.copy()
        (reply_is_valid, submission_id, submission_key, grader_reply) = _is_valid_reply(post)

        if not reply_is_valid:
            return HttpResponse(compose_reply(False, 'Incorrect reply format'))
        else:
            try:
                submission = Submission.objects.get(id=submission_id)
            except Submission.DoesNotExist:
                return HttpResponse(compose_reply(False,'Submission does not exist'))

            if submission.pullkey and submission_key != submission.pullkey:
                return HttpResponse(compose_reply(False,'Incorrect key for submission'))
            
            submission.return_time = timezone.now()
            submission.pullkey = '' 

            # Deliver grading results to LMS
            submission.lms_ack = queue_consumer.post_grade_to_lms(submission.xqueue_header, grader_reply)

            print submission
            submission.save()

            return HttpResponse(compose_reply(success=True, content=''))

def _is_valid_reply(external_reply):
    '''
    Check if external reply is in the right format
        1) Presence of 'xqueue_header' and 'xqueue_body'
        2) Presence of specific metadata in 'xqueue_header'
            ['submission_id', 'submission_key']

    Returns:
        is_valid:       Flag indicating success (Boolean)
        submission_id:  Graded submission's database ID in Xqueue (int)
        submission_key: Secret key to match against Xqueue database (string)
        score_msg:      Grading result from external grader (string)
    '''
    fail = (False,-1,'','')
    try:
        header    = external_reply['xqueue_header']
        score_msg = external_reply['xqueue_body']
    except KeyError:
        return fail

    try:
        header_dict = json.loads(header)
    except (TypeError, ValueError):
        return fail

    for tag in ['submission_id', 'submission_key']:
        if not header_dict.has_key(tag):
            return fail

    submission_id  = int(header_dict['submission_id'])
    submission_key = header_dict['submission_key'] 
    return (True, submission_id, submission_key, score_msg) 
