from rest_framework import serializers

from Backend.Apps.Project.models import (
    ComplianceAssignment,
    ComplianceCampaign,
    DefaultCheckpoint,
    DeliveryAlert,
    DeliveryDocument,
    DeliveryMilestone,
    MilestoneComponent,
    ProjectContact,
    ProjectWorkspace,
    RepositoryLink,
    TeamAssignment,
)


class ProjectWorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectWorkspace
        fields = "__all__"


class ProjectContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectContact
        fields = "__all__"


class DefaultCheckpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = DefaultCheckpoint
        fields = "__all__"


class MilestoneComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MilestoneComponent
        fields = "__all__"


class DeliveryMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryMilestone
        fields = "__all__"


class TeamAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamAssignment
        fields = "__all__"


class RepositoryLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepositoryLink
        fields = "__all__"


class DeliveryDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryDocument
        fields = "__all__"


class DeliveryAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryAlert
        fields = "__all__"


class ComplianceCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceCampaign
        fields = "__all__"


class ComplianceAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceAssignment
        fields = "__all__"
