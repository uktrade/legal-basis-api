from django.contrib.auth.models import Group, Permission, User
from django.urls import reverse
from requests_hawk import HawkAuth
from rest_framework.authtoken.models import Token
from rest_framework.test import APILiveServerTestCase, RequestsClient


class TestHawkAuth(APILiveServerTestCase):
    def setUp(self):
        self.client = RequestsClient()
        self.url = 'http://testserver' + reverse('v1:legalbasis-list')
        self.user = User.objects.create_user(username="read-only", password="password")
        group = Group.objects.create(name="Read only users")
        group.permissions.add(
            Permission.objects.get(codename="view_legalbasis"),
            Permission.objects.get(codename="view_consent"),
        )
        self.user.groups.add(group)

    def test_no_auth(self):
        response = self.client.get(
            self.url
        )
        assert response.status_code == 401

    def test_invalid_key(self):
        Token.objects.create(user=self.user, key='valid-user-key')
        hawk_auth = HawkAuth(id=self.user.username, key='invalid-user-key', always_hash_content=False)
        response = self.client.get(
            self.url,
            auth=hawk_auth,
        )
        assert response.status_code == 401

    def test_user_does_not_exist(self):
        hawk_auth = HawkAuth(id='i-dont-exist', key='non-existent-user-key', always_hash_content=False)
        response = self.client.get(
            self.url,
            auth=hawk_auth,
        )
        assert response.status_code == 401

    def test_valid_key_no_permission(self):
        user = User.objects.create_user(username="no-perms", password="password")
        token = Token.objects.create(user=user, key='valid-user-key')
        hawk_auth = HawkAuth(id=user.username, key=token.key, always_hash_content=False)
        response = self.client.get(
            self.url,
            auth=hawk_auth,
        )
        assert response.status_code == 403

    def test_valid_key(self):
        token = Token.objects.create(user=self.user, key='valid-user-key')
        hawk_auth = HawkAuth(id=self.user.username, key=token.key, always_hash_content=False)
        response = self.client.get(
            self.url,
            auth=hawk_auth,
        )
        assert response.status_code == 200
