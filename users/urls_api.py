# users/urls_api.py
from django.urls import path, include
from rest_framework import routers
from .views_api import PersonneVulnerableViewSet

router = routers.DefaultRouter()
router.register(r'personnes', PersonneVulnerableViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
