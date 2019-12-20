from django.dispatch import receiver
from django_structlog.signals import bind_extra_request_metadata


@receiver(bind_extra_request_metadata)
def bind_cf_request_ids(request, logger, **kwargs):
    logger.bind(
        b3=request.headers.get('B3'),
        x_b3_traceid=request.headers.get('X-B3-TraceId'),
        x_b3_spanid=request.headers.get('X-B3-SpanId'),
        request_id=request.headers.get('X-B3-TraceId')
    )
