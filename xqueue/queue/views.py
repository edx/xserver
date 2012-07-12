from django.http import HttpResponse, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
import queue_send

# Process incoming xqueue request
#--------------------------------------------------
@csrf_exempt
def submit(request):
	if request.method == "POST":
		p = request.POST.copy()
		if queue_send.is_valid_request(p):
			queue_send.push_to_queue(p)
			return HttpResponse(queue_send.compose_reply('SUBMITTED'))
		else:
			return HttpResponse(queue_send.compose_reply('BADREQUEST'))
	else:
		return HttpResponseServerError('NOGET')

# Get queue stat
#	At the moment, just the number of jobs in queue
#--------------------------------------------------
def get_info(request):
	job_count = queue_send.push_to_queue()
	return HttpResponse(queue_send.compose_reply('%d' % job_count))
