"""
Financial App URLs

URL patterns for the financial management application.
"""

from django.urls import path, include
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'financial'

urlpatterns = [
    # Dashboard and Overview
    path('', login_required(views.DashboardView.as_view()), name='dashboard'),
    path('overview/', login_required(views.OverviewView.as_view()), name='overview'),
    
    # Account Management
    path('accounts/', include([
        path('', login_required(views.AccountListView.as_view()), name='account_list'),
        path('create/', login_required(views.AccountCreateView.as_view()), name='account_create'),
        path('<uuid:pk>/', login_required(views.AccountDetailView.as_view()), name='account_detail'),
        path('<uuid:pk>/edit/', login_required(views.AccountUpdateView.as_view()), name='account_edit'),
        path('<uuid:pk>/delete/', login_required(views.AccountDeleteView.as_view()), name='account_delete'),
        path('<uuid:pk>/transactions/', login_required(views.AccountTransactionsView.as_view()), name='account_transactions'),
    ])),
    
    # Transaction Management
    path('transactions/', include([
        path('', login_required(views.TransactionListView.as_view()), name='transaction_list'),
        path('create/', login_required(views.TransactionCreateView.as_view()), name='transaction_create'),
        path('<uuid:pk>/', login_required(views.TransactionDetailView.as_view()), name='transaction_detail'),
        path('<uuid:pk>/edit/', login_required(views.TransactionUpdateView.as_view()), name='transaction_edit'),
        path('<uuid:pk>/delete/', login_required(views.TransactionDeleteView.as_view()), name='transaction_delete'),
        path('bulk-edit/', login_required(views.BulkTransactionEditView.as_view()), name='bulk_transaction_edit'),
        path('reconcile/', login_required(views.ReconciliationView.as_view()), name='reconciliation'),
    ])),
    
    # Category Management
    path('categories/', include([
        path('', login_required(views.CategoryListView.as_view()), name='category_list'),
        path('create/', login_required(views.CategoryCreateView.as_view()), name='category_create'),
        path('<uuid:pk>/', login_required(views.CategoryDetailView.as_view()), name='category_detail'),
        path('<uuid:pk>/edit/', login_required(views.CategoryUpdateView.as_view()), name='category_edit'),
        path('<uuid:pk>/delete/', login_required(views.CategoryDeleteView.as_view()), name='category_delete'),
        path('tree/', login_required(views.CategoryTreeView.as_view()), name='category_tree'),
    ])),
    
    # Tag Management
    path('tags/', include([
        path('', login_required(views.TagListView.as_view()), name='tag_list'),
        path('create/', login_required(views.TagCreateView.as_view()), name='tag_create'),
        path('<uuid:pk>/', login_required(views.TagDetailView.as_view()), name='tag_detail'),
        path('<uuid:pk>/edit/', login_required(views.TagUpdateView.as_view()), name='tag_edit'),
        path('<uuid:pk>/delete/', login_required(views.TagDeleteView.as_view()), name='tag_delete'),
    ])),
    
    # Budget Management
    path('budgets/', include([
        path('', login_required(views.BudgetListView.as_view()), name='budget_list'),
        path('create/', login_required(views.BudgetCreateView.as_view()), name='budget_create'),
        path('<uuid:pk>/', login_required(views.BudgetDetailView.as_view()), name='budget_detail'),
        path('<uuid:pk>/edit/', login_required(views.BudgetUpdateView.as_view()), name='budget_edit'),
        path('<uuid:pk>/delete/', login_required(views.BudgetDeleteView.as_view()), name='budget_delete'),
        path('<uuid:pk>/performance/', login_required(views.BudgetPerformanceView.as_view()), name='budget_performance'),
    ])),
    
    # Data Import
    path('import/', include([
        path('', login_required(views.ImportListView.as_view()), name='import_list'),
        path('upload/', login_required(views.FileUploadView.as_view()), name='file_upload'),
        path('<uuid:pk>/', login_required(views.ImportDetailView.as_view()), name='import_detail'),
        path('<uuid:pk>/process/', login_required(views.ProcessImportView.as_view()), name='process_import'),
        path('<uuid:pk>/cancel/', login_required(views.CancelImportView.as_view()), name='cancel_import'),
        path('template/', login_required(views.DownloadTemplateView.as_view()), name='download_template'),
    ])),
    
    # Analytics and Reporting
    path('analytics/', include([
        path('', login_required(views.AnalyticsView.as_view()), name='analytics'),
        path('trends/', login_required(views.TrendsView.as_view()), name='trends'),
        path('cash-flow/', login_required(views.CashFlowView.as_view()), name='cash_flow'),
        path('budget-analysis/', login_required(views.BudgetAnalysisView.as_view()), name='budget_analysis'),
        path('performance/', login_required(views.PerformanceView.as_view()), name='performance'),
    ])),
    
    # Reports
    path('reports/', include([
        path('', login_required(views.ReportListView.as_view()), name='report_list'),
        path('create/', login_required(views.ReportCreateView.as_view()), name='report_create'),
        path('<uuid:pk>/', login_required(views.ReportDetailView.as_view()), name='report_detail'),
        path('<uuid:pk>/edit/', login_required(views.ReportUpdateView.as_view()), name='report_edit'),
        path('<uuid:pk>/delete/', login_required(views.ReportDeleteView.as_view()), name='report_delete'),
        path('<uuid:pk>/export/', login_required(views.ExportReportView.as_view()), name='export_report'),
        path('scheduled/', login_required(views.ScheduledReportsView.as_view()), name='scheduled_reports'),
    ])),
    
    # Webhooks
    path('webhooks/', include([
        path('', login_required(views.WebhookListView.as_view()), name='webhook_list'),
        path('create/', login_required(views.WebhookCreateView.as_view()), name='webhook_create'),
        path('<uuid:pk>/', login_required(views.WebhookDetailView.as_view()), name='webhook_detail'),
        path('<uuid:pk>/edit/', login_required(views.WebhookUpdateView.as_view()), name='webhook_edit'),
        path('<uuid:pk>/delete/', login_required(views.WebhookDeleteView.as_view()), name='webhook_delete'),
        path('<uuid:pk>/test/', login_required(views.TestWebhookView.as_view()), name='test_webhook'),
        path('<uuid:pk>/deliveries/', login_required(views.WebhookDeliveriesView.as_view()), name='webhook_deliveries'),
    ])),
    
    # Configuration
    path('config/', include([
        path('', login_required(views.ConfigurationView.as_view()), name='configuration'),
        path('general/', login_required(views.GeneralConfigView.as_view()), name='general_config'),
        path('security/', login_required(views.SecurityConfigView.as_view()), name='security_config'),
        path('financial/', login_required(views.FinancialConfigView.as_view()), name='financial_config'),
        path('import/', login_required(views.ImportConfigView.as_view()), name='import_config'),
        path('webhooks/', login_required(views.WebhookConfigView.as_view()), name='webhook_config'),
        path('notifications/', login_required(views.NotificationConfigView.as_view()), name='notification_config'),
        path('performance/', login_required(views.PerformanceConfigView.as_view()), name='performance_config'),
        path('export/', login_required(views.ExportConfigView.as_view()), name='export_config'),
        path('import-config/', login_required(views.ImportConfigFileView.as_view()), name='import_config_file'),
        path('reset/', login_required(views.ResetConfigView.as_view()), name='reset_config'),
    ])),
    
    # API Endpoints
    path('api/', include([
        path('accounts/', views.AccountAPIView.as_view(), name='api_accounts'),
        path('transactions/', views.TransactionAPIView.as_view(), name='api_transactions'),
        path('categories/', views.CategoryAPIView.as_view(), name='api_categories'),
        path('tags/', views.TagAPIView.as_view(), name='api_tags'),
        path('budgets/', views.BudgetAPIView.as_view(), name='api_budgets'),
        path('analytics/', views.AnalyticsAPIView.as_view(), name='api_analytics'),
        path('webhooks/', views.WebhookAPIView.as_view(), name='api_webhooks'),
        path('config/', views.ConfigurationAPIView.as_view(), name='api_config'),
    ])),
    
    # Financial Institutions
    path('institutions/', include([
        path('', login_required(views.InstitutionListView.as_view()), name='institution_list'),
        path('create/', login_required(views.InstitutionCreateView.as_view()), name='institution_create'),
        path('<uuid:pk>/', login_required(views.InstitutionDetailView.as_view()), name='institution_detail'),
        path('<uuid:pk>/edit/', login_required(views.InstitutionUpdateView.as_view()), name='institution_edit'),
        path('<uuid:pk>/delete/', login_required(views.InstitutionDeleteView.as_view()), name='institution_delete'),
    ])),
    
    # Search and Advanced Features
    path('search/', login_required(views.SearchView.as_view()), name='search'),
    path('advanced/', login_required(views.AdvancedFeaturesView.as_view()), name='advanced_features'),
    
    # Export and Backup
    path('export/', include([
        path('transactions/', login_required(views.ExportTransactionsView.as_view()), name='export_transactions'),
        path('accounts/', login_required(views.ExportAccountsView.as_view()), name='export_accounts'),
        path('reports/', login_required(views.ExportReportsView.as_view()), name='export_reports'),
        path('backup/', login_required(views.CreateBackupView.as_view()), name='create_backup'),
    ])),
    
    # Health and Status
    path('health/', views.HealthCheckView.as_view(), name='health_check'),
    path('status/', login_required(views.SystemStatusView.as_view()), name='system_status'),
]