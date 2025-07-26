# users/views.py
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Vérifier si l'utilisateur existe déjà
        if User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur est déjà pris.")
            return redirect('register')

        # Créer un utilisateur en tant que donateur
        user = User.objects.create_user(username=username, password=password, is_donator=True)

        # Lier l'utilisateur à un profil PersonneVulnerable si nécessaire
        # Vous pouvez ajouter un profil PersonneVulnerable pour cet utilisateur ici si c'est nécessaire

        user.is_active = True  # Assurez-vous que l'utilisateur est activé
        user.save()

        login(request, user)  # Connecter l'utilisateur après l'inscription
        messages.success(request, "Inscription réussie. Bienvenue!")
        return redirect('profile')

    return render(request, 'users/register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authentifier l'utilisateur
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:  # Vérifier si l'utilisateur est actif
            login(request, user)
            messages.success(request, "Connexion réussie.")
            return redirect('dashboard_formation_complete')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")

    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté.")
    return redirect('login')


from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from users.models import PersonneVulnerable  # ajuste le chemin si besoin

from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def profile(request):
    user = request.user
    try:
        personne = user.personnevulnerable
    except PersonneVulnerable.DoesNotExist:
        personne = None

    # Initialisation des valeurs pour le donateur
    total_donations = 0
    total_amount = Decimal('0.00')

    if hasattr(user, 'is_donator') and user.is_donator:
        # Tous les dons effectués par cet utilisateur
        dons_donnes = user.dons.all()
  # Assure-toi du related_name sur le modèle Don
        total_donations = dons_donnes.count()
        total_amount = sum([don.montant for don in dons_donnes])

    if personne:
        dons_valides = personne.dons.filter(est_reparti=True)
        dons_recus = []
        montant_total = Decimal('0.00')

        for don in dons_valides:
            try:
                montant = Decimal(don.montant)
            except Exception as e:
                print(f"Erreur conversion montant pour le don {don.id}: {e}")
                montant = Decimal('0.00')

            if don.personne_vulnerable.exists():
                nb_personnes = don.personne_vulnerable.count()
            else:
                nb_personnes = don.entite_vulnerable.personnevulnerable_set.filter(est_vulnerable=True).count()

            montant_par_personne = montant / nb_personnes if nb_personnes > 0 else Decimal('0.00')
            montant_total += montant_par_personne

            dons_recus.append({
                'don': don,
                'montant_recu': montant_par_personne,
            })

        objectif = Decimal('200000.00')
        progression = (montant_total / objectif * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if objectif > 0 else Decimal('0.00')
        progression_float = float(progression)

        # Couleur dynamique
        if progression_float < 25:
            progress_color = "#ff4d4d"
        elif progression_float < 50:
            progress_color = "#ffa500"
        elif progression_float < 75:
            progress_color = "#007bff"
        else:
            progress_color = "#28a745"

        return render(request, 'users/profile.html', {
            'user': user,
            'personne': personne,
            'montant_total': montant_total,
            'dons_recus': dons_recus,
            'progression': progression,
            'progress_color': progress_color,
            'total_donations': total_donations,
            'total_amount': total_amount,
        })

    # Cas utilisateur donateur uniquement
    return render(request, 'users/profile.html', {
        'user': user,
        'personne': None,
        'total_donations': total_donations,
        'total_amount': total_amount,
    })


from django.contrib.auth import authenticate, login, logout

from django.views.decorators.csrf import csrf_exempt



import json
from django.contrib.auth.decorators import login_required

from decimal import Decimal
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from .models import PersonneVulnerable


@api_view(['GET'])
@ensure_csrf_cookie  # Ajout essentiel pour générer le cookie CSRF
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def profile_api(request):
    user = request.user

    # Détermination du rôle avec switch case modernisé
    role_mapping = {
        'is_donator': 'Donateur',
        'is_vulnerable': 'Personne vulnérable',
        'is_recenseur': 'Recenseur'
    }
    role = next((v for k, v in role_mapping.items() if getattr(user, k, False)), 'Utilisateur standard')

    # Calcul des recensements optimisé
    recensements = {
        'count': user.personnes_recensees.count() if user.is_recenseur else 0,
        'last': []
    }

    # Récupération de la personne vulnérable avec gestion d'erreur améliorée
    personne = None
    montant_total = Decimal('0.00')
    dons_recus = []

    if user.is_vulnerable:
        try:
            personne = user.personne_vulnerable
            dons_query = personne.dons.filter(est_reparti=True)

            if personne.entite:
                dons_query |= personne.entite.dons.filter(est_reparti=True)

            for don in dons_query.distinct():
                beneficiaires = (
                                    don.entite.personnevulnerable_set.count()
                                    if don.entite
                                    else 1
                                ) or 1  # Éviter la division par zéro

                montant_par_personne = don.montant / beneficiaires
                montant_total += montant_par_personne

                dons_recus.append({
                    'don_id': don.id,
                    'montant_recu': float(montant_par_personne),
                    'description': don.description,
                    'date_don': don.date_don.strftime('%d/%m/%Y') if don.date_don else ''
                })

        except (PersonneVulnerable.DoesNotExist, AttributeError) as e:
            print(f'Erreur de récupération: {e}')

    # Construction de réponse sécurisée
    return Response({
        'user': {
            'username': user.username,
            'role': role,
            'recensements': recensements
        },
        'personne': {
            'montant_total': float(montant_total),
            'dons_recus': dons_recus
        } if personne else None
    })


@csrf_exempt
def register_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'JSON invalide.'}, status=400)
        username = data.get('username')
        password = data.get('password')

        if not username:
            return JsonResponse({'success': False, 'message': "Le nom d'utilisateur doit être renseigné."}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'message': "Ce nom d'utilisateur est déjà pris."}, status=400)

        try:
            user = User.objects.create_user(username=username, password=password, is_donator=True)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
        user.is_active = True
        user.save()
        login(request, user)
        return JsonResponse({'success': True, 'message': "Inscription réussie. Bienvenue!", 'username': user.username})
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def login_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("Données reçues:", data)  # Log pour déboguer
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'JSON invalide.'}, status=400)
        username = data.get('username')
        password = data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            return JsonResponse({'success': True, 'message': "Connexion réussie.", 'username': user.username})
        else:
            return JsonResponse({'success': False, 'message': "Nom d'utilisateur ou mot de passe incorrect."}, status=403)
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def logout_api(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'success': True, 'message': "Vous avez été déconnecté."})
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


# users/views.py
def home(request):

    return render(request, 'home.html')

from notifications.models import Notification


@login_required
def notifications_view(request):
    # Récupère toutes les notifications de l'utilisateur, triées par date décroissante
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    print(notifications)  # Pour le débogage (affiche dans la console)
    return render(request, 'notifications/notifications.html', {'notifications': notifications})
############


from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import PersonneVulnerable

@csrf_exempt
def update_validation_status(request, personne_id):
    if request.method == "POST":
        personne = get_object_or_404(PersonneVulnerable, id=personne_id)
        validation_status = request.POST.get("validation_status")

        if validation_status == "Oui":
            personne.validated_by_admin = True
        else:
            personne.validated_by_admin = False

        personne.save()
        return redirect('liste_personnes_recensees')

    return HttpResponse(status=405)  # Méthode non autorisée




def modifier_personne(request, personne_id):
    personne = get_object_or_404(PersonneVulnerable, id=personne_id)

    if request.method == 'POST' and not personne.validated_by_admin:  # Empêche modification après validation
        personne.user.first_name = request.POST.get('first_name')
        personne.user.last_name = request.POST.get('last_name')
        personne.age = request.POST.get('age')
        personne.revenu = request.POST.get('revenu')
        personne.entite = request.POST.get('entite')

        personne.user.save()
        personne.save()

        return redirect('voir_personne', personne_id=personne.id)  # Redirige après modification

    return render(request, 'voir_personne.html', {'personne': personne})


