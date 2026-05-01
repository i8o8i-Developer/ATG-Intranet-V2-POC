from django.urls import path
from rest_framework.routers import DefaultRouter

from Backend.Apps.AtgDocs import views

router = DefaultRouter()
router.register("KnowledgeDocuments", views.KnowledgeDocumentViewSet, basename="docs-knowledge-documents")
router.register("KnowledgePermissions", views.KnowledgePermissionViewSet, basename="docs-knowledge-permissions")
router.register("KnowledgeActivities", views.KnowledgeActivityViewSet, basename="docs-knowledge-activities")
router.register("DriveFolders", views.DriveFolderViewSet, basename="docs-drive-folders")
router.register("DriveFiles", views.DriveFileViewSet, basename="docs-drive-files")
router.register("DocumentVersions", views.DocumentVersionViewSet, basename="docs-document-versions")

legacy_home = views.KnowledgeDocumentViewSet.as_view({"get": "library"})
legacy_create_post = views.KnowledgeDocumentViewSet.as_view({"post": "legacy_create_post"})
legacy_post_detail = views.KnowledgeDocumentViewSet.as_view({"get": "open_document"})
legacy_post_update = views.KnowledgeDocumentViewSet.as_view({"get": "retrieve", "post": "update_content", "put": "update_content", "patch": "update_content"})
legacy_my_posts = views.KnowledgeDocumentViewSet.as_view({"get": "my_documents"})
legacy_history = views.KnowledgeDocumentViewSet.as_view({"get": "visit_history"})

urlpatterns = [
	path("", legacy_home, name="docs_home"),
	path("create-post", legacy_create_post, name="post_create"),
	path("post-detail/<int:pk>", legacy_post_detail, name="post_detail"),
	path("post-update/<int:pk>", legacy_post_update, name="post_update"),
	path("myposts/", legacy_my_posts, name="my_posts"),
	path("history", legacy_history, name="history"),
] + router.urls
