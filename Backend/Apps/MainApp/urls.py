from django.urls import path
from rest_framework.routers import DefaultRouter

from Backend.Apps.MainApp import views
from Backend.Apps.MainApp.serializers import CredentialShareGrantSerializer, CredentialVaultItemSerializer, ExternalIssueReferenceSerializer, LeaveRequestSerializer, OnboardingOfferSerializer

router = DefaultRouter()
router.register("OnboardingOffers", views.OnboardingOfferViewSet, basename="mainapp-onboarding-offers")
router.register("LeaveRequests", views.LeaveRequestViewSet, basename="mainapp-leave-requests")
router.register("Notifications", views.NotificationItemViewSet, basename="mainapp-notifications")
router.register("CredentialVaultItems", views.CredentialVaultItemViewSet, basename="mainapp-credential-vault-items")
router.register("CredentialShareGrants", views.CredentialShareGrantViewSet, basename="mainapp-credential-share-grants")
router.register("ExternalIssueReferences", views.ExternalIssueReferenceViewSet, basename="mainapp-external-issue-references")
router.register("NotificationSnoozeRecords", views.NotificationSnoozeRecordViewSet, basename="mainapp-notification-snooze-records")
router.register("ManagerScopes", views.ManagerScopeViewSet, basename="mainapp-manager-scopes")

