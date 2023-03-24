import datetime
from contextlib import contextmanager

from unittest.mock import patch
from unittest import mock

import pytest
from django.core.management import call_command

from server.apps.main.models import LegalBasis


@contextmanager
def mock_activity_stream(published):
    class AttrDict(dict):
        def __init__(self, *args, **kwargs):
            super(AttrDict, self).__init__(*args, **kwargs)
            self.__dict__ = self
        def to_dict(self):
            return self

    with patch("server.apps.poller.api_client.activity.Search") as search_mock:
        results = mock.MagicMock()

        results.to_dict.return_value = {
            "hits": {
                "hits": [{
                    "sort": (1234, "last-id")
                }]
            }
        }
        results.hits.total.value = 2
        results.hits.__len__.return_value = 2

        no_consent_hit = mock.MagicMock()
        no_consent_hit.__contains__.side_effect = lambda key: key == 'object'
        no_consent_hit.object = {
            'dit:directoryFormsApi:Submission:Data': AttrDict({
                'email_address': 'foo@bar.com',
                'contact_consent': [],
            })
        }
        no_consent_hit.to_dict.return_value = {
            'id': 'dit:directoryFormsApi:Submission:134212:Create',
            'url': '/international/trade/contact/',
            'published': '2009-02-13 11:18:05',
        }

        current_hit = mock.MagicMock()
        current_hit.__contains__.side_effect = lambda key: key == 'object'
        current_hit.object = {
            'dit:directoryFormsApi:Submission:Data': AttrDict({
                'email_address': 'foo@bar.com',
                'contact_consent': ['consents_to_email_contact'],
            })
        }
        current_hit.to_dict.return_value = {
            'id': 'dit:directoryFormsApi:Submission:134212:Create',
            'url': '/international/trade/contact/',
            'published': published,
        }
        results.__iter__.return_value = [current_hit, no_consent_hit]

        search_mock.return_value.filter.return_value.sort.return_value.execute.return_value = results

        yield


class TestFormsAPICommand:

    pytestmark = pytest.mark.django_db

    def test_consent_added_from_contact_consent_field(self):
        all_basis = list(LegalBasis.objects.all())
        assert len(all_basis) == 0

        with mock_activity_stream(published='2011-02-13 11:18:05'):
            call_command("poll_formsapi")

        all_current_basis = list(LegalBasis.objects.filter(current=True))
        expected_value = datetime.datetime(2011, 2, 13, 11, 18, 5, tzinfo=datetime.timezone.utc)
        assert all_current_basis[0].modified_at == expected_value
        assert len(all_current_basis) == 1
        assert all_current_basis[0].email == 'foo@bar.com'
        assert len(all_current_basis[0].consents.all()) == 1
        assert all_current_basis[0].consents.all()[0].name == 'email_marketing'

    def test_poll_formsapi_rerun(self):
        with mock_activity_stream(published='2011-02-13 11:18:05'):
            call_command("poll_formsapi")
        assert len(LegalBasis.objects.all()) == 2
        all_current_basis = list(LegalBasis.objects.filter(current=True))
        assert len(all_current_basis) == 1
        expected_value = datetime.datetime(2011, 2, 13, 11, 18, 5, tzinfo=datetime.timezone.utc)
        assert all_current_basis[0].modified_at == expected_value

        with mock_activity_stream(published='2010-02-13 11:18:05'):
            call_command("poll_formsapi_rerun")
        assert len(LegalBasis.objects.all()) == 2
        all_current_basis = list(LegalBasis.objects.filter(current=True))
        assert len(all_current_basis) == 1
        expected_value = datetime.datetime(2010, 2, 13, 11, 18, 5, tzinfo=datetime.timezone.utc)
        assert all_current_basis[0].modified_at == expected_value