import pika
import json
import queue_common

def is_valid_request(get):
	# A valid xqueue request must contain metadata 
	#	associated with the key HEADER_TAG
	return get.has_key(queue_common.HEADER_TAG)

def push_to_queue(get=None):
	connection = pika.BlockingConnection(pika.ConnectionParameters(
		host=queue_common.RABBIT_HOST))
	channel = connection.channel()
	q = channel.queue_declare(queue=queue_common.RABBIT_QUEUE_NAME)
	if get is not None:
		channel.basic_publish(exchange='',
			routing_key=queue_common.RABBIT_QUEUE_NAME,
			body=json.dumps(get),
			properties=pika.BasicProperties(delivery_mode=2),
			)
	connection.close()
	return q.method.message_count

def compose_reply(reply):
	return '<xqueue><server name="%s" desc="%s"/><msg>%s</msg></xqueue>' %\
				(queue_common.SERVER_NAME, queue_common.SERVER_DESC, reply)
