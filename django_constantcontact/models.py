from django.db import models
from datetime import datetime

class GroupList(models.Model):
	constant_contact_id = models.PositiveIntegerField()
	name = models.CharField(max_length=100)

	def __unicode__(self):
		return self.name

class BatchJob(models.Model):
	email = models.CharField(max_length=50)
	first_name = models.CharField(max_length=50,blank=True,null=True)
	last_name = models.CharField(max_length=50,blank=True,null=True)
	lists = models.ManyToManyField(GroupList,blank=True,null=True)
	timestamp = models.DateTimeField(default=datetime.now,editable=False)
	completed = models.NullBooleanField(blank=True) # null means no action, false means error, true means completed
	job = models.CharField(
		choices=[
			('create', 'Create contact'),
			('update', 'Update contact'),
			('remove', 'Remove from lists'),
			('donotmail', 'Do not mail')],
		max_length=10)

	def __unicode__(self):
		return "%s - %s (%s)" % (self.job, self.email, self.timestamp)
	
