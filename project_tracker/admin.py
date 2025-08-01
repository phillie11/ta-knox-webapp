from django.contrib import admin
from .models import ProjectStatus, ProjectTracker

@admin.register(ProjectStatus)
class ProjectStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'display_order')
    ordering = ('display_order',)

@admin.register(ProjectTracker)
class ProjectTrackerAdmin(admin.ModelAdmin):
    list_display = ('job_number', 'project_name', 'client', 'status', 'estimator', 'tender_deadline')
    list_filter = ('status', 'estimator')
    search_fields = ('job_number', 'project_name', 'client', 'location')
    date_hierarchy = 'tender_deadline'
    fieldsets = (
        (None, {
            'fields': ('status', 'job_number', 'estimator', 'client', 'project_name', 'location')
        }),
        ('Project Details', {
            'fields': ('pmqs', 'contract_type')
        }),
        ('Dates', {
            'fields': ('date_received', 'win_room_date', 'rfi_deadline', 'site_visit_date', 
                       'sc_deadline', 'tender_deadline', 'mid_bid_review_date')
        }),
        ('Tender Details', {
            'fields': ('tender_bid_amount', 'margin_percentage', 'key_risks', 'notes')
        }),
    )