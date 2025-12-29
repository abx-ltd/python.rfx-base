"""
SMS notification providers - Self-hosted Kannel gateway
"""
import httpx
from typing import Dict, Any, Optional

from fluvius.data.data_model import DataModel
from fluvius.data import UUID_GENR, timestamp

from .base import NotificationProviderBase
from ..types import NotificationStatusEnum, ProviderTypeEnum
from .. import logger, config


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

    name = "kannel"
    __CONFIG_CLS__ = KannelSMSProviderConfig

    def __init__(self, provider_config: Optional[Any] = None):
        super().__init__(provider_config=provider_config)

    def build_config(self) -> Any:
        return {
            "kannel_host": config.KANNEL_HOST,
            "kannel_port": config.KANNEL_PORT,
            "kannel_username": config.KANNEL_USERNAME,
            "kannel_password": config.KANNEL_PASSWORD,
            "kannel_send_url": config.KANNEL_SEND_URL,
            "kannel_dlr_mask": config.KANNEL_DLR_MASK,
            "kannel_timeout": config.KANNEL_TIMEOUT,
            "kannel_from_number": config.KANNEL_FROM_NUMBER,
        }

    async def send(self, notification: Any) -> Dict[str, Any]:
        """
        Send SMS via self-hosted Kannel gateway.

        Args:
            notification: Notification payload or model
        """
        def get_field(field, default=None):
            if isinstance(notification, dict):
                return notification.get(field, default)
            return getattr(notification, field, default)

        def enum_value(value):
            return value.value if hasattr(value, "value") else value

        recipients = get_field("recipients")
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
                        "recipients": [recipient],
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

            try:
                url = f"http://{self.provider_config.kannel_host}:{self.provider_config.kannel_port}{self.provider_config.kannel_send_url}"

                params = {
                    'username': self.provider_config.kannel_username,
                    'password': self.provider_config.kannel_password,
                    'to': recipient,
                    'text': entry.body,
                }

                from_number = meta.get('from_number') or self.provider_config.kannel_from_number
                if from_number:
                    params['from'] = from_number

                dlr_url = meta.get('dlr_url')
                if dlr_url:
                    params['dlr-url'] = dlr_url
                    params['dlr-mask'] = self.provider_config.kannel_dlr_mask

                logger.info(
                    f"Sending SMS to {recipient} via Kannel at {self.provider_config.kannel_host}:{self.provider_config.kannel_port}"
                )

                async with httpx.AsyncClient(timeout=self.provider_config.kannel_timeout) as client:
                    response = await client.get(url, params=params)

                    response_text = response.text.strip()

                    if response.status_code == 200:
                        if any(indicator in response_text for indicator in ['Sent', 'Queued', 'Accepted']):
                            try:
                                message_id = response_text.split(':')[0].strip()
                            except Exception:
                                message_id = None

                            logger.info(
                                f"SMS sent to {recipient} via Kannel, message_id: {message_id}"
                            )

                            result = {
                                'status': NotificationStatusEnum.SENT,
                                'provider_type': self.provider_type,
                                'provider_message_id': message_id,
                                'response': {
                                    'kannel_response': response_text,
                                    'recipient': recipient,
                                    'kannel_host': self.provider_config.kannel_host,
                                },
                                'error': None
                            }
                        else:
                            logger.error(f"Kannel error: {response_text}")
                            result = {
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
                        result = {
                            'status': NotificationStatusEnum.FAILED,
                            'provider_type': self.provider_type,
                            'provider_message_id': None,
                            'response': {},
                            'error': f"HTTP {response.status_code}: {response.text}"
                        }

            except httpx.TimeoutException:
                logger.error(f"Timeout connecting to Kannel for {recipient}")
                result = {
                    'status': NotificationStatusEnum.FAILED,
                    'provider_type': self.provider_type,
                    'provider_message_id': None,
                    'response': {},
                    'error': "Timeout connecting to Kannel gateway"
                }
            except Exception as e:
                logger.error(f"Error sending SMS to {recipient} via Kannel: {str(e)}")
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
        Check SMS delivery status via Kannel DLR.
        Requires DLR to be configured in Kannel and webhook integration.
        """
        try:
            # Kannel status checking is typically done via DLR webhooks
            # This is a placeholder for status page checking
            url = f"http://{self.provider_config.kannel_host}:{self.provider_config.kannel_port}/status"
            params = {
                'username': self.provider_config.kannel_username,
                'password': self.provider_config.kannel_password,
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
            url = f"http://{self.provider_config.kannel_host}:{self.provider_config.kannel_port}/status"
            params = {
                'username': self.provider_config.kannel_username,
                'password': self.provider_config.kannel_password,
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
