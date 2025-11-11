"""
Email notification providers - Self-hosted SMTP infrastructure
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

from .base import NotificationProviderBase
from ..types import NotificationStatusEnum, ContentTypeEnum, ProviderTypeEnum
from .. import config, logger
from pydantic import BaseModel


class SMTPEmailProviderConfig(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_use_tls: bool
    smtp_use_ssl: bool
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    smtp_timeout: int


class SMTPEmailProvider(NotificationProviderBase):
    name = "smtp"

    __CONFIG_CLS__ = SMTPEmailProviderConfig
    """
    SMTP email provider for sending emails through self-hosted SMTP server.
    The SMTP server (Postfix, Haraka, etc.) runs on the worker machine.
    """

    def __init__(self):
        super().__init__()
        self.smtp_host = config.SMTP_HOST
        self.smtp_port = config.SMTP_PORT
        self.smtp_use_tls = config.SMTP_USE_TLS
        self.smtp_use_ssl = config.SMTP_USE_SSL
        self.smtp_username = config.SMTP_USERNAME
        self.smtp_password = config.SMTP_PASSWORD
        self.smtp_from_email = config.SMTP_FROM_EMAIL
        self.smtp_timeout = config.SMTP_TIMEOUT

    async def send(
        self,
        recipient: str,
        subject: Optional[str],
        body: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send an email via self-hosted SMTP server.

        Args:
            recipient: Email address
            subject: Email subject
            body: Email body
            **kwargs: Additional parameters (from_email, content_type, cc, bcc)
        """
        try:
            from_email = kwargs.get('from_email') or self.smtp_from_email

            if not from_email:
                raise ValueError("SMTP_FROM_EMAIL is not configured")

            # Create message
            content_type = kwargs.get('content_type', ContentTypeEnum.HTML)

            if content_type == ContentTypeEnum.HTML:
                message = MIMEMultipart('alternative')
                message.attach(MIMEText(body, 'html'))
            else:
                message = MIMEText(body, 'plain')

            message['Subject'] = subject or ''
            message['From'] = from_email
            message['To'] = recipient

            # Add CC and BCC if provided
            if 'cc' in kwargs:
                message['Cc'] = kwargs['cc']
            if 'bcc' in kwargs:
                message['Bcc'] = kwargs['bcc']

            logger.info(
                f"Connecting to self-hosted SMTP server at {self.smtp_host}:{self.smtp_port}"
            )

            # Connect to self-hosted SMTP server
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=self.smtp_use_tls,
                timeout=self.smtp_timeout,
            ) as smtp:
                # Authenticate if credentials are provided
                if self.smtp_username and self.smtp_password:
                    await smtp.login(self.smtp_username, self.smtp_password)

                # Send message
                send_result = await smtp.send_message(message)

                logger.info(f"Email sent to {recipient} via self-hosted SMTP server")

                return {
                    'status': NotificationStatusEnum.SENT,
                    'provider_type': self.provider_type,
                    'provider_message_id': message.get('Message-ID'),
                    'response': {
                        'smtp_response': str(send_result),
                        'recipient': recipient,
                        'smtp_host': self.smtp_host,
                    },
                    'error': None
                }

        except aiosmtplib.SMTPException as e:
            logger.error(f"SMTP error sending to {recipient}: {str(e)}")
            return {
                'status': NotificationStatusEnum.FAILED,
                'provider_type': self.provider_type,
                'provider_message_id': None,
                'response': {},
                'error': f"SMTP error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error sending email to {recipient}: {str(e)}")
            return {
                'status': NotificationStatusEnum.FAILED,
                'provider_type': self.provider_type,
                'provider_message_id': None,
                'response': {},
                'error': str(e)
            }

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
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=self.smtp_use_tls,
                timeout=5,
            ) as smtp:
                if self.smtp_username and self.smtp_password:
                    await smtp.login(self.smtp_username, self.smtp_password)
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
