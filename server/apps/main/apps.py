from django.apps import AppConfig


class MainConfig(AppConfig):
    name = 'server.apps.main'

    def ready(self):
        from server.apps.main import signals  # noqa: F401
