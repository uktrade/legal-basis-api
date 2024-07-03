from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Optional, Tuple

from opensearchpy import OpenSearch
from opensearch_dsl import Search
from opensearch_dsl.response import Hit, Response


@dataclass
class ActivityStreamClient(ABC):

    name: ClassVar[str]
    es_client: OpenSearch

    @abstractmethod
    def should_process(self, hit: Hit):
        raise NotImplementedError()

    @abstractmethod
    def get_documents(self, search_after) -> Response:
        raise NotImplementedError()

    @abstractmethod
    def parse_object_data(self, hit) -> dict:
        raise NotImplementedError()

    sort = ({"published": "asc"}, {"id": "asc"})


class FormsApi(ActivityStreamClient):

    name: ClassVar[str] = "dit:directoryFormsApi:Submission"

    def should_process(self, hit: Hit) -> bool:
        if "object" in hit:
            if f"{self.name}:Data" in hit.object:
                data = hit.object[f"{self.name}:Data"]
                if "email_contact_consent" in data or "contact_consent" in data:
                    return True
                # if "phone_number" in data:
                #     return True
        return False

    def _parse_object_key(self, hit, key) -> dict:
        return hit.object[key].to_dict()

    def parse_object_data(self, hit) -> dict:
        return self._parse_object_key(hit, f"{self.name}:Data")

    def parse_object_meta(self, hit) -> dict:
        data = hit.to_dict()
        filtered = {
            "id": data["id"],
            "published": data["published"],
            "url": data.get("object", {}).get("url", ""),
        }
        return filtered

    def get_documents(self, search_after: Optional[Tuple[int, str]]) -> Response:

        documents = (
            Search(using=self.es_client, index="activities")
            .filter("term", object__type=self.name)
            .sort(*self.sort)
        )

        if search_after:
            documents = documents.extra(search_after=search_after)

        return documents.execute()
