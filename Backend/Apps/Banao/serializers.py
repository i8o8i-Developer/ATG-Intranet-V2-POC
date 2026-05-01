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


class LegacyLeadCaptureSerializer(serializers.Serializer):
    full_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    message = serializers.CharField(required=False, allow_blank=True)
    company_name = serializers.CharField(required=False, allow_blank=True)
    origin = serializers.CharField(required=False, allow_blank=True, default="w")
    industry = serializers.CharField(required=False, allow_blank=True, default="Others")
    url = serializers.URLField(required=False, allow_blank=True)
    linkedin_url = serializers.URLField(required=False, allow_blank=True)
    source_page_name = serializers.CharField(required=False, allow_blank=True)
    source_page_url = serializers.URLField(required=False, allow_blank=True)
    page_name = serializers.CharField(required=False, allow_blank=True)
    page_url = serializers.URLField(required=False, allow_blank=True)
    form_page_name = serializers.CharField(required=False, allow_blank=True)
    form_page_url = serializers.URLField(required=False, allow_blank=True)
    country_code = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    country_iso = serializers.CharField(required=False, allow_blank=True)
    country_iso_code = serializers.CharField(required=False, allow_blank=True)
    phone_country_code = serializers.CharField(required=False, allow_blank=True)
    country_dial_code = serializers.CharField(required=False, allow_blank=True)
    dial_code = serializers.CharField(required=False, allow_blank=True)
    countryCode = serializers.CharField(required=False, allow_blank=True)


class LegacyLeadConnectionSerializer(serializers.Serializer):
    domain = serializers.CharField()
    intern_name = serializers.CharField(required=False, allow_blank=True)
    client_name = serializers.CharField(required=False, allow_blank=True)


class BanaoOfferDispatchSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    name = serializers.CharField(max_length=180)
    position_name = serializers.CharField(max_length=180)
    department_name = serializers.CharField(max_length=160)
    pay_type = serializers.CharField(required=False, allow_blank=True, default="Fixed")
    base_pay = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, default=0)
    pay_per_task = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, default=0)
    offer_date = serializers.DateField(required=False)
    offer_type = serializers.CharField(required=False, allow_blank=True, default="Intern")
    title = serializers.CharField(required=False, allow_blank=True)
    whatsapp = serializers.CharField(required=False, allow_blank=True)
    slack = serializers.CharField(required=False, allow_blank=True)
    whatsapp_link = serializers.CharField(required=False, allow_blank=True)


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
