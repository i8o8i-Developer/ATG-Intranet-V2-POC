from django.contrib import admin

from Backend.Apps.HtmlTemplate.models import ContentTemplate, GenericHtmlTemplate, OfferMacro, OfferTemplate, TemplateVariable


@admin.register(TemplateVariable)
class TemplateVariableAdmin(admin.ModelAdmin):
    list_display = ("key", "label", "tenant")
    search_fields = ("key", "label")


@admin.register(OfferMacro)
class OfferMacroAdmin(admin.ModelAdmin):
    list_display = ("name", "macro", "tenant")
    search_fields = ("name", "macro")


@admin.register(ContentTemplate)
class ContentTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "template_type", "offer_domain", "offer_type", "position", "status", "tenant")
    list_filter = ("template_type", "offer_domain", "offer_type", "status", "tenant")
    search_fields = ("name", "subject", "position")


@admin.register(OfferTemplate)
class OfferTemplateAdmin(admin.ModelAdmin):
    list_display = ("template", "position_title", "tenant")


@admin.register(GenericHtmlTemplate)
class GenericHtmlTemplateAdmin(admin.ModelAdmin):
    list_display = ("offer_domain", "offer_type", "position", "template", "tenant")
    list_filter = ("offer_domain", "offer_type", "tenant")