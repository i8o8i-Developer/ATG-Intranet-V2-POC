from django.urls import path
from rest_framework.routers import DefaultRouter

from Backend.Apps.L3 import views

router = DefaultRouter()
router.register("CollegePipelineRecords", views.CollegePipelineRecordViewSet, basename="l3-college-pipeline-records")
router.register("CollegeContacts", views.CollegeContactViewSet, basename="l3-college-contacts")
router.register("CollegeAssignments", views.CollegeAssignmentViewSet, basename="l3-college-assignments")
router.register("CollegeEmailTemplates", views.CollegeEmailTemplateViewSet, basename="l3-college-email-templates")
router.register("CandidateProfiles", views.CandidateProfileViewSet, basename="l3-candidate-profiles")
router.register("TalentAssignments", views.TalentAssignmentViewSet, basename="l3-talent-assignments")
router.register("TalentEmails", views.TalentEmailViewSet, basename="l3-talent-emails")
router.register("TalentPerformanceSnapshots", views.TalentPerformanceSnapshotViewSet, basename="l3-talent-performance-snapshots")

urlpatterns = [
	path("caller/pending_colleges", views.PendingCollegesLegacyAPIView.as_view(), name="pending_colleges"),
	path("caller/new_colleges", views.NewCollegesLegacyAPIView.as_view(), name="new_colleges"),
	path("dataentry/", views.DataEntryLegacyAPIView.as_view(), name="dataentry"),
	path("perform/<str:intern>", views.AssignTaskLegacyAPIView.as_view(), name="assign_task"),
	path("hold/<str:intern>/<str:hold_or_unhold>", views.HoldInternLegacyAPIView.as_view(), name="hold_intern"),
	path("manager/performance_list/", views.PerformanceListLegacyAPIView.as_view(), name="performance_list"),
	path("manager/performance_detail/<str:intern>", views.PerformanceDetailLegacyAPIView.as_view(), name="performance_detail"),
	path("send_mail/<int:id>/<str:path>/<int:assign_id>", views.SendEmailLegacyAPIView.as_view(), name="send_email"),
	path("manager/performance_analytics/", views.PerformanceAnalyticsLegacyAPIView.as_view(), name="performance_analytics"),
	path("update_email/<int:id>/<str:intern>", views.UpdateEmailLegacyAPIView.as_view(), name="email_update"),
	path("update_contact/<int:id>/<int:assign_id>", views.UpdateContactLegacyAPIView.as_view(), name="contact_update"),
	path("archive_task/<int:id>/<str:intern>", views.ArchiveTaskLegacyAPIView.as_view(), name="task_archive"),
] + router.urls
