# formation/models.py
from django.db import models
from django.conf import settings
from users.models import PersonneVulnerable
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Formation(models.Model):
    """Modèle pour les différents types de formations disponibles"""

    TYPE_FORMATION_CHOICES = [
        ('agriculture', 'Agriculture'),
        ('couture', 'Couture'),
        ('mecanique', 'Mécanique'),
        ('cuisine', 'Cuisine'),
        ('tic', 'Technologies de l\'Information'),
        ('menuiserie', 'Menuiserie'),
        ('coiffure', 'Coiffure'),
        ('commerce', 'Commerce'),
        ('artisanat', 'Artisanat'),
        ('elevage', 'Élevage'),
        ('autre', 'Autre'),
    ]

    NIVEAU_REQUIS_CHOICES = [
        ('aucun', 'Aucun prérequis'),
        ('primaire', 'Niveau primaire'),
        ('secondaire', 'Niveau secondaire'),
        ('technique', 'Formation technique antérieure'),
    ]

    nom = models.CharField(max_length=200, verbose_name="Nom de la formation")
    type_formation = models.CharField(
        max_length=50,
        choices=TYPE_FORMATION_CHOICES,
        verbose_name="Type de formation"
    )
    description = models.TextField(verbose_name="Description de la formation")
    duree_semaines = models.PositiveIntegerField(
        verbose_name="Durée en semaines",
        validators=[MinValueValidator(1), MaxValueValidator(104)]
    )
    niveau_requis = models.CharField(
        max_length=50,
        choices=NIVEAU_REQUIS_CHOICES,
        default='aucun',
        verbose_name="Niveau requis"
    )
    age_min = models.PositiveIntegerField(
        default=18,
        verbose_name="Âge minimum"
    )
    age_max = models.PositiveIntegerField(
        default=45,
        verbose_name="Âge maximum"
    )
    cout_formation = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Coût de la formation (FCFA)"
    )
    places_disponibles = models.PositiveIntegerField(
        default=20,
        verbose_name="Nombre de places disponibles"
    )
    est_active = models.BooleanField(
        default=True,
        verbose_name="Formation active"
    )
    competences_acquises = models.TextField(
        verbose_name="Compétences acquises",
        help_text="Liste des compétences que les participants acquerront"
    )
    prerequis_materiels = models.TextField(
        blank=True,
        verbose_name="Prérequis matériels",
        help_text="Matériel nécessaire pour suivre la formation"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Formation"
        verbose_name_plural = "Formations"
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.get_type_formation_display()})"

    def places_restantes(self):
        """Calcule le nombre de places restantes"""
        places_prises = self.demandes_formation.filter(
            statut__in=['acceptee', 'en_cours', 'terminee']
        ).count()
        return max(0, self.places_disponibles - places_prises)


class ProjetVie(models.Model):
    """Modèle pour les projets de vie des bénéficiaires"""

    STATUT_PROJET_CHOICES = [
        ('idee', 'Idée'),
        ('planification', 'En planification'),
        ('validation', 'En validation'),
        ('finance', 'Financé'),
        ('en_cours', 'En cours de réalisation'),
        ('realise', 'Réalisé'),
        ('abandonne', 'Abandonné'),
    ]

    TYPE_FINANCEMENT_CHOICES = [
        ('autofinancement', 'Autofinancement'),
        ('microcredit', 'Microcrédit'),
        ('subvention', 'Subvention'),
        ('investisseur', 'Investisseur privé'),
        ('mixte', 'Financement mixte'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    personne = models.ForeignKey(
        PersonneVulnerable,
        on_delete=models.CASCADE,
        related_name='projets_vie',
        verbose_name="Personne"
    )
    titre_projet = models.CharField(
        max_length=200,
        verbose_name="Titre du projet"
    )
    description = models.TextField(verbose_name="Description du projet")
    secteur_activite = models.CharField(
        max_length=100,
        verbose_name="Secteur d'activité"
    )
    budget_estime = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Budget estimé (FCFA)"
    )
    type_financement = models.CharField(
        max_length=50,
        choices=TYPE_FINANCEMENT_CHOICES,
        verbose_name="Type de financement souhaité"
    )
    statut = models.CharField(
        max_length=50,
        choices=STATUT_PROJET_CHOICES,
        default='idee',
        verbose_name="Statut du projet"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_maj = models.DateTimeField(auto_now=True)

    # Analyse IA
    faisabilite_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Score de faisabilité (%)"
    )
    analyse_ia = models.TextField(
        blank=True,
        verbose_name="Analyse par IA"
    )
    recommandations = models.TextField(
        blank=True,
        verbose_name="Recommandations"
    )

    class Meta:
        verbose_name = "Projet de vie"
        verbose_name_plural = "Projets de vie"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.titre_projet} - {self.personne.get_full_name()}"


