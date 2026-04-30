from rest_framework.routers import DefaultRouter

from Backend.Apps.Assesment import views

router = DefaultRouter()
router.register("AssessmentTemplates", views.AssessmentTemplateViewSet, basename="assesment-assessment-templates")
router.register("AssessmentAssignments", views.AssessmentAssignmentViewSet, basename="assesment-assessment-assignments")
router.register("AssessmentSubmissions", views.AssessmentSubmissionViewSet, basename="assesment-assessment-submissions")
router.register("AssessmentActivities", views.AssessmentActivityViewSet, basename="assesment-assessment-activities")

urlpatterns = router.urls