from rest_framework.routers import DefaultRouter

from Backend.Apps.Banao import views

router = DefaultRouter()
router.register("LeadTags", views.LeadTagViewSet, basename="banao-lead-tags")
router.register("LeadAccounts", views.LeadAccountViewSet, basename="banao-lead-accounts")
router.register("LeadContacts", views.LeadContactViewSet, basename="banao-lead-contacts")
router.register("LeadActivities", views.LeadActivityViewSet, basename="banao-lead-activities")
router.register("LeadNotes", views.LeadNoteViewSet, basename="banao-lead-notes")
router.register("LeadTests", views.LeadTestViewSet, basename="banao-lead-tests")
router.register("ProposalArtifacts", views.ProposalArtifactViewSet, basename="banao-proposal-artifacts")
router.register("AuditArtifacts", views.AuditArtifactViewSet, basename="banao-audit-artifacts")
router.register("WorkflowTransitions", views.WorkflowTransitionViewSet, basename="banao-workflow-transitions")
router.register("WorkflowStatusHistory", views.WorkflowStatusHistoryViewSet, basename="banao-workflow-status-history")

urlpatterns = router.urls
