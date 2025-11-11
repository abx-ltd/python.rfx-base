"""
SMS notification providers
"""
import httpx
from typing import Dict, Any, Optional
from urllib.parse import urlencode
import base64

from .base import NotificationProviderBase
from ..types import NotificationStatusEnum
from .. import logger


class TwilioSMSProvider(NotificationProviderBase):
    """
    Twilio SMS provider for sending text messages.
    """

    def __init__(self, provider_config: Dict[str, Any]):
        super().__init__(provider_config)
        self.account_sid = self.credentials.get('account_sid')
        self.auth_token = self.credentials.get('auth_token')
        self.from_number = self.config.get('from_number')
        self.api_url = f'https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json'

    async def send(
        self,
        recipient: str,
        subject: Optional[str],
        body: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send an SMS via Twilio API.

        Args:
            recipient: Phone number in E.164 format (e.g., +1234567890)
            subject: Not used for SMS
            body: SMS message body (max 1600 characters for Twilio)
            **kwargs: Additional parameters (from_number, media_url for MMS)
        """
        try:
            from_number = kwargs.get('from_number', self.from_number)

            if not from_number:
                raise ValueError("from_number is required for Twilio SMS")

            # Prepare payload
            payload = {
                'To': recipient,
                'From': from_number,
                'Body': body
            }

            # Add media URL for MMS if provided
            if 'media_url' in kwargs:
                payload['MediaUrl'] = kwargs['media_url']

            # Prepare auth header
            auth_string = f"{self.account_sid}:{self.auth_token}"
            auth_bytes = base64.b64encode(auth_string.encode('utf-8'))
            auth_header = f"Basic {auth_bytes.decode('utf-8')}"

            headers = {
                'Authorization': auth_header,
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            # Send request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    data=urlencode(payload),
                    headers=headers
                )

                response_data = response.json()

                if response.status_code == 201:
                    message_sid = response_data.get('sid')
                    logger.info(f"SMS sent via Twilio to {recipient}, SID: {message_sid}")

                    return {
                        'status': NotificationStatusEnum.SENT,
                        'provider_message_id': message_sid,
                        'response': response_data,
                        'error': None
                    }
                else:
                    error_msg = response_data.get('message', 'Unknown error')
                    error_code = response_data.get('code')
                    logger.error(f"Twilio API error: {error_code} - {error_msg}")

                    return {
                        'status': NotificationStatusEnum.FAILED,
                        'provider_message_id': None,
                        'response': response_data,
                        'error': f"{error_code}: {error_msg}"
                    }

        except Exception as e:
            logger.error(f"Failed to send SMS via Twilio: {str(e)}")
            return {
                'status': NotificationStatusEnum.FAILED,
                'provider_message_id': None,
                'response': {},
                'error': str(e)
            }

    async def check_status(self, provider_message_id: str) -> Dict[str, Any]:
        """
        Check SMS delivery status via Twilio API.

        Args:
            provider_message_id: Twilio message SID
        """
        try:
            status_url = f'https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages/{provider_message_id}.json'

            # Prepare auth header
            auth_string = f"{self.account_sid}:{self.auth_token}"
            auth_bytes = base64.b64encode(auth_string.encode('utf-8'))
            auth_header = f"Basic {auth_bytes.decode('utf-8')}"

            headers = {
                'Authorization': auth_header
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(status_url, headers=headers)
                response_data = response.json()

                if response.status_code == 200:
                    twilio_status = response_data.get('status')

                    # Map Twilio status to our status
                    status_map = {
                        'queued': NotificationStatusEnum.PROCESSING,
                        'sending': NotificationStatusEnum.PROCESSING,
                        'sent': NotificationStatusEnum.SENT,
                        'delivered': NotificationStatusEnum.DELIVERED,
                        'undelivered': NotificationStatusEnum.FAILED,
                        'failed': NotificationStatusEnum.FAILED,
                    }

                    status = status_map.get(twilio_status, NotificationStatusEnum.PENDING)

                    return {
                        'status': status,
                        'twilio_status': twilio_status,
                        'error_code': response_data.get('error_code'),
                        'error_message': response_data.get('error_message'),
                        'date_sent': response_data.get('date_sent'),
                        'date_updated': response_data.get('date_updated')
                    }
                else:
                    return {
                        'status': NotificationStatusEnum.PENDING,
                        'error': 'Failed to fetch status from Twilio'
                    }

        except Exception as e:
            logger.error(f"Failed to check Twilio SMS status: {str(e)}")
            return {
                'status': NotificationStatusEnum.PENDING,
                'error': str(e)
            }

    async def validate_config(self) -> bool:
        """
        Validate Twilio configuration by checking account details.
        """
        try:
            account_url = f'https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}.json'

            # Prepare auth header
            auth_string = f"{self.account_sid}:{self.auth_token}"
            auth_bytes = base64.b64encode(auth_string.encode('utf-8'))
            auth_header = f"Basic {auth_bytes.decode('utf-8')}"

            headers = {
                'Authorization': auth_header
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(account_url, headers=headers)
                return response.status_code == 200

        except Exception as e:
            logger.error(f"Twilio configuration validation failed: {str(e)}")
            return False

    def supports_delivery_confirmation(self) -> bool:
        return True  # Twilio supports delivery confirmation
