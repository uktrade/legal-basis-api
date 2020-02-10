from rest_framework import serializers
from rest_framework.fields import DateTimeField

from server.apps.main.models import Consent, LegalBasis


class LegalBasisSerializer(serializers.ModelSerializer):

    consents = serializers.SlugRelatedField(
        many=True,
        allow_null=True,
        allow_empty=True,
        queryset=Consent.objects.all(),
        slug_field="name",
    )
    modified_at = DateTimeField()

    class Meta:
        model = LegalBasis
        exclude = ["commit"]
        depth = 1


class EmailListField(serializers.ListField):
    child = serializers.EmailField()


class ListOfEmailsSerializer(serializers.Serializer):
    emails = EmailListField()
