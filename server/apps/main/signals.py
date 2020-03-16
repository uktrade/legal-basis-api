from django.dispatch import receiver
from django.utils import timezone
from django_structlog.signals import bind_extra_request_metadata


@receiver(bind_extra_request_metadata)
def bind_extra_log_data(request, logger, **kwargs):
    logger.bind(
        b3=request.headers.get("B3"),
        x_b3_traceid=request.headers.get("X-B3-TraceId"),
        x_b3_spanid=request.headers.get("X-B3-SpanId"),
        request_id=request.headers.get("X-B3-TraceId"),
        sso_user_id=request.user.username,
        local_user_id=request.user.id,
        path=request.path,
        host=request.get_host(),
        service="Consent API",
        request_time=timezone.now().isoformat(),
    )