class DemandeFormation(models.Model):
    """Modèle pour les demandes de formation"""

    STATUT_CHOICES = [
        ('en_attente', 'En attente d\'analyse'),
        ('analysee', 'Analysée par IA'),
        ('acceptee', 'Acceptée'),
        ('refusee', 'Refusée'),
        ('en_cours', 'Formation en cours'),
        ('terminee', 'Formation terminée'),
        ('abandonnee', 'Formation abandonnée'),
    ]

    MOTIVATION_CHOICES = [
        ('emploi', 'Trouver un emploi'),
        ('autonomie', 'Devenir autonome'),
        ('creation_entreprise', 'Créer une entreprise'),
        ('amelioration_competences', 'Améliorer mes compétences'),
        ('reconversion', 'Me reconvertir'),
        ('passion', 'Suivre ma passion'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    personne = models.ForeignKey(
        PersonneVulnerable,
        on_delete=models.CASCADE,
        related_name='demandes_formation',
        verbose_name="Demandeur"
    )
    formation_souhaitee = models.ForeignKey(
        Formation,
        on_delete=models.CASCADE,
        related_name='demandes_formation',
        verbose_name="Formation souhaitée"
    )

    # Informations sur la motivation et le projet
    motivation_principale = models.CharField(
        max_length=50,
        choices=MOTIVATION_CHOICES,
        verbose_name="Motivation principale"
    )
    experience_anterieure = models.TextField(
        blank=True,
        verbose_name="Expérience antérieure dans le domaine"
    )
    competences_actuelles = models.TextField(
        blank=True,
        verbose_name="Compétences actuelles"
    )

    # Disponibilité
    disponibilite_horaire = models.CharField(
        max_length=100,
        verbose_name="Disponibilité horaire"
    )
    contraintes_personnelles = models.TextField(
        blank=True,
        verbose_name="Contraintes personnelles"
    )

    # Projet post-formation
    a_idee_projet = models.BooleanField(
        default=False,
        verbose_name="A une idée de projet post-formation"
    )
    description_projet = models.TextField(
        blank=True,
        verbose_name="Description du projet envisagé"
    )
    souhaite_financement = models.BooleanField(
        default=False,
        verbose_name="Souhaite un financement après formation"
    )
    montant_financement = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Montant de financement estimé (FCFA)"
    )
    accepte_mentoring = models.BooleanField(
        default=True,
        verbose_name="Accepte d'être accompagné par un mentor"
    )

    # Statut et suivi
    statut = models.CharField(
        max_length=50,
        choices=STATUT_CHOICES,
        default='en_attente',
        verbose_name="Statut de la demande"
    )
    date_demande = models.DateTimeField(auto_now_add=True)
    date_analyse = models.DateTimeField(null=True, blank=True)
    date_decision = models.DateTimeField(null=True, blank=True)

    # Analyse IA
    score_formabilite = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Score de formabilité (%)"
    )
    analyse_llm = models.TextField(
        blank=True,
        verbose_name="Analyse détaillée par LLM"
    )
    recommandations_llm = models.TextField(
        blank=True,
        verbose_name="Recommandations du LLM"
    )
    criteres_evaluacion = models.JSONField(
        default=dict,
        verbose_name="Critères d'évaluation détaillés"
    )

    # Feedback et suivi
    commentaire_decision = models.TextField(
        blank=True,
        verbose_name="Commentaire sur la décision"
    )
    responsable_decision = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Responsable de la décision"
    )

    class Meta:
        verbose_name = "Demande de formation"
        verbose_name_plural = "Demandes de formation"
        ordering = ['-date_demande']

    def __str__(self):
        return f"{self.personne.get_full_name()} - {self.formation_souhaitee.nom}"

    def get_badge_formabilite(self):
        """Retourne un badge basé sur le score de formabilité"""
        if not self.score_formabilite:
            return None

        if self.score_formabilite >= 80:
            return "Excellent candidat"
        elif self.score_formabilite >= 60:
            return "Bon candidat"
        elif self.score_formabilite >= 40:
            return "Candidat acceptable"
        else:
            return "Candidat à risque"


