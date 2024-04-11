from csp.decorators import csp_exempt
from django.urls import re_path
from rest_framework.routers import DefaultRouter

from server.apps.api.views.legal_basis import LegalBasisViewSet
from server.apps.api.views.schema import schema_view

app_name = "api"
router = DefaultRouter()
router.include_format_suffixes = False

router.register("person", LegalBasisViewSet)

urlpatterns = [
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema_json",
    ),
    re_path(
        r"^swagger/$",
        csp_exempt((schema_view.with_ui("swagger", cache_timeout=0))),
        name="schema_swagger_ui",
    ),
]

urlpatterns += router.urls
