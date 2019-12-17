from django.dispatch import receiver
from django_structlog.signals import bind_extra_request_metadata


@receiver(bind_extra_request_metadata)
def bind_cf_request_ids(request, logger, **kwargs):
    logger.bind(**{
        'X-B3-TraceId': request.headers.get('X-B3-TraceId'),
        'X-B3-SpanId': request.headers.get('X-B3-SpanId'),
    })
