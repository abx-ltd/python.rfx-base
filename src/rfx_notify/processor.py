"""
Notification Content Processor
Handles template resolution and rendering for notifications
"""
from typing import Dict, Any, Optional
from datetime import datetime

from fluvius.data import DataAccessManager, DataModel

from .template import NotificationTemplateService
from .types import NotificationChannelEnum, ContentTypeEnum
from . import logger


class NotificationContentProcessor:
    """Handles notification content resolution and rendering."""

    def __init__(self, stm: DataAccessManager):
        self.stm = stm
        self.template_service = NotificationTemplateService(stm)

    async def process_notification_content(
        self,
        notification: DataModel,
        *,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process notification content based on type.

        Flow:
        1. Check if direct content is provided (no template needed)
        2. Resolve template if template_key is provided
        3. Render content with template data
        4. Return processed content

        Args:
            notification: Notification model instance
            context: Optional context (tenant_id, app_id, locale)

        Returns:
            Dictionary with subject and body
        """
        try:
            # If direct content is provided, use it as-is
            if notification.body and not notification.template_key:
                return {
                    'subject': getattr(notification, 'subject', None),
                    'body': notification.body,
                    'content_type': notification.content_type
                }

            # Template-based content processing
            if notification.template_key:
                return await self._process_template_content(notification, context or {})

            raise ValueError("Notification must have either body or template_key")

        except Exception as e:
            logger.error(f"Content processing failed for notification {notification._id}: {e}")
            raise

    async def _process_template_content(
        self,
        notification: DataModel,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process notification with template-based content.

        Args:
            notification: Notification model instance
            context: Template resolution context

        Returns:
            Dictionary with rendered subject and body
        """
        channel = NotificationChannelEnum(notification.channel)

        # Resolve template
        template = await self.template_service.resolve_template(
            notification.template_key,
            channel=channel.value,
            tenant_id=context.get('tenant_id'),
            app_id=context.get('app_id'),
            locale=context.get('locale'),
            version=getattr(notification, 'template_version', None)
        )

        if not template:
            raise ValueError(
                f"Template not found: {notification.template_key} "
                f"for channel {channel.value}"
            )

        # Get template data
        template_data = getattr(notification, 'template_data', {}) or {}

        # Add system variables
        template_data.update({
            'notification_id': notification._id,
            'timestamp': datetime.utcnow().isoformat(),
            'recipient_id': getattr(notification, 'recipient_id', None),
            'recipient_address': notification.recipient_address,
            # Add more system variables as needed
        })

        # Render template
        rendered = await self.template_service.render_template(template, template_data)

        # Determine content type from template
        content_type = template.get('content_type', ContentTypeEnum.TEXT.value)

        logger.info(
            f"Rendered notification {notification._id} using template "
            f"{template['key']} v{template['version']}"
        )

        return {
            'subject': rendered.get('subject'),
            'body': rendered['body'],
            'content_type': content_type,
            'template_version': template['version'],
            'template_locale': template.get('locale', 'en')
        }

    async def prepare_notification_with_template(
        self,
        channel: NotificationChannelEnum,
        template_key: str,
        template_data: Dict[str, Any],
        recipient_address: str,
        *,
        recipient_id: Optional[str] = None,
        sender_id: Optional[str] = None,
        priority: str = "NORMAL",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Helper method to prepare a notification with template rendering.
        Useful for creating notifications with templates in one step.

        Args:
            channel: Notification channel
            template_key: Template key
            template_data: Data for template rendering
            recipient_address: Recipient address (email, phone, etc.)
            recipient_id: Optional recipient user ID
            sender_id: Optional sender user ID
            priority: Priority level
            context: Optional context for template resolution

        Returns:
            Dictionary with notification data ready to be saved
        """
        # Resolve template
        template = await self.template_service.resolve_template(
            template_key,
            channel=channel.value,
            **(context or {})
        )

        if not template:
            raise ValueError(
                f"Template not found: {template_key} for channel {channel.value}"
            )

        # Add system variables
        enriched_data = {
            **template_data,
            'timestamp': datetime.utcnow().isoformat(),
            'recipient_address': recipient_address,
        }

        # Render template
        rendered = await self.template_service.render_template(template, enriched_data)

        # Prepare notification data
        notification_data = {
            'channel': channel.value,
            'recipient_id': recipient_id,
            'sender_id': sender_id,
            'recipient_address': recipient_address,
            'subject': rendered.get('subject'),
            'body': rendered['body'],
            'content_type': template.get('content_type', ContentTypeEnum.TEXT.value),
            'priority': priority,
            'template_key': template_key,
            'template_version': template['version'],
            'template_data': template_data,
            'status': 'PENDING'
        }

        return notification_data
