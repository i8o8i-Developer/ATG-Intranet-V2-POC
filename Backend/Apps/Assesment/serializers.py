from rest_framework import serializers

from Backend.Apps.Assesment.models import AssessmentActivity, AssessmentAssignment, AssessmentSubmission, AssessmentTemplate


class AssessmentTemplateSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = AssessmentTemplate
        fields = "__all__"


class AssessmentAssignmentSerializer(serializers.ModelSerializer):
    assessment_title = serializers.CharField(source="assessment.title", read_only=True)
    assessment_sequence_number = serializers.IntegerField(source="assessment.sequence_number", read_only=True)
    employee_name = serializers.CharField(source="employee.display_name", read_only=True)
    employee_code = serializers.CharField(source="employee.employee_code", read_only=True)

    class Meta:
        model = AssessmentAssignment
        fields = "__all__"


class AssessmentSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentSubmission
        fields = "__all__"


class AssessmentActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentActivity
        fields = "__all__"


class AssignAssessmentSerializer(serializers.Serializer):
    employee = serializers.IntegerField(required=False)
    employees = serializers.ListField(child=serializers.IntegerField(), required=False, allow_empty=False)
    due_at = serializers.DateTimeField(required=False, allow_null=True)
    generate_provider_link = serializers.BooleanField(default=False)

    def validate(self, attrs):
        if not attrs.get("employee") and not attrs.get("employees"):
            raise serializers.ValidationError("Either Employee Or Employees Is Required.")
        return attrs


class SubmitAssessmentSerializer(serializers.Serializer):
    score = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, default=0)
    percentage = serializers.DecimalField(max_digits=6, decimal_places=2, required=False, allow_null=True)
    answer_payload = serializers.JSONField(required=False)
    evaluated_payload = serializers.JSONField(required=False)
    provider_attempt_id = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)


class ProviderLinkSerializer(serializers.Serializer):
    external_user_id = serializers.CharField(required=False, allow_blank=True)
    assessment_url = serializers.URLField(required=False, allow_blank=True)
    provider_payload = serializers.JSONField(required=False)


class ProviderStatusSerializer(serializers.Serializer):
    provider_payload = serializers.JSONField()


class AssessmentDashboardQuerySerializer(serializers.Serializer):
    department = serializers.IntegerField(required=False)
    search = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)
    ordering = serializers.ChoiceField(choices=["status", "weeks_since_join", "assigned_at"], required=False)


class AssessmentEmailDispatchSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    emails = serializers.ListField(child=serializers.EmailField(), required=False, allow_empty=False)
    assessment_ids = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=False)
    assesment = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=False)
    due_at = serializers.DateTimeField(required=False, allow_null=True)
    generate_provider_link = serializers.BooleanField(default=True)

    def validate(self, attrs):
        emails = attrs.get("emails") or ([attrs["email"]] if attrs.get("email") else [])
        assessment_ids = attrs.get("assessment_ids") or attrs.get("assesment") or []
        if not emails:
            raise serializers.ValidationError({"email": "At Least One Email Is Required."})
        if not assessment_ids:
            raise serializers.ValidationError({"assessment_ids": "At Least One Assessment Reference Is Required."})
        attrs["emails"] = emails
        attrs["assessment_ids"] = assessment_ids
        return attrs


class AssessmentAutomationRunSerializer(serializers.Serializer):
    sync_provider = serializers.BooleanField(default=False)
    auto_assign_next = serializers.BooleanField(default=True)
    create_reminders = serializers.BooleanField(default=True)
    grace_days = serializers.IntegerField(default=5, min_value=0)
