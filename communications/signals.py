# You can either delete this file or simplify it like this:
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import EmailMonitorConfig
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=EmailMonitorConfig)
def log_email_config_changes(sender, instance, created, **kwargs):
    """Log when email monitoring configurations are created or updated"""
    if created:
        logger.info(f"Created email monitoring config for project {instance.project.name}")
    else:
        logger.info(f"Updated email monitoring config for project {instance.project.name}")