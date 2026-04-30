from rest_framework import serializers

from Backend.Apps.MainApp.models import CredentialShareGrant, CredentialVaultItem, ExternalIssueReference, LeaveRequest, ManagerScope, NotificationItem, NotificationSnoozeRecord, OnboardingOffer


class OnboardingOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingOffer
        fields = "__all__"


class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = "__all__"


class NotificationItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationItem
        fields = "__all__"


class CredentialVaultItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CredentialVaultItem
        fields = "__all__"


class CredentialShareGrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = CredentialShareGrant
        fields = "__all__"


class ExternalIssueReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalIssueReference
        fields = "__all__"


class NotificationSnoozeRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSnoozeRecord
        fields = "__all__"


class ManagerScopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManagerScope
        fields = "__all__"
