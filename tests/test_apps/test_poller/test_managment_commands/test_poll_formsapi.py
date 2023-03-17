from unittest.mock import patch
from unittest import mock

import pytest
from django.core.management import call_command

from server.apps.main.models import LegalBasis


class TestFormsAPICommand:

    pytestmark = pytest.mark.django_db

    def test_consent_added_from_contact_consent_field(self):
        all_basis = list(LegalBasis.objects.all())
        assert len(all_basis) == 0

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
            results.hits.total.value = 1
            results.hits.__len__.return_value = 1

            hit = mock.MagicMock()
            hit.__contains__.side_effect = lambda key: key == 'object'
            hit.object = {
                'dit:directoryFormsApi:Submission:Data': AttrDict({
                    'email_address': 'foo@bar.com',
                    'contact_consent': ['consents_to_email_contact'],
                })
            }
            hit.to_dict.return_value = {
                'id': 'any',
                'published': 'any',
            }
            results.__iter__.return_value = [hit]

            search_mock.return_value.filter.return_value.sort.return_value.execute.return_value = results

            call_command("poll_formsapi")

        all_basis = list(LegalBasis.objects.all())
        assert len(all_basis) == 1
        assert all_basis[0].email == 'foo@bar.com'
        assert len(all_basis[0].consents.all()) == 1
        assert all_basis[0].consents.all()[0].name == 'email_marketing'
