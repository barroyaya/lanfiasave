"""
WSGI config for lanfiasave project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# Supprimer les warnings TensorFlow/CUDA
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '-1')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lanfiasave.settings')

application = get_wsgi_application()