#!/usr/bin/env python
import json
import pika
import requests
import sys
import threading 

import queue_common

WORKER_URLS = ['http://ec2-50-16-103-147.compute-1.amazonaws.com']*2

def post_to_lms(header, body):
    # NOTE: hard-coded to my LMS sandbox
    dispatch = 'score_update'
    return_url = 'http://18.189.69.130:8000' + header['return_url'] + dispatch
    payload = { queue_common.HEADER_TAG: json.dumps(header),
                queue_common.BODY_TAG  : body,
              }
    r = requests.post(return_url, data=payload)
    return r.text

# Encapsulation of a single RabbitMQ connection and
#    channel per thread
#------------------------------------------------------------
class SingleChannel(threading.Thread):
    def __init__(self, workerID, workerURL, queue_name):
        threading.Thread.__init__(self)
        self.workerID = workerID
        self.workerURL = workerURL
        self.queue_name = queue_name

    def run(self):
        print " [%d] Starting thread for queue '%s' using %s" % (self.workerID, self.queue_name, self.workerURL)
        connection = pika.BlockingConnection(
                        pika.ConnectionParameters(host=queue_common.RABBIT_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=self.queue_name, durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(self._callback,
                              queue=self.queue_name)
        channel.start_consuming()
        
    def _callback(self, ch, method, properties, qitem):
        print ' [%d] Got work from %s, dispatched to %s' %\
            ( self.workerID, self.queue_name, self.workerURL )
        qitem = json.loads(qitem)
        header = json.loads(qitem.pop(queue_common.HEADER_TAG))
        body = qitem.pop(queue_common.BODY_TAG) # Serialized data

        # Send task to external server synchronously
        try:
            r = requests.post(self.workerURL, data=body)
        except Exception as err:
            msg = 'Error %s - cannot connect to worker at %s' % (err, self.workerURL)
            raise Exception(msg)

        # TODO: Decide if the response from the worker node is satisfactory.
        #    If yes, send back to the LMS
        grader_reply = r.text
        post_to_lms(header, grader_reply)
        print ' [%d] Job done.' % self.workerID

        # Send job completion acknowledgement to queue 
        ch.basic_ack(delivery_tag = method.delivery_tag)

def main():
    if (len(sys.argv) > 1):
        queue_name = sys.argv[1]
        if queue_name not in queue_common.QUEUES:
            print " [!] ERROR: Queue name '%s' not in list of queues" % queue_name
            return
    else:
        queue_name = queue_common.QUEUES[0]

    print ' [*] Starting queue consumers...'

    num_workers = len(WORKER_URLS)
    channels = [None]*num_workers
    for wid in range(num_workers):
        channels[wid] = SingleChannel(wid, WORKER_URLS[wid], queue_name)
        channels[wid].start()
        
    if num_workers > 0:
        channels[0].join() # Wait forever. TODO: Trap Ctrl+C
    else:
        print ' [*] No workers. Exit'

if __name__ == '__main__':
    main()
