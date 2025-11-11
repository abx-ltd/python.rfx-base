"""
Notification Service - Provider Management and Notification Delivery
"""
from typing import Dict, Any, Optional

from .providers import NotificationProviderBase, SMTPEmailProvider, SendGridProvider, TwilioSMSProvider
from .types import (
    NotificationChannelEnum,
    ProviderTypeEnum,
    NotificationStatusEnum
)
from . import config, logger


class NotificationService:
    """
    Service for managing notification providers and sending notifications.
    """

    # Provider class registry
    PROVIDER_CLASSES = {
        ProviderTypeEnum.SMTP: SMTPEmailProvider,
        ProviderTypeEnum.SENDGRID: SendGridProvider,
        ProviderTypeEnum.TWILIO: TwilioSMSProvider,
        # Add more providers as needed
    }

    def __init__(self):
        self._provider_cache: Dict[ProviderTypeEnum, NotificationProviderBase] = {}

    async def send_notification(self, notification: Any) -> Dict[str, Any]:
        """
        Send a notification through the appropriate provider.

        Args:
            notification: Notification model instance

        Returns:
            Dictionary containing status, provider_message_id, response, and error
        """
        channel = NotificationChannelEnum(notification.channel)

        try:
            provider_type = self._determine_provider_type(notification, channel)
        except ValueError as exc:
            logger.error(str(exc))
            return {
                'status': NotificationStatusEnum.FAILED,
                'provider_type': None,
                'provider_message_id': None,
                'response': {},
                'error': str(exc)
            }

        provider_instance = self._get_provider_instance(provider_type)
        if not provider_instance:
            return {
                'status': NotificationStatusEnum.FAILED,
                'provider_type': provider_type.value,
                'provider_message_id': None,
                'response': {},
                'error': f'No provider implementation available for {provider_type.value}'
            }

        # Send notification
        try:
            result = await provider_instance.send(
                recipient=notification.recipient_address,
                subject=getattr(notification, 'subject', None),
                body=notification.body,
                content_type=notification.content_type,
                **self._extract_provider_kwargs(notification)
            )

            result['provider_type'] = provider_type.value
            return result

        except Exception as e:
            logger.error(f"Provider {provider_type.value} failed to send notification: {str(e)}")
            return {
                'status': NotificationStatusEnum.FAILED,
                'provider_type': provider_type.value,
                'provider_message_id': None,
                'response': {},
                'error': str(e)
            }

    async def check_notification_status(
        self,
        provider_key: str,
        provider_message_id: str
    ) -> Dict[str, Any]:
        """
        Check delivery status of a notification from the provider.

        Args:
            provider_key: Provider type key (e.g., SENDGRID)
            provider_message_id: Provider's message ID

        Returns:
            Dictionary with status information
        """
        try:
            provider_type = ProviderTypeEnum(provider_key)
        except ValueError:
            return {
                'status': NotificationStatusEnum.PENDING,
                'error': f'Unknown provider: {provider_key}'
            }

        provider_instance = self._get_provider_instance(provider_type)
        if not provider_instance:
            return {
                'status': NotificationStatusEnum.PENDING,
                'error': f'Failed to initialize provider: {provider_key}'
            }

        try:
            return await provider_instance.check_status(provider_message_id)
        except Exception as e:
            logger.error(f"Failed to check status from provider {provider_key}: {str(e)}")
            return {
                'status': NotificationStatusEnum.PENDING,
                'error': str(e)
            }

    def _determine_provider_type(
        self,
        notification: Any,
        channel: NotificationChannelEnum
    ) -> ProviderTypeEnum:
        """
        Resolve which provider type should handle this notification.
        Preference order:
        1. Explicit provider_type attribute on notification
        2. provider_type declared inside notification.meta
        3. Default mapping per channel using configured credentials
        """
        explicit_type = getattr(notification, 'provider_type', None)
        if explicit_type:
            return ProviderTypeEnum(explicit_type if isinstance(explicit_type, str) else explicit_type)

        meta = getattr(notification, 'meta', {}) or {}
        meta_type = meta.get('provider_type')
        if meta_type:
            return ProviderTypeEnum(meta_type if isinstance(meta_type, str) else meta_type)

        if channel == NotificationChannelEnum.EMAIL:
            if config.SENDGRID_API_KEY:
                return ProviderTypeEnum.SENDGRID
            if config.SMTP_HOST:
                return ProviderTypeEnum.SMTP
        elif channel == NotificationChannelEnum.SMS:
            if config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN:
                return ProviderTypeEnum.TWILIO

        raise ValueError(f"No provider configured for channel {channel.value}")

    def _get_provider_instance(self, provider_type: ProviderTypeEnum) -> Optional[NotificationProviderBase]:
        """
        Get an initialized provider instance.

        Args:
            provider_type: Provider type enum

        Returns:
            Provider class instance or None
        """
        if provider_type in self._provider_cache:
            return self._provider_cache[provider_type]

        provider_class = self.PROVIDER_CLASSES.get(provider_type)
        if not provider_class:
            logger.error(f"No provider class found for type: {provider_type}")
            return None

        provider_instance = provider_class()
        self._provider_cache[provider_type] = provider_instance
        return provider_instance

    def _extract_provider_kwargs(self, notification: Any) -> Dict[str, Any]:
        """
        Extract provider-specific kwargs from notification meta.

        Args:
            notification: Notification model instance

        Returns:
            Dictionary of provider-specific kwargs
        """
        kwargs = {}

        if hasattr(notification, 'meta') and notification.meta:
            # Extract common fields
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

        return kwargs

    async def validate_provider(self, provider_key: str) -> bool:
        """
        Validate a provider's configuration.

        Args:
            provider_key: Provider type key (e.g., SENDGRID)

        Returns:
            True if valid, False otherwise
        """
        try:
            provider_type = ProviderTypeEnum(provider_key)
        except ValueError:
            return False

        provider_instance = self._get_provider_instance(provider_type)
        if not provider_instance:
            return False

        try:
            return await provider_instance.validate_config()
        except Exception as e:
            logger.error(f"Provider validation failed: {str(e)}")
            return False
