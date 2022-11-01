from hashlib import sha512

from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.utils.urls import remove_query_param, replace_query_param

from server.apps.api.serializers import (
    CreateLegalBasisSerializer,
    LegalBasisDataWorkspaceSerializer,
    LegalBasisSerializer,
    ListOfEmailsSerializer,
)
from server.apps.main.models import LegalBasis


class ProtocolLessLimitOffsetPagination(LimitOffsetPagination):

    def corrected_protocol_url(self) -> str:
        url = self.request.build_absolute_uri()
        if not self.request.is_allow_secure_middleware_active:
            return url.replace('https://', 'http://')
        return url

    def get_next_link(self):
        if self.offset + self.limit >= self.count:
            return None

        url = self.corrected_protocol_url()
        url = replace_query_param(url, self.limit_query_param, self.limit)

        offset = self.offset + self.limit
        return replace_query_param(url, self.offset_query_param, offset)

    def get_previous_link(self):
        if self.offset <= 0:
            return None

        url = self.corrected_protocol_url()
        url = replace_query_param(url, self.limit_query_param, self.limit)

        if self.offset - self.limit <= 0:
            return remove_query_param(url, self.offset_query_param)

        offset = self.offset - self.limit
        return replace_query_param(url, self.offset_query_param, offset)


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
    pagination_class = ProtocolLessLimitOffsetPagination

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
        method="get",
        request_body=ListOfEmailsSerializer,
        responses={status.HTTP_200_OK: LegalBasisSerializer(many=True)},
    )
    @action(detail=False, methods=["GET"])  # type: ignore
    def bulk_lookup(self, request) -> Response:
        body = ListOfEmailsSerializer(data={'emails': request.GET.getlist("email")})
        if body.is_valid():
            emails = [email.lower() for email in body.data["emails"]]

            basis_objs = self.paginate_queryset(
                self.filter_queryset(self.queryset).filter(
                    email__in=emails
                )
            )
            serialized = self.get_serializer(instance=basis_objs, many=True)
            return self.get_paginated_response(serialized.data)

        return Response(body.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        method="get",
        responses={status.HTTP_200_OK: LegalBasisDataWorkspaceSerializer(many=True)},
    )
    @action(detail=False, methods=["GET"])  # type: ignore
    def datahub_export(self, request) -> Response:
        serialized = LegalBasisDataWorkspaceSerializer(
            instance=self.paginate_queryset(self.queryset), many=True
        )
        return self.get_paginated_response(serialized.data)

    @swagger_auto_schema(
        request_body=CreateLegalBasisSerializer,
        responses={status.HTTP_200_OK: LegalBasisSerializer},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
