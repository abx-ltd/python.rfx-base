from typing import Dict, Any
from .datadef import Notification
from fluvius.data import serialize_mapping
from .types import (
    MessageTypeEnum,
    RenderStrategyEnum,
    ProcessingModeEnum,
    ContentTypeEnum,
    PriorityLevelEnum,
    DirectionTypeEnum,
)

from fluvius.error import BadRequestError

MESSAGE_RENDERING_MAP = {
    MessageTypeEnum.NOTIFICATION: RenderStrategyEnum.CACHED,  # High volume, can use cached templates
    MessageTypeEnum.ALERT: RenderStrategyEnum.SERVER,  # Critical, needs server-side rendering for reliability
    MessageTypeEnum.REMINDER: RenderStrategyEnum.CLIENT,  # Dynamic content, client-side for personalization
    MessageTypeEnum.SYSTEM: RenderStrategyEnum.STATIC,  # Administrative, usually static content
    MessageTypeEnum.USER: RenderStrategyEnum.CLIENT,  # User-generated, interactive content
}


def get_render_strategy(message_type: MessageTypeEnum) -> RenderStrategyEnum:
    """
    Get the appropriate template rendering strategy for a notification type.

    Rendering strategies:
    - SERVER: Server-side template rendering for critical/reliable content
    - CLIENT: Client-side template rendering for dynamic/interactive content
    - CACHED: Pre-rendered templates cached for high-volume notifications
    - STATIC: Static templates without dynamic content for simple messages
    """
    return MESSAGE_RENDERING_MAP.get(message_type, RenderStrategyEnum.SERVER)


def render_on_server(strategy: RenderStrategyEnum) -> bool:
    return strategy in (
        RenderStrategyEnum.SERVER,
        RenderStrategyEnum.CACHED,
        RenderStrategyEnum.STATIC,
    )


def render_on_client(strategy: RenderStrategyEnum) -> bool:
    return strategy in (RenderStrategyEnum.CLIENT)


def extract_template_context(payload, *, default_locale: str = "en") -> Dict[str, Any]:
    """
    Extract template context from the payload.
    """
    return {
        "tenant_id": payload.get("tenant_id"),
        "app_id": payload.get("app_id"),
        "locale": payload.get("locale", default_locale),
        "channel": payload.get("channel"),
    }


async def determine_processing_mode(
    message_type: MessageTypeEnum, payload: dict
) -> ProcessingModeEnum:
    """Determine how to process the message based on type and content."""

    # Direct content can be processed immediately
    if payload.get("content"):
        return ProcessingModeEnum.SYNC

    # Critical alerts are always immediate
    if message_type == MessageTypeEnum.ALERT:
        return ProcessingModeEnum.IMMEDIATE

    # High priority messages
    if payload.get("priority") == "high":
        return ProcessingModeEnum.SYNC

    # Template-based messages with client rendering can be fast
    strategy = payload.get("render_strategy")
    if strategy == RenderStrategyEnum.CLIENT.value:
        return ProcessingModeEnum.SYNC

    # Default to async for complex rendering
    return ProcessingModeEnum.ASYNC


def message_to_notification_data(message):
    """
    Convert a Message model to a Notification data structure for client consumption.

    Args:
        message: Message DataModel instance
        recipient_id: ID of the specific recipient

    Returns:
        Notification DataModel instance
    """

    return Notification(
        message_id=getattr(message, "_id", None),
        sender_id=getattr(message, "sender_id", None),
        subject=getattr(message, "subject", "") or "",
        content=getattr(message, "rendered_content", None),
        content_type=getattr(message, "content_type", ContentTypeEnum.TEXT),
        priority=getattr(message, "priority", PriorityLevelEnum.MEDIUM),
        is_important=getattr(message, "is_important", False) or False,
        expiration_date=getattr(message, "expiration_date", None),
        tags=getattr(message, "tags", []) or [],
        # Template information for client rendering
        template_key=getattr(message, "template_key", None),
        template_version=getattr(message, "template_version", None),
        template_locale=getattr(message, "template_locale", None),
        template_data=getattr(message, "template_data", {}) or {},
        render_strategy=getattr(message, "render_strategy", RenderStrategyEnum.SERVER),
        data=getattr(message, "data", {}) or {},
    )


async def process_message_content(agg, message_id, payload, mode):
    """
    Process message content and mark it as ready for delivery.

    Args:
        agg: The aggregate instance
        message_id: The message ID to process
        payload: The message payload
        mode: The processing mode

    Returns:
        The processed message
    """
    processed_message = await agg.process_message_content(
        message_id=message_id, context=extract_template_context(payload), mode=mode
    )
    await agg.mark_ready_for_delivery(message_id)
    return processed_message


def notify_recipients(
    client,
    recipients: list,
    kind: str,
    target: str,
    msg: dict,
    mode: ProcessingModeEnum,
):
    """
    Notify recipients via MQTT client.

    Args:
        client: The MQTT client instance
        recipients: List of recipient profile IDs
        kind: The notification kind
        target: The notification target
        msg: The message dictionary
        mode: The processing mode

    Returns:
        List of notification channels

    Raises:
        ValueError: If client is not available
    """
    if not client:
        raise ValueError("Client is not available")
    channels = []
    for profile_id in recipients:
        msg["recipient_id"] = profile_id
        channel = client.notify(
            profile_id,
            kind=kind,
            target=target,
            msg=msg,
            batch_id=mode.value,
        )
        channels.append(channel)
    client.send(mode.value)
    return channels


async def set_message_category_if_provided(agg, message_id, message_category):
    """
    Set message category if provided.

    Args:
        agg: The aggregate instance
        message_id: The message ID
        message_category: The category to set (optional)
    """
    if message_category:
        await agg.set_message_category(
            resource="message", resource_id=message_id, category=message_category
        )


async def determine_and_process_message(
    agg, message_id, message_payload, processing_mode
):
    """
    Determine processing mode and process message content.

    Args:
        agg: The aggregate instance
        message_id: The message ID
        message_payload: The message payload
        processing_mode: The processing mode

    Returns:
        The processed message
    """
    message = await process_message_content(
        agg, message_id, message_payload, processing_mode
    )
    return message


async def get_processing_mode_and_client(agg, message_payload):
    """
    Determine processing mode and get MQTT client from context.

    Args:
        agg: The aggregate instance
        message_payload: The message payload

    Returns:
        Tuple of (processing_mode, client)
    """
    message_type = MessageTypeEnum(message_payload.get("message_type", "NOTIFICATION"))
    processing_mode = await determine_processing_mode(
        message_type=message_type, payload=message_payload
    )
    context = agg.get_context()
    client = context.service_proxy.mqtt_client
    return processing_mode, client


def create_message_response(message_result, message_category=None):
    """
    Create a serialized response for a message operation.

    Args:
        message_result: The message result object
        message_category: Optional message category to include

    Returns:
        Serialized response data dictionary
    """
    response_data = serialize_mapping(message_result)
    if message_category:
        response_data["category"] = message_category
    return response_data


def validate_box_key(box_key: str, direction: DirectionTypeEnum):
    """
    Validate box key.

    Args:
        box_key: The box key to validate
        direction: The direction of the message
    """
    if (
        direction == DirectionTypeEnum.INBOUND
        and box_key == "outbox"
    ):
        raise BadRequestError("M00.004", "Cannot move INBOUND message to outbox")
    if (
        direction == DirectionTypeEnum.OUTBOUND
        and box_key == "inbox"
    ):
        raise BadRequestError("M00.005", "Cannot move OUTBOUND message to inbox")
