# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

from users.managers import CustomUserManager


# ---------------------------
# 1) Modèle User personnalisé
# ---------------------------
class User(AbstractUser):
    """
    Utilisateur personnalisé avec trois attributs booléens
    pour distinguer les rôles (donateur, vulnérable, recenseur).
    """
    is_donator = models.BooleanField(default=False)
    is_vulnerable = models.BooleanField(default=False)
    is_recenseur = models.BooleanField(default=False)
    objects = CustomUserManager()


    @property
    def is_vulnerable_profile(self):
        """Retourne True si l'utilisateur a un profil PersonneVulnerable lié."""
        return hasattr(self, 'personnevulnerable')


# ---------------------------
# 2) Modèle PersonneVulnerable
# ---------------------------
class PersonneVulnerable(models.Model):
    ENTITE_CHOICES = [
        ('orphelin', 'Orphelin'),
        ('veuve', 'Veuve'),
        ('handicape', 'Handicapé'),
        ('senior', 'Senior'),
        ('refugie', 'Réfugié'),
        ('sans_abri', 'Sans Abri'),
        ('famille_nombreuse', 'Famille Nombreuse'),
        ('chomeur', 'Chômeur'),
        ('malade_chronique', 'Malade Chronique'),
        ('etudiant_precaire', 'Étudiant Précaire'),
    ]

    SEXE_CHOICES = [
        ('Homme', 'Homme'),
        ('Femme', 'Femme'),
    ]

    REGION_CHOICES = [
        ('Agnéby', 'Agnéby'),
        ('Bafing', 'Bafing'),
        ('Bas-Sassandra', 'Bas-Sassandra'),
        ('Denguélé', 'Denguélé'),
        ('District des Montagnes', 'District des Montagnes'),
        ('Fromager','Fromager'),
        ('Haut-Sassandra', 'Haut-Sassandra'),
        ('Lacs', 'Lacs'),
        ('Lagunes', 'Lagunes'),
        ('Marahoué', 'Marahoué'),
        ('Moyen-Cavally', 'Moyen-Cavally'),
        ('Moyen-Comoé', 'Moyen-Comoé'),
        ("N’zi-Comoé", "N’zi-Comoé"),
        ('Région du Sud-Comoé', 'Région du Sud-Comoé'),
        ('Savanes', 'Savanes'),
        ('Sud-Bandama', 'Sud-Bandama'),
        ('Vallée du Bandama', 'Vallée du Bandama'),
        ('Worodougou', 'Worodougou'),
        ('Zanzan', 'Zanzan'),
    ]

    # Liaison avec le user (facultative)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='personnevulnerable'
    )

    # Le recenseur éventuel (un autre user)
    recenseur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='personnes_recensees',
        verbose_name='Recenseur'
    )

    # Informations de base
    first_name = models.CharField(max_length=150, verbose_name="Prénom")
    last_name = models.CharField(max_length=150, verbose_name="Nom")
    sexe = models.CharField(
        max_length=5,
        choices=SEXE_CHOICES,
        default='Homme'
    )
    age = models.IntegerField(null=True, blank=True)
    nombre_enfants = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre d'enfants"
    )
    email = models.EmailField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)

    # Situation socio-économique
    est_vulnerable = models.BooleanField(default=False)
    entite = models.CharField(
        max_length=50,
        choices=ENTITE_CHOICES,
        default='autres'
    )
    revenu = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    montant_recu = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

    # Localisation
    region_geographique = models.CharField(
        max_length=100,
        choices=REGION_CHOICES,        # Menu déroulant pour la région
        null=True,
        blank=True,
        verbose_name="Région géographique"
    )

    # Validation
    validated_by_admin = models.BooleanField(
        default=False,
        verbose_name="Validé par l'administrateur"
    )
    # Dans models.py - ajouter ces champs à PersonneVulnerable
    photo = models.ImageField(
        upload_to='photos_recensement/',
        null=True,
        blank=True,
        verbose_name="Photo de profil"
    )
    # Ajouter ce champ pour le fichier document
    documents = models.FileField(
        upload_to='documents_recensement/',
        null=True,
        blank=True,
        verbose_name="Document principal"
    )
    # Pour gérer plusieurs documents, on peut utiliser un JSONField ou créer un modèle séparé
    documents_info = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Informations des documents"
    )
    def upload_documents_path(instance, filename):
        return f'documents_recensement/{instance.id}/{filename}'


    niveau_pauvrete = models.FloatField(null=True, blank=True)
    categorie_predite = models.CharField(max_length=50, null=True, blank=True)
    analyse_llm = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.entite}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
