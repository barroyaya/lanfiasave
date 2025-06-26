# donations/serializers.py
from rest_framework import serializers
from .models import Don

class DonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Don
        # On inclut tous les champs du modèle Don
        fields = '__all__'
        # Certains champs ne doivent pas être modifiables via l'API (ils sont gérés automatiquement)
        read_only_fields = ('donateur', 'est_valide', 'est_reparti', 'est_retires', 'date_don')