urlpatterns = [
	path("leave/", views.MainAppLegacyActionAPIView.as_view(action_name="leave_list"), name="Leave"),
	path("leave/apply/", views.MainAppLegacyActionAPIView.as_view(action_name="apply_leave", response_serializer=LeaveRequestSerializer), name="apply-leave"),
	path("leave/issue/", views.MainAppLegacyActionAPIView.as_view(action_name="issue_leave", response_serializer=LeaveRequestSerializer), name="issue-leave"),
	path("leave/<int:pk>/", views.MainAppLegacyActionAPIView.as_view(action_name="leave_detail", response_serializer=LeaveRequestSerializer), name="leave-detail"),
	path("emp-cal/", views.MainAppLegacyActionAPIView.as_view(action_name="leave_calendar"), name="emp-cal"),
	path("dept-employes/", views.MainAppLegacyActionAPIView.as_view(action_name="employees_by_department"), name="dept-employes"),
	path("employes-leave/", views.MainAppLegacyActionAPIView.as_view(action_name="employee_leaves"), name="employes-leave"),
	path("add-employes-leave/", views.MainAppLegacyActionAPIView.as_view(action_name="add_employee_leave", response_serializer=LeaveRequestSerializer), name="add-employes-leave"),
	path("Hierarchy/", views.MainAppLegacyActionAPIView.as_view(action_name="hierarchy"), name="Heirarchy"),
	path("Payroll/", views.MainAppLegacyActionAPIView.as_view(action_name="payroll"), name="Payroll"),
	path("Documentation/", views.MainAppLegacyActionAPIView.as_view(action_name="documentation"), name="Documentation"),
	path("Onboard/createmantis", views.MainAppLegacyActionAPIView.as_view(action_name="createmantis", response_serializer=ExternalIssueReferenceSerializer), name="createmantis"),
	path("Track/", views.MainAppLegacyActionAPIView.as_view(action_name="track"), name="Track"),
	path("offer/<str:token>", views.MainAppOfferTokenLegacyAPIView.as_view(), name="dummy"),
	path("offer/html/<str:token>", views.OnboardingFlowHTMLView.as_view(), name="onboarding-flow-html"),
	path("download-offer/<str:token>", views.MainAppOfferDownloadLegacyAPIView.as_view(), name="download_offer"),
	path("nda", views.MainAppLegacyActionAPIView.as_view(action_name="nda"), name="nda"),
	path("Onboard/Track_my_reportee", views.MainAppLegacyActionAPIView.as_view(action_name="track_reportee"), name="Track_my_reportee"),
	path("Onboard/manager_track", views.MainAppLegacyActionAPIView.as_view(action_name="manager_track"), name="manager_track"),
	path("Onboard/nda", views.MainAppLegacyActionAPIView.as_view(action_name="nda"), name="onboard-nda"),
	path("Onboard/Delete", views.MainAppLegacyActionAPIView.as_view(action_name="delete_onboard"), name="Delete"),
	path("Onboard/Bug_Issue", views.MainAppLegacyActionAPIView.as_view(action_name="bug_issue", response_serializer=ExternalIssueReferenceSerializer), name="Bug_Issue"),
	path("Onboard/Send_Offer", views.MainAppLegacyActionAPIView.as_view(action_name="send_offer", response_serializer=OnboardingOfferSerializer), name="Send_Offer"),
	path("Onboard/send-actual-offer/", views.MainAppLegacyActionAPIView.as_view(action_name="send_actual_offer", response_serializer=OnboardingOfferSerializer), name="send_actual_offer"),
	path("checkname/", views.MainAppLegacyActionAPIView.as_view(action_name="checkname"), name="checkmail"),
	path("dep_valid/", views.MainAppLegacyActionAPIView.as_view(action_name="dep_valid"), name="dep_valid"),
	path("remind_work/", views.MainAppLegacyActionAPIView.as_view(action_name="remind_work"), name="remind_work"),
	path("execute/", views.MainAppLegacyActionAPIView.as_view(action_name="execute"), name="execute"),
	path("send-pdf-offer", views.MainAppLegacyActionAPIView.as_view(action_name="send_pdf_offer"), name="send-pdf-offer"),
	path("send-certificate", views.MainAppLegacyActionAPIView.as_view(action_name="send_certificate"), name="send_certificate"),
	path("search_username/", views.MainAppLegacyActionAPIView.as_view(action_name="search_username"), name="search_username"),
	path("get_joining_date/", views.MainAppLegacyActionAPIView.as_view(action_name="get_joining_date"), name="get_joining_date"),
	path("deactivate-multiple-employee/", views.MainAppLegacyActionAPIView.as_view(action_name="deactivate_multiple"), name="deactivate-multiple-employee"),
	path("deactivate-employee/", views.MainAppLegacyActionAPIView.as_view(action_name="deactivate"), name="deactivate-employee"),
	path("dep_pos_val/", views.MainAppLegacyActionAPIView.as_view(action_name="dep_pos_val"), name="dep_pos_val"),
	path("api-testing", views.MainAppLegacyActionAPIView.as_view(action_name="api_testing"), name="api_testing"),
	path("docs-view-all/", views.MainAppLegacyActionAPIView.as_view(action_name="docs_view_all"), name="docs-view-all"),
	path("search/", views.MainAppLegacyActionAPIView.as_view(action_name="search"), name="search"),
	path("update_reportee/<int:bug_id>/", views.MainAppLegacyActionAPIView.as_view(action_name="update_reportee", response_serializer=ExternalIssueReferenceSerializer), name="update_reportee"),
	path("load-sub-dept", views.MainAppLegacyActionAPIView.as_view(action_name="load_sub_departments"), name="load-sub-dept"),
	path("get-department-choices/", views.MainAppLegacyActionAPIView.as_view(action_name="department_choices"), name="get_department_choices"),
	path("pass-management/", views.MainAppLegacyActionAPIView.as_view(action_name="pass_management"), name="pass-management"),
	path("create-credentials/", views.MainAppLegacyActionAPIView.as_view(action_name="create_credentials", response_serializer=CredentialVaultItemSerializer), name="create-credentials"),
	path("get-credentials/", views.MainAppLegacyActionAPIView.as_view(action_name="get_credentials"), name="get-credentials"),
	path("share-credentials/", views.MainAppLegacyActionAPIView.as_view(action_name="share_credentials", response_serializer=CredentialShareGrantSerializer), name="share-credentials"),
	path("api/search-user/", views.MainAppLegacyActionAPIView.as_view(action_name="search_user"), name="search-user"),
	path("api/credentials/remove-share/", views.MainAppLegacyActionAPIView.as_view(action_name="remove_share", response_serializer=CredentialShareGrantSerializer), name="remove-share"),
	path("api/test-password-reset/", views.MainAppLegacyActionAPIView.as_view(action_name="test_password_reset"), name="test-password-reset"),
	path("Onboard/register-employee", views.MainAppLegacyActionAPIView.as_view(action_name="register_employee"), name="onboard-register-employee"),
] + router.urls
