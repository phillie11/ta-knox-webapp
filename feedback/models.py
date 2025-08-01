# feedback/models.py
from django.db import models
from django.utils import timezone
from projects.models import Project
from subcontractors.models import Subcontractor

class SubcontractorFeedback(models.Model):
    """Model to track feedback sent to subcontractors after tender comparison"""
    
    FEEDBACK_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='subcontractor_feedback')
    subcontractor = models.ForeignKey(Subcontractor, on_delete=models.CASCADE, related_name='feedback')
    comparison_data = models.JSONField(null=True, blank=True, help_text="Extracted comparison data for this subcontractor")
    
    spreadsheet_path = models.CharField(max_length=255, help_text="Path to the comparison spreadsheet")
    trade = models.CharField(max_length=100, help_text="Trade from the comparison spreadsheet")
    
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=FEEDBACK_STATUS_CHOICES, default='PENDING')
    
    # Store email content for reference
    email_subject = models.CharField(max_length=255, blank=True)
    email_body = models.TextField(blank=True)
    
    # Additional metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Feedback for {self.subcontractor.company} on {self.project.name}"
    
    def mark_as_sent(self):
        """Mark feedback as sent"""
        self.status = 'SENT'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])
    
    def mark_as_failed(self, error_message=None):
        """Mark feedback as failed with optional error message"""
        self.status = 'FAILED'
        if error_message:
            self.email_body += f"\n\nError: {error_message}"
        self.save(update_fields=['status', 'email_body'])