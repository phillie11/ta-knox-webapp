from django.contrib import admin
from .models import Trade, Region, Subcontractor

@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Subcontractor)
class SubcontractorAdmin(admin.ModelAdmin):
    list_display = ('company', 'trade', 'head_office', 'first_name', 'surname', 'email', 'pqq_status', 'subcontractor_score')
    list_filter = ('trade', 'regions', 'pqq_status', 'insurance_expiry')
    search_fields = ('company', 'first_name', 'surname', 'email')
    filter_horizontal = ('regions',)
    fieldsets = (
        (None, {
            'fields': ('trade', 'company', 'head_office', 'regions', 'pqq_status')
        }),
        ('Contact Details', {
            'fields': ('first_name', 'surname', 'email', 'landline', 'mobile', 'website')
        }),
        ('Additional Information', {
            'fields': ('subcontractor_score', 'insurance_expiry', 'meeting_booked', 'notes')
        }),
    )