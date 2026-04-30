from django import forms

from Backend.Apps.Banao.models import LeadAccount, LeadContact, LeadNote, LeadTest


class LeadAccountForm(forms.ModelForm):
    class Meta:
        model = LeadAccount
        fields = ["company_name", "source", "stage", "priority", "owner", "estimated_value", "currency", "tags", "metadata"]


class LeadContactForm(forms.ModelForm):
    class Meta:
        model = LeadContact
        fields = ["lead", "name", "email", "phone", "role", "is_primary"]


class LeadNoteForm(forms.ModelForm):
    class Meta:
        model = LeadNote
        fields = ["lead", "author", "title", "body", "metadata"]


class LeadTestForm(forms.ModelForm):
    class Meta:
        model = LeadTest
        fields = ["lead", "title", "status", "score", "due_at", "metadata"]
