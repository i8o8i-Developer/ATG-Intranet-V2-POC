from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import CapabilityService


class TenantContextMiddleware:
    tenant_header = "X-Tenant-Id"
    workspace_header = "X-Workspace-Id"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = self.resolve_tenant(request)
        request.workspace = self.resolve_workspace(request, request.tenant)
        if request.tenant and getattr(request, "user", None) and request.user.is_authenticated:
            request.capabilities = CapabilityService.list_user_capabilities(request.tenant, request.user, request.workspace)
        else:
            request.capabilities = set()
        return self.get_response(request)

    def resolve_tenant(self, request):
        tenant_id = request.headers.get(self.tenant_header)
        if not tenant_id:
            return None
        return Tenant.objects.filter(id=tenant_id, status=Tenant.STATUS_ACTIVE).first()

    def resolve_workspace(self, request, tenant):
        workspace_id = request.headers.get(self.workspace_header)
        if not workspace_id or not tenant:
            return None
        return Workspace.objects.filter(id=workspace_id, tenant=tenant).first()