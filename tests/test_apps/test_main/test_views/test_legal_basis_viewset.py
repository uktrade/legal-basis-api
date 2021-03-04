import pytest
from django.urls import reverse
from mixer.backend.django import mixer

from server.apps.main.models import LegalBasis


class TestLegalBasisViewSet:
    pytestmark = pytest.mark.django_db

    def test_list_endpoint(self, authenticated_client):
        """This test ensures that list endpoint works."""
        response = authenticated_client.get(reverse("v1:legalbasis-list"))

        assert response.status_code == 200
        assert response.data["count"] == 0

    @pytest.mark.skip
    def test_list_endpoint_by_unauthenticated(self, client):
        """This test ensures that list endpoint works requires being logged in."""
        response = client.get(reverse("v1:legalbasis-list"))

        assert response.status_code == 401

    def test_list_endpoint_with_1_item(self, authenticated_client):
        """This test ensures that list endpoint works."""
        mixer.blend(LegalBasis, consents__name="email", key=None, phone='')

        response = authenticated_client.get(reverse("v1:legalbasis-list"))

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert len(response.data["results"][0]["consents"]) == 1

    def test_list_endpoint_paging(self, authenticated_client):
        """Tests pagination of results."""
        mixer.cycle(2).blend(LegalBasis, consents__name=mixer.sequence("email_{0}"), key=None, phone='')

        url = reverse('v1:legalbasis-list')
        response = authenticated_client.get(
            url,
            data={
                'offset': 1,
                'limit': 1,
            },
        )

        assert response.status_code == 200
        assert response.data['count'] > 1
        assert len(response.data['results']) == 1

    def test_bulk_lookup_endpoint(self, authenticated_client):
        """Test bulk lookup endpoint."""
        emails = ['foo_0@bar.com', 'foo_1@bar.com']
        mixer.cycle(2).blend(
            LegalBasis, key=None, phone="", key_type="email", email=(email for email in emails)
        )

        url = reverse('v1:legalbasis-bulk-lookup')
        response = authenticated_client.post(
            url,
            data={
                'emails': [emails[0].upper(), emails[1]],
            },
        )
        assert response.status_code == 200
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2

        result_emails = [result['email'] for result in response.data['results']]
        assert result_emails == emails
