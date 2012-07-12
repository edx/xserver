from django.http import HttpResponse, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
import json
import pika

def send_to_queue(msg):
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	channel.queue_declare(queue='xqueue')
	channel.basic_publish(exchange='',routing_key='xqueue',body=msg)
	print " [x] send_to_queue done"
	connection.close()

@csrf_exempt
def submit(request):
	if request.method == "POST":
		print '-'*60
		p = request.POST.copy()
		if p.has_key('smod_id'):
			smod_id = json.loads(p['smod_id'])
			print "smod_id:"
			print smod_id
		if p.has_key('edX_cmd'):
			print "edX_cmd: %s" % p['edX_cmd']
		if p.has_key('edX_tests'):
			print "edX_tests: %s" % p['edX_tests']
		if p.has_key('edX_student_response'):
			print "edX_student_response: %s" % p['edX_student_response']
		send_to_queue(json.dumps(p))
		return HttpResponse("xqueue")
	else:
		return HttpResponseServerError("xqueue")
