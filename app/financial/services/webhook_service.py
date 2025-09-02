"""
Webhook Service

Handles webhook event publishing, delivery, and retry logic for external integrations.
Integrates with the existing RabbitMQ message queue system.
"""

import json
import logging
import hashlib
import hmac
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
import requests
from ..models import Webhook, WebhookDelivery
from app.core.audit import audit_logger
from app.core.queue import task_queue
from django.db.models import Count, Q
from django.db.models.functions import F

logger = logging.getLogger(__name__)


class WebhookEventPublisher:
    """Publishes webhook events to the message queue"""
    
    @staticmethod
    def publish_event(event_type: str, payload: Dict[str, Any], user_id: Optional[int] = None):
        """Publish a webhook event to the queue"""
        try:
            event_data = {
                'event_type': event_type,
                'payload': payload,
                'user_id': user_id,
                'timestamp': timezone.now().isoformat(),
                'event_id': f"{event_type}_{int(time.time())}"
            }
            
            # Publish to RabbitMQ queue
            task_queue.publish(
                'webhook_events',
                event_data,
                routing_key='webhook.event'
            )
            
            audit_logger.info(
                f"Published webhook event: {event_type}",
                extra={
                    'event_type': event_type,
                    'user_id': user_id,
                    'event_id': event_data['event_id']
                }
            )
            
            return event_data['event_id']
            
        except Exception as e:
            logger.error(f"Failed to publish webhook event {event_type}: {e}")
            audit_logger.error(
                f"Failed to publish webhook event: {event_type}",
                extra={
                    'event_type': event_type,
                    'user_id': user_id,
                    'error': str(e)
                }
            )
            raise
    
    @staticmethod
    def publish_transaction_event(transaction, event_type: str):
        """Publish transaction-related webhook events"""
        payload = {
            'transaction_id': str(transaction.id),
            'account_id': str(transaction.account.id),
            'description': transaction.description,
            'amount': str(transaction.amount),
            'transaction_type': transaction.transaction_type,
            'transaction_date': transaction.transaction_date.isoformat(),
            'category': transaction.category.name if transaction.category else None,
            'tags': [tag.name for tag in transaction.tags.all()],
            'reference_number': transaction.reference_number,
            'check_number': transaction.check_number,
            'notes': transaction.notes,
            'is_reconciled': transaction.is_reconciled,
            'created_at': transaction.created_at.isoformat(),
            'updated_at': transaction.updated_at.isoformat()
        }
        
        return WebhookEventPublisher.publish_event(
            f"transaction.{event_type}",
            payload,
            transaction.account.user.id
        )
    
    @staticmethod
    def publish_account_event(account, event_type: str):
        """Publish account-related webhook events"""
        payload = {
            'account_id': str(account.id),
            'name': account.name,
            'account_type': account.account_type,
            'balance': str(account.balance),
            'currency': account.currency,
            'institution': account.institution.name if account.institution else None,
            'is_active': account.is_active,
            'created_at': account.created_at.isoformat(),
            'updated_at': account.updated_at.isoformat()
        }
        
        return WebhookEventPublisher.publish_event(
            f"account.{event_type}",
            payload,
            account.user.id
        )
    
    @staticmethod
    def publish_budget_event(budget, event_type: str):
        """Publish budget-related webhook events"""
        payload = {
            'budget_id': str(budget.id),
            'name': budget.name,
            'period_type': budget.period_type,
            'start_date': budget.start_date.isoformat(),
            'end_date': budget.end_date.isoformat(),
            'total_amount': str(budget.total_amount),
            'is_active': budget.is_active,
            'created_at': budget.created_at.isoformat(),
            'updated_at': budget.updated_at.isoformat()
        }
        
        return WebhookEventPublisher.publish_event(
            f"budget.{event_type}",
            payload,
            budget.user.id
        )
    
    @staticmethod
    def publish_import_event(import_history, event_type: str):
        """Publish import-related webhook events"""
        payload = {
            'import_id': str(import_history.id),
            'filename': import_history.filename,
            'file_type': import_history.file_type,
            'status': import_history.status,
            'total_records': import_history.total_records,
            'processed_records': import_history.processed_records,
            'failed_records': import_history.failed_records,
            'started_at': import_history.started_at.isoformat() if import_history.started_at else None,
            'completed_at': import_history.completed_at.isoformat() if import_history.completed_at else None,
            'created_at': import_history.created_at.isoformat()
        }
        
        return WebhookEventPublisher.publish_event(
            f"import.{event_type}",
            payload,
            import_history.user.id
        )


