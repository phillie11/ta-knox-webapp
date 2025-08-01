# feedback/forms.py
from django import forms
from django.core.validators import FileExtensionValidator
from projects.models import Project

class SpreadsheetUploadForm(forms.Form):
    """Form for uploading comparison spreadsheets for feedback processing"""
    
    project = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    spreadsheet = forms.FileField(
        required=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['xlsx', 'xls'])
        ],
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    include_detailed_comparison = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Include detailed comparison data in the feedback",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    send_emails_immediately = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Send feedback emails immediately after processing",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Order projects by most recent first
        self.fields['project'].queryset = Project.objects.all().order_by('-created_at')

class FeedbackEmailTemplateForm(forms.Form):
    """Form for customizing feedback email templates"""
    
    subject_template = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        initial="Tender Feedback: {project_name} - {trade}"
    )
    
    body_template = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 15
        }),
        initial="""
<p>Dear {first_name},</p>

<p>Thank you for your recent tender submission for <strong>{project_name}</strong> in the <strong>{trade}</strong> trade.</p>

<p>We are pleased to provide you with feedback on your submission:</p>

<div style="margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
    <h3>Tender Comparison</h3>
    <p><strong>Status:</strong> {selection_status}</p>
    
    <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
        <tr style="background-color: #f2f2f2;">
            <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Item</th>
            <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Your Submission</th>
        </tr>
        {comparison_table}
    </table>
</div>

<p>We appreciate your participation and look forward to working with you on future projects.</p>

<p>Best regards,<br/>The Estimating Team</p>
        """
    )