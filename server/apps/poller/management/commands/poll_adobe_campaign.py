import logging
from datetime import datetime, timedelta
from time import sleep

from actstream import action
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Model, QuerySet
from django.utils import timezone
from django.utils.functional import cached_property
from django_tqdm import BaseCommand

from server.apps.main.models import KEY_TYPE, Commit, Consent, LegalBasis
from server.apps.poller.api_client.adobe import AdobeClient
from server.apps.poller.models import AdobeCampaign

queryset = LegalBasis.objects.filter(current=True)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Start polling for Adobe campaign subscriptions and unsubscriptions
    The campaigns to track should be set up in the AdobeCampaign model.

    The process will:
    1. For each adobe current subscription, verify that consent is still given, and unsubscribe if not.
    2. Kick off the Adobe workflow to generate unsubscription details, and for each adobe unsubscription, remove consent.

    e.g. ./manage.py poll_adobe_campaign
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


    @transaction.atomic()
    def update_consent(self, email_address, meta=None, consent=True) -> None:
        if meta is None:
            meta = {}
        commit = Commit(extra=meta)
        commit.source = meta.get("url", settings.ADOBE_CAMPAIGN_BASE_URL)
        commit.save()

        self._update_email_consent(commit, email_address, consent)

    def _send_action(self, instance: Model) -> None:
        User = get_user_model()
        adobe_user, _ = User.objects.get_or_create(username="adobecampaign")
        action_kwargs = {
            "sender": adobe_user,
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

    def has_consent(self, email_address) -> bool:
        """
        Returns True if this email address has a current consent, False otherwise
        """
        return queryset.filter(email=email_address).exists()

    def get_service_campaigns(self) -> QuerySet:
        return AdobeCampaign.objects.filter(active=True)

    def validate_campaign_subscribers(self, campaign, client) -> int:
        """
        For each campaign on adobe, check that the subscribers have current
        consent.
        Returns the number of unsubscribe actions due to no current
        consent found.
        """
        self.write(f"Processing: {campaign.name}")
        subscribers = client.subscriptions(campaign.pkey)
        total = next(subscribers)
        unsubscribed = 0
        with self.tqdm(total=total) as progress_bar:
            for subscription in subscribers:
                profile = subscription.get('subscriber', {})
                if profile:
                    email_address = profile.get('email')
                    if self.has_consent(email_address) is False:
                        client.unsubscribe(subscription.get('PKey'))
                        unsubscribed += 1
                progress_bar.update(1)
        campaign.last_fetched_at = timezone.now()
        campaign.save()
        return unsubscribed

    def process_unsubscribe_events(self, campaign, client) -> tuple:
        """
        Fetch all unsubscription events from Adobe, and for each,
        if a record exists in consent service, remove it's consent.
        Returns a tuple with the number of actual consents removed
        and a boolean denoting if any unsubscription events occured.
        """
        self.write(f"Processing unsubscriptions for: {campaign.name}")
        unsubscribers = client.get_unsubscribers()
        unsubscription_events = unsubscribers.get('content', [])
        total = unsubscribers.get('count', {}).get('value')
        consents_removed = 0
        with self.tqdm(total=total) as progress_bar:
            self.write(f"Processing {total} unsubscription events")
            for unsub in unsubscription_events:
                service = unsub.get('service')
                email = unsub.get('email')
                # see about changing to service pkey
                if service == campaign.name and self._should_update(email):
                    self.update_consent(
                        email_address=email,
                        meta={
                            "emt_id": unsub.get('EMT_ID'),
                            "action_date": unsub.get('actionDate')
                        },
                        consent = False)
                    self.write(f"Update sunsub: {email}  {unsub.get('EMT_ID')}")
                    client.delete_unsubscribers(unsub.get('PKey'))
                    consents_removed += 1
                progress_bar.update(1)
        return consents_removed, bool(unsubscription_events)

    def run(self, *args, **options) -> None:
        client = AdobeClient()
        unsubscribed = consents_removed = 0
        service_campaigns = self.get_service_campaigns()
        for campaign in service_campaigns:
            # Validate campaign subscribers
            unsubscribed = self.validate_campaign_subscribers(campaign, client)
            # Check unsubscription events
            consents_removed, has_unsubs = self.process_unsubscribe_events(campaign, client)
            if has_unsubs and settings.ADOBE_STAGING_WORKFLOW:
                self.write("Initiating cleanup workflow")
                client.start_workflow(settings.ADOBE_STAGING_WORKFLOW)
        self.write(
            f"Adobe cycle complete. Unsubscribed={unsubscribed}, Consents removed={consents_removed}"
        )

    def handle(self, *args, **options):
        run_forever = options.pop("forever")
        sleep_time = options.pop("sleep_time")

        if run_forever:
            while True:
                self.write("Polling Adobe Campaign")
                self.run(args, options)
                self.write(
                    f"sleeping until {datetime.now() + timedelta(seconds=sleep_time)}"
                )
                sleep(sleep_time)
        else:
            self.run(args, options)
