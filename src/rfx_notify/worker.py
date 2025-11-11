"""
Worker tasks for notification sending.
Worker receives tasks, fetches notifications, sends via providers, updates state.

This is the single execution point for all notification sending -
the aggregate only queues tasks, the worker does the actual sending.
"""
from fluvius.worker import export_task
from fluvius.data import timestamp
from typing import Dict, Any

from .state import NotifyStateManager
from .service import NotificationService
from .types import NotificationStatusEnum, ProviderTypeEnum
from . import logger


@export_task(name='rfx_notify.send_notification')
async def send_notification_task(ctx, notification_id: str):
    """
    Worker task: Receive notification ID, fetch it, send it, update it, log it.
    This is the ONLY place where notifications actually get sent.

    Args:
        ctx: Worker context
        notification_id: ID of notification to send

    Returns:
        Dictionary with notification_id, status, provider info
    """
    statemgr = NotifyStateManager()
    notification_service = NotificationService()

    try:
        # 1. RECEIVE: Fetch the notification
        notification = await statemgr.fetch("notification", notification_id)
        if not notification:
            logger.error(f"Worker: Notification not found: {notification_id}")
            return {"status": "error", "message": "Notification not found"}

        logger.info(f"Worker received notification {notification_id} for sending")

        # Validate status
        if notification.status != NotificationStatusEnum.PENDING.value:
            logger.warning(
                f"Worker: Notification {notification_id} is not PENDING "
                f"(status: {notification.status})"
            )
            return {
                "status": "skipped",
                "message": f"Notification status is {notification.status}"
            }

        # 2. Update to PROCESSING
        await statemgr.update(notification, status=NotificationStatusEnum.PROCESSING.value)
        logger.info(f"Worker: Processing notification {notification_id}")

        # 3. SEND: Get provider and send (this calls external SaaS APIs)
        result = await notification_service.send_notification(notification)

        # 4. Parse result
        status = result.get('status', NotificationStatusEnum.FAILED)
        provider_type = result.get('provider_type')

        if provider_type and not isinstance(provider_type, ProviderTypeEnum):
            provider_type = ProviderTypeEnum(provider_type)

        # 5. UPDATE: Update notification with send result
        update_data = {
            'status': status.value,
            'provider_type': provider_type,
            'provider_message_id': result.get('provider_message_id'),
            'provider_response': result.get('response', {}),
        }

        if status == NotificationStatusEnum.SENT:
            update_data['sent_at'] = timestamp()
            logger.info(
                f"Worker: Notification {notification_id} sent successfully "
                f"via {provider_type.value if provider_type else 'unknown'}"
            )
        elif status == NotificationStatusEnum.FAILED:
            update_data['error_message'] = result.get('error', 'Unknown error')
            update_data['failed_at'] = timestamp()
            logger.error(
                f"Worker: Notification {notification_id} failed: "
                f"{result.get('error')}"
            )

        await statemgr.update(notification, **update_data)

        # 6. LOG: Log delivery attempt
        await _log_delivery_attempt(
            statemgr,
            notification_id,
            result,
            notification.retry_count + 1
        )

        return {
            "notification_id": notification_id,
            "status": status.value,
            "provider_message_id": result.get('provider_message_id'),
            "provider_type": provider_type.value if provider_type else None,
        }

    except Exception as e:
        logger.error(
            f"Worker: Exception while sending notification {notification_id}: {str(e)}",
            exc_info=True
        )

        # Update to failed
        try:
            notification = await statemgr.fetch("notification", notification_id)
            if notification:
                await statemgr.update(
                    notification,
                    status=NotificationStatusEnum.FAILED.value,
                    error_message=str(e),
                    failed_at=timestamp()
                )

                # Log failed attempt
                await _log_delivery_attempt(
                    statemgr,
                    notification_id,
                    {'status': NotificationStatusEnum.FAILED, 'error': str(e)},
                    notification.retry_count + 1
                )
        except Exception as log_error:
            logger.error(f"Worker: Failed to log error for {notification_id}: {str(log_error)}")

        raise


