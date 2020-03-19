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
from server.apps.poller.api_client.maxemail import MaxEmail

queryset = LegalBasis.objects.filter(current=True)


class Command(BaseCommand):
    help = """
    Start polling for forms api submissions in activity stream.

    e.g. ./manage.py poll_formsapi
    """

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            "--forever", action="store_true", help="Run in a loop forever",
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

    def get_client(self) -> MaxEmail:
        return MaxEmail(settings.MAXEMAIL_USERNAME, settings.MAXEMAIL_PASSWORD)  # type: ignore

    @transaction.atomic()
    def update_consent(self, email_address, meta=None) -> None:
        self.write("Updating consent")
        if meta is None:
            meta = {}
        commit = Commit(extra=meta)
        commit.source = meta.get("url", settings.MAXEMAIL_BASE_URL)
        commit.save()

        self._update_email_consent(commit, email_address, False)

    def _send_action(self, instance: Model) -> None:
        User = get_user_model()
        maxemail_user, _ = User.objects.get_or_create(username="maxemail")
        action_kwargs = {
            "sender": maxemail_user,
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

    def run(self, *args, **options) -> None:
        client = self.get_client()

        unsub_list_id = self._get_unsub_list_id(client)

        results = client.get_members_for_list(unsub_list_id)
        total = int(results["list_total"])

        with self.tqdm(total=total) as progress_bar:
            while progress_bar.n < progress_bar.total:

                for hit in results["records"]:
                    email_address = hit["email_address"]
                    if self._should_update(email_address):
                        self.update_consent(email_address)
                    progress_bar.update(1)
                results = client.get_members_for_list(
                    unsub_list_id, start=progress_bar.n
                )

    def _get_unsub_list_id(self, client) -> str:
        unsub_list = client.get_unsubscribe_list()
        if unsub_list:
            unsub_list_id = unsub_list["list_id"]
        else:
            raise Exception("Cannot find unsubscribe list")
        return unsub_list_id

    def handle(self, *args, **options):
        run_forever = options.pop("forever")
        sleep_time = options.pop("sleep_time")

        if run_forever:
            while True:
                self.write("Polling activity stream")
                self.run(args, options)
                self.write(f"sleeping until {datetime.now() + timedelta(seconds=60)}")
                sleep(sleep_time)
        else:
            self.run(args, options)
