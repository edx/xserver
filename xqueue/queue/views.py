from django.http import HttpResponse, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from queue.models import PulledJob

import hashlib
import json
import pika

import queue_common
import queue_send

# Xqueue submission from LMS
#--------------------------------------------------
@csrf_exempt
def submit(request):
	if request.method == 'POST':
		p = request.POST.copy()

		if queue_send.is_valid_request(p):
			# Which queue do we send to? 
			# Does this xserver instance manage this queue?
			queue_name = queue_send.get_queue_name(p)
			if queue_name in queue_common.QUEUES:
				queue_send.push_to_queue(queue_name, p)
				return HttpResponse(queue_send.compose_reply('SUBMITTED'))
		
		# Defaults to BADREQUEST
		return HttpResponse(queue_send.compose_reply('BADREQUEST'))
	else:
		return HttpResponseServerError('NOGET')

# External polling interface
#	1) get_queuelen
#	2) get_submission
#	3) put_result
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
			job_count = queue_send.push_to_queue(queue_name)
			return HttpResponse(queue_send.compose_reply('%d' % job_count))
		
	# Default behavior: return names of all queues
	return HttpResponse(queue_send.compose_reply('%s' % ' '.join(queue_common.QUEUES)))

def get_submission(request):
	'''
		Retrieves a student submission from queue named by GET['queue_name'].
		The submission is pulled out from the queue, but is tracked in a separate 
			database in xqueue
	'''
	g = request.GET.copy()
	if 'queue_name' in g:
		queue_name = str(g['queue_name'])
		if queue_name in queue_common.QUEUES:
			# Pull a single submission (if one exists) from the named queue
			connection = pika.BlockingConnection(pika.ConnectionParameters(host=queue_common.RABBIT_HOST))
			channel = connection.channel()
			channel.queue_declare(queue=queue_name, durable=True)
			method, header, submission = channel.basic_get(queue=queue_name)

			if method.NAME == 'Basic.GetEmpty': # Got nothing
				print "Got nothing"
			else:
				# Pull request info
				worker = request.META['REMOTE_ADDR']
				pulltime = timezone.now()
				print 'Pull request from %s at %s' % (worker, str(pulltime))

				# Track the pull request in our database
				h = hashlib.md5()
				h.update(str(pulltime))
				h.update(submission)
				pjob_key = h.hexdigest()
				pjob = PulledJob(pjob_key=pjob_key,
								 pulltime=pulltime,
								 worker=worker,
								 submission=submission)
				pjob.save()

				# Deliver sanitized submission to the worker.
				#	Remove header originating from the LMS
				#	Replace with header relevant for Xqueue callback
				submission = json.loads(submission)
				submission.pop(queue_common.HEADER_TAG)
				header = { 'pjob_id' : pjob.id,
						   'pjob_key': pjob_key, } 
				submission.update({queue_common.HEADER_TAG: header})
				channel.basic_ack(method.delivery_tag)
				#pjob.delete()
				return HttpResponse(json.dumps(submission))

			connection.close()

	# Default return
	return HttpResponse(queue_send.compose_reply('get_submission: I got nothing for you'))

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
			return HttpResponse(queue_send.compose_reply('Job does not exist'))

		print pjob
		return HttpResponse(queue_send.compose_reply('Okay'))
	else:
		return HttpResponse(queue_send.compose_reply('Wrong method'))

