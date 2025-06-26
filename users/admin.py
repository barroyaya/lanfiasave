# # users/admin.py
# # users/admin.py
# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# from django.contrib import messages
# from .models import User, PersonneVulnerable
#
# class CustomUserAdmin(UserAdmin):
#     fieldsets = UserAdmin.fieldsets + (
#         (None, {'fields': ('is_donator', 'is_vulnerable', 'is_recenseur')}),
#     )
#     list_display = ('username', 'first_name', 'last_name', 'is_donator', 'is_vulnerable', 'is_recenseur', 'is_staff', 'is_active')
#
#
# admin.site.register(User, CustomUserAdmin)
#
# class PersonneVulnerableAdmin(admin.ModelAdmin):
#     list_display = (
#         'id', 'first_name', 'last_name', 'entite', 'age', 'revenu',
#         'est_vulnerable', 'validated_by_admin', 'montant_recu', 'get_recenseur', 'get_username'
#     )
#     list_filter = ('est_vulnerable', 'validated_by_admin', 'entite')
#     search_fields = ['first_name', 'last_name', 'entite']
#     actions = ['valider_personnes_vulnerables']
#
#     def get_recenseur(self, obj):
#         return obj.recenseur.username if obj.recenseur else "Non renseigné"
#     get_recenseur.short_description = 'Recenseur'
#
#     def get_username(self, obj):
#         return obj.user.username if obj.user else "Aucun compte"
#     get_username.short_description = 'Utilisateur'
#
#     def valider_personnes_vulnerables(self, request, queryset):
#         for personne in queryset:
#             if not personne.user:
#                 messages.error(request, f"La personne {personne} n'a pas de compte utilisateur.")
#                 continue
#             personne.est_vulnerable = True
#             personne.validated_by_admin = True
#             personne.save()
#             if personne.user:
#                 personne.user.is_vulnerable = True
#                 personne.user.is_donator = False
#                 personne.user.save()
#             messages.success(request, f"La personne {personne} a été validée comme vulnérable.")
#     valider_personnes_vulnerables.short_description = "Valider comme personnes vulnérables"
#
#     def save_model(self, request, obj, form, change):
#         if not obj.recenseur:
#             obj.recenseur = request.user
#         super().save_model(request, obj, form, change)
#         if obj.est_vulnerable and obj.user:
#             obj.user.is_vulnerable = True
#             obj.user.is_donator = False
#             obj.user.save()
#
# admin.site.register(PersonneVulnerable, PersonneVulnerableAdmin)
#
# admin.site.site_header = "Administration LanfiaSave"
# admin.site.site_title = "LanfiaSave Admin"
# admin.site.index_title = "Bienvenue dans l'administration"
#
# # Ajout d'un lien vers le tableau de bord personnalisé dans l'index de l'administration
# from django.urls import reverse
# from django.utils.html import format_html
#
# def custom_admin_index(request):
#     dashboard_url = reverse('admin_dashboard')
#     return format_html(f'<a href="{dashboard_url}">Accéder au Tableau de bord</a>')
#
# admin.site.index_template = 'custom_admin_index.html'


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib import messages
from .models import User, PersonneVulnerable

# === CONFIG USER ===
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('is_donator', 'is_vulnerable', 'is_recenseur')}),
    )
    list_display = (
        'username', 'first_name', 'last_name',
        'is_donator', 'is_vulnerable', 'is_recenseur',
        'is_staff', 'is_active'
    )

admin.site.register(User, CustomUserAdmin)

# === CONFIG PERSONNE VULNERABLE ===
class PersonneVulnerableAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'first_name', 'last_name', 'entite', 'age', 'revenu',
        'est_vulnerable', 'validated_by_admin', 'montant_recu',
        'get_recenseur', 'get_username'
    )
    list_filter = ('est_vulnerable', 'validated_by_admin', 'entite')
    search_fields = ['first_name', 'last_name', 'entite']
    actions = ['valider_personnes_vulnerables']

    def get_recenseur(self, obj):
        return obj.recenseur.username if obj.recenseur else "Non renseigné"
    get_recenseur.short_description = 'Recenseur'

    def get_username(self, obj):
        return obj.user.username if obj.user else "Aucun compte"
    get_username.short_description = 'Utilisateur'

    def valider_personnes_vulnerables(self, request, queryset):
        for personne in queryset:
            if not personne.user:
                messages.error(request, f"La personne {personne} n'a pas de compte utilisateur.")
                continue
            personne.est_vulnerable = True
            personne.validated_by_admin = True
            personne.save()
            if personne.user:
                personne.user.is_vulnerable = True
                personne.user.is_donator = False
                personne.user.save()
            messages.success(request, f"La personne {personne} a été validée comme vulnérable.")
    valider_personnes_vulnerables.short_description = "Valider comme personnes vulnérables"

    def save_model(self, request, obj, form, change):
        if not obj.recenseur:
            obj.recenseur = request.user
        super().save_model(request, obj, form, change)
        if obj.est_vulnerable and obj.user:
            obj.user.is_vulnerable = True
            obj.user.is_donator = False
            obj.user.save()

admin.site.register(PersonneVulnerable, PersonneVulnerableAdmin)

# === CUSTOM ADMIN HEADER ===
admin.site.site_header = "Administration LanfiaSave"
admin.site.site_title = "LanfiaSave Admin"
admin.site.index_title = "Bienvenue dans l'administration"

# === LIEN VERS LE TABLEAU DE BORD ET CAROUSEL ===
from django.urls import reverse
from django.utils.html import format_html

def custom_admin_index(request):
    dashboard_url = reverse('admin_dashboard')
    carousel_url = reverse('admin_personnes_carousel')
    return format_html('''
        <div class="dashboard-buttons" style="margin-bottom: 20px;">
            <a class="button" href="{}" style="padding: 8px 12px; background-color: #0d6efd; color: white; text-decoration: none; border-radius: 5px;">📊 Accéder au Tableau de bord</a>
            <a class="button" href="{}" style="padding: 8px 12px; background-color: #198754; color: white; text-decoration: none; border-radius: 5px; margin-left: 10px;">👥 Voir les personnes recensées</a>
        </div>
    ''', dashboard_url, carousel_url)

admin.site.index_template = 'custom_admin_index.html'