class ParcoursFormation(models.Model):
    """Modèle pour suivre le parcours de formation"""

    STATUT_PARCOURS_CHOICES = [
        ('pre_inscrit', 'Pré-inscrit à une formation'),
        ('forme', 'Formé(e)'),
        ('projet_valide', 'Projet validé'),
        ('financement_valide', 'Accompagnement financier validé'),
        ('suivi_3mois', 'Suivi 3 mois'),
        ('suivi_6mois', 'Suivi 6 mois'),
        ('suivi_12mois', 'Suivi 12 mois'),
        ('autonome', 'Autonome'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    demande_formation = models.OneToOneField(
        DemandeFormation,
        on_delete=models.CASCADE,
        related_name='parcours',
        verbose_name="Demande de formation"
    )

    # Dates importantes
    date_debut_formation = models.DateField(null=True, blank=True)
    date_fin_formation = models.DateField(null=True, blank=True)
    date_certification = models.DateField(null=True, blank=True)

    # Statut et progression
    statut_actuel = models.CharField(
        max_length=50,
        choices=STATUT_PARCOURS_CHOICES,
        default='pre_inscrit',
        verbose_name="Statut actuel"
    )
    pourcentage_completion = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Pourcentage de completion (%)"
    )

    # Évaluations
    note_formation = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name="Note de formation (/20)"
    )
    competences_validees = models.TextField(
        blank=True,
        verbose_name="Compétences validées"
    )

    # Projet post-formation
    projet_vie = models.ForeignKey(
        ProjetVie,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parcours_formation',
        verbose_name="Projet de vie associé"
    )

    # Financement
    financement_obtenu = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Financement obtenu (FCFA)"
    )
    type_financement_obtenu = models.CharField(
        max_length=50,
        choices=ProjetVie.TYPE_FINANCEMENT_CHOICES,
        blank=True,
        verbose_name="Type de financement obtenu"
    )

    # Suivi et mentoring
    mentor_assigne = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mentorings',
        verbose_name="Mentor assigné"
    )

    # Évaluations de suivi
    evaluation_3mois = models.TextField(blank=True, verbose_name="Évaluation 3 mois")
    evaluation_6mois = models.TextField(blank=True, verbose_name="Évaluation 6 mois")
    evaluation_12mois = models.TextField(blank=True, verbose_name="Évaluation 12 mois")

    date_creation = models.DateTimeField(auto_now_add=True)
    date_maj = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Parcours de formation"
        verbose_name_plural = "Parcours de formation"
        ordering = ['-date_creation']

    def __str__(self):
        return f"Parcours - {self.demande_formation.personne.get_full_name()}"

    def get_duree_formation_jours(self):
        """Calcule la durée de la formation en jours"""
        if self.date_debut_formation and self.date_fin_formation:
            return (self.date_fin_formation - self.date_debut_formation).days
        return None

    def is_formation_terminee(self):
        """Vérifie si la formation est terminée"""
        return self.statut_actuel in ['forme', 'projet_valide', 'financement_valide', 'suivi_3mois', 'suivi_6mois',
                                      'suivi_12mois', 'autonome']


class SuiviProgression(models.Model):
    """Modèle pour le suivi détaillé de la progression"""

    TYPE_SUIVI_CHOICES = [
        ('formation', 'Suivi formation'),
        ('projet', 'Suivi projet'),
        ('financement', 'Suivi financement'),
        ('mentoring', 'Session mentoring'),
        ('evaluation', 'Évaluation'),
    ]

    parcours = models.ForeignKey(
        ParcoursFormation,
        on_delete=models.CASCADE,
        related_name='suivis',
        verbose_name="Parcours"
    )
    date_suivi = models.DateTimeField(auto_now_add=True)
    type_suivi = models.CharField(
        max_length=50,
        choices=TYPE_SUIVI_CHOICES,
        verbose_name="Type de suivi"
    )
    titre = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(verbose_name="Description")
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Responsable du suivi"
    )

    # Évaluation
    note_progression = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Note progression (/10)"
    )
    points_forts = models.TextField(blank=True, verbose_name="Points forts")
    points_amelioration = models.TextField(blank=True, verbose_name="Points à améliorer")
    prochaines_etapes = models.TextField(blank=True, verbose_name="Prochaines étapes")

    class Meta:
        verbose_name = "Suivi de progression"
        verbose_name_plural = "Suivis de progression"
        ordering = ['-date_suivi']

    def __str__(self):
        return f"{self.titre} - {self.parcours.demande_formation.personne.get_full_name()}"