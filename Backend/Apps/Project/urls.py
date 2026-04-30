from rest_framework.routers import DefaultRouter

from Backend.Apps.Project import views

router = DefaultRouter()
router.register("ProjectWorkspaces", views.ProjectWorkspaceViewSet, basename="project-workspaces")
router.register("ProjectContacts", views.ProjectContactViewSet, basename="project-contacts")
router.register("DefaultCheckpoints", views.DefaultCheckpointViewSet, basename="project-default-checkpoints")
router.register("MilestoneComponents", views.MilestoneComponentViewSet, basename="project-milestone-components")
router.register("DeliveryMilestones", views.DeliveryMilestoneViewSet, basename="project-delivery-milestones")
router.register("TeamAssignments", views.TeamAssignmentViewSet, basename="project-team-assignments")
router.register("RepositoryLinks", views.RepositoryLinkViewSet, basename="project-repository-links")
router.register("DeliveryDocuments", views.DeliveryDocumentViewSet, basename="project-delivery-documents")
router.register("DeliveryAlerts", views.DeliveryAlertViewSet, basename="project-delivery-alerts")
router.register("ComplianceCampaigns", views.ComplianceCampaignViewSet, basename="project-compliance-campaigns")
router.register("ComplianceAssignments", views.ComplianceAssignmentViewSet, basename="project-compliance-assignments")

urlpatterns = router.urls