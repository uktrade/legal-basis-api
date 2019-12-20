from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from typing_extensions import TypedDict


class HawkCredentials(TypedDict):
    id: str
    key: str
    algorithm: str


def hawk_credentials_lookup(id: str) -> HawkCredentials:
    token = Token.objects.get(user__username=id)
    return {
        'id': id,
        'key': token.key,
        'algorithm': 'sha256'
    }


def hawk_user_lookup(request, credentials):
    return User.objects.get(username=credentials['id']), None
