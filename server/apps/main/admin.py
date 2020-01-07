from django.contrib import admin
from rest_framework.authtoken.admin import TokenAdmin

from server.apps.main.models import Consent, LegalBasis

# Register your models here.
admin.site.register(LegalBasis)
admin.site.register(Consent)

# Recommended by drf docs: https://www.django-rest-framework.org/api-guide/authentication/#with-django-admin
TokenAdmin.raw_id_fields = ["user"]
