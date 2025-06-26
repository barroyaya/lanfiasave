# users/views_api.py
from rest_framework import viewsets
from .models import PersonneVulnerable
from .serializers import PersonneVulnerableSerializer
from rest_framework.permissions import IsAuthenticated

class PersonneVulnerableViewSet(viewsets.ModelViewSet):
    """
    API endpoint permettant aux recenseurs et aux administrateurs
    de lister, récupérer et mettre à jour les informations de recensement.
    """
    queryset = PersonneVulnerable.objects.all()
    serializer_class = PersonneVulnerableSerializer
    permission_classes = [IsAuthenticated]
