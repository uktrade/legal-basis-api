from collections import MutableMapping
from typing import Dict, Generator, List, Optional

import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth


class MaxEmail:

    session: requests.Session

    def __init__(self, username, password):
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)

    def _make_request(self, rpc_call, **kwargs) -> MutableMapping:
        url = settings.MAXEMAIL_BASE_URL / rpc_call
        resp = self.session.post(url.tostr(), **kwargs)
        resp.raise_for_status()
        return resp.json()

    def all_lists(self) -> MutableMapping:
        return self._make_request("list", data={"method": "fetchAll"})

    def get_unsubscribe_list(self) -> Optional[MutableMapping]:
        for list_item in self.all_lists():
            if list_item["name"] == settings.MAXEMAIL_UNSUBSCRIBE_LIST_NAME:
                return list_item
        return None

    def get_members_for_list(self, list_id, limit=5000) -> Generator:
        """
        Generator yielding one record at a time for the given `list_id`

        It navigates through all pages with default limit of 5000 records per request
        """
        def get_members_for_page(list_id, offset=0, limit=5000) -> MutableMapping:
            return self._make_request(
                "list",
                data={
                    "method": "fetchRecipientsData",
                    "listId": list_id,
                    "profileFields": "[]",
                    "limit": limit,
                    "start": offset,
                    "sort": "update_ts",
                    "dir": "DESC",
                    "filter": "[]",
                },
            )

        def get_results(list_id)  -> Generator:
            pos = 0
            results = get_members_for_page(list_id, offset=0, limit=limit)
            num_records = int(results["list_total"])
            records: List[Dict] = []
            while pos < num_records:
                records = results["records"]
                yield records
                pos += int(results["count"])
                results = get_members_for_page(list_id, offset=pos, limit=limit)

        results = get_results(list_id)

        for record in results:
            yield from record
