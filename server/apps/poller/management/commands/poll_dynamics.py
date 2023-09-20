from datetime import datetime, timedelta
from time import sleep

from actstream import action
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Model
from django.utils.functional import cached_property
from django_tqdm import BaseCommand

from server.apps.main.models import KEY_TYPE, Commit, Consent, LegalBasis
from server.apps.poller.api_client.dynamics import DynamicsClient

queryset = LegalBasis.objects.filter(current=True)


class Command(BaseCommand):
    help = """
    Start polling for dynamics subs.

    e.g. ./manage.py poll_dynamics
    """

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            "--forever",
            action="store_true",
            help="Run in a loop forever",
        )

        parser.add_argument(
            "--sleep-time",
            action="store",
            type=int,
            help="How long to sleep for (seconds), default: 60",
            default=60,
        )

    @cached_property
    def email_consent(self) -> Consent:
        email_consent, _ = Consent.objects.get_or_create(name="email_marketing")
        return email_consent

    @transaction.atomic()
    def update_consent(self, email_address, meta=None) -> None:
        self.write(f"Updating consent for {self._masked_email(email_address)}")
        if meta is None:
            meta = {}
        commit = Commit(extra=meta)
        commit.source = meta.get("url", settings.DYNAMICS_INSTANCE_URI)
        commit.save()

        self._update_email_consent(commit, email_address, False)

    @transaction.atomic()
    def create_consent(self, email_address, meta=None) -> None:
        self.write(f"Creating consent for {self._masked_email(email_address)}")
        if meta is None:
            meta = {}
        commit = Commit(extra=meta)
        commit.source = meta.get("url", settings.DYNAMICS_INSTANCE_URI)
        commit.save()

        self._update_email_consent(commit, email_address, True)

    @staticmethod
    def _masked_email(full_email: str) -> str:
        email_parts = full_email.split("@")
        if len(email_parts) > 1:
            return f"{email_parts[0][:2]}...@...{email_parts[1][-4:]}"
        return email_parts[0]

    def _send_action(self, instance: Model) -> None:
        dynamics_user, _ = get_user_model().objects.get_or_create(username="dynamics")
        action_kwargs = {
            "sender": dynamics_user,
            "action_object": instance,
            "verb": "Create",
        }
        action.send(**action_kwargs)

    def _update_email_consent(
        self, commit, email_address, email_contact_consent
    ) -> None:
        if email_address:
            obj: LegalBasis = LegalBasis(
                email=email_address, commit=commit, key_type=KEY_TYPE.EMAIL
            )
            obj.save()
            if email_contact_consent:
                obj.consents.add(self.email_consent)
            else:
                obj.consents.remove(self.email_consent)

            self._send_action(obj)

    def _should_update(self, email_address) -> bool:
        # check if there is already a legal basis for this email address
        try:
            lb: LegalBasis = queryset.get(email=email_address)
        except LegalBasis.DoesNotExist:
            return True

        # check if it is already opted out
        if self.email_consent in lb.consents.all():
            return True

        return False

    def _should_create(self, email_address) -> bool:
        return not queryset.filter(
            key_type=KEY_TYPE.EMAIL, email=email_address
        ).exists()

    def _sync_unsubs(self) -> None:
        self.write("Syncing unsubscribed users")
        client = DynamicsClient()
        record_count = update_count = 0
        for contact in client.get_unsubscribed_contacts():
            record_count += 1
            email_address = contact["emailaddress1"]
            self.write(
                f"Got unsubbed email address {self._masked_email(email_address)}"
            )
            if self._should_update(email_address):
                self.update_consent(email_address)
                update_count += 1
        self.write(f"Updated {update_count} records out of {record_count} in total")

    def _sync_unmanaged_users(self) -> None:
        self.write("Syncing unmanaged users")
        client = DynamicsClient()
        record_count = created_count = 0
        for contact in client.get_unmanaged_contacts(created_since_days=7):
            record_count += 1
            email_address = contact["emailaddress1"]
            self.write(
                f"Got unmanaged email address {self._masked_email(email_address)}"
            )
            # If this email address doesn't exist, create an opted in record for it
            if self._should_create(email_address):
                self.create_consent(email_address)
                created_count += 1

        self.write(f"Created {created_count} records out of {record_count} in total")

    def run(self, *args, **options) -> None:
        self._sync_unsubs()
        self._sync_unmanaged_users()

    def handle(self, *args, **options):
        run_forever = options.pop("forever")
        sleep_time = options.pop("sleep_time")

        if run_forever:
            while True:
                self.write("Polling dynamics 365")
                self.run(args, options)
                self.write(
                    f"sleeping until {datetime.now() + timedelta(seconds=sleep_time)}"
                )
                sleep(sleep_time)
        else:
            self.run(args, options)
