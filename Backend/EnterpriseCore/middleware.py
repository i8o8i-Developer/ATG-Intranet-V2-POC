from django.utils import timezone

from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import CapabilityService


class ApiCsrfExemptMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.path.startswith("/admin/"):
            request.csrf_processing_done = True
        return None


class TenantContextMiddleware:
    tenant_header = "X-Tenant-Id"
    workspace_header = "X-Workspace-Id"

    # 
    _tenant_cache = {}
    _tenant_cache_ts = {}
    _workspace_cache = {}
    _workspace_cache_ts = {}
    CACHE_TTL = 60  # seconds

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = self.resolve_tenant(request)
        request.workspace = self.resolve_workspace(request, request.tenant)
        if request.tenant and getattr(request, "user", None) and request.user.is_authenticated:
            try:
                request.capabilities = CapabilityService.list_user_capabilities(request.tenant, request.user, request.workspace)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Capability Lookup Error: {str(e)}", exc_info=True)
                request.capabilities = set()
        else:
            request.capabilities = set()
        return self.get_response(request)

    def _cached_lookup(self, cache, cache_ts, key, lookup_fn, ttl=None):
        if ttl is None:
            ttl = self.CACHE_TTL
        now = timezone.now()
        cache_key = str(key)
        if cache_key in cache:
            age = (now - cache_ts.get(cache_key, now)).total_seconds()
            if age < ttl:
                return cache[cache_key]
        result = lookup_fn()
        cache[cache_key] = result
        cache_ts[cache_key] = now
        return result

    def resolve_tenant(self, request):
        tenant_id = request.headers.get(self.tenant_header)
        if not tenant_id:
            return None
        try:
            tid = int(tenant_id)
        except (ValueError, TypeError):
            return None

        def _lookup():
            try:
                return Tenant.objects.filter(id=tid, status=Tenant.STATUS_ACTIVE).first()
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Tenant Lookup Error: {str(e)}", exc_info=True)
                return None

        return self._cached_lookup(self._tenant_cache, self._tenant_cache_ts, tid, _lookup)

    def resolve_workspace(self, request, tenant):
        if not tenant:
            return None
        workspace_id = request.headers.get(self.workspace_header)
        if not workspace_id:
            return None
        try:
            wid = int(workspace_id)
        except (ValueError, TypeError):
            return None
        cache_key = f"{tenant.id}:{wid}"

        def _lookup():
            try:
                return Workspace.objects.filter(id=wid, tenant=tenant).first()
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Workspace Lookup Error: {str(e)}", exc_info=True)
                return None

        return self._cached_lookup(self._workspace_cache, self._workspace_cache_ts, cache_key, _lookup)