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
