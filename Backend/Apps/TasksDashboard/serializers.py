from rest_framework import serializers

from Backend.Apps.TasksDashboard.models import ClickUpProjectMapping, DailyStatusEntry, ExternalWorkMapping, ManagerAbbreviation, SlackDeliveryMessage, SlackDeliveryThread, TaskActivity, WorkEntry, WorkItem


class WorkItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkItem
        fields = "__all__"


class WorkEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkEntry
        fields = "__all__"


class TaskActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskActivity
        fields = "__all__"


class DailyStatusEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyStatusEntry
        fields = "__all__"


class SlackDeliveryThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlackDeliveryThread
        fields = "__all__"


class SlackDeliveryMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlackDeliveryMessage
        fields = "__all__"


class ExternalWorkMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalWorkMapping
        fields = "__all__"


class ManagerAbbreviationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManagerAbbreviation
        fields = "__all__"


class ClickUpProjectMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClickUpProjectMapping
        fields = "__all__"
