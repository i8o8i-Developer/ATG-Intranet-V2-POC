from rest_framework import serializers

from Backend.Apps.LegacyBridge.models import LegacyApplicationMap, LegacyMigrationIssue, LegacyModelCrosswalk, MigrationRun


class LegacyApplicationMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegacyApplicationMap
        fields = "__all__"


class LegacyModelCrosswalkSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegacyModelCrosswalk
        fields = "__all__"


class MigrationRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = MigrationRun
        fields = "__all__"


class LegacyMigrationIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegacyMigrationIssue
        fields = "__all__"
