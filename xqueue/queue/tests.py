"""
Run with 'python manage.py test queue'
"""
import json
import unittest
import lms_interface

class lms_interface_test(unittest.TestCase):

    def test_is_valid_request(self):
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

        bad_requests = [bad_request1, bad_request2, bad_request3, bad_request4]
        for bad_request in bad_requests:
            (is_valid,_,_,_) = lms_interface._is_valid_request(bad_request)
            self.assertEqual(is_valid, False)
