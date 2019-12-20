import os
import sys
import structlog

LOGLEVEL = os.environ.get('LOGLEVEL', 'info').upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    "formatters": {
        "json": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
        },
        "color": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(),
        },
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {message}',
            'style': '{',
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            'filters': ['require_debug_true'],
            "formatter": "color",
            "stream": sys.stdout
        },
        'django.server': {
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
            "stream": sys.stdout
        },
        "structlog": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": sys.stdout
        }
    },
    "loggers": {
        'django': {
            'handlers': ['console'],
            'level': LOGLEVEL
        },
        'django_structlog': {
            'handlers': ['structlog'],
            'level': LOGLEVEL
        },
        'django.server': {
            'handlers': ['django.server'],
            'level': LOGLEVEL,
            'propagate': False,
        },
    }
}

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
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=structlog.threadlocal.wrap_dict(dict),
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
