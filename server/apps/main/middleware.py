import logging
import uuid
from typing import Callable, Dict, List, Optional

from actstream import action
from django.db.models import Model
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.http import HttpRequest, HttpResponse

from server.apps.main.models import Consent, LegalBasis

logger = logging.getLogger(__name__)


class AuditLogMiddleware:
    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request) -> HttpResponse:

        signal_calls = self.get_signal_calls(request)

        for call in signal_calls:
            call["signal"].connect(weak=False, **call["kwargs"])

        response = self.get_response(request)

        for call in signal_calls:
            call["signal"].disconnect(**call["kwargs"])

        return response

    def get_signal_calls(self, request: HttpRequest) -> List[Dict]:
        return [
            {
                "signal": post_save,
                "kwargs": {
                    "sender": LegalBasis,
                    "receiver": self.make_save_signal_receiver(request),
                    "dispatch_uid": uuid.uuid4(),
                },
            },
            {
                "signal": post_delete,
                "kwargs": {
                    "sender": LegalBasis,
                    "receiver": self.make_delete_signal_receiver(request),
                    "dispatch_uid": uuid.uuid4(),
                },
            },
            {
                "signal": m2m_changed,
                "kwargs": {
                    "sender": LegalBasis.consents.through,
                    "receiver": self.make_m2m_signal_receiver(request),
                    "dispatch_uid": uuid.uuid4(),
                },
            },
        ]

    def make_m2m_signal_receiver(self, request: HttpRequest) -> Callable:
        def inner(sender: Model, **kwargs) -> None:
            action_kwargs = {
                "sender": request.user,
                "remote_addr": self.get_remote_addr(request),
            }

            if kwargs["action"] in ["post_add", "post_remove"]:
                self.handle_m2m_post_add_remove_actions(
                    instance=kwargs["instance"],
                    action_kwargs=action_kwargs,
                    action_name=kwargs["action"],
                    pk_set=kwargs["pk_set"],
                )

            if kwargs["action"] == "post_clear":
                self.handle_m2m_post_clear_action(
                    instance=kwargs["instance"], action_kwargs=action_kwargs
                )

        return inner

    def handle_m2m_post_add_remove_actions(
        self, instance: Model, action_kwargs: Dict, action_name: str, pk_set: List
    ) -> None:
        for pk in pk_set:
            action_kwargs["verb"] = "added" if action_name == "post_add" else "removed"
            action_kwargs["action_object"] = Consent.objects.get(pk=pk)
            action_kwargs["target"] = instance

            action.send(**action_kwargs)
            logger.info(f"Action sent: {action_kwargs}")

    def handle_m2m_post_clear_action(
        self, instance: Model, action_kwargs: Dict
    ) -> None:
        action_kwargs["verb"] = "cleared consents"
        action_kwargs["action_object"] = instance

        action.send(**action_kwargs)
        logger.info(f"Action sent: {action_kwargs}")

    def make_save_signal_receiver(self, request: HttpRequest) -> Callable:
        def inner(sender: Model, **kwargs) -> None:
            action_kwargs = {
                "sender": request.user,
                "action_object": kwargs["instance"],
                "verb": "created" if kwargs.get("created") is True else "updated",
                "remote_addr": self.get_remote_addr(request),
            }

            action.send(**action_kwargs)
            logger.info(f"Action sent: {action_kwargs}")

        return inner

    def make_delete_signal_receiver(self, request: HttpRequest) -> Callable:
        def inner(sender: Model, **kwargs) -> None:
            action_kwargs = {
                "sender": request.user,
                "action_object": kwargs["instance"],
                "verb": "deleted",
                "remote_addr": self.get_remote_addr(request),
            }

            action.send(**action_kwargs)
            logger.info(f"Action sent: {action_kwargs}")

        return inner

    def get_remote_addr(self, request: HttpRequest) -> Optional[str]:
        remote_addr = request.META.get("HTTP_X_FORWARDED_FOR")
        if remote_addr is not None:
            return remote_addr.split(",")[0]
        return request.META.get("REMOTE_ADDR")
