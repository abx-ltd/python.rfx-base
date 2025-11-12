"""
Email notification providers - Self-hosted SMTP infrastructure
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

from fluvius.data.data_model import DataModel

from .base import NotificationProviderBase
from ..types import NotificationStatusEnum, ContentTypeEnum, ProviderTypeEnum
from .. import logger


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

    def __init__(self):
        super().__init__()

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
            from_email = kwargs.get('from_email') or self.config.smtp_from_email

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
                f"Connecting to self-hosted SMTP server at {self.config.smtp_host}:{self.config.smtp_port}"
            )

            # Connect to self-hosted SMTP server
            use_tls = self.config.smtp_use_ssl or self.config.smtp_use_tls
            async with aiosmtplib.SMTP(
                hostname=self.config.smtp_host,
                port=self.config.smtp_port,
                use_tls=use_tls,
                timeout=self.config.smtp_timeout,
            ) as smtp:
                # Authenticate if credentials are provided
                if self.config.smtp_username and self.config.smtp_password:
                    await smtp.login(self.config.smtp_username, self.config.smtp_password)

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
                        'smtp_host': self.config.smtp_host,
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
            use_tls = self.config.smtp_use_ssl or self.config.smtp_use_tls
            async with aiosmtplib.SMTP(
                hostname=self.config.smtp_host,
                port=self.config.smtp_port,
                use_tls=use_tls,
                timeout=self.config.smtp_timeout,
            ) as smtp:
                if self.config.smtp_username and self.config.smtp_password:
                    await smtp.login(self.config.smtp_username, self.config.smtp_password)
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
