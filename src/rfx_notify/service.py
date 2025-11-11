"""
Notification Service - Provider Management and Notification Delivery
"""
from typing import Dict, Any, Optional, List
from fluvius.data import DataAccessManager

from .providers import NotificationProviderBase, SMTPEmailProvider, SendGridProvider, TwilioSMSProvider
from .types import (
    NotificationChannelEnum,
    ProviderTypeEnum,
    ProviderStatusEnum,
    NotificationStatusEnum
)
from . import logger


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

    def __init__(self, stm: DataAccessManager):
        self.stm = stm
        self._provider_cache = {}

    async def send_notification(self, notification: Any) -> Dict[str, Any]:
        """
        Send a notification through the appropriate provider.

        Args:
            notification: Notification model instance

        Returns:
            Dictionary containing status, provider_message_id, response, and error
        """
        channel = NotificationChannelEnum(notification.channel)
        provider = None

        # Try to use specified provider if provided
        if hasattr(notification, 'provider_id') and notification.provider_id:
            provider = await self._get_provider(notification.provider_id)

        # Otherwise, find best available provider for this channel
        if not provider:
            provider = await self._find_best_provider(channel)

        if not provider:
            return {
                'status': NotificationStatusEnum.FAILED,
                'provider_id': None,
                'provider_message_id': None,
                'response': {},
                'error': f'No available provider for channel: {channel.value}'
            }

        # Get provider instance
        provider_instance = await self._get_provider_instance(provider)

        if not provider_instance:
            return {
                'status': NotificationStatusEnum.FAILED,
                'provider_id': provider._id,
                'provider_message_id': None,
                'response': {},
                'error': f'Failed to initialize provider: {provider.name}'
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

            result['provider_id'] = provider._id
            return result

        except Exception as e:
            logger.error(f"Provider {provider.name} failed to send notification: {str(e)}")
            return {
                'status': NotificationStatusEnum.FAILED,
                'provider_id': provider._id,
                'provider_message_id': None,
                'response': {},
                'error': str(e)
            }

    async def check_notification_status(
        self,
        provider_id: str,
        provider_message_id: str
    ) -> Dict[str, Any]:
        """
        Check delivery status of a notification from the provider.

        Args:
            provider_id: ID of the provider
            provider_message_id: Provider's message ID

        Returns:
            Dictionary with status information
        """
        provider = await self._get_provider(provider_id)
        if not provider:
            return {
                'status': NotificationStatusEnum.PENDING,
                'error': f'Provider not found: {provider_id}'
            }

        provider_instance = await self._get_provider_instance(provider)
        if not provider_instance:
            return {
                'status': NotificationStatusEnum.PENDING,
                'error': f'Failed to initialize provider: {provider.name}'
            }

        try:
            return await provider_instance.check_status(provider_message_id)
        except Exception as e:
            logger.error(f"Failed to check status from provider {provider.name}: {str(e)}")
            return {
                'status': NotificationStatusEnum.PENDING,
                'error': str(e)
            }

    async def _find_best_provider(self, channel: NotificationChannelEnum) -> Optional[Any]:
        """
        Find the best available provider for a given channel.
        Considers priority and status.

        Args:
            channel: Notification channel

        Returns:
            Provider model instance or None
        """
        providers = await self.stm.find_all(
            "notification_provider",
            where={
                'channel': channel.value,
                'status': ProviderStatusEnum.ACTIVE.value
            },
            order_by=['priority']  # Lower priority number = higher priority
        )

        # Return first active provider (highest priority)
        return providers[0] if providers else None

    async def _get_provider(self, provider_id: str) -> Optional[Any]:
        """
        Get a provider by ID.

        Args:
            provider_id: Provider ID

        Returns:
            Provider model instance or None
        """
        try:
            return await self.stm.fetch("notification_provider", provider_id)
        except Exception as e:
            logger.error(f"Failed to fetch provider {provider_id}: {str(e)}")
            return None

    async def _get_provider_instance(self, provider: Any) -> Optional[NotificationProviderBase]:
        """
        Get an initialized provider instance.

        Args:
            provider: Provider model instance

        Returns:
            Provider class instance or None
        """
        try:
            provider_type = ProviderTypeEnum(provider.provider_type)
            provider_class = self.PROVIDER_CLASSES.get(provider_type)

            if not provider_class:
                logger.error(f"No provider class found for type: {provider_type}")
                return None

            # Prepare config
            config = {
                'credentials': provider.credentials or {},
                'settings': provider.config or {},
                **provider.config or {}
            }

            # Create and return provider instance
            return provider_class(config)

        except Exception as e:
            logger.error(f"Failed to initialize provider instance: {str(e)}")
            return None

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

    async def validate_provider(self, provider_id: str) -> bool:
        """
        Validate a provider's configuration.

        Args:
            provider_id: Provider ID

        Returns:
            True if valid, False otherwise
        """
        provider = await self._get_provider(provider_id)
        if not provider:
            return False

        provider_instance = await self._get_provider_instance(provider)
        if not provider_instance:
            return False

        try:
            return await provider_instance.validate_config()
        except Exception as e:
            logger.error(f"Provider validation failed: {str(e)}")
            return False

    async def get_active_providers(self, channel: Optional[NotificationChannelEnum] = None) -> List[Any]:
        """
        Get all active providers, optionally filtered by channel.

        Args:
            channel: Optional channel filter

        Returns:
            List of provider model instances
        """
        where = {'status': ProviderStatusEnum.ACTIVE.value}

        if channel:
            where['channel'] = channel.value

        return await self.stm.find_all(
            "notification_provider",
            where=where,
            order_by=['priority']
        )
