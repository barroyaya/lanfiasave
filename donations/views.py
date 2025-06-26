# donations/views.py
"""
Views for managing donations to vulnerable people.
Includes both web views and API endpoints.
"""

# Standard library imports
import json
import random
import traceback
from decimal import Decimal

# Django imports
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db import models, transaction
from django.db.models import Count, Case, When, IntegerField, Sum, Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

# Django REST Framework imports
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response

# Local imports
from .forms import DonationForm
from .models import Don, PersonneVulnerable
from .serializers import DonSerializer
from notifications.models import Notification
from users.models import PersonneVulnerable
from users.serializers import PersonneVulnerableSerializer


# =====================================================
# Web Views (Traditional Django Views)
# =====================================================

@login_required
def donation_list(request):
    """Display list of vulnerable people eligible for donations."""
    personnes = PersonneVulnerable.objects.filter(
        est_vulnerable=True,
        validated_by_admin=True
    )
    return render(request, 'donations/donation_list.html', {'personnes': personnes})


# Remplacer la fonction donation_view et ses fonctions helpers dans views.py

@login_required
def donation_view(request):
    if request.method == 'POST':
        print(">>> Requête POST reçue")
        form = DonationForm(request.POST)
        print(">>> Form valid ?", form.is_valid())
        print(">>> POST reçu :", request.POST)
        print(">>> Requête POST reçue")
        form = DonationForm(request.POST)
        print(">>> Form valid ?", form.is_valid())
        print(">>> POST reçu :", request.POST)

        if not form.is_valid():
            print(">>> Erreurs du formulaire :", form.errors)
        form = DonationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    don = _create_donation(request.user, form)
                    _associate_vulnerable_people(don, form)
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({"success": True, "message": "Don enregistré"})
                messages.success(request, "Votre don a été enregistré...")
                return redirect('profile')
            except ValueError as e:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({"success": False, "error": str(e)}, status=400)
                messages.error(request, str(e))
                return redirect('donation_view')
            except Exception as e:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({"success": False, "error": "Erreur serveur"}, status=500)
                messages.error(request, "Une erreur est survenue...")
                return redirect('donation_view')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"success": False, "errors": form.errors}, status=400)
    else:
        entite = request.GET.get('entite', None)
        form = DonationForm(entite=entite)

    return render(request, 'donations/donation_form.html', {'form': form})


def _create_donation(user, form):
    """Create donation object from form data."""
    montant_str = form.cleaned_data['montant']

    try:
        montant = Decimal(montant_str)
        if montant <= 0:
            raise ValueError("Le montant doit être supérieur à zéro.")
    except (ValueError, TypeError) as e:
        raise ValueError("Montant invalide.")

    # Créer le don avec est_valide=False et est_reparti=False
    don = Don.objects.create(
        donateur=user,
        entite_vulnerable=form.cleaned_data['entite_vulnerable'],
        provenance=form.cleaned_data['provenance'],
        description=form.cleaned_data.get('description', ''),
        montant=montant,
        est_valide=False,  # Le don n'est pas encore validé
        est_reparti=False,  # Le don n'est pas encore réparti
        # nombre_personnes=form.cleaned_data.get('nombre_personnes', 0)
    )

    print(f"Don créé: ID={don.id}, Montant={don.montant}, Donateur={don.donateur.username}")
    return don


def _associate_vulnerable_people(don, form):
    """Associate vulnerable people to the donation without distributing money."""
    personne_vulnerable = form.cleaned_data.get('personne_vulnerable', [])

    if personne_vulnerable:
        # Le donateur a sélectionné des personnes spécifiques
        for personne in personne_vulnerable:
            don.personne_vulnerable.add(personne)
            print(f"Personne associée au don: {personne.user.username if personne.user else 'Sans utilisateur'}")

        don.nombre_personnes = len(personne_vulnerable)
    else:
        # Pas de personnes spécifiques sélectionnées
        # On n'associe pas automatiquement toutes les personnes de l'entité
        # Cela sera fait lors de la validation par l'admin si nécessaire
        print(f"Aucune personne spécifique sélectionnée pour le don {don.id}")

        # On peut stocker le nombre estimé de personnes de l'entité
        personnes_count = PersonneVulnerable.objects.filter(
            entite=don.entite_vulnerable,
            est_vulnerable=True,
            validated_by_admin=True
        ).count()

        don.nombre_personnes = personnes_count if personnes_count > 0 else 1

    don.save()
    print(f"Don sauvegardé avec {don.personne_vulnerable.count()} personne(s) associée(s)")


