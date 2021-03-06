import io
from unittest.mock import patch

import pytest
from django.conf import settings
from mixer.backend.django import mixer

from server.apps.main.models import Consent, LegalBasis
from server.apps.poller.management.commands import poll_maxemail


class TestMaxemailCommand:

    pytestmark = pytest.mark.django_db

    def test_email_consent_creates_if_missing(self):
        Consent.objects.all().delete()

        out = io.StringIO()
        command = poll_maxemail.Command(stdout=out)
        assert Consent.objects.all().count() == 0
        _ = command.email_consent
        assert Consent.objects.all().count() == 1

    def test_email_consent_noop_if_exists(self):
        Consent.objects.all().delete()

        out = io.StringIO()
        mixer.blend(Consent, name="email_marketing")
        command = poll_maxemail.Command(stdout=out)
        assert Consent.objects.all().count() == 1
        _ = command.email_consent
        assert Consent.objects.all().count() == 1

    @patch("server.apps.poller.management.commands.poll_maxemail.MaxEmail")
    def test_get_client(self, mock_client):
        out = io.StringIO()
        command = poll_maxemail.Command(stdout=out)
        _ = command.get_client()
        mock_client.assert_called_once_with(
            settings.MAXEMAIL_USERNAME, settings.MAXEMAIL_PASSWORD
        )

    def test_should_update_exists_without_consent(self):
        mixer.blend(
            LegalBasis, key=None, phone="", key_type="email", email="foo@bar.com"
        )
        out = io.StringIO()
        command = poll_maxemail.Command(stdout=out)
        assert not command._should_update("foo@bar.com")

    def test_should_update_exists_with_consent(self):
        Consent.objects.all().delete()

        out = io.StringIO()
        command = poll_maxemail.Command(stdout=out)
        c = mixer.blend(Consent, name="email_marketing")
        mixer.blend(
            LegalBasis,
            key=None,
            phone="",
            key_type="email",
            email="foo@bar.com",
            consents=c,
        )
        assert command._should_update("foo@bar.com")

    def test_should_update_doesnt_exist(self):
        out = io.StringIO()
        command = poll_maxemail.Command(stdout=out)
        assert command._should_update("foo@bar.com")
