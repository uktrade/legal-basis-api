from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title='Consent API',
        default_version='v1',
        description='Legal Basis for Consent',
        contact=openapi.Contact(email='consent-service@digital.trade.gov.uk'),
        license=openapi.License(name='MIT License'),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
