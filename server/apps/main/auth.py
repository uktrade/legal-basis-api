from typing import Optional

from django.contrib.auth.models import User
from django.http import HttpRequest
from hawkrest import HawkAuthentication
from rest_framework.authtoken.models import Token
from typing_extensions import TypedDict


class HawkCredentials(TypedDict):
    id: str
    key: str
    algorithm: str


def hawk_credentials_lookup(id: str) -> Optional[HawkCredentials]:
    try:
        token = Token.objects.get(user__username=id)
        return {"id": id, "key": token.key, "algorithm": "sha256"}
    except Token.DoesNotExist:
        return None


def hawk_user_lookup(request: HttpRequest, credentials: HawkCredentials):
    return User.objects.get(username=credentials["id"]), None


class HawkUserAuthentication(HawkAuthentication):
    """
    Used as a django authentication backend (not DRF), for auth on
    the ActivityStream feed
    """

    def hawk_user_lookup(self, request: HttpRequest, credentials: HawkCredentials):
        """
        This method is overridden rather than using the function above because
        DRF's authenticate() method returns a (User, Backend) tuple, rather than
        Django's authenticate returning a straight User object
        """
        return User.objects.get(username=credentials["id"])

    def get_user(self, user_id):
        return User.objects.get(id=user_id)