@export_task(name='rfx_notify.retry_notification')
async def retry_notification_task(ctx, notification_id: str):
    """
    Worker task: Retry a failed notification.

    Args:
        ctx: Worker context
        notification_id: ID of notification to retry

    Returns:
        Dictionary with retry result
    """
    statemgr = NotifyStateManager()
    notification_service = NotificationService()

    try:
        # Fetch notification
        notification = await statemgr.fetch("notification", notification_id)
        if not notification:
            logger.error(f"Worker: Notification not found for retry: {notification_id}")
            return {"status": "error", "message": "Notification not found"}

        logger.info(
            f"Worker: Retrying notification {notification_id} "
            f"(attempt {notification.retry_count + 1}/{notification.max_retries})"
        )

        # Check retry limit
        if notification.retry_count >= notification.max_retries:
            await statemgr.update(
                notification,
                status=NotificationStatusEnum.REJECTED.value,
                error_message="Max retries exceeded"
            )
            logger.warning(f"Worker: Notification {notification_id} exceeded max retries")
            return {"status": "rejected", "message": "Max retries exceeded"}

        # Increment retry count and update to processing
        retry_count = notification.retry_count + 1
        await statemgr.update(
            notification,
            retry_count=retry_count,
            status=NotificationStatusEnum.PROCESSING.value
        )

        # Send via provider
        result = await notification_service.send_notification(notification)

        # Update with result
        status = result.get('status', NotificationStatusEnum.FAILED)
        provider_type = result.get('provider_type')

        if provider_type and not isinstance(provider_type, ProviderTypeEnum):
            provider_type = ProviderTypeEnum(provider_type)

        update_data = {
            'status': status.value,
            'provider_type': provider_type,
            'provider_message_id': result.get('provider_message_id'),
            'provider_response': result.get('response', {}),
        }

        if status == NotificationStatusEnum.SENT:
            update_data['sent_at'] = timestamp()
        else:
            update_data['error_message'] = result.get('error', 'Unknown error')
            update_data['failed_at'] = timestamp()

        await statemgr.update(notification, **update_data)

        # Log retry attempt
        await _log_delivery_attempt(statemgr, notification_id, result, retry_count)

        logger.info(
            f"Worker: Retry result for notification {notification_id}: {status.value}"
        )

        return {
            "notification_id": notification_id,
            "status": status.value,
            "attempt": retry_count,
        }

    except Exception as e:
        logger.error(
            f"Worker: Exception during retry for notification {notification_id}: {str(e)}",
            exc_info=True
        )

        try:
            notification = await statemgr.fetch("notification", notification_id)
            if notification:
                await statemgr.update(
                    notification,
                    status=NotificationStatusEnum.FAILED.value,
                    error_message=str(e),
                    failed_at=timestamp()
                )
        except Exception as log_error:
            logger.error(f"Worker: Failed to update error status for {notification_id}: {str(log_error)}")

        raise


async def _log_delivery_attempt(
    statemgr: NotifyStateManager,
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
    provider_type = result.get('provider_type')
    if provider_type and not isinstance(provider_type, ProviderTypeEnum):
        provider_type = ProviderTypeEnum(provider_type)

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
        # Insert log directly without using init_resource since we're in worker
        await statemgr.insert_raw('notification_delivery_log', log_data)
    except Exception as e:
        logger.error(f"Worker: Failed to log delivery attempt for {notification_id}: {str(e)}")


def _extract_provider_params(notification) -> Dict[str, Any]:
    """
    Extract provider-specific parameters from notification metadata.

    Args:
        notification: Notification object

    Returns:
        Dictionary of provider-specific parameters
    """
    metadata = getattr(notification, 'metadata', {}) or {}
    return metadata.get('provider_params', {})
