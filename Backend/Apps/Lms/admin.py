from django.contrib import admin

from Backend.Apps.Lms.models import LeadQueueSnapshot, LearningAssignment, LearningModule, LearningPath, RevenuePerformanceSnapshot


admin.site.register(LearningPath)
admin.site.register(LearningModule)
admin.site.register(LearningAssignment)
admin.site.register(RevenuePerformanceSnapshot)
admin.site.register(LeadQueueSnapshot)