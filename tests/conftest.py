"""
This module is used to provide configuration, fixtures, and plugins for pytest.

It may be also used for extending doctest's context:
1. https://docs.python.org/3/library/doctest.html
2. https://docs.pytest.org/en/latest/doctest.html
"""

import pytest
from django.contrib.auth.models import Group, Permission
from rest_framework.authtoken.models import Token


@pytest.fixture(autouse=True)
def _media_root(settings, tmpdir_factory):
    """Forces django to save media files into temp folder."""
    settings.MEDIA_ROOT = tmpdir_factory.mktemp("media", numbered=True)


@pytest.fixture(autouse=True)
def _password_hashers(settings):
    """Forces django to use fast password hashers for tests."""
    settings.PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]


@pytest.fixture(autouse=True)
def _auth_backends(settings):
    """Deactivates security backend from Axes app."""
    settings.AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)


@pytest.fixture
def authenticated_client(client, django_user_model):
    username = "user1"
    password = "bar"
    django_user_model.objects.create_user(username=username, password=password, is_superuser=False)
    client.login(username=username, password=password)
    return client


@pytest.fixture
def read_write_client(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="read-write", password="password"
    )
    Token.objects.create(user=user, key='test-hawk-key')
    group = Group.objects.create(name="Read/write users")
    group.permissions.add(
        Permission.objects.get(codename="view_legalbasis"),
        Permission.objects.get(codename="add_legalbasis"),
        Permission.objects.get(codename="view_consent"),
        Permission.objects.get(codename="add_consent"),
    )
    user.groups.add(group)
    client.login(username=user.username, password="password")
    return client


@pytest.fixture
def read_only_client(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="read-only", password="password"
    )
    Token.objects.create(user=user, key='test-hawk-key')
    group = Group.objects.create(name="Read only users")
    group.permissions.add(
        Permission.objects.get(codename="view_legalbasis"),
        Permission.objects.get(codename="view_consent"),
    )
    user.groups.add(group)
    client.login(username=user.username, password="password")
    return client


@pytest.fixture
def write_only_client(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="write-only", password="password"
    )
    Token.objects.create(user=user, key='test-hawk-key')
    group = Group.objects.create(name="Write only users")
    group.permissions.add(
        Permission.objects.get(codename="add_legalbasis"),
        Permission.objects.get(codename="add_consent"),
    )
    user.groups.add(group)
    client.login(username=user.username, password="password")
    return client


@pytest.fixture
def directory_forms_user(django_user_model):
    return django_user_model.objects.get_or_create(username="directoryforms")
