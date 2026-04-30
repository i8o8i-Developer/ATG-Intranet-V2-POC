from rest_framework import serializers

from Backend.Apps.GithubExtension.models import BranchReviewerAssignment, BranchTestingAssignment, GitHubRepository, RepositoryBranchStatus


class GitHubRepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GitHubRepository
        fields = "__all__"


class BranchReviewerAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BranchReviewerAssignment
        fields = "__all__"


class BranchTestingAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BranchTestingAssignment
        fields = "__all__"


class RepositoryBranchStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepositoryBranchStatus
        fields = "__all__"


class BranchStatusQuerySerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    list = serializers.CharField(required=False, allow_blank=True)


class BranchAssignmentCreateSerializer(serializers.Serializer):
    repository = serializers.IntegerField(required=False)
    reponame = serializers.CharField(required=False, allow_blank=True)
    branch_name = serializers.CharField(max_length=180)
    user_type = serializers.ChoiceField(choices=["tester", "reviewer"], required=False)
    employee = serializers.IntegerField(required=False)
    test_report_url = serializers.CharField(required=False, allow_blank=True)
    is_pass = serializers.CharField(required=False, allow_blank=True)
    is_claim = serializers.BooleanField(default=False)
    comment = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)


class BranchAssignmentUpdateSerializer(serializers.Serializer):
    test_report_url = serializers.CharField(required=False, allow_blank=True)
    is_pass = serializers.CharField(required=False, allow_blank=True)
    is_claim = serializers.BooleanField(required=False)
    comment = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)
