from rest_framework import serializers

from Backend.Apps.HtmlTemplate.models import ContentTemplate, GenericHtmlTemplate, OfferMacro, OfferTemplate, TemplateVariable


class TemplateVariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateVariable
        fields = "__all__"


class OfferMacroSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferMacro
        fields = "__all__"


class ContentTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentTemplate
        fields = "__all__"


class OfferTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferTemplate
        fields = "__all__"


class GenericHtmlTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenericHtmlTemplate
        fields = "__all__"


class TemplateRenderSerializer(serializers.Serializer):
    variables = serializers.JSONField(required=False)


class ContentTemplateCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=180)
    template_type = serializers.CharField(default="Offer")
    subject = serializers.CharField(required=False, allow_blank=True)
    body_html = serializers.CharField(required=False, allow_blank=True)
    body_text = serializers.CharField(required=False, allow_blank=True)
    email_template = serializers.CharField(required=False, allow_blank=True)
    email_subject = serializers.CharField(required=False, allow_blank=True)
    offer_type = serializers.CharField(default="Intern")
    offer_domain = serializers.CharField(default="ATG")
    position = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(default="Draft")
    metadata = serializers.JSONField(required=False)


class SyncGtmTemplateSerializer(serializers.Serializer):
    template_path = serializers.CharField(required=False, allow_blank=True)
    offer_type = serializers.CharField(default="Intern")
    position = serializers.CharField(default="Business Analyst")
    domains = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=False)
