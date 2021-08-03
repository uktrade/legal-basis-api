import os
import sys

import structlog

from django_log_formatter_ecs import ECSFormatter

LOGLEVEL = os.environ.get("LOGLEVEL", "info").upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse",},
        "require_debug_true": {"()": "django.utils.log.RequireDebugTrue",},
    },
    "formatters": {
        "ecs_formatter": {"()": ECSFormatter},
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[{server_time}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["require_debug_true"],
            "stream": sys.stdout,
        },
        "ecs": {
            "class": "logging.StreamHandler",
            "formatter": "ecs_formatter",
            # "stream": sys.stdout,
        },
    },
    "loggers": {
        "django": {"handlers": ["ecs"], "level": LOGLEVEL},
        "django.server": {"handlers": ["ecs"], "level": LOGLEVEL, "propagate": False,},
        "": {"handlers": ["ecs"], "level": LOGLEVEL, "propagate": False,},
    },
}


def remove_host(_, __, event_dict):
    # The 'host' key seems to be a string, but according to ECS, should be
    # an object. It's easiest to just delete it since it doesn't seem useful
    event_dict.pop("host", None)
    return event_dict


structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.ExceptionPrettyPrinter(),
        remove_host,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=structlog.threadlocal.wrap_dict(dict),
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
