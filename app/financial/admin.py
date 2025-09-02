"""
Django Admin Interface for Financial Models
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    FinancialInstitution, Account, Category, Tag, Transaction,
    Budget, BudgetCategory, ImportHistory, Webhook, WebhookDelivery
)


@admin.register(FinancialInstitution)
class FinancialInstitutionAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_type', 'website', 'is_active', 'created_at']
    list_filter = ['account_type', 'is_active', 'created_at']
    search_fields = ['name', 'website']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'account_type', 'website', 'phone', 'address')
        }),
        ('Media', {
            'fields': ('logo',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'account_type', 'balance', 'currency', 'institution', 'is_active']
    list_filter = ['account_type', 'currency', 'is_active', 'created_at', 'institution']
    search_fields = ['name', 'user__username', 'account_number']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['user__username', 'name']
    
    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'name', 'account_type', 'account_number', 'institution')
        }),
        ('Financial Details', {
            'fields': ('balance', 'currency', 'interest_rate', 'credit_limit', 'due_date')
        }),
        ('Additional Information', {
            'fields': ('notes', 'is_active')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'institution')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'color_display', 'icon', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'parent']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'full_path']
    ordering = ['name']
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'parent', 'description')
        }),
        ('Styling', {
            'fields': ('color', 'icon')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'full_path', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def color_display(self, obj):
        if obj.color:
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                obj.color, obj.color
            )
        return '-'
    color_display.short_description = 'Color'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_display', 'created_by', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'created_by']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['name']
    
    fieldsets = (
        ('Tag Information', {
            'fields': ('name', 'description', 'created_by')
        }),
        ('Styling', {
            'fields': ('color',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def color_display(self, obj):
        if obj.color:
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                obj.color, obj.color
            )
        return '-'
    color_display.short_description = 'Color'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['description', 'account', 'amount', 'transaction_type', 'category', 'transaction_date', 'is_reconciled']
    list_filter = ['transaction_type', 'is_reconciled', 'transaction_date', 'category', 'account__account_type']
    search_fields = ['description', 'reference_number', 'check_number', 'notes']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-transaction_date', '-created_at']
    date_hierarchy = 'transaction_date'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('account', 'description', 'amount', 'transaction_type', 'category')
        }),
        ('Additional Information', {
            'fields': ('tags', 'reference_number', 'check_number', 'notes')
        }),
        ('Dates', {
            'fields': ('transaction_date', 'posted_date')
        }),
        ('Status', {
            'fields': ('is_reconciled', 'is_recurring', 'recurring_pattern')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('account', 'category')


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'period_type', 'start_date', 'end_date', 'total_amount', 'is_active']
    list_filter = ['period_type', 'is_active', 'start_date', 'end_date']
    search_fields = ['name', 'user__username', 'notes']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-start_date']
    
    fieldsets = (
        ('Budget Information', {
            'fields': ('user', 'name', 'period_type', 'start_date', 'end_date', 'total_amount')
        }),
        ('Additional Information', {
            'fields': ('notes', 'is_active')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(BudgetCategory)
class BudgetCategoryAdmin(admin.ModelAdmin):
    list_display = ['budget', 'category', 'planned_amount', 'actual_amount', 'variance', 'variance_percentage']
    list_filter = ['budget__period_type', 'budget__is_active']
    search_fields = ['budget__name', 'category__name']
    readonly_fields = ['id', 'variance', 'variance_percentage', 'created_at', 'updated_at']
    ordering = ['budget__name', 'category__name']
    
    fieldsets = (
        ('Budget Category', {
            'fields': ('budget', 'category', 'planned_amount', 'actual_amount')
        }),
        ('Calculations', {
            'fields': ('variance', 'variance_percentage')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('budget', 'category')


@admin.register(ImportHistory)
class ImportHistoryAdmin(admin.ModelAdmin):
    list_display = ['filename', 'user', 'file_type', 'status', 'total_records', 'processed_records', 'failed_records', 'created_at']
    list_filter = ['status', 'file_type', 'created_at']
    search_fields = ['filename', 'user__username']
    readonly_fields = ['id', 'file_size', 'processing_time', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Import Information', {
            'fields': ('user', 'filename', 'file_type', 'status')
        }),
        ('Processing Details', {
            'fields': ('total_records', 'processed_records', 'failed_records', 'started_at', 'completed_at')
        }),
        ('Additional Information', {
            'fields': ('error_log',)
        }),
        ('Metadata', {
            'fields': ('id', 'file_size', 'processing_time', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'url', 'events_display', 'is_active', 'last_triggered', 'failure_count']
    list_filter = ['is_active', 'created_at', 'last_triggered']
    search_fields = ['name', 'url', 'user__username']
    readonly_fields = ['id', 'last_triggered', 'failure_count', 'created_at', 'updated_at']
    ordering = ['name']
    
    fieldsets = (
        ('Webhook Information', {
            'fields': ('user', 'name', 'url', 'events')
        }),
        ('Configuration', {
            'fields': ('secret_key', 'retry_count', 'timeout')
        }),
        ('Status', {
            'fields': ('is_active', 'last_triggered', 'failure_count')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def events_display(self, obj):
        if obj.events:
            return ', '.join(obj.events[:3]) + ('...' if len(obj.events) > 3 else '')
        return '-'
    events_display.short_description = 'Events'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = ['webhook', 'event_type', 'status', 'response_code', 'attempt_count', 'created_at']
    list_filter = ['status', 'response_code', 'created_at', 'webhook__is_active']
    search_fields = ['webhook__name', 'event_type', 'error_message']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Delivery Information', {
            'fields': ('webhook', 'event_type', 'status')
        }),
        ('Response Details', {
            'fields': ('response_code', 'response_body', 'error_message')
        }),
        ('Retry Information', {
            'fields': ('attempt_count', 'next_retry', 'delivered_at')
        }),
        ('Payload', {
            'fields': ('payload',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('webhook')