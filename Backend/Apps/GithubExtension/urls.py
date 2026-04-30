from rest_framework.routers import DefaultRouter
from django.urls import path

from Backend.Apps.GithubExtension import views

router = DefaultRouter()
router.register("GitHubRepositories", views.GitHubRepositoryViewSet, basename="github-repositories")
router.register("BranchReviewerAssignments", views.BranchReviewerAssignmentViewSet, basename="github-branch-reviewer-assignments")
router.register("BranchTestingAssignments", views.BranchTestingAssignmentViewSet, basename="github-branch-testing-assignments")
router.register("RepositoryBranchStatuses", views.RepositoryBranchStatusViewSet, basename="github-repository-branch-statuses")

urlpatterns = [
	path("api/branch-status-request/", views.RepoBranchStatusAPIView.as_view()),
	path("api/post-branch-status/", views.PostBranchTesterOrReviewerAPIView.as_view()),
	path("api/update-branch-status/<str:user_type>/<int:pk>", views.DetailBranchTesterOrReviewerAPIView.as_view()),
	path("api/check-repo/<str:repo_name>", views.CheckRepositoryAPIView.as_view()),
] + router.urls
