import csv

from django.contrib import admin
from django.contrib.auth.models import Permission

from django.http import HttpRequest, HttpResponse
from rest_framework.authtoken.admin import TokenAdmin

from server.apps.main.models import Commit, Consent, LegalBasis, LegalBasisCurrent


class LegalBasisAdmin(admin.ModelAdmin):

    search_fields = ("email", "phone")

    readonly_fields = ("key", "current")

    list_display = ("key_type", "email", "phone", "modified_at")

    def export_as_csv(self, request, queryset):
        consent_types = list(Consent.objects.all().values_list("name", flat=True))
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename={}.csv".format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names + consent_types)
        for obj in queryset:
            obj_consents = list(obj.consents.all().values_list("name", flat=True))
            row = [getattr(obj, field) for field in field_names]
            row += [consent_type in obj_consents for consent_type in consent_types]

            writer.writerow(row)

        return response

    # noinspection PyTypeHints
    export_as_csv.short_description = "Export as CSV"  # type: ignore


class LegalBasisCurrentAdmin(LegalBasisAdmin):
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False


# Register your models here.
admin.site.register(LegalBasis, LegalBasisAdmin)
admin.site.register(LegalBasisCurrent, LegalBasisCurrentAdmin)
admin.site.register(Consent)
admin.site.register(Commit)
admin.site.register(Permission)

# Recommended by drf docs: https://www.django-rest-framework.org/api-guide/authentication/#with-django-admin
TokenAdmin.raw_id_fields = ["user"]
