# formation/forms.py
from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from .models import (
    DemandeFormation, ProjetVie, Formation,
    ParcoursFormation, SuiviProgression
)


class DemandeFormationForm(forms.ModelForm):
    """Formulaire de demande de formation"""

    class Meta:
        model = DemandeFormation
        fields = [
            'motivation_principale',
            'experience_anterieure',
            'competences_actuelles',
            'disponibilite_horaire',
            'contraintes_personnelles',
            'a_idee_projet',
            'description_projet',
            'souhaite_financement',
            'montant_financement',
            'accepte_mentoring'
        ]

        widgets = {
            'motivation_principale': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'experience_anterieure': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Décrivez votre expérience dans ce domaine...'
            }),
            'competences_actuelles': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Quelles compétences possédez-vous déjà ?'
            }),
            'disponibilite_horaire': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Lundi-Vendredi 9h-17h, Week-ends libres...'
            }),
            'contraintes_personnelles': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Contraintes familiales, de transport, etc.'
            }),
            'a_idee_projet': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'onchange': 'toggleProjetFields()'
            }),
            'description_projet': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Décrivez votre idée de projet post-formation...'
            }),
            'souhaite_financement': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'onchange': 'toggleFinancementField()'
            }),
            'montant_financement': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Montant en FCFA',
                'min': '0'
            }),
            'accepte_mentoring': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'checked': True
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Labels personnalisés
        self.fields['motivation_principale'].label = "Quelle est votre motivation principale ?"
        self.fields['experience_anterieure'].label = "Avez-vous une expérience dans ce domaine ?"
        self.fields['competences_actuelles'].label = "Quelles compétences possédez-vous actuellement ?"
        self.fields['disponibilite_horaire'].label = "Quelle est votre disponibilité horaire ?"
        self.fields['contraintes_personnelles'].label = "Avez-vous des contraintes particulières ?"
        self.fields['a_idee_projet'].label = "Avez-vous une idée de projet après la formation ?"
        self.fields['description_projet'].label = "Décrivez votre projet"
        self.fields['souhaite_financement'].label = "Souhaitez-vous un financement pour votre projet ?"
        self.fields['montant_financement'].label = "Montant de financement souhaité (FCFA)"
        self.fields['accepte_mentoring'].label = "Acceptez-vous d'être accompagné(e) par un mentor ?"

        # Champs conditionnels
        self.fields['description_projet'].required = False
        self.fields['montant_financement'].required = False

    def clean(self):
        cleaned_data = super().clean()
        a_idee_projet = cleaned_data.get('a_idee_projet')
        description_projet = cleaned_data.get('description_projet')
        souhaite_financement = cleaned_data.get('souhaite_financement')
        montant_financement = cleaned_data.get('montant_financement')

        # Validation conditionnelle pour le projet
        if a_idee_projet and not description_projet:
            self.add_error('description_projet', 'Veuillez décrire votre projet.')

        # Validation conditionnelle pour le financement
        if souhaite_financement and not montant_financement:
            self.add_error('montant_financement', 'Veuillez indiquer le montant souhaité.')

        return cleaned_data


class ProjetVieForm(forms.ModelForm):
    """Formulaire de création de projet de vie"""

    class Meta:
        model = ProjetVie
        fields = [
            'titre_projet',
            'description',
            'secteur_activite',
            'budget_estime',
            'type_financement'
        ]

        widgets = {
            'titre_projet': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Atelier de couture, Exploitation maraîchère...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Décrivez en détail votre projet d\'entreprise...'
            }),
            'secteur_activite': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Agriculture, Artisanat, Commerce...'
            }),
            'budget_estime': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Budget total en FCFA',
                'min': '0'
            }),
            'type_financement': forms.Select(attrs={
                'class': 'form-select'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Labels
        self.fields['titre_projet'].label = "Titre de votre projet"
        self.fields['description'].label = "Description détaillée"
        self.fields['secteur_activite'].label = "Secteur d'activité"
        self.fields['budget_estime'].label = "Budget estimé (FCFA)"
        self.fields['type_financement'].label = "Type de financement souhaité"

        # Validation
        self.fields['budget_estime'].validators = [MinValueValidator(1000)]


class FormationForm(forms.ModelForm):
    """Formulaire d'administration des formations"""

    class Meta:
        model = Formation
        fields = [
            'nom',
            'type_formation',
            'description',
            'duree_semaines',
            'niveau_requis',
            'age_min',
            'age_max',
            'cout_formation',
            'places_disponibles',
            'competences_acquises',
            'prerequis_materiels',
            'est_active'
        ]

        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de la formation'
            }),
            'type_formation': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Description de la formation...'
            }),
            'duree_semaines': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '104'
            }),
            'niveau_requis': forms.Select(attrs={
                'class': 'form-select'
            }),
            'age_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '16',
                'max': '65'
            }),
            'age_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '18',
                'max': '65'
            }),
            'cout_formation': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'places_disponibles': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'competences_acquises': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Liste des compétences que les participants acquerront...'
            }),
            'prerequis_materiels': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Matériel nécessaire pour suivre la formation...'
            }),
            'est_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        age_min = cleaned_data.get('age_min')
        age_max = cleaned_data.get('age_max')

        if age_min and age_max and age_min >= age_max:
            self.add_error('age_max', 'L\'âge maximum doit être supérieur à l\'âge minimum.')

        return cleaned_data


