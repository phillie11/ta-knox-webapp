from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Trade(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Region(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Subcontractor(models.Model):
    PQQ_STATUS_CHOICES = [
        ('NONE', 'Not Started'),
        ('SENT', 'Sent'),
        ('COMPLETED', 'Completed'),
    ]

    trade = models.ForeignKey(Trade, on_delete=models.CASCADE, related_name='subcontractors')
    company = models.CharField(max_length=255)
    head_office = models.CharField(max_length=255)
    regions = models.ManyToManyField(Region, blank=True)
    pqq_status = models.CharField(max_length=20, choices=PQQ_STATUS_CHOICES, default='NONE')
    first_name = models.CharField(max_length=100, blank=True)
    surname = models.CharField(max_length=100, blank=True)
    email = models.TextField(help_text="Enter multiple email addresses separated by semicolons (;)")
    subcontractor_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        null=True,
        blank=True
    )
    date_added = models.DateField(auto_now_add=True)
    insurance_expiry = models.DateField(null=True, blank=True)
    landline = models.CharField(max_length=20, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    meeting_booked = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['company', 'head_office']
        ordering = ['company', 'trade']

    def __str__(self):
        return f"{self.company} ({self.trade})"

    def full_name(self):
        return f"{self.first_name} {self.surname}".strip() or "No contact name"