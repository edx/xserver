#!/usr/bin/env python
import json
import pika
import requests
import sys
import threading 

import queue_common

#------------------------------------------------------------
# Encapsulation of a single RabbitMQ connection and
#	channel per thread
#------------------------------------------------------------
class SingleChannel(threading.Thread):
	def __init__(self, workerID, queue_name):
		threading.Thread.__init__(self)
		self.workerID = workerID
		self.workerURL = queue_common.WORKER_URLS[workerID]
		self.queue_name = queue_name

	def run(self):
		print " [%d] Starting thread for queue '%s' at %s" % (self.workerID, self.queue_name, self.workerURL)
		connection = pika.BlockingConnection(
						pika.ConnectionParameters(host=queue_common.RABBIT_HOST))
		channel = connection.channel()
		channel.queue_declare(queue=self.queue_name, durable=True)
		channel.basic_qos(prefetch_count=1)
		channel.basic_consume(self._callback,
							  queue=self.queue_name)
		channel.start_consuming()
		
	def _callback(self, ch, method, properties, body):
		print ' [%d] Got work from %s, dispatched to %s' %\
			( self.workerID, self.queue_name, self.workerURL )
		work = json.loads(body)
		header = json.loads(work.pop(queue_common.HEADER_TAG))

		# Send task to external server synchronously
		try:
			r = requests.post(self.workerURL, data=work)
		except Exception as err:
			msg = 'Error %s - cannot connect to worker at %s' % (err, self.workerURL)
			raise Exception(msg)

		# TODO: Decide if the response from the worker node is satisfactory.
		#	If yes, send back to the LMS
		self._post_to_lms(header, r.text)

		# Send job acknowledgement to queue 
		ch.basic_ack(delivery_tag = method.delivery_tag)

	def _post_to_lms(self, header, rstr):
		# NOTE: hard-coded to my LMS sandbox
		dispatch = 'score_update'
		return_url = 'http://18.189.69.130:8000' + header['return_url'] + dispatch
		payload = { queue_common.HEADER_TAG: json.dumps(header),
					'response': rstr,
				  }
		requests.post(return_url, data=payload)
		print ' [%d] Job done. Results sent to %s' % (self.workerID, return_url)

def main():
	if (len(sys.argv) > 1):
		queue_name = sys.argv[1]
		if queue_name not in queue_common.QUEUES:
			print " [!] ERROR: Queue name '%s' not in list of queues. See queue_common.py" % queue_name
			return
	else:
		queue_name = queue_common.QUEUES[0]

	print ' [*] Starting handlers for %s (%s). Press CTRL+C to exit' %\
		(queue_common.SERVER_NAME, queue_common.SERVER_DESC)

	num_workers = len(queue_common.WORKER_URLS)
	channels = [None]*num_workers
	for wid in range(num_workers):
		channels[wid] = SingleChannel(wid, queue_name) # TODO: Set which queue to listen to
		channels[wid].start()
		
	if num_workers > 0:
		channels[0].join() # Wait forever. To do: Trap Ctrl+C
	else:
		print ' [*] No workers. Exit'

if __name__ == '__main__':
	main()
