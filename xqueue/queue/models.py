from django.db import models

import json

CHARFIELD_LEN_SMALL = 128
CHARFIELD_LEN_LARGE = 1024

class Submission(models.Model):
    '''
    Representation of submission request, including metadata information
    '''
    
    # Submission 
    requester_id  = models.CharField(max_length=CHARFIELD_LEN_SMALL) # ID of LMS
    queue_name    = models.CharField(max_length=CHARFIELD_LEN_SMALL)
    xqueue_header = models.CharField(max_length=CHARFIELD_LEN_LARGE)
    xqueue_body   = models.TextField()

    # Uploaded files
    s3_keys = models.CharField(max_length=CHARFIELD_LEN_LARGE) # S3 keys for internal Xqueue use
    s3_urls = models.CharField(max_length=CHARFIELD_LEN_LARGE) # S3 urls for external access

    # Timing
    arrival_time = models.DateTimeField(auto_now=True)         # Time of arrival from LMS
    pull_time    = models.DateTimeField(null=True, blank=True) # Time of pull request, if pulled from external grader
    push_time    = models.DateTimeField(null=True, blank=True) # Time of push, if xqueue pushed to external grader
    return_time  = models.DateTimeField(null=True, blank=True) # Time of return from external grader

    # External pull interface
    grader_id = models.CharField(max_length=CHARFIELD_LEN_SMALL) # ID of external grader
    pullkey   = models.CharField(max_length=CHARFIELD_LEN_SMALL) # Secret key for external pulling interface
    grader_reply = models.TextField()                            # Reply from external grader

    # Status
    num_failures = models.IntegerField(default=0) # Number of failures in exchange with external grader
    lms_ack = models.BooleanField(default=False)  # True/False on whether LMS acknowledged receipt

    def __unicode__(self):
        submission_info  = "Submission from %s for queue '%s':\n" % (self.requester_id, self.queue_name)
        submission_info += "    Arrival time: %s\n" % self.arrival_time
        submission_info += "    Pull time:    %s\n" % self.pull_time
        submission_info += "    Push time:    %s\n" % self.push_time
        submission_info += "    Return time:  %s\n" % self.return_time
        submission_info += "    Grader_id:    %s\n" % self.grader_id
        submission_info += "    Pullkey:      %s\n" % self.pullkey
        submission_info += "    num_failures: %d\n" % self.num_failures
        submission_info += "    lms_ack:      %s\n" % self.lms_ack
        submission_info += "Original Xqueue header follows:\n"
        submission_info += json.dumps(json.loads(self.xqueue_header), indent=4)
        return submission_info
