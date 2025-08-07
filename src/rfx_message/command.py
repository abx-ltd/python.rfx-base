from fluvius.data import serialize_mapping, UUID_GENR
from fluvius.fastapi.mqtt import FastapiMQTTClient

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
    Send a message to recipients.
    """

    Data = datadef.SendMessagePayload
    class Meta:
        key = "send-message"
        new_resource = True
        resources = ("message",)
        tags = ["message", "create"]
        auth_required = True
        
    async def _process(self, agg, stm, payload):
        context = agg.get_context()
        message_data = serialize_mapping(payload)
        message_data['sender_id'] = context.user_id

        recipients = message_data.pop("recipients", [])
        message = await agg.generate_message(data=message_data)
        message_data['_id'] = message['message_id']

        if recipients:
            recipients = await agg.add_recipients(data=recipients, message_id=message["message_id"])
            await notify_multiple_recipients(self.mqtt_client, message_data, recipients)

        yield agg.create_response({
            "status": "success",
            "message_id": message["message_id"],
            "recipients_count": len(recipients.get("recipients", [])) if recipients else 0
        }, _type="message-service-response")

class ReadMessage(Command):
    """
    Mark a message as read for the current user
    """

    Data = datadef.ReadMessagePayload

    class Meta:
        key = "read-message"
        resources = ("message-recipient",)
        tags = ["message", "read"]
        auth_required = True
    
    async def _process(self, agg, stm, payload):
        context = agg.get_context()
        
        # Mark message as read for the current user
        await agg.mark_message_read(
            message_id=payload.message_id,
            user_id=context.user_id
        )
        
        yield agg.create_response({
            "status": "success",
            "message_id": payload.message_id,
            "user_id": context.user_id,
            "read_at": context.timestamp.isoformat()
        }, _type="message-service-response")


class UpdateMessage(Command):
    """
    Update an existing message (only by sender)
    """

    Data = datadef.UpdateMessagePayload

    class Meta:
        key = "update-message"
        resources = ("message",)
        tags = ["message", "update"]
        auth_required = True
    
    async def _process(self, agg, stm, payload):
        context = agg.get_context()
        
        message_data = serialize_mapping(payload)
        message_data['updated_by'] = context.user_id
        
        # Update the message
        updated_message = await agg.update_message(data=message_data)
        
        yield agg.create_response({
            "status": "success",
            "message_id": updated_message["message_id"],
            "updated_at": context.timestamp.isoformat()
        }, _type="message-service-response")


class DeleteMessage(Command):
    """
    Delete a message (only by sender)
    """

    Data = datadef.DeleteMessagePayload

    class Meta:
        key = "delete-message"
        resources = ("message",)
        tags = ["message", "delete"]
        auth_required = True
    
    async def _process(self, agg, stm, payload):
        context = agg.get_context()
        
        # Delete the message
        await agg.delete_message(
            message_id=payload.message_id,
            deleted_by=context.user_id
        )
        
        yield agg.create_response({
            "status": "success",
            "message_id": payload.message_id,
            "deleted_at": context.timestamp.isoformat()
        }, _type="message-service-response")


class AddMessageRecipients(Command):
    """
    Add additional recipients to an existing message
    """

    Data = datadef.AddRecipientsPayload

    class Meta:
        key = "add-message-recipients"
        resources = ("message-recipient",)
        tags = ["message", "recipients", "add"]
        auth_required = True
    
    async def _process(self, agg, stm, payload):
        context = agg.get_context()
        
        # Add recipients to the message
        new_recipients = await agg.add_recipients(
            data=payload.recipients,
            message_id=payload.message_id
        )
        
        yield agg.create_response({
            "status": "success",
            "message_id": payload.message_id,
            "added_recipients": len(new_recipients.get("recipients", [])),
            "added_at": context.timestamp.isoformat()
        }, _type="message-service-response")


class RemoveMessageRecipient(Command):
    """
    Remove a recipient from a message
    """

    Data = datadef.RemoveRecipientPayload

    class Meta:
        key = "remove-message-recipient"
        resources = ("message-recipient",)
        tags = ["message", "recipients", "remove"]
        auth_required = True
    
    async def _process(self, agg, stm, payload):
        context = agg.get_context()
        
        # Remove recipient from the message
        await agg.remove_recipient(
            message_id=payload.message_id,
            recipient_id=payload.recipient_id,
            removed_by=context.user_id
        )
        
        yield agg.create_response({
            "status": "success",
            "message_id": payload.message_id,
            "removed_recipient": payload.recipient_id,
            "removed_at": context.timestamp.isoformat()
        }, _type="message-service-response")


class MarkAllMessagesRead(Command):
    """
    Mark all unread messages as read for the current user
    """

    class Meta:
        key = "mark-all-messages-read"
        resources = ("message-recipient",)
        tags = ["message", "read", "bulk"]
        auth_required = True
    
    async def _process(self, agg, stm, payload):
        context = agg.get_context()
        
        # Mark all messages as read for the current user
        read_count = await agg.mark_all_messages_read(user_id=context.user_id)
        
        yield agg.create_response({
            "status": "success",
            "user_id": context.user_id,
            "messages_read": read_count,
            "read_at": context.timestamp.isoformat()
        }, _type="message-service-response")


class AddMessageAttachment(Command):
    """
    Add an attachment to a message
    """

    Data = datadef.AddAttachmentPayload

    class Meta:
        key = "add-message-attachment"
        resources = ("message-attachment",)
        tags = ["message", "attachment", "add"]
        auth_required = True
    
    async def _process(self, agg, stm, payload):
        context = agg.get_context()
        
        attachment_data = serialize_mapping(payload)
        attachment_data['uploaded_by'] = context.user_id
        
        # Add attachment to the message
        attachment = await agg.add_attachment(data=attachment_data)
        
        yield agg.create_response({
            "status": "success",
            "message_id": payload.message_id,
            "attachment_id": attachment["attachment_id"],
            "added_at": context.timestamp.isoformat()
        }, _type="message-service-response")