from django.contrib import admin

from Backend.Apps.L3.models import CandidateProfile, CollegeAssignment, CollegeContact, CollegeEmailTemplate, CollegePipelineRecord, TalentAssignment, TalentEmail, TalentPerformanceSnapshot


@admin.register(CollegePipelineRecord)
class CollegePipelineRecordAdmin(admin.ModelAdmin):
    list_display = ("college_name", "state", "workflow_status", "owner", "is_archived", "tenant")
    list_filter = ("workflow_status", "state", "is_archived", "tenant")
    search_fields = ("college_name", "contact_email")


@admin.register(CollegeContact)
class CollegeContactAdmin(admin.ModelAdmin):
    list_display = ("name", "college", "role", "email", "is_primary", "tenant")


@admin.register(CollegeAssignment)
class CollegeAssignmentAdmin(admin.ModelAdmin):
    list_display = ("college", "assigned_to", "workflow_status", "follow_up_at", "is_archived", "tenant")
    list_filter = ("workflow_status", "is_archived", "tenant")


@admin.register(CollegeEmailTemplate)
class CollegeEmailTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "subject", "status", "tenant")


admin.site.register(CandidateProfile)
admin.site.register(TalentAssignment)
admin.site.register(TalentEmail)
admin.site.register(TalentPerformanceSnapshot)