from django.shortcuts import render, get_object_or_404


def voir_personne(request, personne_id):
    personne = get_object_or_404(PersonneVulnerable, id=personne_id)

    # Formulaire pour éditer les informations
    if request.method == 'POST':
        form = RecensementForm(request.POST, instance=personne)
        if form.is_valid():
            form.save()
            return redirect('liste_personnes_recensees')  # Rediriger après la mise à jour
    else:
        form = RecensementForm(instance=personne)

    return render(request, 'voir_personne.html', {'form': form, 'personne': personne})


from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RecensementForm
from .models import PersonneVulnerable, User
from detection.utils import est_vulnerable  # Votre modèle de prédiction


# Vérifier si l'utilisateur est un recenseur ou un admin
def is_recenseur_or_admin(user):
    return user.is_recenseur or user.is_superuser



# @login_required
# @user_passes_test(is_recenseur_or_admin)
# def recenser_personne(request):
#     """
#     Vue pour permettre à un recenseur d'enregistrer une nouvelle personne.
#     """
#     if request.method == 'POST':
#         form = RecensementForm(request.POST)
#         if form.is_valid():
#             # Créer une nouvelle instance de PersonneVulnerable
#             personne = form.save(commit=False)
#
#             # Associer les champs first_name et last_name à l'instance
#             personne.nom = form.cleaned_data['last_name']
#             personne.prenom = form.cleaned_data['first_name']
#
#             # Associer le recenseur (utilisateur connecté) automatiquement
#             personne.recenseur = request.user
#
#             # Effectuer la prédiction de vulnérabilité
#             age = personne.age
#             revenu = personne.revenu
#             personne.est_vulnerable = est_vulnerable(age, revenu)
#
#             # Sauvegarder la personne dans la base de données
#             personne.save()
#
#             messages.success(
#                 request,
#                 f"La personne {personne.nom} {personne.prenom} a été enregistrée avec succès. "
#                 f"Résultat du modèle : {'Vulnérable' if personne.est_vulnerable else 'Non vulnérable'}. "
#                 f"L'admin doit valider cette personne pour qu'elle devienne vulnérable."
#             )
#             return redirect('recenser_personne')
#
#     else:
#         form = RecensementForm()
#
#     return render(request, 'users/recensement.html', {'form': form})



import os
import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from .forms import RecensementForm
from .models import PersonneVulnerable
from langchain_ollama import ChatOllama
import json
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RecensementForm

llm = ChatOllama(base_url="http://localhost:11434", model="mistral")

from langchain_ollama import ChatOllama
import json
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RecensementForm

# Initialise l’instance du LLM (ajuste l’URL et le modèle si besoin)
from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, SystemMessage
import json
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RecensementForm

llm = ChatOllama(base_url="http://localhost:11434", model="mistral")

def build_poverty_prompt(data):
    return (
        f"Voici les données d'une personne recensée :\n"
        f"- Âge : {data.get('age')}\n"
        f"- Revenu mensuel (FCFA) : {data.get('revenu')}\n"
        f"- Type de logement : {data.get('logement')}\n"
        f"- Situation matrimoniale : {data.get('situation_matrimoniale')}\n"
        f"- Source d'eau : {data.get('source_eau')}\n"
        f"- Type de sanitaires : {data.get('type_sanitaires')}\n"
        f"- Accès à l'électricité : {data.get('acces_electricite')}\n"
        f"- Emploi : {data.get('emploi')}\n"
        f"- Niveau d'éducation : {data.get('niveau_education')}\n"
        f"- État de santé : {data.get('etat_sante')}\n"
        f"- Handicap : {data.get('handicap')}\n"
        f"- Enfants non scolarisés : {data.get('enfants_non_scolarises')}\n"
        f"- Nombre de personnes dans le ménage : {data.get('nombre_personnes_menage')}\n"
        f"- Montant total reçu (allocations) : {data.get('montant_total_recu')}\n\n"
        f"En te basant sur ces informations, donne :\n"
        f"1) Une prédiction du niveau de pauvreté en pourcentage (0-100%).\n"
        f"2) Une analyse expliquant pourquoi cette personne est pauvre ou non.\n"
        f"3) Le type principal de pauvreté détecté parmi : pauvreté financière, pauvreté matérielle, besoin spécifique.\n"
        f"Réponds en JSON strict, uniquement, avec les clés : 'niveau_pauvrete', 'analyse', 'type_pauvrete'."
    )

from langchain.schema import HumanMessage, SystemMessage

def predict_poverty_with_llm(prompt):
    messages = [
        SystemMessage(content="Tu es un expert en prédiction de pauvreté."),
        HumanMessage(content=prompt)
    ]
    response = llm(messages)  # Retourne un AIMessage
    return response.content  # Texte simple

@login_required
@user_passes_test(lambda u: u.is_recenseur or u.is_superuser)
def recenser_personne(request):
    if request.method == 'POST':
        form = RecensementForm(request.POST, request.FILES)  # <-- ici request.FILES ajouté
        if form.is_valid():
            data_user = form.cleaned_data
            prompt = build_poverty_prompt(data_user)
            llm_response = predict_poverty_with_llm(prompt)

            try:
                result = json.loads(llm_response)
                niveau = result.get('niveau_pauvrete')
                analyse = result.get('analyse')
                type_pauvrete = result.get('type_pauvrete')
            except Exception as e:
                niveau = None
                analyse = f"Erreur : {str(e)}"
                type_pauvrete = None

            niveau_float = None
            if niveau is not None:
                try:
                    niveau_float = float(niveau.replace('%', '').strip())
                except Exception:
                    niveau_float = None

            if type_pauvrete:
                type_pauvrete = type_pauvrete.strip().capitalize()
            else:
                type_pauvrete = 'Inconnu'

            personne = form.save(commit=False)
            personne.recenseur = request.user
            personne.niveau_pauvrete = niveau_float
            personne.categorie_predite = type_pauvrete
            personne.analyse_llm = analyse or 'Pas d\'analyse disponible.'
            personne.save()

            # messages.success(request,
            #     f"Niveau de pauvreté prédit : {niveau_float if niveau_float is not None else 'N/A'}%\n"
            #     f"Type de pauvreté : {type_pauvrete}\n"
            #     f"Analyse : {analyse}"
            # )
            return redirect('recenser_personne')

    else:
        form = RecensementForm()

    return render(request, 'users/recensement.html', {'form': form})


