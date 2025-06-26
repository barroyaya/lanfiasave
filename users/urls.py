from django.urls import path
from . import views
from .views import admin_dashboard, update_validation_status, voir_personne, modifier_personne, \
    personnes_vulnerables_api, personnes_recensees_api, users_list_api, AssignAccountView

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('notifications/', views.notifications_view, name='notifications'),

    # Autres routes pour gérer les personnes vulnérables, etc.
    path('recensement/', views.recenser_personne, name='recenser_personne'),
    path('recensees/', views.liste_personnes_recensees, name='liste_personnes_recensees'),
    path('valider/<int:personne_id>/', views.valider_personne, name='valider_personne'),
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('update-validation-status/<int:personne_id>/', update_validation_status, name='update_validation_status'),
    path('voir-personne/<int:personne_id>/', voir_personne, name='voir_personne'),
    path('modifier-personne/<int:personne_id>/', modifier_personne, name='modifier_personne'),
    path('register_api/', views.register_api, name='register_api'),
    path('profile_api/', views.profile_api, name='profile_api'),
    path('login_api/', views.login_api, name='login_api'),
    path('logout_api/', views.logout_api, name='logout_api'),
    path('api/personnes/', personnes_vulnerables_api, name='personnes_api'),
    path('login_api1/', views.login_api1, name='login_api1'),
    path('api/personnes/', personnes_recensees_api, name='personnes_api'),
    path('api/users/', users_list_api, name='users_list_api'),
    path('profile_api1/', views.profile_api1, name='profile_api1'),
    path("api/recenser-personne/", views.recenser_personne_api, name="recenser_personne_api"),
    path('api/create-user/', views.create_user_api, name='create_user_api'),
    path('api/recensement/', views.recensement_api, name='recensement_api'),
    path('api/create-vulnerable-person/', views.create_vulnerable_person_api, name='create_vulnerable_person_api'),
    path('api/connected-users/', views.get_connected_users_api, name='get_connected_users_api'),
    path('api/pending-vulnerable/', views.pending_vulnerable_api, name='pending_vulnerable_api'),
    path('api/validate-vulnerable/<int:person_id>/', views.validate_vulnerable_api, name='validate_vulnerable_api'),
    path('api/assign-account/<int:person_id>/', AssignAccountView.as_view(), name='assign-account'),
    path('recenseur/profile/', views.recenseur_profile_api, name='recenseur_profile_api'),
    path('recenseur/last-five/', views.last_five_persons_api, name='last_five_persons_api'),
    path('recenseur/person/<int:person_id>/', views.recensed_person_detail_api, name='recensed_person_detail_api'),
    path('logout_api1/', views.logout_api, name='logout_api1'),
    path('api/change-password/', views.change_password_api, name='change_password_api'),
    path('personnes-carousel/', views.admin_personnes_carousel, name='admin_personnes_carousel'),
    path('valider_personne/<int:personne_id>/', views.valider_personne, name='valider_personne'),
    path('rejeter_personne/<int:personne_id>/', views.rejeter_personne, name='rejeter_personne'),



]
