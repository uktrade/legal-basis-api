from django.contrib import admin

from server.apps.main.models import Consent, LegalBasis

# Register your models here.
admin.site.register(LegalBasis)
admin.site.register(Consent)
