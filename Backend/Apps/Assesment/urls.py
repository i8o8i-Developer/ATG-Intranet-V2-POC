from django.urls import path
from rest_framework.routers import DefaultRouter

from Backend.Apps.Assesment import views

router = DefaultRouter()
router.register("AssessmentTemplates", views.AssessmentTemplateViewSet, basename="assesment-assessment-templates")
router.register("AssessmentAssignments", views.AssessmentAssignmentViewSet, basename="assesment-assessment-assignments")
router.register("AssessmentSubmissions", views.AssessmentSubmissionViewSet, basename="assesment-assessment-submissions")
router.register("AssessmentActivities", views.AssessmentActivityViewSet, basename="assesment-assessment-activities")

legacy_send_assessment = views.AssessmentAssignmentViewSet.as_view({"post": "assign_by_email"})
legacy_checkassign = views.AssessmentAssignmentViewSet.as_view({"get": "legacy_checkassign", "post": "legacy_checkassign"})
legacy_dashboard = views.AssessmentAssignmentViewSet.as_view({"get": "legacy_dashboard"})

urlpatterns = [
	path("assessment/", legacy_dashboard, name="assesment-legacy-assessment"),
	path("api/sendassessmentapi/", legacy_send_assessment, name="assesment-legacy-sendassessmentapi"),
	path("checkassign/", legacy_checkassign, name="assesment-legacy-checkassign"),
] + router.urls