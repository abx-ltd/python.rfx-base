"""
RFX Messaging Domain Aggregate - Business Logic and State Management
"""
from fluvius.domain.aggregate import Aggregate, action
from fluvius.data import serialize_mapping, UUID_GENR

from . import logger

class MessageAggregate(Aggregate):
    """
    Aggregate for managing message-related operations.
    This includes actions on messages, recipients, attachments, embedded content, and references.
    """

    # ========================================================================
    # MESSAGE OPERATIONS
    # ========================================================================

    @action("message-generated", resources="message")
    async def generate_message(self, *, data):
        """Action to create a new message."""
        message = self.init_resource(
            "message",
            serialize_mapping(data),
            _id=self.aggroot.identifier)
        await self.statemgr.insert(message)
        return {
            "message_id": message._id,
        }
        
    # @action("message-updated", resources="message")
    # async def update_message(self, stm, /, *, data):
    #     """Action to update an existing message."""
    #     message_id = data.pop("message_id")
        
    #     # Fetch the existing message
    #     message = await stm.fetch("message", message_id)
        
    #     # Only update non-None fields
    #     update_data = {k: v for k, v in data.items() if v is not None}
        
    #     await stm.update(message, **update_data)
    #     return {
    #         "message_id": message_id,
    #     }

    # @action("message-deleted", resources="message")
    # async def delete_message(self, stm, /, *, message_id):
    #     """Action to delete a message."""
    #     # Fetch the message and soft delete it
    #     message = await stm.fetch("message", message_id)
    #     await stm.invalidate(message)
        
    #     return {
    #         "message_id": message_id,
    #     }

    @action("message-retrieved", resources=("message", "message-recipient"))
    async def add_recipients(self, *, data, message_id):
        """Action to add recipients to a message."""
        recipient_records = []
        
        for recipient_id in data:
            recipient_data = {
                "message_id": message_id,
                "recipient_id": recipient_id,
                "_id": UUID_GENR(),
                "read": False,
                "archived": False
            }
            # Use init_resource to create the model object properly
            recipient_record = self.init_resource("message-recipient", recipient_data)
            recipient_records.append(recipient_record)

        # Insert each record individually since insert_many doesn't work with model objects
        for record in recipient_records:
            await self.statemgr.insert(record)
        
        return {
            "recipients": recipient_records
        }

    @action("message-read", resources=("message-recipient"))
    async def mark_message_read(self):
        """Action to mark a message as read for a specific user."""
        # Find the recipient record for this user and message
        recipient_record = await self.statemgr.fetch("message-recipient", self.aggroot.identifier)

        await self.statemgr.update(recipient_record, 
            read=True,
            mark_as_read=self.context.timestamp
        )
        return {
            "status": "success",
            "message_id": self.get_aggroot().identifier,
            "user_id": self.context.user_id,
            "read_at": self.context.timestamp.isoformat()
        }

    @action("bulk-messages-read", resources="message-recipient")
    async def mark_all_messages_read(self, *, user_id):
        """Action to mark all unread messages as read for a user."""
        # Find all unread message-recipient records for this user
        unread_recipients = await self.statemgr.find_all(
            "message-recipient",
            where=dict(
                recipient_id=user_id, 
                read=False
            )
        )
        
        await self.statemgr.upsert_many(
            "message-recipient",
            *[{
                "_id": recipient._id,
                "read": True,
                "mark_as_read": self.context.timestamp
            } for recipient in unread_recipients]
        )
        
        return {
            "status": "success",
            "user_id": user_id,
            "messages_read": len(unread_recipients),
        }

    @action("message-archived", resources="message-recipient")
    async def archive_message(self):
        """Action to archive a message for a specific user."""
        recipient_record = await self.statemgr.fetch("message-recipient", self.aggroot.identifier)
        await self.statemgr.update(recipient_record, archived=True)

        return {"status": "success", "message_id": self.aggroot.identifier}


    @action("attachment-added", resources="message-attachment")
    async def add_attachment(self, *, data):
        """Action to add an attachment to a message."""
        attachment_data = serialize_mapping(data)
        attachment_data['_id'] = UUID_GENR()
        
        attachment = self.statemgr.create("message-attachment", attachment_data)
        await self.statemgr.insert(attachment)
        
        return {
            "attachment_id": attachment._id,
            "message_id": data["message_id"],
        }