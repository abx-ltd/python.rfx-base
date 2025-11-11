"""
RFX Notify Domain Aggregate - Business Logic and State Management
"""
from fluvius.domain.aggregate import Aggregate, action
from fluvius.data import serialize_mapping, timestamp
from typing import Optional, Dict, Any
from datetime import datetime

from .service import NotificationService
from .processor import NotificationContentProcessor
from .template import NotificationTemplateService
from .types import NotificationStatusEnum, NotificationChannelEnum
from . import logger


class NotifyAggregate(Aggregate):
    """
    Aggregate for managing notification-related operations.
    Handles sending notifications through various channels (Email, SMS, Push, etc.)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._notification_service = None
        self._content_processor = None
        self._template_service = None

    @property
    def notification_service(self) -> NotificationService:
        """Lazy-loaded notification service."""
        if self._notification_service is None:
            self._notification_service = NotificationService()
        return self._notification_service

    @property
    def content_processor(self) -> NotificationContentProcessor:
        """Lazy-loaded content processor."""
        if self._content_processor is None:
            self._content_processor = NotificationContentProcessor(self.statemgr)
        return self._content_processor

    @property
    def template_service(self) -> NotificationTemplateService:
        """Lazy-loaded template service."""
        if self._template_service is None:
            self._template_service = NotificationTemplateService(self.statemgr)
        return self._template_service

    # ========================================================================
    # NOTIFICATION OPERATIONS
    # ========================================================================

    @action("notification-created", resources="notification")
    async def create_notification(self, *, data):
        """Create a new notification record."""
        notification_data = data
        notification_data['status'] = NotificationStatusEnum.PENDING.value

        notification = self.init_resource("notification", notification_data, _id=self.aggroot.identifier)
        await self.statemgr.insert(notification)

        return {
            "notification_id": notification._id,
            "status": notification.status
        }

    @action("notification-sent", resources="notification")
    async def send_notification(self, *, notification_id: str):
        """
        Send a notification through the appropriate provider.
        """
        notification = await self.statemgr.fetch("notification", notification_id)
        if not notification:
            raise ValueError(f"Notification not found: {notification_id}")

        if notification.status != NotificationStatusEnum.PENDING:
            raise ValueError(f"Notification {notification_id} is not in PENDING state")

        # Update status to processing
        await self.statemgr.update(notification, status=NotificationStatusEnum.PROCESSING.value)

        try:
            # Send through notification service
            result = await self.notification_service.send_notification(notification)

            # Update notification with result
            update_data = {
                'status': result['status'].value,
                'sent_at': timestamp() if result['status'] == NotificationStatusEnum.SENT else None,
                'provider_message_id': result.get('provider_message_id'),
                'provider_response': result.get('response', {}),
            }

            if result.get('error'):
                update_data['error_message'] = result['error']
                update_data['failed_at'] = timestamp()

            await self.statemgr.update(notification, **update_data)

            # Log delivery attempt
            await self._log_delivery_attempt(notification_id, result, 1)

            return {
                "notification_id": notification_id,
                "status": result['status'].value,
                "provider_message_id": result.get('provider_message_id')
            }

        except Exception as e:
            logger.error(f"Failed to send notification {notification_id}: {str(e)}")
            await self.statemgr.update(
                notification,
                status=NotificationStatusEnum.FAILED.value,
                error_message=str(e),
                failed_at=timestamp()
            )
            raise

    @action("notification-retried", resources="notification")
    async def retry_notification(self, *, notification_id: str):
        """
        Retry sending a failed notification.
        """
        notification = await self.statemgr.fetch("notification", notification_id)
        if not notification:
            raise ValueError(f"Notification not found: {notification_id}")

        if notification.status not in [NotificationStatusEnum.FAILED.value, NotificationStatusEnum.REJECTED.value]:
            raise ValueError(f"Notification {notification_id} is not in a retriable state")

        if notification.retry_count >= notification.max_retries:
            raise ValueError(f"Notification {notification_id} has exceeded max retries")

        # Increment retry count
        await self.statemgr.update(
            notification,
            retry_count=notification.retry_count + 1,
            status=NotificationStatusEnum.PROCESSING.value
        )

        try:
            # Send through notification service
            result = await self.notification_service.send_notification(notification)

            # Update notification with result
            update_data = {
                'status': result['status'].value,
                'sent_at': timestamp() if result['status'] == NotificationStatusEnum.SENT else None,
                'provider_message_id': result.get('provider_message_id'),
                'provider_response': result.get('response', {}),
            }

            if result.get('error'):
                update_data['error_message'] = result['error']
                update_data['failed_at'] = timestamp()

            await self.statemgr.update(notification, **update_data)

            # Log delivery attempt
            await self._log_delivery_attempt(notification_id, result, notification.retry_count)

            return {
                "notification_id": notification_id,
                "status": result['status'].value,
                "attempt": notification.retry_count
            }

        except Exception as e:
            logger.error(f"Failed to retry notification {notification_id}: {str(e)}")
            await self.statemgr.update(
                notification,
                status=NotificationStatusEnum.FAILED.value,
                error_message=str(e),
                failed_at=timestamp()
            )
            raise

    @action("notification-status-updated", resources="notification")
    async def update_notification_status(self, *, notification_id: str, status: str, **kwargs):
        """
        Update notification status (used for webhook callbacks from providers).
        """
        notification = await self.statemgr.fetch("notification", notification_id)
        if not notification:
            raise ValueError(f"Notification not found: {notification_id}")

        update_data = {'status': status}

        if status == NotificationStatusEnum.DELIVERED.value:
            update_data['delivered_at'] = timestamp()
        elif status == NotificationStatusEnum.FAILED.value:
            update_data['failed_at'] = timestamp()

        if 'error_message' in kwargs:
            update_data['error_message'] = kwargs['error_message']

        await self.statemgr.update(notification, **update_data)

        return {
            "notification_id": notification_id,
            "status": status
        }

    async def _log_delivery_attempt(self, notification_id: str, result: Dict[str, Any], attempt_number: int):
        """
        Log a delivery attempt to the delivery log table.
        """
        log_data = {
            'notification_id': notification_id,
            'provider_id': result.get('provider_id'),
            'attempt_number': attempt_number,
            'attempted_at': timestamp(),
            'status': result['status'].value,
            'response': result.get('response', {}),
            'error_message': result.get('error'),
        }

        log_record = self.init_resource("notification_delivery_log", log_data)
        await self.statemgr.insert(log_record)

    # ========================================================================
    # PREFERENCE OPERATIONS
    # ========================================================================

    @action("preference-updated", resources="notification_preference")
    async def update_user_preference(self, *, data):
        """Update user notification preferences."""
        user_id = self.context.user_id
        channel = data.get('channel')

        # Find existing preference
        existing = await self.statemgr.find_one(
            "notification_preference",
            where={'user_id': user_id, 'channel': channel}
        )

        if existing:
            await self.statemgr.update(existing, **data)
            return {
                "user_id": user_id,
                "channel": channel,
                "updated": True
            }
        else:
            preference_data = {**data, 'user_id': user_id}
            preference = self.init_resource("notification_preference", preference_data)
            await self.statemgr.insert(preference)

            return {
                "user_id": user_id,
                "channel": channel,
                "created": True
            }

    # ========================================================================
    # TEMPLATE OPERATIONS
    # ========================================================================

    @action("notification-template-created", resources="notification_template")
    async def create_notification_template(self, *, data):
        """Create a new notification template."""
        template_data = serialize_mapping(data)

        # Use template service to create
        template = await self.template_service.create_template(
            key=template_data['key'],
            channel=template_data['channel'],
            body_template=template_data['body_template'],
            subject_template=template_data.get('subject_template'),
            name=template_data.get('name'),
            engine=template_data.get('engine', 'jinja2'),
            locale=template_data.get('locale', 'en'),
            content_type=template_data.get('content_type', 'TEXT'),
            tenant_id=template_data.get('tenant_id'),
            app_id=template_data.get('app_id'),
            variables_schema=template_data.get('variables_schema'),
        )

        return {
            "template_id": template._id,
            "key": template.key,
            "version": template.version
        }

    @action("notification-template-activated", resources="notification_template")
    async def activate_notification_template(self):
        """Activate a notification template."""
        template_id = self.aggroot.identifier
        template = await self.template_service.activate_template(template_id)

        return {
            "template_id": template._id,
            "is_active": template.is_active
        }

    @action("notification-template-deactivated", resources="notification_template")
    async def deactivate_notification_template(self):
        """Deactivate a notification template."""
        template_id = self.aggroot.identifier
        template = await self.template_service.deactivate_template(template_id)

        return {
            "template_id": template._id,
            "is_active": template.is_active
        }
