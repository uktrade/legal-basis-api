import argparse

import tablib
from dateutil.parser import parse
from django.utils.functional import cached_property
from django.utils.timezone import now
from django_tqdm import BaseCommand
from str2bool import str2bool

from server.apps.main.models import KEY_TYPE, Commit, Consent, LegalBasis


class Command(BaseCommand):
    help = """
    Start polling for forms api submissions in activity stream.

    csv columns should be:
    email,accepts_dit_email_marketing,modified_at

    e.g. ./manage.py import_email_consent filename.csv
    see server/apps/main/management/commands/example.csv for an example
    """

    def add_arguments(self, parser):
        parser.add_argument("csv", type=argparse.FileType("r"))

    @cached_property
    def email_consent(self):
        email_consent, _ = Consent.objects.get_or_create(name="email_marketing")
        return email_consent

    def _update_email_consent(
        self, commit, email_address, email_contact_consent, modified_at
    ) -> None:
        if email_address:
            obj: LegalBasis = LegalBasis(
                email=email_address,
                commit=commit,
                key_type=KEY_TYPE.EMAIL,
                modified_at=modified_at,
            )
            obj.save()
            if email_contact_consent:
                obj.consents.add(self.email_consent)
            else:
                obj.consents.remove(self.email_consent)

    def handle(self, *args, **options):
        input_csv = options["csv"]
        dataset = tablib.Dataset().load(input_csv)
        row_count = len(dataset)

        commit = Commit(
            extra={"import_time": now().isoformat(), "row_count": row_count}
        )

        commit.source = "management command: import_email_consent"
        commit.save()
        with self.tqdm(total=row_count) as progress_bar:
            for row in dataset.dict:
                self._update_email_consent(
                    commit,
                    row["email"],
                    str2bool(row["accepts_dit_email_marketing"]),
                    parse(row["modified_at"]),
                )
                progress_bar.update(1)
