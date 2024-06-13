import logging
import time
from typing import Dict, Generator, Optional

import requests
from django.conf import settings
from msal import ConfidentialClientApplication

logger = logging.getLogger(__name__)

CONTACT_POINT_TYPE_ID = 534120000  # email
CONSENT_TYPE_ID = 534120000  # purpose
CONSENT_PURPOSE_ID = "10000000-0000-0000-0000-000000000003"  # commercial
CONSENT_OPTED_IN = 534120001
CONSENT_OPTED_OUT = 534120002


class DynamicsClient:
    token: str
    max_retry_attempts: int = 10
    contacts_url: str = f"{settings.DYNAMICS_INSTANCE_URI}/api/data/v9.2/contacts"
    consents_url: str = (
        f"{settings.DYNAMICS_INSTANCE_URI}/api/data/v9.2/msdynmkt_contactpointconsent4s"
    )

    def __init__(self) -> None:
        self.token = self._get_access_token()

    def _make_request(self, url, method, params=None, data=None) -> Dict:
        num_attempts = 1
        while True:
            response = requests.request(
                method,
                url,
                params=params,
                json=data,
                headers={
                    "Authorization": f"Bearer {self.token}",
                },
            )
            try:
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError:
                logger.error("Request failed: %s", response.status_code)
                if (
                    response.status_code == 429
                    and num_attempts < self.max_retry_attempts
                ):
                    num_attempts += 1
                    logger.error(
                        "Retrying attempt %d of %d",
                        num_attempts,
                        self.max_retry_attempts,
                    )
                    time.sleep(int(response.headers.get("Retry-After", 1)))
                    continue
                raise

    @staticmethod
    def _get_access_token() -> str:
        app = ConfidentialClientApplication(
            client_id=settings.DYNAMICS_APPLICATION_ID,
            authority=f"https://login.microsoftonline.com/{settings.DYNAMICS_TENANT_ID}",
            client_credential=settings.DYNAMICS_CLIENT_SECRET,
            token_cache=None,
        )
        token_response = app.acquire_token_for_client(
            scopes=[f"{settings.DYNAMICS_INSTANCE_URI}/.default"]
        )
        if "access_token" not in token_response:
            raise Exception(
                f'Failed to acquire token: {token_response.get("error_description")}'
            )

        return token_response["access_token"]

    def get_unsubscribed_contacts(self) -> Generator:
        logger.info("Fetching all dynamics contacts with donotbulkemail set to true")
        next_link: Optional[str] = self.contacts_url + "?$filter=donotbulkemail eq true"
        record_count = 0
        while next_link is not None:
            logger.info("Fetching from %s", next_link)
            response = self._make_request(next_link, "GET")
            for record in response["value"]:
                record_count += 1
                yield record
            next_link = response.get("@odata.nextLink")
        logger.info("Fetched %d unsubscribed contacts in total", record_count)

    def get_unmanaged_contacts(
        self, created_since_days: Optional[int] = None
    ) -> Generator:
        """
        An unmanaged contact is one that was manually uploaded to dynamics
        rather than synced via data-flow. We want to keep track of these
        contacts for future reference.
        """
        logger.info("Fetching all unmanaged contacts from dynamics")
        filters = [
            # Contact has opted in (donotbulkemail == False)
            "donotbulkemail eq false",
            # Contact is unmanaged by data-flow (externaluseridentifier == None)
            "externaluseridentifier eq null",
        ]
        if created_since_days is not None:
            # Contact was created in the last X days
            filters.append(
                f"Microsoft.Dynamics.CRM.LastXDays(PropertyName='createdon',PropertyValue={created_since_days})"
            )
        next_link: Optional[
            str
        ] = f"{self.contacts_url}?$filter={' and '.join(filters)}"
        record_count = 0
        while next_link is not None:
            logger.info("Fetching from %s", next_link)
            response = self._make_request(next_link, "GET")
            for record in response["value"]:
                if record["emailaddress1"] is None:
                    continue
                record_count += 1
                yield record
            next_link = response.get("@odata.nextLink")
        logger.info("Fetched %d unmanaged contacts in total", record_count)

    def get_consents(self) -> Generator:  # noqa: C901
        logger.info("Fetching all consent records from the dynamics consent center")
        next_link: Optional[str] = self.consents_url
        record_count = 0
        while next_link is not None:
            logger.info("Fetching from %s", next_link)
            response = self._make_request(next_link, "GET")
            for record in response["value"]:
                email = record["msdynmkt_contactpointvalue"]
                contact_point_type = record["msdynmkt_contactpointtype"]
                consent_type = record["msdynmkt_contactpointconsenttype"]
                purpose = record["_msdynmkt_purposeid_value"]
                consent_value = record["msdynmkt_value"]
                opted_in = None
                if consent_value == CONSENT_OPTED_IN:
                    opted_in = True
                elif consent_value == CONSENT_OPTED_OUT:
                    opted_in = False

                # Skip records that have neither opted in or out
                if opted_in is None:
                    logger.info("Skipping unset consent record")
                    continue

                # Skip any consents that are not type "EMAIL"
                if contact_point_type != CONTACT_POINT_TYPE_ID:
                    logger.info("Skipping non-email consent")
                    continue

                # Skip consent types that are not "Purpose"
                if consent_type != CONSENT_TYPE_ID:
                    logger.info("Skipping non-purpose consent type")
                    continue

                # Skip purposes that are not "Commercial"
                if purpose != CONSENT_PURPOSE_ID:
                    logger.info("Skipping non-commercial purpose")
                    continue

                logger.info(f"User: {email} has opted {'in' if opted_in else 'out'}")
                record_count += 1
                yield {"email": email, "consent": opted_in}

            next_link = response.get("@odata.nextLink")
        logger.info("Fetched %d consent records in total", record_count)
