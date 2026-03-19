"""
RFX Notify Domain Aggregate - Business Logic and State Management
"""
from fluvius.domain.aggregate import Aggregate, action
from fluvius.data import serialize_mapping, timestamp


from .types import NotificationStatusEnum, ProviderTypeEnum
from .service import NotificationService
from . import logger


class NotifyAggregate(Aggregate):
    """
    Aggregate for managing notification-related operations.
    Handles sending notifications through various channels (Email, SMS, Push, etc.)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._notification_service = None

    @property
    def notification_service(self) -> NotificationService:
        """Lazy-loaded notification service."""
        if self._notification_service is None:
            self._notification_service = NotificationService()
        return self._notification_service

    # ========================================================================
    # NOTIFICATION OPERATIONS
    # ========================================================================

    @action("notification-created", resources="notification")
    async def create_notification(self, *, data):
        """Create a new notification record."""
        notification_data = data
        notification_data['status'] = NotificationStatusEnum.PENDING

        notification = self.init_resource("notification", notification_data, _id=self.aggroot.identifier)
        await self.statemgr.insert(notification)

        return {
            "notification_id": notification._id,
            "status": notification.status
        }

    @action("notification-sent", resources="notification")
    async def send_notification(self, *, notification_id: str | None = None, data: dict | None = None):
        """
        Send notification through provider.
        Service handles the full flow: send, update status, log delivery.
        """
        if data is not None:
            logger.info("Sending notification from payload")
            return await self.notification_service.send_notification(data)

        if notification_id is None:
            raise ValueError("notification_id or data is required")

        notification = await self.statemgr.fetch("notification", notification_id)
        if not notification:
            raise ValueError(f"Notification not found: {notification_id}")

        if notification.status != NotificationStatusEnum.PENDING:
            raise ValueError(f"Notification {notification_id} is not in PENDING state")

        logger.info(f"Sending notification {notification_id}")

        # Delegate to service - it handles send, update, and logging
        return await self.notification_service.send_notification(notification)

    @action("notification-retried", resources="notification")
    async def retry_notification(self, *, notification_id: str):
        """
        Retry a failed notification.
        """
        notification = await self.statemgr.fetch("notification", notification_id)
        if not notification:
            raise ValueError(f"Notification not found: {notification_id}")

        if notification.status not in [NotificationStatusEnum.FAILED, NotificationStatusEnum.REJECTED]:
            raise ValueError(f"Notification {notification_id} is not in a retriable state")

        if notification.retry_count >= notification.max_retries:
            raise ValueError(f"Notification {notification_id} has exceeded max retries")

        logger.info(
            f"Retrying notification {notification_id} "
            f"(attempt {notification.retry_count + 1}/{notification.max_retries})"
        )

        # Increment retry count
        await self.statemgr.update(notification, retry_count=notification.retry_count + 1)

        # Refetch to get updated retry_count
        notification = await self.statemgr.fetch("notification", notification_id)

        # Delegate to service - it handles send, update, and logging
        result = await self.notification_service.send_notification(notification)

        result['attempt'] = notification.retry_count
        return result

    @action("notification-status-updated", resources="notification")
    async def update_notification_status(self, *, notification_id: str, status: str, **kwargs):
        """
        Update notification status (used for webhook callbacks from providers).
        """
        notification = await self.statemgr.fetch("notification", notification_id)
        if not notification:
            raise ValueError(f"Notification not found: {notification_id}")

        update_data = {'status': status}

        if status == NotificationStatusEnum.DELIVERED:
            update_data['delivered_at'] = timestamp()
        elif status == NotificationStatusEnum.FAILED:
            update_data['failed_at'] = timestamp()

        if 'error_message' in kwargs:
            update_data['error_message'] = kwargs['error_message']

        await self.statemgr.update(notification, **update_data)

        return {
            "notification_id": notification_id,
            "status": status
        }

    # ========================================================================
    # PREFERENCE OPERATIONS
    # ========================================================================

    @action("preference-updated", resources="notification_preference")
    async def update_user_preference(self, *, data):
        """Update user notification preferences."""
        user_id = self.context.user_id
        channel = data.get('channel')

        # Find existing preference
        existing = await self.statemgr.exist(
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



