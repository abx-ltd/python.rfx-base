"""
Commands for the RFX notification domain.
"""
from fluvius.data import serialize_mapping
from typing import Optional, List

from .domain import NotifyServiceDomain
from . import logger

from . import datadef

processor = NotifyServiceDomain.command_processor
Command = NotifyServiceDomain.Command


class SendNotification(Command):
    """
    Send a notification through Email, SMS, Push, or other channels.

    This command creates a notification record and sends it through
    the appropriate provider based on the channel.
    """

    class Meta:
        key = "send-notification"
        new_resource = True
        resources = ("notification",)
        tags = ["notification", "send"]
        auth_required = True
        policy_required = False



    Data = datadef.SendNotificationPayload

    async def _process(self, agg, stm, payload):
        try:
            notification_payload = serialize_mapping(payload)

            # 1. Create notification record
            create_result = await agg.create_notification(data=notification_payload)
            notification_id = create_result["notification_id"]

            # 2. Send notification
            send_result = await agg.send_notification(notification_id=notification_id)

            yield agg.create_response({
                "status": "success",
                "notification_id": notification_id,
                "delivery_status": send_result["status"],
                "provider_message_id": send_result.get("provider_message_id")
            }, _type="notify-service-response")

        except Exception as e:
            logger.error(f"SendNotification failed: {e}")
            yield agg.create_response({
                "status": "error",
                "error": str(e)
            }, _type="notify-service-response")
            raise


