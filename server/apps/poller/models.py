from typing import Optional, Tuple

from django.db import models
from typing_extensions import final


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
