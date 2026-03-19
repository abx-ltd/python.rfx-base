"""
Notification Service - Provider Management and Notification Delivery
"""
from typing import Dict, Any, Optional

from .providers import NotificationProviderBase
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

    # Provider registry mapping between ProviderTypeEnum and provider registry names
    PROVIDER_NAMES = {
        ProviderTypeEnum.SMTP: "smtp",
        ProviderTypeEnum.KANNEL: "kannel",
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
        channel_value = self._get_field(notification, "channel")
        channel = NotificationChannelEnum(channel_value)

        provider_type = self._determine_provider_type(notification, channel)
        provider_instance = self._get_provider_instance(provider_type)
        if not provider_instance:
            raise ValueError(f'No provider implementation available for {provider_type.value}')

        result = await provider_instance.send(notification)
        return result

    async def check_notification_status(
        self,
        provider_key: str,
        provider_message_id: str
    ) -> Dict[str, Any]:
        """
        Check delivery status of a notification from the provider.

        Args:
            provider_key: Provider type key (e.g., SMTP, KANNEL)
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
        explicit_type = self._get_field(notification, 'provider_type')
        if explicit_type:
            return ProviderTypeEnum(explicit_type if isinstance(explicit_type, str) else explicit_type)

        meta = self._get_field(notification, 'meta', {}) or {}
        meta_type = meta.get('provider_type')
        if meta_type:
            return ProviderTypeEnum(meta_type if isinstance(meta_type, str) else meta_type)

        if channel == NotificationChannelEnum.EMAIL:
            if config.SMTP_HOST:
                return ProviderTypeEnum.SMTP
        elif channel == NotificationChannelEnum.SMS:
            if config.KANNEL_HOST:
                return ProviderTypeEnum.KANNEL

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

        provider_name = self.PROVIDER_NAMES.get(provider_type)
        if not provider_name:
            logger.error(f"No provider registered for type: {provider_type}")
            return None

        try:
            provider_instance = NotificationProviderBase.init_provider(provider_name)
        except ValueError:
            logger.error(f"Provider [{provider_name}] is not registered.")
            return None
        except Exception as exc:
            logger.error(f"Provider [{provider_name}] failed to initialize: {exc}")
            return None

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

        meta = self._get_field(notification, 'meta')
        if meta:
            # Extract common fields
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

    @staticmethod
    def _get_field(notification: Any, field: str, default: Any = None) -> Any:
        if isinstance(notification, dict):
            return notification.get(field, default)

        return getattr(notification, field, default)

    async def validate_provider(self, provider_key: str) -> bool:
        """
        Validate a provider's configuration.

        Args:
            provider_key: Provider type key (e.g., SMTP, KANNEL)

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