class RetryNotification(Command):
    """Retry sending a failed notification."""

    class Meta:
        key = "retry-notification"
        resources = ("notification",)
        tags = ["notification", "retry"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        try:
            notification_id = self.aggroot.identifier

            result = await agg.retry_notification(notification_id=notification_id)

            yield agg.create_response({
                "status": "success",
                "notification_id": notification_id,
                "attempt": result["attempt"],
                "delivery_status": result["status"]
            }, _type="notify-service-response")

        except Exception as e:
            logger.error(f"RetryNotification failed: {e}")
            yield agg.create_response({
                "status": "error",
                "error": str(e)
            }, _type="notify-service-response")
            raise


class UpdateNotificationStatus(Command):
    """
    Update notification status.
    Used for webhook callbacks from providers.
    """

    class Meta:
        key = "update-notification-status"
        resources = ("notification",)
        tags = ["notification", "status"]
        auth_required = False  # Webhooks may not have user auth
        policy_required = False

    Data = datadef.NotificationStatusUpdatePayload

    async def _process(self, agg, stm, payload):
        try:
            notification_id = self.aggroot.identifier
            status = payload.get('status')

            if not status:
                raise ValueError("Status is required")

            result = await agg.update_notification_status(
                notification_id=notification_id,
                status=status,
                **payload
            )

            yield agg.create_response({
                "status": "success",
                "notification_id": notification_id,
                "new_status": result["status"]
            }, _type="notify-service-response")

        except Exception as e:
            logger.error(f"UpdateNotificationStatus failed: {e}")
            yield agg.create_response({
                "status": "error",
                "error": str(e)
            }, _type="notify-service-response")
            raise


# Provider Management Commands

class CreateProvider(Command):
    """Create a new notification provider."""

    class Meta:
        key = "create-provider"
        new_resource = True
        resources = ("notification_provider",)
        tags = ["provider", "create"]
        auth_required = True
        policy_required = True  # Admins only

    Data = datadef.NotificationProviderPayload

    async def _process(self, agg, stm, payload):
        try:
            result = await agg.create_provider(data=serialize_mapping(payload))

            yield agg.create_response({
                "status": "success",
                "provider_id": result["provider_id"],
                "name": result["name"],
                "provider_type": result["provider_type"]
            }, _type="notify-service-response")

        except Exception as e:
            logger.error(f"CreateProvider failed: {e}")
            yield agg.create_response({
                "status": "error",
                "error": str(e)
            }, _type="notify-service-response")
            raise


class UpdateProvider(Command):
    """Update an existing notification provider."""

    class Meta:
        key = "update-provider"
        resources = ("notification_provider",)
        tags = ["provider", "update"]
        auth_required = True
        policy_required = True  # Admins only

    Data = datadef.NotificationProviderUpdatePayload

    async def _process(self, agg, stm, payload):
        try:
            result = await agg.update_provider(data=serialize_mapping(payload))

            yield agg.create_response({
                "status": "success",
                "provider_id": result["provider_id"],
                "name": result["name"]
            }, _type="notify-service-response")

        except Exception as e:
            logger.error(f"UpdateProvider failed: {e}")
            yield agg.create_response({
                "status": "error",
                "error": str(e)
            }, _type="notify-service-response")
            raise


class ChangeProviderStatus(Command):
    """Change provider status (activate/deactivate)."""

    class Meta:
        key = "change-provider-status"
        resources = ("notification_provider",)
        tags = ["provider", "status"]
        auth_required = True
        policy_required = True  # Admins only

    Data = datadef.ChangeProviderStatusPayload

    async def _process(self, agg, stm, payload):
        try:
            status = payload.get('status')

            if not status:
                raise ValueError("Status is required")

            result = await agg.change_provider_status(status=status)

            yield agg.create_response({
                "status": "success",
                "provider_id": result["provider_id"],
                "new_status": result["status"]
            }, _type="notify-service-response")

        except Exception as e:
            logger.error(f"ChangeProviderStatus failed: {e}")
            yield agg.create_response({
                "status": "error",
                "error": str(e)
            }, _type="notify-service-response")
            raise


# User Preference Commands

class UpdateNotificationPreference(Command):
    """Update user notification preferences."""

    class Meta:
        key = "update-notification-preference"
        new_resource = True
        resources = ("notification_preference",)
        tags = ["preference", "update"]
        auth_required = True
        policy_required = False

    Data = datadef.NotificationPreferencePayload

    async def _process(self, agg, stm, payload):
        try:
            result = await agg.update_user_preference(data=serialize_mapping(payload))

            yield agg.create_response({
                "status": "success",
                "user_id": result["user_id"],
                "channel": result["channel"],
                "updated": result.get("updated", False),
                "created": result.get("created", False)
            }, _type="notify-service-response")

        except Exception as e:
            logger.error(f"UpdateNotificationPreference failed: {e}")
            yield agg.create_response({
                "status": "error",
                "error": str(e)
            }, _type="notify-service-response")
            raise


# Template Management Commands

class CreateNotificationTemplate(Command):
    """Create a new notification template."""

    class Meta:
        key = "create-notification-template"
        new_resource = True
        resources = ("notification_template",)
        tags = ["template", "create"]
        auth_required = True
        policy_required = True  # Admins only

    Data = datadef.NotificationTemplatePayload

    async def _process(self, agg, stm, payload):
        try:
            result = await agg.create_notification_template(data=serialize_mapping(payload))

            yield agg.create_response({
                "status": "success",
                "template_id": result["template_id"],
                "key": result["key"],
                "version": result["version"]
            }, _type="notify-service-response")

        except Exception as e:
            logger.error(f"CreateNotificationTemplate failed: {e}")
            yield agg.create_response({
                "status": "error",
                "error": str(e)
            }, _type="notify-service-response")
            raise


class ActivateNotificationTemplate(Command):
    """Activate a notification template."""

    class Meta:
        key = "activate-notification-template"
        resources = ("notification_template",)
        tags = ["template", "activate"]
        auth_required = True
        policy_required = True  # Admins only

    async def _process(self, agg, stm, payload):
        try:
            result = await agg.activate_notification_template()

            yield agg.create_response({
                "status": "success",
                "template_id": result["template_id"],
                "is_active": result["is_active"]
            }, _type="notify-service-response")

        except Exception as e:
            logger.error(f"ActivateNotificationTemplate failed: {e}")
            yield agg.create_response({
                "status": "error",
                "error": str(e)
            }, _type="notify-service-response")
            raise


class DeactivateNotificationTemplate(Command):
    """Deactivate a notification template."""

    class Meta:
        key = "deactivate-notification-template"
        resources = ("notification_template",)
        tags = ["template", "deactivate"]
        auth_required = True
        policy_required = True  # Admins only

    async def _process(self, agg, stm, payload):
        try:
            result = await agg.deactivate_notification_template()

            yield agg.create_response({
                "status": "success",
                "template_id": result["template_id"],
                "is_active": result["is_active"]
            }, _type="notify-service-response")

        except Exception as e:
            logger.error(f"DeactivateNotificationTemplate failed: {e}")
            yield agg.create_response({
                "status": "error",
                "error": str(e)
            }, _type="notify-service-response")
            raise
