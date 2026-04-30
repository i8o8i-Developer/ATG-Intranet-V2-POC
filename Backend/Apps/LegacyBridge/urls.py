from rest_framework.routers import DefaultRouter

from Backend.Apps.LegacyBridge import views

router = DefaultRouter()
router.register("LegacyApplicationMaps", views.LegacyApplicationMapViewSet, basename="legacy-application-maps")
router.register("LegacyModelCrosswalks", views.LegacyModelCrosswalkViewSet, basename="legacy-model-crosswalks")
router.register("MigrationRuns", views.MigrationRunViewSet, basename="legacy-migration-runs")
router.register("LegacyMigrationIssues", views.LegacyMigrationIssueViewSet, basename="legacy-migration-issues")

urlpatterns = router.urls