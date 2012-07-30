from django.db import models

class PulledJob(models.Model):
	pjob_key = models.CharField(max_length=256)
	pulltime = models.DateTimeField()
	requester = models.CharField(max_length=256)
	qitem = models.CharField(max_length=2**16)

	def __unicode__(self):
		return 'Job pulled by %s at %s' % (self.worker, str(self.pulltime))
