from django.urls import path
from . import views
from .views import api_notifications, api_notifi

urlpatterns = [
    path('api/', views.api_notifications, name='api_notifications'),
    path('api1/', api_notifi, name='api_notifications1'),
    # path('notifications/', views.notifications_view, name='notifications'),  # Vue principale des notifications


]
