# communications/models.py
from django.db import models
from projects.models import Project
from subcontractors.models import Subcontractor

class EmailLog(models.Model):
    EMAIL_TYPES = [
        ('INVITATION', 'Tender Invitation'),
        ('REMINDER', 'Deadline Reminder'),
        ('ADDENDUM', 'Tender Addendum'),
        ('OTHER', 'Other Communication'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='emails')
    subcontractor = models.ForeignKey(Subcontractor, on_delete=models.CASCADE, related_name='emails')
    email_type = models.CharField(max_length=20, choices=EMAIL_TYPES)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.email_type} to {self.subcontractor.company} for {self.project.name}"

class EmailMonitorConfig(models.Model):
    """Configuration for email monitoring per project"""
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='email_config')
    folder_name = models.CharField(max_length=255, help_text="Name of folder in Outlook to monitor")
    folder_id = models.CharField(max_length=255, blank=True, help_text="ID of the folder in Outlook")
    last_check_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Email monitoring for {self.project.name}"