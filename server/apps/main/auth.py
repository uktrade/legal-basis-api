import logging

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from mohawk import Receiver
from mohawk.exc import HawkFail
from rest_framework.authentication import BaseAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)


class HawkUserAuthentication(BaseAuthentication):
    """
    Used as a django authentication backend (not DRF), for auth on
    the ActivityStream feed
    """

    def authenticate_header(self, request):
        """
        This is returned as the WWW-Authenticate header when AuthenticationFailed is raised.
        DRF also requires this to send a 401 (as opposed to 403)
        """
        return 'Hawk'

    def authenticate(self, request):
        """
        Authenticates a request using Hawk signature

        If either of these suggest we cannot authenticate, AuthenticationFailed
        is raised, as required in the DRF authentication flow
        """
        if 'HTTP_AUTHORIZATION' not in request.META:
            raise AuthenticationFailed('Authentication credentials were not provided.')

        try:
            hawk_receiver = self._authorise(request)
        except HawkFail as e:
            logger.warning('Failed authentication {e}'.format(e=e))
            raise AuthenticationFailed('Incorrect authentication credentials.')

        user = get_user_model().objects.get(username=hawk_receiver.parsed_header['id'])
        return user, hawk_receiver

    @staticmethod
    def _lookup_credentials(username):
        """
        Raises a HawkFail if the passed token does not exist as a username
        """
        try:
            token = Token.objects.get(user__username=username)
            return {'id': username, 'key': token.key, 'algorithm': 'sha256'}
        except Token.DoesNotExist:
            logger.warning('Provided token does not exist %s', username)
            raise HawkFail(f'No Hawk ID of {username}')

    @staticmethod
    def _seen_nonce(token, nonce, _):
        """
        Returns true if the passed access_key_id/nonce combination has been used within 60 seconds
        """
        cache_key = f'legal-basis:{token}:{nonce}'
        seen_cache_key = not cache.add(
            cache_key, True, timeout=60,
        )

        if seen_cache_key:
            logger.warning('Already seen nonce {nonce}'.format(nonce=nonce))

        return seen_cache_key

    def _authorise(self, request) -> Receiver:
        """Raises a HawkFail if the passed request cannot be authenticated"""
        return Receiver(
            self._lookup_credentials,
            request.META['HTTP_AUTHORIZATION'],
            request.build_absolute_uri(),
            request.method,
            content=request.body,
            content_type=request.content_type,
            seen_nonce=self._seen_nonce,
        )


class HawkResponseMiddleware(MiddlewareMixin):
    """
    Adds Hawk Server-Authorization header to the response
    """

    def process_response(self, request, response):
        if getattr(request, 'auth', None) is not None:
            response['Server-Authorization'] = request.auth.respond(
                content=response.content,
                content_type=response['Content-Type'],
            )
        return response
