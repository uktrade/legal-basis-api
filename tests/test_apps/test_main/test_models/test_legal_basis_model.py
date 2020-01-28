from hypothesis import given
from hypothesis.extra import django
from hypothesis.strategies import emails

from server.apps.main.models import LegalBasis


class TestLegalBasis(django.TestCase):
    """This is a property-based test that ensures model correctness."""

    @given(django.from_model(LegalBasis, email=emails()))
    def test_model_properties(self, instance):
        """Tests that instance can be saved and has correct representation."""
        instance.save()

        assert '@' in  instance.email
        assert len(str(instance)) <= 254
