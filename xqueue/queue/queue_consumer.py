#!/usr/bin/env python
import json
import os
import pika
import requests
import sys
import threading 

from django.utils import timezone
from os.path import abspath, dirname, join

# DB-based consumer needs access to Django
path = abspath(join(dirname(__file__),'../'))
sys.path.append(path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'xqueue.settings'

import queue_common
from queue.models import Submission

# TODO: Convenient hook for setting WORKER_URLS
NUM_WORKERS = 4
WORKER_URLS = ['http://600xgrader.edx.org']*NUM_WORKERS


def clean_up_submission(submission):
    '''
    TODO: Delete files on S3
    '''
    return

def get_single_qitem(queue_name):
    '''
    Retrieve a single queued item, if one exists, from the named queue

    Returns (success, qitem):
        success: Flag whether retrieval is successful (Boolean)
                 If no items in the queue, then return False
        qitem:   Retrieved item
    '''
    queue_name = str(queue_name)
    
    # Pull a single submission (if one exists) from the named queue
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=queue_common.RABBIT_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)

    # qitem is the item from the queue
    method, header, qitem = channel.basic_get(queue=queue_name)

    if method.NAME == 'Basic.GetEmpty': # Got nothing
        connection.close()
        return (False, '')
    else:
        channel.basic_ack(method.delivery_tag)
        connection.close()
        return (True, qitem)

def post_grade_to_lms(header, body):
    '''
    Send grading results back to LMS
        header:  JSON-serialized xqueue_header (string)
        body:    grader reply (string)

    Returns:
        success: Flag indicating successful exchange (Boolean)
    '''
    header_dict = json.loads(header)
    lms_callback_url = header_dict['lms_callback_url']

    payload = {'xqueue_header': header, 'xqueue_body': body}
    (success,_) = _http_post(lms_callback_url, payload) 

    return success


def _http_post(url, data):
    '''
    Contact external grader server, but fail gently.

    Returns (success, msg), where:
        success: Flag indicating successful exchange (Boolean)
        msg: Accompanying message; Grader reply when successful (string)
    '''
    try:
        r = requests.post(url, data=data)
    except requests.exceptions.ConnectionError:
        return (False, 'cannot connect to server')

    if r.status_code not in [200]:
        return (False, 'unexpected HTTP status code [%d]' % r.status_code)
    return (True, r.text) 


class SingleChannel(threading.Thread):
    '''
    Encapsulation of a single RabbitMQ queue listener
    '''
    def __init__(self, workerID, workerURL, queue_name):
        threading.Thread.__init__(self)
        self.workerID = workerID
        self.workerURL = workerURL
        self.queue_name = str(queue_name) # Important, queue_name must be str, not unicode!

    def run(self):
        print " [%d] Starting consumer for queue '%s' using %s" % (self.workerID, self.queue_name, self.workerURL)
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=queue_common.RABBIT_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=self.queue_name, durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(self.consumer_callback,
                              queue=self.queue_name)
        channel.start_consuming()
        
    def consumer_callback(self, ch, method, properties, qitem):

        submission_id = int(qitem)
        try:
            submission = Submission.objects.get(id=submission_id)
        except Submission.DoesNotExist:
            ch.basic_ack(delivery_tag = method.delivery_tag)
            return # Just move on
        
        # Deliver job to worker
        payload = {'xqueue_body':  submission.xqueue_body,
                   'xqueue_files': submission.s3_urls}

        submission.grader_id = self.workerURL
        submission.push_time = timezone.now()
        (grading_success, grader_reply) = _http_post(self.workerURL, json.dumps(payload))
        submission.return_time = timezone.now()

        if grading_success:
            submission.grader_reply = grader_reply
            submission.lms_ack = post_grade_to_lms(submission.xqueue_header, grader_reply) 
        else:
            submission.num_failures += 1
        
        submission.save()

        # Take item off of queue. 
        # TODO: Logic for resubmission when failed
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
