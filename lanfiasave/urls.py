"""
URL configuration for lanfiasave project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# lanfiasave/urls.py
from django.contrib import admin
from django.urls import path, include
from users import views as user_views  # Importer la vue home depuis users
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', user_views.home, name='home'),  # Page d'accueil par défaut
    path('users/', include('users.urls')),  # Vos URLs utilisateurs
    path('users/', include('users.urls_api')),  # Nos endpoints API
    path('donations/', include('donations.urls')),  # Vos URLs donations
    path('notifications/', include('notifications.urls')),  # Vos URLs notifications

    # Routes de changement de mot de passe
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html'),
         name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'),
         name='password_change_done'),
    # Autres routes si nécessaire
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)