from django.contrib import admin
from .models import Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'reference', 'location', 'start_date', 'tender_deadline')
    list_filter = ('start_date', 'tender_deadline')
    search_fields = ('name', 'reference', 'location', 'description')
    date_hierarchy = 'tender_deadline'
    fieldsets = (
        (None, {
            'fields': ('name', 'reference', 'location')
        }),
        ('Details', {
            'fields': ('description',)
        }),
        ('Dates', {
            'fields': ('start_date', 'tender_deadline')
        }),
    )