# formation/views.py
import json

import csv
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum, Max
from django.utils import timezone
from django.db.models.functions import TruncMonth

from .forms import (
    ParcoursFormationForm, EvaluationSuiviForm,
    FiltreDemandesForm, DecisionDemandeForm
)

from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, SystemMessage

from .models import (
    Formation, DemandeFormation, ParcoursFormation,
    ProjetVie, SuiviProgression
)
from .forms import (
    DemandeFormationForm, ProjetVieForm,
    FormationForm, EvaluationSuiviForm
)
from users.models import PersonneVulnerable, User

# Initialisation du LLM
llm = ChatOllama(base_url="http://localhost:11434", model="mistral")


def is_vulnerable_or_admin(user):
    """Vérifie si l'utilisateur est vulnérable ou admin"""
    return user.is_vulnerable or user.is_superuser


def is_admin_or_mentor(user):
    """Vérifie si l'utilisateur est admin ou mentor"""
    return user.is_superuser or user.is_staff


@login_required
def formations_list(request):
    """Liste des formations disponibles"""
    formations = Formation.objects.filter(est_active=True).order_by('nom')

    # Filtres
    type_filter = request.GET.get('type')
    if type_filter:
        formations = formations.filter(type_formation=type_filter)

    search = request.GET.get('search')
    if search:
        formations = formations.filter(
            Q(nom__icontains=search) |
            Q(description__icontains=search)
        )

    # Pagination
    paginator = Paginator(formations, 12)
    page_number = request.GET.get('page')
    formations_page = paginator.get_page(page_number)

    # Types de formation pour le filtre
    types_formation = Formation.TYPE_FORMATION_CHOICES

    # Vérifier si l'utilisateur a un profil PersonneVulnerable
    has_vulnerable_profile = False
    user_profile = None
    if request.user.is_authenticated:
        try:
            user_profile = request.user.personnevulnerable
            has_vulnerable_profile = True
        except PersonneVulnerable.DoesNotExist:
            has_vulnerable_profile = False

    # Statistiques pour l'affichage
    total_places = formations.aggregate(
        total=Sum('places_disponibles')
    )['total'] or 0

    context = {
        'formations': formations_page,
        'types_formation': types_formation,
        'type_filter': type_filter,
        'search': search,
        'has_vulnerable_profile': has_vulnerable_profile,
        'user_profile': user_profile,
        'total_places_disponibles': total_places,
    }

    return render(request, 'formation/formations_list.html', context)

@login_required
def formation_detail(request, formation_id):
    """Détail d'une formation"""
    formation = get_object_or_404(Formation, id=formation_id, est_active=True)

    # Vérifier si l'utilisateur a déjà fait une demande
    demande_existante = None
    if hasattr(request.user, 'personnevulnerable'):
        demande_existante = DemandeFormation.objects.filter(
            personne=request.user.personnevulnerable,
            formation_souhaitee=formation
        ).first()

    context = {
        'formation': formation,
        'demande_existante': demande_existante,
        'places_restantes': formation.places_restantes(),
    }

    return render(request, 'formation/formation_detail.html', context)


@login_required
@user_passes_test(is_vulnerable_or_admin)
def demande_formation(request, formation_id):
    """Création d'une demande de formation"""
    formation = get_object_or_404(Formation, id=formation_id, est_active=True)

    # Vérifier que l'utilisateur a un profil PersonneVulnerable
    try:
        personne = request.user.personnevulnerable
    except PersonneVulnerable.DoesNotExist:
        messages.error(request, "Vous devez avoir un profil de personne vulnérable pour faire une demande.")
        return redirect('formation:formations_list')

    # Vérifier qu'il n'y a pas déjà une demande
    demande_existante = DemandeFormation.objects.filter(
        personne=personne,
        formation_souhaitee=formation
    ).exclude(statut='refusee').first()

    if demande_existante:
        messages.warning(request, "Vous avez déjà une demande en cours pour cette formation.")
        return redirect('formation:mes_demandes')

    if request.method == 'POST':
        form = DemandeFormationForm(request.POST)
        if form.is_valid():
            demande = form.save(commit=False)
            demande.personne = personne
            demande.formation_souhaitee = formation
            demande.save()

            # Analyser automatiquement la demande avec le LLM (VERSION SYNCHRONE)
            try:
                result = analyser_demande_formation_sync(demande.id)
                if result['success']:
                    messages.success(request, "Votre demande a été soumise et analysée avec succès!")
                else:
                    messages.warning(request, "Votre demande a été soumise mais l'analyse automatique a échoué.")
            except Exception as e:
                messages.warning(request, "Votre demande a été soumise mais l'analyse automatique a échoué.")

            return redirect('formation:mes_demandes')
    else:
        form = DemandeFormationForm()

    context = {
        'form': form,
        'formation': formation,
        'personne': personne,
    }

    return render(request, 'formation/demande_formation.html', context)


def build_formation_analysis_prompt(demande):
    """Construit le prompt pour l'analyse de formabilité - VERSION CORRIGÉE"""
    personne = demande.personne
    formation = demande.formation_souhaitee

    return f"""
Vous êtes un expert en évaluation de formabilité pour des programmes d'insertion socio-économique.

Analysez cette demande de formation et déterminez la formabilité du candidat :

PROFIL DU CANDIDAT :
- Nom : {personne.get_full_name()}
- Âge : {getattr(personne, 'age', 'Non renseigné')} ans
- Niveau d'éducation : {getattr(personne, 'niveau_etude', 'Non renseigné')}
- Situation professionnelle : {getattr(personne, 'emploi', 'Non renseigné')}
- Revenu mensuel : {getattr(personne, 'revenu', 'Non renseigné')} FCFA
- Région : {getattr(personne, 'region_geographique', 'Non renseigné')}
- Nombre de personnes dans le ménage : {getattr(personne, 'nombre_personnes_menage', 'Non renseigné')}
- État de santé : {getattr(personne, 'etat_sante', 'Non renseigné')}
- Handicap : {getattr(personne, 'handicap', 'Non renseigné')}

FORMATION DEMANDÉE :
- Nom : {formation.nom}
- Type : {formation.get_type_formation_display()}
- Durée : {formation.duree_semaines} semaines
- Niveau requis : {formation.get_niveau_requis_display()}
- Âge requis : {formation.age_min}-{formation.age_max} ans

MOTIVATION ET PROJET :
- Motivation principale : {demande.get_motivation_principale_display()}
- Expérience antérieure : {demande.experience_anterieure or "Aucune"}
- Compétences actuelles : {demande.competences_actuelles or "Non renseignées"}
- Disponibilité : {demande.disponibilite_horaire}
- Contraintes : {demande.contraintes_personnelles or "Aucune"}
- A une idée de projet : {"Oui" if demande.a_idee_projet else "Non"}
- Description du projet : {demande.description_projet or "Non renseigné"}
- Souhaite financement : {"Oui" if demande.souhaite_financement else "Non"}
- Montant souhaité : {demande.montant_financement or "Non renseigné"} FCFA
- Accepte mentoring : {"Oui" if demande.accepte_mentoring else "Non"}

CRITÈRES D'ÉVALUATION :
1. Compatibilité âge et prérequis (0-20 points)
2. Motivation et engagement (0-25 points)
3. Capacité d'apprentissage et niveau éducatif (0-20 points)
4. Faisabilité du projet post-formation (0-20 points)
5. Contexte socio-économique favorable (0-15 points)

Répondez en JSON strict avec les clés suivantes :
{{
    "score_formabilite": <score de 0 à 100>,
    "analyse_detaillee": "<analyse complète des points forts et faiblesses>",
    "recommandations": "<recommandations spécifiques>",
    "criteres_scores": {{
        "compatibilite": <score 0-20>,
        "motivation": <score 0-25>,
        "capacite_apprentissage": <score 0-20>,
        "faisabilite_projet": <score 0-20>,
        "contexte_socio": <score 0-15>
    }},
    "decision_recommandee": "<accepter|refuser|conditionner>",
    "conditions": "<conditions si décision conditionnée>"
}}
"""


