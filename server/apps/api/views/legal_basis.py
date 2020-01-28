from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from server.apps.api.serializers import LegalBasisSerializer, ListOfEmailsSerializer
from server.apps.main.models import LegalBasis


class LegalBasisViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `create`, `update`, `list` and `detail` actions.

    There is also a `bulk_lookup` endpoint that takes a list of email addresses
    and returns their consent status.
    """

    queryset = LegalBasis.objects.prefetch_related("consents").all()
    serializer_class = LegalBasisSerializer
    filter_backends = [DjangoFilterBackend]
    lookup_value_regex = r"[^/]+"
    lookup_field = "email"
    filterset_fields = ["consents__name", "consents"]

    @swagger_auto_schema(
        method="post",
        request_body=ListOfEmailsSerializer,
        responses={status.HTTP_200_OK: LegalBasisSerializer(many=True)},
    )
    @action(detail=False, methods=["POST"])
    def bulk_lookup(self, request) -> Response:
        body = ListOfEmailsSerializer(data=request.data)

        if body.is_valid():
            basis_objs = self.paginate_queryset(
                self.filter_queryset(self.queryset).filter(pk__in=body.data["emails"])
            )
            serialized = self.get_serializer(instance=basis_objs, many=True)
            return self.get_paginated_response(serialized.data)

        return Response(body.errors, status=status.HTTP_400_BAD_REQUEST)
