import pika
import json
import queue_common

def push_to_queue(queue_name, qitem=None):
    '''
    Publishes qitem (serialized data) to a specified queue.
    Returns the number of outstanding messages in specified queue
    '''
    queue_name = str(queue_name) # Important: queue_name cannot be unicode!

    if queue_name == 'null':
        return 0

    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=queue_common.RABBIT_HOST))
    channel = connection.channel()
    q = channel.queue_declare(queue=queue_name, durable=True)
    if qitem is not None:
        channel.basic_publish(exchange='',
            routing_key=queue_name,
            body=qitem,
            properties=pika.BasicProperties(delivery_mode=2),
            )
    connection.close()
    return q.method.message_count

