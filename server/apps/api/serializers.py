import types

from django.conf import settings
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


class LegalBasisDataWorkspaceSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        """
        Create {consent_type}_consent field for each Consent type.

        This flattens consent status in the API response, rather than returning
        nested serialized Consent objects
        """
        super(LegalBasisDataWorkspaceSerializer, self).__init__(*args, **kwargs)

        for name in settings.CONSENT_TYPES:
            field_name = f"{name}_consent"
            method_name = f"get_{field_name}"

            def wrapper(name) -> types.MethodType:
                def inner(self, obj) -> bool:
                    return name in [c.name for c in obj.consents.all()]

                return types.MethodType(inner, self)

            setattr(self, method_name, wrapper(name))

            self.fields[field_name] = serializers.SerializerMethodField(
                method_name=method_name
            )

    class Meta:
        model = LegalBasis
        exclude = ["consents", "commit"]


class CreateLegalBasisSerializer(LegalBasisSerializer):

    email = serializers.EmailField(required=False)
    phone = PhoneNumberField(required=False)
    modified_at = serializers.DateTimeField(required=False)

    def to_internal_value(self, data):
        data = data.copy()
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
        if not attrs.get(attrs["key_type"]):
            raise serializers.ValidationError(
                f"{attrs['key_type']} must be provided if key type is {attrs['key_type']}"
            )
        if not any([attrs.get("email"), attrs.get("phone")]):
            raise serializers.ValidationError("One of email or phone must be supplied")

        if all([attrs.get("email"), attrs.get("phone")]):
            raise serializers.ValidationError(
                "Both email or phone must not be supplied"
            )

        return super().validate(attrs)

    class Meta(LegalBasisSerializer.Meta):
        exclude = ["commit", "key", "created_at", "current", "id"]
        read_only = ["key"]


class EmailListField(serializers.ListField):
    child = serializers.EmailField()


class ListOfEmailsSerializer(serializers.Serializer):
    emails = EmailListField()
