from rest_framework import serializers

from Backend.Apps.Lms.models import LeadQueueSnapshot, LearningAssignment, LearningModule, LearningPath, RevenuePerformanceSnapshot


class LearningPathSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningPath
        fields = "__all__"


class LearningModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningModule
        fields = "__all__"


class LearningAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningAssignment
        fields = "__all__"


class RevenuePerformanceSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = RevenuePerformanceSnapshot
        fields = "__all__"


class LeadQueueSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadQueueSnapshot
        fields = "__all__"
