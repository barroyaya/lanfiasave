# donations/urls.py
from django.urls import path
from . import views
from .views import dashboard_api, dons_en_attente_api, withdraw_donation_api

urlpatterns = [
    # path('', views.donation_list, name='donation_list'),
    path('', views.donation_view, name='donation_view'),
    # path('donate/<int:person_id>/', views.make_donation, name='make_donation'),
    path('admin/dons-attente/', views.liste_dons_attente, name='liste_dons_attente'),
    # path('admin/repartir-don/<int:don_id>/', views.repartir_don_admin, name='repartir_don'),
    path('historique-dons/', views.historique_dons, name='historique_dons'),
    path('mes-dons/', views.voir_retirer_dons, name='voir_retirer_dons'),
    path('retirer-don/<int:don_id>/', views.retirer_don, name='retirer_don'),

    path('get_personnes_vulnerables/<str:entite>/', views.get_personnes_vulnerables, name='get_personnes_vulnerables'),
    path('retirer-tous-les-dons/', views.retirer_tous_les_dons, name='retirer_tous_les_dons'),
    path('mes-dons-en-attente/', views.mes_dons_en_attente, name='mes_dons_en_attente'),
    path('dashboard/', views.dashboard_donateur, name='dashboard_donateur'),
    path('dashboard_api/', dashboard_api, name='dashboard_api'),
    path('api/dons-en-attente/', dons_en_attente_api, name='dons_en_attente_api'),
    path('api/mes-dons/', views.mes_dons_api, name='mes_dons_api'),
    path('api/create-don/', views.create_don_api, name='create_don_api'),
    path('api/validate-don/<int:donation_id>/', views.validate_don_api, name='validate_don_api'),
    path('get_personnes_vulnerables_api/<str:entite>/', views.get_personnes_vulnerables_api, name='get_personnes_vulnerables_api'),
    path('api/withdraw-donation/', withdraw_donation_api, name='withdraw_donation_api'),
    path('stats_api/', views.donation_stats_api, name='donation_stats_api'),
]
