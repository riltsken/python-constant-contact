from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from python_constantcontact.django_constantcontact.models import BatchJob
from python_constantcontact import cc

class Command(BaseCommand):

	args = 'No args'
	help = "For each entry in the constant contact batch jobs, executes that job. If there are more than 25 jobs, it will execute a batch job, per the terms of use on constant contact."

	def handle(self,*args,**kwargs):
		jobs = BatchJob.objects.filter(completed__isnull=True).order_by('timestamp')
		api = cc.Api(**settings.CONSTANTCONTACT_CREDENTIALS)
		if jobs.count() < 25:
			for j in jobs:
				if 'create' == j.job:
					lists = [str(l) for l in j.lists.values_list("constant_contact_id", flat=True)]
					try:
						api.create_contact(j.email, lists, j.first_name, j.last_name)
						print "Created: contact %s adding to list(s) - %s" % (j.email, ",".join(lists))
					except cc.HTTPConflict:
						api.add_contact_to_lists_by_email(j.email, lists)
						print "Creation failed: Contact %s exists, updating contacts lists (%s)" % (j.email, ",".join(lists))
				elif 'remove' == j.job:
					api.remove_contact_by_email(j.email)
					print "Removed: %s from all lists" % j.email

				j.completed = True
				j.save()				

			
