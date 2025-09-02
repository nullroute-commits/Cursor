"""
Financial Permissions System

Enhanced RBAC permissions for financial data access and management.
Extends the core RBAC system with financial-specific permissions.
"""

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from app.core.rbac import Role, Permission as CorePermission
from .models import Account, Transaction, Category, Tag, Budget, Webhook


class FinancialPermissions:
    """Financial permission constants and management"""
    
    # Account Level Permissions
    VIEW_OWN_ACCOUNTS = "financial.view_own_accounts"
    VIEW_ALL_ACCOUNTS = "financial.view_all_accounts"
    CREATE_ACCOUNTS = "financial.create_accounts"
    EDIT_OWN_ACCOUNTS = "financial.edit_own_accounts"
    EDIT_ALL_ACCOUNTS = "financial.edit_all_accounts"
    DELETE_OWN_ACCOUNTS = "financial.delete_own_accounts"
    DELETE_ALL_ACCOUNTS = "financial.delete_all_accounts"
    
    # Transaction Level Permissions
    VIEW_OWN_TRANSACTIONS = "financial.view_own_transactions"
    VIEW_ALL_TRANSACTIONS = "financial.view_all_transactions"
    CREATE_TRANSACTIONS = "financial.create_transactions"
    EDIT_OWN_TRANSACTIONS = "financial.edit_own_transactions"
    EDIT_ALL_TRANSACTIONS = "financial.edit_all_transactions"
    DELETE_OWN_TRANSACTIONS = "financial.delete_own_transactions"
    DELETE_ALL_TRANSACTIONS = "financial.delete_all_transactions"
    RECONCILE_TRANSACTIONS = "financial.reconcile_transactions"
    
    # Category and Tag Permissions
    VIEW_CATEGORIES = "financial.view_categories"
    MANAGE_CATEGORIES = "financial.manage_categories"
    VIEW_TAGS = "financial.view_tags"
    MANAGE_TAGS = "financial.manage_tags"
    
    # Budget Permissions
    VIEW_OWN_BUDGETS = "financial.view_own_budgets"
    VIEW_ALL_BUDGETS = "financial.view_all_budgets"
    CREATE_BUDGETS = "financial.create_budgets"
    EDIT_OWN_BUDGETS = "financial.edit_own_budgets"
    EDIT_ALL_BUDGETS = "financial.edit_all_budgets"
    DELETE_OWN_BUDGETS = "financial.delete_own_budgets"
    DELETE_ALL_BUDGETS = "financial.delete_all_budgets"
    
    # Import Permissions
    VIEW_IMPORTS = "financial.view_imports"
    CREATE_IMPORTS = "financial.create_imports"
    MANAGE_IMPORTS = "financial.manage_imports"
    
    # Reporting Permissions
    VIEW_REPORTS = "financial.view_reports"
    CREATE_REPORTS = "financial.create_reports"
    EXPORT_REPORTS = "financial.export_reports"
    
    # Webhook Permissions
    VIEW_WEBHOOKS = "financial.view_webhooks"
    CREATE_WEBHOOKS = "financial.create_webhooks"
    EDIT_WEBHOOKS = "financial.edit_webhooks"
    DELETE_WEBHOOKS = "financial.delete_webhooks"
    
    # System Administration
    ADMIN_FINANCIAL_SYSTEM = "financial.admin_system"
    VIEW_AUDIT_LOGS = "financial.view_audit_logs"
    
    # All permissions list
    ALL_PERMISSIONS = [
        # Account permissions
        VIEW_OWN_ACCOUNTS, VIEW_ALL_ACCOUNTS, CREATE_ACCOUNTS,
        EDIT_OWN_ACCOUNTS, EDIT_ALL_ACCOUNTS, DELETE_OWN_ACCOUNTS, DELETE_ALL_ACCOUNTS,
        
        # Transaction permissions
        VIEW_OWN_TRANSACTIONS, VIEW_ALL_TRANSACTIONS, CREATE_TRANSACTIONS,
        EDIT_OWN_TRANSACTIONS, EDIT_ALL_TRANSACTIONS, DELETE_OWN_TRANSACTIONS, DELETE_ALL_TRANSACTIONS,
        RECONCILE_TRANSACTIONS,
        
        # Category and tag permissions
        VIEW_CATEGORIES, MANAGE_CATEGORIES, VIEW_TAGS, MANAGE_TAGS,
        
        # Budget permissions
        VIEW_OWN_BUDGETS, VIEW_ALL_BUDGETS, CREATE_BUDGETS,
        EDIT_OWN_BUDGETS, EDIT_ALL_BUDGETS, DELETE_OWN_BUDGETS, DELETE_ALL_BUDGETS,
        
        # Import permissions
        VIEW_IMPORTS, CREATE_IMPORTS, MANAGE_IMPORTS,
        
        # Reporting permissions
        VIEW_REPORTS, CREATE_REPORTS, EXPORT_REPORTS,
        
        # Webhook permissions
        VIEW_WEBHOOKS, CREATE_WEBHOOKS, EDIT_WEBHOOKS, DELETE_WEBHOOKS,
        
        # System permissions
        ADMIN_FINANCIAL_SYSTEM, VIEW_AUDIT_LOGS,
    ]


