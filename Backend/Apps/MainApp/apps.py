from django.apps import AppConfig


class MainAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Backend.Apps.MainApp"
    label = "MainApp"
    verbose_name = "Main App"
