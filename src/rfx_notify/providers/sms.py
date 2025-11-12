"""
SMS notification providers - Self-hosted Kannel gateway
"""
import httpx
from typing import Dict, Any, Optional

from fluvius.data.data_model import DataModel

from .base import NotificationProviderBase
from ..types import NotificationStatusEnum, ProviderTypeEnum
from .. import logger


class KannelSMSProviderConfig(DataModel):
    kannel_host: str
    kannel_port: int = 13013
    kannel_username: Optional[str] = None
    kannel_password: Optional[str] = None
    kannel_send_url: str = "/cgi-bin/sendsms"
    kannel_dlr_mask: int = 31
    kannel_timeout: int = 30
    kannel_from_number: Optional[str] = None


class KannelSMSProvider(NotificationProviderBase):
    """
    Kannel SMS gateway provider for self-hosted SMS infrastructure.
    Kannel should be running on the same machine as the worker.
    """

    __CONFIG_CLS__ = KannelSMSProviderConfig

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
        Send SMS via self-hosted Kannel gateway.

        Args:
            recipient: Phone number in E.164 format (e.g., +1234567890)
            subject: Not used for SMS
            body: SMS message body
            **kwargs: Additional parameters (from_number, dlr_url for delivery reports)
        """
        try:
            # Build Kannel sendsms URL
            url = f"http://{self.config.kannel_host}:{self.config.kannel_port}{self.config.kannel_send_url}"

            # Prepare parameters
            params = {
                'username': self.config.kannel_username,
                'password': self.config.kannel_password,
                'to': recipient,
                'text': body,
            }

            # Add from number if configured
            from_number = kwargs.get('from_number') or self.config.kannel_from_number
            if from_number:
                params['from'] = from_number

            # Add DLR (Delivery Report) configuration if webhook URL provided
            dlr_url = kwargs.get('dlr_url')
            if dlr_url:
                params['dlr-url'] = dlr_url
                params['dlr-mask'] = self.config.kannel_dlr_mask

            logger.info(
                f"Sending SMS to {recipient} via Kannel at {self.config.kannel_host}:{self.config.kannel_port}"
            )

            async with httpx.AsyncClient(timeout=self.config.kannel_timeout) as client:
                response = await client.get(url, params=params)

                # Kannel returns different status codes and messages
                # Successful: "0: Accepted for delivery" or similar
                # Error: "3: Temporarily failed" or error message
                response_text = response.text.strip()

                if response.status_code == 200:
                    # Check response text for success indicators
                    if any(indicator in response_text for indicator in ['Sent', 'Queued', 'Accepted']):
                        # Extract message ID from response (format: "0: Accepted for delivery")
                        try:
                            message_id = response_text.split(':')[0].strip()
                        except:
                            message_id = None

                        logger.info(
                            f"SMS sent to {recipient} via Kannel, message_id: {message_id}"
                        )

                        return {
                            'status': NotificationStatusEnum.SENT,
                            'provider_type': self.provider_type,
                            'provider_message_id': message_id,
                            'response': {
                                'kannel_response': response_text,
                                'recipient': recipient,
                                'kannel_host': self.config.kannel_host,
                            },
                            'error': None
                        }
                    else:
                        # Response indicates error
                        logger.error(f"Kannel error: {response_text}")
                        return {
                            'status': NotificationStatusEnum.FAILED,
                            'provider_type': self.provider_type,
                            'provider_message_id': None,
                            'response': {'kannel_response': response_text},
                            'error': f"Kannel error: {response_text}"
                        }
                else:
                    logger.error(
                        f"Kannel HTTP error {response.status_code}: {response.text}"
                    )
                    return {
                        'status': NotificationStatusEnum.FAILED,
                        'provider_type': self.provider_type,
                        'provider_message_id': None,
                        'response': {},
                        'error': f"HTTP {response.status_code}: {response.text}"
                    }

        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to Kannel for {recipient}")
            return {
                'status': NotificationStatusEnum.FAILED,
                'provider_type': self.provider_type,
                'provider_message_id': None,
                'response': {},
                'error': "Timeout connecting to Kannel gateway"
            }
        except Exception as e:
            logger.error(f"Error sending SMS to {recipient} via Kannel: {str(e)}")
            return {
                'status': NotificationStatusEnum.FAILED,
                'provider_type': self.provider_type,
                'provider_message_id': None,
                'response': {},
                'error': str(e)
            }

    async def check_status(self, provider_message_id: str) -> Dict[str, Any]:
        """
        Check SMS delivery status via Kannel DLR.
        Requires DLR to be configured in Kannel and webhook integration.
        """
        try:
            # Kannel status checking is typically done via DLR webhooks
            # This is a placeholder for status page checking
            url = f"http://{self.config.kannel_host}:{self.config.kannel_port}/status"
            params = {
                'username': self.config.kannel_username,
                'password': self.config.kannel_password,
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)

                if response.status_code == 200:
                    return {
                        'status': 'unknown',
                        'message': 'Check Kannel DLR logs for detailed delivery status'
                    }
                else:
                    return {
                        'status': 'error',
                        'message': f'Kannel status page returned {response.status_code}'
                    }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    async def validate_config(self) -> bool:
        """
        Validate Kannel configuration by checking status page.
        """
        try:
            url = f"http://{self.config.kannel_host}:{self.config.kannel_port}/status"
            params = {
                'username': self.config.kannel_username,
                'password': self.config.kannel_password,
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, params=params)
                is_valid = response.status_code == 200

                if is_valid:
                    logger.info(f"Kannel configuration validated successfully")
                else:
                    logger.error(f"Kannel validation failed with status {response.status_code}")

                return is_valid
        except Exception as e:
            logger.error(f"Kannel configuration validation failed: {str(e)}")
            return False

    @property
    def provider_type(self):
        return ProviderTypeEnum.SMS

    def supports_delivery_confirmation(self) -> bool:
        return True  # Kannel supports DLR (Delivery Reports)