class WebhookDeliveryService:
    """Handles webhook delivery and retry logic"""
    
    def __init__(self, webhook: Webhook):
        self.webhook = webhook
        self.session = requests.Session()
        self.session.timeout = webhook.timeout
    
    def deliver_webhook(self, event_type: str, payload: Dict[str, Any]) -> WebhookDelivery:
        """Deliver a webhook to the configured URL"""
        # Create delivery record
        delivery = WebhookDelivery.objects.create(
            webhook=self.webhook,
            event_type=event_type,
            payload=payload,
            status='pending'
        )
        
        try:
            # Prepare request data
            request_data = self._prepare_request_data(event_type, payload)
            
            # Send webhook
            response = self._send_webhook(request_data)
            
            # Update delivery record
            delivery.status = 'sent' if response.successful else 'failed'
            delivery.response_code = response.status_code
            delivery.response_body = response.text[:1000]  # Limit response body size
            delivery.delivered_at = timezone.now()
            delivery.attempt_count += 1
            
            if not response.successful:
                delivery.error_message = f"HTTP {response.status_code}: {response.reason}"
                delivery.status = 'failed'
            
            delivery.save()
            
            # Update webhook statistics
            self._update_webhook_stats(response.successful)
            
            # Log delivery
            audit_logger.info(
                f"Webhook delivered: {self.webhook.name} - {event_type}",
                extra={
                    'webhook_id': str(self.webhook.id),
                    'delivery_id': str(delivery.id),
                    'event_type': event_type,
                    'response_code': response.status_code,
                    'success': response.successful
                }
            )
            
            return delivery
            
        except Exception as e:
            # Handle delivery failure
            delivery.status = 'failed'
            delivery.error_message = str(e)
            delivery.attempt_count += 1
            delivery.save()
            
            logger.error(f"Webhook delivery failed: {self.webhook.name} - {event_type}: {e}")
            
            # Schedule retry if attempts remaining
            if delivery.attempt_count < self.webhook.retry_count:
                self._schedule_retry(delivery)
            
            return delivery
    
    def _prepare_request_data(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare webhook request data with headers and signature"""
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'FinancialApp-Webhook/1.0',
            'X-Webhook-Event': event_type,
            'X-Webhook-ID': str(self.webhook.id),
            'X-Webhook-Timestamp': str(int(time.time()))
        }
        
        # Add signature if secret key is configured
        if self.webhook.secret_key:
            signature = self._generate_signature(payload, self.webhook.secret_key)
            headers['X-Webhook-Signature'] = signature
        
        # Prepare request data
        request_data = {
            'url': self.webhook.url,
            'method': 'POST',
            'headers': headers,
            'json': payload
        }
        
        return request_data
    
    def _generate_signature(self, payload: Dict[str, Any], secret_key: str) -> str:
        """Generate HMAC signature for webhook payload"""
        payload_str = json.dumps(payload, cls=DjangoJSONEncoder, sort_keys=True)
        signature = hmac.new(
            secret_key.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    def _send_webhook(self, request_data: Dict[str, Any]) -> requests.Response:
        """Send the webhook HTTP request"""
        try:
            response = self.session.post(
                request_data['url'],
                headers=request_data['headers'],
                json=request_data['json']
            )
            return response
            
        except requests.exceptions.Timeout:
            raise Exception("Webhook delivery timeout")
        except requests.exceptions.ConnectionError:
            raise Exception("Webhook delivery connection error")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Webhook delivery request error: {e}")
    
    def _update_webhook_stats(self, success: bool):
        """Update webhook statistics"""
        self.webhook.last_triggered = timezone.now()
        if not success:
            self.webhook.failure_count += 1
        self.webhook.save()
    
    def _schedule_retry(self, delivery: WebhookDelivery):
        """Schedule a retry for failed webhook delivery"""
        # Calculate exponential backoff delay
        delay_minutes = min(2 ** (delivery.attempt_count - 1), 60)  # Max 60 minutes
        
        delivery.next_retry = timezone.now() + timedelta(minutes=delay_minutes)
        delivery.status = 'retrying'
        delivery.save()
        
        # Schedule retry task
        task_queue.publish(
            'webhook_retries',
            {
                'delivery_id': str(delivery.id),
                'retry_at': delivery.next_retry.isoformat()
            },
            routing_key='webhook.retry',
            delay=delay_minutes * 60  # Convert to seconds
        )


class WebhookManager:
    """Manages webhook operations and event routing"""
    
    @staticmethod
    def get_active_webhooks_for_event(event_type: str, user_id: Optional[int] = None) -> List[Webhook]:
        """Get active webhooks that should receive a specific event type"""
        query = Webhook.objects.filter(
            is_active=True,
            events__contains=[event_type]
        )
        
        if user_id:
            query = query.filter(user_id=user_id)
        
        return list(query)
    
    @staticmethod
    def deliver_event_to_webhooks(event_type: str, payload: Dict[str, Any], user_id: Optional[int] = None):
        """Deliver an event to all relevant webhooks"""
        webhooks = WebhookManager.get_active_webhooks_for_event(event_type, user_id)
        
        deliveries = []
        for webhook in webhooks:
            try:
                delivery_service = WebhookDeliveryService(webhook)
                delivery = delivery_service.deliver_webhook(event_type, payload)
                deliveries.append(delivery)
                
            except Exception as e:
                logger.error(f"Failed to deliver webhook {webhook.name}: {e}")
                
                # Create failed delivery record
                delivery = WebhookDelivery.objects.create(
                    webhook=webhook,
                    event_type=event_type,
                    payload=payload,
                    status='failed',
                    error_message=str(e),
                    attempt_count=1
                )
                deliveries.append(delivery)
        
        return deliveries
    
    @staticmethod
    def retry_failed_deliveries():
        """Retry all failed webhook deliveries"""
        failed_deliveries = WebhookDelivery.objects.filter(
            status='failed',
            attempt_count__lt=F('webhook__retry_count')
        ).select_related('webhook')
        
        retried_count = 0
        for delivery in failed_deliveries:
            try:
                delivery_service = WebhookDeliveryService(delivery.webhook)
                delivery_service.deliver_webhook(delivery.event_type, delivery.payload)
                retried_count += 1
                
            except Exception as e:
                logger.error(f"Retry failed for delivery {delivery.id}: {e}")
        
        return retried_count
    
    @staticmethod
    def cleanup_old_deliveries(days_old: int = 90):
        """Clean up old webhook delivery records"""
        cutoff_date = timezone.now() - timedelta(days=days_old)
        deleted_count, _ = WebhookDelivery.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old webhook delivery records")
        return deleted_count


class WebhookEventProcessor:
    """Process webhook events from the message queue"""
    
    @staticmethod
    @task_queue.task
    def process_webhook_event(event_data: Dict[str, Any]):
        """Process a webhook event from the queue"""
        try:
            event_type = event_data['event_type']
            payload = event_data['payload']
            user_id = event_data.get('user_id')
            
            # Deliver to relevant webhooks
            deliveries = WebhookManager.deliver_event_to_webhooks(
                event_type, payload, user_id
            )
            
            # Log processing
            audit_logger.info(
                f"Processed webhook event: {event_type}",
                extra={
                    'event_type': event_type,
                    'user_id': user_id,
                    'deliveries_count': len(deliveries),
                    'event_id': event_data.get('event_id')
                }
            )
            
            return {
                'success': True,
                'event_type': event_type,
                'deliveries_count': len(deliveries)
            }
            
        except Exception as e:
            logger.error(f"Failed to process webhook event: {e}")
            audit_logger.error(
                f"Failed to process webhook event",
                extra={
                    'event_data': event_data,
                    'error': str(e)
                }
            )
            
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    @task_queue.task
    def retry_webhook_delivery(delivery_id: str):
        """Retry a specific webhook delivery"""
        try:
            delivery = WebhookDelivery.objects.get(id=delivery_id)
            
            if delivery.status == 'retrying' and delivery.next_retry <= timezone.now():
                delivery_service = WebhookDeliveryService(delivery.webhook)
                delivery_service.deliver_webhook(delivery.event_type, delivery.payload)
                
                return {
                    'success': True,
                    'delivery_id': delivery_id,
                    'status': delivery.status
                }
            else:
                return {
                    'success': False,
                    'error': 'Delivery not ready for retry'
                }
                
        except WebhookDelivery.DoesNotExist:
            return {
                'success': False,
                'error': 'Delivery not found'
            }
        except Exception as e:
            logger.error(f"Failed to retry webhook delivery {delivery_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class WebhookHealthChecker:
    """Monitor webhook health and performance"""
    
    @staticmethod
    def check_webhook_health(webhook: Webhook) -> Dict[str, Any]:
        """Check the health of a specific webhook"""
        try:
            # Test webhook endpoint
            response = requests.get(
                webhook.url,
                timeout=webhook.timeout,
                headers={'User-Agent': 'FinancialApp-HealthCheck/1.0'}
            )
            
            health_status = {
                'webhook_id': str(webhook.id),
                'webhook_name': webhook.name,
                'url': webhook.url,
                'status': 'healthy' if response.status_code < 400 else 'unhealthy',
                'response_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'last_check': timezone.now().isoformat()
            }
            
            # Update webhook statistics
            if response.status_code >= 400:
                webhook.failure_count += 1
                webhook.save()
            
            return health_status
            
        except Exception as e:
            health_status = {
                'webhook_id': str(webhook.id),
                'webhook_name': webhook.name,
                'url': webhook.url,
                'status': 'unhealthy',
                'error': str(e),
                'last_check': timezone.now().isoformat()
            }
            
            # Update failure count
            webhook.failure_count += 1
            webhook.save()
            
            return health_status
    
    @staticmethod
    def get_webhook_statistics() -> Dict[str, Any]:
        """Get overall webhook statistics"""
        total_webhooks = Webhook.objects.count()
        active_webhooks = Webhook.objects.filter(is_active=True).count()
        
        # Get delivery statistics
        delivery_stats = WebhookDelivery.objects.aggregate(
            total_deliveries=Count('id'),
            successful_deliveries=Count('id', filter=Q(status='sent')),
            failed_deliveries=Count('id', filter=Q(status='failed')),
            pending_deliveries=Count('id', filter=Q(status='pending')),
            retrying_deliveries=Count('id', filter=Q(status='retrying'))
        )
        
        # Calculate success rate
        total_deliveries = delivery_stats['total_deliveries'] or 0
        success_rate = 0
        if total_deliveries > 0:
            success_rate = (delivery_stats['successful_deliveries'] or 0) / total_deliveries * 100
        
        return {
            'total_webhooks': total_webhooks,
            'active_webhooks': active_webhooks,
            'delivery_statistics': delivery_stats,
            'success_rate': round(success_rate, 2),
            'last_updated': timezone.now().isoformat()
        }