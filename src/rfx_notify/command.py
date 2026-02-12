"""
Commands for the RFX notification domain.
"""

from fluvius.data import serialize_mapping

from .domain import NotifyServiceDomain
from . import datadef, logger
from .types import NotificationChannelEnum


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
        resource_init = True
        resources = ("notification",)
        tags = ["notification", "send"]
        auth_required = True
        policy_required = False

    Data = datadef.SendNotificationPayload

    async def _process(self, agg, stm, payload):
        try:
            notification_payload = serialize_mapping(payload)
            recipients = notification_payload.get("recipients") or []
            notification_payload["recipients"] = recipients
            template_key = notification_payload.get("template_key")

            context = {
                key: notification_payload.get(key)
                for key in ("tenant_id", "app_id", "locale")
                if notification_payload.get(key) is not None
            }

            if template_key:
                channel = NotificationChannelEnum(notification_payload["channel"])
                template_data = notification_payload.get("template_data", {}) or {}
                template_version = notification_payload.get("template_version")

                if not recipients:
                    raise ValueError("Recipients list cannot be empty")

                # Render template via rfx-template domain
                template_client = self.context.service_proxy.ttp_client

                response = await template_client.request(
                    "rfx-template:render-template",
                    command="render-template",
                    resource="template",
                    payload={
                        "key": template_key,
                        "data": template_data,
                        "tenant_id": context.get("tenant_id"),
                        "app_id": context.get("app_id"),
                        "locale": context.get("locale", "en"),
                        "channel": channel.value,
                        "version": template_version,
                    },
                    _headers={},
                    _context={
                        "audit": {
                            "user_id": str(self.context.user_id) if self.context.user_id else None,
                            "profile_id": str(self.context.profile_id) if self.context.profile_id else None,
                        },
                        "source": "rfx-notify",
                    },
                )

                # Extract rendered content from template-service-response
                service_response = response.get("template-service-response", response)
                rendered_body = service_response.get('body', '')
                rendered_subject = service_response.get('subject')  # May be None

                # Create notification payload for each recipient
                results = []
                for recipient in recipients:
                    rendered_payload = {
                        **notification_payload,
                        "body": rendered_body,
                        "recipients": [recipient],
                    }
                    if rendered_subject:
                        rendered_payload["subject"] = rendered_subject

                    # Remove template fields as we now have rendered content
                    rendered_payload.pop("template_key", None)
                    rendered_payload.pop("template_data", None)
                    rendered_payload.pop("template_version", None)

                    send_result = await agg.send_notification(data=rendered_payload)
                    results.append(send_result)

                send_result = {"count": len(results), "results": results}
            else:
                # Send notification (provider will create the record)
                if not recipients:
                    raise ValueError("Recipients list cannot be empty")
                send_result = await agg.send_notification(data=notification_payload)

            yield agg.create_response(
                {
                    "status": "success",
                    "notification_id": send_result.get("notification_id"),
                    "delivery_status": send_result.get("status"),
                    "provider_message_id": send_result.get("provider_message_id"),
                    "results": send_result.get("results"),
                    "count": send_result.get("count"),
                },
                _type="notify-service-response",
            )

        except Exception as e:
            logger.error(f"SendNotification failed: {e}")
            yield agg.create_response(
                {"status": "error", "error": str(e)}, _type="notify-service-response"
            )
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

            yield agg.create_response(
                {
                    "status": "success",
                    "notification_id": notification_id,
                    "attempt": result["attempt"],
                    "delivery_status": result["status"],
                },
                _type="notify-service-response",
            )

        except Exception as e:
            logger.error(f"RetryNotification failed: {e}")
            yield agg.create_response(
                {"status": "error", "error": str(e)}, _type="notify-service-response"
            )
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
            status = payload.get("status")

            if not status:
                raise ValueError("Status is required")

            result = await agg.update_notification_status(
                notification_id=notification_id, status=status, **payload
            )

            yield agg.create_response(
                {
                    "status": "success",
                    "notification_id": notification_id,
                    "new_status": result["status"],
                },
                _type="notify-service-response",
            )

        except Exception as e:
            logger.error(f"UpdateNotificationStatus failed: {e}")
            yield agg.create_response(
                {"status": "error", "error": str(e)}, _type="notify-service-response"
            )
            raise


# User Preference Commands


class UpdateNotificationPreference(Command):
    """Update user notification preferences."""

    class Meta:
        key = "update-notification-preference"
        resource_init = True
        resources = ("notification_preference",)
        tags = ["preference", "update"]
        auth_required = True
        policy_required = False

    Data = datadef.NotificationPreferencePayload

    async def _process(self, agg, stm, payload):
        try:
            result = await agg.update_user_preference(data=serialize_mapping(payload))

            yield agg.create_response(
                {
                    "status": "success",
                    "user_id": result["user_id"],
                    "channel": result["channel"],
                    "updated": result.get("updated", False),
                    "created": result.get("created", False),
                },
                _type="notify-service-response",
            )

        except Exception as e:
            logger.error(f"UpdateNotificationPreference failed: {e}")
            yield agg.create_response(
                {"status": "error", "error": str(e)}, _type="notify-service-response"
            )
            raise


# Template Management Commands
