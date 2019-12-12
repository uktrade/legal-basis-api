from csp.decorators import csp_exempt
from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from server.apps.api.views.schema import schema_view

app_name = 'api'
router = DefaultRouter()
urlpatterns = [
    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema_json'),
    url(r'^swagger/$', csp_exempt((schema_view.with_ui('swagger', cache_timeout=0))), name='schema_swagger_ui'),
]

urlpatterns += router.urls
