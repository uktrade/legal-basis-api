import pytz
from datetime import datetime, timedelta
from time import sleep

from actstream import action
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Model
from django.utils import timezone
from django.utils.functional import cached_property
from django_tqdm import BaseCommand

from server.apps.main.models import KEY_TYPE, Commit, Consent, LegalBasis
from server.apps.poller.api_client.adobe import AdobeClient 
from server.apps.poller.models import AdobeCampaign 

queryset = LegalBasis.objects.filter(current=True)


class Command(BaseCommand):
    help = """
    Start polling for Adobe campaign subscriptions.
    The campaigns to track should be set up in the AdobeCampaign model. 

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
        email_consent, _ = Consent.objects.get_or_create(name="email_address")
        return email_consent


    @transaction.atomic()
    def update_consent(self, email_address, meta=None) -> None:
        # self.write("Updating consent")
        if meta is None:
            meta = {}
        commit = Commit(extra=meta)
        commit.source = meta.get("url", settings.ADOBE_CAMPAIGN_BASE_URL)
        commit.save()

        self._update_email_consent(commit, email_address, False)

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

    def get_service_campaigns(self):
        return AdobeCampaign.objects.filter(active=True)

    def run(self, *args, **options) -> None:
        client = AdobeClient()
        service_campaigns = self.get_service_campaigns()
        for campaign in service_campaigns:
            self.write(f"Processing: {campaign.name}")
            subscribers = client.subscriptions(campaign.pkey)
            total = next(subscribers)
            
            with self.tqdm(total=total) as progress_bar:
                for subscriber in subscribers:
                    profile = subscriber.get('subscriber', {})
                    email_address = profile.get('email')
                    meta = {
                        'profile_pkey': profile.get('PKey'),
                        'service_pkey': campaign.pkey,
                        'first_name': profile.get('firstName'),
                        'last_name': profile.get('lastName'),
                        'campaign_id': campaign.id, 
                    }
                    if self._should_update(email_address):
                        self.update_consent(email_address, meta=meta)
                    progress_bar.update(1)  
            campaign.last_fetched_at = timezone.now()
            campaign.save()

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
