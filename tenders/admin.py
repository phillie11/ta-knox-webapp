# tenders/admin.py - Fixed version without SubcontractorRecommendation
from django.contrib import admin
from .models import (
    TenderInvitation, TenderDocument, TenderAddendum, TenderAnalysis,
    TenderQuestion, RFIItem, DocumentQuestion
)

@admin.register(TenderInvitation)
class TenderInvitationAdmin(admin.ModelAdmin):
    list_display = ('project', 'subcontractor', 'status', 'email_sent', 'email_opened', 'documents_downloaded')
    list_filter = ('status', 'documents_downloaded')
    search_fields = ('project__name', 'subcontractor__company')
    date_hierarchy = 'email_sent'

@admin.register(TenderDocument)
class TenderDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'document_type', 'created_at')
    list_filter = ('document_type',)
    search_fields = ('title', 'project__name')

@admin.register(TenderAddendum)
class TenderAddendumAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'created_at', 'sent_at')
    search_fields = ('title', 'project__name')

@admin.register(TenderAnalysis)
class TenderAnalysisAdmin(admin.ModelAdmin):
    list_display = ('project', 'analysis_date', 'risk_level', 'analysis_confidence', 'estimated_project_value')
    list_filter = ('risk_level', 'analysis_date', 'contract_type')
    search_fields = ('project__name',)
    readonly_fields = ('analysis_date', 'updated_date', 'documents_analyzed')

    fieldsets = (
        ('Project Information', {
            'fields': ('project', 'analysis_date', 'updated_date')
        }),
        ('Analysis Results', {
            'fields': ('project_overview', 'scope_of_work', 'risk_level', 'analysis_confidence', 'analysis_method')
        }),
        ('Requirements & Specifications', {
            'fields': ('key_requirements', 'technical_specifications'),
            'classes': ('collapse',)
        }),
        ('Financial Analysis', {
            'fields': ('estimated_value_range', 'estimated_project_value', 'cost_breakdown', 'budget_estimates'),
            'classes': ('collapse',)
        }),
        ('Timeline & Milestones', {
            'fields': ('project_duration_weeks', 'critical_milestones'),
            'classes': ('collapse',)
        }),
        ('Standards & Compliance', {
            'fields': ('building_standards', 'environmental_requirements', 'environmental_considerations',
                      'health_safety_requirements', 'compliance_requirements'),
            'classes': ('collapse',)
        }),
        ('Contract Information', {
            'fields': ('contract_type', 'contract_information'),
            'classes': ('collapse',)
        }),
        ('Quality & Safety', {
            'fields': ('quality_requirements', 'safety_requirements'),
            'classes': ('collapse',)
        }),
        ('Risk Analysis', {
            'fields': ('risk_assessment', 'identified_risks'),
            'classes': ('collapse',)
        }),
        ('Procurement & Coordination', {
            'fields': ('coordination_requirements', 'subcontractor_requirements', 'procurement_strategy'),
            'classes': ('collapse',)
        }),
        ('Analysis Metadata', {
            'fields': ('documents_analyzed', 'recommended_actions', 'clarification_needed'),
            'classes': ('collapse',)
        }),
    )

# Register TenderQuestion if it exists
try:
    @admin.register(TenderQuestion)
    class TenderQuestionAdmin(admin.ModelAdmin):
        list_display = ('project', 'category', 'priority', 'is_answered', 'created_at')
        list_filter = ('category', 'priority', 'is_answered')
        search_fields = ('question_text', 'project__name')
        readonly_fields = ('created_at', 'answered_at')
except:
    pass

# Register RFIItem if it exists
try:
    @admin.register(RFIItem)
    class RFIItemAdmin(admin.ModelAdmin):
        list_display = ('project', 'category', 'priority', 'status', 'created_at')
        list_filter = ('category', 'priority', 'status')
        search_fields = ('question', 'project__name')
        readonly_fields = ('created_at', 'updated_at')
except:
    pass

# Register DocumentQuestion if it exists
try:
    @admin.register(DocumentQuestion)
    class DocumentQuestionAdmin(admin.ModelAdmin):
        list_display = ('project', 'asked_by', 'created_at')
        search_fields = ('question_text', 'answer_text', 'project__name')
        readonly_fields = ('created_at',)
except:
    pass