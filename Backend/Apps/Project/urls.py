from django.urls import path
from rest_framework.routers import DefaultRouter

from Backend.Apps.Project import views
from Backend.Apps.Project.serializers import DeliveryDocumentSerializer, DeliveryMilestoneSerializer, ProjectWorkspaceSerializer, RepositoryLinkSerializer, TeamAssignmentSerializer
from Backend.Apps.TasksDashboard.serializers import ClickUpProjectMappingSerializer, WorkItemSerializer

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
router.register("ProjectDelays", views.ProjectDelayViewSet, basename="project-delays")

urlpatterns = [
	path("onboarding/", views.ProjectLegacyActionAPIView.as_view(action_name="onboarding"), name="project-onboarding"),
	path("terms/<int:project_id>/", views.ProjectLegacyActionAPIView.as_view(action_name="terms"), name="project-terms"),
	path("dashboard/<int:pk>/<str:name>/", views.ProjectLegacyActionAPIView.as_view(action_name="dashboard"), name="project-dashboard"),
	path("check-repo-exists/", views.ProjectLegacyActionAPIView.as_view(action_name="check_repo_exists"), name="check_repo_exists"),
	path("create-repo/", views.ProjectLegacyActionAPIView.as_view(action_name="create_repo", response_serializer=RepositoryLinkSerializer), name="create_github_repo"),
	path("assign-repo/", views.ProjectLegacyActionAPIView.as_view(action_name="assign_repo", response_serializer=RepositoryLinkSerializer), name="assign_repo"),
	path("revoke-repo/", views.ProjectLegacyActionAPIView.as_view(action_name="revoke_repo", response_serializer=RepositoryLinkSerializer), name="revoke_repo"),
	path("addnewlink/", views.ProjectLegacyActionAPIView.as_view(action_name="add_new_link", response_serializer=DeliveryDocumentSerializer), name="project-add-new-link"),
	path("mark_absent/", views.ProjectLegacyActionAPIView.as_view(action_name="mark_absent", response_serializer=TeamAssignmentSerializer), name="mark-absent"),
	path("replaceMember/", views.ProjectLegacyActionAPIView.as_view(action_name="replace_member", response_serializer=TeamAssignmentSerializer), name="replace-member"),
	path("removeMember/", views.ProjectLegacyActionAPIView.as_view(action_name="remove_member", response_serializer=TeamAssignmentSerializer), name="remove-member"),
	path("addMember/", views.ProjectLegacyActionAPIView.as_view(action_name="add_member", response_serializer=TeamAssignmentSerializer), name="add-member"),
	path("checkgit/", views.ProjectLegacyActionAPIView.as_view(action_name="update_git"), name="checkgit"),
	path("cleangit/", views.ProjectLegacyActionAPIView.as_view(action_name="cleanup_git"), name="cleangit"),
	path("update_details/", views.ProjectLegacyActionAPIView.as_view(action_name="update_details", response_serializer=ProjectWorkspaceSerializer), name="update-project-details"),
	path("update_milestone/", views.ProjectLegacyActionAPIView.as_view(action_name="update_milestone", response_serializer=DeliveryMilestoneSerializer), name="update-milestones"),
	path("notifications_read/", views.ProjectLegacyActionAPIView.as_view(action_name="notifications_read"), name="mark_as_read"),
	path("addMemberBack/", views.ProjectLegacyActionAPIView.as_view(action_name="add_member_back", response_serializer=TeamAssignmentSerializer), name="add_member_back"),
	path("get_user_organizations/", views.ProjectLegacyActionAPIView.as_view(action_name="get_user_organizations"), name="get_user_organizations"),
	path("add_ktlink/", views.ProjectLegacyActionAPIView.as_view(action_name="add_kt_link", response_serializer=DeliveryDocumentSerializer), name="add_kt_link"),
	path("send_daily_notif/", views.ProjectLegacyActionAPIView.as_view(action_name="daily_notifications"), name="daily project notifications"),
	path("get_user_repo/<int:member_id>/<int:project_id>/", views.ProjectLegacyActionAPIView.as_view(action_name="get_user_repo"), name="get_user_repos"),
	path("days_left_data/<int:project_id>/", views.ProjectLegacyActionAPIView.as_view(action_name="days_left"), name="get_days_left"),
	path("alert_data/<int:project_id>/", views.ProjectLegacyActionAPIView.as_view(action_name="alerts"), name="get_alerts"),
	path("update-subtask-status/<str:subtask_id>/", views.ProjectLegacyActionAPIView.as_view(action_name="update_subtask_status", response_serializer=WorkItemSerializer), name="subtask-status"),
	path("add_task/", views.ProjectLegacyActionAPIView.as_view(action_name="add_task", response_serializer=WorkItemSerializer), name="add_Task"),
	path("create_clickup_mapping/", views.ProjectLegacyActionAPIView.as_view(action_name="create_clickup_mapping", response_serializer=ClickUpProjectMappingSerializer), name="clickupmapping"),
	path("update-task/", views.ProjectLegacyActionAPIView.as_view(action_name="update_task", response_serializer=WorkItemSerializer), name="update-task"),
	path("delete-task/", views.ProjectLegacyActionAPIView.as_view(action_name="delete_task"), name="delete-task"),
	path("extract/", views.ProjectLegacyActionAPIView.as_view(action_name="extract_milestones"), name="extract-and-save-milestones"),
	path("rename/<int:task_id>/", views.ProjectLegacyActionAPIView.as_view(action_name="rename_task", response_serializer=WorkItemSerializer), name="update-task-name"),
	path("save-assignee/", views.ProjectLegacyActionAPIView.as_view(action_name="assign_assignee", response_serializer=WorkItemSerializer), name="save assignee"),
	path("update-priority/", views.ProjectLegacyActionAPIView.as_view(action_name="update_priority", response_serializer=WorkItemSerializer), name="priority update"),
	path("update-type/<int:task_id>/", views.ProjectLegacyActionAPIView.as_view(action_name="update_type", response_serializer=WorkItemSerializer), name="type update"),
	path("update-description/<int:task_id>/", views.ProjectLegacyActionAPIView.as_view(action_name="update_description", response_serializer=WorkItemSerializer), name="desc update"),
	path("update-bounty/", views.ProjectLegacyActionAPIView.as_view(action_name="update_bounty", response_serializer=WorkItemSerializer), name="bounty update"),
	path("update-duedate/", views.ProjectLegacyActionAPIView.as_view(action_name="update_duedate", response_serializer=WorkItemSerializer), name="date update"),
	path("update-task-order/", views.ProjectLegacyActionAPIView.as_view(action_name="update_task_order"), name="update_task_order"),
	path("update-subtask-parent/", views.ProjectLegacyActionAPIView.as_view(action_name="update_subtask_parent", response_serializer=WorkItemSerializer), name="update_subtask_parent"),
	path("get/tasks/<int:pk>/", views.ProjectLegacyActionAPIView.as_view(action_name="task_detail"), name="task-detail"),
	path("task/save_link/", views.ProjectLegacyActionAPIView.as_view(action_name="save_task_link", response_serializer=WorkItemSerializer), name="save task link"),
	path("task/delete_item/", views.ProjectLegacyActionAPIView.as_view(action_name="delete_item"), name="delete_item"),
	path("link/", views.ProjectLegacyActionAPIView.as_view(action_name="link_prs_to_tasks"), name="link_prs_to_tasks"),
	path("upload-project-docs/", views.ProjectLegacyActionAPIView.as_view(action_name="upload_project_docs", response_serializer=DeliveryDocumentSerializer), name="upload-project-docs"),
	path("create-document/", views.ProjectLegacyActionAPIView.as_view(action_name="create_document", response_serializer=DeliveryDocumentSerializer), name="create-document"),
	path("get-file-name/", views.ProjectLegacyActionAPIView.as_view(action_name="get_file_name"), name="get_file_name"),
	path("updateHat/", views.ProjectLegacyActionAPIView.as_view(action_name="update_hat", response_serializer=TeamAssignmentSerializer), name="assign_hat"),
	path("removeHat/", views.ProjectLegacyActionAPIView.as_view(action_name="remove_hat", response_serializer=TeamAssignmentSerializer), name="remove_hat"),
	path("remove_task/<int:project_id>", views.ProjectLegacyActionAPIView.as_view(action_name="delete_clickup_tasks"), name="delete_clickup_tasks"),
	path("relink_task/<int:project_id>/<str:clickup_name>", views.ProjectLegacyActionAPIView.as_view(action_name="relink_clickup_tasks"), name="relink_tasks"),
	path("delete-project-document/", views.ProjectLegacyActionAPIView.as_view(action_name="delete_project_document", response_serializer=DeliveryDocumentSerializer), name="delete_project_document"),
	path("edit-project-document/", views.ProjectLegacyActionAPIView.as_view(action_name="edit_project_document", response_serializer=DeliveryDocumentSerializer), name="edit_project_document"),
	path("toggle-pin-document/", views.ProjectLegacyActionAPIView.as_view(action_name="toggle_pin_document", response_serializer=DeliveryDocumentSerializer), name="toggle_pin_document"),
	path("send-anti-phishing-assessment/", views.ProjectLegacyActionAPIView.as_view(action_name="send_anti_phishing_assessment"), name="send_anti_phishing_assessment"),
	path("anti-phishing-assessment/<str:token>/", views.AntiPhishingAssessmentLegacyAPIView.as_view(), name="take_anti_phishing_assessment"),
	path("anti-phishing-reports/", views.ProjectLegacyActionAPIView.as_view(action_name="anti_phishing_reports"), name="anti_phishing_reports"),
	path("api/add-delay/", views.ProjectLegacyActionAPIView.as_view(action_name="add_delay", response_serializer=DeliveryMilestoneSerializer), name="add_delay"),
	path("api/get-items/", views.ProjectLegacyActionAPIView.as_view(action_name="get_items"), name="get_items"),
] + router.urls