import os
from celery import Celery
import ssl

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

CELERY_BROKER_URL = os.getenv("REDIS_URL")


CELERY_BROKER_USE_SSL = {
    "ssl_cert_reqs": ssl.CERT_NONE
}


app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
