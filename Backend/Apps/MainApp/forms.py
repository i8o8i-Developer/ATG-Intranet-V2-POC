from django import forms

from Backend.Apps.MainApp.models import CredentialShareGrant, CredentialVaultItem, LeaveRequest, ManagerScope, NotificationItem, OnboardingOffer


class OnboardingOfferForm(forms.ModelForm):
    class Meta:
        model = OnboardingOffer
        fields = ["candidate_name", "candidate_email", "company_name", "position_title", "offer_type", "status", "expires_at", "offer_payload"]


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ["employee", "leave_type", "starts_on", "ends_on", "requested_days", "approval_stage", "status", "reason", "approval_payload"]


class NotificationItemForm(forms.ModelForm):
    class Meta:
        model = NotificationItem
        fields = ["recipient", "title", "message", "category", "resource_type", "resource_id", "snoozed_until", "metadata"]


class CredentialVaultItemForm(forms.ModelForm):
    class Meta:
        model = CredentialVaultItem
        fields = ["owner", "name", "system_name", "secret_reference", "status", "rotation_due_at", "metadata"]


class CredentialShareGrantForm(forms.ModelForm):
    class Meta:
        model = CredentialShareGrant
        fields = ["credential", "grantee", "permission", "expires_at", "revoked_at", "reason"]


class ManagerScopeForm(forms.ModelForm):
    class Meta:
        model = ManagerScope
        fields = ["manager", "employee", "department", "scope_type", "status", "metadata"]