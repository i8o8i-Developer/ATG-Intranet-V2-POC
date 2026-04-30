from Backend.Apps.HtmlTemplate.models import ContentTemplate, GenericHtmlTemplate, OfferMacro, OfferTemplate, TemplateVariable
from Backend.Apps.HtmlTemplate.serializers import (
    ContentTemplateCreateSerializer,
    ContentTemplateSerializer,
    GenericHtmlTemplateSerializer,
    OfferMacroSerializer,
    OfferTemplateSerializer,
    SyncGtmTemplateSerializer,
    TemplateRenderSerializer,
    TemplateVariableSerializer,
)
from Backend.Apps.HtmlTemplate.services import TemplateRenderService
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response


class TemplateVariableViewSet(TenantScopedModelViewSet):
    queryset = TemplateVariable.objects.select_related("tenant", "workspace").all()
    serializer_class = TemplateVariableSerializer


class OfferMacroViewSet(TenantScopedModelViewSet):
    queryset = OfferMacro.objects.select_related("tenant", "workspace").all()
    serializer_class = OfferMacroSerializer


class ContentTemplateViewSet(TenantScopedModelViewSet):
    queryset = ContentTemplate.objects.select_related("tenant", "workspace").prefetch_related("variables").all()
    serializer_class = ContentTemplateSerializer

    @action(detail=True, methods=["post"], url_path="render")
    def render(self, request, pk=None):
        serializer = TemplateRenderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = TemplateRenderService.render_text_template(self.get_object(), serializer.validated_data.get("variables") or {})
        return self.service_response(result)

    @action(detail=False, methods=["post"], url_path="create-template")
    def create_template(self, request):
        serializer = ContentTemplateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = TemplateRenderService.create_content_template(self.get_tenant_context(), **serializer.validated_data)
        return self.service_response(result, ContentTemplateSerializer)

    @action(detail=True, methods=["get"], url_path="variables")
    def variables(self, request, pk=None):
        template = self.get_object()
        body = "\n".join([template.body_html or "", template.body_text or "", template.email_template or ""])
        return Response({"variables": TemplateRenderService.extract_variables(body)})


class OfferTemplateViewSet(TenantScopedModelViewSet):
    queryset = OfferTemplate.objects.select_related("tenant", "workspace", "template").all()
    serializer_class = OfferTemplateSerializer


class GenericHtmlTemplateViewSet(TenantScopedModelViewSet):
    queryset = GenericHtmlTemplate.objects.select_related("tenant", "workspace", "template").all()
    serializer_class = GenericHtmlTemplateSerializer

    @action(detail=False, methods=["post"], url_path="sync-gtm-template")
    def sync_gtm_template(self, request):
        serializer = SyncGtmTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = TemplateRenderService.sync_gtm_offer_template(
            self.get_tenant_context(),
            template_path=data.get("template_path", ""),
            offer_type=data.get("offer_type", "Intern"),
            position=data.get("position", "Business Analyst"),
            domains=data.get("domains") or ["ATG", "EI"],
        )
        return Response(result.data if result.ok else result.errors, status=result.status_code)

    @action(detail=True, methods=["post"], url_path="render")
    def render(self, request, pk=None):
        serializer = TemplateRenderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = TemplateRenderService.render_text_template(self.get_object(), serializer.validated_data.get("variables") or {})
        return self.service_response(result)
