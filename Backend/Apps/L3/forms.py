from django import forms

from Backend.Apps.L3.models import CollegeAssignment, CollegeContact, CollegeEmailTemplate, CollegePipelineRecord


class CollegePipelineRecordForm(forms.ModelForm):
    class Meta:
        model = CollegePipelineRecord
        fields = ["college_name", "city", "state", "category", "contact_email", "contact_phone", "workflow_status", "owner", "follow_up_at", "is_archived", "metadata"]


class CollegeContactForm(forms.ModelForm):
    class Meta:
        model = CollegeContact
        fields = ["college", "name", "role", "email", "phone", "is_primary", "metadata"]


class CollegeAssignmentForm(forms.ModelForm):
    class Meta:
        model = CollegeAssignment
        fields = ["college", "assigned_to", "workflow_status", "follow_up_at", "completed_at", "is_archived", "notes", "metadata"]


class CollegeEmailTemplateForm(forms.ModelForm):
    class Meta:
        model = CollegeEmailTemplate
        fields = ["name", "subject", "body_html", "body_text", "attachment_reference", "status", "metadata"]