class EvaluationSuiviForm(forms.ModelForm):
    """Formulaire d'évaluation et suivi"""

    class Meta:
        model = SuiviProgression
        fields = [
            'type_suivi',
            'titre',
            'description',
            'note_progression',
            'points_forts',
            'points_amelioration',
            'prochaines_etapes'
        ]

        widgets = {
            'type_suivi': forms.Select(attrs={
                'class': 'form-select'
            }),
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de l\'évaluation'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Description détaillée de l\'évaluation...'
            }),
            'note_progression': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '10',
                'step': '0.1'
            }),
            'points_forts': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Points forts observés...'
            }),
            'points_amelioration': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Points à améliorer...'
            }),
            'prochaines_etapes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Prochaines étapes recommandées...'
            })
        }


class ParcoursFormationForm(forms.ModelForm):
    """Formulaire de gestion du parcours de formation"""

    class Meta:
        model = ParcoursFormation
        fields = [
            'date_debut_formation',
            'date_fin_formation',
            'date_certification',
            'statut_actuel',
            'pourcentage_completion',
            'note_formation',
            'competences_validees',
            'financement_obtenu',
            'type_financement_obtenu',
            'mentor_assigne'
        ]

        widgets = {
            'date_debut_formation': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_fin_formation': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_certification': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'statut_actuel': forms.Select(attrs={
                'class': 'form-select'
            }),
            'pourcentage_completion': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100'
            }),
            'note_formation': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '20',
                'step': '0.5'
            }),
            'competences_validees': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Liste des compétences validées...'
            }),
            'financement_obtenu': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'type_financement_obtenu': forms.Select(attrs={
                'class': 'form-select'
            }),
            'mentor_assigne': forms.Select(attrs={
                'class': 'form-select'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrer les mentors (staff ou superuser)
        from users.models import User
        self.fields['mentor_assigne'].queryset = User.objects.filter(
            models.Q(is_staff=True) | models.Q(is_superuser=True)
        )
        self.fields['mentor_assigne'].empty_label = "Aucun mentor assigné"


class RechercheFormationForm(forms.Form):
    """Formulaire de recherche de formations"""

    TYPE_FORMATION_CHOICES = [('', 'Tous les types')] + Formation.TYPE_FORMATION_CHOICES
    NIVEAU_REQUIS_CHOICES = [('', 'Tous les niveaux')] + Formation.NIVEAU_REQUIS_CHOICES

    recherche = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher une formation...'
        })
    )

    type_formation = forms.ChoiceField(
        choices=TYPE_FORMATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    niveau_requis = forms.ChoiceField(
        choices=NIVEAU_REQUIS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    duree_max = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Durée max (semaines)',
            'min': '1'
        })
    )

    cout_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Coût max (FCFA)',
            'min': '0'
        })
    )


class FiltreDemandesForm(forms.Form):
    """Formulaire de filtrage des demandes pour l'admin"""

    STATUT_CHOICES = [('', 'Tous les statuts')] + DemandeFormation.STATUT_CHOICES

    statut = forms.ChoiceField(
        choices=STATUT_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    formation = forms.ModelChoiceField(
        queryset=Formation.objects.filter(est_active=True),
        required=False,
        empty_label="Toutes les formations",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    score_min = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Score min',
            'min': '0',
            'max': '100'
        })
    )

    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class DecisionDemandeForm(forms.Form):
    """Formulaire de prise de décision sur une demande"""

    DECISION_CHOICES = [
        ('accepter', 'Accepter'),
        ('refuser', 'Refuser'),
        ('conditionner', 'Accepter sous conditions')
    ]

    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )

    commentaire = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Commentaire sur la décision...'
        })
    )

    conditions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Conditions à remplir (si applicable)...'
        })
    )

    date_debut_formation = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    mentor_assigne = forms.ModelChoiceField(
        required=False,
        queryset=None,  # Sera défini dans __init__
        empty_label="Aucun mentor",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Récupérer les mentors disponibles
        from users.models import User
        self.fields['mentor_assigne'].queryset = User.objects.filter(
            models.Q(is_staff=True) | models.Q(is_superuser=True)
        ).order_by('username')

    def clean(self):
        cleaned_data = super().clean()
        decision = cleaned_data.get('decision')
        conditions = cleaned_data.get('conditions')

        if decision == 'conditionner' and not conditions:
            self.add_error('conditions', 'Veuillez spécifier les conditions.')

        return cleaned_data