from hashlib import sha512

from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from server.apps.api.serializers import (
    CreateLegalBasisSerializer,
    LegalBasisSerializer,
    ListOfEmailsSerializer,
)
from server.apps.main.models import LegalBasis


class LegalBasisViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `create`, `list` and `detail` actions.

    There is also a `bulk_lookup` endpoint that takes a list of email addresses
    and returns their consent status.
    """

    queryset = LegalBasis.objects.prefetch_related("consents").filter(current=True)
    serializer_class = LegalBasisSerializer
    create_serializer_class = CreateLegalBasisSerializer
    filter_backends = [DjangoFilterBackend]
    lookup_value_regex = r"[^/]+"
    lookup_field = "key"
    filterset_fields = ["consents__name", "consents", "key_type"]
    http_method_names = ["get", "post", "head"]

    def get_serializer_class(self):
        if self.action == "create":
            return self.create_serializer_class
        return super().get_serializer_class()

    def get_object(self):
        # hash lookup_kwarg here, normalise email here (upper)

        self.kwargs[self.lookup_field] = sha512(
            self.kwargs[self.lookup_field].lower().encode()
        ).digest()
        return super().get_object()

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

    @swagger_auto_schema(
        request_body=CreateLegalBasisSerializer,
        responses={status.HTTP_200_OK: LegalBasisSerializer},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
