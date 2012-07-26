from django.http import HttpResponse, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt

import json
import pika

import queue_common
import queue_send

# Xqueue submission from LMS
#--------------------------------------------------
@csrf_exempt
def submit(request):
	if request.method == "POST":
		p = request.POST.copy()

		if queue_send.is_valid_request(p):
			# Which queue do we send to? Does this xserver instance manage this queue?
			queue_name = queue_send.get_queue_name(p)
			if queue_name in queue_common.QUEUES:
				queue_send.push_to_queue(queue_name, p)
				return HttpResponse(queue_send.compose_reply('SUBMITTED'))
		
		# Defaults to BADREQUEST
		return HttpResponse(queue_send.compose_reply('BADREQUEST'))
	else:
		return HttpResponseServerError('NOGET')

# External polling interface
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
			else: # Do stuff with submission
				print '-'*60
				print type(submission)
				print dir(submission)
				print submission
				channel.basic_ack(method.delivery_tag)

			connection.close()

	
	# Default return
	return HttpResponse(queue_send.compose_reply('get_submission'))

def put_result(request):
	return HttpResponse(queue_send.compose_reply('put_result'))

