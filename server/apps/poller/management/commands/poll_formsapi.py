from datetime import datetime, timedelta
from pprint import pformat
from time import sleep

from django.conf import settings
from django.utils.functional import cached_property
from django_tqdm import BaseCommand
from elasticsearch import Elasticsearch, RequestsHttpConnection
from elasticsearch_dsl.response import Hit
from requests_hawk import HawkAuth

from server.apps.main.models import Consent, LegalBasis
from server.apps.poller.clients import FormsApi
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

    def get_client(self) -> FormsApi:
        es_client = Elasticsearch(
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

    def update_consent(self, object_data) -> None:
        email_address = object_data["email_address"]
        email_contact_consent = object_data["email_contact_consent"]

        obj: LegalBasis
        obj, _ = LegalBasis.objects.get_or_create(email=email_address)

        if email_contact_consent:
            obj.consents.add(self.email_consent)
        else:
            obj.consents.remove(self.email_consent)

    def run(self, *args, **options) -> None:
        client = self.get_client()

        obj = self.get_activity_instance(client.name)
        results = client.get_documents(obj.search_after)

        with self.tqdm(total=results.hits.total) as progress_bar:
            while len(results.hits):

                last_hit: Hit
                for hit in results:
                    if client.should_process(hit):
                        self.write(pformat(hit.to_dict()))
                        object_data = client.parse_object_data(hit)
                        self.update_consent(object_data)
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
