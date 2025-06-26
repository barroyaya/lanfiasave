# users/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model

from donations.serializers import DonSerializer
from .models import PersonneVulnerable

User = get_user_model()

class PersonneVulnerableSerializer(serializers.ModelSerializer):
    dons_recus = DonSerializer(source='dons', many=True, read_only=True)
    class Meta:
        model = PersonneVulnerable
        fields = '__all__'
        # Le champ "user" ne peut être modifié via l’API – il restera None jusqu’à ce que l’admin l’associe.
        read_only_fields = ('user',)

class UserSerializer(serializers.ModelSerializer):
    recensed_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'is_donator', 'is_vulnerable', 'is_recenseur', 'recensed_count']

    def get_recensed_count(self, obj):
        # Si l'utilisateur est recenseur, renvoie le nombre de personnes recensées
        if obj.is_recenseur:
            return obj.personnes_recensees.count()
        return None

class AccountAssignmentSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        return value

    def create_account(self, personne: PersonneVulnerable):
        username = self.validated_data['username']
        password = self.validated_data['password']
        # Créer l'utilisateur avec create_user pour hacher le mot de passe
        user = User.objects.create_user(username=username, password=password)
        # Forcer les rôles : ce compte est destiné à une personne vulnérable
        user.is_vulnerable = True
        user.is_donator = False  # Désactiver le statut donateur si présent
        user.save()
        # Lier le compte au profil et marquer le profil comme validé
        personne.user = user
        personne.validated_by_admin = True
        personne.est_vulnerable = True
        personne.save()
        return user
