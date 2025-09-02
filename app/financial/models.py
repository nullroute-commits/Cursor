"""
Financial Models

Core models for the financial management system including:
- Accounts, Transactions, Categories, Tags, Budgets
- Financial Institutions and Import History
"""

import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from app.core.audit import AuditableModel

User = get_user_model()


class FinancialInstitution(models.Model):
    """Financial institution (bank, credit union, etc.)"""
    
    ACCOUNT_TYPES = [
        ('bank', _('Bank')),
        ('credit_union', _('Credit Union')),
        ('investment', _('Investment Firm')),
        ('credit_card', _('Credit Card Company')),
        ('other', _('Other')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='bank')
    website = models.URLField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='institutions/logos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Financial Institution')
        verbose_name_plural = _('Financial Institutions')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Account(models.Model):
    """Financial account (bank account, credit card, investment account)"""
    
    ACCOUNT_TYPES = [
        ('checking', _('Checking Account')),
        ('savings', _('Savings Account')),
        ('credit_card', _('Credit Card')),
        ('investment', _('Investment Account')),
        ('loan', _('Loan Account')),
        ('other', _('Other Account')),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('JPY', 'Japanese Yen'),
        ('CAD', 'Canadian Dollar'),
        ('AUD', 'Australian Dollar'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='financial_accounts')
    name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    institution = models.ForeignKey(FinancialInstitution, on_delete=models.SET_NULL, null=True, blank=True)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    interest_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.0000'))
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Account')
        verbose_name_plural = _('Accounts')
        ordering = ['name']
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()})"
    
    @property
    def available_balance(self):
        """Available balance considering credit limits"""
        if self.account_type == 'credit_card' and self.credit_limit:
            return self.credit_limit + self.balance
        return self.balance


class Category(models.Model):
    """Financial transaction categories"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    color = models.CharField(max_length=7, default='#3B82F6')  # Hex color
    icon = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['name']
        unique_together = ['name', 'parent']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    @property
    def full_path(self):
        """Get full category path"""
        path = [self.name]
        current = self.parent
        while current:
            path.insert(0, current.name)
            current = current.parent
        return ' > '.join(path)


class Tag(models.Model):
    """Custom transaction tags"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default='#6B7280')  # Hex color
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Transaction(models.Model):
    """Financial transaction record"""
    
    TRANSACTION_TYPES = [
        ('income', _('Income')),
        ('expense', _('Expense')),
        ('transfer', _('Transfer')),
        ('adjustment', _('Balance Adjustment')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    description = models.TextField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='transactions')
    transaction_date = models.DateField()
    posted_date = models.DateField(null=True, blank=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    check_number = models.CharField(max_length=20, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_reconciled = models.BooleanField(default=False)
    is_recurring = models.BooleanField(default=False)
    recurring_pattern = models.JSONField(null=True, blank=True)  # Store recurring pattern
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['account', 'transaction_date']),
            models.Index(fields=['transaction_date']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.description} - {self.amount} ({self.transaction_date})"
    
    def save(self, *args, **kwargs):
        """Override save to update account balance"""
        if self.pk:  # Update existing transaction
            old_transaction = Transaction.objects.get(pk=self.pk)
            old_amount = old_transaction.amount
            old_type = old_transaction.transaction_type
            
            # Reverse old transaction impact
            if old_type == 'income':
                self.account.balance -= old_amount
            elif old_type == 'expense':
                self.account.balance += old_amount
            elif old_type == 'transfer':
                # Handle transfer logic
                pass
        
        # Apply new transaction impact
        if self.transaction_type == 'income':
            self.account.balance += self.amount
        elif self.transaction_type == 'expense':
            self.account.balance -= self.amount
        elif self.transaction_type == 'transfer':
            # Handle transfer logic
            pass
        
        # Save account balance
        self.account.save()
        super().save(*args, **kwargs)


class Budget(models.Model):
    """Budget planning and tracking"""
    
    PERIOD_TYPES = [
        ('monthly', _('Monthly')),
        ('quarterly', _('Quarterly')),
        ('yearly', _('Yearly')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    name = models.CharField(max_length=255)
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES, default='monthly')
    start_date = models.DateField()
    end_date = models.DateField()
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Budget')
        verbose_name_plural = _('Budgets')
        ordering = ['-start_date']
        unique_together = ['user', 'name', 'start_date']
    
    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"


class BudgetCategory(models.Model):
    """Budget allocation by category"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='categories')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    planned_amount = models.DecimalField(max_digits=15, decimal_places=2)
    actual_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Budget Category')
        verbose_name_plural = _('Budget Categories')
        unique_together = ['budget', 'category']
    
    def __str__(self):
        return f"{self.budget.name} - {self.category.name}"
    
    @property
    def variance(self):
        """Budget variance (planned - actual)"""
        return self.planned_amount - self.actual_amount
    
    @property
    def variance_percentage(self):
        """Budget variance as percentage"""
        if self.planned_amount > 0:
            return (self.variance / self.planned_amount) * 100
        return 0


class ImportHistory(models.Model):
    """Track data import operations"""
    
    IMPORT_STATUS = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='imports')
    filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=20)  # csv, excel, pdf
    status = models.CharField(max_length=20, choices=IMPORT_STATUS, default='pending')
    total_records = models.IntegerField(default=0)
    processed_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
    error_log = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Import History')
        verbose_name_plural = _('Import History')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.filename} - {self.get_status_display()}"
    
    @property
    def processing_time(self):
        """Total processing time"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


class Webhook(models.Model):
    """Webhook configuration for external integrations"""
    
    WEBHOOK_EVENTS = [
        ('transaction.created', _('Transaction Created')),
        ('transaction.updated', _('Transaction Updated')),
        ('transaction.deleted', _('Transaction Deleted')),
        ('account.balance_changed', _('Account Balance Changed')),
        ('budget.threshold_exceeded', _('Budget Threshold Exceeded')),
        ('import.completed', _('Import Completed')),
        ('import.failed', _('Import Failed')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='webhooks')
    name = models.CharField(max_length=255)
    url = models.URLField()
    events = models.JSONField()  # List of event types
    is_active = models.BooleanField(default=True)
    secret_key = models.CharField(max_length=255, blank=True, null=True)
    retry_count = models.IntegerField(default=3)
    timeout = models.IntegerField(default=30)  # seconds
    last_triggered = models.DateTimeField(null=True, blank=True)
    failure_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Webhook')
        verbose_name_plural = _('Webhooks')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.url}"


class WebhookDelivery(models.Model):
    """Track webhook delivery attempts"""
    
    DELIVERY_STATUS = [
        ('pending', _('Pending')),
        ('sent', _('Sent')),
        ('failed', _('Failed')),
        ('retrying', _('Retrying')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    webhook = models.ForeignKey(Webhook, on_delete=models.CASCADE, related_name='deliveries')
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    status = models.CharField(max_length=20, choices=DELIVERY_STATUS, default='pending')
    response_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    attempt_count = models.IntegerField(default=0)
    next_retry = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Webhook Delivery')
        verbose_name_plural = _('Webhook Deliveries')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.webhook.name} - {self.event_type} ({self.get_status_display()})"