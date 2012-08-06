from django.db import models

class PulledJob(models.Model):
	pjob_key = models.CharField(max_length=256)
	pulltime = models.DateTimeField()
	requester = models.CharField(max_length=256)
	qitem = models.TextField()

	def __unicode__(self):
		return 'Job pulled by %s at %s' % (self.worker, str(self.pulltime))

class Submission(models.Model):
    qitem = models.TextField()                       # Serialized record of the queued item
    external_url = models.CharField(max_length=1024) # URL to externally-hosted (e.g. S3) file, if any 

    arrival_time = models.DateTimeField() # Time of arrival from LMS
    pull_time = models.DateTimeField()    # Time of pull request, if pulled from external grader
    push_time = models.DateTimeField()    # Time of push, if xqueue pushed to external grader
    return_time = models.DateTimeField()  # Time of return from external grader

    grader  = models.CharField(max_length=1024) # ID of external grader
    pullkey = models.CharField(max_length=1024) # Secret key for external pulling interface

    num_failures = models.IntegerField() # Number of failures in exchange with external grader
    lms_ack = models.BooleanField()      # True/False on whether LMS acknowledged receipt
