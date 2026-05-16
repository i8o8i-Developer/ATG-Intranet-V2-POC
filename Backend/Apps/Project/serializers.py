from rest_framework import serializers

from Backend.Apps.Project.models import (
    ComplianceAssignment,
    ComplianceCampaign,
    DefaultCheckpoint,
    DeliveryAlert,
    DeliveryDocument,
    DeliveryMilestone,
    MilestoneComponent,
    ProjectBudget,
    ProjectContact,
    ProjectDelay,
    ProjectWorkspace,
    RepositoryLink,
    TeamAssignment,
    TeamAssignmentHistory,
    UserRepositoryStatus,
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


class ProjectDelaySerializer(serializers.ModelSerializer):
    project_name = serializers.SerializerMethodField()
    task_title = serializers.SerializerMethodField()
    reporter_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectDelay
        fields = "__all__"

    def get_project_name(self, obj):
        return obj.project.name if obj.project else None

    def get_task_title(self, obj):
        return obj.task.title if obj.task else None

    def get_reporter_name(self, obj):
        return obj.reported_by.display_name if obj.reported_by else None


class ProjectBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectBudget
        fields = "__all__"


class TeamAssignmentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamAssignmentHistory
        fields = "__all__"


class UserRepositoryStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRepositoryStatus
        fields = "__all__"
