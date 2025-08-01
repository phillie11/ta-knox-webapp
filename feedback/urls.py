# feedback/urls.py

from django.urls import path
from . import views

app_name = 'feedback'

urlpatterns = [
    path('', views.feedback_dashboard, name='dashboard'),
    path('upload/', views.upload_feedback_file, name='upload'),
    path('results/', views.feedback_results, name='results'),
    path('export/', views.export_analysis, name='export'),
    path('download/<str:format_type>/', views.download_report, name='download_report'),
    path('clear/', views.clear_analysis, name='clear'),
    path('test/', views.test_feedback_analysis, name='test'),
    path('ajax/analyze-sample/', views.ajax_analyze_sample, name='ajax_analyze_sample'),
]