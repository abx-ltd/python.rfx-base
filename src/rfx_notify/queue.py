"""
Notification queue service abstraction.

Domain defines the interface, implementation is injected from outside (app layer).
This follows dependency inversion principle - domain doesn't depend on worker.
"""
from abc import ABC, abstractmethod
from typing import Optional


class NotificationQueueService(ABC):
    """
    Abstract interface for queueing notification tasks.

    Implementation is provided by the application layer and injected at startup.
    This allows the domain to queue tasks without knowing about worker implementation.
    """

    @abstractmethod
    async def queue_send_notification(self, notification_id: str) -> str:
        """
        Queue a notification for sending.

        Args:
            notification_id: Notification ID to send

        Returns:
            Task ID from the queue system
        """
        pass

    @abstractmethod
    async def queue_retry_notification(self, notification_id: str) -> str:
        """
        Queue a notification for retry.

        Args:
            notification_id: Notification ID to retry

        Returns:
            Task ID from the queue system
        """
        pass


# Global queue service instance (injected at startup)
_queue_service: Optional[NotificationQueueService] = None


def set_queue_service(service: NotificationQueueService):
    """
    Set the global queue service implementation.

    This should be called once at application startup (in worker bootstrap or API startup).

    Args:
        service: Implementation of NotificationQueueService
    """
    global _queue_service
    _queue_service = service


def get_queue_service() -> NotificationQueueService:
    """
    Get the current queue service implementation.

    Returns:
        The injected queue service instance

    Raises:
        RuntimeError: If queue service hasn't been initialized
    """
    if _queue_service is None:
        raise RuntimeError(
            "NotificationQueueService not initialized. "
            "Call set_queue_service() during application startup."
        )
    return _queue_service
