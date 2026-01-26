from django.apps import AppConfig


class GroupMakerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.group_maker"

    def ready(self):
        # Import signals to register them
        from . import signals  # noqa: F401
