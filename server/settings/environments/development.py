from server.settings.environments.production import *  # noqa: 401,403

# Uncomment to have plain text logging locally
# LOGGING["loggers"]["django_structlog"]["handlers"] = ["console"]  # type: ignore

SECURE_SSL_REDIRECT_EXEMPT_HOSTNAMES = ("localhost",)
