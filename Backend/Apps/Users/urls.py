from django.urls import path
from rest_framework.routers import DefaultRouter

from Backend.Apps.Users import apis, views_interviewgod
from Backend.Apps.Users import views

router = DefaultRouter()
router.register("Domains", views.DomainViewSet, basename="users-domains")
router.register("Departments", views.DepartmentViewSet, basename="users-departments")
router.register("SubDepartments", views.SubDepartmentViewSet, basename="users-sub-departments")
router.register("Positions", views.PositionViewSet, basename="users-positions")
router.register("Skills", views.SkillViewSet, basename="users-skills")
router.register("EmployeeProfiles", views.EmployeeProfileViewSet, basename="users-employee-profiles")
router.register("DepartmentMemberships", views.DepartmentMembershipViewSet, basename="users-department-memberships")
router.register("UserSkills", views.UserSkillViewSet, basename="users-user-skills")
router.register("Goals", views.GoalViewSet, basename="users-goals")
router.register("GoalFeedback", views.GoalFeedbackViewSet, basename="users-goal-feedback")
router.register("UserStatusSnapshots", views.UserStatusSnapshotViewSet, basename="users-status-snapshots")
router.register("BenchPeriods", views.BenchPeriodViewSet, basename="users-bench-periods")
router.register("EmployeeRatings", views.EmployeeRatingViewSet, basename="users-employee-ratings")
router.register("EmployeeCertificates", views.EmployeeCertificateViewSet, basename="users-employee-certificates")
router.register("EmployeeFeedback", views.EmployeeFeedbackViewSet, basename="users-employee-feedback")
router.register("PayProfiles", views.PayProfileViewSet, basename="users-pay-profiles")
router.register("EmployeeBankAccounts", views.EmployeeBankAccountViewSet, basename="users-bank-accounts")
router.register("EmployeePaymentSnapshots", views.EmployeePaymentSnapshotViewSet, basename="users-payment-snapshots")
router.register("LeavePolicies", views.LeavePolicyViewSet, basename="users-leave-policies")
router.register("LeaveBalances", views.LeaveBalanceViewSet, basename="users-leave-balances")
router.register("LeaveTransactions", views.LeaveTransactionViewSet, basename="users-leave-transactions")
router.register("ResignationRequests", views.ResignationRequestViewSet, basename="users-resignation-requests")
router.register("UserEffortReports", views.UserEffortReportViewSet, basename="users-effort-reports")
router.register("InterviewProgress", views.InterviewProgressViewSet, basename="users-interview-progress")

urlpatterns = [
	path("api/issues/", apis.FetchIssuesAPIView.as_view(), name="users-api-issues"),
	path("api/payments/calculate/", apis.CalculatePayments.as_view(), name="users-api-payments-calculate"),
	path("api/payroll/calculate/", apis.CalculatePayroll.as_view(), name="users-api-payroll-calculate"),
	path("api/payments/previous/", apis.CalculatePreviousPaymentData.as_view(), name="users-api-payment-previous"),
	path("api/change-department/", apis.ChangeDepartmentView.as_view(), name="users-api-change-department"),
	path("interviewgod/run-sync/", views_interviewgod.RunInterviewSyncAPIView.as_view(), name="users-interviewgod-run-sync"),
	path("interviewgod/create-candidates/", views_interviewgod.CreateInterviewCandidatesAPIView.as_view(), name="users-interviewgod-create-candidates"),
	path("interviewgod/send-interviews/", views_interviewgod.SendInterviewsAPIView.as_view(), name="users-interviewgod-send-interviews"),
	path("interviewgod/send/<int:user_id>/", views_interviewgod.SendInterviewForUserAPIView.as_view(), name="users-interviewgod-send-user"),
] + router.urls