def analyser_demande_formation_sync(demande_id):
    """Analyse synchrone d'une demande de formation par le LLM"""
    try:
        demande = DemandeFormation.objects.get(id=demande_id)

        prompt = build_formation_analysis_prompt(demande)

        messages_llm = [
            SystemMessage(content="Tu es un expert en évaluation de formabilité et insertion socio-économique."),
            HumanMessage(content=prompt)
        ]

        response = llm(messages_llm)
        llm_response = response.content

        try:
            result = json.loads(llm_response)

            # Mettre à jour la demande avec les résultats
            demande.score_formabilite = result.get('score_formabilite')
            demande.analyse_llm = result.get('analyse_detaillee', '')
            demande.recommandations_llm = result.get('recommandations', '')
            demande.criteres_evaluacion = result.get('criteres_scores', {})
            demande.statut = 'analysee'
            demande.date_analyse = timezone.now()

            # Décision automatique basée sur le score
            if demande.score_formabilite >= 70:
                demande.statut = 'acceptee'
                demande.date_decision = timezone.now()

                # Créer automatiquement le parcours de formation
                parcours = ParcoursFormation.objects.create(
                    demande_formation=demande
                )

                # Si la personne a un projet, le créer
                if demande.a_idee_projet and demande.description_projet:
                    projet = ProjetVie.objects.create(
                        personne=demande.personne,
                        titre_projet=f"Projet post-formation {demande.formation_souhaitee.nom}",
                        description=demande.description_projet,
                        secteur_activite=demande.formation_souhaitee.get_type_formation_display(),
                        budget_estime=demande.montant_financement or 0,
                        type_financement='microcredit' if demande.souhaite_financement else 'autofinancement'
                    )
                    parcours.projet_vie = projet
                    parcours.save()

            demande.save()

            return {
                'success': True,
                'score': demande.score_formabilite,
                'statut': demande.statut
            }

        except json.JSONDecodeError as e:
            demande.analyse_llm = f"Erreur d'analyse : {str(e)}"
            demande.statut = 'analysee'
            demande.save()
            return {'success': False, 'error': str(e)}

    except DemandeFormation.DoesNotExist:
        return {'success': False, 'error': 'Demande introuvable'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def build_projet_analysis_prompt(projet):
    """Construit le prompt pour l'analyse de faisabilité d'un projet - VERSION CORRIGÉE"""
    return f"""
Analysez la faisabilité de ce projet d'entreprise :

PROJET :
- Titre : {projet.titre_projet}
- Description : {projet.description}
- Secteur : {projet.secteur_activite}
- Budget estimé : {projet.budget_estime} FCFA
- Type de financement : {projet.get_type_financement_display()}

PROFIL PORTEUR :
- Nom : {projet.personne.get_full_name()}
- Âge : {getattr(projet.personne, 'age', 'Non renseigné')} ans
- Éducation : {getattr(projet.personne, 'niveau_etude', 'Non renseigné')}
- Région : {getattr(projet.personne, 'region_geographique', 'Non renseigné')}
- Situation : {getattr(projet.personne, 'emploi', 'Non renseigné')}

Évaluez et répondez en JSON :
{{
    "faisabilite_score": <score 0-100>,
    "analyse": "<analyse détaillée>",
    "recommandations": "<recommandations>",
    "risques": "<principaux risques>",
    "points_forts": "<points forts du projet>"
}}
"""


def analyser_projet_vie_sync(projet_id):
    """Analyse synchrone d'un projet de vie par le LLM"""
    try:
        projet = ProjetVie.objects.get(id=projet_id)
        prompt = build_projet_analysis_prompt(projet)

        messages_llm = [
            SystemMessage(content="Tu es un expert en analyse de faisabilité de projets d'entreprise."),
            HumanMessage(content=prompt)
        ]

        response = llm(messages_llm)

        try:
            result = json.loads(response.content)

            projet.faisabilite_score = result.get('faisabilite_score')
            projet.analyse_ia = result.get('analyse', '')
            projet.recommandations = result.get('recommandations', '')
            projet.save()

            return {'success': True}

        except json.JSONDecodeError as e:
            projet.analyse_ia = f"Erreur d'analyse : {str(e)}"
            projet.save()
            return {'success': False, 'error': str(e)}

    except ProjetVie.DoesNotExist:
        return {'success': False, 'error': 'Projet introuvable'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# Version asynchrone pour Celery (optionnel) avec gestion d'erreur
try:
    from celery import shared_task


    @shared_task
    def analyser_demande_formation(demande_id):
        return analyser_demande_formation_sync(demande_id)


    @shared_task
    def analyser_projet_vie(projet_id):
        return analyser_projet_vie_sync(projet_id)

except ImportError:
    # Si Celery n'est pas installé, utiliser la version synchrone
    def analyser_demande_formation(demande_id):
        return analyser_demande_formation_sync(demande_id)


    def analyser_projet_vie(projet_id):
        return analyser_projet_vie_sync(projet_id)


@login_required
@user_passes_test(is_vulnerable_or_admin)
def mes_demandes(request):
    """Liste des demandes de formation de l'utilisateur"""
    try:
        personne = request.user.personnevulnerable
    except PersonneVulnerable.DoesNotExist:
        messages.error(request, "Vous devez avoir un profil de personne vulnérable.")
        return redirect('profile')

    demandes = DemandeFormation.objects.filter(personne=personne).order_by('-date_demande')

    context = {
        'demandes': demandes,
        'personne': personne,
    }

    return render(request, 'formation/mes_demandes.html', context)


@login_required
@user_passes_test(is_vulnerable_or_admin)
def mon_parcours(request):
    """Vue du parcours de formation de l'utilisateur"""
    try:
        personne = request.user.personnevulnerable
    except PersonneVulnerable.DoesNotExist:
        messages.error(request, "Vous devez avoir un profil de personne vulnérable.")
        return redirect('profile')

    parcours = ParcoursFormation.objects.filter(
        demande_formation__personne=personne
    ).order_by('-date_creation')

    context = {
        'parcours_list': parcours,
        'personne': personne,
    }

    return render(request, 'formation/mon_parcours.html', context)


@login_required
@user_passes_test(is_vulnerable_or_admin)
def projet_vie_create(request):
    """Création d'un projet de vie"""
    try:
        personne = request.user.personnevulnerable
    except PersonneVulnerable.DoesNotExist:
        messages.error(request, "Vous devez avoir un profil de personne vulnérable.")
        return redirect('profile')

    if request.method == 'POST':
        form = ProjetVieForm(request.POST)
        if form.is_valid():
            projet = form.save(commit=False)
            projet.personne = personne
            projet.save()

            # Analyser la faisabilité du projet avec le LLM (VERSION SYNCHRONE)
            try:
                result = analyser_projet_vie_sync(projet.id)
                if result['success']:
                    messages.success(request, "Votre projet a été créé et analysé automatiquement.")
                else:
                    messages.warning(request, "Votre projet a été créé mais l'analyse automatique a échoué.")
            except Exception as e:
                messages.warning(request, "Votre projet a été créé mais l'analyse automatique a échoué.")

            return redirect('formation:mes_projets')
    else:
        form = ProjetVieForm()

    context = {
        'form': form,
        'personne': personne,
    }

    return render(request, 'formation/projet_vie_create.html', context)


@login_required
@user_passes_test(is_vulnerable_or_admin)
def mes_projets(request):
    """Liste des projets de vie de l'utilisateur"""
    try:
        personne = request.user.personnevulnerable
    except PersonneVulnerable.DoesNotExist:
        messages.error(request, "Vous devez avoir un profil de personne vulnérable.")
        return redirect('profile')

    projets = ProjetVie.objects.filter(personne=personne).order_by('-date_creation')

    context = {
        'projets': projets,
        'personne': personne,
    }

    return render(request, 'formation/mes_projets.html', context)


# ===== VUES ADMIN =====

@login_required
@user_passes_test(is_admin_or_mentor)
def admin_dashboard(request):
    """Dashboard administrateur pour le module formation"""
    # Statistiques générales
    stats = {
        'total_formations': Formation.objects.filter(est_active=True).count(),
        'total_demandes': DemandeFormation.objects.count(),
        'demandes_en_attente': DemandeFormation.objects.filter(statut='en_attente').count(),
        'formations_en_cours': DemandeFormation.objects.filter(statut='en_cours').count(),
        'formations_terminees': DemandeFormation.objects.filter(statut='terminee').count(),
        'projets_actifs': ProjetVie.objects.exclude(statut='abandonne').count(),
    }

    # Demandes récentes
    demandes_recentes = DemandeFormation.objects.select_related(
        'personne', 'formation_souhaitee'
    ).order_by('-date_demande')[:10]

    # Formations populaires
    formations_populaires = Formation.objects.annotate(
        nb_demandes=Count('demandes_formation')
    ).order_by('-nb_demandes')[:5]

    # Score moyen de formabilité
    score_moyen = DemandeFormation.objects.filter(
        score_formabilite__isnull=False
    ).aggregate(
        avg_score=Avg('score_formabilite')
    )['avg_score']

    context = {
        'stats': stats,
        'demandes_recentes': demandes_recentes,
        'formations_populaires': formations_populaires,
        'score_moyen_formabilite': score_moyen,
    }

    return render(request, 'formation/admin/dashboard.html', context)


@login_required
@user_passes_test(is_admin_or_mentor)
def admin_demandes_list(request):
    """Liste des demandes pour l'administration"""
    demandes = DemandeFormation.objects.select_related(
        'personne', 'formation_souhaitee'
    ).order_by('-date_demande')

    # Filtres
    statut_filter = request.GET.get('statut')
    if statut_filter:
        demandes = demandes.filter(statut=statut_filter)

    formation_filter = request.GET.get('formation')
    if formation_filter:
        demandes = demandes.filter(formation_souhaitee_id=formation_filter)

    # Pagination
    paginator = Paginator(demandes, 20)
    page_number = request.GET.get('page')
    demandes_page = paginator.get_page(page_number)

    # Données pour les filtres
    formations = Formation.objects.filter(est_active=True)
    statuts = DemandeFormation.STATUT_CHOICES

    context = {
        'demandes': demandes_page,
        'formations': formations,
        'statuts': statuts,
        'statut_filter': statut_filter,
        'formation_filter': formation_filter,
    }

    return render(request, 'formation/admin/demandes_list.html', context)


@login_required
@user_passes_test(is_admin_or_mentor)
def admin_demande_detail(request, demande_id):
    """Détail d'une demande pour l'administration"""
    demande = get_object_or_404(
        DemandeFormation.objects.select_related('personne', 'formation_souhaitee'),
        id=demande_id
    )

    if request.method == 'POST':
        action = request.POST.get('action')
        commentaire = request.POST.get('commentaire', '')

        if action == 'accepter':
            demande.statut = 'acceptee'
            demande.date_decision = timezone.now()
            demande.responsable_decision = request.user
            demande.commentaire_decision = commentaire

            # Créer le parcours si pas déjà créé
            parcours, created = ParcoursFormation.objects.get_or_create(
                demande_formation=demande
            )

            messages.success(request, "Demande acceptée avec succès.")

        elif action == 'refuser':
            demande.statut = 'refusee'
            demande.date_decision = timezone.now()
            demande.responsable_decision = request.user
            demande.commentaire_decision = commentaire
            messages.success(request, "Demande refusée.")

        elif action == 'reanalyser':
            # Relancer l'analyse IA
            result = analyser_demande_formation_sync(demande.id)
            if result['success']:
                messages.success(request, "Réanalyse effectuée avec succès.")
            else:
                messages.error(request, f"Erreur lors de la réanalyse : {result['error']}")

        demande.save()
        return redirect('formation:admin_demande_detail', demande_id=demande.id)

    # Récupérer le parcours s'il existe
    try:
        parcours = demande.parcours
    except ParcoursFormation.DoesNotExist:
        parcours = None

    context = {
        'demande': demande,
        'parcours': parcours,
    }

    return render(request, 'formation/admin/demande_detail.html', context)


@login_required
@user_passes_test(is_admin_or_mentor)
def admin_formations_manage(request):
    """Gestion des formations"""
    formations = Formation.objects.all().order_by('nom')

    context = {
        'formations': formations,
    }

    return render(request, 'formation/admin/formations_manage.html', context)


@login_required
@user_passes_test(is_admin_or_mentor)
def admin_formation_create(request):
    """Création d'une nouvelle formation"""
    if request.method == 'POST':
        form = FormationForm(request.POST)
        if form.is_valid():
            formation = form.save()
            messages.success(request, f"Formation '{formation.nom}' créée avec succès.")
            return redirect('formation:admin_formations_manage')
    else:
        form = FormationForm()

    context = {
        'form': form,
        'title': 'Créer une formation',
    }

    return render(request, 'formation/admin/formation_form.html', context)


@login_required
@user_passes_test(is_admin_or_mentor)
def admin_formation_edit(request, formation_id):
    """Modification d'une formation"""
    formation = get_object_or_404(Formation, id=formation_id)

    if request.method == 'POST':
        form = FormationForm(request.POST, instance=formation)
        if form.is_valid():
            formation = form.save()
            messages.success(request, f"Formation '{formation.nom}' mise à jour avec succès.")
            return redirect('formation:admin_formations_manage')
    else:
        form = FormationForm(instance=formation)

    context = {
        'form': form,
        'formation': formation,
        'title': 'Modifier la formation',
    }

    return render(request, 'formation/admin/formation_form.html', context)


# ===== API ENDPOINTS =====

@csrf_exempt
def api_analyser_demande(request, demande_id):
    """API pour analyser une demande spécifique"""
    if request.method == 'POST':
        result = analyser_demande_formation_sync(demande_id)
        return JsonResponse(result)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def api_stats_formation(request):
    """API pour les statistiques de formation"""
    stats = {
        'demandes_par_statut': {},
        'demandes_par_formation': {},
        'evolution_mensuelle': {},
    }

    # Demandes par statut
    for statut, label in DemandeFormation.STATUT_CHOICES:
        count = DemandeFormation.objects.filter(statut=statut).count()
        stats['demandes_par_statut'][label] = count

    # Demandes par formation
    formations_stats = Formation.objects.annotate(
        nb_demandes=Count('demandes_formation')
    ).values('nom', 'nb_demandes')

    for formation in formations_stats:
        stats['demandes_par_formation'][formation['nom']] = formation['nb_demandes']

    return JsonResponse(stats)


# ===== VUES ADDITIONNELLES =====

@login_required
@user_passes_test(is_vulnerable_or_admin)
def demande_detail(request, demande_id):
    """Détail d'une demande de formation pour l'utilisateur"""
    try:
        personne = request.user.personnevulnerable
        demande = get_object_or_404(
            DemandeFormation.objects.select_related('formation_souhaitee'),
            id=demande_id,
            personne=personne
        )
    except PersonneVulnerable.DoesNotExist:
        messages.error(request, "Accès non autorisé.")
        return redirect('profile')

    context = {
        'demande': demande,
        'personne': personne,
    }

    return render(request, 'formation/demande_detail.html', context)


@login_required
@user_passes_test(is_vulnerable_or_admin)
def projet_detail(request, projet_id):
    """Détail d'un projet de vie pour l'utilisateur"""
    try:
        personne = request.user.personnevulnerable
        projet = get_object_or_404(ProjetVie, id=projet_id, personne=personne)
    except PersonneVulnerable.DoesNotExist:
        messages.error(request, "Accès non autorisé.")
        return redirect('profile')

    context = {
        'projet': projet,
        'personne': personne,
    }

    return render(request, 'formation/projet_detail.html', context)


@login_required
@user_passes_test(is_vulnerable_or_admin)
def parcours_detail(request, parcours_id):
    """Détail d'un parcours de formation pour l'utilisateur"""
    try:
        personne = request.user.personnevulnerable
        parcours = get_object_or_404(
            ParcoursFormation.objects.select_related('demande_formation__formation_souhaitee'),
            id=parcours_id,
            demande_formation__personne=personne
        )
    except PersonneVulnerable.DoesNotExist:
        messages.error(request, "Accès non autorisé.")
        return redirect('profile')

    # Récupérer les suivis de progression
    suivis = SuiviProgression.objects.filter(parcours=parcours).order_by('-date_suivi')

    context = {
        'parcours': parcours,
        'suivis': suivis,
        'personne': personne,
    }

    return render(request, 'formation/parcours_detail.html', context)


# ===== VUES ADMIN ADDITIONNELLES =====

@login_required
@user_passes_test(is_admin_or_mentor)
def admin_parcours_list(request):
    """Liste des parcours de formation pour l'administration"""
    parcours = ParcoursFormation.objects.select_related(
        'demande_formation__personne',
        'demande_formation__formation_souhaitee',
        'mentor_assigne'
    ).order_by('-date_creation')

    # Filtres
    statut_filter = request.GET.get('statut')
    if statut_filter:
        parcours = parcours.filter(statut_actuel=statut_filter)

    mentor_filter = request.GET.get('mentor')
    if mentor_filter:
        parcours = parcours.filter(mentor_assigne_id=mentor_filter)

    # Pagination
    paginator = Paginator(parcours, 20)
    page_number = request.GET.get('page')
    parcours_page = paginator.get_page(page_number)

    # Données pour les filtres
    from users.models import User
    mentors = User.objects.filter(
        Q(is_staff=True) | Q(is_superuser=True)
    ).order_by('username')

    statuts = ParcoursFormation.STATUT_PARCOURS_CHOICES

    context = {
        'parcours': parcours_page,
        'mentors': mentors,
        'statuts': statuts,
        'statut_filter': statut_filter,
        'mentor_filter': mentor_filter,
    }

    return render(request, 'formation/admin/parcours_list.html', context)


@login_required
@user_passes_test(is_admin_or_mentor)
def admin_parcours_detail(request, parcours_id):
    """Détail d'un parcours pour l'administration"""
    parcours = get_object_or_404(
        ParcoursFormation.objects.select_related(
            'demande_formation__personne',
            'demande_formation__formation_souhaitee',
            'projet_vie'
        ),
        id=parcours_id
    )

    if request.method == 'POST':
        form = ParcoursFormationForm(request.POST, instance=parcours)
        if form.is_valid():
            form.save()
            messages.success(request, "Parcours mis à jour avec succès.")
            return redirect('formation:admin_parcours_detail', parcours_id=parcours.id)
    else:
        form = ParcoursFormationForm(instance=parcours)

    # Récupérer les suivis
    suivis = SuiviProgression.objects.filter(parcours=parcours).order_by('-date_suivi')

    context = {
        'parcours': parcours,
        'form': form,
        'suivis': suivis,
    }

    return render(request, 'formation/admin/parcours_detail.html', context)


@login_required
@user_passes_test(is_admin_or_mentor)
def admin_parcours_suivi(request, parcours_id):
    """Ajouter un suivi de progression"""
    parcours = get_object_or_404(ParcoursFormation, id=parcours_id)

    if request.method == 'POST':
        form = EvaluationSuiviForm(request.POST)
        if form.is_valid():
            suivi = form.save(commit=False)
            suivi.parcours = parcours
            suivi.responsable = request.user
            suivi.save()

            # Mettre à jour la progression si nécessaire
            if form.cleaned_data['note_progression']:
                # Calculer le nouveau pourcentage basé sur les évaluations
                moyenne_notes = SuiviProgression.objects.filter(
                    parcours=parcours,
                    note_progression__isnull=False
                ).aggregate(avg_note=Avg('note_progression'))['avg_note']

                if moyenne_notes:
                    parcours.pourcentage_completion = min(100, (moyenne_notes / 10) * 100)
                    parcours.save()

            messages.success(request, "Suivi ajouté avec succès.")
            return redirect('formation:admin_parcours_detail', parcours_id=parcours.id)
    else:
        form = EvaluationSuiviForm()

    context = {
        'form': form,
        'parcours': parcours,
    }

    return render(request, 'formation/admin/parcours_suivi.html', context)


@login_required
@user_passes_test(is_admin_or_mentor)
def admin_projets_list(request):
    """Liste des projets de vie pour l'administration"""
    projets = ProjetVie.objects.select_related('personne').order_by('-date_creation')

    # Filtres
    statut_filter = request.GET.get('statut')
    if statut_filter:
        projets = projets.filter(statut=statut_filter)

    secteur_filter = request.GET.get('secteur')
    if secteur_filter:
        projets = projets.filter(secteur_activite__icontains=secteur_filter)

    # Pagination
    paginator = Paginator(projets, 20)
    page_number = request.GET.get('page')
    projets_page = paginator.get_page(page_number)

    context = {
        'projets': projets_page,
        'statut_filter': statut_filter,
        'secteur_filter': secteur_filter,
        'statuts': ProjetVie.STATUT_PROJET_CHOICES,
    }

    return render(request, 'formation/admin/projets_list.html', context)


@login_required
@user_passes_test(is_admin_or_mentor)
def admin_projet_detail(request, projet_id):
    """Détail d'un projet pour l'administration"""
    projet = get_object_or_404(ProjetVie.objects.select_related('personne'), id=projet_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'valider':
            projet.statut = 'validation'
            messages.success(request, "Projet validé.")
        elif action == 'financer':
            projet.statut = 'finance'
            messages.success(request, "Projet financé.")
        elif action == 'rejeter':
            projet.statut = 'abandonne'
            messages.warning(request, "Projet rejeté.")

        projet.save()
        return redirect('formation:admin_projet_detail', projet_id=projet.id)

    context = {
        'projet': projet,
    }

    return render(request, 'formation/admin/projet_detail.html', context)


# ===== MENTORING =====

@login_required
@user_passes_test(is_admin_or_mentor)
def mentoring_dashboard(request):
    """Dashboard pour les mentors"""
    # Parcours assignés au mentor
    mes_parcours = ParcoursFormation.objects.filter(
        mentor_assigne=request.user
    ).select_related(
        'demande_formation__personne',
        'demande_formation__formation_souhaitee'
    )

    # Statistiques
    stats = {
        'total_mentores': mes_parcours.count(),
        'en_cours': mes_parcours.filter(statut_actuel='en_cours').count(),
        'termines': mes_parcours.filter(statut_actuel__in=['forme', 'autonome']).count(),
        'moyenne_progression': mes_parcours.aggregate(
            avg=Avg('pourcentage_completion')
        )['avg'] or 0,
    }

    context = {
        'mes_parcours': mes_parcours,
        'stats': stats,
    }

    return render(request, 'formation/mentoring/dashboard.html', context)


@login_required
@user_passes_test(is_admin_or_mentor)
def mentoring_parcours_detail(request, parcours_id):
    """Détail d'un parcours pour le mentor"""
    parcours = get_object_or_404(
        ParcoursFormation.objects.select_related(
            'demande_formation__personne',
            'demande_formation__formation_souhaitee'
        ),
        id=parcours_id,
        mentor_assigne=request.user
    )

    suivis = SuiviProgression.objects.filter(parcours=parcours).order_by('-date_suivi')

    context = {
        'parcours': parcours,
        'suivis': suivis,
    }

    return render(request, 'formation/mentoring/parcours_detail.html', context)


@login_required
@user_passes_test(is_admin_or_mentor)
def mentoring_evaluation(request, parcours_id):
    """Évaluation par le mentor"""
    parcours = get_object_or_404(
        ParcoursFormation,
        id=parcours_id,
        mentor_assigne=request.user
    )

    if request.method == 'POST':
        form = EvaluationSuiviForm(request.POST)
        if form.is_valid():
            suivi = form.save(commit=False)
            suivi.parcours = parcours
            suivi.responsable = request.user
            suivi.save()

            messages.success(request, "Évaluation enregistrée avec succès.")
            return redirect('formation:mentoring_parcours_detail', parcours_id=parcours.id)
    else:
        form = EvaluationSuiviForm(initial={'type_suivi': 'mentoring'})

    context = {
        'form': form,
        'parcours': parcours,
    }

    return render(request, 'formation/mentoring/evaluation.html', context)


# ===== API ENDPOINTS ADDITIONNELS =====

@csrf_exempt
def api_analyser_projet(request, projet_id):
    """API pour analyser un projet spécifique"""
    if request.method == 'POST':
        result = analyser_projet_vie_sync(projet_id)
        return JsonResponse(result)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def api_dashboard_stats(request):
    """API pour les statistiques du dashboard"""
    stats = {
        'formations': {
            'total': Formation.objects.filter(est_active=True).count(),
            'populaires': list(
                Formation.objects.annotate(
                    nb_demandes=Count('demandes_formation')
                ).values('nom', 'nb_demandes').order_by('-nb_demandes')[:5]
            )
        },
        'demandes': {
            'total': DemandeFormation.objects.count(),
            'en_attente': DemandeFormation.objects.filter(statut='en_attente').count(),
            'acceptees': DemandeFormation.objects.filter(statut='acceptee').count(),
            'en_cours': DemandeFormation.objects.filter(statut='en_cours').count(),
            'terminees': DemandeFormation.objects.filter(statut='terminee').count(),
        },
        'parcours': {
            'actifs': ParcoursFormation.objects.exclude(statut_actuel='autonome').count(),
            'progression_moyenne': ParcoursFormation.objects.aggregate(
                avg=Avg('pourcentage_completion')
            )['avg'] or 0,
        },
        'projets': {
            'total': ProjetVie.objects.count(),
            'actifs': ProjetVie.objects.exclude(statut='abandonne').count(),
            'finances': ProjetVie.objects.filter(statut='finance').count(),
        }
    }

    return JsonResponse(stats)


@login_required
def api_formations_populaires(request):
    """API pour les formations les plus populaires"""
    formations = Formation.objects.annotate(
        nb_demandes=Count('demandes_formation')
    ).values(
        'nom', 'type_formation', 'nb_demandes'
    ).order_by('-nb_demandes')[:10]

    return JsonResponse({'formations': list(formations)})


@login_required
def api_evolution_demandes(request):
    """API pour l'évolution des demandes par mois"""
    demandes_par_mois = DemandeFormation.objects.annotate(
        mois=TruncMonth('date_demande')
    ).values('mois').annotate(
        count=Count('id')
    ).order_by('mois')

    data = [
        {
            'mois': item['mois'].strftime('%Y-%m'),
            'count': item['count']
        }
        for item in demandes_par_mois
    ]

    return JsonResponse({'evolution': data})


@login_required
def api_repartition_scores(request):
    """API pour la répartition des scores de formabilité"""
    scores = DemandeFormation.objects.filter(
        score_formabilite__isnull=False
    ).values_list('score_formabilite', flat=True)

    # Répartition par tranches
    tranches = {
        '0-25': 0,
        '26-50': 0,
        '51-75': 0,
        '76-100': 0
    }

    for score in scores:
        if score <= 25:
            tranches['0-25'] += 1
        elif score <= 50:
            tranches['26-50'] += 1
        elif score <= 75:
            tranches['51-75'] += 1
        else:
            tranches['76-100'] += 1

    return JsonResponse({'repartition': tranches})


@login_required
def api_recherche_formations(request):
    """API pour la recherche de formations"""
    query = request.GET.get('q', '')
    type_formation = request.GET.get('type', '')

    formations = Formation.objects.filter(est_active=True)

    if query:
        formations = formations.filter(
            Q(nom__icontains=query) |
            Q(description__icontains=query)
        )

    if type_formation:
        formations = formations.filter(type_formation=type_formation)

    data = [
        {
            'id': f.id,
            'nom': f.nom,
            'type': f.get_type_formation_display(),
            'duree': f.duree_semaines,
            'places_restantes': f.places_restantes()
        }
        for f in formations[:20]
    ]

    return JsonResponse({'formations': data})


@csrf_exempt
def api_accepter_demande(request, demande_id):
    """API pour accepter une demande"""
    if request.method == 'POST':
        try:
            demande = DemandeFormation.objects.get(id=demande_id)
            demande.statut = 'acceptee'
            demande.responsable_decision = request.user
            demande.date_decision = timezone.now()
            demande.save()

            # Créer le parcours
            parcours, created = ParcoursFormation.objects.get_or_create(
                demande_formation=demande
            )

            return JsonResponse({'success': True})
        except DemandeFormation.DoesNotExist:
            return JsonResponse({'error': 'Demande introuvable'}, status=404)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def api_refuser_demande(request, demande_id):
    """API pour refuser une demande"""
    if request.method == 'POST':
        try:
            demande = DemandeFormation.objects.get(id=demande_id)
            demande.statut = 'refusee'
            demande.responsable_decision = request.user
            demande.date_decision = timezone.now()
            demande.commentaire_decision = request.POST.get('commentaire', '')
            demande.save()

            return JsonResponse({'success': True})
        except DemandeFormation.DoesNotExist:
            return JsonResponse({'error': 'Demande introuvable'}, status=404)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def api_update_progression(request, parcours_id):
    """API pour mettre à jour la progression"""
    if request.method == 'POST':
        try:
            parcours = ParcoursFormation.objects.get(id=parcours_id)

            data = json.loads(request.body)
            parcours.pourcentage_completion = data.get('pourcentage', parcours.pourcentage_completion)
            parcours.statut_actuel = data.get('statut', parcours.statut_actuel)

            parcours.save()

            return JsonResponse({'success': True})
        except ParcoursFormation.DoesNotExist:
            return JsonResponse({'error': 'Parcours introuvable'}, status=404)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


# ===== EXPORT CSV =====

@login_required
@user_passes_test(is_admin_or_mentor)
def export_demandes_csv(request):
    """Export des demandes en CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="demandes_formation.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Demandeur', 'Formation', 'Motivation', 'Statut',
        'Score Formabilité', 'Date Demande', 'Date Analyse'
    ])

    demandes = DemandeFormation.objects.select_related(
        'personne', 'formation_souhaitee'
    ).all()

    for demande in demandes:
        writer.writerow([
            str(demande.id),
            demande.personne.get_full_name(),
            demande.formation_souhaitee.nom,
            demande.get_motivation_principale_display(),
            demande.get_statut_display(),
            demande.score_formabilite or '',
            demande.date_demande.strftime('%d/%m/%Y'),
            demande.date_analyse.strftime('%d/%m/%Y') if demande.date_analyse else ''
        ])

    return response


@login_required
@user_passes_test(is_admin_or_mentor)
def export_formations_csv(request):
    """Export des formations en CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="formations.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Nom', 'Type', 'Durée (semaines)', 'Niveau Requis',
        'Âge Min', 'Âge Max', 'Places Disponibles', 'Coût',
        'Nb Demandes', 'Active'
    ])

    formations = Formation.objects.annotate(
        nb_demandes=Count('demandes_formation')
    ).all()

    for formation in formations:
        writer.writerow([
            formation.id,
            formation.nom,
            formation.get_type_formation_display(),
            formation.duree_semaines,
            formation.get_niveau_requis_display(),
            formation.age_min,
            formation.age_max,
            formation.places_disponibles,
            formation.cout_formation,
            formation.nb_demandes,
            'Oui' if formation.est_active else 'Non'
        ])

    return response


@login_required
@user_passes_test(is_admin_or_mentor)
def export_parcours_csv(request):
    """Export des parcours en CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="parcours_formation.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Participant', 'Formation', 'Statut', 'Progression (%)',
        'Date Début', 'Date Fin', 'Note', 'Mentor'
    ])

    parcours = ParcoursFormation.objects.select_related(
        'demande_formation__personne',
        'demande_formation__formation_souhaitee',
        'mentor_assigne'
    ).all()

    for p in parcours:
        writer.writerow([
            str(p.id),
            p.demande_formation.personne.get_full_name(),
            p.demande_formation.formation_souhaitee.nom,
            p.get_statut_actuel_display(),
            p.pourcentage_completion,
            p.date_debut_formation.strftime('%d/%m/%Y') if p.date_debut_formation else '',
            p.date_fin_formation.strftime('%d/%m/%Y') if p.date_fin_formation else '',
            p.note_formation or '',
            p.mentor_assigne.username if p.mentor_assigne else ''
        ])

    return response


# ===== RAPPORTS =====

@login_required
@user_passes_test(is_admin_or_mentor)
def rapports_formation(request):
    """Page des rapports de formation"""
    # Statistiques générales
    total_formations = Formation.objects.filter(est_active=True).count()
    total_demandes = DemandeFormation.objects.count()
    taux_acceptation = 0

    if total_demandes > 0:
        acceptees = DemandeFormation.objects.filter(statut='acceptee').count()
        taux_acceptation = (acceptees / total_demandes) * 100

    # Formations par type
    formations_par_type = Formation.objects.values(
        'type_formation'
    ).annotate(
        count=Count('id')
    ).order_by('-count')

    # Évolution mensuelle - CORRECTION ICI
    from datetime import timedelta
    from django.utils import timezone

    # Calculer la date d'il y a 12 mois
    twelve_months_ago = timezone.now() - timedelta(days=365)

    evolution_mensuelle = DemandeFormation.objects.filter(
        date_demande__gte=twelve_months_ago
    ).annotate(
        mois=TruncMonth('date_demande')
    ).values('mois').annotate(
        count=Count('id')
    ).order_by('mois')

    context = {
        'total_formations': total_formations,
        'total_demandes': total_demandes,
        'taux_acceptation': taux_acceptation,
        'formations_par_type': formations_par_type,
        'evolution_mensuelle': evolution_mensuelle,
    }

    return render(request, 'formation/admin/rapports.html', context)

@login_required
def api_formation_notifications(request):
    """API pour les notifications du module formation"""
    notifications = []

    if request.user.is_superuser or request.user.is_staff:
        # Demandes en attente d'analyse
        demandes_attente = DemandeFormation.objects.filter(
            statut='en_attente'
        ).count()

        if demandes_attente > 0:
            notifications.append({
                'type': 'warning',
                'message': f"{demandes_attente} demande(s) en attente d'analyse",
                'url': '/formation/admin/demandes/?statut=en_attente'
            })

        # Parcours nécessitant un suivi
        parcours_suivi = ParcoursFormation.objects.filter(
            statut_actuel='en_cours',
            suivis__date_suivi__lt=timezone.now() - timedelta(days=30)
        ).count()

        if parcours_suivi > 0:
            notifications.append({
                'type': 'info',
                'message': f"{parcours_suivi} parcours nécessitent un suivi",
                'url': '/formation/admin/parcours/'
            })

    return JsonResponse({'notifications': notifications})


# ===== VUES MANQUANTES À AJOUTER À LA FIN DU FICHIER views.py =====

@login_required
@user_passes_test(is_admin_or_mentor)
def rapport_formation_detail(request, formation_id):
    """Rapport détaillé d'une formation spécifique"""
    formation = get_object_or_404(Formation, id=formation_id)

    # Statistiques de la formation
    demandes = DemandeFormation.objects.filter(formation_souhaitee=formation)

    stats = {
        'total_demandes': demandes.count(),
        'demandes_acceptees': demandes.filter(statut='acceptee').count(),
        'demandes_refusees': demandes.filter(statut='refusee').count(),
        'demandes_en_attente': demandes.filter(statut='en_attente').count(),
        'score_moyen': demandes.filter(score_formabilite__isnull=False).aggregate(
            avg=Avg('score_formabilite')
        )['avg'] or 0,
        'taux_reussite': 0
    }

    # Calcul du taux de réussite
    if stats['total_demandes'] > 0:
        stats['taux_reussite'] = (stats['demandes_acceptees'] / stats['total_demandes']) * 100

    # Parcours de formation liés
    parcours = ParcoursFormation.objects.filter(
        demande_formation__formation_souhaitee=formation
    ).select_related('demande_formation__personne')

    # Évolution des demandes par mois - CORRECTION ICI
    from datetime import timedelta
    from django.utils import timezone

    # Calculer la date d'il y a 12 mois
    twelve_months_ago = timezone.now() - timedelta(days=365)

    evolution_demandes = demandes.filter(
        date_demande__gte=twelve_months_ago
    ).annotate(
        mois=TruncMonth('date_demande')
    ).values('mois').annotate(
        count=Count('id')
    ).order_by('mois')

    # Répartition des scores de formabilité
    scores = demandes.filter(score_formabilite__isnull=False).values_list('score_formabilite', flat=True)
    repartition_scores = {
        'excellent': len([s for s in scores if s >= 85]),
        'bon': len([s for s in scores if 70 <= s < 85]),
        'moyen': len([s for s in scores if 50 <= s < 70]),
        'faible': len([s for s in scores if s < 50])
    }

    # Profil des candidats
    profils = {
        'age_moyen': demandes.aggregate(
            avg=Avg('personne__age')
        )['avg'] or 0,
        'repartition_genre': demandes.values('personne__genre').annotate(
            count=Count('id')
        ),
        'niveaux_education': demandes.values('personne__niveau_education').annotate(
            count=Count('id')
        )
    }

    context = {
        'formation': formation,
        'stats': stats,
        'parcours': parcours,
        'evolution_demandes': evolution_demandes,
        'repartition_scores': repartition_scores,
        'profils': profils,
        'demandes_recentes': demandes.order_by('-date_demande')[:10]
    }

    return render(request, 'formation/admin/rapport_formation_detail.html', context)


@login_required
@user_passes_test(is_admin_or_mentor)
def export_rapport(request, type_rapport):
    """Export de différents types de rapports"""

    if type_rapport == 'demandes':
        return export_demandes_csv(request)
    elif type_rapport == 'formations':
        return export_formations_csv(request)
    elif type_rapport == 'parcours':
        return export_parcours_csv(request)
    elif type_rapport == 'analyses_ia':
        return export_analyses_ia_csv(request)
    elif type_rapport == 'statistiques':
        return export_statistiques_csv(request)
    else:
        messages.error(request, "Type de rapport non reconnu.")
        return redirect('formation:admin_dashboard')


@login_required
@user_passes_test(is_admin_or_mentor)
def export_analyses_ia_csv(request):
    """Export des analyses IA en CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="analyses_ia_formation.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID Demande', 'Demandeur', 'Formation', 'Score Formabilité',
        'Décision Recommandée', 'Date Analyse', 'Analyse Détaillée',
        'Recommandations', 'Statut Final'
    ])

    demandes = DemandeFormation.objects.filter(
        score_formabilite__isnull=False
    ).select_related('personne', 'formation_souhaitee').order_by('-date_analyse')

    for demande in demandes:
        # Extraire la décision recommandée des critères d'évaluation
        decision_recommandee = ""
        if demande.criteres_evaluacion:
            try:
                import json
                criteres = json.loads(demande.criteres_evaluacion) if isinstance(demande.criteres_evaluacion,
                                                                                 str) else demande.criteres_evaluacion
                decision_recommandee = criteres.get('decision_recommandee', '')
            except:
                decision_recommandee = "Non disponible"

        writer.writerow([
            demande.id,
            demande.personne.get_full_name(),
            demande.formation_souhaitee.nom,
            demande.score_formabilite,
            decision_recommandee,
            demande.date_analyse.strftime('%d/%m/%Y %H:%M') if demande.date_analyse else '',
            demande.analyse_llm[:200] + '...' if len(demande.analyse_llm) > 200 else demande.analyse_llm,
            demande.recommandations_llm[:200] + '...' if len(
                demande.recommandations_llm) > 200 else demande.recommandations_llm,
            demande.get_statut_display()
        ])

    return response


@login_required
@user_passes_test(is_admin_or_mentor)
def export_statistiques_csv(request):
    """Export des statistiques générales en CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="statistiques_formation.csv"'

    writer = csv.writer(response)

    # En-têtes
    writer.writerow(['STATISTIQUES GÉNÉRALES - MODULE FORMATION'])
    writer.writerow([])

    # Statistiques formations
    writer.writerow(['FORMATIONS'])
    writer.writerow(['Nom Formation', 'Type', 'Places Totales', 'Places Restantes', 'Nb Demandes', 'Taux Occupation %'])

    formations = Formation.objects.annotate(
        nb_demandes=Count('demandes_formation')
    ).filter(est_active=True)

    for formation in formations:
        places_occupees = formation.places_disponibles - formation.places_restantes()
        taux_occupation = (
                    places_occupees / formation.places_disponibles * 100) if formation.places_disponibles > 0 else 0

        writer.writerow([
            formation.nom,
            formation.get_type_formation_display(),
            formation.places_disponibles,
            formation.places_restantes(),
            formation.nb_demandes,
            f"{taux_occupation:.1f}%"
        ])

    writer.writerow([])

    # Statistiques par statut
    writer.writerow(['RÉPARTITION DES DEMANDES PAR STATUT'])
    writer.writerow(['Statut', 'Nombre', 'Pourcentage'])

    total_demandes = DemandeFormation.objects.count()
    for statut, label in DemandeFormation.STATUT_CHOICES:
        count = DemandeFormation.objects.filter(statut=statut).count()
        pourcentage = (count / total_demandes * 100) if total_demandes > 0 else 0
        writer.writerow([label, count, f"{pourcentage:.1f}%"])

    return response


@login_required
def api_filtrer_demandes(request):
    """API pour filtrer les demandes avec AJAX"""

    # Paramètres de filtrage
    statut = request.GET.get('statut', '')
    formation_id = request.GET.get('formation', '')
    score_min = request.GET.get('score_min', '')
    score_max = request.GET.get('score_max', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')

    # Requête de base
    demandes = DemandeFormation.objects.select_related(
        'personne', 'formation_souhaitee'
    ).all()

    # Application des filtres
    if statut:
        demandes = demandes.filter(statut=statut)

    if formation_id:
        demandes = demandes.filter(formation_souhaitee_id=formation_id)

    if score_min:
        try:
            demandes = demandes.filter(score_formabilite__gte=int(score_min))
        except ValueError:
            pass

    if score_max:
        try:
            demandes = demandes.filter(score_formabilite__lte=int(score_max))
        except ValueError:
            pass

    if date_debut:
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
            demandes = demandes.filter(date_demande__gte=date_obj)
        except ValueError:
            pass

    if date_fin:
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
            demandes = demandes.filter(date_demande__lte=date_obj)
        except ValueError:
            pass

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(demandes.order_by('-date_demande'), 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Préparation des données
    data = {
        'demandes': [],
        'pagination': {
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'number': page_obj.number,
            'num_pages': paginator.num_pages,
            'count': paginator.count
        }
    }

    for demande in page_obj:
        data['demandes'].append({
            'id': demande.id,
            'nom_complet': demande.personne.get_full_name(),
            'formation': demande.formation_souhaitee.nom,
            'statut': demande.get_statut_display(),
            'statut_code': demande.statut,
            'score_formabilite': demande.score_formabilite,
            'date_demande': demande.date_demande.strftime('%d/%m/%Y'),
            'date_analyse': demande.date_analyse.strftime('%d/%m/%Y %H:%M') if demande.date_analyse else None,
            'url_detail': f'/formation/admin/demandes/{demande.id}/'
        })

    return JsonResponse(data)


@login_required
@user_passes_test(is_vulnerable_or_admin)
def analyse_ia_detail(request, demande_id):
    """Vue détaillée de l'analyse IA d'une demande"""
    try:
        # Vérifier les permissions
        if request.user.is_superuser or request.user.is_staff:
            # Admin peut voir toutes les demandes
            demande = get_object_or_404(DemandeFormation, id=demande_id)
        else:
            # Utilisateur normal ne peut voir que ses propres demandes
            personne = request.user.personnevulnerable
            demande = get_object_or_404(
                DemandeFormation,
                id=demande_id,
                personne=personne
            )
    except PersonneVulnerable.DoesNotExist:
        messages.error(request, "Accès non autorisé.")
        return redirect('formation:formations_list')

    # Traitement des critères d'évaluation si disponibles
    criteres_scores = {}
    decision_details = {}

    if demande.criteres_evaluacion:
        try:
            import json
            if isinstance(demande.criteres_evaluacion, str):
                criteres_data = json.loads(demande.criteres_evaluacion)
            else:
                criteres_data = demande.criteres_evaluacion

            criteres_scores = criteres_data.get('criteres_scores', {})
            decision_details = {
                'decision_recommandee': criteres_data.get('decision_recommandee', ''),
                'conditions': criteres_data.get('conditions', '')
            }
        except (json.JSONDecodeError, TypeError):
            pass

    # Calcul du pourcentage par critère
    criteres_pourcentages = {}
    criteres_max = {
        'compatibilite': 20,
        'motivation': 25,
        'capacite_apprentissage': 20,
        'faisabilite_projet': 20,
        'contexte_socio': 15
    }

    for critere, score in criteres_scores.items():
        if critere in criteres_max:
            max_score = criteres_max[critere]
            pourcentage = (score / max_score * 100) if max_score > 0 else 0
            criteres_pourcentages[critere] = {
                'score': score,
                'max_score': max_score,
                'pourcentage': pourcentage
            }

    context = {
        'demande': demande,
        'criteres_scores': criteres_scores,
        'criteres_pourcentages': criteres_pourcentages,
        'decision_details': decision_details,
        'is_admin': request.user.is_superuser or request.user.is_staff
    }

    return render(request, 'formation/analyse_ia_detail.html', context)


@login_required
@user_passes_test(is_admin_or_mentor)
def reanalyser_demande(request, demande_id):
    """Relancer l'analyse IA d'une demande"""
    demande = get_object_or_404(DemandeFormation, id=demande_id)

    if request.method == 'POST':
        try:
            # Relancer l'analyse
            result = analyser_demande_formation_sync(demande_id)

            if result['success']:
                messages.success(
                    request,
                    f"Analyse IA relancée avec succès. Nouveau score: {result['score']}/100"
                )
            else:
                messages.error(
                    request,
                    f"Erreur lors de la réanalyse: {result.get('error', 'Erreur inconnue')}"
                )

        except Exception as e:
            messages.error(request, f"Erreur technique lors de la réanalyse: {str(e)}")

    return redirect('formation:analyse_ia_detail', demande_id=demande_id)


@login_required
@user_passes_test(is_admin_or_mentor)
def analyses_ia_dashboard(request):
    """Dashboard des analyses IA"""

    # Statistiques générales
    total_analyses = DemandeFormation.objects.filter(score_formabilite__isnull=False).count()
    score_moyen = DemandeFormation.objects.filter(
        score_formabilite__isnull=False
    ).aggregate(avg=Avg('score_formabilite'))['avg'] or 0

    # Répartition des scores
    scores = DemandeFormation.objects.filter(
        score_formabilite__isnull=False
    ).values_list('score_formabilite', flat=True)

    repartition = {
        'excellent': len([s for s in scores if s >= 85]),
        'bon': len([s for s in scores if 70 <= s < 85]),
        'moyen': len([s for s in scores if 50 <= s < 70]),
        'faible': len([s for s in scores if s < 50])
    }

    # Analyses récentes
    analyses_recentes = DemandeFormation.objects.filter(
        score_formabilite__isnull=False
    ).select_related('personne', 'formation_souhaitee').order_by('-date_analyse')[:10]

    # Formations avec les meilleurs scores moyens
    formations_top = Formation.objects.annotate(
        score_moyen=Avg('demandes_formation__score_formabilite'),
        nb_analyses=Count('demandes_formation', filter=Q(demandes_formation__score_formabilite__isnull=False))
    ).filter(nb_analyses__gt=0).order_by('-score_moyen')[:5]

    # Évolution mensuelle des scores - CORRECTION ICI
    from datetime import datetime, timedelta
    from django.utils import timezone

    # Calculer la date d'il y a 6 mois
    six_months_ago = timezone.now() - timedelta(days=180)

    evolution_scores = DemandeFormation.objects.filter(
        score_formabilite__isnull=False,
        date_analyse__gte=six_months_ago  # Filtrer les 6 derniers mois
    ).annotate(
        mois=TruncMonth('date_analyse')
    ).values('mois').annotate(
        score_moyen=Avg('score_formabilite'),
        count=Count('id')
    ).order_by('mois')  # Ordre croissant normal

    context = {
        'total_analyses': total_analyses,
        'score_moyen': score_moyen,
        'repartition': repartition,
        'analyses_recentes': analyses_recentes,
        'formations_top': formations_top,
        'evolution_scores': evolution_scores
    }

    return render(request, 'formation/admin/analyses_ia_dashboard.html', context)


@login_required
def mes_analyses_ia(request):
    """Analyses IA des demandes de l'utilisateur"""
    try:
        personne = request.user.personnevulnerable
    except PersonneVulnerable.DoesNotExist:
        messages.error(request, "Vous devez avoir un profil de personne vulnérable.")
        return redirect('profile')

    # Demandes avec analyse IA
    demandes_analysees = DemandeFormation.objects.filter(
        personne=personne,
        score_formabilite__isnull=False
    ).select_related('formation_souhaitee').order_by('-date_analyse')

    # Statistiques personnelles
    if demandes_analysees.exists():
        score_moyen_personnel = demandes_analysees.aggregate(
            avg=Avg('score_formabilite')
        )['avg']
        # CORRECTION ICI - utiliser Max au lieu de Count
        meilleur_score = demandes_analysees.aggregate(
            max=Max('score_formabilite')  # Changé Count en Max
        )['max']
    else:
        score_moyen_personnel = 0
        meilleur_score = 0

    context = {
        'demandes_analysees': demandes_analysees,
        'score_moyen_personnel': score_moyen_personnel,
        'meilleur_score': meilleur_score,
        'personne': personne
    }

    return render(request, 'formation/mes_analyses_ia.html', context)


@login_required
@user_passes_test(is_admin_or_mentor)
def admin_lancer_analyses_lot(request):
    """Vue pour lancer des analyses IA en lot"""

    if request.method == 'POST':
        # Récupérer les IDs des demandes sélectionnées
        demandes_ids = request.POST.getlist('demandes_selected')

        if not demandes_ids:
            messages.error(request, "Aucune demande sélectionnée.")
            return redirect('formation:admin_lancer_analyses_lot')

        # Statistiques de traitement
        total_demandes = len(demandes_ids)
        analyses_reussies = 0
        analyses_echouees = 0

        # Traiter chaque demande
        for demande_id in demandes_ids:
            try:
                result = analyser_demande_formation_sync(demande_id)
                if result['success']:
                    analyses_reussies += 1
                else:
                    analyses_echouees += 1
            except Exception as e:
                analyses_echouees += 1

        # Messages de résultat
        if analyses_reussies > 0:
            messages.success(
                request,
                f"✅ {analyses_reussies}/{total_demandes} analyses réussies"
            )

        if analyses_echouees > 0:
            messages.warning(
                request,
                f"⚠️ {analyses_echouees}/{total_demandes} analyses échouées"
            )

        return redirect('formation:admin_demandes_list')

    # GET: Afficher les demandes disponibles pour analyse
    # Demandes sans analyse ou avec analyse ancienne
    demandes_sans_analyse = DemandeFormation.objects.filter(
        score_formabilite__isnull=True,
        statut='en_attente'
    ).select_related('personne', 'formation_souhaitee')

    # Demandes avec analyse ancienne (+ de 30 jours)
    from datetime import timedelta
    ancienne_date = timezone.now() - timedelta(days=30)
    demandes_analyse_ancienne = DemandeFormation.objects.filter(
        score_formabilite__isnull=False,
        date_analyse__lt=ancienne_date
    ).select_related('personne', 'formation_souhaitee')

    context = {
        'demandes_sans_analyse': demandes_sans_analyse,
        'demandes_analyse_ancienne': demandes_analyse_ancienne,
    }

    return render(request, 'formation/admin/lancer_analyses_lot.html', context)


@login_required
@user_passes_test(is_admin_or_mentor)
def admin_analyser_toutes_demandes(request):
    """Analyser TOUTES les demandes en attente d'un coup"""

    if request.method == 'POST':
        # Confirmation requise
        confirmation = request.POST.get('confirmation')
        if confirmation != 'CONFIRME':
            messages.error(request, "Confirmation requise pour cette action.")
            return redirect('formation:admin_dashboard')

        # Récupérer toutes les demandes sans analyse
        demandes_a_analyser = DemandeFormation.objects.filter(
            score_formabilite__isnull=True,
            statut='en_attente'
        )

        total = demandes_a_analyser.count()
        if total == 0:
            messages.info(request, "Aucune demande en attente d'analyse.")
            return redirect('formation:admin_dashboard')

        # Traitement en lot
        reussies = 0
        echouees = 0

        for demande in demandes_a_analyser:
            try:
                result = analyser_demande_formation_sync(demande.id)
                if result['success']:
                    reussies += 1
                else:
                    echouees += 1
            except Exception:
                echouees += 1

        messages.success(
            request,
            f"🧠 Analyse en lot terminée : {reussies}/{total} réussies, {echouees} échouées"
        )

        return redirect('formation:admin_dashboard')

    # GET: Page de confirmation
    demandes_count = DemandeFormation.objects.filter(
        score_formabilite__isnull=True,
        statut='en_attente'
    ).count()

    context = {
        'demandes_count': demandes_count,
    }

    return render(request, 'formation/admin/confirmer_analyse_lot.html', context)


@login_required
@user_passes_test(is_admin_or_mentor)
def admin_configuration_ia(request):
    """Configuration des paramètres d'analyse IA"""

    if request.method == 'POST':
        # Sauvegarder les paramètres (vous pouvez utiliser un modèle Configuration)
        auto_analyse = request.POST.get('auto_analyse') == 'on'
        seuil_acceptation = int(request.POST.get('seuil_acceptation', 70))

        # Ici vous pouvez sauvegarder dans un modèle ou dans les settings
        # Pour l'exemple, on utilise la session
        request.session['ia_config'] = {
            'auto_analyse': auto_analyse,
            'seuil_acceptation': seuil_acceptation,
        }

        messages.success(request, "Configuration IA mise à jour.")
        return redirect('formation:admin_configuration_ia')

    # GET: Afficher la configuration actuelle
    config = request.session.get('ia_config', {
        'auto_analyse': True,
        'seuil_acceptation': 70,
    })

    context = {
        'config': config,
    }

    return render(request, 'formation/admin/configuration_ia.html', context)


@login_required
@user_passes_test(is_admin_or_mentor)
def admin_historique_analyses(request):
    """Historique complet des analyses IA avec filtres"""

    # Toutes les demandes analysées
    analyses = DemandeFormation.objects.filter(
        score_formabilite__isnull=False
    ).select_related('personne', 'formation_souhaitee', 'responsable_decision')

    # Filtres
    score_min = request.GET.get('score_min')
    score_max = request.GET.get('score_max')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    formation_id = request.GET.get('formation')

    if score_min:
        analyses = analyses.filter(score_formabilite__gte=score_min)
    if score_max:
        analyses = analyses.filter(score_formabilite__lte=score_max)
    if date_debut:
        analyses = analyses.filter(date_analyse__gte=date_debut)
    if date_fin:
        analyses = analyses.filter(date_analyse__lte=date_fin)
    if formation_id:
        analyses = analyses.filter(formation_souhaitee_id=formation_id)

    # Pagination
    paginator = Paginator(analyses.order_by('-date_analyse'), 25)
    page_number = request.GET.get('page')
    analyses_page = paginator.get_page(page_number)

    # Statistiques rapides
    stats = {
        'total': analyses.count(),
        'score_moyen': analyses.aggregate(avg=Avg('score_formabilite'))['avg'] or 0,
        'acceptees_auto': analyses.filter(
            statut='acceptee',
            score_formabilite__gte=70
        ).count(),
    }

    context = {
        'analyses': analyses_page,
        'stats': stats,
        'formations': Formation.objects.filter(est_active=True),
        'filters': {
            'score_min': score_min,
            'score_max': score_max,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'formation_id': formation_id,
        }
    }

    return render(request, 'formation/admin/historique_analyses.html', context)


@csrf_exempt
@login_required
@user_passes_test(is_admin_or_mentor)
def api_lancer_analyse_ajax(request, demande_id):
    """API AJAX pour lancer une analyse depuis l'interface admin"""

    if request.method == 'POST':
        try:
            demande = DemandeFormation.objects.get(id=demande_id)

            # Vérifier si une analyse existe déjà
            if demande.score_formabilite:
                force_reanalyse = request.POST.get('force', False)
                if not force_reanalyse:
                    return JsonResponse({
                        'success': False,
                        'error': 'Analyse déjà existante. Utilisez force=true pour forcer.',
                        'existing_score': demande.score_formabilite
                    })

            # Lancer l'analyse
            result = analyser_demande_formation_sync(demande_id)

            if result['success']:
                # Recharger la demande pour récupérer les nouvelles données
                demande.refresh_from_db()

                return JsonResponse({
                    'success': True,
                    'score': demande.score_formabilite,
                    'statut': demande.get_statut_display(),
                    'date_analyse': demande.date_analyse.strftime('%d/%m/%Y %H:%M'),
                    'message': f'Analyse terminée. Score: {demande.score_formabilite}/100'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Erreur inconnue')
                })

        except DemandeFormation.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Demande introuvable'
            }, status=404)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur technique: {str(e)}'
            }, status=500)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
@user_passes_test(is_admin_or_mentor)
def admin_test_ia_connection(request):
    """Tester la connexion avec l'IA (Ollama)"""

    try:
        # Test simple avec un prompt basique
        test_messages = [
            SystemMessage(content="Tu es un assistant de test."),
            HumanMessage(content="Réponds simplement 'OK' si tu reçois ce message.")
        ]

        response = llm(test_messages)

        return JsonResponse({
            'success': True,
            'message': 'Connexion IA fonctionnelle',
            'response': response.content[:100] + '...' if len(response.content) > 100 else response.content,
            'model': 'mistral (Ollama)'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur de connexion IA: {str(e)}',
            'solution': 'Vérifiez que Ollama est démarré avec le modèle Mistral'
        }, status=500)