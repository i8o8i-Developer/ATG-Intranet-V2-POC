from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import TenantContext
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import viewsets


@method_decorator(csrf_exempt, name="dispatch")
class TenantScopedModelViewSet(viewsets.ModelViewSet):
    tenant_header = "X-Tenant-Id"
    workspace_header = "X-Workspace-Id"

    def get_request_tenant(self):
        tenant = getattr(self.request, "tenant", None)
        if tenant:
            return tenant
        tenant_id = self.request.headers.get(self.tenant_header)
        if not tenant_id:
            return None
        try:
            tid = int(tenant_id)
            return Tenant.objects.filter(id=tid).first()
        except (ValueError, TypeError):
            return None

    def get_request_workspace(self):
        workspace = getattr(self.request, "workspace", None)
        if workspace:
            return workspace
        workspace_id = self.request.headers.get(self.workspace_header)
        if not workspace_id:
            return None
        try:
            wid = int(workspace_id)
            tenant = self.get_request_tenant()
            queryset = Workspace.objects.filter(id=wid)
            if tenant:
                queryset = queryset.filter(tenant=tenant)
            return queryset.first()
        except (ValueError, TypeError):
            return None

    def get_tenant_context(self):
        return TenantContext(
            tenant=self.get_request_tenant(),
            workspace=self.get_request_workspace(),
            actor=self.request.user if self.request.user.is_authenticated else None,
        )

    def get_queryset(self):
        queryset = super().get_queryset()
        model_fields = {field.name for field in queryset.model._meta.fields}
        tenant = self.get_request_tenant()
        workspace = self.get_request_workspace()
        if "tenant" in model_fields and not tenant:
            return queryset.none()
        if tenant and "tenant" in model_fields:
            queryset = queryset.filter(tenant=tenant)
        if workspace and "workspace" in model_fields:
            queryset = queryset.filter(workspace=workspace)
        return queryset

    def get_serializer(self, *args, **kwargs):
        data = kwargs.get("data")
        if data is not None and hasattr(self, "queryset"):
            mutable_data = data.copy()
            model_fields = {field.name for field in self.queryset.model._meta.fields}
            tenant = self.get_request_tenant()
            workspace = self.get_request_workspace()
            if tenant and "tenant" in model_fields and not mutable_data.get("tenant"):
                mutable_data["tenant"] = tenant.pk
            if workspace and "workspace" in model_fields and not mutable_data.get("workspace"):
                mutable_data["workspace"] = workspace.pk
            kwargs["data"] = mutable_data
        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        values = {}
        model_fields = {field.name for field in serializer.Meta.model._meta.fields}
        tenant = self.get_request_tenant()
        workspace = self.get_request_workspace()
        if "tenant" in model_fields and not tenant and "tenant" not in serializer.validated_data:
            raise serializers.ValidationError({"tenant": "X-Tenant-Id Header Or Tenant Field Is Required."})
        if tenant and "tenant" in model_fields and "tenant" not in serializer.validated_data:
            values["tenant"] = tenant
        if workspace and "workspace" in model_fields and "workspace" not in serializer.validated_data:
            values["workspace"] = workspace
        if "created_by" in model_fields and self.request.user.is_authenticated:
            values["created_by"] = self.request.user
        if "updated_by" in model_fields and self.request.user.is_authenticated:
            values["updated_by"] = self.request.user
        serializer.save(**values)

    def service_response(self, result, serializer_class=None):
        if not result.ok:
            return Response(result.errors, status=result.status_code)
        if serializer_class and result.data is not None:
            return Response(serializer_class(result.data, context=self.get_serializer_context()).data, status=result.status_code)
        return Response(result.data, status=result.status_code)

    def perform_update(self, serializer):
        values = {}
        model_fields = {field.name for field in serializer.Meta.model._meta.fields}
        if "updated_by" in model_fields and self.request.user.is_authenticated:
            values["updated_by"] = self.request.user
        serializer.save(**values)
