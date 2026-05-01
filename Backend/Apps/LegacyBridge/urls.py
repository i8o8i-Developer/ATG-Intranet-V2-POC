from django.urls import path
from rest_framework.routers import DefaultRouter

from Backend.Apps.LegacyBridge import views

router = DefaultRouter()
router.register("LegacyApplicationMaps", views.LegacyApplicationMapViewSet, basename="legacy-application-maps")
router.register("LegacyModelCrosswalks", views.LegacyModelCrosswalkViewSet, basename="legacy-model-crosswalks")
router.register("MigrationRuns", views.MigrationRunViewSet, basename="legacy-migration-runs")
router.register("LegacyMigrationIssues", views.LegacyMigrationIssueViewSet, basename="legacy-migration-issues")

urlpatterns = [
	path("api/application-maps/preview-defaults/", views.PreviewDefaultsLegacyAPIView.as_view(), name="legacy-preview-defaults"),
	path("api/application-maps/seed-defaults/", views.SeedDefaultsLegacyAPIView.as_view(), name="legacy-seed-defaults"),
	path("api/crosswalks/record/", views.RecordCrosswalkLegacyAPIView.as_view(), name="legacy-record-crosswalk"),
	path("api/migration-runs/start/", views.StartRunLegacyAPIView.as_view(), name="legacy-start-run"),
	path("api/migration-runs/<int:run_id>/complete/", views.CompleteRunLegacyAPIView.as_view(), name="legacy-complete-run"),
	path("api/migration-runs/<int:run_id>/fail/", views.FailRunLegacyAPIView.as_view(), name="legacy-fail-run"),
	path("api/migration-runs/<int:run_id>/rollback/", views.RollbackRunLegacyAPIView.as_view(), name="legacy-rollback-run"),
] + router.urls