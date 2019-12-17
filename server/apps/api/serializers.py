from rest_framework import serializers
from server.apps.main.models import Consent, LegalBasis

class ConsentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Consent
        fields = '__all__'

class LegalBasisSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalBasis
        fields = '__all__'
        queryset = LegalBasis.objects.prefetch_related('consent_set').all()
