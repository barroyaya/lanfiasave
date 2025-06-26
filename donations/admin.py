# donations/admin.py
from django.contrib import admin
from django.db import transaction, models
from django.utils.html import format_html
from django.utils import timezone
from decimal import Decimal

# Import des modèles locaux
from .models import Don
from users.models import PersonneVulnerable
from notifications.models import Notification


def valider_dons(modeladmin, request, queryset):
    """Action pour valider et répartir les dons sélectionnés."""
    updated_count = 0
    errors = []

    for don in queryset:
        if not don.est_reparti:
            try:
                with transaction.atomic():
                    # Marquer le don comme validé et réparti
                    don.est_valide = True
                    don.est_reparti = True
                    don.save()
                    updated_count += 1

                    print(f"Validation du don {don.id} de {don.montant}€")

                    # Déterminer les personnes bénéficiaires
                    if don.personne_vulnerable.exists():
                        # Don ciblé sur des personnes spécifiques
                        personnes = don.personne_vulnerable.all()
                        montant_par_personne = don.montant / personnes.count()

                        print(f"Don ciblé: {personnes.count()} personne(s), {montant_par_personne}€ par personne")

                        for personne in personnes:
                            # Mettre à jour le montant reçu
                            if personne.montant_recu is None:
                                personne.montant_recu = Decimal('0.00')

                            personne.montant_recu += montant_par_personne

                            # Vérifier si la personne dépasse le seuil
                            if personne.montant_recu >= Decimal('200000.00'):
                                personne.est_vulnerable = False
                                message = f"Félicitations ! Vous avez atteint votre objectif de financement."
                            else:
                                reste = Decimal('200000.00') - personne.montant_recu
                                message = f"Il vous reste {reste:.2f}€ pour atteindre votre objectif."

                            personne.save()

                            # Créer une notification pour la personne
                            if personne.user:
                                Notification.objects.create(
                                    user=personne.user,
                                    message=f"Vous avez reçu un don de {montant_par_personne:.2f}F de {don.donateur.username}. {message}"
                                )
                    else:
                        # Don pour toute l'entité
                        personnes_entite = PersonneVulnerable.objects.filter(
                            entite=don.entite_vulnerable,
                            est_vulnerable=True,
                            validated_by_admin=True
                        )

                        if personnes_entite.exists():
                            montant_par_personne = don.montant / personnes_entite.count()

                            print(
                                f"Don pour l'entité {don.entite_vulnerable}: {personnes_entite.count()} personne(s), {montant_par_personne}€ par personne")

                            # Associer ces personnes au don pour la traçabilité
                            for personne in personnes_entite:
                                don.personne_vulnerable.add(personne)

                                # Mettre à jour le montant reçu
                                if personne.montant_recu is None:
                                    personne.montant_recu = Decimal('0.00')

                                personne.montant_recu += montant_par_personne

                                # Vérifier si la personne dépasse le seuil
                                if personne.montant_recu >= Decimal('200000.00'):
                                    personne.est_vulnerable = False
                                    message = f"Félicitations ! Vous avez atteint votre objectif de financement."
                                else:
                                    reste = Decimal('200000.00') - personne.montant_recu
                                    message = f"Il vous reste {reste:.2f}€ pour atteindre votre objectif."

                                personne.save()

                                # Créer une notification pour la personne
                                if personne.user:
                                    Notification.objects.create(
                                        user=personne.user,
                                        message=f"Vous avez reçu un don de {montant_par_personne:.2f}F de {don.donateur.username}. {message}"
                                    )
                        else:
                            errors.append(
                                f"Don #{don.id}: Aucune personne vulnérable validée dans l'entité {don.entite_vulnerable}")
                            # Annuler la validation
                            don.est_valide = False
                            don.est_reparti = False
                            don.save()
                            updated_count -= 1
                            continue

                    # Créer une notification pour le donateur
                    Notification.objects.create(
                        user=don.donateur,
                        message=f"Votre don de {don.montant}€ a été validé et réparti avec succès."
                    )

            except Exception as e:
                print(f"Erreur lors de la validation du don {don.id}: {str(e)}")
                errors.append(f"Erreur pour le don #{don.id}: {str(e)}")
                continue

    # Messages de retour
    if updated_count > 0:
        modeladmin.message_user(
            request,
            f"{updated_count} don(s) ont été validé(s) et réparti(s) avec succès."
        )

    if errors:
        for error in errors:
            modeladmin.message_user(request, error, level='ERROR')


valider_dons.short_description = "Valider les dons en attente"


@admin.register(Don)
class DonAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'donateur',
        'get_personne_name',
        'entite_vulnerable',
        'montant',
        'est_reparti',
        'est_retires',
        'date_don',

    ]

    list_filter = [
        'est_reparti',
        'est_valide',
        'est_retires',
        'date_don',
        'entite_vulnerable'
    ]

    search_fields = [
        'donateur__username',
        'donateur__email',
        'personne_vulnerable__user__username',
        'description'
    ]

    ordering = ['-date_don']  # Trier par date décroissante (plus récent en premier)

    actions = [valider_dons]

    list_per_page = 25

    def get_personne_name(self, obj):
        """Afficher les noms des personnes vulnérables associées."""
        # Filtrer les personnes vulnérables qui ont un utilisateur associé
        personnes = obj.personne_vulnerable.filter(user__isnull=False).select_related('user')

        if personnes.exists():
            # Limiter à 3 personnes pour l'affichage
            noms = []
            for p in personnes[:3]:
                if p.user:
                    noms.append(p.user.username)

            resultat = ", ".join(noms)
            if personnes.count() > 3:
                resultat += f" ... (+{personnes.count() - 3})"

            return resultat
        else:
            return "-"

    get_personne_name.short_description = 'Personnes Vulnérables'
    get_personne_name.admin_order_field = 'personne_vulnerable'

    def get_queryset(self, request):
        """Optimiser les requêtes pour éviter les problèmes de performances."""
        qs = super().get_queryset(request)
        # Précharger les relations pour éviter les requêtes N+1
        return qs.select_related('donateur').prefetch_related('personne_vulnerable__user')

    # Configuration du formulaire d'édition
    fieldsets = [
        ('Informations du don', {
            'fields': ['donateur', 'montant', 'entite_vulnerable', 'provenance', 'description']
        }),
        ('Bénéficiaires', {
            'fields': ['personne_vulnerable'],
            'description': 'Laissez vide pour répartir entre toutes les personnes de l\'entité'
        }),
        ('Statut', {
            'fields': ['est_valide', 'est_reparti', 'est_retires'],
        }),
        ('Métadonnées', {
            'fields': ['date_don'],
            'classes': ['collapse']
        })
    ]

    readonly_fields = ['date_don']

    def has_delete_permission(self, request, obj=None):
        """Empêcher la suppression des dons validés."""
        if obj and obj.est_reparti:
            return False
        return super().has_delete_permission(request, obj)