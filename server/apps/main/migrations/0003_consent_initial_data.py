
from django.conf import settings
from django.db import migrations

from server.apps.main.models import Consent


class Migration(migrations.Migration):

    def create_consent(apps, schema_editor):
        for name in settings.CONSENT_TYPES:
            Consent.objects.get_or_create(name=name)

    def delete_consent(apps, schema_editor):
        for name in settings.CONSENT_TYPES:
            Consent.objects.get(name=name).delete()

    dependencies = [
        ('main', '0002_auto_20200218_1028'),
    ]

    operations = [
        migrations.RunPython(create_consent, delete_consent),
    ]
