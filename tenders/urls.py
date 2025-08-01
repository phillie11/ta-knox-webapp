# tenders/urls.py - UPDATED with simple tracking endpoints

from django.urls import path
from . import views

app_name = 'tenders'

urlpatterns = [
# Enhanced Ask AI endpoints
    path('project/<int:project_id>/ask-ai-enhanced/', views.ask_ai_question_enhanced, name='ask_ai_enhanced'),
    path('project/<int:project_id>/clear-knowledge-cache/', views.clear_project_knowledge_cache, name='clear_knowledge_cache'),
    path('project/<int:project_id>/knowledge-stats/', views.get_project_knowledge_stats, name='knowledge_stats'),

    # Main tender views
    path('', views.TenderListView.as_view(), name='list'),
    path('project/<int:project_id>/tracking/', views.TenderTrackingView.as_view(), name='tracking'),

    # RFI Management
    path('project/<int:project_id>/rfis/', views.rfi_list, name='rfi_list'),
    path('project/<int:project_id>/rfis/generate/', views.generate_rfis, name='generate_rfis'),
    path('project/<int:project_id>/rfis/regenerate/', views.regenerate_rfis, name='regenerate_rfis'),
    path('project/<int:project_id>/rfis/<int:rfi_id>/', views.rfi_detail, name='rfi_detail'),
    path('project/<int:project_id>/export-rfi-schedule/', views.export_rfi_schedule, name='export_rfi_schedule'),




    # Analysis views (if they exist)
    path('analysis/<int:project_id>/', views.TenderAnalysisView.as_view(), name='analysis'),
    path('project/<int:project_id>/generate-analysis/', views.GenerateAnalysisView.as_view(), name='generate_analysis'),
    path('project/<int:project_id>/update-analysis/', views.update_analysis, name='update_analysis'),

    # Invitation management
    path('project/<int:project_id>/send-invitation/', views.SendTenderInvitationView.as_view(), name='send_invitation'),
    path('project/<int:project_id>/send-addendum/', views.SendAddendumView.as_view(), name='send_addendum'),
    path('project/<int:project_id>/send-reminders/', views.SendAllRemindersView.as_view(), name='send_reminders'),
    path('analysis/<int:project_id>/file-formats/', views.ajax_file_format_analysis, name='ajax_file_format_analysis'),
    # Individual invitation actions
    path('invitation/<int:invitation_id>/send-reminder/', views.SendReminderView.as_view(), name='send_reminder'),
    path('invitation/<int:invitation_id>/resend/', views.ResendInvitationView.as_view(), name='resend_invitation'),
    path('invitation/<int:invitation_id>/update-notes/', views.update_invitation_notes, name='update_invitation_notes'),
    path('invitation/<int:invitation_id>/update-status/', views.UpdateInvitationStatusView.as_view(), name='update_invitation_status'),
    path('invitation/<int:invitation_id>/toggle-returned/', views.toggle_tender_returned, name='toggle_tender_returned'),

    # SIMPLIFIED: Document access (no tracking)
    path('project/<int:project_id>/download-documents/', views.download_documents, name='download_documents'),
    path('ai-diagnostics/', views.ai_service_diagnostics, name='ai_diagnostics'),

    # FIXED: Email tracking and responses
    path('response/<str:token>/', views.TenderResponseView.as_view(), name='response'),
    path('track-email/<str:token>/', views.TrackEmailView.as_view(), name='track_email'),
    path('ask-ai-question/<int:project_id>/', views.ask_ai_question, name='ask_ai_question'),

    # NEW: Simple tracking endpoints
    path('track-response/<str:token>/', views.TrackResponseView.as_view(), name='track_response'),
    path('track-download/<str:token>/', views.TrackDownloadView.as_view(), name='track_download'),

    # Analysis export endpoints
    path('export-contract/<int:project_id>/', views.export_contract_summary, name='export_contract'),
    path('export-rfi/<int:project_id>/', views.export_rfi_schedule, name='export_rfi'),

    # API endpoints
    path('tender-returned-api/', views.tender_returned_api, name='tender_returned_api'),
    path('manual-tender-return/', views.manual_tender_return, name='manual_tender_return'),

    # Email and reporting (if they exist)
    path('project/<int:project_id>/email-link/', views.EmailLinkView.as_view(), name='email_link'),
    path('project/<int:project_id>/email-screenshot/', views.EmailScreenshotView.as_view(), name='email_screenshot'),


# Enhanced Ask AI (add these to avoid conflicts with existing ask-ai)
    path('project/<int:project_id>/enhanced-ask-ai/', views.EnhancedAskAIView.as_view(), name='enhanced_ask_ai'),

    path('project/<int:project_id>/enhanced-ask-ai/question/', views.enhanced_ask_ai_question, name='enhanced_ask_ai_question'),

    path('project/<int:project_id>/conversation-history/', views.get_conversation_history, name='conversation_history'),

    path('project/<int:project_id>/enhanced-ask-ai-with-analysis/', views.enhanced_ask_ai_question_with_analysis, name='enhanced_ask_ai_with_analysis'),

    path('project/<int:project_id>/clear-cache/', views.clear_document_cache, name='clear_document_cache'),

    path('project/<int:project_id>/document-analysis/', views.get_document_analysis_summary, name='document_analysis_summary'),
    path('project/<int:project_id>/start-file-analysis/', views.start_file_format_analysis, name='start_file_analysis'),

    path('project/<int:project_id>/analysis-progress/', views.get_analysis_progress, name='analysis_progress'),

    path('project/<int:project_id>/file-analysis-results/', views.get_file_analysis_results, name='file_analysis_results'),
    path('analysis/<int:project_id>/preview/', views.ajax_analysis_preview, name='ajax_analysis_preview'),
    path('analysis/<int:project_id>/status/', views.ajax_analysis_status, name='ajax_analysis_status'),
    path('analysis/<int:project_id>/validate/', views.ajax_validate_analysis, name='ajax_validate_analysis'),
    path('analysis/<int:project_id>/export/', views.ajax_export_analysis, name='ajax_export_analysis'),
]