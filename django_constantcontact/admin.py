from django.contrib import admin
import models

class BatchJobAdmin(admin.ModelAdmin):
	list_display = ['email', 'timestamp', 'completed', 'job']
	search_fields = ['email']
	list_filter = ['job', 'completed']
	ordering = ['-timestamp']

admin.site.register(models.BatchJob, BatchJobAdmin)
admin.site.register(models.GroupList)
