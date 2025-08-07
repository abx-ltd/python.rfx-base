"""
RFX Messaging Domain Aggregate - Business Logic and State Management
"""
from fluvius.domain.aggregate import Aggregate, action
from fluvius.data import serialize_mapping, UUID_GENR

class MessageAggregate(Aggregate):
    """
    Aggregate for managing message-related operations.
    This includes actions on messages, recipients, attachments, embedded content, and references.
    """

    # ========================================================================
    # MESSAGE OPERATIONS
    # ========================================================================

    @action("message-generated", resources="message")
    async def generate_message(self, stm, /, *, data):
        """Action to create a new message."""
        message = self.init_resource(
            "message",
            serialize_mapping(data),
            _id=self.aggroot.identifier)
        await stm.insert(message)
        return {
            "message_id": message._id,
        }
        
    @action("message-updated", resources="message")
    async def update_message(self, stm, /, *, data):
        """Action to update an existing message."""
        message_id = data.pop("message_id")
        
        # Only update non-None fields
        update_data = {k: v for k, v in data.items() if v is not None}
        update_data.update(self.audit_updated())
        
        await stm.update("message", message_id, update_data)
        return {
            "message_id": message_id,
        }

    @action("message-deleted", resources="message")
    async def delete_message(self, stm, /, *, message_id, deleted_by):
        """Action to delete a message."""
        # Soft delete - mark as deleted
        delete_data = {
            "is_deleted": True,
            "deleted_by": deleted_by,
            **self.audit_updated()
        }
        
        await stm.update("message", message_id, delete_data)
        return {
            "message_id": message_id,
        }

    @action("message-retrieved", resources=("message","message-recipient"))
    async def add_recipients(self, stm, /, *, data, message_id):
        """Action to add a recipient to a message."""
        recipient_objects = [
            self.init_resource(
                "message-recipient",
                data={
                    "message_id": message_id,
                    "recipient_id": recipient_data,
                    "_id": UUID_GENR()
                }
            ) for recipient_data in data
        ]

        recipients = [serialize_mapping(recipient) for recipient in recipient_objects]
        await stm.insert_many("message-recipient", *recipients)
        return {
            "recipients": [recipient for recipient in recipients]
        }

    @action("recipient-removed", resources="message-recipient")
    async def remove_recipient(self, stm, /, *, message_id, recipient_id, removed_by):
        """Action to remove a recipient from a message."""
        # Find and soft delete the recipient record
        recipient_record = await stm.fetch_by_filter(
            "message-recipient",
            {"message_id": message_id, "recipient_id": recipient_id}
        )
        
        if recipient_record:
            await stm.update("message-recipient", recipient_record._id, {
                "is_deleted": True,
                "removed_by": removed_by,
                **self.audit_updated()
            })
        
        return {
            "message_id": message_id,
            "recipient_id": recipient_id,
        }

    @action("message-read", resources="message-recipient")
    async def mark_message_read(self, stm, /, *, message_id, user_id):
        """Action to mark a message as read for a specific user."""
        # Find the recipient record for this user and message
        recipient_record = await stm.fetch_by_filter(
            "message-recipient",
            {"message_id": message_id, "recipient_id": user_id}
        )
        
        if recipient_record:
            await stm.update("message-recipient", recipient_record._id, {
                "is_read": True,
                "read_at": self.context.timestamp,
                **self.audit_updated()
            })
        
        return {
            "message_id": message_id,
            "user_id": user_id,
        }

    @action("bulk-messages-read", resources="message-recipient")
    async def mark_all_messages_read(self, stm, /, *, user_id):
        """Action to mark all unread messages as read for a user."""
        # Update all unread message-recipient records for this user
        updated_count = await stm.update_by_filter(
            "message-recipient",
            {"recipient_id": user_id, "is_read": False},
            {
                "is_read": True,
                "read_at": self.context.timestamp,
                **self.audit_updated()
            }
        )
        
        return updated_count

    @action("attachment-added", resources="message-attachment")
    async def add_attachment(self, stm, /, *, data):
        """Action to add an attachment to a message."""
        attachment = self.init_resource(
            "message-attachment",
            serialize_mapping(data),
            _id=UUID_GENR()
        )
        await stm.insert(attachment)
        return {
            "attachment_id": attachment._id,
            "message_id": data["message_id"],
        }

    # ========================================================================
    # RECIPIENT OPERATIONS
    # ========================================================================
