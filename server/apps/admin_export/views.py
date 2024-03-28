import csv
from typing import Iterator, List

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import QuerySet
from django.http import StreamingHttpResponse
from django.views import View

from server.apps.main.models import LegalBasis


class Echo:
    """
    An object that implements just the write method of the file-like
    interface.
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


class ExportLegalBasisCSV(View):
    http_method_names = ["get"]

    def get(self, request) -> StreamingHttpResponse:
        return StreamingHttpResponse(
            (self.iter_items(self.get_queryset(), Echo())),
            content_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="legal_basis.csv"'},
        )

    def iter_items(self, items, pseudo_buffer) -> Iterator[str]:
        """Writes the values including the headings for the StreamingHttpResponse."""
        writer = csv.DictWriter(pseudo_buffer, fieldnames=self.get_columns())
        yield pseudo_buffer.write(f"{','.join(self.get_columns())}\n")

        for item in items:
            yield writer.writerow(item)

    def get_queryset(self) -> QuerySet:
        """Returns a list of LegalBasis data for CSV export."""
        return (
            LegalBasis.objects.select_related("commit")
            .prefetch_related("consents")
            .annotate(
                consents_name=ArrayAgg("consents__name"),
                consents_description=ArrayAgg("consents__description"),
            )
            .values(*self.get_columns())
        )

    def get_columns(self) -> List[str]:
        """Values for the LegalBasis table, also used for CSV headers."""
        return [
            "email",
            "phone",
            "key_type",
            "created_at",
            "modified_at",
            "current",
            "commit__created_at",
            "commit__source",
            "commit__extra",
            "consents_name",
            "consents_description",
        ]
