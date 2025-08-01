# projects/forms.py
from django import forms
from django.utils import timezone
from .models import Project

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'name', 'reference', 'location', 'description',
            'status', 'estimator', 'project_manager', 'pmqs', 'contract_type',
            'start_date', 'tender_deadline', 'win_room_date',
            'rfi_deadline', 'site_visit_date', 'sc_deadline', 'mid_bid_review_date',
            'tender_bid_amount', 'margin_percentage', 'key_risks',
            'sharepoint_folder_url', 'sharepoint_link_description'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'win_room_date': forms.DateInput(attrs={'type': 'date'}),
            'rfi_deadline': forms.DateInput(attrs={'type': 'date'}),
            'site_visit_date': forms.DateInput(attrs={'type': 'date'}),
            'sc_deadline': forms.DateInput(attrs={'type': 'date'}),
            'mid_bid_review_date': forms.DateInput(attrs={'type': 'date'}),
            'tender_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'description': forms.Textarea(attrs={'rows': 4}),
            'key_risks': forms.Textarea(attrs={'rows': 3}),
            'sharepoint_folder_url': forms.URLInput(attrs={
                'placeholder': 'https://yourtenant.sharepoint.com/sites/...',
                'class': 'form-control'
            }),
            'sharepoint_link_description': forms.TextInput(attrs={
                'placeholder': 'ITT Documents',
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only process if we have an existing instance with a primary key
        if self.instance and self.instance.pk:
            # Format tender_deadline with timezone handling
            if self.instance.tender_deadline:
                local_deadline = timezone.localtime(self.instance.tender_deadline)
                self.initial['tender_deadline'] = local_deadline.strftime('%Y-%m-%dT%H:%M')

            # Format all date fields for proper HTML date input format (YYYY-MM-DD)
            date_fields = [
                'start_date', 'win_room_date', 'rfi_deadline',
                'site_visit_date', 'sc_deadline', 'mid_bid_review_date'
            ]

            for field_name in date_fields:
                value = getattr(self.instance, field_name)
                if value:
                    # Make sure to convert to string in YYYY-MM-DD format for HTML date input
                    self.initial[field_name] = value.strftime('%Y-%m-%d')

    def clean_tender_deadline(self):
        """Ensure proper timezone handling for tender_deadline"""
        tender_deadline = self.cleaned_data.get('tender_deadline')

        if tender_deadline and timezone.is_naive(tender_deadline):
            # Interpret the naive datetime as being in the current time zone
            tender_deadline = timezone.make_aware(
                tender_deadline,
                timezone.get_current_timezone()
            )

        return tender_deadline

    def clean_sharepoint_documents_link(self):
        """Validate SharePoint link format"""
        link = self.cleaned_data.get('sharepoint_folder_url')

        if link:
            # Basic validation - ensure it's a valid URL and looks like SharePoint
            if not any(domain in link.lower() for domain in ['sharepoint.com', 'sharepoint.']):
                raise forms.ValidationError(
                    "Please enter a valid SharePoint URL (should contain 'sharepoint.com' or 'sharepoint.')"
                )

        return link