from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Backend.Apps.Users"
    label = "Users"
    verbose_name = "Users"

    def ready(self):
        from Backend.Apps.Users import signals  # noqa: F401
