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

    def test_list_endpoint_by_unauthenticated(self, client):
        """This test ensures that list endpoint works requires being logged in."""
        response = client.get(reverse("v1:legalbasis-list"))

        assert response.status_code == 401

    def test_list_endpoint_with_1_item(self, authenticated_client):
        """This test ensures that list endpoint works."""
        mixer.blend(LegalBasis, consents__name="email")

        response = authenticated_client.get(reverse("v1:legalbasis-list"))

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert len(response.data["results"][0]["consents"]) == 1
