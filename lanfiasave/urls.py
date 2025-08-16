# lanfiasave/urls.py
from django.contrib import admin
from django.urls import path, include
from users import views as user_views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', user_views.home, name='home'),
    path('users/', include('users.urls')),
    path('users/', include('users.urls_api')),
    path('donations/', include('donations.urls')),
    path('notifications/', include('notifications.urls')),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html'),
         name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'),
         name='password_change_done'),
    path('formation/', include('formation.urls')),
]

# ✅ CORRECTION : Servir les fichiers statiques en mode DEBUG
if settings.DEBUG:
    # Fichiers statiques depuis STATICFILES_DIRS (pour le développement)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.STATIC_ROOT)
    # Fichiers media
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)