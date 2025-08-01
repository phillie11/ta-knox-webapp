# feedback/apps.py
from django.apps import AppConfig

class FeedbackConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'feedback'
    verbose_name = 'Subcontractor Feedback'
    
    def ready(self):
        # Import signals to ensure they are registered
        # Note: If you add signals later, uncomment this line
        # import feedback.signals
        pass