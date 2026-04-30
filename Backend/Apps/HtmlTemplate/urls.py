from rest_framework.routers import DefaultRouter

from Backend.Apps.HtmlTemplate import views

router = DefaultRouter()
router.register("TemplateVariables", views.TemplateVariableViewSet, basename="html-template-variables")
router.register("OfferMacros", views.OfferMacroViewSet, basename="html-offer-macros")
router.register("ContentTemplates", views.ContentTemplateViewSet, basename="html-content-templates")
router.register("OfferTemplates", views.OfferTemplateViewSet, basename="html-offer-templates")
router.register("GenericHtmlTemplates", views.GenericHtmlTemplateViewSet, basename="html-generic-templates")

urlpatterns = router.urls
