from datetime import datetime, timedelta, timezone
from pprint import pformat
from time import sleep

from actstream import action
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Model
from django.utils.functional import cached_property
from django_tqdm import BaseCommand
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearch_dsl.response import Hit
from phonenumber_field.phonenumber import PhoneNumber
from phonenumbers import NumberParseException
from requests_hawk import HawkAuth

from server.apps.main.models import KEY_TYPE, Commit, Consent, LegalBasis
from server.apps.poller.api_client.activity import FormsApi
from server.apps.poller.models import ActivityStreamType


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

    @cached_property
    def phone_consent(self) -> Consent:
        phone_consent, _ = Consent.objects.get_or_create(name="phone_marketing")
        return phone_consent

    def get_client(self) -> FormsApi:
        es_client = OpenSearch(
            http_auth=HawkAuth(
                id=settings.ACTIVITY_STREAM_ID, key=settings.ACTIVITY_STREAM_KEY
            ),
            connection_class=RequestsHttpConnection,
            port=443,
            use_ssl=True,
            host=settings.ACTIVITY_STREAM_URL.host,
            url_prefix=str(settings.ACTIVITY_STREAM_URL.path),
        )

        return FormsApi(es_client=es_client)

    def get_activity_instance(self, name: str) -> ActivityStreamType:
        obj, created = ActivityStreamType.objects.get_or_create(name=name)
        if created:
            print(f"First run for {name}. Creating model {obj}")
        return obj

    @transaction.atomic()
    def update_consent(self, object_data, meta) -> None:
        email_address = object_data.get("email_address", object_data.get("email"))
        email_contact_consent = object_data.get("email_contact_consent") or "consents_to_email_contact" in object_data.get("contact_consent", [])

        phone_number = object_data.get("phone_number")
        phone_number_country = object_data.get("country")
        phone_consent = object_data.get("telephone_contact_consent")

        commit = Commit(extra=meta)
        commit.source = meta["url"] or ''  # Not all forms API submissions have an URL
        commit.save()

        self._update_email_consent(
            commit,
            email_address,
            email_contact_consent,
            datetime.fromisoformat(meta["published"]).replace(tzinfo=timezone.utc),
        )

        self._update_phone_consent(
            commit, phone_consent, phone_number, phone_number_country
        )

    def _update_phone_consent(
        self, commit, phone_consent, phone_number, phone_number_country
    ) -> None:
        if phone_number:
            try:
                phone_number_parsed: PhoneNumber = PhoneNumber.from_string(
                    phone_number, region=phone_number_country
                )
                phone_number = phone_number_parsed.as_e164
            except NumberParseException:
                pass

            obj = LegalBasis(
                phone=phone_number, commit=commit, key_type=KEY_TYPE.PHONE,
            )
            obj.save()
            if phone_consent:
                obj.consents.add(self.phone_consent)
            else:
                obj.consents.remove(self.phone_consent)

            self._send_action(obj)

    def _send_action(self, instance: Model) -> None:
        User = get_user_model()
        directoryforms_user = User.objects.get(username="directoryforms")
        action_kwargs = {
            "sender": directoryforms_user,
            "action_object": instance,
            "verb": "Create",
        }
        action.send(**action_kwargs)

    def _update_email_consent(
        self, commit, email_address, email_contact_consent, hit_modified_at
    ) -> None:
        if email_address:
            obj: LegalBasis = LegalBasis(
                email=email_address,
                commit=commit,
                key_type=KEY_TYPE.EMAIL,
                modified_at=hit_modified_at,
            )
            obj.save()
            if email_contact_consent:
                obj.consents.add(self.email_consent)
            else:
                obj.consents.remove(self.email_consent)

            self._send_action(obj)

    def run(self, *args, **options) -> None:
        client = self.get_client()

        obj = self.get_activity_instance(client.name)
        results = client.get_documents(obj.search_after)
        total_hits = results.hits.total.value
        with self.tqdm(total=total_hits) as progress_bar:
            while len(results.hits):

                last_hit: Hit
                for hit in results:
                    if client.should_process(hit):
                        self.write(pformat(hit.to_dict()))
                        object_data = client.parse_object_data(hit)
                        meta = client.parse_object_meta(hit)
                        self.update_consent(object_data, meta)
                    progress_bar.update(1)

                obj.last_document_timestamp, obj.last_document_id = results.to_dict()[
                    "hits"
                ]["hits"][-1]["sort"]
                obj.save()

                results = client.get_documents(obj.search_after)

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
