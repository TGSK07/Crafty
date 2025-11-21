import os, redis
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crafty_backend.settings")
app = Celery("crafty_backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()