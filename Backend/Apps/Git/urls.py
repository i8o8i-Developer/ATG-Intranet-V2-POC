from rest_framework.routers import DefaultRouter
from django.urls import path

from Backend.Apps.Git import views

router = DefaultRouter()
router.register("GitRepositorySnapshots", views.GitRepositorySnapshotViewSet, basename="git-repository-snapshots")
router.register("GitActivitySnapshots", views.GitActivitySnapshotViewSet, basename="git-activity-snapshots")
router.register("RepositoryUtilityRequests", views.RepositoryUtilityRequestViewSet, basename="git-repository-utility-requests")

urlpatterns = [path("download/", views.LegacyGitDownloadAPIView.as_view(), name="git-download")] + router.urls
