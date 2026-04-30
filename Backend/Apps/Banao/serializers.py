from rest_framework import serializers

from Backend.Apps.Banao.models import AuditArtifact, LeadAccount, LeadActivity, LeadContact, LeadNote, LeadTag, LeadTest, ProposalArtifact, WorkflowStatusHistory, WorkflowTransition


class LeadTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadTag
        fields = "__all__"


class LeadAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadAccount
        fields = "__all__"


class LeadContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadContact
        fields = "__all__"


class LeadActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadActivity
        fields = "__all__"


class LeadNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadNote
        fields = "__all__"


class LeadTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadTest
        fields = "__all__"


class ProposalArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalArtifact
        fields = "__all__"


class AuditArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditArtifact
        fields = "__all__"


class WorkflowTransitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowTransition
        fields = "__all__"


class WorkflowStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStatusHistory
        fields = "__all__"


class LeadCaptureSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=220)
    source = serializers.CharField(required=False, allow_blank=True)
    priority = serializers.CharField(default="Normal")
    owner = serializers.IntegerField(required=False, allow_null=True)
    estimated_value = serializers.DecimalField(max_digits=14, decimal_places=2, required=False)
    currency = serializers.CharField(default="INR")
    contact_name = serializers.CharField(required=False, allow_blank=True)
    contact_email = serializers.EmailField(required=False, allow_blank=True)
    contact_phone = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)


class LeadNoteCreateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True)
    body = serializers.CharField()
    author = serializers.IntegerField(required=False, allow_null=True)
    metadata = serializers.JSONField(required=False)


class WorkflowActionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.JSONField(required=False)


class LeadTestCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=220)
    status = serializers.CharField(default="Pending")
    score = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    due_at = serializers.DateTimeField(required=False, allow_null=True)
    metadata = serializers.JSONField(required=False)
