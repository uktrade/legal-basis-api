from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from rest_framework.fields import DateTimeField

from server.apps.main.models import Commit, Consent, LegalBasis


class LegalBasisSerializer(serializers.ModelSerializer):

    consents = serializers.SlugRelatedField(
        many=True,
        allow_null=True,
        allow_empty=True,
        queryset=Consent.objects.all(),
        slug_field="name",
    )
    modified_at = DateTimeField(required=False)

    class Meta:
        model = LegalBasis
        exclude = ["commit"]
        depth = 1


class CreateLegalBasisSerializer(LegalBasisSerializer):

    email = serializers.EmailField(required=False)
    phone = PhoneNumberField(required=False)
    modified_at = serializers.DateTimeField(required=False)

    def to_internal_value(self, data):
        data["key_type"] = "email" if data.get("email") else "phone"
        return super().to_internal_value(data)

    def create(self, validated_data):
        commit = Commit()
        request = self.context.get("request")
        if request:
            commit.source = request.path
        commit.save()
        validated_data["commit_id"] = commit.pk
        return super().create(validated_data)

    def validate(self, attrs):
        if not any([attrs.get("email"), attrs.get("phone")]):
            raise serializers.ValidationError("One of email or phone must be supplied")
        return super().validate(attrs)

    class Meta(LegalBasisSerializer.Meta):
        exclude = ["commit", "key", "created_at", "current", "id"]
        read_only = ["key"]


class EmailListField(serializers.ListField):
    child = serializers.EmailField()


class ListOfEmailsSerializer(serializers.Serializer):
    emails = EmailListField()
