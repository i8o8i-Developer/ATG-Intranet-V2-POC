from rest_framework.permissions import BasePermission, IsAuthenticated


class IsTenantAuthenticated(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return bool(getattr(request, "tenant", None) or request.headers.get("X-Tenant-Id"))


class HasEnterpriseCapability(BasePermission):
    required_capability = None

    def has_permission(self, request, view):
        capability = getattr(view, "required_capability", None) or self.required_capability
        if not capability:
            return True
        user_capabilities = getattr(request, "capabilities", set())
        return capability in user_capabilities
