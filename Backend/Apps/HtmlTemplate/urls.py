from django.urls import path
from rest_framework.routers import DefaultRouter

from Backend.Apps.HtmlTemplate import views

router = DefaultRouter()
router.register("TemplateVariables", views.TemplateVariableViewSet, basename="html-template-variables")
router.register("OfferMacros", views.OfferMacroViewSet, basename="html-offer-macros")
router.register("ContentTemplates", views.ContentTemplateViewSet, basename="html-content-templates")
router.register("OfferTemplates", views.OfferTemplateViewSet, basename="html-offer-templates")
router.register("GenericHtmlTemplates", views.GenericHtmlTemplateViewSet, basename="html-generic-templates")

urlpatterns = [
	path("api/content-templates/create-template/", views.ContentTemplateCreateLegacyAPIView.as_view(), name="html-create-template"),
	path("api/content-templates/<int:pk>/render/", views.ContentTemplateRenderLegacyAPIView.as_view(), name="html-render-content-template"),
	path("api/generic-html-templates/sync-gtm-template/", views.GenericHtmlTemplateSyncLegacyAPIView.as_view(), name="html-sync-gtm-template"),
	path("api/generic-html-templates/sync-legacy-library/", views.GenericHtmlTemplateSyncLegacyLibraryAPIView.as_view(), name="html-sync-legacy-library"),
	path("api/generic-html-templates/<int:pk>/render/", views.GenericHtmlTemplateRenderLegacyAPIView.as_view(), name="html-render-generic-template"),
] + router.urls
