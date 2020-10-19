import datetime

import jwt  # noqa
import requests
from django.conf import settings


class AdobeCampaignRequestException(Exception):
    def __init__(self, message=None, status_code=None) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AdobeClient:
    """
    An API client for Adobe Campaigns. The client is using the custom resource endpoints and is
    specifically tailored to the implementation for DIT's nurture program.
    """
    def __init__(self) -> None:
        self.token = self.get_token()

    def get_token(self) -> str:
        """
        Generate, encode and exchange the JWT token for an access token.
        """
        url = "https://ims-na1.adobelogin.com/ims/exchange/jwt"
        expiry = datetime.datetime.now() + datetime.timedelta(minutes=5)
        payload = {
            "exp": int(expiry.timestamp()),
            "iss": settings.ADOBE_ORGANISATION_ID,
            "sub": settings.ADOBE_TECHNICAL_ACCOUNT_ID,
            "aud": f"https://ims-na1.adobelogin.com/c/{settings.ADOBE_API_KEY}",
            "https://ims-na1.adobelogin.com/s/ent_campaign_sdk": True,
            "https://ims-na1.adobelogin.com/s/ent_adobeio_sdk": True,
        }
        encoded_jwt = jwt.encode(payload, settings.ADOBE_PRIVATE_KEY, algorithm='RS256')
        response = requests.post(url, data={
            'client_id': settings.ADOBE_API_KEY,
            'client_secret': settings.ADOBE_API_SECRET,
            'jwt_token': encoded_jwt,
        }).json()
        return response.get('access_token')

    @property
    def headers(self) -> dict:
        """
        Standard request headers
        """
        return {
            'Authorization': f'Bearer {self.token}',
            'X-Api-Key': settings.ADOBE_API_KEY,
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json',
        }

    def url(self, path) -> str:
        """
        Generate a url for Adobe Campaign for a given path.
        """
        return f"https://mc.adobe.io/{settings.ADOBE_TENANT_ID}/campaign/{path}"

    def subscribe(self, service_pkey, profile_pkey=None, subscribe_url=None) -> dict:
        """
        Subscribe a profile to a campaign. This method was implemented but will not be used
        directly as we are instead loading profiles into a staging area in adobe and using
        a predefined workflow to subscribe them to the campaign.
        """
        if not subscribe_url and profile_pkey:
            profile = self.get_profile(profile_pkey)
            subscribe_url = profile.get('subscriptions', {}).get('href')
        return requests.post(
            subscribe_url,
            json={'service': {'PKey': service_pkey}},
            headers=self.headers
        ).json()

    def get_unsubscribers(self) -> dict:
        """
        Return a list of those who unsubscribed via Adobe side. The records come from a
        custom resource which collects unsubscriptions via the Adobe platform.
        """
        url = self.url("profileAndServicesExt/cusInvestUnsubscribes")
        return requests.get(url, headers=self.headers).json()

    def delete_unsubscribers(self, pkey) -> object:
        """
        Delete an unsubscription entry
        """
        url = self.url(f"profileAndServicesExt/cusInvestUnsubscribes/{pkey}")
        return requests.delete(url, headers=self.headers)

    def unsubscribe(self, subscription_url) -> dict:
        """
        Unsubscribe a profile from a service via the subscription url
        """
        return requests.delete(subscription_url, headers=self.headers).json()

    def get_profile(self, pkey) -> dict:
        """
        Return a profile by a pkey
        """
        url = self.url(f"profileAndServicesExt/profile/{pkey}")
        return requests.get(url, headers=self.headers).json()

    def get_all_profiles(self) -> dict:
        """
        Return all profiles
        """
        url = self.url("profileAndServicesExt/profile")
        return requests.get(url, headers=self.headers).json()

    def get_services(self) -> dict:
        """
        Return all services (campaigns)
        """
        url = self.url("profileAndServicesExt/service")
        return requests.get(url, headers=self.headers).json()

    def get_service(self, pkey) -> dict:
        """
        Return a single service by its pkey
        """
        url = self.url(f"profileAndServicesExt/service/{pkey}")
        return requests.get(url, headers=self.headers).json()

    def get_subscriptions(self, pkey) -> dict:
        """
        Return a campaign's subscriptions
        """
        service = self.get_service(pkey)
        url = service.get('subscriptions', {}).get('href')
        return requests.get(url, headers=self.headers).json()

    def subscriptions(self, pkey):
        """
        A generator to return service subscriptions.
        The first yield contains the total (int).
        Any subsequent yield will produce the next subscription
        """
        subscriptions = self.get_subscriptions(pkey)
        _count_block = subscriptions.get('count', {})
        if 'value' in _count_block:
            total = _count_block.get('value')
        else:
            total = self.get_url(_count_block.get('href')).get('count', 0)
        yield total
        while True:
            if not subscriptions.get('content'):
                break
            for subscription in subscriptions.get('content', []):
                yield subscription
            next_url = subscriptions.get('next', {}).get('href')
            if next_url:
                subscriptions = self.get_url(next_url)
            else:
                subscriptions = {'content': []}

    def start_workflow(self, workflow_id) -> dict:
        url = self.url(f"workflow/execution/{workflow_id}/commands")
        response = requests.post(url, headers=self.headers, json={'method': 'start'})
        return response.json()

    def get_url(self, url) -> dict:
        """
        GET an arbitrary url
        """
        response = requests.get(url, headers=self.headers)
        return response.json()
