from server.settings.environments.production import *  # noqa: 401,403

from server.settings.components.common import INSTALLED_APPS


INSTALLED_APPS += (
    "django_extensions",
    "django_migration_linter",
)

SECURE_SSL_REDIRECT = False