# @login_required
# @user_passes_test(is_recenseur_or_admin)
# def recenser_personne(request):
#     if request.method == 'POST':
#         form = RecensementForm(request.POST)
#         if form.is_valid():
#             personne = form.save(commit=False)
#             personne.nom = form.cleaned_data['last_name']
#             personne.prenom = form.cleaned_data['first_name']
#             personne.recenseur = request.user
#
#             # === 🔍 Chargement du modèle et préprocesseur ===
#             detection_dir = os.path.join(settings.BASE_DIR, 'detection')
#             model_path = os.path.join(detection_dir, 'modele_vulnerabilite.h5')
#             preprocessor_path = os.path.join(detection_dir, 'preprocessor.pkl')
#
#             model = tf.keras.models.load_model(model_path)
#             preprocessor = joblib.load(preprocessor_path)
#
#             # === 📊 Construction du DataFrame d'entrée ===
#             input_data = {
#                 'age': [personne.age],
#                 'revenu': [personne.revenu],
#                 'logement': [personne.logement],
#                 'type_sanitaires': [personne.type_sanitaires],
#                 'sexe': [personne.sexe],
#                 'situation_matrimoniale': [personne.situation_matrimoniale],
#                 'source_eau': [personne.source_eau],
#                 'acces_electricite': [personne.acces_electricite],
#                 'emploi': [personne.emploi],
#                 'niveau_education': [personne.niveau_education],
#                 'etat_sante': [personne.etat_sante],
#                 'handicap': [personne.handicap],
#                 'enfants_non_scolarises': [personne.enfants_non_scolarises],
#                 'nombre_personnes_menage': [personne.nombre_personnes_menage],
#                 'montant_total_recu': [personne.montant_total_recu],
#             }
#             df_input = pd.DataFrame(input_data)
#
#             # === ⚙️ Prétraitement + Prédiction ===
#             X_input = preprocessor.transform(df_input)
#             y_proba = model.predict(X_input)
#             y_pred = np.argmax(y_proba)
#
#             # === 🧠 Interprétation de la classe prédite ===
#             labels = ['Résilient', 'Stable', 'Vulnérable', 'Très vulnérable']
#             personne.categorie_predite = labels[y_pred]  # ⚠️ ajoute ce champ dans ton modèle
#
#             personne.save()
#
#             messages.success(
#                 request,
#                 f"La personne {personne.nom} {personne.prenom} a été enregistrée avec succès. "
#                 f"Résultat du modèle : {labels[y_pred]}."
#             )
#             return redirect('recenser_personne')
#     else:
#         form = RecensementForm()
#
#     return render(request, 'users/recensement.html', {'form': form})

@login_required
@user_passes_test(is_recenseur_or_admin)
def liste_personnes_recensees(request):
    """
    Vue pour afficher la liste des personnes recensées par le recenseur.
    """
    personnes = PersonneVulnerable.objects.filter(recenseur=request.user)  # Personnes sans compte utilisateur
    return render(request, 'users/liste_personnes_recensees.html', {'personnes': personnes})


@login_required
@user_passes_test(lambda u: u.is_superuser)  # Accessible uniquement par les admins
def valider_personne(request, personne_id):
    """
    Vue pour permettre à l'admin de valider une personne comme vulnérable.
    """
    try:
        personne = PersonneVulnerable.objects.get(id=personne_id)
    except PersonneVulnerable.DoesNotExist:
        messages.error(request, "La personne demandée n'existe pas.")
        return redirect('liste_personnes_recensees')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, "Veuillez fournir un nom d'utilisateur et un mot de passe.")
            return redirect('valider_personne', personne_id=personne_id)

        # Créer un utilisateur pour cette personne
        user = User.objects.create_user(username=username, password=password, is_vulnerable=True)
        personne.user = user
        personne.save()

        messages.success(
            request,
            f"La personne {personne.get_full_name()} a été validée et un compte utilisateur a été créé.",
        )
        return redirect('liste_personnes_recensees')

    return render(request, 'users/valider_personne.html', {'personne': personne})


###################################
from django.db.models import Count, Sum
from django.http import JsonResponse

from django.db.models import Count, Sum, F
from django.shortcuts import render
from .models import User, PersonneVulnerable

def admin_dashboard(request):
    # Calculs principaux
    total_recenseurs = User.objects.filter(is_recenseur=True).count()

    recenseurs_actifs = User.objects.filter(is_recenseur=True, is_active=True).count()
    recenseurs_inactifs = total_recenseurs - recenseurs_actifs

    total_personnes_vulnerables = PersonneVulnerable.objects.filter(est_vulnerable=True).count()
    total_personnes_non_vulnerables = PersonneVulnerable.objects.filter(est_vulnerable=False).count()

    personnes_vulnerables_dons = (
        PersonneVulnerable.objects.filter(est_vulnerable=True, montant_recu__gt=0).count()
    )

    # Nombre total de donateurs
    total_donateurs = User.objects.filter(is_donator=True).count()

    # Progression des dons (exemple : progression sur 200 euros)
    progression_dons = (
        PersonneVulnerable.objects.filter(est_vulnerable=True)
        .aggregate(total_dons=Sum('montant_recu'))['total_dons'] or 0
    )
    progression_dons_percentage = min((progression_dons / 200) * 100, 100)  # Cap à 100%

    # Top communes/régions vulnérables
    top_regions_vulnerables = (
        PersonneVulnerable.objects.filter(est_vulnerable=True)
        .values('entite')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )

    # Préparer les données pour le tableau des personnes vulnérables
    personnes_vulnerables = PersonneVulnerable.objects.filter(est_vulnerable=True).order_by('-id').annotate(
        progression_percentage=F('montant_recu') * 100 / 200  # Calculer la progression en pourcentage
    )

    # Compter le nombre de personnes recensées par chaque recenseur
    recenseurs_counts = User.objects.filter(is_recenseur=True).annotate(
        count_personnes_recensees=Count('personnes_recensees')  # Nouveau nom d'annotation pour éviter le conflit
    )

    # Données pour les graphiques
    labels_top_regions = [region['entite'] for region in top_regions_vulnerables]
    values_top_regions = [region['total'] for region in top_regions_vulnerables]

    # Données à afficher dans le tableau de bord
    context = {
        'total_recenseurs': total_recenseurs,
        'recenseurs_actifs': recenseurs_actifs,
        'recenseurs_inactifs': recenseurs_inactifs,
        'total_personnes_vulnerables': total_personnes_vulnerables,
        'total_personnes_non_vulnerables': total_personnes_non_vulnerables,
        'personnes_vulnerables_dons': personnes_vulnerables_dons,
        'total_donateurs': total_donateurs,
        'progression_dons': progression_dons,
        'progression_dons_percentage': progression_dons_percentage,
        'labels_top_regions': labels_top_regions,
        'values_top_regions': values_top_regions,
        'personnes_vulnerables': personnes_vulnerables,  # Ajout des personnes vulnérables pour le tableau
        'recenseurs_counts': recenseurs_counts  # Ajouter les comptes des recenseurs
    }

    return render(request, 'admin_dashboard.html', context)
# users/views.py (ajoutez une vue API)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import PersonneVulnerable
from .serializers import PersonneVulnerableSerializer

@api_view(['GET'])
@permission_classes([AllowAny])
def personnes_vulnerables_api(request):
    personnes = PersonneVulnerable.objects.all()  # Vous pouvez filtrer si nécessaire
    print(personnes)
    serializer = PersonneVulnerableSerializer(personnes, many=True)
    return Response(serializer.data)

####################################
# users/views.py (ou dans un fichier api_views.py dédié)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from rest_framework.authtoken.models import Token

@api_view(['POST'])
@permission_classes([AllowAny])
def login_api1(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    if user is not None and user.is_active:
        login(request, user)
        # Génère ou récupère le token associé à cet utilisateur
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'success': True,
            'token': token.key,
            'user': {
                'username': user.username,
                'role': (
                    'admin' if user.is_superuser else
                    'recenseur' if user.is_recenseur else
                    'personne_vulnerable' if user.is_vulnerable else
                    'donateur'
                )
            }
        })
    return Response({'success': False, 'message': 'Identifiants invalides'}, status=403)

# users/views.py
from rest_framework.decorators import api_view, permission_classes

@api_view(['GET'])
@permission_classes([AllowAny])
def personnes_recensees_api(request):
    personnes = PersonneVulnerable.objects.all()
    serializer = PersonneVulnerableSerializer(personnes, many=True)
    return Response(serializer.data)

# users/views.py
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from .serializers import UserSerializer

User = get_user_model()

