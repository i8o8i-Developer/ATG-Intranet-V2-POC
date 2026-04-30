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

urlpatterns = router.urls