class FinancialPermissionManager:
    """Manager for financial permissions and role assignments"""
    
    @classmethod
    def create_financial_permissions(cls):
        """Create all financial permissions in the database"""
        content_type = ContentType.objects.get_for_model(Account)
        
        permissions_created = []
        
        for permission_codename in FinancialPermissions.ALL_PERMISSIONS:
            permission_name = permission_codename.replace('financial.', '').replace('_', ' ').title()
            
            permission, created = Permission.objects.get_or_create(
                codename=permission_codename,
                content_type=content_type,
                defaults={'name': permission_name}
            )
            
            if created:
                permissions_created.append(permission)
        
        return permissions_created
    
    @classmethod
    def create_financial_roles(cls):
        """Create default financial roles with appropriate permissions"""
        roles_created = []
        
        # Basic User Role - Can view and manage own financial data
        basic_user_role, created = Role.objects.get_or_create(
            name="Financial Basic User",
            defaults={'description': "Basic financial user with access to own accounts and transactions"}
        )
        if created:
            basic_user_role.permissions.add(
                Permission.objects.get(codename=FinancialPermissions.VIEW_OWN_ACCOUNTS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_OWN_TRANSACTIONS),
                Permission.objects.get(codename=FinancialPermissions.CREATE_TRANSACTIONS),
                Permission.objects.get(codename=FinancialPermissions.EDIT_OWN_TRANSACTIONS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_CATEGORIES),
                Permission.objects.get(codename=FinancialPermissions.VIEW_TAGS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_OWN_BUDGETS),
                Permission.objects.get(codename=FinancialPermissions.CREATE_BUDGETS),
                Permission.objects.get(codename=FinancialPermissions.EDIT_OWN_BUDGETS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_REPORTS),
                Permission.objects.get(codename=FinancialPermissions.CREATE_IMPORTS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_IMPORTS),
            )
            roles_created.append(basic_user_role)
        
        # Advanced User Role - Can manage categories and tags
        advanced_user_role, created = Role.objects.get_or_create(
            name="Financial Advanced User",
            defaults={'description': "Advanced financial user with category and tag management"}
        )
        if created:
            advanced_user_role.permissions.add(
                Permission.objects.get(codename=FinancialPermissions.VIEW_OWN_ACCOUNTS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_ALL_ACCOUNTS),
                Permission.objects.get(codename=FinancialPermissions.CREATE_ACCOUNTS),
                Permission.objects.get(codename=FinancialPermissions.EDIT_OWN_ACCOUNTS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_OWN_TRANSACTIONS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_ALL_TRANSACTIONS),
                Permission.objects.get(codename=FinancialPermissions.CREATE_TRANSACTIONS),
                Permission.objects.get(codename=FinancialPermissions.EDIT_OWN_TRANSACTIONS),
                Permission.objects.get(codename=FinancialPermissions.RECONCILE_TRANSACTIONS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_CATEGORIES),
                Permission.objects.get(codename=FinancialPermissions.MANAGE_CATEGORIES),
                Permission.objects.get(codename=FinancialPermissions.VIEW_TAGS),
                Permission.objects.get(codename=FinancialPermissions.MANAGE_TAGS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_OWN_BUDGETS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_ALL_BUDGETS),
                Permission.objects.get(codename=FinancialPermissions.CREATE_BUDGETS),
                Permission.objects.get(codename=FinancialPermissions.EDIT_OWN_BUDGETS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_REPORTS),
                Permission.objects.get(codename=FinancialPermissions.CREATE_REPORTS),
                Permission.objects.get(codename=FinancialPermissions.EXPORT_REPORTS),
                Permission.objects.get(codename=FinancialPermissions.CREATE_IMPORTS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_IMPORTS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_WEBHOOKS),
                Permission.objects.get(codename=FinancialPermissions.CREATE_WEBHOOKS),
                Permission.objects.get(codename=FinancialPermissions.EDIT_WEBHOOKS),
            )
            roles_created.append(advanced_user_role)
        
        # Manager Role - Can manage all financial data for their team
        manager_role, created = Role.objects.get_or_create(
            name="Financial Manager",
            defaults={'description': "Financial manager with team oversight capabilities"}
        )
        if created:
            manager_role.permissions.add(
                Permission.objects.get(codename=FinancialPermissions.VIEW_ALL_ACCOUNTS),
                Permission.objects.get(codename=FinancialPermissions.CREATE_ACCOUNTS),
                Permission.objects.get(codename=FinancialPermissions.EDIT_ALL_ACCOUNTS),
                Permission.objects.get(codename=FinancialPermissions.DELETE_OWN_ACCOUNTS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_ALL_TRANSACTIONS),
                Permission.objects.get(codename=FinancialPermissions.CREATE_TRANSACTIONS),
                Permission.objects.get(codename=FinancialPermissions.EDIT_ALL_TRANSACTIONS),
                Permission.objects.get(codename=FinancialPermissions.DELETE_OWN_TRANSACTIONS),
                Permission.objects.get(codename=FinancialPermissions.RECONCILE_TRANSACTIONS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_CATEGORIES),
                Permission.objects.get(codename=FinancialPermissions.MANAGE_CATEGORIES),
                Permission.objects.get(codename=FinancialPermissions.VIEW_TAGS),
                Permission.objects.get(codename=FinancialPermissions.MANAGE_TAGS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_ALL_BUDGETS),
                Permission.objects.get(codename=FinancialPermissions.CREATE_BUDGETS),
                Permission.objects.get(codename=FinancialPermissions.EDIT_ALL_BUDGETS),
                Permission.objects.get(codename=FinancialPermissions.DELETE_OWN_BUDGETS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_REPORTS),
                Permission.objects.get(codename=FinancialPermissions.CREATE_REPORTS),
                Permission.objects.get(codename=FinancialPermissions.EXPORT_REPORTS),
                Permission.objects.get(codename=FinancialPermissions.CREATE_IMPORTS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_IMPORTS),
                Permission.objects.get(codename=FinancialPermissions.MANAGE_IMPORTS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_WEBHOOKS),
                Permission.objects.get(codename=FinancialPermissions.CREATE_WEBHOOKS),
                Permission.objects.get(codename=FinancialPermissions.EDIT_WEBHOOKS),
                Permission.objects.get(codename=FinancialPermissions.DELETE_WEBHOOKS),
                Permission.objects.get(codename=FinancialPermissions.VIEW_AUDIT_LOGS),
            )
            roles_created.append(manager_role)
        
        # Administrator Role - Full system access
        admin_role, created = Role.objects.get_or_create(
            name="Financial Administrator",
            defaults={'description': "Financial system administrator with full access"}
        )
        if created:
            admin_role.permissions.add(*Permission.objects.filter(
                codename__in=FinancialPermissions.ALL_PERMISSIONS
            ))
            roles_created.append(admin_role)
        
        return roles_created


