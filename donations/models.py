# donations/models.py

from django.db import models
from users.models import PersonneVulnerable, User


class Don(models.Model):
    entite_vulnerable = models.CharField(max_length=100)  # Exemple: femme_enceinte, enfants_handicapes
    personne_vulnerable = models.ManyToManyField(PersonneVulnerable, related_name="dons",blank=True)  # Relation avec PersonneVulnerable
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    donateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dons')
    provenance = models.CharField(max_length=100)  # Source du don
    description = models.TextField()  # Raison du don, précisions sur les personnes concernées
    est_valide = models.BooleanField(default=False)  # Le don est-il validé par l'admin ?
    est_reparti = models.BooleanField(default=False)  # Champ indiquant si le don est réparti
    est_retires = models.BooleanField(default=False)  # Champ indiquant si le don est retiré
    date_don = models.DateTimeField(auto_now_add=True)

    # nombre_personnes = models.PositiveIntegerField(default=1)  # Nombre de personnes à soutenir dans l'entité choisie

    def __str__(self):
        return f"Don de {self.donateur.username} - {self.montant} €"
