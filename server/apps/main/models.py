import hashlib

from django.contrib.postgres.fields import CIEmailField
from django.contrib.postgres.fields.jsonb import JSONField
from django.db import models
from django.db.models import Max, Q
from django.db.models.fields import TextField
from django.utils import timezone
from extended_choices import AutoChoices
from phonenumber_field.modelfields import PhoneNumberField
from typing_extensions import final

# noinspection PyTypeChecker
KEY_TYPE = AutoChoices("EMAIL", "PHONE")


@final
class Consent(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()

    def __str__(self) -> str:
        return f"{self.name}"


@final
class Commit(models.Model):

    created_at = models.DateTimeField(auto_now=True)
    source = TextField()
    extra = JSONField(default=dict)

    def __str__(self) -> str:
        return f"created: {self.created_at}, source: {self.source}"


class LegalBasis(models.Model):
    """
    Main model for querying about legal basis, the primary key is
    an email address. You can see this to find the consent types an
    email address has consented to.
    """

    key = models.BinaryField(null=False)
    email = CIEmailField(db_index=True)
    phone = PhoneNumberField(db_index=True)
    key_type = TextField(choices=KEY_TYPE, blank=False)

    consents = models.ManyToManyField(Consent)
    commit = models.ForeignKey(Commit, on_delete=models.PROTECT)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    current = models.BooleanField(default=False, db_index=True)

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if self.email:
            self.email = self.email.lower()

        if not self.key:
            to_hash = self.email + str(self.phone)
            hasher = hashlib.sha512(to_hash.encode())
            self.key = hasher.digest()

        last_modified = (
            LegalBasis.objects.filter(key=self.key)
            .exclude(id=self.id)
            .aggregate(Max("modified_at"))["modified_at__max"]
        )

        if not self.modified_at:
            self.modified_at = timezone.now()

        if last_modified is None or self.modified_at > last_modified:
            self.current = True
            LegalBasis.objects.filter(key=self.key).exclude(id=self.id).update(
                current=False
            )

        return super(LegalBasis, self).save(
            force_insert, force_update, using, update_fields
        )

    def __str__(self) -> str:
        return f"{self.email}"

    class Meta:
        verbose_name_plural = "LegalBases"
        indexes = [
            models.Index(fields=["email", "-modified_at"]),
            models.Index(fields=["phone", "-modified_at"]),
            models.Index(fields=["key", "-modified_at"]),
            models.Index(fields=["key", "key_type", "-modified_at"]),
            models.Index(fields=["key", "current"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=(Q(email="") & ~Q(phone="")) | (~Q(email="") & Q(phone="")),
                name="only_one_key",
            )
        ]
