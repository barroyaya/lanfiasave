import json
from django import forms
from .models import PersonneVulnerable

class RecensementForm(forms.ModelForm):
    # Champs du modèle existants
    first_name = forms.CharField(
        label="Prénom",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrez le prénom'})
    )
    last_name = forms.CharField(
        label="Nom",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrez le nom'})
    )
    email = forms.EmailField(
        label="Adresse email",
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre adresse email'
        })
    )
    telephone = forms.CharField(
        label="Téléphone",
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre numéro de téléphone'
        })
    )
    age = forms.IntegerField(
        label="Âge",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': "Entrez l'âge"})
    )
    sexe = forms.ChoiceField(
        choices=[('Homme', 'Homme'), ('Femme', 'Femme')],
        label="Sexe",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Nouvelle colonne Région
    region = forms.ChoiceField(
        choices=[
            ('Abidjan','Abidjan'),
            ('Bouaké','Bouaké'),
            ('Daloa','Daloa'),
            ('Korhogo','Korhogo'),
            ('Man','Man'),
            ('San Pedro','San Pedro'),
            ('Yamoussoukro','Yamoussoukro')
        ],
        label="Région",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Champs additionnels du modèle
    situation_matrimoniale = forms.ChoiceField(
        choices=[('Célibataire','Célibataire'),('Marié','Marié'),('Divorcé','Divorcé'),('Veuf','Veuf')],
        label="Situation matrimoniale",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    logement = forms.ChoiceField(
        choices=[
            ('Maison en dur','Maison en dur'),
            ('Maison en terre','Maison en terre'),
            ('Abri précaire','Abri précaire'),
            ('Rue','Rue'),],
        label="Type de logement",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    source_eau = forms.ChoiceField(
        choices=[('Rivière','Rivière'),('Forage','Forage'),('Puits','Puits'),('Distribution','Distribution')],
        label="Source d'eau",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    type_sanitaires = forms.ChoiceField(
        choices=[
            ('Toilettes publiques','Toilettes publiques'),
            ('Toilettes domestiques','Toilettes domestiques'),
            ('Latrine','Latrine'),
            ('Toilette moderne','Toilette moderne'),
            ('Robinet','Robinet'),
            ('Aucun','Aucun')],
        label="Type de sanitaires",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    acces_electricite = forms.ChoiceField(
        choices=[('Oui','Oui'),('Non','Non')],
        label="Accès à l’électricité",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    emploi = forms.ChoiceField(
        choices=[('Stable','Emploi stable'),('Précaire','Emploi précaire'),('Aucun','Sans emploi'),
            ('Chômeur','Chômeur'),
            ('Auto-entrepreneur','Auto-entrepreneur'),
            ('Étudiant','Étudiant'),
            ('Retraité','Retraité'),
            ('Autre','Autre')],
        label="Situation professionnelle",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    revenu = forms.DecimalField(
        label="Revenu mensuel (FCFA)",
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Entrez le revenu mensuel'})
    )
    niveau_education = forms.ChoiceField(
        choices=[('Non-scolarisé','Non-scolarisé'),('Primaire','Primaire'),('Secondaire','Secondaire'),('Supérieur','Supérieur'), ('Autodidacte','Autodidacte')],
        label="Niveau d’éducation",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    etat_sante = forms.ChoiceField(
        choices=[
            ('Bon', 'Bon'),
            ('Précaire', 'Précaire'),
            ('Maladie chronique', 'Maladie chronique'),
            ('Maladie transmissible', 'Maladie transmissible')
        ],
        label="État de santé",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    handicap = forms.ChoiceField(
        choices=[('Oui','Oui'),('Non','Non')],
        label="Handicap",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    auto_eval_vulnerabilite = forms.ChoiceField(
        choices=[('Faible','Faible'),('Modérée','Modérée'),('Élevée','Élevée')],
        label="Auto-évaluation de vulnérabilité",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    enfants_non_scolarises = forms.IntegerField(
        label="Enfants non scolarisés",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Nombre d’enfants non scolarisés'})
    )
    nombre_personnes_menage = forms.IntegerField(
        label="Nombre de personnes dans le ménage",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Entrez le nombre de personnes'})
    )
    montant_total_recu = forms.DecimalField(
        label="Montant total reçu (allocations)",
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Entrez le montant total reçu'})
    )

    region_geographique = forms.ChoiceField(
        label="Région géographique",
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    commentaire = forms.CharField(
        label="Commentaires supplémentaires",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    # Dans forms.py - corriger les champs upload
    photo = forms.ImageField(
        label="Photo de profil",
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'file-input',
            'accept': 'image/*'
        })
    )

    # Pour les documents multiples, on utilise cette approche
    documents= forms.FileField(
        label="Documents officiels",
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'file-input',
            'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'
        })
    )

    class Meta:
        model = PersonneVulnerable
        fields = [
            'first_name', 'last_name','email', 'telephone', 'age', 'sexe', 'photo', 'documents', 'region',
            'situation_matrimoniale', 'logement', 'source_eau', 'type_sanitaires', 'acces_electricite',
            'emploi', 'revenu', 'niveau_education', 'etat_sante', 'handicap',
            'auto_eval_vulnerabilite', 'enfants_non_scolarises', 'nombre_personnes_menage', 'montant_total_recu',
            'region_geographique', 'commentaire'
        ]

    def clean_revenu(self):
        revenu = self.cleaned_data.get('revenu')
        if revenu is not None and revenu < 0:
            raise forms.ValidationError("Le revenu ne peut pas être négatif.")
        return revenu

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Charger le JSON pour régions dynamiques
        try:
            with open('donations/json_ci/IvoryCoast.json', encoding='utf-8') as f:
                data = json.load(f)
                regions = data.get('regions', [])
                choices = [(r['name'], r['name']) for r in regions if 'name' in r]
                self.fields['region_geographique'].choices = sorted(set(choices), key=lambda x: x[0])
        except FileNotFoundError:
            self.fields['region_geographique'].choices = []


# import json
# from django import forms
# from .models import PersonneVulnerable
#
# class RecensementForm(forms.ModelForm):
#     # 1. Champs du modèle
#     first_name = forms.CharField(
#         label="Prénom",
#         max_length=150,
#         widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrez le prénom'}),
#     )
#     last_name = forms.CharField(
#         label="Nom",
#         max_length=150,
#         widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrez le nom'}),
#     )
#     age = forms.IntegerField(
#         label="Âge",
#         widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': "Entrez l'âge"})
#     )
#     sexe = forms.ChoiceField(
#         choices=[('Homme', 'Homme'), ('Femme', 'Femme')],
#         label="Sexe",
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     nombre_enfants = forms.IntegerField(
#         label="Nombre d'enfants",
#         required=False,
#         widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': "Entrez le nombre d'enfants"})
#     )
#     revenu = forms.DecimalField(
#         label="Revenu mensuel",
#         max_digits=10,
#         decimal_places=2,
#         widget=forms.NumberInput(attrs={'class': 'form-control'})
#     )
#     entite = forms.ChoiceField(
#         choices=[('femme_enceinte', 'Femme Enceinte'),
#                  ('enfants_handicapes', 'Enfants Handicapés'),
#                  ('enfants_de_la_rue', 'Enfants de la Rue'),
#                  ('autres', 'Autres')],
#         label="Entité",
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     # region_geographique sera alimenté dynamiquement dans __init__:
#     region_geographique = forms.ChoiceField(
#         label="Région géographique",
#         choices=[],  # On va injecter les choix depuis le JSON dans __init__
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#
#     # 2. Champs supplémentaires (n'existant PAS dans le modèle)
#     #    => ils ne seront pas sauvegardés en base, car pas dans le Model ni dans Meta.fields
#     situation_matrimoniale = forms.ChoiceField(
#         choices=[('Célibataire', 'Célibataire'),
#                  ('Marié', 'Marié'),
#                  ('Divorcé', 'Divorcé'),
#                  ('Veuf', 'Veuf')],
#         label="Situation matrimoniale",
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     emploi = forms.ChoiceField(
#         choices=[('Emploi stable', 'Emploi stable'),
#                  ('Emploi précaire', 'Emploi précaire'),
#                  ('Sans emploi', 'Sans emploi')],
#         label="Emploi",
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     logement = forms.ChoiceField(
#         choices=[('Propriétaire', 'Propriétaire'),
#                  ('Locataire', 'Locataire'),
#                  ('Autre', 'Autre')],
#         label="Type de logement",
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     niveau_education = forms.ChoiceField(
#         choices=[('Non-scolarisé', 'Non-scolarisé'),
#                  ('Primaire', 'Primaire'),
#                  ('Secondaire', 'Secondaire'),
#                  ('Supérieur', 'Supérieur')],
#         label="Niveau d’éducation",
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     maladies_chroniques = forms.ChoiceField(
#         choices=[('Oui', 'Oui'), ('Non', 'Non')],
#         label="Maladies chroniques",
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     acces_soins = forms.ChoiceField(
#         choices=[('Accès facile', 'Accès facile'),
#                  ('Accès limité', 'Accès limité'),
#                  ('Accès difficile', 'Accès difficile')],
#         label="Accès aux soins de santé",
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     femme_enceinte = forms.ChoiceField(
#         choices=[('Oui', 'Oui'), ('Non', 'Non')],
#         label="Femmes enceintes",
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     handicap = forms.ChoiceField(
#         choices=[('Oui', 'Oui'), ('Non', 'Non')],
#         label="Handicap",
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     acces_eau_assainissement = forms.ChoiceField(
#         choices=[('Oui', 'Oui'), ('Non', 'Non')],
#         label="Accès à l'eau potable et assainissement",
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     violence_domestique = forms.ChoiceField(
#         choices=[('Oui', 'Oui'), ('Non', 'Non')],
#         label="Victime de violence domestique",
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     soutien_familial = forms.ChoiceField(
#         choices=[('Oui', 'Oui'), ('Non', 'Non')],
#         label="Soutien familial et social",
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     histoire_migration = forms.ChoiceField(
#         choices=[('Oui', 'Oui'), ('Non', 'Non')],
#         label="Histoire de migration",
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     historique_pauvrete = forms.ChoiceField(
#         choices=[('Oui', 'Oui'), ('Non', 'Non')],
#         label="Historique de pauvreté",
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     acces_aide = forms.ChoiceField(
#         choices=[('Oui', 'Oui'), ('Non', 'Non')],
#         label="Accès à des programmes d'aide",
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     nature_mur = forms.ChoiceField(
#         choices=[('Béton', 'Béton'), ('Brique', 'Brique'), ('Bois', 'Bois')],
#         label="Nature du mur",
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     nature_toit = forms.ChoiceField(
#         choices=[('Tôle', 'Tôle'), ('Zinc', 'Zinc'), ('Béton', 'Béton')],
#         label="Nature du toit",
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     nature_sol = forms.ChoiceField(
#         choices=[('Carrelage', 'Carrelage'), ('Terre battue', 'Terre battue'), ('Parquet', 'Parquet')],
#         label="Nature du sol",
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     statut_occupation = forms.ChoiceField(
#         choices=[('Propriétaire', 'Propriétaire'), ('Locataire', 'Locataire')],
#         label="Statut d’occupation du logement",
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     equipements = forms.MultipleChoiceField(
#         choices=[
#             ('Bicyclette', 'Bicyclette'), ('Motocyclette', 'Motocyclette'),
#             ('Véhicule', 'Véhicule'), ('Téléphone mobile', 'Téléphone mobile'),
#             ('Ordinateur', 'Ordinateur'), ('Télévision', 'Télévision'),
#             ('Réfrigérateur', 'Réfrigérateur'), ('Connexion internet', 'Connexion internet')
#         ],
#         widget=forms.CheckboxSelectMultiple,
#         label="Équipements possédés",
#         required=False
#     )
#     milieu_residence = forms.ChoiceField(
#         choices=[('Urbain', 'Urbain'), ('Rural', 'Rural')],
#         label="Milieu de résidence",
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     commentaire = forms.CharField(
#         widget=forms.Textarea(attrs={'class': 'form-control'}),
#         label="Commentaires supplémentaires",
#         required=False
#     )
#
#     class Meta:
#         model = PersonneVulnerable
#         # Ne listez que les champs qui existent réellement dans le modèle:
#         fields = [
#             'first_name',
#             'last_name',
#             'age',
#             'sexe',
#             'nombre_enfants',
#             'revenu',
#             'entite',
#             'region_geographique',
#         ]
#
#     def clean_revenu(self):
#         revenu = self.cleaned_data.get('revenu')
#         if revenu is not None and revenu < 0:
#             raise forms.ValidationError("Le revenu ne peut pas être négatif.")
#         return revenu
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Charger le JSON pour récupérer dynamiquement la liste de régions
#         with open('donations/json_ci/IvoryCoast.json', encoding='utf-8') as f:
#             data_json = json.load(f)
#
#         regions_list = data_json.get("regions", [])
#         region_names = [r["name"] for r in regions_list if "name" in r]
#
#         region_choices = [(name, name) for name in sorted(set(region_names))]
#         # On injecte les choices dans le champ region_geographique
#         self.fields['region_geographique'].choices = region_choices
#
#
#
# # from django import forms
# # from .models import PersonneVulnerable
# #
# #
# # class RecensementForm(forms.ModelForm):
# #     # Ajout des champs supplémentaires pour le formulaire
# #     first_name = forms.CharField(
# #         label="Prénom",
# #         max_length=150,
# #         widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrez le prénom'}),
# #     )
# #     last_name = forms.CharField(
# #         label="Nom",
# #         max_length=150,
# #         widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrez le nom'}),
# #     )
# #
# #     class Meta:
# #         model = PersonneVulnerable
# #         fields = ['first_name', 'last_name', 'age', 'revenu', 'entite']
# #         widgets = {
# #             'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Entrez l\'âge'}),
# #             'revenu': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Entrez le revenu'}),
# #             'entite': forms.Select(attrs={'class': 'form-control'}),
# #         }
# #
# #     def clean_revenu(self):
# #         # Validation personnalisée pour le champ revenu
# #         revenu = self.cleaned_data.get('revenu')
# #         if revenu is not None and revenu < 0:
# #             raise forms.ValidationError("Le revenu ne peut pas être négatif.")
# #         return revenu
#
#
# ########
