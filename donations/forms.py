# donations/forms.py
from django import forms
from users.models import PersonneVulnerable

from django import forms
from users.models import PersonneVulnerable

# from django import forms
# from users.models import PersonneVulnerable
#
# class DonationForm(forms.Form):
#     montant = forms.DecimalField(max_digits=10, decimal_places=2, label="Montant")
#
#     ENTITES = [
#         ('femme_enceinte', 'Femmes Enceintes'),
#         ('enfants_handicapes', 'Enfants Handicapés'),
#         ('enfants_de_la_rue', 'Enfants de la Rue'),
#         ('autres', 'Autres'),
#     ]
#     entite_vulnerable = forms.ChoiceField(choices=ENTITES, label="Entité vulnérable")
#
#     provenance = forms.CharField(max_length=100, label="Provenance")
#     description = forms.CharField(widget=forms.Textarea, label="Description", required=False)
#     nombre_personnes = forms.IntegerField(min_value=1, label="Nombre de personnes", initial=1)
#
#     # Ce champ sera mis à jour dynamiquement via JavaScript
#     personne_vulnerable = forms.ModelMultipleChoiceField(queryset=PersonneVulnerable.objects.filter(est_vulnerable=True), required=False, label="Personnes vulnérables")
#
#     def __init__(self, *args, **kwargs):
#         # On prend l'entité choisie et on filtre les personnes vulnérables
#         entite = kwargs.pop('entite', None)
#         super().__init__(*args, **kwargs)
#
#         # Filtrage des personnes vulnérables basé sur l'entité
#         if entite:
#             self.fields['personne_vulnerable'].queryset = PersonneVulnerable.objects.filter(entite=entite, est_vulnerable=True)
#
#     def clean_montant(self):
#         montant = self.cleaned_data['montant']
#         if montant <= 0:
#             raise forms.ValidationError("Le montant doit être supérieur à zéro.")
#         return montant

from django import forms
from users.models import PersonneVulnerable
from decimal import Decimal


class DonationForm(forms.Form):
    montant = forms.DecimalField(max_digits=10, decimal_places=2, label="Montant")

    ENTITES = [
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

    entite_vulnerable = forms.ChoiceField(choices=ENTITES, label="Entité vulnérable")

    provenance = forms.CharField(max_length=100, label="Provenance")
    description = forms.CharField(widget=forms.Textarea, label="Description", required=False)

    # Dynamically populated based on the selected entity
    personne_vulnerable = forms.ModelMultipleChoiceField(
        queryset=PersonneVulnerable.objects.filter(est_vulnerable=True),
        required=False,
        label="Personnes vulnérables"
    )

    # Number of people the donor wants to support
    # nombre_personnes = forms.IntegerField(min_value=1, label="Nombre de personnes", initial=1)

    def __init__(self, *args, **kwargs):
        entite = kwargs.pop('entite', None)  # Get the entity if passed in
        super().__init__(*args, **kwargs)

        # Filter vulnerable people based on the entity selected
        if entite:
            self.fields['personne_vulnerable'].queryset = PersonneVulnerable.objects.filter(entite=entite,
                                                                                            est_vulnerable=True)
        else:
            self.fields['personne_vulnerable'].queryset = PersonneVulnerable.objects.filter(est_vulnerable=True)

    def clean_montant(self):
        montant = self.cleaned_data['montant']
        if montant <= 0:
            raise forms.ValidationError("Le montant doit être supérieur à zéro.")
        return montant
