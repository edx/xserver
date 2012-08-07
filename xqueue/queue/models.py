from django.db import models

class PulledJob(models.Model):
	pjob_key = models.CharField(max_length=256)
	pulltime = models.DateTimeField()
	requester = models.CharField(max_length=256)
	qitem = models.TextField()

	def __unicode__(self):
		return 'Job pulled by %s at %s' % (self.worker, str(self.pulltime))

MAX_CHARFIELD_LEN = 1024

class Submission(models.Model):
    '''
    Writeme
    '''
    # Request
    queue_name    = models.CharField(max_length=MAX_CHARFIELD_LEN)
    xqueue_header = models.CharField(max_length=MAX_CHARFIELD_LEN)
    xqueue_body   = models.TextField()
    xqueue_files  = models.CharField(max_length=MAX_CHARFIELD_LEN)

    # Timing
    arrival_time = models.DateTimeField(auto_now=True) # Time of arrival from LMS
    pull_time = models.DateTimeField()    # Time of pull request, if pulled from external grader
    push_time = models.DateTimeField()    # Time of push, if xqueue pushed to external grader
    return_time = models.DateTimeField()  # Time of return from external grader

    # External pull interface
    grader  = models.CharField(max_length=MAX_CHARFIELD_LEN) # ID of external grader
    pullkey = models.CharField(max_length=MAX_CHARFIELD_LEN) # Secret key for external pulling interface

    # Status
    num_failures = models.IntegerField() # Number of failures in exchange with external grader
    lms_ack = models.BooleanField()      # True/False on whether LMS acknowledged receipt
