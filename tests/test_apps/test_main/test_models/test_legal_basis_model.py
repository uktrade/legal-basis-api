from hypothesis import given
from hypothesis.extra.django import TestCase, from_model
from hypothesis.strategies import emails, just

from server.apps.main.models import Consent, LegalBasis


class TestLegalBasis(TestCase):
    """This is a property-based test that ensures model correctness."""

    @given(from_model(LegalBasis, email=emails()))
    def test_model_properties(self, instance):
        """Tests that instance can be saved and has correct representation."""
        instance.save()

        assert "@" in instance.email
        assert len(str(instance)) <= 254

    @given(
        from_model(LegalBasis, email=just("FOO@BAR.COM")),
        from_model(LegalBasis, email=just("foo@bar.com")),
    )
    def test_model_email_case_insensitive(
        self, instance1: LegalBasis, instance2: LegalBasis
    ):
        instance1.save()
        assert instance1.email == instance2.email

    @given(
        from_model(Consent), from_model(LegalBasis, email=just("FOO@BAR.COM")),
    )
    def test_model_can_store_consent(self, consent: Consent, instance1: LegalBasis):
        consent.save()
        instance1.consents.add(consent)
        instance1.save()
        assert consent in instance1.consents.all()
        assert len(instance1.consents.all()) == 1
