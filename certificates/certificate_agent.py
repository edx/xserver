from argparse import ArgumentParser, RawTextHelpFormatter
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError, Timeout
from collections import namedtuple
import logging
import json
import sys
import time

CERTINFO = ['url', 'org', 'name', 'grade', 'course', 'invalidate']
SLEEP_TIME = 5


def parse_args(args=sys.argv[1:]):
    parser = ArgumentParser(description="""

    Generate edX certificates
    -------------------------

    """, formatter_class=RawTextHelpFormatter)

    parser.add_argument('--auth', help='auth json file',
            default='auth.json')
    parser.add_argument('--env', help='env json file',
            default='env.json')

    return parser.parse_args()


class QueueManager(object):

    def __init__(self, settings):
        self.url = settings['QUEUE_URL']
        self.queue_name = settings['QUEUE_NAME']
        self.auth_user = settings['QUEUE_AUTH_USER']
        self.auth_pass = settings['QUEUE_AUTH_PASS']
        self.queue_user = settings['QUEUE_USER']
        self.queue_pass = settings['QUEUE_PASS']

    def login(self):
        try:
            self.session = requests.session(auth=HTTPBasicAuth(
                self.auth_user, self.auth_pass))
            request = self.session.post('{0}/xqueue/login/'.format(self.url),
                    data={
                        'username': self.queue_user,
                        'password': self.queue_pass
                        })
            response = json.loads(request.text)
            if response['return_code'] != 0:
                raise Exception("Invalid return code in reply resp:{0}".format(
                    str(response)))
            return True
        except (Exception, ConnectionError, Timeout) as e:
            logging.warning("Unable to connect to queue: {0}".format(e))

    def get_length(self):
        try:
            request = self.session.get('{0}/xqueue/get_queuelen/'.format(
                self.url), params={'queue_name': self.queue_name})
            response = json.loads(request.text)
            if response['return_code'] != 0:
                raise Exception("Invalid return code in reply")
            length = int(response['content'])
        except (ValueError, Exception, ConnectionError, Timeout) as e:
            logging.critical("Unable to get queue length: {0}".format(e))
            raise

        return length

    def get_submission(self):
        try:
            request = self.session.get('{0}/xqueue/get_submission/',
                    params={'queue_name': self.queue_name})
        except (ConnectionError, Timeout) as e:
            logging.critical("Unable to get submission from queue: {0}")
            raise

        try:
            response = json.loads(request.text)
            if response['return_code'] != 0:
                raise Exception("Invalid return code in reply")

            certinfo = namedtuple('certinfo', ','.join(CERTINFO))
            return certinfo(*[response[field] for field in CERTINFO])

        except (Exception, ValueError, KeyError) as e:
            logging.critical("Unable to parse queue message: {0}".format(e))
            raise

    def __str__(self):
        return self.url


def main():

    logging.basicConfig(format='%(asctime)s: %(message)s',
            level=logging.DEBUG)
    args = parse_args()
    settings = {}

    with open(args.auth) as f:
        settings.update(json.load(f))
    with open(args.env) as f:
        settings.update(json.load(f))

    manager = QueueManager(settings)

    while True:

        if not manager.login():
            logging.critical("Error logging into {0}".format(
                str(manager)))
            continue
        if manager.get_length() == 0:
            logging.debug("{0} has no jobs".format(
                str(manager)))
            continue

        print manager.get_submission()
        time.sleep(SLEEP_TIME)


if __name__ == '__main__':
    main()
