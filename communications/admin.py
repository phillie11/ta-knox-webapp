from django.contrib import admin
from .models import EmailLog, EmailMonitorConfig

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('email_type', 'project', 'subcontractor', 'subject', 'sent_at', 'opened_at')
    list_filter = ('email_type', 'project', 'sent_at', 'opened_at')
    search_fields = ('subject', 'body', 'project__name', 'subcontractor__company')
    date_hierarchy = 'sent_at'
    readonly_fields = ('opened_at',)

@admin.register(EmailMonitorConfig)
class EmailMonitorConfigAdmin(admin.ModelAdmin):
    list_display = ('project', 'folder_name', 'last_check_time', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('project__name', 'folder_name')
    readonly_fields = ('last_check_time',)