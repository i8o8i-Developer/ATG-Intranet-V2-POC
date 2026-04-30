from rest_framework import serializers

from Backend.Apps.Git.models import GitActivitySnapshot, GitRepositorySnapshot, RepositoryUtilityRequest


class GitRepositorySnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitRepositorySnapshot
        fields = "__all__"


class GitActivitySnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitActivitySnapshot
        fields = "__all__"


class RepositoryUtilityRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepositoryUtilityRequest
        fields = "__all__"


class GitRepositorySyncSerializer(serializers.Serializer):
    live = serializers.BooleanField(default=False)


class CollaboratorAccessSerializer(serializers.Serializer):
    employee = serializers.IntegerField(required=False, allow_null=True)
    github_username = serializers.CharField(required=False, allow_blank=True)
    repositories = serializers.ListField(child=serializers.IntegerField(), required=False, allow_empty=False)
    live = serializers.BooleanField(default=False)

    def validate(self, attrs):
        if not attrs.get("employee") and not attrs.get("github_username"):
            raise serializers.ValidationError("Either employee or github_username is required.")
        return attrs
