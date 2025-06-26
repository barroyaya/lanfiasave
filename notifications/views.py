import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Notification

@login_required
def api_notifications(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    # Préparer les données des notifications au format liste de dictionnaires
    notif_list = [
        {
            'message': n.message,
            'created_at': n.created_at.strftime("%d/%m/%Y %H:%M"),
        }
        for n in notifications
    ]
    # Optionnel : marquer les notifications comme lues
    notifications.update(is_read=True)
    return JsonResponse({'notifications': notif_list})

# your_app/views.py
# your_app/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_notifi(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    # Marquer les notifications comme lues
    notifications.update(is_read=True)
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)
