from django import forms

from Backend.Apps.AtgDocs.models import KnowledgeDocument, KnowledgePermission


class KnowledgeDocumentForm(forms.ModelForm):
    class Meta:
        model = KnowledgeDocument
        fields = ["title", "slug", "document_type", "status", "body", "owner", "department", "visibility", "metadata"]


class KnowledgePermissionForm(forms.ModelForm):
    class Meta:
        model = KnowledgePermission
        fields = ["document", "subject_type", "subject_id", "permission"]
