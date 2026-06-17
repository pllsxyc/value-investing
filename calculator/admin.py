from django.contrib import admin

from .models import DcfCalculation, DcfTag


@admin.register(DcfTag)
class DcfTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at']
    search_fields = ['name', 'user__username']


@admin.register(DcfCalculation)
class DcfCalculationAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'ticker', 'tag', 'user', 'value_per_share', 'created_at']
    search_fields = ['company_name', 'ticker', 'tag', 'user__username']
    list_filter = ['tag', 'created_at']
