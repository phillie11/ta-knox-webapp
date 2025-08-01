# projects/forms.py - MINIMAL WORKING VERSION
from django import forms
from django.utils import timezone
from .models import Project

class ProjectForm(forms.ModelForm):

    sharepoint_folder_id = forms.CharField(required=False, widget=forms.HiddenInput())
    email_folder_id = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Project
        fields = [
            'name', 'reference', 'location', 'description',
            'status', 'estimator', 'project_manager', 'pmqs', 'contract_type',
            'start_date', 'tender_deadline', 'win_room_date',
            'rfi_deadline', 'site_visit_date', 'sc_deadline', 'mid_bid_review_date',
            'tender_bid_amount', 'margin_percentage', 'key_risks',
            'sharepoint_folder_url', 'sharepoint_link_description',
            'sharepoint_folder_id', 'email_folder_id',
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
            'sharepoint_folder_url': forms.URLInput(attrs={'readonly': True}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['sharepoint_folder_url'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Select a SharePoint folder from the dropdown below'
        })

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
                field_value = getattr(self.instance, field_name, None)
                if field_value:
                    self.initial[field_name] = field_value.strftime('%Y-%m-%d')