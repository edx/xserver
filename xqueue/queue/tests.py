"""
Run me with: 
    python manage.py test --settings=xqueue.test_settings queue
"""
import json
import unittest

from django.contrib.auth.models import User
from django.test.client import Client

import ext_interface
import lms_interface

def parse_xreply(xreply):
    xreply = json.loads(xreply)
    return (xreply['return_code'], xreply['content'])

class lms_interface_test(unittest.TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='LMS',password='CambridgeMA')

    def tearDown(self):
        self.user.delete()

    def test_log_in(self):
        '''
        Test Xqueue login behavior. Particularly important is the response for GET (e.g. by redirect)
        '''
        c = Client()
        login_url = '/xqueue/login/'
        
        # 0) Attempt login with GET, must fail with message='login_required'
        #    The specific message is important, as it is used as a flag by LMS to reauthenticate!
        response = c.get(login_url)
        (error, msg) = parse_xreply(response.content)
        self.assertEqual(error, True)
        self.assertEqual(msg, 'login_required')

        # 1) Attempt login with POST, but no auth 
        response = c.post(login_url)
        (error,_) = parse_xreply(response.content)
        self.assertEqual(error, True)

        # 2) Attempt login with POST, incorrect auth
        response = c.post(login_url,{'username':'LMS','password':'PaloAltoCA'})
        (error,_) = parse_xreply(response.content)
        self.assertEqual(error, True)

        # 3) Login correctly
        response = c.post(login_url,{'username':'LMS','password':'CambridgeMA'})
        (error,_) = parse_xreply(response.content)
        self.assertEqual(error, False)

    def test_is_valid_request(self):
        '''
        Test Xqueue's ability to evaluate valid request format from LMS
            and its ability to gracefully reject
        '''
        # 0) This is a valid Xqueue request from LMS
        good_request = {'xqueue_header': json.dumps({'lms_callback_url':'/',
                                                     'lms_key':'qwerty',
                                                     'queue_name':'python'}),
                        'xqueue_body': 'def square(x):\n    return n**2'}
        (is_valid,_,_,_) = lms_interface._is_valid_request(good_request)
        self.assertEqual(is_valid, True)

        # 1) Header is missing
        bad_request1 = {'xqueue_body': 'def square(x):\n    return n**2'}
        # 2) Body is missing
        bad_request2 = {'xqueue_header': json.dumps({'lms_callback_url':'/',
                                                     'lms_key':'qwerty',
                                                     'queue_name':'python'})}
        # 3) Header not serialized
        bad_request3 = {'xqueue_header': {'lms_callback_url':'/',
                                          'lms_key':'qwerty',
                                          'queue_name':'python'},
                        'xqueue_body': 'def square(x):\n    return n**2'}
        # 4) 'lms_key' is missing in header
        bad_request4 = {'xqueue_header': json.dumps({'lms_callback_url':'/',
                                                     'queue_name':'python'}),
                        'xqueue_body': 'def square(x):\n    return n**2'}
        # 5) Header is not a dict
        bad_request5 = {'xqueue_header': json.dumps(['MIT', 'Harvard', 'Berkeley']),
                        'xqueue_body': 'def square(x):\n    return n**2'}
        # 6) Arbitrary payload
        bad_request6 = 'The capital of Mongolia is Ulaanbaatar'

        bad_requests = [bad_request1, bad_request2, bad_request3, bad_request4, bad_request5, bad_request6]
        for bad_request in bad_requests:
            (is_valid,_,_,_) = lms_interface._is_valid_request(bad_request)
            self.assertEqual(is_valid, False)


class ext_interface_test(unittest.TestCase):

    def setUp(self):
        pass
        
    def tearDown(self):
        pass

    def test_put_result(self):
        pass

    def test_is_valid_reply(self):
        pass
        
