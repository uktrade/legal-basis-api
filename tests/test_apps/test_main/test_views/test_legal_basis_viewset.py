import pytest
from django.urls import reverse
from mixer.backend.django import mixer

from server.apps.main.models import LegalBasis


class TestLegalBasisViewSet:
    pytestmark = pytest.mark.django_db

    def test_list_endpoint_by_unauthenticated(self, client):
        """This test ensures that list endpoint works requires being logged in."""
        response = client.get(reverse("v1:legalbasis-list"))
        assert response.status_code == 401

    def test_list_endpoint_paging(self, read_only_client):
        """Tests pagination of results."""
        mixer.cycle(2).blend(
            LegalBasis, consents__name=mixer.sequence("email_{0}"), key=None, phone=''
        )

        url = reverse('v1:legalbasis-list')
        response = read_only_client.get(
            url,
            data={
                'offset': 1,
                'limit': 1,
            },
        )

        assert response.status_code == 200
        assert response.data['count'] > 1
        assert len(response.data['results']) == 1

    def test_bulk_lookup_endpoint(self, read_write_client):
        """Test bulk lookup endpoint."""
        emails = ['foo_0@bar.com', 'foo_1@bar.com']
        mixer.cycle(2).blend(
            LegalBasis,
            key=None,
            phone="",
            key_type="email",
            email=(email for email in emails),
        )

        url = reverse('v1:legalbasis-bulk-lookup')
        response = read_write_client.post(
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

    def test_read_only_bulk_lookup(self, read_only_client):
        lb1 = mixer.blend(LegalBasis, consents__name="email", key=None, phone="")
        mixer.blend(LegalBasis, consents__name="phone", key=None, email="")
        response = read_only_client.post(
            reverse("v1:legalbasis-bulk-lookup"),
            data={"emails": [lb1.email]},
            format="json",
        )
        assert response.status_code == 403

    def test_user_with_no_permissions(self, authenticated_client):
        mixer.blend(LegalBasis, consents__name="email", key=None, phone="")
        response = authenticated_client.get(reverse("v1:legalbasis-list"))
        assert response.status_code == 403

    def test_read_write_user_can_read(self, read_write_client):
        mixer.blend(LegalBasis, consents__name="email", key=None, phone="")
        response = read_write_client.get(reverse("v1:legalbasis-list"))
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert len(response.data["results"][0]["consents"]) == 1

    def test_read_write_user_can_write(self, read_write_client):
        mixer.blend(LegalBasis, consents__name="email", key=None, phone="")
        legal_basis_count = LegalBasis.objects.all().count()
        response = read_write_client.post(
            reverse("v1:legalbasis-list"),
            data={"email": "test.email@example.com", "consents": ["email"]},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["email"] == "test.email@example.com"
        assert response.data["phone"] == ""
        assert response.data["consents"] == ["email"]
        assert LegalBasis.objects.all().count() == legal_basis_count + 1

    def test_read_only_user_can_read(self, read_only_client):
        mixer.blend(LegalBasis, consents__name="email", key=None, phone="")
        response = read_only_client.get(reverse("v1:legalbasis-list"))
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert len(response.data["results"][0]["consents"]) == 1

    def test_read_only_user_cannot_write(self, read_only_client):
        legal_basis_count = LegalBasis.objects.all().count()
        response = read_only_client.post(
            reverse("v1:legalbasis-list"),
            data={
                "email": "this.wont.work@example.com",
                "consents": ["email_marketing"],
            },
            format="json",
        )
        assert response.status_code == 403
        assert LegalBasis.objects.all().count() == legal_basis_count

    def test_write_only_user_cannot_read(self, write_only_client):
        mixer.blend(LegalBasis, consents__name="email", key=None, phone="")
        response = write_only_client.get(reverse("v1:legalbasis-list"))
        assert response.status_code == 403

    def test_write_only_user_can_write(self, write_only_client):
        mixer.blend(LegalBasis, consents__name="phone", key=None, phone="")
        legal_basis_count = LegalBasis.objects.all().count()
        response = write_only_client.post(
            reverse("v1:legalbasis-list"),
            data={"phone": "+447897395794", "consents": ["phone_marketing"]},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["email"] == ""
        assert response.data["phone"] == "+447897395794"
        assert response.data["consents"] == ["phone_marketing"]
        assert LegalBasis.objects.all().count() == legal_basis_count + 1

    def test_write_only_datahub_export(self, write_only_client):
        mixer.blend(LegalBasis, consents__name="email", key=None, phone="")
        response = write_only_client.get(reverse("v1:legalbasis-datahub-export"))
        assert response.status_code == 403

    def test_read_write_datahub_export(self, read_write_client):
        lb = mixer.blend(LegalBasis, consents__name="email", key=None, phone="")
        response = read_write_client.get(reverse("v1:legalbasis-datahub-export"))
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == lb.id

    def test_read_write_bulk_lookup(self, read_write_client):
        lb1 = mixer.blend(LegalBasis, consents__name="email", key=None, phone="")
        mixer.blend(LegalBasis, consents__name="phone", key=None, email="")
        response = read_write_client.post(
            reverse("v1:legalbasis-bulk-lookup"),
            data={"emails": [lb1.email]},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert len(response.data["results"][0]["consents"]) == 1
