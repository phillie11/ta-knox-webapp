# communications/apps.py - Simplified version
from django.apps import AppConfig
from django.conf import settings

class CommunicationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'communications'