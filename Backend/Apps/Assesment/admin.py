from django.contrib import admin

from Backend.Apps.Assesment.models import AssessmentActivity, AssessmentAssignment, AssessmentSubmission, AssessmentTemplate


@admin.register(AssessmentTemplate)
class AssessmentTemplateAdmin(admin.ModelAdmin):
    list_display = ("title", "code", "department", "sequence_number", "assessment_type", "status", "passing_score", "tenant")
    list_filter = ("status", "assessment_type", "department", "tenant")
    search_fields = ("title", "code", "provider_template_id", "external_id")


@admin.register(AssessmentAssignment)
class AssessmentAssignmentAdmin(admin.ModelAdmin):
    list_display = ("assessment", "employee", "status", "note", "is_pass", "percentage", "assigned_at", "due_at", "tenant")
    list_filter = ("status", "note", "is_pass", "tenant")
    search_fields = ("employee__display_name", "employee__employee_code", "assessment__title", "external_user_id")
    readonly_fields = ("assigned_at", "last_synced_at", "created_at", "updated_at")


@admin.register(AssessmentSubmission)
class AssessmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ("assignment", "attempt_number", "percentage", "passed", "status", "submitted_at", "tenant")
    list_filter = ("passed", "status", "tenant")
    search_fields = ("assignment__employee__display_name", "assignment__assessment__title", "provider_attempt_id")


@admin.register(AssessmentActivity)
class AssessmentActivityAdmin(admin.ModelAdmin):
    list_display = ("activity_type", "title", "assignment", "actor", "created_at", "tenant")
    list_filter = ("activity_type", "tenant")
    search_fields = ("title", "message", "assignment__employee__display_name")
