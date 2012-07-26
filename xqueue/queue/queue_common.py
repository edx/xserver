SERVER_NAME = 'Xqueue1'
SERVER_DESC = 'Xqueue for 6.00x pyxserver'

HEADER_TAG = 'xqueue_header'

RABBIT_HOST = 'localhost'
QUEUES = ['mitx-600x', 'mitx-6189x', 'python']

NUM_WORKERS = 2
WORKER_URLS = ['http://ec2-50-16-103-147.compute-1.amazonaws.com']*NUM_WORKERS
