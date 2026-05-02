from Backend.Apps.LegacyBridge.models import LegacyApplicationMap, LegacyMigrationIssue, LegacyModelCrosswalk, MigrationRun
from Backend.Apps.LegacyBridge.serializers import LegacyApplicationMapSerializer, LegacyMigrationIssueSerializer, LegacyModelCrosswalkSerializer, MigrationRunSerializer
from Backend.Apps.LegacyBridge.services import LegacyMappingService, LegacyMigrationService
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import ServiceResult, TenantContext
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView


class LegacyApplicationMapViewSet(TenantScopedModelViewSet):
    queryset = LegacyApplicationMap.objects.select_related("tenant", "workspace").all()
    serializer_class = LegacyApplicationMapSerializer

    @action(detail=False, methods=["post"], url_path="seed-defaults")
    def seed_defaults(self, request):
        result = LegacyMappingService.seed_default_app_map(self.get_tenant_context())
        return self.service_response(result)

    @action(detail=False, methods=["get"], url_path="preview-defaults")
    def preview_defaults(self, request):
        result = LegacyMappingService.preview_default_app_map(self.get_tenant_context())
        return self.service_response(result)


class LegacyModelCrosswalkViewSet(TenantScopedModelViewSet):
    queryset = LegacyModelCrosswalk.objects.select_related("tenant", "workspace").all()
    serializer_class = LegacyModelCrosswalkSerializer

    @action(detail=False, methods=["post"], url_path="record")
    def record(self, request):
        result = LegacyMigrationService.record_crosswalk(self.get_tenant_context(), request.data)
        return self.service_response(result, LegacyModelCrosswalkSerializer)


class MigrationRunViewSet(TenantScopedModelViewSet):
    queryset = MigrationRun.objects.select_related("tenant", "workspace").all()
    serializer_class = MigrationRunSerializer

    @action(detail=False, methods=["post"], url_path="start")
    def start(self, request):
        result = LegacyMigrationService.start_run(
            self.get_tenant_context(),
            request.data.get("source_app_label", ""),
            target_app_label=request.data.get("target_app_label", ""),
            mode=request.data.get("mode", "Preview"),
            dry_run=request.data.get("dry_run", True),
            batch_id=request.data.get("batch_id", ""),
            total_rows=request.data.get("total_rows", 0),
        )
        return self.service_response(result, MigrationRunSerializer)

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        result = LegacyMigrationService.complete_run(self.get_tenant_context(), pk, request.data.get("migrated_rows", 0), request.data.get("skipped_rows", 0), request.data.get("result_payload") or {})
        return self.service_response(result, MigrationRunSerializer)

    @action(detail=True, methods=["post"], url_path="fail")
    def fail(self, request, pk=None):
        result = LegacyMigrationService.fail_run(self.get_tenant_context(), pk, request.data.get("failure_reason", "Migration failed."))
        return self.service_response(result, MigrationRunSerializer)

    @action(detail=True, methods=["post"], url_path="rollback")
    def rollback(self, request, pk=None):
        result = LegacyMigrationService.rollback_run(self.get_tenant_context(), pk)
        return self.service_response(result)


class LegacyMigrationIssueViewSet(TenantScopedModelViewSet):
    queryset = LegacyMigrationIssue.objects.select_related("tenant", "workspace", "migration_run").all()
    serializer_class = LegacyMigrationIssueSerializer


class LegacyBridgeMixin:
    permission_classes = [permissions.IsAuthenticated]

    def get_context(self, request):
        actor = request.user if request.user.is_authenticated else None
        actor_profile = EmployeeProfile.objects.filter(user=actor).select_related("tenant", "workspace").order_by("id").first() if actor else None
        if actor_profile:
            return ServiceResult.success(TenantContext(tenant=actor_profile.tenant, workspace=actor_profile.workspace, actor=actor, source="LegacyBridgeAPI"))
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
            return ServiceResult.failure({"tenant": "Tenant Context Is Required For LegacyBridge Request."}, status_code=400)
        return ServiceResult.success(TenantContext(tenant=tenant, workspace=workspace, actor=actor, source="LegacyBridgeAPI"))

    def with_context(self, request):
        result = self.get_context(request)
        if not result.ok:
            return None, Response(result.errors, status=result.status_code)
        return result.data, None


class PreviewDefaultsLegacyAPIView(LegacyBridgeMixin, APIView):
    def get(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = LegacyMappingService.preview_default_app_map(context)
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class SeedDefaultsLegacyAPIView(LegacyBridgeMixin, APIView):
    def post(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = LegacyMappingService.seed_default_app_map(context)
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class RecordCrosswalkLegacyAPIView(LegacyBridgeMixin, APIView):
    def post(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = LegacyMigrationService.record_crosswalk(context, request.data)
        return Response(LegacyModelCrosswalkSerializer(result.data).data if result.ok else result.errors, status=result.status_code)


class StartRunLegacyAPIView(LegacyBridgeMixin, APIView):
    def post(self, request):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = LegacyMigrationService.start_run(
            context,
            request.data.get("source_app_label", ""),
            target_app_label=request.data.get("target_app_label", ""),
            mode=request.data.get("mode", "Preview"),
            dry_run=request.data.get("dry_run", True),
            batch_id=request.data.get("batch_id", ""),
            total_rows=request.data.get("total_rows", 0),
        )
        return Response(MigrationRunSerializer(result.data).data if result.ok else result.errors, status=result.status_code)


class CompleteRunLegacyAPIView(LegacyBridgeMixin, APIView):
    def post(self, request, run_id):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = LegacyMigrationService.complete_run(context, run_id, request.data.get("migrated_rows", 0), request.data.get("skipped_rows", 0), request.data.get("result_payload") or {})
        return Response(MigrationRunSerializer(result.data).data if result.ok else result.errors, status=result.status_code)


class FailRunLegacyAPIView(LegacyBridgeMixin, APIView):
    def post(self, request, run_id):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = LegacyMigrationService.fail_run(context, run_id, request.data.get("failure_reason", "Migration failed."))
        return Response(MigrationRunSerializer(result.data).data if result.ok else result.errors, status=result.status_code)


class RollbackRunLegacyAPIView(LegacyBridgeMixin, APIView):
    def post(self, request, run_id):
        context, error_response = self.with_context(request)
        if error_response:
            return error_response
        result = LegacyMigrationService.rollback_run(context, run_id)
        return Response(result.data if result.ok else result.errors, status=result.status_code)
