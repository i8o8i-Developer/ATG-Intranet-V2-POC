from django.urls import path
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

urlpatterns = [
	path("lead-create/", views.lead_create, name="banao-lead-create"),
	path("new-lead-create/", views.new_lead_create, name="banao-new-lead-create"),
	path("update-lead-on-connection-sent/", views.update_lead_on_connection_sent, name="update-lead-on-connection-sent"),
	path("department-list/", views.department_options, name="department-list"),
	path("user-list/", views.user_options, name="user-list"),
	path("sendoffer/", views.sendoffer, name="banaosendoffer"),
	path("offer/<str:token>", views.banao_dummy, name="banaodummy"),
]

urlpatterns += router.urls
