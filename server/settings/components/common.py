"""
Django settings for server project.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their config, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
from typing import Dict, List, Tuple, Union

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as ugt
from furl import furl

from server.settings.components import BASE_DIR, env

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

SECRET_KEY = env.str("DJANGO_SECRET_KEY")

# create required env vars from CloudFoundry VCAP_SERVICES json env var
VCAP_SERVICES = env.json("VCAP_SERVICES", {})

if "REDIS_URL" not in os.environ:
    try:
        os.environ["REDIS_URL"] = VCAP_SERVICES["redis"][0]["credentials"]["uri"]
    except (KeyError, IndexError):
        pass

# Application definition:

INSTALLED_APPS: Tuple[str, ...] = (
    # Your apps go here:
    "server.apps.main",
    "server.apps.api",
    "server.apps.poller",
    # 3rd party django apps
    "rest_framework",
    "rest_framework.authtoken",
    "drf_yasg",
    "django_filters",
    # Default django apps:
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # django-admin:
    "django.contrib.admin",
    "django.contrib.admindocs",
    # Security:
    "axes",
    # Health checks:
    # You may want to enable other checks as well,
    # see: https://github.com/KristianOellegaard/django-health-check
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
    # Third party apps
    "django_http_referrer_policy",
    "hawkrest",
    "authbroker_client",
    # Activity Stream
    "actstream",
)

MIDDLEWARE: Tuple[str, ...] = (
    "allow_cidr.middleware.AllowCIDRMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # Content Security Policy:
    "csp.middleware.CSPMiddleware",
    # SSL redirect hostname exemptions
    "server.apps.main.middleware.SslRedirectExemptHostnamesMiddleware",
    # Django:
    "django.middleware.security.SecurityMiddleware",
    "django_feature_policy.FeaturePolicyMiddleware",  # django-feature-policy
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # ours
    "server.apps.main.middleware.AuditLogMiddleware",
    "server.apps.main.middleware.NeverCacheMiddleware",
    # hawk rest
    "hawkrest.middleware.HawkResponseMiddleware",
    # Django HTTP Referrer Policy:
    "django_http_referrer_policy.middleware.ReferrerPolicyMiddleware",
    "django_structlog.middlewares.RequestMiddleware",
    # Axes:
    "axes.middleware.AxesMiddleware",
)

ROOT_URLCONF = "server.urls"

WSGI_APPLICATION = "server.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases


DATABASES = {
    "default": env.db(),
}

# Django Sites
SITE_ID = 1

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en-gb"

USE_I18N = True
USE_L10N = False

LANGUAGES = (("en", ugt("English")),)

LOCALE_PATHS = ("locale/",)

USE_TZ = True
TIME_ZONE = "UTC"


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATIC_URL = "/static/"

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)


# Templates
# https://docs.djangoproject.com/en/2.2/ref/templates/api

TEMPLATES = [
    {
        "APP_DIRS": True,
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            # Contains plain text templates, like `robots.txt`:
            BASE_DIR.joinpath("server", "templates"),
        ],
        "OPTIONS": {
            "context_processors": [
                # Default template context processors:
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ],
        },
    }
]


# Media files
# Media root dir is commonly changed in production
# (see development.py and production.py).
# https://docs.djangoproject.com/en/2.2/topics/files/

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR.joinpath("media")


# Django authentication system
# https://docs.djangoproject.com/en/2.2/topics/auth/

AUTHENTICATION_BACKENDS = (
    "axes.backends.AxesBackend",
    "django.contrib.auth.backends.ModelBackend",
    "authbroker_client.backends.AuthbrokerBackend",
    "server.apps.main.auth.HawkUserAuthentication",
)

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.BCryptPasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.Argon2PasswordHasher",
]

# Sessions
SESSION_ENGINE = "django.contrib.sessions.backends.cache"


# Security
# https://docs.djangoproject.com/en/2.2/topics/security/

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

X_FRAME_OPTIONS = "DENY"

# https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Referrer-Policy#Syntax
REFERRER_POLICY = "same-origin"

# https://github.com/adamchainz/django-feature-policy#setting
FEATURE_POLICY: Dict[str, Union[str, List[str]]] = {}  # noqa: TAE002


# Timeouts
EMAIL_TIMEOUT = 5

# Authbroker
AUTHBROKER_URL = env.url("AUTHBROKER_URL").geturl()
AUTHBROKER_CLIENT_ID = env.str("AUTHBROKER_CLIENT_ID")
AUTHBROKER_CLIENT_SECRET = env.str("AUTHBROKER_CLIENT_SECRET")

LOGIN_URL = reverse_lazy("authbroker_client:login")
LOGIN_REDIRECT_URL = reverse_lazy("admin:index")

INTERNAL_IPS = ("127.0.0.1",)

# Activity Stream Credentials
ACTIVITY_STREAM_URL = env("ACTIVITY_STREAM_URL", cast=furl)
ACTIVITY_STREAM_KEY = env.str("ACTIVITY_STREAM_KEY")
ACTIVITY_STREAM_ID = env.str("ACTIVITY_STREAM_ID")

# This app's Activity Stream config
ACTSTREAM_SETTINGS = {
    "USE_JSONFIELD": True,
}

# libphonenumber
PHONENUMBER_DEFAULT_REGION = env.str("PHONENUMBER_DEFAULT_REGION", default="GB")

MAXEMAIL_BASE_URL = env("MAXEMAIL_BASE_URL", cast=furl)
MAXEMAIL_USERNAME = env.str("MAXEMAIL_USERNAME")
MAXEMAIL_PASSWORD = env.str("MAXEMAIL_PASSWORD")
MAXEMAIL_UNSUBSCRIBE_LIST_NAME = env.str(
    "MAXEMAIL_UNSBUSCRIBE_LIST_NAME", default="Master Unsubscribe List"
)


# Whitenoise
def add_whitenoise_headers(headers, _path, _url):
    """
    add security headers to static files
    """
    headers["Cache-Control"] = "no-cache, no-store, must-revalidate, private"
    headers["Pragma"] = "no-cache"
    headers["X-Content-Type-Options"] = "nosniff"
    headers["X-Frame-Options"] = "DENY"
    headers["X-XSS-Protection"] = "1; mode=block"


WHITENOISE_ADD_HEADERS_FUNCTION = add_whitenoise_headers

# Elastic APM
ELASTIC_APM = {
    "SERVICE_NAME": "Consent API",
    "SECRET_TOKEN": env.str("ELASTIC_APM_SECRET_TOKEN", default=None),
    "SERVER_URL": "https://apm.elk.uktrade.digital",
    "ENVIRONMENT": env.str("DJANGO_ENV"),
}

# django-allow-cidr
ALLOWED_CIDR_NETS = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
SECURE_SSL_REDIRECT_EXEMPT_HOSTNAMES = ()
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CONSENT_TYPES = ("email_marketing", "phone_marketing")

# Adobe Campaigns

ADOBE_PRIVATE_KEY = env.str('ADOBE_PRIVATE_KEY', '').replace('~~', """
""")
ADOBE_API_KEY = env.str('ADOBE_API_KEY', '')
ADOBE_API_ID = env.str('ADOBE_API_ID', '')
ADOBE_API_SECRET = env.str('ADOBE_API_SECRET', '')
ADOBE_TENANT_ID = env.str('ADOBE_TENANT_ID', '')
ADOBE_ORGANISATION_ID = env.str('ADOBE_ORGANISATION_ID', '')
ADOBE_TECHNICAL_ACCOUNT_ID = env.str('ADOBE_TECHNICAL_ACCOUNT_ID', '')
ADOBE_CAMPAIGN_BASE_URL = env.str('ADOBE_CAMPAIGN_BASE_URL', 'adobe_campaign')
ADOBE_STAGING_WORKFLOW = env.str('ADOBE_UNSUB_WORKFLOW', 'WKF29')
