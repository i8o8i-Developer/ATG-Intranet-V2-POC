from django.apps import AppConfig


class LegacyBridgeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Backend.Apps.LegacyBridge"
    label = "LegacyBridge"
    verbose_name = "Legacy Bridge"
