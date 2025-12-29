"""
Email notification providers - Self-hosted SMTP infrastructure
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

from fluvius.data.data_model import DataModel
from fluvius.data import UUID_GENR, timestamp

from .base import NotificationProviderBase
from ..types import NotificationStatusEnum, ContentTypeEnum, ProviderTypeEnum
from .. import logger, config


class SMTPEmailProviderConfig(DataModel):
    smtp_host: str
    smtp_port: int = 25
    smtp_use_tls: bool = False
    smtp_use_ssl: bool = False
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_timeout: int = 30


class SMTPEmailProvider(NotificationProviderBase):
    name = "smtp"

    __CONFIG_CLS__ = SMTPEmailProviderConfig
    """
    SMTP email provider for sending emails through self-hosted SMTP server.
    The SMTP server (Postfix, Haraka, etc.) runs on the worker machine.
    """

    def __init__(self, provider_config: Optional[Any] = None):
        super().__init__(provider_config=provider_config)

    def build_config(self) -> Any:
        return {
            "smtp_host": config.SMTP_HOST,
            "smtp_port": config.SMTP_PORT,
            "smtp_use_tls": config.SMTP_USE_TLS,
            "smtp_use_ssl": config.SMTP_USE_SSL,
            "smtp_username": config.SMTP_USERNAME,
            "smtp_password": config.SMTP_PASSWORD,
            "smtp_from_email": config.SMTP_FROM_EMAIL,
            "smtp_timeout": config.SMTP_TIMEOUT,
        }

    async def send(self, notification: Any) -> Dict[str, Any]:
        """
        Send an email via self-hosted SMTP server.

        Args:
            notification: Notification payload or model
        """
        def get_field(field, default=None):
            if isinstance(notification, dict):
                return notification.get(field, default)
            return getattr(notification, field, default)

        def enum_value(value):
            return value.value if hasattr(value, "value") else value

        recipients = get_field("recipients") or get_field("recipient_address")
        if not recipients:
            raise ValueError("Missing recipient address.")

        if isinstance(recipients, (list, tuple, set)):
            recipients = [recipient for recipient in recipients if recipient]
        else:
            recipients = [recipients]

        results = []
        is_bulk = len(recipients) > 1

        for recipient in recipients:
            async with self.statemgr.transaction():
                entry = None
                if not is_bulk:
                    if isinstance(notification, dict) and notification.get("_id"):
                        entry = await self.statemgr.fetch("notification", notification["_id"])
                    elif get_field("_id"):
                        entry = notification

                if entry is None:
                    data = {
                        "_id": UUID_GENR(),
                        "channel": enum_value(get_field("channel")),
                        "recipient_address": recipient,
                        "subject": get_field("subject"),
                        "body": get_field("body"),
                        "content_type": enum_value(get_field("content_type")),
                        "recipient_id": get_field("recipient_id"),
                        "sender_id": get_field("sender_id"),
                        "provider_type": self.provider_type.value,
                        "priority": enum_value(get_field("priority")),
                        "scheduled_at": get_field("scheduled_at"),
                        "template_key": get_field("template_key"),
                        "template_version": get_field("template_version"),
                        "template_data": get_field("template_data", {}),
                        "meta": get_field("meta", {}),
                        "tags": get_field("tags", []),
                        "max_retries": get_field("max_retries", 0),
                        "retry_count": 0,
                        "status": NotificationStatusEnum.PENDING.value,
                    }
                    entry = self.statemgr.create("notification", data)
                    await self.statemgr.insert(entry)

                await self.statemgr.update(
                    entry,
                    status=NotificationStatusEnum.PROCESSING.value,
                )

            attempt_number = entry.retry_count + 1
            meta = getattr(entry, "meta", None) or {}
            from_email = meta.get('from_email') or self.provider_config.smtp_from_email
            content_type = getattr(entry, "content_type", None)

            try:
                if not from_email:
                    raise ValueError("SMTP_FROM_EMAIL is not configured")

                if isinstance(content_type, str):
                    try:
                        resolved_content_type = ContentTypeEnum(content_type)
                    except ValueError:
                        resolved_content_type = ContentTypeEnum.HTML
                else:
                    resolved_content_type = content_type or ContentTypeEnum.HTML

                if resolved_content_type == ContentTypeEnum.HTML:
                    message = MIMEMultipart('alternative')
                    message.attach(MIMEText(entry.body or "", 'html'))
                else:
                    message = MIMEText(entry.body or "", 'plain')

                message['Subject'] = entry.subject or ''
                message['From'] = from_email
                message['To'] = recipient

                if 'cc' in meta:
                    message['Cc'] = meta['cc']
                if 'bcc' in meta:
                    message['Bcc'] = meta['bcc']

                logger.info(
                    f"Connecting to self-hosted SMTP server at {self.provider_config.smtp_host}:{self.provider_config.smtp_port}"
                )

                use_tls = self.provider_config.smtp_use_ssl or self.provider_config.smtp_use_tls
                async with aiosmtplib.SMTP(
                    hostname=self.provider_config.smtp_host,
                    port=self.provider_config.smtp_port,
                    use_tls=use_tls,
                    timeout=self.provider_config.smtp_timeout,
                ) as smtp:
                    if self.provider_config.smtp_username and self.provider_config.smtp_password:
                        await smtp.login(self.provider_config.smtp_username, self.provider_config.smtp_password)

                    send_result = await smtp.send_message(message)

                result = {
                    'status': NotificationStatusEnum.SENT,
                    'provider_type': self.provider_type,
                    'provider_message_id': message.get('Message-ID'),
                    'response': {
                        'smtp_response': str(send_result),
                        'recipient': recipient,
                        'smtp_host': self.provider_config.smtp_host,
                    },
                    'error': None
                }

            except aiosmtplib.SMTPException as e:
                logger.error(f"SMTP error sending to {recipient}: {str(e)}")
                result = {
                    'status': NotificationStatusEnum.FAILED,
                    'provider_type': self.provider_type,
                    'provider_message_id': None,
                    'response': {},
                    'error': f"SMTP error: {str(e)}"
                }
            except Exception as e:
                logger.error(f"Unexpected error sending email to {recipient}: {str(e)}")
                result = {
                    'status': NotificationStatusEnum.FAILED,
                    'provider_type': self.provider_type,
                    'provider_message_id': None,
                    'response': {},
                    'error': str(e)
                }

            status = result.get('status', NotificationStatusEnum.FAILED)
            provider_type = result.get('provider_type', self.provider_type)

            update_data = {
                'status': enum_value(status),
                'provider_type': enum_value(provider_type),
                'provider_message_id': result.get('provider_message_id'),
                'provider_response': result.get('response', {}),
            }

            if status == NotificationStatusEnum.SENT:
                update_data['sent_at'] = timestamp()
            elif status == NotificationStatusEnum.FAILED:
                update_data['error_message'] = result.get('error', 'Unknown error')
                update_data['failed_at'] = timestamp()

            log_data = {
                'notification_id': entry._id,
                'provider_type': enum_value(provider_type),
                'attempt_number': attempt_number,
                'attempted_at': timestamp(),
                'status': enum_value(status),
                'response': result.get('response', {}),
                'error_message': result.get('error'),
            }

            async with self.statemgr.transaction():
                await self.statemgr.update(entry, **update_data)
                await self.statemgr.add_notification_log(**log_data)

            results.append({
                "notification_id": entry._id,
                "status": enum_value(status),
                "provider_message_id": result.get('provider_message_id'),
                "provider_type": enum_value(provider_type),
            })

        if len(results) == 1:
            return results[0]

        return {"count": len(results), "results": results}

    async def check_status(self, provider_message_id: str) -> Dict[str, Any]:
        """
        SMTP doesn't support delivery confirmation by default.
        Would need to implement bounce handling separately.
        """
        return {
            'status': 'unknown',
            'message': 'SMTP does not support delivery status checking'
        }

    async def validate_config(self) -> bool:
        """
        Validate SMTP configuration by attempting connection to self-hosted server.
        """
        try:
            use_tls = self.provider_config.smtp_use_ssl or self.provider_config.smtp_use_tls
            async with aiosmtplib.SMTP(
                hostname=self.provider_config.smtp_host,
                port=self.provider_config.smtp_port,
                use_tls=use_tls,
                timeout=self.provider_config.smtp_timeout,
            ) as smtp:
                if self.provider_config.smtp_username and self.provider_config.smtp_password:
                    await smtp.login(self.provider_config.smtp_username, self.provider_config.smtp_password)
                logger.info(f"SMTP configuration validated successfully")
                return True
        except Exception as e:
            logger.error(f"SMTP configuration validation failed: {str(e)}")
            return False

    @property
    def provider_type(self):
        return ProviderTypeEnum.SMTP

    def supports_delivery_confirmation(self) -> bool:
        return False  # Basic SMTP doesn't support this
