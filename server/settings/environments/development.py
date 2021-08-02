from server.settings.environments.production import *  # noqa: 401,403


# We really don't want ecs logs in the console for development
for logger in LOGGING["loggers"]:  # noqa
    LOGGING["loggers"][logger]["handlers"] = ["console"]  # noqa


SECURE_SSL_REDIRECT_EXEMPT_HOSTNAMES = ("localhost",)
