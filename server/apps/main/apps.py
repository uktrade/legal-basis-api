from django.apps import AppConfig


class MainConfig(AppConfig):
    name = "server.apps.main"

    def ready(self):
        from server.apps.main import signals  # noqa: F401
        from actstream import registry  # noqa: F401
        from django.contrib.auth.models import User

        registry.register(self.get_model("Consent"))
        registry.register(self.get_model("LegalBasis"))
        registry.register(User)
