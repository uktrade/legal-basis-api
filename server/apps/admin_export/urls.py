from django.urls import path

from server.apps.admin_export.views import ExportLegalBasisCSV


app_name = "admin_export"

urlpatterns = [
    path(
        "legal-basis-export", ExportLegalBasisCSV.as_view(), name="legal-basis-export"
    ),
]
