"""
Base notification provider interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..state import NotifyStateManager

from .. import logger, config


class NotificationProviderBase(ABC):
    """
    Abstract base class for all notification providers.
    All provider implementations must inherit from this class.
    """
    __REGISTRY__ = {}
    __CONFIG_CLS__ = None
    name = None

    def __init__(self, provider_config: Optional[Any] = None):
        """
        Base providers accept configuration explicitly on init.
        """
        super().__init__()
        if provider_config is None:
            provider_config = self.build_config()
        self.provider_config = self._init_config_model(provider_config)
        self.statemgr = NotifyStateManager(None)

    def __init_subclass__(cls):
        if not getattr(cls, "name", None):
            raise ValueError(f"Provider subclass [{cls.__name__}] must define a unique `name`.")

        if cls.name in cls.__REGISTRY__:
            raise ValueError(f"Provider [{cls.name}] already registered.")

        cls.__REGISTRY__[cls.name] = cls

    def _init_config_model(self, provider_config):
        if not self.__CONFIG_CLS__:
            return None

        if provider_config is None:
            raise ValueError(
                f"Provider [{self.__class__.__name__}] requires an explicit config instance."
            )

        if isinstance(provider_config, self.__CONFIG_CLS__):
            return provider_config

        if isinstance(provider_config, dict):
            return self.__CONFIG_CLS__(**provider_config)

        if hasattr(provider_config, "model_dump"):
            return self.__CONFIG_CLS__(**provider_config.model_dump())

        if hasattr(provider_config, "dict"):
            return self.__CONFIG_CLS__(**provider_config.dict())

        raise TypeError(
            f"Unsupported config type for [{self.__class__.__name__}]: {type(provider_config)}"
        )

    @classmethod
    def init_provider(cls, name, **params):
        if name not in cls.__REGISTRY__:
            raise ValueError("Not Found")

        return cls.__REGISTRY__[name](**params)

    @abstractmethod
    def build_config(self) -> Any:
        """
        Build a provider-specific config instance or dict.
        """
        pass

    @abstractmethod
    async def send(self, notification: Any) -> Dict[str, Any]:
        """
        Send a notification through this provider.

        Args:
            notification: Notification model or payload data.

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

        if isinstance(notification, dict):
            meta = notification.get('meta')
        else:
            meta = getattr(notification, 'meta', None)
        if meta:
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
