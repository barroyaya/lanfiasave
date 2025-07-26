# formation/urls.py - URLs corrigées avec le bon type selon le modèle

from django.urls import path
from . import views

app_name = 'formation'

urlpatterns = [
    # URLs de base
    path('', views.formations_list, name='formations_list'),
    path('formation/<int:formation_id>/', views.formation_detail, name='formation_detail'),  # Formation = INT
    path('demande/<int:formation_id>/', views.demande_formation, name='demande_formation'),  # Formation = INT

    # URLs utilisateur
    path('mes-demandes/', views.mes_demandes, name='mes_demandes'),
    path('mes-demandes/<uuid:demande_id>/', views.demande_detail, name='demande_detail'),  # DemandeFormation = UUID
    path('mon-parcours/', views.mon_parcours, name='mon_parcours'),
    path('parcours/<uuid:parcours_id>/', views.parcours_detail, name='parcours_detail'),  # ParcoursFormation = UUID

    # Projets de vie
    path('projet/creer/', views.projet_vie_create, name='projet_vie_create'),
    path('mes-projets/', views.mes_projets, name='mes_projets'),
    path('projet/<uuid:projet_id>/', views.projet_detail, name='projet_detail'),  # ProjetVie = UUID

    # ===== URLs POUR L'ANALYSE IA =====
    path('mes-analyses-ia/', views.mes_analyses_ia, name='mes_analyses_ia'),
    path('analyse-ia/<uuid:demande_id>/', views.analyse_ia_detail, name='analyse_ia_detail'),  # DemandeFormation = UUID
    path('reanalyser/<uuid:demande_id>/', views.reanalyser_demande, name='reanalyser_demande'),
    # DemandeFormation = UUID

    # URLs Admin
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/demandes/', views.admin_demandes_list, name='admin_demandes_list'),
    path('admin/demandes/<uuid:demande_id>/', views.admin_demande_detail, name='admin_demande_detail'),
    # DemandeFormation = UUID
    path('admin/formations/', views.admin_formations_manage, name='admin_formations_manage'),
    path('admin/formation/creer/', views.admin_formation_create, name='admin_formation_create'),
    path('admin/formation/<int:formation_id>/modifier/', views.admin_formation_edit, name='admin_formation_edit'),
    # Formation = INT

    # Parcours Admin
    path('admin/parcours/', views.admin_parcours_list, name='admin_parcours_list'),
    path('admin/parcours/<uuid:parcours_id>/', views.admin_parcours_detail, name='admin_parcours_detail'),
    # ParcoursFormation = UUID
    path('admin/parcours/<uuid:parcours_id>/suivi/', views.admin_parcours_suivi, name='admin_parcours_suivi'),
    # ParcoursFormation = UUID

    # Projets Admin
    path('admin/projets/', views.admin_projets_list, name='admin_projets_list'),
    path('admin/projet/<uuid:projet_id>/', views.admin_projet_detail, name='admin_projet_detail'),  # ProjetVie = UUID

    # ===== URLs POUR LES ANALYSES IA ADMIN =====
    path('admin/analyses-ia/', views.analyses_ia_dashboard, name='analyses_ia_dashboard'),
    path('admin/analyses-lot/', views.admin_lancer_analyses_lot, name='admin_lancer_analyses_lot'),
    path('admin/analyser-toutes/', views.admin_analyser_toutes_demandes, name='admin_analyser_toutes_demandes'),
    path('admin/configuration-ia/', views.admin_configuration_ia, name='admin_configuration_ia'),
    path('admin/historique-analyses/', views.admin_historique_analyses, name='admin_historique_analyses'),
    path('admin/test-ia-connection/', views.admin_test_ia_connection, name='admin_test_ia_connection'),

    # Mentoring
    path('mentoring/', views.mentoring_dashboard, name='mentoring_dashboard'),
    path('mentoring/parcours/<uuid:parcours_id>/', views.mentoring_parcours_detail, name='mentoring_parcours_detail'),
    # ParcoursFormation = UUID
    path('mentoring/evaluation/<uuid:parcours_id>/', views.mentoring_evaluation, name='mentoring_evaluation'),
    # ParcoursFormation = UUID

    # ===== URLs POUR LES RAPPORTS =====
    path('rapports/formation/<int:formation_id>/', views.rapport_formation_detail, name='rapport_formation_detail'),
    # Formation = INT
    path('rapports/export/<str:type_rapport>/', views.export_rapport, name='export_rapport'),
    path('rapports/', views.rapports_formation, name='rapports_formation'),

    # Export CSV
    path('export/demandes/', views.export_demandes_csv, name='export_demandes_csv'),
    path('export/formations/', views.export_formations_csv, name='export_formations_csv'),
    path('export/parcours/', views.export_parcours_csv, name='export_parcours_csv'),

    # APIs
    path('api/analyser-demande/<uuid:demande_id>/', views.api_analyser_demande, name='api_analyser_demande'),
    # DemandeFormation = UUID
    path('api/analyser-projet/<uuid:projet_id>/', views.api_analyser_projet, name='api_analyser_projet'),
    # ProjetVie = UUID
    path('api/stats/', views.api_stats_formation, name='api_stats_formation'),
    path('api/dashboard-stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
    path('api/formations-populaires/', views.api_formations_populaires, name='api_formations_populaires'),
    path('api/evolution-demandes/', views.api_evolution_demandes, name='api_evolution_demandes'),
    path('api/repartition-scores/', views.api_repartition_scores, name='api_repartition_scores'),
    path('api/recherche-formations/', views.api_recherche_formations, name='api_recherche_formations'),
    path('api/accepter-demande/<uuid:demande_id>/', views.api_accepter_demande, name='api_accepter_demande'),
    # DemandeFormation = UUID
    path('api/refuser-demande/<uuid:demande_id>/', views.api_refuser_demande, name='api_refuser_demande'),
    # DemandeFormation = UUID
    path('api/update-progression/<uuid:parcours_id>/', views.api_update_progression, name='api_update_progression'),
    # ParcoursFormation = UUID
    path('api/notifications/', views.api_formation_notifications, name='api_formation_notifications'),

    # ===== API POUR LE FILTRAGE =====
    path('api/filtrer-demandes/', views.api_filtrer_demandes, name='api_filtrer_demandes'),

    # ===== URLs DE DEBUG (à retirer en production) =====
    path('debug/test-ollama/', views.admin_test_ia_connection, name='debug_test_ollama'),
    # path('debug/test-analyse/<uuid:demande_id>/', views.admin_test_analyse_demande, name='debug_test_analyse'),
]