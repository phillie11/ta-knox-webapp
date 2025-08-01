# subcontractors/forms.py - Updated to include TradeForm
from django import forms
from .models import Subcontractor, Trade, Region
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

class SubcontractorForm(forms.ModelForm):
    class Meta:
        model = Subcontractor
        fields = [
            'trade', 'company', 'head_office', 'regions', 'pqq_status',
            'first_name', 'surname', 'email', 'subcontractor_score',
            'insurance_expiry', 'landline', 'mobile', 'website',
            'meeting_booked', 'notes'
        ]
        widgets = {
            'regions': forms.CheckboxSelectMultiple(),
            'insurance_expiry': forms.DateInput(attrs={'type': 'date'}),
            'meeting_booked': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'email': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Enter email addresses separated by semicolons (;)\nExample: john@company.com; jane@company.com; admin@company.com',
                'class': 'form-control'
            }),
        }

        labels = {
            'email': 'Email Address(es)',
        }

        help_texts = {
            'email': 'Enter multiple email addresses separated by semicolons (;). All addresses will receive tender invitations.',
        }

    def clean_email(self):
        """
        CUSTOM: Validate multiple email addresses
        """
        email_input = self.cleaned_data.get('email', '').strip()

        if not email_input:
            raise ValidationError("At least one email address is required.")

        # Split by semicolon and clean each email
        email_addresses = []

        # Handle both semicolon and comma separation
        if ';' in email_input:
            raw_emails = email_input.split(';')
        elif ',' in email_input:
            raw_emails = email_input.split(',')
        else:
            raw_emails = [email_input]

        for email in raw_emails:
            email = email.strip()
            if email:  # Skip empty strings
                try:
                    validate_email(email)
                    email_addresses.append(email)
                except ValidationError:
                    raise ValidationError(f"'{email}' is not a valid email address.")

        if not email_addresses:
            raise ValidationError("At least one valid email address is required.")

        # Join back with semicolons for consistent storage
        return '; '.join(email_addresses)


class TradeForm(forms.ModelForm):
    """Form for creating and editing Trade categories"""
    class Meta:
        model = Trade
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter trade name (e.g., Electrical, Plumbing, etc.)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description of this trade category'
            }),
        }

    def clean_name(self):
        """Ensure trade name is unique (case-insensitive)"""
        name = self.cleaned_data['name']
        if Trade.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A trade with this name already exists.")
        return name