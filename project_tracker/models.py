from django.db import models
from django.utils import timezone
from datetime import datetime
from django.contrib.auth.models import User

class ProjectStatus(models.Model):
    """Status options for tenders"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    display_order = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name
    
    class Meta:
        app_label = 'project_tracker'
        ordering = ['display_order']
        verbose_name_plural = "Project Statuses"

class ProjectTracker(models.Model):
    """Main model for tracking tender projects"""
    # Basic Info
    status = models.ForeignKey(ProjectStatus, on_delete=models.PROTECT, related_name="projects")
    job_number = models.CharField(max_length=20, unique=True)
    estimator = models.CharField(max_length=50)
    client = models.CharField(max_length=255)
    project_name = models.CharField(max_length=255)
    pmqs = models.CharField(max_length=100, blank=True, null=True)
    contract_type = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=255)
    
    # Dates
    date_received = models.DateField(null=True, blank=True)
    win_room_date = models.DateField(null=True, blank=True)
    rfi_deadline = models.DateField(null=True, blank=True)
    site_visit_date = models.DateField(null=True, blank=True)
    sc_deadline = models.DateField(null=True, blank=True)
    tender_deadline = models.DateTimeField(null=True, blank=True)
    mid_bid_review_date = models.DateField(null=True, blank=True)
    
    # Financial Data
    tender_bid_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    margin_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Notes
    key_risks = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def time_left(self):
        """Calculate time remaining until deadline"""
        if not self.tender_deadline:
            return "No deadline set"
        
        now = timezone.now()
        if now > self.tender_deadline:
            return "Expired"
        
        delta = self.tender_deadline - now
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        return f"{days} days, {hours} hours, {minutes} minutes"
    
    @property
    def is_live(self):
        return self.status.name == "LIVE"
    
    @property
    def formatted_deadline(self):
        if self.tender_deadline:
            return self.tender_deadline.strftime("%A %d/%m/%Y %I:%M %p")
        return "TBC"
    
    def __str__(self):
        return f"{self.job_number} - {self.project_name}"