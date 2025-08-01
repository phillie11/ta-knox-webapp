# feedback/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import SubcontractorFeedback

@admin.register(SubcontractorFeedback)
class SubcontractorFeedbackAdmin(admin.ModelAdmin):
    list_display = ('project', 'subcontractor', 'trade', 'status_badge', 'created_at', 'sent_at')
    list_filter = ('status', 'created_at', 'sent_at', 'project')
    search_fields = ('project__name', 'subcontractor__company', 'trade')
    readonly_fields = ('created_at', 'updated_at', 'sent_at', 'preview_email')
    
    fieldsets = (
        (None, {
            'fields': ('project', 'subcontractor', 'trade', 'status')
        }),
        ('Spreadsheet Info', {
            'fields': ('spreadsheet_path',)
        }),
        ('Email Content', {
            'fields': ('email_subject', 'preview_email')
        }),
        ('Timing', {
            'fields': ('created_at', 'updated_at', 'sent_at')
        }),
    )
    
    def status_badge(self, obj):
        """Display status as a colored badge"""
        colors = {
            'PENDING': 'warning',
            'SENT': 'success',
            'FAILED': 'danger'
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def preview_email(self, obj):
        """Display email body with proper HTML formatting"""
        if obj.email_body:
            return format_html(
                '<div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; max-height: 300px; overflow-y: auto;">{}</div>',
                obj.email_body
            )
        return "No email content"
    preview_email.short_description = 'Email Preview'