@api_view(['GET'])
@permission_classes([AllowAny])
def users_list_api(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework import status
from .serializers import PersonneVulnerableSerializer
from users.models import PersonneVulnerable

@api_view(['GET'])
# @authentication_classes([TokenAuthentication])
# @permission_classes([IsAuthenticated])
@permission_classes([AllowAny])
def profile_api1(request):
    user = request.user
    print("User:", user)

    try:
        profile = user.personnevulnerable  # Accès au profil via OneToOneField
        print("Profile:", profile)
        # Vérification du statut du profil
        if profile.est_vulnerable:
            update = {}
            if not user.is_vulnerable:
                update['is_vulnerable'] = True
            if user.is_donator:
                update['is_donator'] = False
            if update:
                # On force la mise à jour uniquement des champs modifiés
                for field, value in update.items():
                    setattr(user, field, value)
                user.save(update_fields=list(update.keys()))
    except PersonneVulnerable.DoesNotExist:
        profile = None

    data = {
        "user": {
            "username": user.username,
            "role": (
                "admin" if user.is_superuser else
                "recenseur" if user.is_recenseur else
                "personne_vulnerable" if user.is_vulnerable else
                "donateur"
            )
        }
    }

    if profile:
        serializer = PersonneVulnerableSerializer(profile)
        personne_data = serializer.data
        personne_data["don_count"] = profile.dons.count()
        data["personne"] = personne_data
    else:
        data["personne"] = None

    return Response(data, status=status.HTTP_200_OK)



from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from users.models import PersonneVulnerable
from users.serializers import PersonneVulnerableSerializer
from decimal import Decimal

# users/api_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import PersonneVulnerable
from .serializers import PersonneVulnerableSerializer
from detection.views import est_vulnerable  # Adaptez le chemin si nécessaire


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import PersonneVulnerable
from .serializers import PersonneVulnerableSerializer
from detection.views import est_vulnerable  # Adaptez le chemin selon votre structure

# users/api_views.py (ou dans le fichier approprié)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import PersonneVulnerable
from .serializers import PersonneVulnerableSerializer
from detection.utils import est_vulnerable  # Assurez-vous que ce chemin est correct


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recenser_personne_api(request):
    """
    Crée une nouvelle PersonneVulnerable:
      - recenseur = request.user
      - user reste à None (pas de compte affecté)
      - est_vulnerable est calculé via la fonction de prédiction
    """
    data = request.data.copy()

    # On ignore tout champ "user" envoyé par le client
    data.pop('user', None)

    # On force le recenseur à l’utilisateur connecté
    data['recenseur'] = request.user.id

    # Prédiction (par exemple avec votre fonction "est_vulnerable")
    age = data.get('age')
    revenu = data.get('revenu')
    data['est_vulnerable'] = est_vulnerable(age, revenu)

    serializer = PersonneVulnerableSerializer(data=data)
    if serializer.is_valid():
        serializer.save()  # Le champ "user" restera None
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# users/api_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_user_api(request):
    """
    Crée un nouvel utilisateur. Seul un admin peut créer un utilisateur via cette API.
    Pour créer un recenseur, l'admin devra passer "is_recenseur": true dans le payload.
    """
    username = request.data.get('username')
    password = request.data.get('password')
    if not username or not password:
        return Response({"error": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

    # Créez l'utilisateur en utilisant create_user (qui hache le mot de passe)
    user = User.objects.create_user(username=username, password=password)
    # Mettez à jour les rôles selon les données envoyées
    user.is_donator = request.data.get('is_donator', False)
    user.is_vulnerable = request.data.get('is_vulnerable', False)
    user.is_recenseur = request.data.get('is_recenseur', False)
    user.save()

    return Response({
        "success": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "is_donator": user.is_donator,
            "is_vulnerable": user.is_vulnerable,
            "is_recenseur": user.is_recenseur,
            "recensed_count": user.personnes_recensees.count() if user.is_recenseur else None,
        }
    }, status=status.HTTP_201_CREATED)


# users/api_views.py (or within users/views.py)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .forms import RecensementForm  # if you want to reuse your Django form
from .models import PersonneVulnerable

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recensement_api(request):
    """
    Enregistre les données de recensement pour une personne vulnérable.
    - recenseur = request.user
    - user reste à None (aucun compte attribué)
    - est_vulnerable est calculé via la fonction de prédiction
    """
    # On copie les données reçues et on retire le champ 'user' s'il existe
    data = request.data.copy()
    data.pop('user', None)

    # On force le recenseur à l’utilisateur connecté
    data['recenseur'] = request.user.id

    # Calcul de la vulnérabilité via votre fonction (exemple)
    age = data.get('age')
    revenu = data.get('revenu')
    data['est_vulnerable'] = est_vulnerable(age, revenu)

    serializer = PersonneVulnerableSerializer(data=data)
    if serializer.is_valid():
        serializer.save()  # Ici, le champ "user" reste None, et "recenseur" est défini
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# users/api_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from .serializers import PersonneVulnerableSerializer

@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_vulnerable_person_api(request):
    """
    Crée une nouvelle personne vulnérable.
    Seul un admin peut créer une personne vulnérable via cette API.
    """
    serializer = PersonneVulnerableSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# users/api_views.py
from django.utils import timezone
from datetime import timedelta
from .serializers import UserSerializer

@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_connected_users_api(request):
    """
    Renvoie une liste d'utilisateurs considérés comme connectés.
    Ici, on suppose que les utilisateurs ayant une dernière connexion dans les 10 dernières minutes sont connectés.
    """
    ten_minutes_ago = timezone.now() - timedelta(minutes=10)
    User = get_user_model()
    connected_users = User.objects.filter(last_login__gte=ten_minutes_ago)
    serializer = UserSerializer(connected_users, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import PersonneVulnerable
from .serializers import PersonneVulnerableSerializer


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from .models import PersonneVulnerable
from .serializers import PersonneVulnerableSerializer

@api_view(['GET'])
@permission_classes([IsAdminUser])
def pending_vulnerable_api(request):
    """
    Retourne les personnes vulnérables qui n'ont PAS encore été validées par l'admin
    ET qui n'ont pas encore de compte utilisateur (user is null).
    """
    personnes = PersonneVulnerable.objects.filter(validated_by_admin=False, user__isnull=True)
    serializer = PersonneVulnerableSerializer(personnes, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_vulnerable_api(request, person_id):
    """
    Valide une personne vulnérable en mettant à jour son profil.
    Seul un utilisateur authentifié peut appeler cette API.
    """
    try:
        person = PersonneVulnerable.objects.get(id=person_id)
    except PersonneVulnerable.DoesNotExist:
        return Response(
            {"detail": "Personne non trouvée."},
            status=status.HTTP_404_NOT_FOUND
        )

    # Mettre à jour le profil de la personne vulnérable
    person.est_vulnerable = True
    person.validated_by_admin = True
    person.save()

    # Mettre à jour le modèle User associé, si existant
    if person.user:
        person.user.is_vulnerable = True
        person.user.save()

    serializer = PersonneVulnerableSerializer(person)
    return Response(serializer.data, status=status.HTTP_200_OK)


# users/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import PersonneVulnerable
from .serializers import AccountAssignmentSerializer

class AssignAccountView(APIView):
    """
    API permettant d'assigner un compte à une personne vulnérable.
    URL : /users/api/assign-account/<person_id>/
    """

    def post(self, request, person_id, format=None):
        try:
            personne = PersonneVulnerable.objects.get(id=person_id)
        except PersonneVulnerable.DoesNotExist:
            return Response(
                {"detail": "Personne vulnérable introuvable."},
                status=status.HTTP_404_NOT_FOUND
            )

        if personne.user is not None:
            return Response(
                {"detail": "Cette personne a déjà un compte."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AccountAssignmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.create_account(personne)
            return Response(
                {"detail": "Compte créé avec succès."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# users/api_views.py
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import logout, get_user_model
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework import status
from users.models import PersonneVulnerable
from users.serializers import PersonneVulnerableSerializer, UserSerializer

User = get_user_model()


from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import logout, get_user_model
from .models import PersonneVulnerable
from .serializers import PersonneVulnerableSerializer, UserSerializer

# ---------------------------------------------------------------------------
# Recenseur – Profil
# ---------------------------------------------------------------------------
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import PersonneVulnerableSerializer
from .models import PersonneVulnerable


from .models import PersonneVulnerable
from .serializers import PersonneVulnerableSerializer, UserSerializer
from rest_framework.authtoken.models import Token

User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recenseur_profile_api(request):
    recenseur = request.user
    try:
        profile = recenseur.personnevulnerable
    except PersonneVulnerable.DoesNotExist:
        # Créer un profil vide si inexistant
        profile = PersonneVulnerable.objects.create(recenseur=recenseur)
    serializer = PersonneVulnerableSerializer(profile)
    # Compter uniquement les recensements validés par l'admin
    recense_count = PersonneVulnerable.objects.filter(
        recenseur=recenseur,
        validated_by_admin=True
    ).count()
    data = serializer.data
    data['recense_count'] = recense_count
    data['user'] = {
        "username": recenseur.username,
        "role": (
            "admin" if recenseur.is_superuser else
            "recenseur" if recenseur.is_recenseur else
            "donateur" if recenseur.is_donator else
            "vulnerable" if recenseur.is_vulnerable else
            "inconnu"
        )
    }
    return Response(data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Recenseur – Derniers recensements
# ---------------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def last_five_persons_api(request):
    """
    Retourne les 5 dernières personnes recensées par le recenseur.
    """
    recenseur = request.user
    # Récupérer les 5 derniers recensements (par ordre décroissant de l'ID par exemple)
    persons = PersonneVulnerable.objects.filter(recenseur=recenseur).order_by('-id')[:5]
    serializer = PersonneVulnerableSerializer(persons, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

# ---------------------------------------------------------------------------
# Recenseur – Détail d'une personne recensée
# ---------------------------------------------------------------------------
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def recensed_person_detail_api(request, person_id):
    """
    GET: Retourne le détail d'une personne recensée par le recenseur.
    PUT: Permet de modifier une personne recensée non encore validée par l'admin.
    DELETE: Permet de supprimer une personne recensée non encore validée par l'admin.
    """
    recenseur = request.user
    try:
        person = PersonneVulnerable.objects.get(id=person_id, recenseur=recenseur)
    except PersonneVulnerable.DoesNotExist:
        return Response({"detail": "Personne recensée non trouvée."},
                        status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = PersonneVulnerableSerializer(person)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        # Seules les personnes non validées par l'admin peuvent être modifiées
        if person.validated_by_admin:
            return Response({"detail": "Modification non autorisée, la personne est déjà validée."},
                            status=status.HTTP_403_FORBIDDEN)
        serializer = PersonneVulnerableSerializer(person, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        # Seules les personnes non validées par l'admin peuvent être supprimées
        if person.validated_by_admin:
            return Response({"detail": "Suppression non autorisée, la personne est déjà validée."},
                            status=status.HTTP_403_FORBIDDEN)
        person.delete()
        return Response({"detail": "Personne supprimée avec succès."}, status=status.HTTP_200_OK)

# ---------------------------------------------------------------------------
# Recenseur – Déconnexion
# ---------------------------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    """
    Logs out the current user by deleting their token (if using TokenAuthentication).
    """
    try:
        token = Token.objects.get(user=request.user)
        token.delete()
    except Token.DoesNotExist:
        pass
    return Response({"detail": "Déconnecté avec succès."}, status=status.HTTP_200_OK)

from django.contrib.auth import update_session_auth_hash

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_api(request):
    """
    Change the password of the authenticated user.
    Expects JSON body with 'old_password' and 'new_password'.
    """
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    if not old_password or not new_password:
        return Response(
            {"detail": "Ancien et nouveau mot de passe sont requis."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not user.check_password(old_password):
        return Response(
            {"detail": "Ancien mot de passe incorrect."},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.set_password(new_password)
    user.save()
    update_session_auth_hash(request, user)  # Important, so user is not logged out
    return Response({"detail": "Mot de passe modifié avec succès."}, status=status.HTTP_200_OK)

# @login_required
# @user_passes_test(lambda u: u.is_superuser)
# def admin_personnes_carousel(request):
#     personnes = PersonneVulnerable.objects.all().order_by('-id')
#     return render(request, 'users/admin_personnes_carousel.html', {'personnes': personnes})
# @login_required
# @user_passes_test(lambda u: u.is_superuser)
# def valider_personne(request, personne_id):
#     personne = get_object_or_404(PersonneVulnerable, id=personne_id)
#     personne.validated_by_admin = True
#     personne.save()
#     messages.success(request, f"{personne.get_full_name()} validée.")
#     return redirect('admin_personnes_carousel')
#
# @login_required
# @user_passes_test(lambda u: u.is_superuser)
# def rejeter_personne(request, personne_id):
#     personne = get_object_or_404(PersonneVulnerable, id=personne_id)
#     personne.validated_by_admin = False
#     personne.save()
#     messages.success(request, f"{personne.get_full_name()} rejetée.")
#     return redirect('admin_personnes_carousel')


import json
import string
import random
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import PersonneVulnerable


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_personnes_carousel(request):
    personnes = PersonneVulnerable.objects.all().order_by('-id')
    return render(request, 'users/admin_personnes_carousel.html', {'personnes': personnes})


# users/views.py
import json
import string
import random
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import PersonneVulnerable

# Utiliser get_user_model() pour votre modèle User personnalisé
User = get_user_model()


@login_required
@user_passes_test(lambda u: u.is_superuser)
@csrf_exempt
def valider_personne(request, personne_id):
    if request.method == 'POST':
        try:
            print(f"Request body: {request.body}")
            print(f"Content type: {request.content_type}")

            if not request.body:
                return JsonResponse({
                    'success': False,
                    'error': 'Corps de requête vide'
                }, status=400)

            data = json.loads(request.body)
            category = data.get('category')

            if not category:
                return JsonResponse({
                    'success': False,
                    'error': 'Catégorie non spécifiée'
                }, status=400)

            personne = get_object_or_404(PersonneVulnerable, id=personne_id)

            # Vérifier si déjà validé
            if personne.validated_by_admin:
                return JsonResponse({
                    'success': False,
                    'error': 'Cette personne est déjà validée'
                }, status=400)

            # Vérifier que la catégorie reçue fait partie des ENTITE_CHOICES
            entite_choices = [c[0] for c in PersonneVulnerable.ENTITE_CHOICES]
            if category not in entite_choices:
                return JsonResponse({
                    'success': False,
                    'error': f"Catégorie '{category}' non valide."
                }, status=400)

            # Générer nom d'utilisateur et mot de passe
            username = generate_username(personne.get_full_name())
            password = generate_random_password()

            # Créer ou mettre à jour l'utilisateur
            if not personne.user:
                try:
                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        first_name=personne.first_name,
                        last_name=personne.last_name,
                        email=personne.email or '',
                        is_vulnerable=True
                    )
                    personne.user = user
                    print(f"Utilisateur créé: {username}")
                except Exception as e:
                    print(f"Erreur création utilisateur: {e}")
                    return JsonResponse({
                        'success': False,
                        'error': f"Erreur lors de la création de l'utilisateur : {str(e)}"
                    }, status=500)
            else:
                username = personne.user.username
                personne.user.set_password(password)
                personne.user.is_vulnerable = True
                personne.user.save()
                print(f"Utilisateur mis à jour: {username}")

            # Affecter la catégorie directement (plus de mapping)
            personne.entite = category
            personne.validated_by_admin = True
            personne.est_vulnerable = True
            personne.save()

            print(f"Personne validée: {personne.get_full_name()}")

            return JsonResponse({
                'success': True,
                'username': username,
                'password': password,
                'message': f"{personne.get_full_name()} validé(e) avec succès.",
                'category': category
            })

        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Format JSON invalide'
            }, status=400)

        except Exception as e:
            print(f"Error in valider_personne: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    # Méthode GET fallback
    personne = get_object_or_404(PersonneVulnerable, id=personne_id)
    personne.validated_by_admin = True
    personne.est_vulnerable = True
    personne.save()
    messages.success(request, f"{personne.get_full_name()} validée.")
    return redirect('admin_personnes_carousel')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def rejeter_personne(request, personne_id):
    if request.method == 'POST':
        try:
            personne = get_object_or_404(PersonneVulnerable, id=personne_id)
            personne.validated_by_admin = False
            personne.est_vulnerable = False

            # Mettre à jour l'utilisateur associé si il existe
            if personne.user:
                personne.user.is_vulnerable = False
                personne.user.save()

            personne.save()

            return JsonResponse({
                'success': True,
                'message': f"{personne.get_full_name()} rejeté(e) avec succès."
            })
        except Exception as e:
            print(f"Error in rejeter_personne: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

    # Méthode GET classique (fallback)
    personne = get_object_or_404(PersonneVulnerable, id=personne_id)
    personne.validated_by_admin = False
    personne.est_vulnerable = False

    if personne.user:
        personne.user.is_vulnerable = False
        personne.user.save()

    personne.save()
    messages.success(request, f"{personne.get_full_name()} rejetée.")
    return redirect('admin_personnes_carousel')


def generate_username(full_name):
    """Générer un nom d'utilisateur basé sur le nom complet"""
    if not full_name:
        full_name = "user"

    # Nettoyer et formater le nom
    username = full_name.lower().replace(' ', '.').replace('-', '.')
    # Supprimer les caractères spéciaux et accents
    import unicodedata
    username = unicodedata.normalize('NFKD', username)
    username = ''.join(c for c in username if c.isalnum() or c == '.')
    # Limiter la longueur
    username = username[:20] if username else "user"

    # S'assurer de l'unicité
    base_username = username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1

    return username


def generate_random_password(length=8):
    """Générer un mot de passe aléatoire sécurisé"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(characters) for i in range(length))







#######################################
# users/views.py - Vue complète du dashboard avec formations

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from users.models import PersonneVulnerable, User

# Imports pour les formations
try:
    from formation.models import (
        Formation, DemandeFormation, ParcoursFormation,
        ProjetVie, SuiviProgression
    )

    FORMATIONS_AVAILABLE = True
except ImportError:
    FORMATIONS_AVAILABLE = False


    # Modèles factices si les formations ne sont pas installées
    class Formation:
        objects = type('MockManager', (), {'filter': lambda **kwargs: [], 'count': lambda: 0})()


    class DemandeFormation:
        objects = type('MockManager', (), {'filter': lambda **kwargs: [], 'count': lambda: 0})()


    class ParcoursFormation:
        objects = type('MockManager', (), {'filter': lambda **kwargs: [], 'count': lambda: 0})()


    class ProjetVie:
        objects = type('MockManager', (), {'filter': lambda **kwargs: [], 'count': lambda: 0})()


@login_required
def dashboard_formation_complete(request):
    """
    Vue principale du dashboard avec intégration complète des formations
    """
    user = request.user
    context = {
        'user': user,
        'current_date': timezone.now().strftime('%d %B %Y'),
        'formations_available': FORMATIONS_AVAILABLE,
    }

    # === STATISTIQUES FORMATIONS GLOBALES ===
    if FORMATIONS_AVAILABLE:
        try:
            # Formations actives
            formations_actives = Formation.objects.filter(est_active=True).count()
            formations_disponibles = Formation.objects.filter(
                est_active=True,
                places_disponibles__gt=0
            ).count()

            # Demandes en attente globales
            demandes_en_attente = DemandeFormation.objects.filter(
                statut__in=['en_attente', 'analysee']
            ).count()

            # Parcours en cours
            parcours_en_cours = ParcoursFormation.objects.filter(
                statut_actuel__in=['pre_inscrit', 'forme', 'projet_valide']
            ).count()

            context.update({
                'formations_actives': formations_actives,
                'formations_disponibles': formations_disponibles,
                'demandes_en_attente': demandes_en_attente,
                'parcours_en_cours': parcours_en_cours,
            })
        except Exception as e:
            print(f"Erreur formations globales: {e}")
            context.update({
                'formations_actives': 0,
                'formations_disponibles': 0,
                'demandes_en_attente': 0,
                'parcours_en_cours': 0,
            })

    # === DASHBOARD DONATEUR AVEC FORMATIONS ===
    if user.is_donator:
        try:
            # Dons classiques
            dons_donnes = getattr(user, 'dons', None)
            if dons_donnes:
                dons_donnes = dons_donnes.all()
                total_donations = dons_donnes.count()
                total_amount = sum([float(don.montant) for don in dons_donnes]) if dons_donnes else 0

                # Bénéficiaires uniques
                beneficiaires = set()
                for don in dons_donnes.filter(est_reparti=True):
                    if hasattr(don, 'personne_vulnerable') and don.personne_vulnerable.exists():
                        beneficiaires.update(don.personne_vulnerable.values_list('id', flat=True))

                # Dons récents (30 derniers jours)
                date_recente = timezone.now() - timedelta(days=30)
                recent_amount = sum([
                    float(don.montant) for don in dons_donnes.filter(date_don__gte=date_recente)
                ]) if dons_donnes.filter(date_don__gte=date_recente).exists() else 0

                new_donations = dons_donnes.filter(date_don__gte=date_recente).count()
                dons_en_attente = dons_donnes.filter(est_reparti=False).count()

                context.update({
                    'total_donations': total_donations,
                    'total_amount': int(total_amount),
                    'beneficiaires': len(beneficiaires),
                    'recent_amount': int(recent_amount),
                    'new_donations': new_donations,
                    'dons_en_attente': dons_en_attente,
                })
            else:
                context.update({
                    'total_donations': 0,
                    'total_amount': 0,
                    'beneficiaires': 0,
                    'recent_amount': 0,
                    'new_donations': 0,
                    'dons_en_attente': 0,
                })

        except Exception as e:
            print(f"Erreur dashboard donateur: {e}")
            context.update({
                'total_donations': 0,
                'total_amount': 0,
                'beneficiaires': 0,
                'recent_amount': 0,
                'new_donations': 0,
                'dons_en_attente': 0,
            })

    # === DASHBOARD PERSONNE VULNÉRABLE AVEC FORMATIONS ===
    elif user.is_vulnerable:
        try:
            personne = user.personnevulnerable

            if FORMATIONS_AVAILABLE:
                # Demandes de formation de cette personne
                demandes_formation = DemandeFormation.objects.filter(personne=personne)
                demandes_formation_count = demandes_formation.count()

                # Parcours de formation
                parcours_actifs = ParcoursFormation.objects.filter(
                    demande_formation__personne=personne,
                    statut_actuel__in=['pre_inscrit', 'forme', 'projet_valide']
                ).count()

                # Projets de vie
                projets_vie = ProjetVie.objects.filter(personne=personne)
                projets_vie_count = projets_vie.count()
                projets_actifs = projets_vie.exclude(statut='abandonne').count()

                # Formations terminées
                formations_terminees = ParcoursFormation.objects.filter(
                    demande_formation__personne=personne,
                    statut_actuel__in=['forme', 'autonome']
                ).count()

                # Pourcentage de progression formations
                total_parcours = ParcoursFormation.objects.filter(
                    demande_formation__personne=personne
                ).count()
                formations_completees_pct = (formations_terminees / total_parcours * 100) if total_parcours > 0 else 0

                # Pourcentage projets lancés
                projets_lances = projets_vie.filter(
                    statut__in=['en_cours', 'realise']
                ).count()
                projets_lances_pct = (projets_lances / projets_vie_count * 100) if projets_vie_count > 0 else 0

                context.update({
                    'demandes_formation_count': demandes_formation_count,
                    'parcours_actifs': parcours_actifs,
                    'projets_vie_count': projets_vie_count,
                    'projets_actifs': projets_actifs,
                    'formations_terminees': formations_terminees,
                    'formations_completees': formations_terminees,
                    'formations_completees_pct': formations_completees_pct,
                    'projets_lances': projets_lances,
                    'projets_lances_pct': projets_lances_pct,
                })
            else:
                context.update({
                    'demandes_formation_count': 0,
                    'parcours_actifs': 0,
                    'projets_vie_count': 0,
                    'projets_actifs': 0,
                    'formations_terminees': 0,
                    'formations_completees': 0,
                    'formations_completees_pct': 0,
                    'projets_lances': 0,
                    'projets_lances_pct': 0,
                })

            # Calcul des dons reçus (existant)
            montant_total = Decimal('0.00')
            nombre_donateurs = set()

            dons_recus = []
            if hasattr(personne, 'dons'):
                dons_recus.extend(personne.dons.filter(est_reparti=True))

            for don in dons_recus:
                try:
                    if hasattr(don, 'personne_vulnerable') and don.personne_vulnerable.exists():
                        nb_beneficiaires = don.personne_vulnerable.count()
                    elif hasattr(don, 'entite_vulnerable') and don.entite_vulnerable:
                        nb_beneficiaires = don.entite_vulnerable.personnevulnerable_set.filter(
                            est_vulnerable=True
                        ).count()
                    else:
                        nb_beneficiaires = 1

                    montant_par_personne = don.montant / nb_beneficiaires if nb_beneficiaires > 0 else don.montant
                    montant_total += montant_par_personne
                    nombre_donateurs.add(don.donateur.id if hasattr(don, 'donateur') else 0)

                except Exception as e:
                    print(f"Erreur calcul don {don.id}: {e}")
                    continue

            # Progression vers objectif
            objectif = Decimal('200000.00')
            progression = (montant_total / objectif * 100) if objectif > 0 else Decimal('0.00')
            progression = min(progression, 100)

            context.update({
                'personne': personne,
                'montant_total': float(montant_total),
                'progression': float(progression),
                'nombre_donateurs': len(nombre_donateurs),
                'objectif': float(objectif),
            })

        except PersonneVulnerable.DoesNotExist:
            context.update({
                'personne': None,
                'montant_total': 0,
                'progression': 0,
                'nombre_donateurs': 0,
                'objectif': 200000,
                'demandes_formation_count': 0,
                'parcours_actifs': 0,
                'projets_vie_count': 0,
                'projets_actifs': 0,
                'formations_terminees': 0,
            })

    # === DASHBOARD RECENSEUR AVEC FORMATIONS ===
    elif user.is_recenseur:
        try:
            personnes_recensees = user.personnes_recensees.all()
            total_recensements = personnes_recensees.count()

            # Statistiques recensement
            validees = personnes_recensees.filter(validated_by_admin=True).count()
            en_attente = personnes_recensees.filter(validated_by_admin=False).count()
            taux_validation = (validees / total_recensements * 100) if total_recensements > 0 else 0

            # Recensements récents
            debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            new_recensements = personnes_recensees.count()  # Adapter selon votre modèle de date

            context.update({
                'total_recensements': total_recensements,
                'validees': validees,
                'en_attente': en_attente,
                'taux_validation': round(taux_validation, 1),
                'new_recensements': new_recensements,
            })

        except Exception as e:
            print(f"Erreur dashboard recenseur: {e}")
            context.update({
                'total_recensements': 0,
                'validees': 0,
                'en_attente': 0,
                'taux_validation': 0,
                'new_recensements': 0,
            })

    # === DASHBOARD ADMINISTRATEUR AVEC FORMATIONS ===
    elif user.is_superuser or user.is_staff:
        try:
            # Statistiques utilisateurs
            total_users = User.objects.count()
            total_donateurs = User.objects.filter(is_donator=True).count()
            total_vulnerables = User.objects.filter(is_vulnerable=True).count()
            total_recenseurs = User.objects.filter(is_recenseur=True).count()

            # Personnes à valider
            personnes_a_valider = PersonneVulnerable.objects.filter(
                validated_by_admin=False,
                user__isnull=True
            ).count()

            if FORMATIONS_AVAILABLE:
                # Statistiques formations admin
                formations_actives = Formation.objects.filter(est_active=True).count()
                demandes_en_attente = DemandeFormation.objects.filter(
                    statut__in=['en_attente', 'analysee']
                ).count()
                parcours_en_cours = ParcoursFormation.objects.filter(
                    statut_actuel__in=['pre_inscrit', 'forme', 'projet_valide']
                ).count()
                projets_en_cours = ProjetVie.objects.exclude(statut='abandonne').count()

                # Taux de succès formations
                total_parcours = ParcoursFormation.objects.count()
                parcours_reussis = ParcoursFormation.objects.filter(
                    statut_actuel__in=['forme', 'autonome']
                ).count()
                taux_succes = (parcours_reussis / total_parcours * 100) if total_parcours > 0 else 0

                context.update({
                    'formations_actives': formations_actives,
                    'demandes_en_attente': demandes_en_attente,
                    'parcours_en_cours': parcours_en_cours,
                    'projets_en_cours': projets_en_cours,
                    'taux_succes_formations': round(taux_succes, 1),
                })

            context.update({
                'total_users': total_users,
                'total_donateurs': total_donateurs,
                'total_vulnerables': total_vulnerables,
                'total_recenseurs': total_recenseurs,
                'personnes_a_valider': personnes_a_valider,
                'total_platform_dons': 0,  # À calculer selon votre modèle
                'total_impact': total_vulnerables,
            })

        except Exception as e:
            print(f"Erreur dashboard admin: {e}")
            context.update({
                'total_users': 0,
                'total_donateurs': 0,
                'total_vulnerables': 0,
                'total_recenseurs': 0,
                'personnes_a_valider': 0,
                'formations_actives': 0,
                'demandes_en_attente': 0,
                'parcours_en_cours': 0,
                'total_platform_dons': 0,
                'total_impact': 0,
            })

    # === NOTIFICATIONS ===
    try:
        notifications_count = 0
        if hasattr(user, 'notifications'):
            notifications_count = user.notifications.filter(is_read=False).count()
        context['notifications_count'] = notifications_count
    except:
        context['notifications_count'] = 0

    return render(request, 'users/dashboard_formation.html', context)


@login_required
def api_dashboard_formation_stats(request):
    """
    API pour les statistiques du dashboard formations en temps réel
    """
    from django.http import JsonResponse

    user = request.user
    stats = {}

    try:
        if user.is_donator:
            dons = getattr(user, 'dons', None)
            if dons:
                dons = dons.all()
                stats = {
                    'total_donations': dons.count(),
                    'total_amount': sum([float(don.montant) for don in dons]),
                    'dons_en_attente': dons.filter(est_reparti=False).count(),
                }
            else:
                stats = {'total_donations': 0, 'total_amount': 0, 'dons_en_attente': 0}

        elif user.is_vulnerable:
            try:
                personne = user.personnevulnerable

                # Stats dons
                montant_total = Decimal('0.00')
                if hasattr(personne, 'dons'):
                    for don in personne.dons.filter(est_reparti=True):
                        nb_beneficiaires = 1
                        if hasattr(don, 'personne_vulnerable') and don.personne_vulnerable.exists():
                            nb_beneficiaires = don.personne_vulnerable.count()
                        montant_total += don.montant / nb_beneficiaires

                progression = (montant_total / Decimal('200000.00') * 100) if montant_total > 0 else 0

                # Stats formations
                formation_stats = {}
                if FORMATIONS_AVAILABLE:
                    demandes = DemandeFormation.objects.filter(personne=personne).count()
                    projets = ProjetVie.objects.filter(personne=personne).count()
                    formation_stats = {
                        'demandes_formation_count': demandes,
                        'projets_vie_count': projets,
                    }

                stats = {
                    'montant_total': float(montant_total),
                    'progression': float(min(progression, 100)),
                    **formation_stats
                }
            except PersonneVulnerable.DoesNotExist:
                stats = {'montant_total': 0, 'progression': 0}

        elif user.is_recenseur:
            personnes = user.personnes_recensees.all()
            stats = {
                'total_recensements': personnes.count(),
                'validees': personnes.filter(validated_by_admin=True).count(),
                'en_attente': personnes.filter(validated_by_admin=False).count(),
            }

        elif user.is_superuser or user.is_staff:
            admin_stats = {
                'total_users': User.objects.count(),
                'personnes_a_valider': PersonneVulnerable.objects.filter(
                    validated_by_admin=False,
                    user__isnull=True
                ).count(),
                'total_vulnerables': User.objects.filter(is_vulnerable=True).count(),
            }

            if FORMATIONS_AVAILABLE:
                formation_admin_stats = {
                    'formations_actives': Formation.objects.filter(est_active=True).count(),
                    'demandes_en_attente': DemandeFormation.objects.filter(
                        statut__in=['en_attente', 'analysee']
                    ).count(),
                    'parcours_en_cours': ParcoursFormation.objects.filter(
                        statut_actuel__in=['pre_inscrit', 'forme', 'projet_valide']
                    ).count(),
                }
                admin_stats.update(formation_admin_stats)

            stats = admin_stats

    except Exception as e:
        print(f"Erreur API stats formations: {e}")
        stats = {'error': 'Erreur lors de la récupération des statistiques'}

    return JsonResponse(stats)


@login_required
def api_formation_activity(request):
    """
    API pour récupérer l'activité récente liée aux formations
    """
    from django.http import JsonResponse

    user = request.user
    activities = []

    try:
        if user.is_vulnerable and FORMATIONS_AVAILABLE:
            personne = user.personnevulnerable

            # Demandes de formation récentes
            recent_demandes = DemandeFormation.objects.filter(
                personne=personne
            ).order_by('-date_demande')[:5]

            for demande in recent_demandes:
                activities.append({
                    'type': 'demande_formation',
                    'title': 'Demande de formation',
                    'description': f'Formation: {demande.formation_souhaitee.nom}',
                    'time': demande.date_demande.strftime('%d/%m/%Y %H:%M'),
                    'icon': 'fas fa-graduation-cap',
                    'color': 'primary',
                    'status': demande.get_statut_display()
                })

            # Projets récents
            recent_projets = ProjetVie.objects.filter(
                personne=personne
            ).order_by('-date_creation')[:3]

            for projet in recent_projets:
                activities.append({
                    'type': 'projet_vie',
                    'title': 'Projet de vie',
                    'description': f'Projet: {projet.titre_projet}',
                    'time': projet.date_creation.strftime('%d/%m/%Y %H:%M'),
                    'icon': 'fas fa-lightbulb',
                    'color': 'success',
                    'status': projet.get_statut_display()
                })

        elif user.is_recenseur and FORMATIONS_AVAILABLE:
            # Orientations vers formations
            recent_recensements = user.personnes_recensees.order_by('-id')[:5]
            for personne in recent_recensements:
                activities.append({
                    'type': 'orientation',
                    'title': 'Orientation formation',
                    'description': f'Personne: {personne.get_full_name()}',
                    'time': 'Récemment',
                    'icon': 'fas fa-user-graduate',
                    'color': 'info',
                    'status': 'Validée' if personne.validated_by_admin else 'En attente'
                })

        elif (user.is_superuser or user.is_staff) and FORMATIONS_AVAILABLE:
            # Activité admin formations
            recent_demandes = DemandeFormation.objects.filter(
                statut='en_attente'
            ).order_by('-date_demande')[:5]

            for demande in recent_demandes:
                activities.append({
                    'type': 'admin_demande',
                    'title': 'Nouvelle demande',
                    'description': f'{demande.personne.get_full_name()} - {demande.formation_souhaitee.nom}',
                    'time': demande.date_demande.strftime('%d/%m/%Y %H:%M'),
                    'icon': 'fas fa-inbox',
                    'color': 'warning',
                    'status': 'À traiter'
                })

    except Exception as e:
        print(f"Erreur récupération activité formations: {e}")

    return JsonResponse({'activities': activities})


# Décorateur pour vérifier l'accès aux formations
def formations_required(view_func):
    """Décorateur pour vérifier que les formations sont disponibles"""
    from functools import wraps
    from django.contrib import messages
    from django.shortcuts import redirect

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not FORMATIONS_AVAILABLE:
            messages.warning(request, "Les fonctionnalités de formation ne sont pas disponibles.")
            return redirect('users:dashboard_formation_complete')
        return view_func(request, *args, **kwargs)

    return _wrapped_view


# Vue pour les statistiques formations détaillées
@login_required
@formations_required
def formation_detailed_stats(request):
    """
    Vue pour les statistiques détaillées des formations
    """
    user = request.user
    context = {}

    if user.is_vulnerable:
        try:
            personne = user.personnevulnerable

            # Progression détaillée
            demandes = DemandeFormation.objects.filter(personne=personne)
            parcours = ParcoursFormation.objects.filter(demande_formation__personne=personne)
            projets = ProjetVie.objects.filter(personne=personne)

            context.update({
                'demandes_formation': demandes,
                'parcours_formation': parcours,
                'projets_vie': projets,
                'moyenne_score_formabilite': demandes.aggregate(
                    avg_score=Avg('score_formabilite')
                )['avg_score'] or 0,
            })

        except PersonneVulnerable.DoesNotExist:
            context = {'error': 'Profil non trouvé'}

    elif user.is_recenseur:
        # Stats pour recenseur - orientations formations
        personnes_orientees = user.personnes_recensees.filter(
            validated_by_admin=True
        )

        context.update({
            'personnes_orientees': personnes_orientees,
            'taux_orientation_formation': 0,  # À calculer selon vos besoins
        })

    elif user.is_superuser or user.is_staff:
        # Stats administrateur formations
        context.update({
            'formations_populaires': Formation.objects.annotate(
                nb_demandes=Count('demandes_formation')
            ).order_by('-nb_demandes')[:10],
            'taux_reussite_global': 0,  # À calculer
            'revenue_formations': 0,  # À calculer
        })

    return render(request, 'users/formation_detailed_stats.html', context)


# Fonction utilitaire pour les graphiques formations
def get_formation_monthly_data(user, months=12):
    """
    Récupère les données mensuelles liées aux formations pour un utilisateur
    """
    if not FORMATIONS_AVAILABLE:
        return [0] * months

    monthly_data = []

    for i in range(months):
        month_start = timezone.now().replace(day=1) - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)

        if user.is_vulnerable:
            try:
                personne = user.personnevulnerable
                count = DemandeFormation.objects.filter(
                    personne=personne,
                    date_demande__gte=month_start,
                    date_demande__lt=month_end
                ).count()
                monthly_data.append(count)
            except:
                monthly_data.append(0)

        elif user.is_superuser or user.is_staff:
            count = DemandeFormation.objects.filter(
                date_demande__gte=month_start,
                date_demande__lt=month_end
            ).count()
            monthly_data.append(count)

        else:
            monthly_data.append(0)

    return list(reversed(monthly_data))