from django.contrib.auth import authenticate
from django.core import signing
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


class LegacyGitHubTokenObtainPairSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        request = self.context.get("request")
        user = authenticate(request=request, username=attrs["username"], password=attrs["password"])
        if not user or not user.is_active:
            raise serializers.ValidationError({"detail": "No active account found with the given credentials."})
        self.user = user
        data = {
            "refresh": signing.dumps({"user_id": user.id, "type": "refresh"}, salt="github-extension-refresh"),
            "access": signing.dumps({"user_id": user.id, "type": "access"}, salt="github-extension-access"),
        }
        employee = user.new_employee_profiles.select_related("position", "department").order_by("id").first()
        if employee and employee.position_id:
            user_type = employee.position.title
        elif employee and employee.department and employee.department.category:
            user_type = employee.department.category
        else:
            user_type = "Position not found"
        data["user_type"] = user_type
        return data


class LegacyGitHubTokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        try:
            payload = signing.loads(attrs["refresh"], salt="github-extension-refresh", max_age=604800)
        except signing.BadSignature as exc:
            raise serializers.ValidationError({"detail": "Invalid refresh token."}) from exc
        return {
            "access": signing.dumps({"user_id": payload.get("user_id"), "type": "access"}, salt="github-extension-access")
        }
    def validate(self, attrs):
        data = super().validate(attrs)
        employee = self.user.new_employee_profiles.select_related("position", "department").order_by("id").first()
        if employee and employee.position_id:
            user_type = employee.position.title
        elif employee and employee.department and employee.department.category:
            user_type = employee.department.category
        else:
            user_type = "Position not found"
        data["user_type"] = user_type
        return data
