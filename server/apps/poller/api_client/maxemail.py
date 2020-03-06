import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth


class MaxEmail:

    session: requests.Session

    def __init__(self, username, password):
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)

    def _make_request(self, rpc_call, **kwargs):
        url = settings.MAXEMAIL_BASE_URL / rpc_call
        resp = self.session.post(url.tostr(), **kwargs)
        resp.raise_for_status()
        return resp.json()

    def all_lists(self):
        return self._make_request("list", data={"method": "fetchAll"})

    def get_unsubscribe_list(self):
        for list_item in self.all_lists():
            if list_item["name"] == settings.MAXEMAIL_UNSUBSCRIBE_LIST_NAME:
                return list_item

    def get_members_for_list(self, list_id, start=0, limit=5000):
        return self._make_request(
            "list",
            data={
                "method": "fetchRecipientsData",
                "listId": list_id,
                "profileFields": "[]",
                "limit": limit,
                "start": start,
                "sort": "update_ts",
                "dir": "DESC",
                "filter": "[]",
            },
        )
