from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from server.apps.api.serializers import LegalBasisSerializer
from server.apps.main.models import LegalBasis


class LegalBasisViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `create`, `update`, `list` and `detail` actions.
    """

    queryset = LegalBasis.objects.all()
    serializer_class = LegalBasisSerializer
    filter_backends = [DjangoFilterBackend]
    lookup_value_regex = r"[^/]+"
    lookup_field = "email"
    filterset_fields = ['consents__name', 'consents']
