from django import forms
from .models import EmailMonitorConfig

class EmailMonitorConfigForm(forms.ModelForm):
    class Meta:
        model = EmailMonitorConfig
        fields = ['folder_name', 'is_active']
        widgets = {
            'folder_name': forms.TextInput(attrs={'class': 'form-control'}),
        }