class FinancialPermissionMixin:
    """Mixin for views that require financial permissions"""
    
    def has_financial_permission(self, user, permission_codename):
        """Check if user has specific financial permission"""
        return user.has_perm(f"financial.{permission_codename}")
    
    def has_account_access(self, user, account, permission_type='view'):
        """Check if user has access to specific account"""
        if user.is_superuser:
            return True
        
        # Check if user owns the account
        if account.user == user:
            if permission_type == 'view':
                return self.has_financial_permission(user, FinancialPermissions.VIEW_OWN_ACCOUNTS)
            elif permission_type == 'edit':
                return self.has_financial_permission(user, FinancialPermissions.EDIT_OWN_ACCOUNTS)
            elif permission_type == 'delete':
                return self.has_financial_permission(user, FinancialPermissions.DELETE_OWN_ACCOUNTS)
        
        # Check if user has all accounts permission
        if permission_type == 'view':
            return self.has_financial_permission(user, FinancialPermissions.VIEW_ALL_ACCOUNTS)
        elif permission_type == 'edit':
            return self.has_financial_permission(user, FinancialPermissions.EDIT_ALL_ACCOUNTS)
        elif permission_type == 'delete':
            return self.has_financial_permission(user, FinancialPermissions.DELETE_ALL_ACCOUNTS)
        
        return False
    
    def has_transaction_access(self, user, transaction, permission_type='view'):
        """Check if user has access to specific transaction"""
        if user.is_superuser:
            return True
        
        # Check if user owns the transaction's account
        if transaction.account.user == user:
            if permission_type == 'view':
                return self.has_financial_permission(user, FinancialPermissions.VIEW_OWN_TRANSACTIONS)
            elif permission_type == 'edit':
                return self.has_financial_permission(user, FinancialPermissions.EDIT_OWN_TRANSACTIONS)
            elif permission_type == 'delete':
                return self.has_financial_permission(user, FinancialPermissions.DELETE_OWN_TRANSACTIONS)
        
        # Check if user has all transactions permission
        if permission_type == 'view':
            return self.has_financial_permission(user, FinancialPermissions.VIEW_ALL_TRANSACTIONS)
        elif permission_type == 'edit':
            return self.has_financial_permission(user, FinancialPermissions.EDIT_ALL_TRANSACTIONS)
        elif permission_type == 'delete':
            return self.has_financial_permission(user, FinancialPermissions.DELETE_ALL_TRANSACTIONS)
        
        return False


