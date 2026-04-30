from django import forms

from Backend.Apps.Users.models import EmployeeBankAccount, EmployeeFeedback, EmployeeProfile, ResignationRequest


class EmployeeProfileForm(forms.ModelForm):
    class Meta:
        model = EmployeeProfile
        fields = ["display_name", "contact_number", "avatar_url", "github_username", "timezone_name", "employment_type"]


class EmployeeBankAccountForm(forms.ModelForm):
    class Meta:
        model = EmployeeBankAccount
        fields = ["account_holder_name", "masked_account_number", "ifsc_code", "upi_id"]


class EmployeeFeedbackForm(forms.ModelForm):
    class Meta:
        model = EmployeeFeedback
        fields = ["employee", "feedback_type", "project_name", "feedback_text"]


class ResignationRequestForm(forms.ModelForm):
    class Meta:
        model = ResignationRequest
        fields = ["employee", "reason", "last_working_day"]
