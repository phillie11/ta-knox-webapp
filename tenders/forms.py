# tenders/forms.py
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import TenderInvitation, TenderAddendum
from projects.models import Project
from subcontractors.models import Subcontractor, Trade
import logging

logger = logging.getLogger(__name__)

class TenderInvitationForm(forms.Form):
    subject = forms.CharField(
        max_length=255,
        initial="Tender Invitation"
    )
    message = forms.CharField(
        widget=forms.Textarea,
        initial="""We would like to invite you to tender for our project.

Please find the tender documents accessible via the SharePoint link below. The tender deadline is {deadline}.

Please let us know if you will be tendering by clicking one of the buttons below."""
    )
    subcontractors = forms.ModelMultipleChoiceField(
        queryset=Subcontractor.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    # Keep sharepoint_link field for manual override if needed
    sharepoint_link = forms.URLField(
        required=False,
        help_text="Optional: Override the project's default SharePoint link"
    )

    def __init__(self, *args, **kwargs):
        self.project_id = kwargs.pop('project_id')
        super().__init__(*args, **kwargs)

        # Get the project
        try:
            project = Project.objects.get(id=self.project_id)

            # Set up subcontractors queryset (all available)
            self.fields['subcontractors'].queryset = Subcontractor.objects.all().order_by('trade__name', 'company')

            # Update initial message with project name
            initial_message = self.fields['message'].initial
            initial_message = initial_message.replace("our project", f"the {project.name} project")
            self.fields['message'].initial = initial_message

            # Update subject with project name
            self.fields['subject'].initial = f"Tender Invitation: {project.name}"

            self.fields['sharepoint_link'].help_text = "Enter SharePoint link manually for this invitation"

        except Project.DoesNotExist:
            # Handle the case where the project doesn't exist
            logger.error(f"Project with ID {self.project_id} not found when initializing TenderInvitationForm")

    def clean(self):
        cleaned_data = super().clean()

        # Get the project to check if it has a SharePoint link
        try:
            project = Project.objects.get(id=self.project_id)
            sharepoint_link = cleaned_data.get('sharepoint_link', '')

            # If no manual SharePoint link provided, check if project has one
            project_has_sharepoint = (
                (hasattr(project, 'sharepoint_folder_url') and project.sharepoint_folder_url) or
                (hasattr(project, 'sharepoint_documents_link') and project.sharepoint_documents_link)
            )

            if not sharepoint_link and not project_has_sharepoint:
                raise ValidationError(
                    "No SharePoint link available. Please either add a SharePoint link to the project "
                    "or provide one in the form below."
                )

        except Project.DoesNotExist:
            raise ValidationError("Project not found.")

        return cleaned_data

class AddendumForm(forms.Form):
    subject = forms.CharField(
        max_length=255,
        initial="Tender Addendum"
    )
    message = forms.CharField(
        widget=forms.Textarea,
        initial="""Please note the following changes to the tender:

{changes}

All other tender conditions remain unchanged."""
    )
    subcontractors = forms.ModelMultipleChoiceField(
        queryset=Subcontractor.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    # Keep sharepoint_link field for manual override if needed
    sharepoint_link = forms.URLField(
        required=False,
        help_text="Optional: Override the project's default SharePoint link"
    )

    def __init__(self, *args, **kwargs):
        self.project_id = kwargs.pop('project_id')
        super().__init__(*args, **kwargs)

        try:
            project = Project.objects.get(id=self.project_id)

            # Include ALL subcontractors that have been invited
            invited_subcontractors = Subcontractor.objects.filter(
                tender_invitations__project=project
            ).distinct()

            # For display purposes, we'll mark declined ones in the template
            self.declined_subcontractors = Subcontractor.objects.filter(
                tender_invitations__project=project,
                tender_invitations__status='DECLINED'
            ).values_list('id', flat=True)

            self.fields['subcontractors'].queryset = invited_subcontractors.order_by('trade__name', 'company')

            # Update subject with project name
            self.fields['subject'].initial = f"Tender Addendum: {project.name}"

            self.fields['sharepoint_link'].help_text = "Enter SharePoint link manually for this addendum"

        except Project.DoesNotExist:
            logger.error(f"Project with ID {self.project_id} not found when initializing AddendumForm")