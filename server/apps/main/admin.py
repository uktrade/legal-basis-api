from django.contrib import admin  # noqa: F401

from server.apps.main.models import LegalBasis, Consent

# Register your models here.
admin.site.register(LegalBasis)
admin.site.register(Consent)
