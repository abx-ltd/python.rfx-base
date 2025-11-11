"""
Base notification provider interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..types import NotificationStatusEnum
from .. import config


class NotificationProviderBase(ABC):
    """
    Abstract base class for all notification providers.
    All provider implementations must inherit from this class.
    """

    def __init__(self):
        """
        Base providers pull their configuration directly from rfx_notify config.
        """
        super().__init__()

    async def send_and_update(
        self,
        notification: Any,
        statemgr: Any
    ) -> Dict[str, Any]:
        """
        Complete send flow: update status, send, update result, log delivery.
        This is the high-level method that orchestrates the entire process.

        Args:
            notification: Notification model instance
            statemgr: State manager for database operations

        Returns:
            Dictionary with notification_id, status, provider info
        """
        from fluvius.data import timestamp

        notification_id = notification._id
        attempt_number = notification.retry_count + 1

        # Update to PROCESSING
        await statemgr.update(notification, status=NotificationStatusEnum.PROCESSING.value)

        try:
            # Send via provider implementation
            result = await self.send(
                recipient=notification.recipient_address,
                subject=getattr(notification, 'subject', None),
                body=notification.body,
                content_type=notification.content_type,
                **self._extract_kwargs(notification)
            )

            # Parse result
            status = result.get('status', NotificationStatusEnum.FAILED)
            provider_type = result.get('provider_type')

            # Update notification with send result
            update_data = {
                'status': status.value if hasattr(status, 'value') else status,
                'provider_type': provider_type,
                'provider_message_id': result.get('provider_message_id'),
                'provider_response': result.get('response', {}),
            }

            if status == NotificationStatusEnum.SENT:
                update_data['sent_at'] = timestamp()
            elif status == NotificationStatusEnum.FAILED:
                update_data['error_message'] = result.get('error', 'Unknown error')
                update_data['failed_at'] = timestamp()

            await statemgr.update(notification, **update_data)

            # Log delivery attempt
            await self._log_delivery_attempt(statemgr, notification_id, result, attempt_number)

            return {
                "notification_id": notification_id,
                "status": status.value if hasattr(status, 'value') else status,
                "provider_message_id": result.get('provider_message_id'),
                "provider_type": provider_type,
            }

        except Exception as e:
            from .. import logger
            logger.error(f"Exception while sending notification {notification_id}: {str(e)}", exc_info=True)

            # Update to failed
            await statemgr.update(
                notification,
                status=NotificationStatusEnum.FAILED.value,
                error_message=str(e),
                failed_at=timestamp()
            )

            # Log failed attempt
            await self._log_delivery_attempt(
                statemgr,
                notification_id,
                {'status': NotificationStatusEnum.FAILED, 'error': str(e), 'provider_type': self.provider_type},
                attempt_number
            )

            raise

    @abstractmethod
    async def send(
        self,
        recipient: str,
        subject: Optional[str],
        body: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a notification through this provider.

        Args:
            recipient: Recipient address (email, phone, etc.)
            subject: Subject/title of the notification (optional for SMS)
            body: Body content of the notification
            **kwargs: Additional provider-specific parameters

        Returns:
            Dictionary containing:
                - status: NotificationStatusEnum
                - provider_message_id: External provider's message ID
                - response: Full provider response
                - error: Error message if failed
        """
        pass

    @abstractmethod
    async def check_status(self, provider_message_id: str) -> Dict[str, Any]:
        """
        Check delivery status of a sent notification.

        Args:
            provider_message_id: The ID returned by the provider

        Returns:
            Dictionary containing status and delivery information
        """
        pass

    @abstractmethod
    async def validate_config(self) -> bool:
        """
        Validate that the provider configuration is correct.

        Returns:
            True if configuration is valid, False otherwise
        """
        pass

    @property
    @abstractmethod
    def provider_type(self):
        """
        Return the provider type enum.
        Must be implemented by subclasses.
        """
        pass

    def supports_delivery_confirmation(self) -> bool:
        """
        Check if this provider supports delivery confirmation.

        Returns:
            True if provider can confirm delivery
        """
        return False

    def get_rate_limits(self) -> Dict[str, int]:
        """
        Get rate limits for this provider.

        Returns:
            Dictionary with rate limit information
        """
        return {
            'per_minute': config.NOTIFY_RATE_LIMIT_PER_MINUTE,
            'per_hour': config.NOTIFY_RATE_LIMIT_PER_HOUR,
            'per_day': config.NOTIFY_RATE_LIMIT_PER_DAY,
        }

    def _extract_kwargs(self, notification: Any) -> Dict[str, Any]:
        """
        Extract provider-specific kwargs from notification meta.

        Args:
            notification: Notification model instance

        Returns:
            Dictionary of provider-specific kwargs
        """
        kwargs = {}

        if hasattr(notification, 'meta') and notification.meta:
            meta = notification.meta
            if 'from_email' in meta:
                kwargs['from_email'] = meta['from_email']
            if 'from_number' in meta:
                kwargs['from_number'] = meta['from_number']
            if 'cc' in meta:
                kwargs['cc'] = meta['cc']
            if 'bcc' in meta:
                kwargs['bcc'] = meta['bcc']
            if 'media_url' in meta:
                kwargs['media_url'] = meta['media_url']
            if 'dlr_url' in meta:
                kwargs['dlr_url'] = meta['dlr_url']

        return kwargs

    async def _log_delivery_attempt(
        self,
        statemgr: Any,
        notification_id: str,
        result: Dict[str, Any],
        attempt_number: int
    ):
        """
        Helper to log delivery attempt to the database.

        Args:
            statemgr: State manager instance
            notification_id: Notification ID
            result: Result from provider send
            attempt_number: Attempt number
        """
        from fluvius.data import timestamp
        from .. import logger
        from ..types import ProviderTypeEnum

        provider_type = result.get('provider_type')
        if provider_type and not isinstance(provider_type, ProviderTypeEnum):
            try:
                provider_type = ProviderTypeEnum(provider_type)
            except:
                pass

        status = result.get('status', NotificationStatusEnum.FAILED)

        log_data = {
            'notification_id': notification_id,
            'provider_type': provider_type,
            'attempt_number': attempt_number,
            'attempted_at': timestamp(),
            'status': status.value if hasattr(status, 'value') else status,
            'response': result.get('response', {}),
            'error_message': result.get('error'),
        }

        try:
            await statemgr.add_notification_log(**log_data)
        except Exception as e:
            logger.error(f"Failed to log delivery attempt for {notification_id}: {str(e)}")
