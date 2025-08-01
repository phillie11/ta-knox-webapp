# projects/models.py
from django.db import models
from django.utils import timezone

class Project(models.Model):
    # Existing fields
    name = models.CharField(max_length=255)
    reference = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    sharepoint_folder_id = models.CharField(max_length=255, blank=True, null=True)
    email_folder_id = models.CharField(max_length=255, blank=True, null=True)
    email_folder_name = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField()
    tender_deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Status and tracking fields
    STATUS_CHOICES = [
        ('LIVE', 'Live'),
        ('SUBMITTED', 'Submitted'),
        ('SUCCESSFUL', 'Successful'),
        ('UNSUCCESSFUL', 'Unsuccessful'),
        ('DECLINED', 'Declined'),
        ('NEXT_STAGE', 'Next Stage'),
        ('ON_HOLD', 'On Hold'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='LIVE')
    estimator = models.CharField(max_length=50, blank=True)
    project_manager = models.CharField(max_length=50, blank=True)
    pmqs = models.CharField(max_length=100, blank=True, null=True)
    contract_type = models.CharField(max_length=50, blank=True, null=True)
    win_room_date = models.DateField(null=True, blank=True)
    rfi_deadline = models.DateField(null=True, blank=True)
    site_visit_date = models.DateField(null=True, blank=True)
    sc_deadline = models.DateField(null=True, blank=True)
    mid_bid_review_date = models.DateField(null=True, blank=True)
    tender_bid_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    margin_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    key_risks = models.TextField(blank=True)

    sharepoint_folder_url = models.URLField(
        blank=True,
        null=True,
        help_text="SharePoint link to the ITT (Invitation to Tender) documents folder"
    )
    sharepoint_link_description = models.CharField(
        max_length=255,
        blank=True,
        default="ITT Documents",
        help_text="Description for the SharePoint link (e.g., 'ITT Documents', 'Tender Package')"
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.reference})" if self.reference else self.name

    @property
    def has_sharepoint_documents(self):
        """Check if project has SharePoint documents configured"""
        return bool(self.sharepoint_folder_url)

    @property
    def can_generate_ai_analysis(self):
        """Check if AI analysis can be generated"""
        return bool(self.sharepoint_folder_url)

    @property
    def has_ai_analysis(self):
        """Check if project has AI analysis"""
        return hasattr(self, 'tender_analysis')

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
        return self.status == "LIVE"

    @property
    def formatted_deadline(self):
        if self.tender_deadline:
            return self.tender_deadline.strftime("%A %d/%m/%Y %I:%M %p")
        return "TBC"

    def __str__(self):
        return self.name