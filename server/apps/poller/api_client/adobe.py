import datetime
import requests 
import jwt
from django.conf import settings


class AdobeClient:
    def __init__(self):
        self.token = self.get_token()

    def get_token(self):
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
    def headers(self):
        return {
            'Authorization': f'Bearer {self.token}',
            'X-Api-Key': settings.ADOBE_API_KEY,
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json',
        }

    def create_profile(self, email, first_name=None, last_name=None, service_pkey=None):
        url = f"https://mc.adobe.io/{settings.ADOBE_TENANT_ID}/campaign/profileAndServices/profile"
        response = requests.post(url, json={
            'firstName': first_name, 
            'lastName': last_name, 
            'email': email,
        }, headers=self.headers).json() 
        print(response)
        if service_pkey:
            sub_res = self.subscribe(service_pkey, subscribe_url=response.get('subscriptions', {}).get('href'))
            print(sub_res)
        return response

    def subscribe(self, service_pkey, profile_pkey=None, subscribe_url=None):
        if not subscribe_url and profile_pkey:
            profile = self.get_profile(profile_pkey)
            subscribe_url = profile.get('subscriptions', {}).get('href')
        return requests.post(subscribe_url, json={'service': {'PKey': service_pkey}}, headers=self.headers).json()

    def get_profile(self, pkey):
        """
        Return a profile
        """
        url = f"https://mc.adobe.io/{settings.ADOBE_TENANT_ID}/campaign/profileAndServices/profile/{pkey}"
        return requests.get(url, headers=self.headers).json()

    def get_all_profiles(self):
        """
        Return all subscribers (profiles)
        """
        url = f"https://mc.adobe.io/{settings.ADOBE_TENANT_ID}/campaign/profileAndServices/profile"
        return requests.get(url, headers=self.headers).json()

    def get_services(self):
        """
        Return all services (campaigns)
        """
        url = f"https://mc.adobe.io/{settings.ADOBE_TENANT_ID}/campaign/profileAndServices/service"
        return requests.get(url, headers=self.headers).json() 

    def get_service(self, pkey):
        """
        Return a single service by it's pkey
        """
        url = f"https://mc.adobe.io/{settings.ADOBE_TENANT_ID}/campaign/profileAndServices/service/{pkey}"
        return requests.get(url, headers=self.headers).json()

    def get_subscriptions(self, pkey):
        """
        Return a campaign's subscriptions
        """
        service = self.get_service(pkey)
        url = service.get('subscriptions', {}).get('href')  
        return requests.get(url, headers=self.headers).json()
    
    def subscriptions(self, pkey):
        """
        A generator to return service subscriptions
        """
        subscriptions = self.get_subscriptions(pkey)
        total = self.get_url(subscriptions.get('count', {}).get('href')).get('count', 0)
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

    def get_url(self, url):
        """
        GET an arbitrary url 
        """
        response = requests.get(url, headers=self.headers)
        return response.json()

