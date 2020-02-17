import json
from typing import Dict, List

from actstream.feeds import ModelJSONActivityFeed
from actstream.models import Action
from cursor_pagination import CursorPaginator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest
from django.urls import reverse
from django.utils.feedgenerator import rfc3339_date


class W3CModelJSONActivityFeed(
    LoginRequiredMixin, UserPassesTestMixin, ModelJSONActivityFeed
):
    # raise_exception = True
    id_prefix = ["dit", "ConsentAPI"]

    def test_func(self):
        return True

    def get_action_id(self, parts: List) -> str:
        """
        Returns an RFC3987 IRI ID for the given object, action and date.
        """
        return ":".join([str(i) for i in self.id_prefix + parts])

    def format(self, action: Action) -> Dict:
        """
        Returns a formatted dictionary for the given action.
        """
        item = {
            "id": self.get_action_id(
                [
                    action.action_object.__class__.__name__,
                    action.action_object_object_id,
                    action.verb,
                ]
            ),
            "type": action.verb,
            "published": rfc3339_date(action.timestamp),
            "actor": self.format_actor(action),
            "name": str(action),
        }
        if action.description:
            item["content"] = action.description
        if action.target:
            item["target"] = self.format_target(action)
        if action.action_object:
            item["object"] = self.format_action_object(action)
        return item

    def format_item(self, action: Action, item_type="actor") -> Dict:
        """
        Returns a formatted dictionary for an individual item based on the action and item_type.
        """
        obj = getattr(action, item_type)
        obj_type = obj.__class__.__name__
        return {
            "id": self.get_action_id([obj_type, obj.pk]),
            "type": self.get_action_id([obj_type]),
            "name": str(obj),
        }

    def serialize(self, request: HttpRequest, *args, **kwargs) -> str:
        """
        Returns JSON activity stream as per W3C Activity Stream 2.0 spec,
        with cursor-based pagination
        """
        items = self.items(request, *args, **kwargs)

        page_size = 10
        paginator = CursorPaginator(items, ordering=("-timestamp", "-id"))
        page = paginator.page(first=page_size, after=request.GET.get("cursor"))

        response = {
            "@context": [
                "https://www.w3.org/ns/activitystreams",
                {"dit": "https://www.trade.gov.uk/ns/activitystreams/v1"},
            ],
            "type": "Collection",
            "totalItems": items.count(),
            "orderedItems": [self.format(item) for item in page],
        }

        if page.has_next:
            url = reverse("actstream_model_feed_json", kwargs=kwargs)
            response["next"] = f"{url}?cursor={paginator.cursor(page[-1])}"

        return json.dumps(response, indent=4 if "pretty" in request.GET else None)