def _distribute_donation_amount(don, form):
    """Distribute donation amount among vulnerable people."""
    personne_vulnerable = form.cleaned_data['personne_vulnerable']

    if personne_vulnerable:
        # Donor selected specific people
        montant_par_personne = don.montant / len(personne_vulnerable)
        for personne in personne_vulnerable:
            don.personne_vulnerable.add(personne)
            personne.montant_recu += montant_par_personne
            personne.save()
    else:
        # Distribute among all vulnerable people in the entity
        personnes = PersonneVulnerable.objects.filter(
            entite=don.entite_vulnerable,
            est_vulnerable=True,
            validated_by_admin=True
        )
        if personnes.exists():
            montant_par_personne = don.montant / personnes.count()
            for personne in personnes:
                don.personne_vulnerable.add(personne)
                personne.montant_recu += montant_par_personne
                personne.save()

    don.save()


@staff_member_required
def liste_dons_attente(request):
    """Display pending donations for admin validation."""
    dons_en_attente = Don.objects.filter(est_reparti=False).select_related('donateur')
    return render(request, 'donations/liste_dons_attente.html', {'dons': dons_en_attente})


@staff_member_required
def repartir_don_admin(request, don_id):
    """Admin action to validate and distribute a donation."""
    don = get_object_or_404(Don, pk=don_id)

    if not don.est_valide:
        with transaction.atomic():
            don.est_valide = True
            don.est_reparti = True
            don.save()

            # Process each vulnerable person
            for personne in don.personne_vulnerable.all():
                personne.montant_recu = (personne.montant_recu or Decimal('0.00')) + don.montant

                if personne.montant_recu >= Decimal('200000.00'):
                    personne.est_vulnerable = False
                    message = f"{personne.user.username} n'est plus considéré comme vulnérable."
                else:
                    message = f"Le don de {don.montant} € a été réparti à {personne.user.username}."

                personne.save()

                # Notify vulnerable person
                Notification.objects.create(
                    user=personne.user,
                    message=f"Vous avez reçu un don de {don.montant} € de {don.donateur.username}. {message}"
                )

            # Notify donor
            Notification.objects.create(
                user=don.donateur,
                message=f"Votre don de {don.montant} € a été validé et réparti avec succès."
            )

            messages.success(request, f"Le don de {don.montant} € a été validé et réparti.")
    else:
        messages.warning(request, "Ce don a déjà été validé.")

    return redirect('liste_dons_attente')


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from donations.models import Don

@login_required
def historique_dons(request):
    """Affichage de l'historique des dons pour l'utilisateur connecté."""
    dons_en_attente = Don.objects.filter(
        donateur=request.user,
        est_reparti=False
    ).order_by('-date_don')

    dons_repartis = Don.objects.filter(
        donateur=request.user,
        est_reparti=True
    ).order_by('-date_don')

    # Total des dons
    total_dons = dons_en_attente.count() + dons_repartis.count()

    # Total du montant donné (tous les dons)
    total_montant = sum(don.montant for don in list(dons_en_attente) + list(dons_repartis))

    # Score d'impact (exemple : % de dons répartis * 100)
    if total_dons > 0:
        impact_score = round((dons_repartis.count() / total_dons) * 100, 2)
    else:
        impact_score = 0

    context = {
        'dons_en_attente': dons_en_attente,
        'dons_repartis': dons_repartis,
        'total_dons': total_dons,
        'total_montant': total_montant,
        'impact_score': impact_score,
    }

    return render(request, 'donations/historique_dons.html', context)


@login_required
def voir_retirer_dons(request):
    """Display donations available for withdrawal by vulnerable person."""
    try:
        personne = request.user.personnevulnerable
    except PersonneVulnerable.DoesNotExist:
        return redirect('home')

    dons_a_retirer = Don.objects.filter(
        personne_vulnerable=personne,
        est_reparti=True,
        est_retires=False
    )

    dons_recus = []
    total_retirer = Decimal('0.00')

    for don in dons_a_retirer:
        montant_par_personne = _calculate_amount_per_person(don, personne)
        total_retirer += montant_par_personne

        dons_recus.append({
            'don': don,
            'montant_recu': montant_par_personne,
        })

    dons_retires = Don.objects.filter(personne_vulnerable=personne, est_retires=True)
    total_retires = dons_retires.aggregate(total=Sum('montant'))['total'] or Decimal('0.00')

    context = {
        'dons': dons_recus,
        'total_retirer': total_retirer,
        'total_retires': total_retires,
    }
    return render(request, 'donations/voir_retirer_dons.html', context)


