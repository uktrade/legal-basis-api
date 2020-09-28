from typing import Optional, Tuple
from django.db import models
from typing_extensions import final
from server.apps.poller.api_client.adobe import AdobeClient

@final
class ActivityStreamType(models.Model):

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()

    last_document_id = models.TextField()
    last_document_timestamp = models.BigIntegerField(null=True)

    @property
    def search_after(self) -> Optional[Tuple[int, str]]:
        if self.last_document_timestamp and self.last_document_id:
            return (self.last_document_timestamp, self.last_document_id)
        return None

    def __str__(self) -> str:
        return f"{self.name}"


class AdobeCampaign(models.Model):
    """
    A campaign service in Adobe campaign.
    """
    pkey = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=500, null=True, blank=True)
    last_fetched_at = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.name} [{self.pkey}]"

    def fetch_details(self):
        client = AdobeClient()
        service = client.get_service(self.pkey)
        self.name = service.get('title')
        self.save()