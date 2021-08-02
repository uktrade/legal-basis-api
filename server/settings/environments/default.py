"""
This file contains all the settings that defines the development server.

SECURITY WARNING: don't run with debug turned on in production!
"""

import logging
from typing import List

from server.settings.components import env
from server.settings.components.common import INSTALLED_APPS, MIDDLEWARE
from server.settings.components.logging import LOGGING

# Setting the development status:

DEBUG = True

ALLOWED_HOSTS = [env.str("DOMAIN_NAME"), "localhost", "127.0.0.1", "[::1]"]


# Installed apps for developement only:
INSTALLED_APPS = ("whitenoise.runserver_nostatic",) + INSTALLED_APPS

INSTALLED_APPS += (
    "django_extensions",
    "debug_toolbar",
    "nplusone.ext.django",
    "django_migration_linter",
)


# Static files:
# https://docs.djangoproject.com/en/2.2/ref/settings/#std:setting-STATICFILES_DIRS

STATICFILES_DIRS: List[str] = []


# Django debug toolbar:
# https://django-debug-toolbar.readthedocs.io

MIDDLEWARE += (
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    # https://github.com/bradmontgomery/django-querycount
    # Prints how many queries were executed, useful for the APIs.
    "querycount.middleware.QueryCountMiddleware",
)


def custom_show_toolbar(request):
    """Only show the debug toolbar to users with the superuser flag."""
    return request.user.is_superuser


DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": "server.settings.environments.default.custom_show_toolbar"
}

# This will make debug toolbar to work with django-csp,
# since `ddt` loads some scripts from `ajax.googleapis.com`:
CSP_SCRIPT_SRC = ("'self'", "ajax.googleapis.com")
CSP_IMG_SRC = ("'self'", "data:")


# nplusone
# https://github.com/jmcarp/nplusone

# Should be the first in line:
MIDDLEWARE = ("nplusone.ext.django.NPlusOneMiddleware",) + MIDDLEWARE  # noqa: WPS440

# Logging N+1 requests:
# NPLUSONE_RAISE = True  # comment out if you want to allow N+1 requests
NPLUSONE_LOGGER = logging.getLogger("django")
NPLUSONE_LOG_LEVEL = logging.WARN

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "http")
