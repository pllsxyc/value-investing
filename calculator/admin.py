from django.contrib import admin

from .models import DcfCalculation, DcfTag


@admin.register(DcfTag)
class DcfTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at']
    search_fields = ['name', 'user__username']


@admin.register(DcfCalculation)
class DcfCalculationAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'ticker', 'user', 'value_per_share', 'created_at']
    search_fields = ['company_name', 'ticker', 'tags__name', 'user__username']
    list_filter = ['tags', 'created_at']
    filter_horizontal = ['tags']
