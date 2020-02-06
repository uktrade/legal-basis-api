import uuid
from typing import Callable, Dict, List, Optional

from actstream import action
from django.db.models import Model
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.http import HttpRequest, HttpResponse
from typing_extensions import final

from server.apps.main.models import Consent, LegalBasis


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

    @final
    def get_signal_calls(self, request: HttpRequest) -> List[Dict]:
        m2m_through = LegalBasis.consents.through

        return [
            {
                "signal": signal,
                "kwargs": {
                    "sender": sender,
                    "receiver": receiver,
                    "dispatch_uid": uuid.uuid4(),
                },
            }
            for signal, sender, receiver in [
                (post_save, LegalBasis, self.make_save_signal_receiver(request),),
                (post_delete, LegalBasis, self.make_delete_signal_receiver(request),),
                (m2m_changed, m2m_through, self.make_m2m_signal_receiver(request),),
            ]
        ]

    @final
    def make_m2m_signal_receiver(self, request: HttpRequest) -> Callable:
        def inner(sender: Model, **kwargs) -> None:
            action_kwargs = {
                "sender": request.user,
                "action_object": kwargs["instance"],
                "remote_addr": self.get_remote_addr(request),
            }

            if kwargs["action"] in ["post_add", "post_remove"]:
                for pk in kwargs["pk_set"]:
                    action_kwargs["verb"] = (
                        "added" if kwargs["action"] == "post_add" else "removed"
                    )
                    action_kwargs["target"] = Consent.objects.get(pk=pk)

                    action.send(**action_kwargs)
                    print(f"Action sent: {action_kwargs}")

            if kwargs["action"] == "post_clear":
                action_kwargs["verb"] = "cleared consents"

                action.send(**action_kwargs)
                print(f"Action sent: {action_kwargs}")

        return inner

    @final
    def make_save_signal_receiver(self, request: HttpRequest) -> Callable:
        def inner(sender: Model, **kwargs) -> None:
            action_kwargs = {
                "sender": request.user,
                "action_object": kwargs["instance"],
                "verb": "created" if kwargs.get("created") is True else "updated",
                "remote_addr": self.get_remote_addr(request),
            }

            action.send(**action_kwargs)
            print(f"Action sent: {action_kwargs}")

        return inner

    @final
    def make_delete_signal_receiver(self, request: HttpRequest) -> Callable:
        def inner(sender: Model, **kwargs) -> None:
            action_kwargs = {
                "sender": request.user,
                "action_object": kwargs["instance"],
                "verb": "deleted",
                "remote_addr": self.get_remote_addr(request),
            }

            action.send(**action_kwargs)
            print(f"Action sent: {action_kwargs}")

        return inner

    @final
    def get_remote_addr(self, request: HttpRequest) -> Optional[str]:
        remote_addr = request.META.get("HTTP_X_FORWARDED_FOR")
        if remote_addr is not None:
            return remote_addr.split(",")[0]
        return request.META.get("REMOTE_ADDR")
