"""
Email notification providers
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import httpx

from .base import NotificationProviderBase
from ..types import NotificationStatusEnum, ContentTypeEnum
from .. import logger


class SMTPEmailProvider(NotificationProviderBase):
    """
    SMTP email provider for sending emails through standard SMTP servers.
    """

    async def send(
        self,
        recipient: str,
        subject: Optional[str],
        body: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send an email via SMTP.

        Args:
            recipient: Email address
            subject: Email subject
            body: Email body
            **kwargs: Additional parameters (from_email, content_type, cc, bcc)
        """
        try:
            # Extract SMTP configuration
            smtp_host = self.config.get('host', 'localhost')
            smtp_port = self.config.get('port', 587)
            use_tls = self.config.get('use_tls', True)
            username = self.credentials.get('username')
            password = self.credentials.get('password')
            from_email = kwargs.get('from_email') or self.config.get('from_email', username)

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

            # Send email
            smtp_client = aiosmtplib.SMTP(hostname=smtp_host, port=smtp_port, use_tls=use_tls)
            await smtp_client.connect()

            if username and password:
                await smtp_client.login(username, password)

            await smtp_client.send_message(message)
            await smtp_client.quit()

            logger.info(f"Email sent successfully to {recipient}")

            return {
                'status': NotificationStatusEnum.SENT,
                'provider_message_id': None,  # SMTP doesn't provide message IDs typically
                'response': {'success': True},
                'error': None
            }

        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {str(e)}")
            return {
                'status': NotificationStatusEnum.FAILED,
                'provider_message_id': None,
                'response': {},
                'error': str(e)
            }

    async def check_status(self, provider_message_id: str) -> Dict[str, Any]:
        """
        SMTP doesn't support status checking.
        """
        return {
            'status': NotificationStatusEnum.SENT,
            'message': 'SMTP does not support delivery confirmation'
        }

    async def validate_config(self) -> bool:
        """
        Validate SMTP configuration by attempting to connect.
        """
        try:
            smtp_host = self.config.get('host', 'localhost')
            smtp_port = self.config.get('port', 587)
            use_tls = self.config.get('use_tls', True)

            smtp_client = aiosmtplib.SMTP(hostname=smtp_host, port=smtp_port, use_tls=use_tls)
            await smtp_client.connect()
            await smtp_client.quit()
            return True
        except Exception as e:
            logger.error(f"SMTP configuration validation failed: {str(e)}")
            return False


class SendGridProvider(NotificationProviderBase):
    """
    SendGrid email provider using SendGrid API v3.
    """

    def __init__(self, provider_config: Dict[str, Any]):
        super().__init__(provider_config)
        self.api_key = self.credentials.get('api_key')
        self.api_url = 'https://api.sendgrid.com/v3/mail/send'

    async def send(
        self,
        recipient: str,
        subject: Optional[str],
        body: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send an email via SendGrid API.
        """
        try:
            from_email = kwargs.get('from_email') or self.config.get('from_email')
            content_type = kwargs.get('content_type', ContentTypeEnum.HTML)

            # Prepare SendGrid payload
            payload = {
                'personalizations': [{
                    'to': [{'email': recipient}],
                    'subject': subject or ''
                }],
                'from': {'email': from_email},
                'content': [{
                    'type': 'text/html' if content_type == ContentTypeEnum.HTML else 'text/plain',
                    'value': body
                }]
            }

            # Add CC and BCC if provided
            if 'cc' in kwargs:
                payload['personalizations'][0]['cc'] = [{'email': kwargs['cc']}]
            if 'bcc' in kwargs:
                payload['personalizations'][0]['bcc'] = [{'email': kwargs['bcc']}]

            # Send request
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(self.api_url, json=payload, headers=headers)

                if response.status_code == 202:
                    message_id = response.headers.get('X-Message-Id')
                    logger.info(f"Email sent via SendGrid to {recipient}, message_id: {message_id}")

                    return {
                        'status': NotificationStatusEnum.SENT,
                        'provider_message_id': message_id,
                        'response': {'status_code': response.status_code},
                        'error': None
                    }
                else:
                    error_msg = response.text
                    logger.error(f"SendGrid API error: {error_msg}")

                    return {
                        'status': NotificationStatusEnum.FAILED,
                        'provider_message_id': None,
                        'response': {'status_code': response.status_code, 'error': error_msg},
                        'error': error_msg
                    }

        except Exception as e:
            logger.error(f"Failed to send email via SendGrid: {str(e)}")
            return {
                'status': NotificationStatusEnum.FAILED,
                'provider_message_id': None,
                'response': {},
                'error': str(e)
            }

    async def check_status(self, provider_message_id: str) -> Dict[str, Any]:
        """
        Check delivery status via SendGrid Event Webhook (would need to be implemented).
        """
        # SendGrid uses webhooks for delivery status, not a pull API
        return {
            'status': NotificationStatusEnum.SENT,
            'message': 'SendGrid status checking requires webhook integration'
        }

    async def validate_config(self) -> bool:
        """
        Validate SendGrid API key by making a test request.
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }

            async with httpx.AsyncClient() as client:
                # Test with API key validation endpoint
                response = await client.get(
                    'https://api.sendgrid.com/v3/scopes',
                    headers=headers
                )
                return response.status_code == 200

        except Exception as e:
            logger.error(f"SendGrid configuration validation failed: {str(e)}")
            return False

    def supports_delivery_confirmation(self) -> bool:
        return True  # SendGrid supports delivery confirmation via webhooks
