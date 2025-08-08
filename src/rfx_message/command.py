from fluvius.data import serialize_mapping, UUID_GENR

from .domain import MessageServiceDomain
from . import datadef

processor = MessageServiceDomain.command_processor
Command = MessageServiceDomain.Command

async def notify_multiple_recipients(mqtt_client, message_data, recipients):
    batch_id = f"msg-{message_data['_id']}"

    for recipient_id in recipients:
        mqtt_client.notify(
            user_id=recipient_id,
            kind="message",
            target="notification",
            msg=message_data,
            batch_id=batch_id
        )
    
    mqtt_client.send(batch_id)

class SendMessage(Command):
    """
    Send a notification to recipients.
    
    This is typically called by domain events or business logic,
    not directly by users. Recipients and content are determined
    by the business rules of the triggering domain.
    """

    Data = datadef.SendMessagePayload

    class Meta:
        key = "send-message"
        new_resource = True
        resources = ("message",)
        tags = ["notification", "create", "system"]
        auth_required = True
        
    async def _process(self, agg, stm, payload):
        context = agg.get_context()
        message_data = serialize_mapping(payload)
        message_data['sender_id'] = context.user_id  # System/service that triggered

        recipients = message_data.pop("recipients", [])
        message = await agg.generate_message(data=message_data)

        if recipients:
            recipients = await agg.add_recipients(data=recipients, message_id=message["message_id"])
            # await notify_multiple_recipients(self.mqtt_client, message_data, recipients)

        yield agg.create_response({
            "status": "success",
            "message_id": message["message_id"],
            "recipients_count": len(recipients.get("recipients", [])) if recipients else 0,
            "user_id": context.user_id,
        }, _type="message-service-response")

class ReadMessage(Command):
    """
    Mark a notification as read for the current user
    """

    # Data = datadef.ReadMessagePayload

    class Meta:
        key = "read-message"
        resources = ("message-recipient",)
        tags = ["notification", "read"]
        auth_required = True
    
    async def _process(self, agg, stm, payload):
        # Mark notification as read for the current user
        result = await agg.mark_message_read()
        
        yield agg.create_response({
            "status": result["status"],
            "message_id": result["message_id"],
            "user_id": result["user_id"],
            "read_at": result["read_at"]
        }, _type="message-service-response")

class MarkAllMessagesRead(Command):
    """
    Mark all unread notifications as read for the current user
    """

    class Meta:
        key = "mark-all-messages-read"
        resources = ("message-recipient",)
        tags = ["notification", "read", "bulk"]
        auth_required = True
        new_resource = True
    
    async def _process(self, agg, stm, payload):
        context = agg.get_context()
        
        # Mark all notifications as read for the current user
        result = await agg.mark_all_messages_read(user_id=context.user_id)
        
        yield agg.create_response({
            "status": result["status"],
            "user_id": result["user_id"],
            "messages_read": result["messages_read"],
            "read_at": context.timestamp.isoformat()
        }, _type="message-service-response")


class ArchiveMessage(Command):
    """
    Archive a notification for the current user
    """

    Data = datadef.ReadMessagePayload  # Reuse same payload structure

    class Meta:
        key = "archive-message"
        resources = ("message-recipient",)
        tags = ["notification", "archive"]
        auth_required = True
    
    async def _process(self, agg, stm, payload):
        # Archive notification for the current user
        await agg.archive_message()
        
        yield agg.create_response({
            "status": "success",
            "message_id": payload.message_id,
        }, _type="message-service-response")