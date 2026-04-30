from Backend.Apps.LegacyBridge.models import LegacyApplicationMap, LegacyMigrationIssue, LegacyModelCrosswalk, MigrationRun
from Backend.Apps.LegacyBridge.serializers import LegacyApplicationMapSerializer, LegacyMigrationIssueSerializer, LegacyModelCrosswalkSerializer, MigrationRunSerializer
from Backend.Apps.LegacyBridge.services import LegacyMappingService, LegacyMigrationService
from Backend.EnterpriseCore.viewsets import TenantScopedModelViewSet
from rest_framework.decorators import action


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
