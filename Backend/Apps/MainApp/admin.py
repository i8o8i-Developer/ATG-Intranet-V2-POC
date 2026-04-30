from django.contrib import admin

from Backend.Apps.MainApp.models import CredentialShareGrant, CredentialVaultItem, ExternalIssueReference, LeaveRequest, ManagerScope, NotificationItem, NotificationSnoozeRecord, OnboardingOffer


admin.site.register(OnboardingOffer)
admin.site.register(LeaveRequest)
admin.site.register(NotificationItem)
admin.site.register(NotificationSnoozeRecord)
admin.site.register(CredentialVaultItem)
admin.site.register(CredentialShareGrant)
admin.site.register(ExternalIssueReference)
admin.site.register(ManagerScope)