def _calculate_amount_per_person(don, personne):
    """Calculate the amount a specific person receives from a donation."""
    if don.personne_vulnerable.exists():
        nombre_personnes = don.personne_vulnerable.count()
        if nombre_personnes > 0:
            return don.montant / nombre_personnes
    else:
        personnes_entite = don.entite_vulnerable.personnevulnerable_set.filter(est_vulnerable=True)
        nombre_personnes = personnes_entite.count()
        if nombre_personnes > 0:
            return don.montant / nombre_personnes

    return Decimal('0.00')


@login_required
def retirer_don(request, don_id):
    """Mark a donation as withdrawn by vulnerable person."""
    try:
        personne = request.user.personnevulnerable
    except PersonneVulnerable.DoesNotExist:
        return redirect('home')

    don = get_object_or_404(
        Don,
        pk=don_id,
        personne_vulnerable=personne,
        est_reparti=True
    )

    don.est_retires = True
    don.save()

    messages.success(request, "Le don a été retiré avec succès.")
    return redirect('voir_retirer_dons')


@login_required
def retirer_tous_les_dons(request):
    """Mark all donations as withdrawn for the vulnerable person."""
    try:
        personne = request.user.personnevulnerable
    except PersonneVulnerable.DoesNotExist:
        return redirect('home')

    dons_a_retirer = Don.objects.filter(
        personne_vulnerable=personne,
        est_reparti=True,
        est_retires=False
    )

    dons_a_retirer.update(est_retires=True)

    messages.success(request, "Tous vos dons ont été retirés avec succès.")
    return redirect('voir_retirer_dons')


@login_required
def mes_dons_en_attente(request):
    """Display pending donations for the logged-in user."""
    dons_en_attente = Don.objects.filter(
        donateur=request.user,
        est_reparti=False
    ).order_by('-date_don')

    context = {'dons_en_attente': dons_en_attente}
    return render(request, 'donations/mes_dons_en_attente.html', context)


# =====================================================
# AJAX/JSON Views
# =====================================================

from django.http import JsonResponse
from donations.models import PersonneVulnerable

def get_personnes_vulnerables(request, entite):
    """
    Retourne les personnes vulnérables valides pour une entité donnée.
    """
    try:
        personnes = PersonneVulnerable.objects.filter(
            entite=entite,
            est_vulnerable=True,
            validated_by_admin=True,
            user__isnull=False,
            montant_recu__lt=200.00
        ).select_related('user')

        data = []
        for p in personnes:
            data.append({
                'id': p.id,
                'nom_complet': f"{p.first_name or 'Nom'} {p.last_name or 'Inconnu'}",
                'entite': p.get_entite_display(),
                'montant_recu': float(p.montant_recu or 0),
                'montant_requis': 200000.00,
                'pourcentage_atteint': round((float(p.montant_recu or 0) / 200000.00) * 100, 2),
                'username': p.user.username,
            })

        return JsonResponse({'personnes': data})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)



# =====================================================
# Dashboard Views
# =====================================================

@login_required
def dashboard_donateur(request):
    """Display donor dashboard with statistics and visualizations."""
    # Load regions data
    with open('donations/json_ci/IvoryCoast.json', encoding='utf-8') as f:
        data_json = json.load(f)
    regions_data_raw = data_json.get("regions", [])

    # Get statistics
    stats = _get_dashboard_statistics()

    # Get last three vulnerable people
    last_three_vulnerables = PersonneVulnerable.objects.filter(
        est_vulnerable=True,
        validated_by_admin=True
    ).order_by('-id')[:3]

    # Add simulated vulnerability percentage if missing
    last_three_list = []
    for p in last_three_vulnerables:
        vulnerability_percentage = getattr(p, 'pourcentage_vulnerabilite', random.randint(80, 99))
        last_three_list.append({
            'nom': p.first_name,
            'prenom': p.last_name,
            'pourcentage_vulnerabilite': vulnerability_percentage
        })

    # Process regions data
    regions_data = _process_regions_data(regions_data_raw, stats['stats_region'])

    # Calculate vulnerability rate
    globalVuln = next((stat['total'] for stat in stats['stats_pauvrete'] if stat['est_vulnerable'] is True), 0)
    globalNonVuln = next((stat['total'] for stat in stats['stats_pauvrete'] if stat['est_vulnerable'] is False), 0)
    totalPersons = globalVuln + globalNonVuln
    taux_vulnerabilite = (globalVuln / totalPersons * 100) if totalPersons > 0 else 0

    context = {
        'regions_data': json.dumps(regions_data),
        'stats_pauvrete': json.dumps(stats['stats_pauvrete']),
        'stats_region': json.dumps(stats['stats_region']),
        'stats_entite': json.dumps(stats['stats_entite']),
        'stats_sexe': json.dumps(stats['stats_sexe']),
        'stats_age': json.dumps(stats['stats_age']),
        'stats_enfants': json.dumps(stats['stats_enfants']),
        'nombre_personnes_total': stats['nombre_personnes_total'],
        'nombre_personnes_aidees': stats['nombre_personnes_aidees'],
        'nombre_personnes_vulnerables': stats['nombre_personnes_vulnerables'],
        'taux_vulnerabilite': round(taux_vulnerabilite, 2),
        'last_three_list': json.dumps(last_three_list)
    }

    return render(request, 'donations/dashboard_donateur.html', context)


