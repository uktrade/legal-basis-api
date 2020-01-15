from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Optional, Tuple, MutableMapping

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.response import Hit, Response


@dataclass # type: ignore
class ActivityStreamClient(ABC):

    name: ClassVar[str]
    es_client: Elasticsearch

    @abstractmethod
    def should_process(self, hit: Hit):
        raise NotImplementedError()

    @abstractmethod
    def get_documents(self, search_after) -> Response:
        raise NotImplementedError()

    @abstractmethod
    def parse_object_data(self, hit) -> MutableMapping:
        raise NotImplementedError()

    sort = (
        {"published": "asc"},
        {"id": "asc"}
    )

class FormsApi(ActivityStreamClient):

    name: ClassVar[str] = 'dit:directoryFormsApi:Submission'

    def should_process(self, hit: Hit) -> bool:
        if 'object' in hit:
            if f'{self.name}:Data' in hit.object:
                if 'email_contact_consent' in hit.object[f'{self.name}:Data']:
                    return True
        return False

    def parse_object_data(self, hit) -> MutableMapping:
        object_data = hit.object[f'{self.name}:Data']
        return object_data

    def get_documents(self, search_after: Optional[Tuple[int, str]]) -> Response:

        documents = Search(using=self.es_client, index='activities') \
            .filter('term', object__type=self.name) \
            .sort(*self.sort)

        if search_after:
            documents = documents.extra(search_after=search_after)

        return documents.execute()
