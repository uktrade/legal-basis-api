# Generated by Django 2.2.10 on 2020-03-25 15:54

import django.contrib.postgres.fields.citext
import phonenumber_field.modelfields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0004_legalbasiscurrent"),
    ]

    operations = [
        migrations.AlterField(
            model_name="legalbasis",
            name="consents",
            field=models.ManyToManyField(blank=True, to="main.Consent"),
        ),
        migrations.AlterField(
            model_name="legalbasis",
            name="email",
            field=django.contrib.postgres.fields.citext.CIEmailField(
                blank=True, db_index=True, max_length=254
            ),
        ),
        migrations.AlterField(
            model_name="legalbasis",
            name="phone",
            field=phonenumber_field.modelfields.PhoneNumberField(
                blank=True, db_index=True, max_length=128, region=None
            ),
        ),
    ]