def _get_dashboard_statistics():
    """Get all statistics for dashboard."""
    stats_region = list(
        PersonneVulnerable.objects
        .values('region_geographique')
        .annotate(
            total_vulnerables=Count(
                Case(When(est_vulnerable=True, then=1), output_field=IntegerField())
            ),
            total_non_vulnerables=Count(
                Case(When(est_vulnerable=False, then=1), output_field=IntegerField())
            )
        )
    )

    stats_pauvrete = list(
        PersonneVulnerable.objects
        .values('est_vulnerable')
        .annotate(total=Count('id'))
    )

    stats_entite = list(
        PersonneVulnerable.objects
        .values('entite')
        .annotate(
            total_vulnerables=Count('id', filter=Q(est_vulnerable=True)),
            total_non_vulnerables=Count('id', filter=Q(est_vulnerable=False)),
            total=Count('id')
        )
    )

    # Calculate percentages for each entity
    for stat in stats_entite:
        total = stat['total']
        if total:
            stat['pourcentage_vulnerables'] = round((stat['total_vulnerables'] * 100) / total, 2)
            stat['pourcentage_non_vulnerables'] = round((stat['total_non_vulnerables'] * 100) / total, 2)
        else:
            stat['pourcentage_vulnerables'] = 0
            stat['pourcentage_non_vulnerables'] = 0

    stats_sexe = list(
        PersonneVulnerable.objects
        .values('sexe')
        .annotate(
            total_vulnerables=Count('id', filter=Q(est_vulnerable=True)),
            total_non_vulnerables=Count('id', filter=Q(est_vulnerable=False))
        )
    )

    stats_age = list(
        PersonneVulnerable.objects
        .values('age')
        .annotate(
            total_vulnerables=Count('id', filter=Q(est_vulnerable=True)),
            total_non_vulnerables=Count('id', filter=Q(est_vulnerable=False))
        )
        .order_by('age')
    )

    stats_enfants = PersonneVulnerable.objects.aggregate(
        enfants_vulnerables=Sum('nombre_enfants', filter=Q(est_vulnerable=True)),
        enfants_non_vulnerables=Sum('nombre_enfants', filter=Q(est_vulnerable=False))
    )

    nombre_personnes_total = PersonneVulnerable.objects.count()
    nombre_personnes_aidees = PersonneVulnerable.objects.filter(
        est_vulnerable=True,
        montant_recu__gt=0
    ).count()
    nombre_personnes_vulnerables = PersonneVulnerable.objects.filter(est_vulnerable=True).count()

    return {
        'stats_region': stats_region,
        'stats_pauvrete': stats_pauvrete,
        'stats_entite': stats_entite,
        'stats_sexe': stats_sexe,
        'stats_age': stats_age,
        'stats_enfants': stats_enfants,
        'nombre_personnes_total': nombre_personnes_total,
        'nombre_personnes_aidees': nombre_personnes_aidees,
        'nombre_personnes_vulnerables': nombre_personnes_vulnerables,
    }


def _process_regions_data(regions_data_raw, stats_region):
    """Process regions data with statistics."""
    regions_data = []
    for region_raw in regions_data_raw:
        region_name = region_raw.get("name")
        if not region_name:
            continue

        found_stats = next(
            (s for s in stats_region if s["region_geographique"] == region_name),
            None
        )

        total_vuln = found_stats["total_vulnerables"] if found_stats else 0
        total_nonvuln = found_stats["total_non_vulnerables"] if found_stats else 0

        regions_data.append({
            "name": region_name,
            "lat": float(region_raw.get("lat", 0)),
            "lng": float(region_raw.get("lng", 0)),
            "total_vulnerables": total_vuln,
            "total_non_vulnerables": total_nonvuln
        })

    return regions_data


