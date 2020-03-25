from django.db import migrations

from server.apps.main.models import Consent

# Also present in settings.common, but hardcoded here
# so that migrations don't break if the settings are changed
CONSENT_TYPES = ("email_marketing", "phone_marketing")


class Migration(migrations.Migration):
    def create_consent(apps, schema_editor):
        for name in CONSENT_TYPES:
            Consent.objects.get_or_create(name=name)

    def delete_consent(apps, schema_editor):
        for name in CONSENT_TYPES:
            Consent.objects.get(name=name).delete()

    dependencies = [
        ("main", "0002_auto_20200218_1028"),
    ]

    operations = [
        migrations.RunPython(create_consent, delete_consent),
    ]
