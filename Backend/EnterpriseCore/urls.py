from rest_framework.routers import DefaultRouter

from Backend.EnterpriseCore import views

router = DefaultRouter()
router.register("Tenants", views.TenantViewSet, basename="enterprise-tenants")
router.register("Organizations", views.OrganizationViewSet, basename="enterprise-organizations")
router.register("BusinessUnits", views.BusinessUnitViewSet, basename="enterprise-business-units")
router.register("Workspaces", views.WorkspaceViewSet, basename="enterprise-workspaces")
router.register("Capabilities", views.CapabilityViewSet, basename="enterprise-capabilities")
router.register("Roles", views.RoleViewSet, basename="enterprise-roles")
router.register("RoleCapabilities", views.RoleCapabilityViewSet, basename="enterprise-role-capabilities")
router.register("RoleAssignments", views.RoleAssignmentViewSet, basename="enterprise-role-assignments")
router.register("ResourcePolicies", views.ResourcePolicyViewSet, basename="enterprise-resource-policies")
router.register("AccessAuditLogs", views.AccessAuditLogViewSet, basename="enterprise-access-audit-logs")
router.register("OutboxEvents", views.OutboxEventViewSet, basename="enterprise-outbox-events")
router.register("IdempotencyKeys", views.IdempotencyKeyViewSet, basename="enterprise-idempotency-keys")

urlpatterns = router.urls