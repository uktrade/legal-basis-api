from rest_framework import viewsets

from server.apps.api.serializers import LegalBasisSerializer
from server.apps.main.models import LegalBasis


class LegalBasisViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = LegalBasis.objects.all()
    serializer_class = LegalBasisSerializer
    lookup_value_regex = r"[^/]+"
    lookup_field = 'email'
