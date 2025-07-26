import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lanfiasave.settings')

app = Celery('lanfiasave')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
