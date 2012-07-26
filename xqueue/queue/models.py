from django.db import models

class PulledJobs(models.Model):
	digest = models.IntegerField()
	pulltime = models.DateTimeField()
	submission = models.CharField(max_length=2**16)
