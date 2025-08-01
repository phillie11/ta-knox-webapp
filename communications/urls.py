# communications/urls.py - Simplified version
from django.urls import path
from . import views

app_name = 'communications'

urlpatterns = [
    # Main email monitoring functions
    path('project/<int:project_id>/configure-monitoring/', views.configure_email_monitoring, name='configure_monitoring'),
    path('project/<int:project_id>/check-now/', views.run_email_check_now, name='check_now'),
    path('mail-folders/', views.get_mail_folders, name='mail_folders'),
    path('manual-tender-return/', views.manual_tender_return, name='manual_tender_return'),
    path('api/mail-folders/', views.get_mail_folders, name='get_mail_folders'),
]