def require_financial_permission(permission_codename):
    """Decorator to require specific financial permission"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.has_perm(f"financial.{permission_codename}"):
                from django.contrib.auth.decorators import user_passes_test
                return user_passes_test(lambda u: False)(view_func)(request, *args, **kwargs)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_account_access(permission_type='view'):
    """Decorator to require account access permission"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            account_id = kwargs.get('account_id') or kwargs.get('pk')
            if account_id:
                try:
                    account = Account.objects.get(id=account_id)
                    mixin = FinancialPermissionMixin()
                    if not mixin.has_account_access(request.user, account, permission_type):
                        from django.contrib.auth.decorators import user_passes_test
                        return user_passes_test(lambda u: False)(view_func)(request, *args, **kwargs)
                except Account.DoesNotExist:
                    pass
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_transaction_access(permission_type='view'):
    """Decorator to require transaction access permission"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            transaction_id = kwargs.get('transaction_id') or kwargs.get('pk')
            if transaction_id:
                try:
                    transaction = Transaction.objects.get(id=transaction_id)
                    mixin = FinancialPermissionMixin()
                    if not mixin.has_transaction_access(request.user, transaction, permission_type):
                        from django.contrib.auth.decorators import user_passes_test
                        return user_passes_test(lambda u: False)(view_func)(request, *args, **kwargs)
                except Transaction.DoesNotExist:
                    pass
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator