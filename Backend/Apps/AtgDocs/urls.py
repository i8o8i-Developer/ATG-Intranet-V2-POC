from rest_framework.routers import DefaultRouter

from Backend.Apps.AtgDocs import views

router = DefaultRouter()
router.register("KnowledgeDocuments", views.KnowledgeDocumentViewSet, basename="docs-knowledge-documents")
router.register("KnowledgePermissions", views.KnowledgePermissionViewSet, basename="docs-knowledge-permissions")
router.register("KnowledgeActivities", views.KnowledgeActivityViewSet, basename="docs-knowledge-activities")
router.register("DriveFolders", views.DriveFolderViewSet, basename="docs-drive-folders")
router.register("DriveFiles", views.DriveFileViewSet, basename="docs-drive-files")
router.register("DocumentVersions", views.DocumentVersionViewSet, basename="docs-document-versions")

urlpatterns = router.urls
