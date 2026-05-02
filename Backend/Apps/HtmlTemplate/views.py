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
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import ServiceResult, TenantContext
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView


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


class HtmlTemplateLegacyMixin:
    permission_classes = [permissions.IsAuthenticated]

    def get_context(self, request):
        actor = request.user if request.user.is_authenticated else None
        actor_profile = EmployeeProfile.objects.filter(user=actor).select_related("tenant", "workspace").order_by("id").first() if actor else None
        if actor_profile:
            return ServiceResult.success(TenantContext(tenant=actor_profile.tenant, workspace=actor_profile.workspace, actor=actor, source="HtmlTemplateLegacyAPI"))
        tenant_hint = request.headers.get("X-Tenant-Id") or request.query_params.get("tenant") or request.data.get("tenant")
        workspace_hint = request.headers.get("X-Workspace-Id") or request.query_params.get("workspace") or request.data.get("workspace")
        tenant = Tenant.objects.filter(id=tenant_hint).first() if str(tenant_hint or "").isdigit() else Tenant.objects.filter(slug__iexact=str(tenant_hint or "")).first()
        workspace = Workspace.objects.filter(id=workspace_hint).first() if str(workspace_hint or "").isdigit() else Workspace.objects.filter(code__iexact=str(workspace_hint or "")).first()
        if not tenant:
            active_tenants = list(Tenant.objects.filter(status=Tenant.STATUS_ACTIVE).order_by("id")[:2])
            tenant = active_tenants[0] if len(active_tenants) == 1 else None
        if tenant and workspace and workspace.tenant_id != tenant.id:
            workspace = None
        if tenant and not workspace:
            workspace = Workspace.objects.filter(tenant=tenant).order_by("id").first()
        if not tenant:
            return ServiceResult.failure({"tenant": "Tenant Context Is Required For HtmlTemplate Request."}, status_code=400)
        return ServiceResult.success(TenantContext(tenant=tenant, workspace=workspace, actor=actor, source="HtmlTemplateLegacyAPI"))

    def with_context(self, request):
        result = self.get_context(request)
        if not result.ok:
            return None, Response(result.errors, status=result.status_code)
        return result.data, None


class ContentTemplateCreateLegacyAPIView(HtmlTemplateLegacyMixin, APIView):
    def post(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        serializer = ContentTemplateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = TemplateRenderService.create_content_template(context, **serializer.validated_data)
        return Response(ContentTemplateSerializer(result.data).data if result.ok else result.errors, status=result.status_code)


class ContentTemplateRenderLegacyAPIView(HtmlTemplateLegacyMixin, APIView):
    def post(self, request, pk):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        template = ContentTemplate.objects.filter(tenant=context.tenant, id=pk).first()
        if not template:
            return Response({"template": "Content Template Not Found."}, status=404)
        serializer = TemplateRenderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = TemplateRenderService.render_text_template(template, serializer.validated_data.get("variables") or {})
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class GenericHtmlTemplateSyncLegacyAPIView(HtmlTemplateLegacyMixin, APIView):
    def post(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        serializer = SyncGtmTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = TemplateRenderService.sync_gtm_offer_template(
            context,
            template_path=data.get("template_path", ""),
            offer_type=data.get("offer_type", "Intern"),
            position=data.get("position", "Business Analyst"),
            domains=data.get("domains") or ["ATG", "EI"],
            html_content=request.data.get("html_content", ""),
        )
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class GenericHtmlTemplateRenderLegacyAPIView(HtmlTemplateLegacyMixin, APIView):
    def post(self, request, pk):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        template = GenericHtmlTemplate.objects.filter(tenant=context.tenant, id=pk).first()
        if not template:
            return Response({"template": "Generic HTML Template Not Found."}, status=404)
        serializer = TemplateRenderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = TemplateRenderService.render_text_template(template, serializer.validated_data.get("variables") or {})
        return Response(result.data if result.ok else result.errors, status=result.status_code)
