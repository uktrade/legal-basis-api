"""
This file contains all the settings used in production.

This file is required and if development.py is present these
values are overridden.
"""
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from server.settings.components import env
from server.settings.components.common import INSTALLED_APPS

# Production flags:
# https://docs.djangoproject.com/en/2.2/howto/deployment/

DEBUG = False

ALLOWED_HOSTS = [env.str("DOMAIN_NAME"), ".apps.internal"]

# Elastic APM always opens a connection to the APM server, even
# if "disabled", so only enable it in production-like envs
INSTALLED_APPS += ("elasticapm.contrib.django",)

# Staticfiles
# https://docs.djangoproject.com/en/2.2/ref/contrib/staticfiles/
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

_PASS = "django.contrib.auth.password_validation"  # nosec noqa: S105
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "{0}.UserAttributeSimilarityValidator".format(_PASS)},
    {"NAME": "{0}.MinimumLengthValidator".format(_PASS)},
    {"NAME": "{0}.CommonPasswordValidator".format(_PASS)},
    {"NAME": "{0}.NumericPasswordValidator".format(_PASS)},
]


# Security
# https://docs.djangoproject.com/en/2.2/topics/security/

SECURE_HSTS_SECONDS = 31536000  # the same as Caddy has
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_SSL_REDIRECT = False
SECURE_SSL_REDIRECT_EXEMPT_HOSTNAMES = (r"\.apps\.internal:8080$",)

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SENTRY_DSN = env.str("SENTRY_DSN", default=None)

if SENTRY_DSN is not None:
    sentry_sdk.hub.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        send_default_pii=True,
    )