def dashboard_api(request):
    """API endpoint for dashboard data."""
    stats = _get_dashboard_statistics()

    # Load regions data
    with open('donations/json_ci/IvoryCoast.json', encoding='utf-8') as f:
        data_json = json.load(f)
    regions_data_raw = data_json.get("regions", [])

    regions_data = _process_regions_data(regions_data_raw, stats['stats_region'])

    # Calculate vulnerability rate
    globalVuln = next((stat['total'] for stat in stats['stats_pauvrete'] if stat['est_vulnerable'] is True), 0)
    globalNonVuln = next((stat['total'] for stat in stats['stats_pauvrete'] if stat['est_vulnerable'] is False), 0)
    totalPersons = globalVuln + globalNonVuln
    taux_vulnerabilite = (globalVuln / totalPersons * 100) if totalPersons > 0 else 0

    data = {
        'regions_data': regions_data,
        'stats_pauvrete': stats['stats_pauvrete'],
        'stats_region': stats['stats_region'],
        'stats_entite': stats['stats_entite'],
        'stats_sexe': stats['stats_sexe'],
        'stats_age': stats['stats_age'],
        'stats_enfants': stats['stats_enfants'],
        'nombre_personnes_total': stats['nombre_personnes_total'],
        'nombre_personnes_aidees': stats['nombre_personnes_aidees'],
        'nombre_personnes_vulnerables': stats['nombre_personnes_vulnerables'],
        'taux_vulnerabilite': round(taux_vulnerabilite, 2),
        'stats_pauvrete_vulnerables': globalVuln,
        'stats_pauvrete_non_vulnerables': globalNonVuln,
    }

    return JsonResponse(data)


def donation_stats_api(request):
    """API endpoint for donation statistics."""
    total_personnes = PersonneVulnerable.objects.filter(
        validated_by_admin=True,
        est_vulnerable=True
    ).count()

    total_montant = Don.objects.filter(
        est_reparti=True,
        date_don__month=timezone.now().month
    ).aggregate(total=Sum('montant'))['total'] or 0

    return JsonResponse({
        'total_personnes': total_personnes,
        'total_montant': float(total_montant)
    })


# =====================================================
# REST API Views
# =====================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def dons_en_attente_api(request):
    """API endpoint to get pending donations."""
    dons = Don.objects.filter(est_reparti=False).select_related('donateur')
    serializer = DonSerializer(dons, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mes_dons_api(request):
    """API endpoint to get user's donations."""
    try:
        dons = Don.objects.filter(donateur=request.user).order_by('-date_don')
        serializer = DonSerializer(dons, many=True)
        return Response({
            "count": dons.count(),
            "results": serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Erreur serveur: {str(e)}")
        return Response(
            {"error": "Erreur de récupération des dons"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_don_api(request):
    """API endpoint to create a new donation."""
    serializer = DonSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(donateur=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def validate_don_api(request, donation_id):
    """API endpoint for admin to validate a donation."""
    try:
        don = Don.objects.get(id=donation_id)
    except Don.DoesNotExist:
        return Response(
            {"success": False, "message": "Don non trouvé"},
            status=status.HTTP_404_NOT_FOUND
        )

    if don.est_reparti:
        return Response(
            {"success": False, "message": "Ce don a déjà été validé"},
            status=status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():
        don.est_reparti = True
        don.est_valide = True
        don.save()

        # Create notification for donor
        Notification.objects.create(
            user=don.donateur,
            message=f"Votre don de {don.montant} € a été validé."
        )

    serializer = DonSerializer(don)
    return Response(
        {"success": True, "message": "Don validé avec succès", "don": serializer.data},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_personnes_vulnerables_api(request, entite):
    """API endpoint to get vulnerable people by entity."""
    personnes = PersonneVulnerable.objects.filter(
        entite=entite,
        est_vulnerable=True,
        validated_by_admin=True
    ).select_related('user')
    serializer = PersonneVulnerableSerializer(personnes, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def withdraw_donation_api(request):
    """API endpoint for vulnerable person to withdraw a donation."""
    donation_id = request.data.get('donation_id')

    if donation_id is None:
        return Response(
            {"detail": "L'identifiant du don est requis."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        donation = Don.objects.get(
            id=donation_id,
            personne_vulnerable__user=request.user
        )
    except Don.DoesNotExist:
        return Response(
            {"detail": "Don introuvable ou non autorisé."},
            status=status.HTTP_404_NOT_FOUND
        )

    if not donation.est_reparti:
        return Response(
            {"detail": "Ce don ne peut pas être retiré car il n'est pas encore réparti."},
            status=status.HTTP_400_BAD_REQUEST
        )

    donation.est_retires = True
    donation.save()

    return Response(
        {"detail": "Don retiré avec succès."},
        status=status.HTTP_200_OK
    )