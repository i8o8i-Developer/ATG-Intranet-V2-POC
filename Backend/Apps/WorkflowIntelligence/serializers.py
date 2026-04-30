from rest_framework import serializers

from Backend.Apps.WorkflowIntelligence.models import BusinessWorkflowMap, RouteUsageAggregate, WorkflowReport


class RouteUsageAggregateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteUsageAggregate
        fields = "__all__"


class WorkflowReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowReport
        fields = "__all__"


class BusinessWorkflowMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessWorkflowMap
        fields = "__all__"
